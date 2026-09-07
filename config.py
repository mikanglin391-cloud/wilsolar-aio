# -*- coding: utf-8 -*-
"""
config.py — 全局配置与行业词库
户外路灯外贸 AIO 获客系统
公司：伟澳新能源（Wilsolar）
"""
import os

# ============ 路径配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORT_DIR = os.path.join(BASE_DIR, "export")
DB_PATH = os.path.join(DATA_DIR, "aio_lighting.db")

for _d in (DATA_DIR, EXPORT_DIR):
    os.makedirs(_d, exist_ok=True)

# ============ 公司/品牌信息（植入所有内容） ============
COMPANY = {
    "brand": "Wilsolar",
    "full_name": "Zhongshan Wei'ao New Energy Optoelectronic Co., Ltd.",
    "short_name": "Wei'ao New Energy",
    "city": "Zhongshan, Guangdong, China",
    "base": "Guzhen Town, Zhongshan (China Lighting Capital)",
    "founded": 2010,
    "website": "https://www.wilsolar.com",
    "email": "info@wilsolar.com",
    "whatsapp": "+86 13726103985",
    "product_range": "5W – 200W",
    "product_range_note": "5W to 200W LED / solar / AC street lights",
}

# ============ 认证与信任信号 ============
CERTIFICATIONS = ["CE", "RoHS", "ISO 9001", "ETL", "UL", "VDE"]

TRUST_SIGNALS = [
    "Direct factory since 2010 — no middlemen, OEM/ODM welcome",
    "In-house production of light poles, solar panels, batteries and LED luminaires",
    f"Full certification: {', '.join(CERTIFICATIONS)}",
    "5-year warranty on LED luminaires, 3-year on batteries",
    "200+ completed municipal & commercial projects across Africa, Middle East, Southeast Asia",
    "Located in Guzhen, Zhongshan — China's largest lighting manufacturing hub",
    "Free lighting layout (Dialux) & installation support for project buyers",
    "Strict QC: 100% aging test before shipment",
    "MOQ as low as 2 pcs for samples, bulk from 50 pcs",
    "Dedicated English-speaking project engineer for every order",
]

# ============ 应用场景库（海外高频采购场景） ============
SCENES = {
    "parking_lot": {
        "en": "parking lot lighting",
        "zh": "停车场",
        "pain_point": "24/7 security visibility, low maintenance, motion-sensing dimming",
        "buyer": "commercial real estate, shopping malls, logistics centers",
    },
    "industrial_park": {
        "en": "industrial park lighting",
        "zh": "厂区/工业园",
        "pain_point": "high-brightness for safety, dust/water resistance, long lifespan",
        "buyer": "factories, industrial park developers, EPC contractors",
    },
    "rural_road": {
        "en": "rural road lighting",
        "zh": "乡村道路",
        "pain_point": "off-grid solar, no trenching, low total cost of ownership",
        "buyer": "governments, NGOs, rural electrification projects",
    },
    "municipal": {
        "en": "municipal street lighting",
        "zh": "市政工程",
        "pain_point": "standard compliance, smart control, bulk supply reliability",
        "buyer": "municipalities, EPC contractors, utility companies",
    },
    "residential": {
        "en": "residential community lighting",
        "zh": "住宅小区",
        "pain_point": "aesthetic design, glare control, energy saving",
        "buyer": "real estate developers, property management",
    },
    "highway": {
        "en": "highway lighting",
        "zh": "公路/高速",
        "pain_point": "high wattage, wide spacing, vibration resistance",
        "buyer": "highway authorities, infrastructure contractors",
    },
}

# ============ 参数维度（用于长尾词拓展） ============
POWER = [30, 50, 60, 80, 100, 120, 150, 200]  # 单位 W
TYPES = ["solar street light", "LED street light", "solar powered street light",
         "all in one solar street light", "integrated solar street light",
         "commercial LED street light", "outdoor lighting"]

# ============ 核心关键词库（内置50个，含核心词+长尾词） ============
CORE_KEYWORDS = [
    # 品类核心词
    "solar street light", "LED street light", "solar street light manufacturer",
    "solar street light supplier", "outdoor solar lights", "commercial street lighting",
    "solar road light", "integrated solar street light", "all in one solar street light",
    "solar street light factory", "solar street light wholesale",
    # 场景词
    "solar street light for parking lot", "solar street light for industrial park",
    "solar street light for rural road", "solar street light for residential area",
    "LED street light for municipal project", "solar street light for highway",
    "solar parking lot lights", "solar street lights for village",
    # 参数+品类长尾词
    "100W solar street light", "200W LED street light", "60W solar street light",
    "150W solar street light", "50W solar street light", "120W solar street light",
    "100W solar street light for industrial park", "200W solar street light price",
    # 采购意图词
    "solar street light price", "solar street light MOQ", "solar street light OEM",
    "solar street light ODM", "buy solar street light in bulk",
    "solar street light import from China", "solar street light distributor wanted",
    "solar street light agent wanted", "street light project quotation",
    "solar street light tender", "solar street light with pole and battery",
    "solar street light CE ROHS", "solar street light ETL listed",
    "solar street light warranty", "solar street light installation guide",
    "solar street light vs LED street light", "how to choose solar street light",
    "best solar street light brand", "top solar street light manufacturers China",
    "solar street light for Africa project", "solar street light for Middle East",
    "solar street light for Southeast Asia", "solar street light with motion sensor",
]

# ============ FAQ 模板主题 ============
FAQ_TOPICS = [
    ("What is the lifespan of a Wilsolar solar street light?",
     "The LED luminaire is rated for 50,000+ hours and carries a 5-year warranty. The lithium battery lasts 3-5 years depending on depth of discharge, with a 3-year warranty."),
    ("How long do solar street lights work on a cloudy day?",
     "Our systems are engineered for 3-5 rainy/cloudy days of autonomy. We size the solar panel and battery based on your local peak-sun-hours so the light keeps running through bad weather."),
    ("Can I get a sample before bulk order?",
     "Yes. MOQ for samples is 2 pcs. We also provide a full lighting layout (Dialux) and datasheet so you can evaluate performance before committing."),
    ("Do you support OEM / ODM and custom pole heights?",
     "Yes. We manufacture poles, panels, batteries and luminaires in-house, so we can customize wattage, pole height (4m-12m), color temperature, and brand your logo."),
    ("What certifications do your street lights have?",
     "CE, RoHS, ISO 9001, ETL, UL and VDE. We provide certificates with every shipment for customs and project compliance."),
    ("What is the lead time for a bulk order?",
     "Samples ship in 3-5 days. Bulk orders (50-500 pcs) typically ship in 15-25 days depending on quantity and customization."),
]

# ============ 选型指南要点 ============
SELECTION_GUIDE = {
    "title": "How to Choose the Right Solar Street Light for Your Project",
    "steps": [
        ("1. Determine required brightness (lumen)", "Match wattage to road width and pole height. 30-60W for residential, 80-120W for main roads, 150-200W for highways."),
        ("2. Check local peak-sun-hours", "This decides solar panel size and battery capacity for reliable night-time autonomy."),
        ("3. Confirm pole height & spacing", "Typical: 4-6m for residential, 6-8m for secondary roads, 8-12m for main roads."),
        ("4. Match certifications to project", "EU projects need CE/RoHS, North America needs ETL/UL. Ask for certificates upfront."),
        ("5. Verify warranty & support", "Look for 5-year luminaire warranty and a supplier who provides installation support."),
    ],
}

# ============ 发布渠道默认值 ============
DEFAULT_CHANNELS = [
    {"name": "独立站官网 (wilsolar.com)", "type": "website", "url": "https://www.wilsolar.com", "note": "WordPress"},
    {"name": "Google 商家档案 (Google Business Profile)", "type": "gmb", "url": "", "note": "发布产品帖子+FAQ"},
    {"name": "行业目录站 (Alibaba/GlobalSources/TradeKey)", "type": "directory", "url": "", "note": "产品详情页"},
    {"name": "LinkedIn 公司主页", "type": "social", "url": "", "note": "长文+文档分享"},
]

# ============ 监测平台 ============
PLATFORMS = ["ChatGPT", "Bing AI (Copilot)", "Google SGE (AI Overview)"]

# ============ 绩效规则常量 ============
PERF_RULES = {
    "monthly_bonus": 5000,           # 每人每月绩效基数（元）
    "daily_weight": 0.40,            # 每日任务完成度 40% = 2000元
    "weekly_weight": 0.30,           # 周度阶段目标 30% = 1500元
    "monthly_weight": 0.30,          # 月度效果指标 30% = 1500元
    "consecutive_miss_penalty": 3,   # 连续3天未完成触发额外扣减
    "extra_penalty_per_day": 100,    # 连续未完成第4天起每天额外扣100元
}

# ============ 2人角色分工 ============
ROLES = {
    "A": {
        "name": "角色A（内容运营）",
        "duties": ["每日生成并审核指定数量 AIO 内容", "发布到独立站/目录站", "维护关键词库与词库"],
        "daily_tasks": [
            {"task_type": "content_gen", "label": "生成 AIO 内容", "qty": 4},
            {"task_type": "content_publish", "label": "发布内容到渠道", "qty": 4},
            {"task_type": "keyword_maintain", "label": "维护/新增关键词", "qty": 2},
        ],
    },
    "B": {
        "name": "角色B（数据运营）",
        "duties": ["每日执行排名监测并记录", "分析 AI 引用来源", "绩效核算", "对接发布渠道"],
        "daily_tasks": [
            {"task_type": "rank_monitor", "label": "监测关键词排名", "qty": 10},
            {"task_type": "source_analyze", "label": "分析 AI 引用来源", "qty": 3},
            {"task_type": "lead_record", "label": "归集/录入询盘线索", "qty": 0},
            {"task_type": "perf_calc", "label": "绩效核算", "qty": 1},
        ],
    },
}

# ============ 3个月阶段目标 ============
PHASES = {
    1: {"name": "基础建设期", "goal": "词库搭建、内容模板、基础内容铺设、系统部署",
        "weekly_target": "每周完成40条基础内容、20个关键词建档、渠道全部开通"},
    2: {"name": "快速增长期", "goal": "批量产出AIO内容、全渠道分发、排名快速提升",
        "weekly_target": "每周完成60条内容、60次发布、50次排名监测"},
    3: {"name": "稳定优化期", "goal": "稳定前3推荐位、优化转化、沉淀SOP",
        "weekly_target": "每周完成50条内容、50次发布、稳定前3位关键词≥15个"},
}
