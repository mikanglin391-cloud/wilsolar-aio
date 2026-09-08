# -*- coding: utf-8 -*-
"""
m2_distribution.py — 模块2：多渠道内容分发管理
增强：模拟/真实标签、一键复制 URL、URL 格式校验、Excel 导出
"""
from datetime import datetime, date
import streamlit as st
import db
import config
import utils


def render():
    st.header("📡 模块2 · 多渠道内容分发管理")

    conn = db.get_conn()
    tab_ch, tab_pub, tab_fresh = st.tabs(["发布渠道", "发布内容", "新鲜度与收录"])

    # ---- 渠道管理 ----
    with tab_ch:
        st.subheader("发布渠道")
        channels = conn.execute("SELECT * FROM channels WHERE status='active'").fetchall()
        for c in channels:
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            col1.write(f"**{c['name']}**  ({c['ch_type']})")
            col2.write(c["url"] if c["url"] else "—")
            col3.write(c["note"])
            if col4.button("删除", key=f"delch{c['id']}"):
                conn.execute("UPDATE channels SET status='archived' WHERE id=?", (c["id"],))
                conn.commit()
                utils.log(conn, "修改", "模块2-渠道", st.session_state.get("operator", ""), f"删除渠道：{c['name']}")
                st.rerun()

        st.divider()
        c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
        with c1:
            new_name = st.text_input("渠道名称", key="ch_name")
        with c2:
            new_type = st.selectbox("类型", ["website", "gmb", "directory", "social"], key="ch_type")
        with c3:
            new_url = st.text_input("URL（可选）", key="ch_url")
        with c4:
            if st.button("➕ 添加渠道"):
                if new_name:
                    conn.execute("INSERT INTO channels (name, ch_type, url) VALUES (?,?,?)",
                                 (new_name, new_type, new_url))
                    conn.commit()
                    utils.log(conn, "新增", "模块2-渠道", st.session_state.get("operator", ""), f"新增渠道：{new_name}")
                    st.toast("渠道已添加 ✅")
                else:
                    st.warning("请填写渠道名称")

    # ---- 发布内容 ----
    with tab_pub:
        st.subheader("记录内容发布")
        contents = conn.execute("SELECT id, title, keyword FROM content ORDER BY id DESC").fetchall()
        channels = conn.execute("SELECT id, name FROM channels WHERE status='active'").fetchall()
        if not contents:
            st.info("内容库为空，请先在模块1生成内容")
        else:
            content_map = {f"#{c['id']} {c['title'][:40]}": c for c in contents}
            ch_map = {c["name"]: c["id"] for c in channels}
            sel_content = st.selectbox("选择内容", list(content_map.keys()))
            sel_channel = st.selectbox("选择渠道", list(ch_map.keys()))
            pub_date = st.date_input("发布日期", date.today())
            pub_url = st.text_input("发布 URL（独立站/目录站链接）", help=utils.HELP["url"])
            if st.button("✅ 记录发布", type="primary"):
                # URL 格式校验
                ok, err = utils.validate_url(pub_url)
                if not ok:
                    st.error(f"❌ {err}（模拟链接可留空或标记为模拟）")
                else:
                    c = content_map[sel_content]
                    # 默认标记：URL 为空或非法 → 模拟记录；合法 URL → 仍默认模拟，可手动切真实
                    is_real = 1 if (pub_url.strip().startswith("http")) else 0
                    tag = "real" if is_real else "simulated"
                    conn.execute(
                        "INSERT INTO publish_log (content_id, channel_id, keyword, publish_date, url, tag, is_real) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (c["id"], ch_map[sel_channel], c["keyword"], pub_date.isoformat(), pub_url, tag, is_real)
                    )
                    conn.execute("UPDATE content SET status='published' WHERE id=?", (c["id"],))
                    conn.commit()
                    utils.log(conn, "新增", "模块2-发布", st.session_state.get("operator", ""),
                              f"发布：{c['keyword']} → {sel_channel}")
                    st.toast("发布记录已保存 ✅")

        st.divider()
        st.caption("最近发布记录（可切换真实上线状态 / 复制 URL）")
        logs = conn.execute(
            "SELECT p.id, c.title, ch.name, p.keyword, p.publish_date, p.url, p.tag, p.is_real "
            "FROM publish_log p LEFT JOIN content c ON c.id=p.content_id "
            "LEFT JOIN channels ch ON ch.id=p.channel_id ORDER BY p.id DESC LIMIT 20"
        ).fetchall()
        if logs:
            for lg in logs:
                r1, r2, r3, r4 = st.columns([3, 2, 1, 1])
                status = "🟢 已真实上线" if lg["is_real"] else "🟡 模拟记录"
                r1.write(f"**{lg['title'] or '—'}** → {lg['name']}  `{status}`")
                r2.write(f"{lg['publish_date']} · {lg['keyword']}")
                # 一键复制 URL
                if r3.button("复制URL", key=f"cp{lg['id']}", help=lg["url"] or "无URL"):
                    st.session_state[f"url_{lg['id']}"] = lg["url"]
                # 切换真实/模拟
                toggle_label = "标为真实" if not lg["is_real"] else "标为模拟"
                if r4.button(toggle_label, key=f"tg{lg['id']}"):
                    new_real = 0 if lg["is_real"] else 1
                    conn.execute("UPDATE publish_log SET is_real=?, tag=? WHERE id=?",
                                 (new_real, "real" if new_real else "simulated", lg["id"]))
                    conn.commit()
                    utils.log(conn, "修改", "模块2-发布", st.session_state.get("operator", ""),
                              f"切换标签：#{lg['id']} → {'已真实上线' if new_real else '模拟记录'}")
                    st.rerun()
                if st.session_state.get(f"url_{lg['id']}"):
                    utils.copy_block(st.session_state[f"url_{lg['id']}"], "已复制，点击右上角复制按钮")
            # 导出 Excel
            df = utils.to_df([{"ID": lg["id"], "标题": lg["title"], "渠道": lg["name"],
                               "关键词": lg["keyword"], "发布日期": lg["publish_date"],
                               "URL": lg["url"], "状态": "已真实上线" if lg["is_real"] else "模拟记录"} for lg in logs])
            utils.export_excel(df, "publish_log.xlsx")
        else:
            st.info("暂无发布记录")

    # ---- 新鲜度 ----
    with tab_fresh:
        st.subheader("内容新鲜度")
        st.caption("AI 搜索引擎偏好新鲜、持续更新的内容。新鲜度 = 距发布日期天数，≤30天为「新鲜」")
        logs = conn.execute(
            "SELECT keyword, MAX(publish_date) as last_pub FROM publish_log GROUP BY keyword ORDER BY last_pub DESC"
        ).fetchall()
        today = date.today()
        fresh = stale = 0
        data = []
        for r in logs:
            try:
                d = datetime.strptime(r["last_pub"], "%Y-%m-%d").date()
                days = (today - d).days
            except Exception:
                days = 999
            status = "🟢 新鲜" if days <= 30 else ("🟡 一般" if days <= 60 else "🔴 陈旧")
            if days <= 30:
                fresh += 1
            else:
                stale += 1
            data.append({"关键词": r["keyword"], "最近发布": r["last_pub"], "距今(天)": days, "状态": status})
        c1, c2 = st.columns(2)
        c1.metric("新鲜内容（≤30天）", fresh)
        c2.metric("陈旧内容（>30天）", stale)
        if data:
            st.dataframe(utils.to_df(data), width="stretch")

        st.divider()
        st.subheader("📮 站点地图提交提醒")
        st.info(
            "发布新内容后，把 sitemap 提交到：\n\n"
            "1. Google Search Console → 站点地图 → 提交 `sitemap.xml`\n"
            "2. Bing Webmaster → 站点地图 → 提交\n"
            "3. 用 Google URL Inspection 请求「编入索引」\n\n"
            "这一步能触发 Google/Bing 的 AI 爬虫快速抓取，加速被 AI 搜索引擎引用。"
        )
        if st.button("🔔 今日已提交（记录）"):
            utils.log(conn, "打卡", "模块2-sitemap", st.session_state.get("operator", ""), "提交 sitemap")
            st.toast("已记录 ✅ 建议每周提交 1-2 次")

    conn.close()
