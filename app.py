# -*- coding: utf-8 -*-
"""
app.py — 户外路灯外贸 AIO 获客自动化系统 · 主入口
运行：streamlit run app.py
"""
import streamlit as st
import config
import db
from modules import m1_content_gen, m2_distribution, m3_ranking, m4_leads, m5_project

st.set_page_config(page_title="户外路灯外贸 AIO 获客系统", page_icon="💡", layout="wide")


@st.cache_resource
def _init():
    db.init_db()
    return True


_init()

# 侧边栏导航
st.sidebar.title("💡 伟澳新能源 AIO 获客系统")
st.sidebar.caption("户外路灯 · 外贸 B 端 · AI 搜索优化")
menu = st.sidebar.radio(
    "功能模块",
    ["🏠 首页概览", "📝 1. AIO内容生成", "📡 2. 内容分发", "📈 3. 排名监测",
     "🎯 4. 线索效果", "👥 5. 项目管理与绩效"],
)

if menu.startswith("🏠"):
    _home()
elif menu.startswith("📝"):
    m1_content_gen.render()
elif menu.startswith("📡"):
    m2_distribution.render()
elif menu.startswith("📈"):
    m3_ranking.render()
elif menu.startswith("🎯"):
    m4_leads.render()
elif menu.startswith("👥"):
    m5_project.render()


def _home():
    st.title("户外路灯外贸 AIO 获客自动化系统")
    st.caption(f"品牌：{config.COMPANY['brand']} · 官网：{config.COMPANY['website']}")
    conn = db.get_conn()
    kw = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    content = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    published = conn.execute("SELECT COUNT(*) FROM content WHERE status='published'").fetchone()[0]
    rankings = conn.execute("SELECT COUNT(*) FROM ranking_snapshots").fetchone()[0]
    leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("关键词库", kw)
    c2.metric("内容库", content)
    c3.metric("已发布", published)
    c4.metric("排名记录", rankings)
    c5.metric("客户线索", leads)

    st.divider()
    st.subheader("🎯 3个月目标")
    st.markdown(
        "> **核心业务目标：** 让 ChatGPT / Bing AI / Google SGE 在搜索「户外路灯采购需求」时，"
        "优先推荐 Wilsolar；3个月内核心关键词 AI 推荐排名进入前 3 位。"
    )
    for m, p in config.PHASES.items():
        st.markdown(f"- **第{m}个月（{p['name']}）**：{p['goal']}")

    st.divider()
    st.subheader("🚀 今日快速入口")
    st.info(
        "**运营节奏：**\n\n"
        "· 角色A（内容运营）：模块1生成内容 → 模块2发布\n"
        "· 角色B（数据运营）：模块3监测排名 → 模块4录线索\n"
        "· 两人共同：模块5 每日打卡 + 绩效核算"
    )

    # 最近排名与线索预览
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("最新排名记录")
        rows = conn.execute("SELECT keyword, platform, rank, snap_date FROM ranking_snapshots ORDER BY id DESC LIMIT 8").fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True)
        else:
            st.caption("暂无，请到模块3开始监测")
    with col2:
        st.subheader("最新线索")
        rows = conn.execute("SELECT company, country, source_keyword, status, lead_date FROM leads ORDER BY id DESC LIMIT 8").fetchall()
        if rows:
            st.dataframe([dict(r) for r in rows], use_container_width=True)
        else:
            st.caption("暂无，请到模块4录入")
    conn.close()


if __name__ == "__main__":
    # 本地直接运行时的简易说明（正常通过 streamlit run 启动）
    print("请使用命令启动：streamlit run app.py")
