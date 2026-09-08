# -*- coding: utf-8 -*-
"""
m4_leads.py — 模块4：线索与效果统计
增强：模拟/正式模式、跟进状态流转、Excel 导出、完善转化统计
"""
from datetime import date
import streamlit as st
import db
import utils

STATUS_LABELS = {
    "new": "新线索", "contacted": "跟进中", "quoted": "报价", "won": "成交", "lost": "流失",
}
STATUS_ORDER = ["new", "contacted", "quoted", "won", "lost"]


def render():
    st.header("🎯 模块4 · 线索与效果统计")

    conn = db.get_conn()
    is_formal = st.session_state.get("biz_mode", "simulate") == "formal"
    mode_badge = "🔴 正式业务模式（邮箱/关键词/国家必填）" if is_formal else "🟡 模拟模式（字段可留空）"
    st.caption(f"当前：{mode_badge}（可在左侧切换）")

    tab_add, tab_list, tab_stat, tab_report = st.tabs(["录入线索", "线索跟进", "转化统计", "月度报表"])

    # ---- 录入线索 ----
    with tab_add:
        st.subheader("录入客户询盘线索")
        c1, c2, c3 = st.columns(3)
        with c1:
            company = st.text_input("公司名", help=utils.HELP["company"])
            contact = st.text_input("联系人", help=utils.HELP["contact"])
            country = st.text_input("国家/地区" + (" *" if is_formal else ""), help=utils.HELP["country"])
        with c2:
            email = st.text_input("邮箱" + (" *" if is_formal else ""), help=utils.HELP["email"])
            whatsapp = st.text_input("WhatsApp", help=utils.HELP["whatsapp"])
        with c3:
            source_kw = st.text_input("来源关键词" + (" *" if is_formal else ""), help=utils.HELP["source_keyword"])
            platform = st.selectbox("来源平台", ["ChatGPT", "Bing AI", "Google SGE", "Google 搜索", "官网直达", "其他"], help=utils.HELP["platform"])
        content_type = st.selectbox("内容类型", ["产品页", "场景页", "FAQ", "选型指南", "安装教程", "视频", "其他"], help=utils.HELP["content_type"])
        inquiry = st.text_area("询盘内容", help=utils.HELP["inquiry"])
        lead_date = st.date_input("询盘日期", date.today())
        status = st.selectbox("初始状态", STATUS_ORDER, format_func=lambda s: STATUS_LABELS[s])

        if st.button("➕ 保存线索", type="primary"):
            # 正式模式必填校验
            if is_formal:
                missing = []
                if not email.strip():
                    missing.append("邮箱")
                if not source_kw.strip():
                    missing.append("来源关键词")
                if not country.strip():
                    missing.append("国家")
                if missing:
                    st.error("❌ 正式业务模式下，以下字段必填：" + "、".join(missing))
                else:
                    ok, err = utils.validate_email(email)
                    if not ok:
                        st.error(f"❌ {err}")
                    else:
                        _save_lead(conn, company, contact, email, whatsapp, country, source_kw, platform, content_type, inquiry, status, lead_date)
            else:
                if email.strip():
                    ok, err = utils.validate_email(email)
                    if not ok:
                        st.error(f"❌ {err}")
                    else:
                        _save_lead(conn, company, contact, email, whatsapp, country, source_kw, platform, content_type, inquiry, status, lead_date)
                else:
                    _save_lead(conn, company, contact, email, whatsapp, country, source_kw, platform, content_type, inquiry, status, lead_date)

    # ---- 线索跟进 ----
    with tab_list:
        st.subheader("线索列表与跟进")
        rows = conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 50").fetchall()
        if not rows:
            st.info("暂无线索，请先在「录入线索」添加")
        else:
            for r in rows:
                status_label = STATUS_LABELS.get(r["status"], r["status"])
                with st.expander(f"#{r['id']} {r['company'] or '（无公司名）'} · {status_label} · {r['lead_date']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**联系人：** {r['contact'] or '—'}")
                        st.write(f"**邮箱：** {r['email'] or '—'}")
                        st.write(f"**WhatsApp：** {r['whatsapp'] or '—'}")
                    with c2:
                        st.write(f"**国家：** {r['country'] or '—'}")
                        st.write(f"**来源关键词：** {r['source_keyword'] or '—'}")
                        st.write(f"**平台：** {r['platform'] or '—'}")
                    st.write(f"**询盘：** {r['inquiry'] or '—'}")

                    # 跟进记录
                    followups = db.get_followups(conn, r["id"])
                    if followups:
                        st.caption("跟进记录：")
                        for fu in followups:
                            st.markdown(f"- `{fu['follow_date']}` [{STATUS_LABELS.get(fu['status'], fu['status'])}] {fu['note']}")

                    # 添加跟进 + 状态流转
                    st.markdown("**➕ 添加跟进记录（并流转状态）**")
                    f1, f2, f3 = st.columns([1, 1, 2])
                    with f1:
                        fu_date = st.date_input("跟进日期", date.today(), key=f"fd{r['id']}")
                    with f2:
                        fu_status = st.selectbox("新状态", STATUS_ORDER,
                                                 index=STATUS_ORDER.index(r["status"]) if r["status"] in STATUS_ORDER else 0,
                                                 format_func=lambda s: STATUS_LABELS[s], key=f"fs{r['id']}")
                    with f3:
                        fu_note = st.text_input("跟进备注", key=f"fn{r['id']}")
                    if st.button("保存跟进", key=f"fbtn{r['id']}"):
                        db.add_followup(conn, r["id"], fu_note, fu_status, fu_date.isoformat())
                        conn.execute("UPDATE leads SET status=? WHERE id=?", (fu_status, r["id"]))
                        conn.commit()
                        utils.log(conn, "修改", "模块4-跟进", st.session_state.get("operator", ""),
                                  f"线索#{r['id']} 流转 → {STATUS_LABELS[fu_status]}")
                        st.toast("跟进已保存 ✅")
                        st.rerun()

            # 导出线索 Excel
            df = utils.to_df([{"ID": r["id"], "公司": r["company"], "联系人": r["contact"],
                               "邮箱": r["email"], "国家": r["country"], "来源关键词": r["source_keyword"],
                               "平台": r["platform"], "状态": STATUS_LABELS.get(r["status"], r["status"]),
                               "日期": r["lead_date"]} for r in rows])
            utils.export_excel(df, "leads.xlsx")

    # ---- 转化统计 ----
    with tab_stat:
        st.subheader("转化率与 ROI 统计")
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        won = conn.execute("SELECT COUNT(*) FROM leads WHERE status='won'").fetchone()[0]
        quoted = conn.execute("SELECT COUNT(*) FROM leads WHERE status='quoted'").fetchone()[0]
        conv_rate = (won / total * 100) if total else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("总线索数", total)
        m2.metric("成交线索数", won)
        m3.metric("已报价", quoted)
        m4.metric("询盘转化率", f"{conv_rate:.1f}%")

        st.divider()
        st.caption("按关键词统计（AI 来源线索数）")
        by_kw = conn.execute(
            "SELECT source_keyword, COUNT(*) n, SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) won "
            "FROM leads WHERE source_keyword!='' GROUP BY source_keyword ORDER BY n DESC"
        ).fetchall()
        if by_kw:
            kw_df = utils.to_df([{"关键词": r["source_keyword"], "线索数": r["n"], "成交数": r["won"] or 0} for r in by_kw])
            st.dataframe(kw_df, width="stretch")
            utils.export_excel(kw_df, "conversion_by_keyword.xlsx")

        st.caption("按平台统计")
        by_plat = conn.execute("SELECT platform, COUNT(*) n FROM leads GROUP BY platform ORDER BY n DESC").fetchall()
        if by_plat:
            plat_df = utils.to_df([{"平台": r["platform"], "线索数": r["n"]} for r in by_plat])
            st.dataframe(plat_df, width="stretch")
            utils.export_excel(plat_df, "conversion_by_platform.xlsx")

        # ROI 估算
        st.divider()
        st.subheader("ROI 估算")
        avg_order = st.number_input("单笔订单平均金额（USD）", 1000, 1000000, 20000)
        revenue = won * avg_order
        cost = total * 15
        roi = ((revenue - cost) / cost * 100) if cost else 0
        r1, r2, r3 = st.columns(3)
        r1.metric("预估收入(USD)", f"{revenue:,}")
        r2.metric("预估获客成本(USD)", f"{cost:,}")
        r3.metric("ROI", f"{roi:.0f}%")

    # ---- 月度报表 ----
    with tab_report:
        st.subheader("月度效果报表")
        month = st.text_input("报表月份（YYYY-MM）", date.today().strftime("%Y-%m"))
        rows = conn.execute("SELECT * FROM leads WHERE lead_date LIKE ?", (month + "%",)).fetchall()
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
            st.dataframe(utils.to_df([{"关键词": r["source_keyword"], "线索数": r["n"]} for r in kw_m]), width="stretch")
        if st.button("📄 导出月度报表（文本）"):
            lines = [f"=== {month} 月度效果报表 ===", f"总线索: {total_m}", f"成交: {won_m}", "", "Top关键词:"]
            for r in kw_m:
                lines.append(f"  - {r['source_keyword']}: {r['n']} 条")
            report = "\n".join(lines)
            st.download_button("⬇️ 下载报表", report, file_name=f"monthly_report_{month}.txt")

    conn.close()


def _save_lead(conn, company, contact, email, whatsapp, country, source_kw, platform, content_type, inquiry, status, lead_date):
    conn.execute(
        "INSERT INTO leads (company, contact, email, whatsapp, country, source_keyword, platform, content_type, inquiry, status, lead_date) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (company, contact, email, whatsapp, country, source_kw, platform, content_type, inquiry, status, lead_date.isoformat())
    )
    conn.commit()
    utils.log(conn, "新增", "模块4-线索", st.session_state.get("operator", ""), f"录入线索：{company or source_kw}")
    st.toast("线索已保存 ✅")
    st.success("线索已保存 ✅")
