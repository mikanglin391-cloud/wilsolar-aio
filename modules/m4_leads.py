# -*- coding: utf-8 -*-
"""
m4_leads.py — 模块4：线索与效果统计
归集来自 AI 搜索的客户询盘，按关键词/平台/内容类型统计转化率，计算 ROI，生成月度报表。
"""
from datetime import date
import streamlit as st
import db


def render():
    st.header("🎯 模块4 · 线索与效果统计")

    conn = db.get_conn()
    tab_add, tab_stat, tab_report = st.tabs(["录入线索", "转化统计", "月度报表"])

    # ---- 录入线索 ----
    with tab_add:
        st.subheader("录入客户询盘线索")
        c1, c2, c3 = st.columns(3)
        with c1:
            company = st.text_input("公司名")
            contact = st.text_input("联系人")
            country = st.text_input("国家/地区")
        with c2:
            email = st.text_input("邮箱")
            whatsapp = st.text_input("WhatsApp")
        with c3:
            source_kw = st.text_input("来源关键词（如 100W solar street light）")
            platform = st.selectbox("来源平台", ["ChatGPT", "Bing AI", "Google SGE", "Google 搜索", "官网直达", "其他"])
        content_type = st.selectbox("内容类型", ["产品页", "场景页", "FAQ", "选型指南", "安装教程", "视频", "其他"])
        inquiry = st.text_area("询盘内容")
        lead_date = st.date_input("询盘日期", date.today())
        status = st.selectbox("跟进状态", ["new", "contacted", "quoted", "won", "lost"],
                              format_func=lambda s: {"new": "新线索", "contacted": "已联系", "quoted": "已报价", "won": "已成交", "lost": "已流失"}[s])

        if st.button("➕ 保存线索", type="primary"):
            conn.execute(
                "INSERT INTO leads (company, contact, email, whatsapp, country, source_keyword, platform, content_type, inquiry, status, lead_date) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (company, contact, email, whatsapp, country, source_kw, platform, content_type, inquiry, status, lead_date.isoformat())
            )
            conn.commit()
            st.toast("线索已保存 ✅")

        st.divider()
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 30").fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], width='stretch')
        else:
            st.info("暂无线索，录入后会在此显示")

    # ---- 转化统计 ----
    with tab_stat:
        st.subheader("转化率与 ROI 统计")
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        won = conn.execute("SELECT COUNT(*) FROM leads WHERE status='won'").fetchone()[0]
        quoted = conn.execute("SELECT COUNT(*) FROM leads WHERE status='quoted'").fetchone()[0]
        conv_rate = (won / total * 100) if total else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("总线索", total)
        m2.metric("已报价", quoted)
        m3.metric("已成交", won)
        m4.metric("成交转化率", f"{conv_rate:.1f}%")

        st.divider()
        st.caption("按关键词统计（AI 来源线索数）")
        by_kw = conn.execute(
            "SELECT source_keyword, COUNT(*) n, SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) won "
            "FROM leads WHERE source_keyword!='' GROUP BY source_keyword ORDER BY n DESC"
        ).fetchall()
        if by_kw:
            st.dataframe([{"关键词": r["source_keyword"], "线索数": r["n"], "成交数": r["won"] or 0} for r in by_kw], width='stretch')

        st.caption("按平台统计")
        by_plat = conn.execute("SELECT platform, COUNT(*) n FROM leads GROUP BY platform ORDER BY n DESC").fetchall()
        if by_plat:
            st.dataframe([{"平台": r["platform"], "线索数": r["n"]} for r in by_plat], width='stretch')

        # ROI 估算
        st.divider()
        st.subheader("ROI 估算")
        avg_order = st.number_input("单笔订单平均金额（USD）", 1000, 1000000, 20000)
        revenue = won * avg_order
        cost = total * 15  # 假设每线索获客成本约 15 USD（内容+人力分摊）
        roi = ((revenue - cost) / cost * 100) if cost else 0
        r1, r2, r3 = st.columns(3)
        r1.metric("预估收入(USD)", f"{revenue:,}")
        r2.metric("预估获客成本(USD)", f"{cost:,}")
        r3.metric("ROI", f"{roi:.0f}%")

    # ---- 月度报表 ----
    with tab_report:
        st.subheader("月度效果报表")
        month = st.text_input("报表月份（YYYY-MM）", date.today().strftime("%Y-%m"))
        rows = conn.execute(
            "SELECT * FROM leads WHERE lead_date LIKE ?", (month + "%",)
        ).fetchall()
        total_m = len(rows)
        won_m = sum(1 for r in rows if r["status"] == "won")
        kw_m = conn.execute(
            "SELECT source_keyword, COUNT(*) n FROM leads WHERE lead_date LIKE ? AND source_keyword!='' "
            "GROUP BY source_keyword ORDER BY n DESC LIMIT 10", (month + "%",)
        ).fetchall()

        st.markdown(f"### {month} 月度效果报告")
        c1, c2 = st.columns(2)
        c1.metric("本月线索", total_m)
        c2.metric("本月成交", won_m)
        if kw_m:
            st.write("**Top 关键词线索来源：**")
            st.dataframe([{"关键词": r["source_keyword"], "线索数": r["n"]} for r in kw_m], width='stretch')
        if st.button("📄 导出月度报表（文本）"):
            lines = [f"=== {month} 月度效果报表 ===", f"总线索: {total_m}", f"成交: {won_m}", "", "Top关键词:"]
            for r in kw_m:
                lines.append(f"  - {r['source_keyword']}: {r['n']} 条")
            report = "\n".join(lines)
            st.download_button("⬇️ 下载报表", report, file_name=f"月度报表_{month}.txt")

    conn.close()
