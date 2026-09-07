# -*- coding: utf-8 -*-
"""
m3_ranking.py — 模块3：AI 排名每日监测
监测核心关键词在 ChatGPT / Bing AI / Google SGE 中的推荐位次。
说明：生成式 AI 搜索无公开稳定 API，且需真实海外环境，故采用「监测提示词模板 + 手动录入 + 自动趋势分析」的落地方式。
"""
from datetime import date, datetime, timedelta
import streamlit as st
import db
import config


def render():
    st.header("📈 模块3 · AI 排名每日监测")

    conn = db.get_conn()
    tab_monitor, tab_trend, tab_suggest = st.tabs(["今日监测录入", "排名趋势", "优化建议"])

    # ---- 监测录入 ----
    with tab_monitor:
        st.subheader("监测操作指引（海外环境查询后录入）")
        with st.expander("🔍 如何监测 AI 排名（复制提示词到各平台查询）", expanded=False):
            st.markdown(
                "**在真实海外网络环境**（或登录 ChatGPT/Bing 国际版）中，用以下提示词查询，"
                "记录我方品牌 `Wilsolar` 出现的位置、推荐话术、引用来源：\n\n"
                "**ChatGPT：**\n"
                "`Top 10 solar street light manufacturers in China for B2B project buyers, "
                "ranked by reliability and certifications`\n\n"
                "**Bing AI (Copilot)：**\n"
                "`Best 100W solar street light suppliers for industrial park projects with CE/RoHS`\n\n"
                "**Google SGE：** 直接在 Google 搜索关键词，看顶部 AI Overview 是否提到 Wilsolar。\n\n"
                "⚠️ 若查询环境被 OpenAI 封锁（数据中心 IP），改用 Bing AI / Google SGE 或手机热点。"
            )

        keywords = [r["keyword"] for r in conn.execute("SELECT keyword FROM keywords WHERE status='active' ORDER BY id")]
        c1, c2, c3 = st.columns(3)
        with c1:
            kw = st.selectbox("关键词", keywords)
        with c2:
            platform = st.selectbox("AI 平台", config.PLATFORMS)
        with c3:
            snap_date = st.date_input("监测日期", date.today())

        r1, r2 = st.columns(2)
        with r1:
            rank = st.number_input("我方出现位次（0=未出现，1=第1位）", 0, 20, 0)
        with r2:
            source_url = st.text_input("AI 引用来源 URL（选填）")
        mention = st.text_area("AI 推荐话术（AI 提到我方的原话）")

        if st.button("💾 记录本次排名", type="primary"):
            kw_id = conn.execute("SELECT id FROM keywords WHERE keyword=?", (kw,)).fetchone()["id"]
            conn.execute(
                "INSERT INTO ranking_snapshots (keyword_id, keyword, platform, snap_date, rank, mention_text, source_url) "
                "VALUES (?,?,?,?,?,?,?)",
                (kw_id, kw, platform, snap_date.isoformat(), rank, mention, source_url)
            )
            conn.commit()
            st.toast("排名已记录 ✅")

        st.divider()
        st.caption("今日已监测记录")
        today = date.today().isoformat()
        rows = conn.execute(
            "SELECT keyword, platform, rank, mention_text FROM ranking_snapshots WHERE snap_date=? ORDER BY id DESC",
            (today,)
        ).fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True)
        else:
            st.info("今日暂无记录")

    # ---- 排名趋势 ----
    with tab_trend:
        st.subheader("排名趋势报告")
        kw = st.selectbox("选择关键词查看趋势", [r["keyword"] for r in conn.execute("SELECT keyword FROM keywords ORDER BY id")], key="trend_kw")
        days = st.slider("查看最近天数", 7, 60, 30)
        since = (date.today() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT snap_date, platform, rank, mention_text, source_url FROM ranking_snapshots "
            "WHERE keyword=? AND snap_date>=? ORDER BY snap_date, platform", (kw, since)
        ).fetchall()
        if not rows:
            st.info("该关键词暂无排名数据，请先在「今日监测录入」记录")
        else:
            df = [dict(r) for r in rows]
            st.dataframe(df, use_container_width=True)
            # 升降标注
            by_platform = {}
            for r in df:
                by_platform.setdefault(r["platform"], []).append((r["snap_date"], r["rank"]))
            st.markdown("**升降变化：**")
            for p, seq in by_platform.items():
                seq_sorted = sorted(seq)
                latest = seq_sorted[-1][1]
                if len(seq_sorted) >= 2:
                    prev = seq_sorted[-2][1]
                    if latest == 0:
                        arrow = "🔴 未出现"
                    elif prev == 0 and latest > 0:
                        arrow = f"🟢 新进入 第{latest}位"
                    elif latest < prev:
                        arrow = f"📈 上升 第{prev}→{latest}位"
                    elif latest > prev:
                        arrow = f"📉 下降 第{prev}→{latest}位"
                    else:
                        arrow = f"➖ 持平 第{latest}位"
                else:
                    arrow = f"首次 第{latest}位" if latest > 0 else "未出现"
                st.write(f"- **{p}**: {arrow}")

    # ---- 优化建议 ----
    with tab_suggest:
        st.subheader("自动优化建议")
        st.caption("根据最新排名与内容新鲜度自动生成")
        today = date.today()
        kws = [r["keyword"] for r in conn.execute("SELECT keyword FROM keywords WHERE status='active'")]
        suggestions = []
        for kw in kws:
            latest = conn.execute(
                "SELECT platform, rank, snap_date FROM ranking_snapshots WHERE keyword=? ORDER BY snap_date DESC LIMIT 1",
                (kw,)
            ).fetchone()
            if latest is None:
                suggestions.append((kw, "未监测", "⏳ 请先完成首次排名监测，建立基线"))
                continue
            r = latest["rank"]
            if r == 0:
                suggestions.append((kw, "未出现", "🔴 增加该词内容覆盖 + 发布 FAQ/选型指南 + 提交 sitemap"))
            elif r <= 3:
                suggestions.append((kw, f"第{r}位", "🟢 保持高频更新 + 强化信任信号，巩固前3位"))
            elif r <= 10:
                suggestions.append((kw, f"第{r}位", "🟡 补充结构化数据(JSON-LD) + 场景化内容，冲刺前3"))
            else:
                suggestions.append((kw, f"第{r}位", "🔴 重新审视内容匹配度，扩展长尾词覆盖"))
        st.dataframe([{"关键词": s[0], "当前排名": s[1], "建议": s[2]} for s in suggestions], use_container_width=True)

    conn.close()
