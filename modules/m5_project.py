# -*- coding: utf-8 -*-
"""
m5_project.py — 模块5：项目管理与绩效核算
增强：打卡完成率颜色状态、绩效核算自动统计、阶段看板进度条
"""
from datetime import date, datetime, timedelta
import calendar
import streamlit as st
import db
import config
import utils


def render():
    st.header("👥 模块5 · 项目管理与绩效核算")

    conn = db.get_conn()
    today = date.today().isoformat()
    db.upsert_tasks_for_date(today, conn)

    tab_phase, tab_task, tab_perf, tab_alert = st.tabs(["阶段看板", "每日任务打卡", "绩效核算", "任务预警"])

    # ---- 阶段看板（含进度条） ----
    with tab_phase:
        st.subheader("3个月阶段拆解与进度")
        # 当前累计值
        actual = {
            "内容产出": conn.execute("SELECT COUNT(*) FROM content").fetchone()[0],
            "发布次数": conn.execute("SELECT COUNT(*) FROM publish_log").fetchone()[0],
            "排名监测": conn.execute("SELECT COUNT(*) FROM ranking_snapshots").fetchone()[0],
            "询盘线索": conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
        }
        for m, p in config.PHASES.items():
            with st.expander(f"第{m}个月 · {p['name']}", expanded=(m == 1)):
                st.markdown(f"**目标：** {p['goal']}")
                st.markdown(f"**周度目标：** {p['weekly_target']}")
                goal = config.PHASE_GOALS[m]
                cols = st.columns(4)
                for i, (k, g) in enumerate(goal.items()):
                    a = actual.get(k, 0)
                    ratio = min(1.0, a / g) if g else 0
                    cols[i].metric(k, f"{a}/{g}", f"{int(ratio * 100)}%")
                    cols[i].progress(ratio)
        st.caption("角色分工")
        for r, cfg in config.ROLES.items():
            st.markdown(f"**{cfg['name']}** — {'、'.join(cfg['duties'])}")

    # ---- 每日任务打卡（完成率颜色状态） ----
    with tab_task:
        st.subheader("每日任务打卡")
        d = st.date_input("选择日期", date.today())
        ds = d.isoformat()
        db.upsert_tasks_for_date(ds, conn)

        for role in ["A", "B"]:
            st.markdown(f"### {config.ROLES[role]['name']}")
            tasks = conn.execute("SELECT * FROM tasks WHERE task_date=? AND role=? ORDER BY id", (ds, role)).fetchall()
            for t in tasks:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{t['label']}**（目标 {t['target_qty']}）")
                done = c2.number_input("完成数", 0, 999, t["done_qty"], key=f"done{t['id']}")
                if c3.button("打卡", key=f"ck{t['id']}"):
                    completed = 1 if (t["target_qty"] == 0 or done >= t["target_qty"]) else 0
                    conn.execute("UPDATE tasks SET done_qty=?, completed=? WHERE id=?", (done, completed, t["id"]))
                    conn.execute("INSERT INTO task_checkins (task_id, check_date, qty) VALUES (?,?,?)", (t["id"], ds, done))
                    conn.commit()
                    utils.log(conn, "打卡", "模块5-任务", st.session_state.get("operator", ""),
                              f"{config.ROLES[role]['name']} 打卡：{t['label']} {done}/{t['target_qty']}")
                    st.toast("已打卡 ✅")

        # 当日完成率（颜色状态）
        total_t = conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=?", (ds,)).fetchone()[0]
        done_t = conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=? AND completed=1", (ds,)).fetchone()[0]
        rate = (done_t / total_t * 100) if total_t else 0
        if rate >= 100:
            st.success(f"✅ 当日任务完成率 {rate:.0f}%（{done_t}/{total_t} 项）— 达标")
        elif rate >= 50:
            st.warning(f"⚠️ 当日任务完成率 {rate:.0f}%（{done_t}/{total_t} 项）— 部分完成")
        else:
            st.error(f"🔴 当日任务完成率 {rate:.0f}%（{done_t}/{total_t} 项）— 低完成率")

    # ---- 绩效核算（含自动统计） ----
    with tab_perf:
        st.subheader("绩效核算（每人每月 5000 元）")
        st.caption("40% 每日任务 + 30% 周度目标 + 30% 月度效果，不设固定发放")
        role = st.radio("核算对象", ["A", "B"], format_func=lambda r: config.ROLES[r]["name"], horizontal=True)
        month = st.text_input("核算月份（YYYY-MM）", today[:7])

        # 周期内自动统计
        st.divider()
        st.caption("📊 周期内数据统计（自动）")
        gen_n = conn.execute("SELECT COUNT(*) FROM content WHERE created_at LIKE ?", (month + "%",)).fetchone()[0]
        pub_n = conn.execute("SELECT COUNT(*) FROM publish_log WHERE publish_date LIKE ?", (month + "%",)).fetchone()[0]
        lead_n = conn.execute("SELECT COUNT(*) FROM leads WHERE lead_date LIKE ?", (month + "%",)).fetchone()[0]
        rank_n = conn.execute("SELECT COUNT(*) FROM ranking_snapshots WHERE snap_date LIKE ?", (month + "%",)).fetchone()[0]
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("AIO 生成数", gen_n)
        s2.metric("发布数量", pub_n)
        s3.metric("获取线索数", lead_n)
        s4.metric("排名监测数", rank_n)

        st.divider()
        if st.button("🧮 开始核算", type="primary"):
            result = calc_performance(conn, role, month)
            _show_perf_result(result)
            if st.button("💾 保存本次核算结果"):
                conn.execute(
                    "INSERT INTO performance (period, period_type, role, daily_score, weekly_score, monthly_score, bonus, penalty, note) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (month, "monthly", role, result["daily_rate"], result["weekly_rate"], result["monthly_rate"],
                     result["bonus"], result["penalty"], result["note"])
                )
                conn.commit()
                utils.log(conn, "新增", "模块5-绩效", st.session_state.get("operator", ""),
                          f"核算 {config.ROLES[role]['name']} {month}：{result['bonus']} 元")
                st.toast("核算结果已保存 ✅")

    # ---- 任务预警 ----
    with tab_alert:
        st.subheader("任务预警")
        st.caption("当日未完成自动提醒；连续3天未完成触发额外扣减（第4天起每天额外扣 100 元）")
        for role in ["A", "B"]:
            miss_days = _consecutive_miss(conn, role)
            name = config.ROLES[role]["name"]
            if miss_days >= 3:
                st.error(f"🚨 {name}：已连续 {miss_days} 天未完成当日任务，触发额外扣减")
            elif miss_days > 0:
                st.warning(f"⚠️ {name}：连续 {miss_days} 天未完成，再 {3 - miss_days} 天将触发扣减")
            else:
                st.success(f"✅ {name}：今日任务正常")

        st.divider()
        st.caption("今日未完成任务")
        pending = conn.execute("SELECT * FROM tasks WHERE task_date=? AND completed=0 ORDER BY role", (today,)).fetchall()
        if pending:
            st.dataframe(utils.to_df([{"角色": config.ROLES[r["role"]]["name"], "任务": r["label"], "目标": r["target_qty"], "已完成": r["done_qty"]} for r in pending]), width="stretch")
        else:
            st.success("今日任务已全部完成")

    conn.close()


# ============ 绩效核算核心逻辑（原有，保持不变） ============

def _consecutive_miss(conn, role):
    """计算该角色连续未完成天数（从今天往前）。"""
    d = date.today()
    miss = 0
    for _ in range(90):
        ds = d.isoformat()
        total = conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=? AND role=?", (ds, role)).fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=? AND role=? AND completed=1", (ds, role)).fetchone()[0]
        if total == 0:
            break
        if done < total:
            miss += 1
        else:
            break
        d -= timedelta(days=1)
    return miss


def calc_performance(conn, role, month):
    """核算某角色某月绩效。返回 dict。"""
    year, mon = int(month[:4]), int(month[5:7])
    days_in_month = calendar.monthrange(year, mon)[1]
    base = config.PERF_RULES["monthly_bonus"]
    daily_pool = base * config.PERF_RULES["daily_weight"]
    weekly_pool = base * config.PERF_RULES["weekly_weight"]
    monthly_pool = base * config.PERF_RULES["monthly_weight"]

    daily_earned = 0.0
    daily_done_days = 0
    for day in range(1, days_in_month + 1):
        ds = f"{month}-{day:02d}"
        total = conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=? AND role=?", (ds, role)).fetchone()[0]
        if total == 0:
            continue
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=? AND role=? AND completed=1", (ds, role)).fetchone()[0]
        daily_earned += (daily_pool / days_in_month) * (done / total)
        if done >= total:
            daily_done_days += 1
    daily_rate = daily_earned / daily_pool * 100 if daily_pool else 0

    weekly_rate = _calc_weekly(conn, role, month)
    monthly_rate = _calc_monthly(conn, role, month)

    miss = _consecutive_miss(conn, role)
    penalty = 0.0
    if miss >= config.PERF_RULES["consecutive_miss_penalty"]:
        extra = miss - config.PERF_RULES["consecutive_miss_penalty"] + 1
        penalty = extra * config.PERF_RULES["extra_penalty_per_day"]

    bonus = daily_earned + weekly_pool * (weekly_rate / 100) + monthly_pool * (monthly_rate / 100) - penalty
    bonus = max(0.0, round(bonus, 2))

    note = (f"每日部分 {daily_earned:.0f}元 | 周度达成率 {weekly_rate:.0f}% | 月度达成率 {monthly_rate:.0f}% | "
            f"连续未完成 {miss} 天（扣 {penalty:.0f} 元）")

    return {
        "role": role, "month": month,
        "daily_rate": round(daily_rate, 1), "daily_earned": round(daily_earned, 1),
        "weekly_rate": round(weekly_rate, 1), "weekly_earned": round(weekly_pool * weekly_rate / 100, 1),
        "monthly_rate": round(monthly_rate, 1), "monthly_earned": round(monthly_pool * monthly_rate / 100, 1),
        "penalty": round(penalty, 1), "bonus": bonus, "note": note,
    }


def _calc_weekly(conn, role, month):
    """周度达成率：按内容产出量(角色A) / 排名监测量(角色B) 统计。"""
    mon = int(month[5:7])
    if role == "A":
        weekly_target = {1: 40, 2: 60, 3: 50}.get(mon, 40)
        actual = conn.execute("SELECT COUNT(*) FROM content WHERE created_at LIKE ?", (month + "%",)).fetchone()[0]
    else:
        weekly_target = {1: 30, 2: 50, 3: 40}.get(mon, 30)
        actual = conn.execute("SELECT COUNT(*) FROM ranking_snapshots WHERE snap_date LIKE ?", (month + "%",)).fetchone()[0]
    weeks = 4
    target = weekly_target * weeks
    rate = (actual / target * 100) if target else 0
    return min(150, rate)


def _calc_monthly(conn, role, month):
    """月度效果：核心词排名达标率(50%) + 询盘增量(50%)。"""
    ranked = conn.execute("SELECT COUNT(*) FROM ranking_snapshots WHERE snap_date LIKE ?", (month + "%",)).fetchone()[0]
    hit = conn.execute("SELECT COUNT(*) FROM ranking_snapshots WHERE snap_date LIKE ? AND rank>0 AND rank<=3", (month + "%",)).fetchone()[0]
    rank_rate = (hit / ranked * 100) if ranked else 0

    leads = conn.execute("SELECT COUNT(*) FROM leads WHERE lead_date LIKE ?", (month + "%",)).fetchone()[0]
    lead_target = 20
    lead_rate = (leads / lead_target * 100) if lead_target else 0

    return (rank_rate * 0.5 + min(150, lead_rate) * 0.5)


def _show_perf_result(r):
    st.success(f"### {config.ROLES[r['role']]['name']} · {r['month']} 绩效核算结果")
    c1, c2, c3 = st.columns(3)
    c1.metric("每日任务 (40%)", f"{r['daily_earned']} 元", f"完成率 {r['daily_rate']}%")
    c2.metric("周度目标 (30%)", f"{r['weekly_earned']} 元", f"达成率 {r['weekly_rate']}%")
    c3.metric("月度效果 (30%)", f"{r['monthly_earned']} 元", f"达成率 {r['monthly_rate']}%")
    p1, p2 = st.columns(2)
    p1.metric("⚠️ 连续未完成扣减", f"-{r['penalty']} 元")
    p2.metric("💰 本月实发绩效", f"{r['bonus']} 元")
    st.caption(r["note"])
