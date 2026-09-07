# -*- coding: utf-8 -*-
"""
db.py — SQLite 数据库层
负责建表、连接、初始数据种子（默认关键词库 + 默认渠道）。
"""
import sqlite3
import os
import json
from datetime import datetime, date
import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    kw_type TEXT DEFAULT 'core',          -- core / longtail
    category TEXT DEFAULT '',             -- 品类/场景分类
    scene TEXT DEFAULT '',                -- 场景 key
    status TEXT DEFAULT 'active',         -- active / archived
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    keyword_id INTEGER,
    content_type TEXT DEFAULT 'product',  -- product / scene / faq / guide / install
    scene TEXT DEFAULT '',
    body_md TEXT,
    body_html TEXT,
    json_ld TEXT,
    keyword TEXT,
    status TEXT DEFAULT 'draft',          -- draft / published
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    ch_type TEXT DEFAULT 'website',       -- website / gmb / directory / social
    url TEXT DEFAULT '',
    note TEXT DEFAULT '',
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS publish_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER,
    channel_id INTEGER,
    keyword TEXT,
    publish_date TEXT,
    url TEXT DEFAULT '',
    status TEXT DEFAULT 'published'
);

CREATE TABLE IF NOT EXISTS ranking_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER,
    keyword TEXT,
    platform TEXT,                        -- ChatGPT / Bing AI (Copilot) / Google SGE
    snap_date TEXT,                       -- YYYY-MM-DD
    rank INTEGER,                         -- 我方出现位次，0=未出现
    mention_text TEXT DEFAULT '',         -- AI 推荐话术
    source_url TEXT DEFAULT '',           -- AI 引用来源
    note TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT DEFAULT '',
    contact TEXT DEFAULT '',
    email TEXT DEFAULT '',
    whatsapp TEXT DEFAULT '',
    country TEXT DEFAULT '',
    source_keyword TEXT DEFAULT '',
    platform TEXT DEFAULT '',
    content_type TEXT DEFAULT '',
    inquiry TEXT DEFAULT '',
    status TEXT DEFAULT 'new',            -- new / contacted / quoted / won / lost
    lead_date TEXT DEFAULT (date('now')),
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_date TEXT,                       -- YYYY-MM-DD
    role TEXT,                            -- A / B
    task_type TEXT,
    label TEXT,
    target_qty INTEGER DEFAULT 0,
    done_qty INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    note TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS task_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    check_date TEXT,
    qty INTEGER DEFAULT 0,
    note TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT,                          -- YYYY-MM (月) 或 YYYY-Wxx (周)
    period_type TEXT,                     -- daily / weekly / monthly
    role TEXT,
    user_name TEXT DEFAULT '',
    daily_score REAL DEFAULT 0,
    weekly_score REAL DEFAULT 0,
    monthly_score REAL DEFAULT 0,
    bonus REAL DEFAULT 0,
    penalty REAL DEFAULT 0,
    note TEXT DEFAULT '',
    calc_date TEXT DEFAULT (datetime('now','localtime'))
);
"""


def get_conn():
    """获取数据库连接（开启行工厂）。"""
    conn = sqlite3.connect(config.DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建表 + 首次运行时种子数据。"""
    conn = get_conn()
    # WAL 模式持久化在数据库文件里，只需设置一次（避免每次连接重复执行 PRAGMA 引发锁冲突）
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except sqlite3.OperationalError:
        pass
    conn.executescript(SCHEMA)
    conn.commit()

    # 种子：默认关键词库
    cur = conn.execute("SELECT COUNT(*) FROM keywords")
    if cur.fetchone()[0] == 0:
        for kw in config.CORE_KEYWORDS:
            scene = _detect_scene(kw)
            conn.execute(
                "INSERT OR IGNORE INTO keywords (keyword, kw_type, scene) VALUES (?,?,?)",
                (kw, "core", scene)
            )
        conn.commit()

    # 种子：默认渠道
    cur = conn.execute("SELECT COUNT(*) FROM channels")
    if cur.fetchone()[0] == 0:
        for ch in config.DEFAULT_CHANNELS:
            conn.execute(
                "INSERT INTO channels (name, ch_type, url, note) VALUES (?,?,?,?)",
                (ch["name"], ch["type"], ch["url"], ch["note"])
            )
        conn.commit()

    conn.close()


def _detect_scene(kw: str) -> str:
    """根据关键词自动识别场景。"""
    mapping = {
        "parking": "parking_lot",
        "industrial": "industrial_park",
        "rural": "rural_road",
        "village": "rural_road",
        "road": "rural_road",
        "municipal": "municipal",
        "residential": "residential",
        "highway": "highway",
    }
    for k, v in mapping.items():
        if k in kw:
            return v
    return ""


def add_keyword(keyword, kw_type="longtail", scene=""):
    """新增关键词，返回 id。"""
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO keywords (keyword, kw_type, scene) VALUES (?,?,?)",
        (keyword.strip(), kw_type, scene)
    )
    conn.commit()
    row = conn.execute("SELECT id FROM keywords WHERE keyword=?", (keyword.strip(),)).fetchone()
    conn.close()
    return row["id"] if row else None


def upsert_tasks_for_date(d: str, conn=None):
    """为指定日期生成 2 人每日任务（若不存在）。
    可传入已有连接 conn 以共享连接，避免多连接写冲突（SQLite 单写锁）。
    """
    own = conn is None
    if own:
        conn = get_conn()
    for role, cfg in config.ROLES.items():
        for t in cfg["daily_tasks"]:
            exists = conn.execute(
                "SELECT id FROM tasks WHERE task_date=? AND role=? AND task_type=?",
                (d, role, t["task_type"])
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO tasks (task_date, role, task_type, label, target_qty, done_qty, completed) "
                    "VALUES (?,?,?,?,?,0,0)",
                    (d, role, t["task_type"], t["label"], t["qty"])
                )
    if own:
        conn.commit()
        conn.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成:", config.DB_PATH)
    print("关键词数:", end=" ")
    conn = get_conn()
    print(conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0])
    print("渠道数:", conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0])
    conn.close()
