# -*- coding: utf-8 -*-
"""
m1_content_gen.py — 模块1：AIO 智能内容生成
生成符合 AI 搜索引擎抓取偏好的英文外贸内容，支持批量生成与导出。
"""
import json
import os
import streamlit as st
import config
import db
import ai_engine


def render():
    st.header("📝 模块1 · AIO 智能内容生成")

    conn = db.get_conn()
    keywords = [r["keyword"] for r in conn.execute("SELECT keyword FROM keywords WHERE status='active' ORDER BY id")]

    col1, col2, col3 = st.columns(3)
    with col1:
        kw = st.selectbox("目标关键词", keywords, index=0 if keywords else None)
    with col2:
        scene_key = st.selectbox("应用场景", list(config.SCENES.keys()),
                                 format_func=lambda k: config.SCENES[k]["en"])
    with col3:
        wattage = st.selectbox("功率", [f"{w}W" for w in config.POWER], index=6)  # 默认100W

    # 产品参数可折叠编辑
    with st.expander("⚙️ 产品参数（可修改后生成）", expanded=False):
        model = st.text_input("型号", ai_engine.DEFAULT_PRODUCT["model"])
        lumen = st.text_input("光通量", ai_engine.DEFAULT_PRODUCT["lumen"])
        battery = st.text_input("电池", ai_engine.DEFAULT_PRODUCT["battery"])
        warranty = st.text_input("质保", ai_engine.DEFAULT_PRODUCT["warranty"])
        price = st.text_input("价格", ai_engine.DEFAULT_PRODUCT["price"])
        moq = st.text_input("MOQ", ai_engine.DEFAULT_PRODUCT["moq"])

    product_override = {
        "model": model, "lumen": lumen, "battery": battery,
        "warranty": warranty, "price": price, "moq": moq,
    }

    tab_gen, tab_batch, tab_kw = st.tabs(["单条生成", "批量生成", "词库管理"])

    # ---- 单条生成 ----
    with tab_gen:
        if st.button("✨ 生成这条内容", type="primary"):
            title, md, html, jld = ai_engine.gen_product_content(kw, scene_key, product_override)
            st.session_state["gen_title"] = title
            st.session_state["gen_md"] = md
            st.session_state["gen_html"] = html
            st.session_state["gen_jld"] = jld

        if "gen_md" in st.session_state:
            st.success(f"✅ 已生成：{st.session_state['gen_title']}")
            sub = st.tabs(["Markdown 预览", "HTML 源码", "JSON-LD"])
            with sub[0]:
                st.markdown(st.session_state["gen_md"])
            with sub[1]:
                st.code(st.session_state["gen_html"], language="html")
            with sub[2]:
                st.code(st.session_state["gen_jld"], language="json")

            if st.button("💾 保存到内容库"):
                kw_id = conn.execute("SELECT id FROM keywords WHERE keyword=?", (kw,)).fetchone()["id"]
                conn.execute(
                    "INSERT INTO content (title, keyword_id, content_type, scene, body_md, body_html, json_ld, keyword, status) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (st.session_state["gen_title"], kw_id, "scene", scene_key,
                     st.session_state["gen_md"], st.session_state["gen_html"],
                     st.session_state["gen_jld"], kw, "draft")
                )
                conn.commit()
                st.toast("已保存到内容库 ✅")

    # ---- 批量生成 ----
    with tab_batch:
        st.caption("勾选关键词，批量生成内容（每个关键词自动匹配场景）")
        sel_kws = st.multiselect("选择要批量生成的关键词", keywords)
        if st.button("🚀 批量生成", type="primary"):
            count = 0
            progress = st.progress(0.0)
            for i, k in enumerate(sel_kws):
                title, md, html, jld = ai_engine.gen_product_content(k, None, product_override)
                kw_id = conn.execute("SELECT id FROM keywords WHERE keyword=?", (k,)).fetchone()["id"]
                conn.execute(
                    "INSERT INTO content (title, keyword_id, content_type, scene, body_md, body_html, json_ld, keyword, status) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (title, kw_id, "scene", ai_engine._detect_scene_from_keyword(k) or "municipal",
                     md, html, jld, k, "draft")
                )
                count += 1
                progress.progress((i + 1) / len(sel_kws))
            conn.commit()
            st.success(f"✅ 批量生成完成：{count} 条内容已存入内容库")

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
                st.success(f"已拓展并入库 {added} 个长尾关键词")
        with c2:
            manual = st.text_input("手动新增关键词")
            if st.button("➕ 新增") and manual:
                db.add_keyword(manual, "longtail", ai_engine._detect_scene_from_keyword(manual))
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
        exp_c1, exp_c2, exp_c3 = st.columns(3)
        with exp_c1:
            if st.button("导出全部 Markdown"):
                _export_batch(rows, "md")
        with exp_c2:
            if st.button("导出全部 HTML"):
                _export_batch(rows, "html")
        with exp_c3:
            if st.button("导出 sitemap 提示"):
                _export_sitemap(rows)
    conn.close()


def _export_batch(rows, fmt):
    import config as cfg
    outdir = os.path.join(cfg.EXPORT_DIR, "content_" + fmt)
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
    import config as cfg
    urls = []
    for r in rows:
        slug = _safe(r["title"]).replace(" ", "-").lower()
        urls.append(f"https://www.wilsolar.com/{slug}/")
    content = "".join(f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n" for u in urls)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + content + "</urlset>"
    p = os.path.join(cfg.EXPORT_DIR, "sitemap_suggestion.xml")
    with open(p, "w", encoding="utf-8") as f:
        f.write(sitemap)
    st.success(f"✅ 已生成站点地图建议 → 提交到 Google Search Console / Bing Webmaster，加速 AI 爬虫收录：{p}")


def _safe(s):
    import re
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "_", s)[:60]
