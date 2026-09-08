# -*- coding: utf-8 -*-
"""
m1_content_gen.py — 模块1：AIO 智能内容生成
增强：一键导出 HTML、重复关键词检测、批量生成仅留 UI 入口
"""
import os
import re
import streamlit as st
import config
import db
import ai_engine
import utils


def render():
    st.header("📝 模块1 · AIO 智能内容生成")

    conn = db.get_conn()
    keywords = [r["keyword"] for r in conn.execute("SELECT keyword FROM keywords WHERE status='active' ORDER BY id")]

    col1, col2, col3 = st.columns(3)
    with col1:
        kw = st.selectbox("目标关键词", keywords, index=0 if keywords else None, help=utils.HELP["keyword"])
    with col2:
        scene_key = st.selectbox("应用场景", list(config.SCENES.keys()),
                                 format_func=lambda k: config.SCENES[k]["en"], help=utils.HELP["scene"])
    with col3:
        wattage = st.selectbox("功率", [f"{w}W" for w in config.POWER], index=6, help=utils.HELP["wattage"])

    with st.expander("⚙️ 产品参数（可修改后生成）", expanded=False):
        model = st.text_input("型号", ai_engine.DEFAULT_PRODUCT["model"], help=utils.HELP["model"])
        lumen = st.text_input("光通量", ai_engine.DEFAULT_PRODUCT["lumen"], help=utils.HELP["lumen"])
        battery = st.text_input("电池", ai_engine.DEFAULT_PRODUCT["battery"], help=utils.HELP["battery"])
        warranty = st.text_input("质保", ai_engine.DEFAULT_PRODUCT["warranty"], help=utils.HELP["warranty"])
        price = st.text_input("价格", ai_engine.DEFAULT_PRODUCT["price"], help=utils.HELP["price"])
        moq = st.text_input("MOQ", ai_engine.DEFAULT_PRODUCT["moq"], help=utils.HELP["moq"])

    product_override = {
        "model": model, "lumen": lumen, "battery": battery,
        "warranty": warranty, "price": price, "moq": moq,
    }

    tab_gen, tab_batch, tab_kw = st.tabs(["单条生成", "批量生成", "词库管理"])

    # ---- 单条生成 ----
    with tab_gen:
        if st.button("✨ 生成这条内容", type="primary"):
            # 重复关键词检测
            dup = conn.execute("SELECT COUNT(*) FROM content WHERE keyword=?", (kw,)).fetchone()[0]
            if dup > 0:
                st.warning(f"⚠️ 关键词「{kw}」已制作过 {dup} 条内容，避免重复制作相同内容。")
            title, md, html, jld = ai_engine.gen_product_content(kw, scene_key, product_override)
            st.session_state["gen_title"] = title
            st.session_state["gen_md"] = md
            st.session_state["gen_html"] = html
            st.session_state["gen_jld"] = jld
            st.session_state["gen_kw"] = kw

        if "gen_md" in st.session_state:
            st.success(f"✅ 已生成：{st.session_state['gen_title']}")
            sub = st.tabs(["Markdown 预览", "HTML 源码", "JSON-LD"])
            with sub[0]:
                st.markdown(st.session_state["gen_md"])
            with sub[1]:
                st.code(st.session_state["gen_html"], language="html")
            with sub[2]:
                st.code(st.session_state["gen_jld"], language="json")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 保存到内容库", width="stretch"):
                    kw_id = conn.execute("SELECT id FROM keywords WHERE keyword=?", (st.session_state["gen_kw"],)).fetchone()["id"]
                    conn.execute(
                        "INSERT INTO content (title, keyword_id, content_type, scene, body_md, body_html, json_ld, keyword, status) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (st.session_state["gen_title"], kw_id, "scene", scene_key,
                         st.session_state["gen_md"], st.session_state["gen_html"],
                         st.session_state["gen_jld"], st.session_state["gen_kw"], "draft")
                    )
                    conn.commit()
                    utils.log(conn, "新增", "模块1-内容生成", st.session_state.get("operator", ""),
                              f"保存内容：{st.session_state['gen_kw']}")
                    st.toast("已保存到内容库 ✅")
            with c2:
                # 一键导出 HTML 文件（ASCII 安全文件名，避免 Windows [Errno 22]）
                fname = utils.ascii_filename(st.session_state["gen_kw"]) + ".html"
                st.download_button("⬇️ 一键下载 HTML 文件", st.session_state["gen_html"],
                                   file_name=fname, mime="text/html", width="stretch")

    # ---- 批量生成（仅预留 UI 入口，不实现完整逻辑） ----
    with tab_batch:
        st.caption("批量生成功能规划中，当前请使用「单条生成」逐条制作")
        sel_kws = st.multiselect("选择要批量生成的关键词（预留）", keywords, disabled=True)
        if st.button("🚀 批量生成（开发中）"):
            st.info("批量生成功能将在后续版本开放，当前请使用「单条生成」")

    # ---- 词库管理 ----
    with tab_kw:
        st.caption("拓展长尾关键词（场景 + 参数 + 品类）")
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("🧠 自动拓展长尾词"):
                new_kws = ai_engine.expand_longtail_keywords()
                added = 0
                for k in new_kws:
                    if db.add_keyword(k, "longtail", ai_engine._detect_scene_from_keyword(k)):
                        added += 1
                utils.log(conn, "新增", "模块1-词库", st.session_state.get("operator", ""), f"自动拓展长尾词 {added} 个")
                st.success(f"已拓展并入库 {added} 个长尾关键词")
        with c2:
            manual = st.text_input("手动新增关键词", help="新增关键词会自动检测场景")
            if st.button("➕ 新增") and manual:
                db.add_keyword(manual, "longtail", ai_engine._detect_scene_from_keyword(manual))
                utils.log(conn, "新增", "模块1-词库", st.session_state.get("operator", ""), f"新增关键词：{manual}")
                st.toast("已新增 ✅")

        total = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
        core = conn.execute("SELECT COUNT(*) FROM keywords WHERE kw_type='core'").fetchone()[0]
        longtail = conn.execute("SELECT COUNT(*) FROM keywords WHERE kw_type='longtail'").fetchone()[0]
        st.metric("关键词总数", total, f"核心{core} / 长尾{longtail}")

    # ---- 导出 ----
    st.divider()
    st.subheader("📤 导出内容库")
    rows = conn.execute("SELECT id, title, keyword, content_type, status, body_md, body_html FROM content ORDER BY id DESC").fetchall()
    st.caption(f"内容库共 {len(rows)} 条")
    if rows:
        exp_c1, exp_c2, exp_c3, exp_c4 = st.columns(4)
        with exp_c1:
            if st.button("导出全部 Markdown", width="stretch"):
                _export_batch(rows, "md")
        with exp_c2:
            if st.button("导出全部 HTML", width="stretch"):
                _export_batch(rows, "html")
        with exp_c3:
            if st.button("导出 sitemap 提示", width="stretch"):
                _export_sitemap(rows)
        with exp_c4:
            # 导出 Excel（英文文件名，避免 Windows [Errno 22]）
            df = utils.to_df([{"ID": r["id"], "标题": r["title"], "关键词": r["keyword"],
                               "类型": r["content_type"], "状态": r["status"]} for r in rows])
            utils.export_excel(df, "content_library.xlsx", "📊 导出 Excel")
    conn.close()


def _export_batch(rows, fmt):
    outdir = os.path.join(config.EXPORT_DIR, "content_" + fmt)
    os.makedirs(outdir, exist_ok=True)
    n = 0
    for r in rows:
        fname = f"{r['id']}_{_safe(r['title'])}.{fmt}"
        body = r["body_md"] if fmt == "md" else r["body_html"]
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            f.write(body)
        n += 1
    st.success(f"✅ 已导出 {n} 个文件到：{outdir}")


def _export_sitemap(rows):
    urls = []
    for r in rows:
        slug = _safe(r["title"]).replace(" ", "-").lower()
        urls.append(f"https://www.wilsolar.com/{slug}/")
    content = "".join(f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n" for u in urls)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + content + "</urlset>"
    p = os.path.join(config.EXPORT_DIR, "sitemap_suggestion.xml")
    with open(p, "w", encoding="utf-8") as f:
        f.write(sitemap)
    st.success(f"✅ 已生成站点地图建议：{p}")


def _safe(s):
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "_", s)[:60]
