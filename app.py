# -*- coding: utf-8 -*-
"""
app.py — 户外路灯外贸 AIO 获客自动化系统 · 主入口
运行：streamlit run app.py
"""
from datetime import date, datetime, timedelta
from collections import defaultdict
import pandas as pd
import streamlit as st
import config
import db
import utils
from modules import m1_content_gen, m2_distribution, m3_ranking, m4_leads, m5_project

st.set_page_config(page_title="户外路灯外贸 AIO 获客系统", page_icon="💡", layout="wide")


@st.cache_resource
def _init():
    db.init_db()
    return True


_init()


def _current_phase():
    """根据项目启动日期计算当前处于第几个月（1-3）。"""
    try:
        start = datetime.strptime(config.PROJECT_START_DATE, "%Y-%m-%d")
        now = datetime.now()
        m = (now.year - start.year) * 12 + (now.month - start.month) + 1
        return max(1, min(3, m))
    except Exception:
        return 1


def _daily_counts(conn, table, date_col, days=14):
    """统计近 N 天每天新增数（用于首页小趋势图）。"""
    rows = conn.execute(f"SELECT {date_col} AS d FROM {table}").fetchall()
    counts = defaultdict(int)
    for r in rows:
        key = (r["d"] or "")[:10]
        if key:
            counts[key] += 1
    today = date.today()
    data = []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        data.append({"日期": d[5:], "新增": counts.get(d, 0)})
    return pd.DataFrame(data)


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

    # ---- 小型趋势图（近14天新增） ----
    st.divider()
    st.subheader("📊 近期增长趋势（近 14 天）")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.caption("关键词新增")
        st.bar_chart(_daily_counts(conn, "keywords", "created_at").set_index("日期"), height=160)
    with t2:
        st.caption("内容新增")
        st.bar_chart(_daily_counts(conn, "content", "created_at").set_index("日期"), height=160)
    with t3:
        st.caption("发布新增")
        st.bar_chart(_daily_counts(conn, "publish_log", "publish_date").set_index("日期"), height=160)

    # ---- 3个月目标进度条 ----
    st.divider()
    st.subheader("🎯 3个月目标进度")
    phase = _current_phase()
    # 当前累计值
    actual = {
        "内容产出": content,
        "发布次数": conn.execute("SELECT COUNT(*) FROM publish_log").fetchone()[0],
        "排名监测": rankings,
        "询盘线索": leads,
    }
    for m, p in config.PHASES.items():
        goal = config.PHASE_GOALS[m]
        mark = "🟢 当前阶段" if m == phase else ""
        with st.expander(f"第{m}个月 · {p['name']} {mark}", expanded=(m == phase)):
            cols = st.columns(4)
            for i, (k, g) in enumerate(goal.items()):
                a = actual.get(k, 0)
                ratio = min(1.0, a / g) if g else 0
                cols[i].metric(k, f"{a}/{g}", f"{int(ratio*100)}%")
                cols[i].progress(ratio)

    # ---- 今日快速入口（可点击跳转） ----
    st.divider()
    st.subheader("🚀 今日快速入口")
    b1, b2, b3, b4, b5 = st.columns(5)
    if b1.button("📝 生成内容", width="stretch"):
        st.session_state.menu = "📝 1. AIO内容生成"
        st.rerun()
    if b2.button("📡 内容分发", width="stretch"):
        st.session_state.menu = "📡 2. 内容分发"
        st.rerun()
    if b3.button("📈 排名监测", width="stretch"):
        st.session_state.menu = "📈 3. 排名监测"
        st.rerun()
    if b4.button("🎯 线索效果", width="stretch"):
        st.session_state.menu = "🎯 4. 线索效果"
        st.rerun()
    if b5.button("👥 项目绩效", width="stretch"):
        st.session_state.menu = "👥 5. 项目管理与绩效"
        st.rerun()

    # 最近排名与线索预览
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("最新排名记录")
        rows = conn.execute("SELECT keyword, platform, rank, snap_date FROM ranking_snapshots ORDER BY id DESC LIMIT 8").fetchall()
        if rows:
            st.dataframe(utils.to_df(rows), width="stretch")
        else:
            st.caption("暂无，请到模块3开始监测")
    with col2:
        st.subheader("最新线索")
        rows = conn.execute("SELECT company, country, source_keyword, status, lead_date FROM leads ORDER BY id DESC LIMIT 8").fetchall()
        if rows:
            st.dataframe(utils.to_df(rows), width="stretch")
        else:
            st.caption("暂无，请到模块4录入")
    conn.close()


# ============ 侧边栏：操作人 + 模式开关 + 导航 ============
st.sidebar.title("💡 伟澳新能源 AIO 获客系统")
st.sidebar.caption("户外路灯 · 外贸 B 端 · AI 搜索优化")

# 当前操作人（供操作日志记录）
if "operator" not in st.session_state:
    st.session_state.operator = "A"
st.session_state.operator = st.sidebar.selectbox(
    "👤 当前操作人", ["A", "B"],
    format_func=lambda x: config.ROLES[x]["name"],
    help=utils.HELP["operator"],
)

# 模拟 / 正式业务模式全局开关
if "biz_mode" not in st.session_state:
    st.session_state.biz_mode = "simulate"
st.session_state.biz_mode = st.sidebar.radio(
    "🔧 业务模式", ["simulate", "formal"],
    format_func=lambda x: "模拟模式" if x == "simulate" else "正式业务模式",
    horizontal=True,
    help="模拟模式：字段可留空，方便测试流程；正式业务模式：邮箱/关键词/国家必填",
)

st.sidebar.divider()

menu = st.sidebar.radio(
    "功能模块",
    ["🏠 首页概览", "📝 1. AIO内容生成", "📡 2. 内容分发", "📈 3. 排名监测",
     "🎯 4. 线索效果", "👥 5. 项目管理与绩效"],
    key="menu",
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


if __name__ == "__main__":
    print("请使用命令启动：streamlit run app.py")
