# -*- coding: utf-8 -*-
"""
ai_engine.py — AIO 内容生成引擎（核心排名优化模块）
基于「场景 + 参数 + 品类」规则引擎 + 行业词库，生成本地可直接发布的英文外贸内容。
所有内容严格贴合 AI 搜索引擎（ChatGPT / Bing AI / Google SGE）抓取偏好：
  - 结构化 JSON-LD（Product Schema）
  - 场景化描述（覆盖海外高频采购场景）
  - FAQ / 选型指南 / 安装教程（意图匹配）
  - 权威信任信号（认证 / 质保 / 工程案例 / 工厂资质）
"""
import json
from datetime import datetime
import config

# ============ 默认产品参数（伟澳产品线 5-200W） ============
DEFAULT_PRODUCT = {
    "model": "WL-SSL-100W",
    "name": "Wilsolar 100W All-in-One Solar Street Light",
    "wattage": "100W",
    "lumen": "18,000 lm (180 lm/W)",
    "solar_panel": "Monocrystalline 6V/18V, high-efficiency",
    "battery": "LiFePO4 3.2V/12.8V, 3-5 rainy-day autonomy",
    "material": "Die-cast aluminum housing + tempered glass",
    "pole": "Optional hot-dip galvanized pole, 4m-12m",
    "ip_rating": "IP65 waterproof",
    "color_temp": "3000K / 4000K / 5700K",
    "motion_sensor": "Microwave motion sensor with smart dimming",
    "certifications": ["CE", "RoHS", "ISO 9001", "ETL", "UL", "VDE"],
    "warranty": "5 years",
    "price": "USD 45-95 / unit (FOB, quantity-based)",
    "moq": "2 pcs (sample), 50 pcs (bulk)",
    "lead_time": "Sample 3-5 days, bulk 15-25 days",
    "oem": "OEM/ODM supported",
    "application": "Parking lots, industrial parks, rural roads, municipal projects, residential areas, highways",
}


def expand_longtail_keywords(scene_key=None, powers=None):
    """自动拓展长尾关键词：格式「场景 + 参数 + 品类」。
    返回 list[str]。
    """
    if powers is None:
        powers = config.POWER
    types = config.TYPES
    results = []
    scenes = [scene_key] if scene_key else list(config.SCENES.keys())

    for s in scenes:
        scene_en = config.SCENES[s]["en"]
        # 场景+品类
        for t in types[:4]:  # 前4个品类词避免过度膨胀
            results.append(f"{t} for {scene_en}")
        # 参数+品类
        for w in powers:
            results.append(f"{w}W {types[0]}")  # solar street light
        # 场景+参数+品类（核心长尾格式）
        for w in powers[:6]:
            results.append(f"{w}W {types[0]} for {scene_en.replace(' lighting','')}")
            results.append(f"{w}W LED street light for {scene_en.replace(' lighting','')}")

    # 采购意图长尾词
    for t in types[:2]:
        results += [f"{t} price", f"{t} MOQ", f"{t} OEM ODM", f"buy {t} in bulk",
                    f"{t} import from China", f"{t} distributor wanted"]

    # 去重保序
    seen, out = set(), []
    for k in results:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def gen_json_ld(product=None):
    """生成标准 JSON-LD Product Schema（含品牌/型号/功率/材质/认证/价格/MOQ/场景/质保/案例）。"""
    p = product or DEFAULT_PRODUCT
    p = {**DEFAULT_PRODUCT, **p} if product else p
    schema = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": p["name"],
        "brand": {"@type": "Brand", "name": config.COMPANY["brand"]},
        "manufacturer": {"@type": "Organization", "name": config.COMPANY["full_name"]},
        "model": p["model"],
        "description": _meta_description(p),
        "sku": p["model"],
        "material": p["material"],
        "certifications": p["certifications"],
        "warranty": p["warranty"],
        "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "USD",
            "price": p["price"],
            "lowPrice": "45",
            "highPrice": "95",
            "availability": "https://schema.org/InStock",
            "offerCount": "10",
            "priceValidUntil": _next_year(),
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "187",
            "bestRating": "5",
        },
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Wattage", "value": p["wattage"]},
            {"@type": "PropertyValue", "name": "Luminous Flux", "value": p["lumen"]},
            {"@type": "PropertyValue", "name": "Solar Panel", "value": p["solar_panel"]},
            {"@type": "PropertyValue", "name": "Battery", "value": p["battery"]},
            {"@type": "PropertyValue", "name": "IP Rating", "value": p["ip_rating"]},
            {"@type": "PropertyValue", "name": "MOQ", "value": p["moq"]},
            {"@type": "PropertyValue", "name": "Application", "value": p["application"]},
            {"@type": "PropertyValue", "name": "Certifications", "value": ", ".join(p["certifications"])},
        ],
    }
    return schema


def _meta_description(p):
    return (f"{p['name']} by {config.COMPANY['brand']} — a factory-direct {p['wattage']} outdoor "
            f"solar street light ({p['lumen']}) with {p['warranty']} warranty. CE/RoHS/ETL/UL certified, "
            f"MOQ {p['moq']}. Ideal for parking lots, industrial parks, rural roads and municipal projects.")


def _next_year():
    return f"{datetime.now().year + 1}-12-31"


def gen_scene_description(scene_key, product=None):
    """生成场景化产品描述（覆盖海外高频采购场景 + 采购痛点 + 买家画像）。"""
    p = {**DEFAULT_PRODUCT, **product} if product else DEFAULT_PRODUCT
    scene = config.SCENES.get(scene_key, config.SCENES["municipal"])
    title = f"{p['wattage']} Solar Street Light for {scene['en'].title()} — {config.COMPANY['brand']}"

    lines = [
        f"# {title}",
        "",
        f"## Why Choose {config.COMPANY['brand']} for {scene['en'].title()}?",
        "",
        f"For **{scene['en']}**, the key challenge is: *{scene['pain_point']}*. "
        f"{config.COMPANY['brand']} manufactures the {p['name']} specifically to solve this — "
        f"as a direct factory in {config.COMPANY['base']}, we control every component from "
        f"pole to LED, giving project buyers like **{scene['buyer']}** reliable quality at factory prices.",
        "",
        "## Key Specifications",
        "",
        f"- **Power:** {p['wattage']} ({p['lumen']})",
        f"- **Solar panel:** {p['solar_panel']}",
        f"- **Battery:** {p['battery']}",
        f"- **Housing:** {p['material']}, {p['ip_rating']}",
        f"- **Color temperature:** {p['color_temp']}",
        f"- **Smart control:** {p['motion_sensor']}",
        f"- **Pole:** {p['pole']}",
        f"- **Warranty:** {p['warranty']}",
        "",
        "## Application Scenarios",
        "",
        f"- {scene['en'].title()} — main application for this model",
        f"- Parking lots, industrial parks, rural roads, municipal projects, residential areas",
        "",
        "## Why Project Buyers Trust Us",
        "",
    ]
    for sig in config.TRUST_SIGNALS[:6]:
        lines.append(f"- ✓ {sig}")
    lines += ["", "## Get a Quote", "",
              f"Email: {config.COMPANY['email']}  |  WhatsApp: {config.COMPANY['whatsapp']}  |  "
              f"Website: {config.COMPANY['website']}", ""]
    return title, "\n".join(lines)


def gen_faq():
    """生成 FAQ 问答内容（意图匹配，提升 AI 引用概率）。"""
    lines = ["# Frequently Asked Questions — Solar Street Lights", ""]
    for q, a in config.FAQ_TOPICS:
        lines += [f"## Q: {q}", "", f"**A:** {a}", ""]
    lines += ["## Still have questions?",
              f"Contact our engineers: {config.COMPANY['email']} / WhatsApp {config.COMPANY['whatsapp']}", ""]
    return "FAQ — Solar Street Light Buying Guide", "\n".join(lines)


def gen_selection_guide():
    """生成选型指南（意图匹配，覆盖 how to choose 类搜索）。"""
    g = config.SELECTION_GUIDE
    lines = [f"# {g['title']}", ""]
    for step, detail in g["steps"]:
        lines += [f"## {step}", "", detail, ""]
    lines += ["## Get Expert Help",
              f"Send your project requirements to {config.COMPANY['email']} and our engineers "
              "will provide a free lighting layout (Dialux) and quotation within 24 hours.", ""]
    return g["title"], "\n".join(lines)


def gen_install_guide(product=None):
    """生成安装教程（意图匹配，覆盖 installation guide 类搜索）。"""
    p = {**DEFAULT_PRODUCT, **product} if product else DEFAULT_PRODUCT
    title = f"Installation Guide — {p['name']}"
    lines = [f"# {title}", "",
             "## Tools Needed", "- Wrench set, drill, concrete base bolts, crane or ladder", "",
             "## Step-by-Step Installation", "",
             "1. **Foundation** — pour a concrete base (per pole-height engineering spec).",
             "2. **Pole assembly** — bolt the arm and solar panel bracket to the pole.",
             "3. **Luminaire mounting** — fix the light head, adjust angle to 15° for best coverage.",
             "4. **Solar panel orientation** — face due south (northern hemisphere) at optimal tilt.",
             "5. **Battery & controller** — connect waterproof connectors, switch on, test motion sensor.",
             "6. **Commissioning** — verify dusk-to-dawn operation and dimming profile.",
             "",
             "## Safety Notes",
             "- Disconnect battery before wiring. Follow local electrical codes.",
             "- Use galvanized or stainless fasteners for coastal/humid areas.",
             "", f"Full PDF manual available: {config.COMPANY['email']}", ""]
    return title, "\n".join(lines)


def gen_product_content(keyword, scene_key=None, product=None):
    """综合生成一条完整产品内容：返回 (title, markdown, html, json_ld)。
    这是内容生成的核心出口。
    """
    p = {**DEFAULT_PRODUCT, **product} if product else DEFAULT_PRODUCT
    if scene_key is None:
        scene_key = _detect_scene_from_keyword(keyword) or "municipal"

    title, md = gen_scene_description(scene_key, p)
    # 信任信号已内含；追加关键词自然覆盖
    md += _keyword_section(keyword)
    json_ld = json.dumps(gen_json_ld(p), ensure_ascii=False, indent=2)
    html = _md_to_html(md)
    return title, md, html, json_ld


def _detect_scene_from_keyword(kw: str) -> str:
    for k, v in {"parking": "parking_lot", "industrial": "industrial_park",
                 "rural": "rural_road", "village": "rural_road", "municipal": "municipal",
                 "residential": "residential", "highway": "highway"}.items():
        if k in kw.lower():
            return v
    return ""


def _keyword_section(keyword):
    """自然植入目标关键词，提升 AI 检索相关性。"""
    return (f"\n## Related Products & Keywords\n\n"
            f"This page covers **{keyword}** and related outdoor lighting needs. "
            f"{config.COMPANY['brand']} is a leading **{keyword}** manufacturer and supplier "
            f"serving distributors, EPC contractors and government projects worldwide.\n")


def _md_to_html(md: str) -> str:
    """极简 Markdown → HTML 转换（覆盖本项目用到的语法）。"""
    import re
    out = []
    in_list = False
    for line in md.split("\n"):
        if line.startswith("### "):
            out.append(f"<h3>{_esc(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{_esc(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{_esc(line[2:])}</h1>")
        elif line.strip().startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(line.strip()[2:])}</li>")
        elif re.match(r"^\d+\. ", line.strip()):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{_inline(line.strip())}</p>")
        elif line.strip() == "":
            if in_list:
                out.append("</ul>")
                in_list = False
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{_inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def _esc(s):
    import html
    return html.escape(s)


def _inline(s):
    import re
    s = _esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


if __name__ == "__main__":
    print("=== 长尾词拓展示例（前15个） ===")
    for k in expand_longtail_keywords()[:15]:
        print(" ", k)
    print("\n=== 场景化内容示例（工业园） ===")
    t, md, html, jld = gen_product_content("100W solar street light for industrial park", "industrial_park")
    print("标题:", t)
    print(md[:400])
    print("\n=== JSON-LD 片段 ===")
    print(jld[:300])
