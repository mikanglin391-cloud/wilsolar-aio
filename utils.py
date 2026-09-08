# -*- coding: utf-8 -*-
"""
utils.py — 全局工具：URL 校验、Excel 导出、一键复制、操作日志、帮助提示
"""
import io
import re
import pandas as pd
import streamlit as st
import db


def validate_url(url):
    """校验 URL 格式。返回 (是否合法, 错误信息)。空值视为合法（可选字段）。"""
    if not url or not url.strip():
        return True, ""
    pattern = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
    if pattern.match(url.strip()):
        return True, ""
    return False, "URL 格式不正确，需以 http:// 或 https:// 开头"


def validate_email(email):
    """校验邮箱格式（宽松）。空值返回 True（可选字段由调用方决定必填）。"""
    if not email or not email.strip():
        return True, ""
    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    return (True, "") if pattern.match(email.strip()) else (False, "邮箱格式不正确")


def ascii_filename(name):
    """把文件名转成 ASCII 安全（去除非 ASCII 字符）。
    Windows 下 Streamlit 的 download_button 对中文文件名会抛 OSError [Errno 22]。"""
    cleaned = re.sub(r"[^\w\-.]", "_", name, flags=re.ASCII)
    cleaned = cleaned.strip("_.")
    return cleaned if cleaned else "download"


def export_excel(df, filename, label="📥 导出 Excel"):
    """把 pandas DataFrame 导出为 Excel 下载按钮。"""
    filename = ascii_filename(filename)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    return st.download_button(
        label, buf.getvalue(), file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def to_df(rows):
    """把 sqlite Row 列表转成 pandas DataFrame（空列表返回空 DataFrame）。"""
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


def highlight_rank(df, col="rank"):
    """给 rank 列值 >= 1 的行加绿色背景高亮（rank>=1 表示 AI 已出现我方品牌）。
    返回 pandas Styler，可直接传给 st.dataframe / st.table。"""
    if df.empty or col not in df.columns:
        return df

    def _style(row):
        try:
            v = row[col]
        except Exception:
            return [""] * len(row)
        if v is not None and v >= 1:
            return ["background-color: #d4edda;"] * len(row)
        return [""] * len(row)

    return df.style.apply(_style, axis=1)


def copy_block(text, caption="点击右上角复制按钮", language="text"):
    """用 st.code 展示文本（自带复制按钮），满足「一键复制」需求。"""
    st.caption(caption)
    st.code(text, language=language)


def log(conn, action, module, operator="", detail=""):
    """记录操作日志。"""
    try:
        db.log_action(conn, action, module, operator, detail)
    except Exception:
        pass  # 日志失败不影响主流程


# ============ 帮助提示文本（输入框 help= 参数引用） ============
HELP = {
    "keyword": "目标关键词：AI 搜索里客户会搜的词，如 100W solar street light for industrial park",
    "scene": "应用场景：决定内容命中的采购场景（停车场/厂区/乡村道路/市政/住宅/公路）",
    "wattage": "产品功率：5W–200W",
    "url": "发布 URL：产品页链接，需以 http:// 或 https:// 开头（留空或模拟链接会自动标记为「模拟记录」）",
    "operator": "当前操作人：谁在操作系统（角色A内容运营 / 角色B数据运营）",
    "company": "客户公司名：正式业务模式必填，模拟模式可留空",
    "email": "客户邮箱：正式业务模式必填，格式如 name@domain.com",
    "country": "客户国家：正式业务模式必填，如 Nigeria / UAE / Philippines",
    "source_keyword": "来源关键词：客户通过哪个关键词找到你（AI 搜索推荐时，AI 平台会给出）",
    "rank": "我方出现位次：0=AI 没提我方；1=第一位推荐；≥1 表示 AI 已出现我方品牌",
}
