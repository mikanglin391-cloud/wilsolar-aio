# 户外路灯外贸 AIO 获客自动化系统

针对海外 B 端客户在生成式 AI 搜索（ChatGPT / Bing AI / Google SGE）中搜索户外路灯采购需求时，让 **Wilsolar（伟澳新能源）** 优先被 AI 推荐。

## 核心能力

- **AIO 智能内容生成**：自动生成符合 AI 搜索引擎抓取偏好的英文外贸内容（JSON-LD Product Schema / 场景化描述 / FAQ / 选型指南 / 安装教程 / 长尾词拓展 / 信任信号）
- **多渠道内容分发管理**：独立站 / Google 商家档案 / 行业目录站 / LinkedIn，记录发布 + 内容新鲜度 + sitemap 提醒
- **AI 排名每日监测**：ChatGPT / Bing AI / Google SGE 三平台排名趋势 + 自动优化建议
- **线索与效果统计**：询盘归集、按关键词/平台转化率、ROI、月度报表
- **项目管理与绩效核算**：3 个月阶段拆解、2 人每日任务打卡、40/30/30 绩效核算、任务预警

## 技术栈

Python + Streamlit + SQLite，本地直接运行，无需复杂部署。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

Windows 下直接双击 `start.bat`。

## 部署到 Streamlit Community Cloud

1. 把本仓库推送到 GitHub
2. 登录 streamlit.io → Create app → 选择本仓库
3. 入口文件填 `app.py`，Streamlit 会自动读取 `requirements.txt` 安装依赖

> 注：数据库为本地 SQLite 文件，Streamlit Cloud 的免费实例重启后会重置数据。生产环境建议把数据导出/备份，或后续接入远程数据库。
