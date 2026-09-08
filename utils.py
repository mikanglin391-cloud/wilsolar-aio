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
    # 产品参数
    "model": "产品型号：如 WL-SSL-100W，用于 JSON-LD 结构化标记",
    "lumen": "光通量：如 18,000 lm（180 lm/W）",
    "battery": "电池规格：如 LiFePO4 3.2V/12.8V，含阴雨天续航天数",
    "warranty": "质保年限：如 5 years",
    "price": "价格区间：如 USD 45-95 / unit（FOB，按量浮动）",
    "moq": "最小起订量：如 2 pcs（样品）/ 50 pcs（批量）",
    # 渠道
    "channel_name": "渠道名称：如 独立站官网、Google 商家档案、行业目录站",
    "channel_type": "渠道类型：website=官网 / gmb=Google商家 / directory=目录站 / social=社媒",
    "channel_url": "渠道主页地址，可留空",
    # 排名监测
    "source_url": "AI 引用来源 URL：AI 回答里引用了我方哪个页面的链接（选填）",
    "mention": "AI 推荐话术：AI 提到我方品牌时的原话，用于分析 AI 引用内容",
    # 线索
    "contact": "客户联系人姓名",
    "whatsapp": "客户 WhatsApp 号码（含国家区号，如 +63）",
    "platform": "客户从哪个 AI 平台找到你（ChatGPT/Bing/Google SGE 等）",
    "content_type": "客户看到的内容类型（产品页/场景页/FAQ 等），用于统计哪类内容转化好",
    "inquiry": "客户询盘的具体内容（要什么产品、数量、目标市场等）",
}
