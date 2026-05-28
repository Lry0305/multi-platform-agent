# Skill: data-viz — 数据可视化作业全流程 Agent

## Description

一站式数据可视化作业 agent：网页数据爬取 → 数据处理 → 精美可视化图表 → Word 文档排版。

覆盖能力：
- **爬虫**：requests + BeautifulSoup / Scrapy 静态/动态页面数据采集
- **分析**：pandas + numpy 数据清洗与统计分析
- **可视化**：matplotlib / seaborn / plotly / pyecharts 多维度精美图表
- **文档**：python-docx 自动化 Word 排版

## 目录结构

```
skills/data-viz/
├── SKILL.md                    # 本文件 — 技能定义
├── scripts/                    # 可执行脚本
│   ├── scraper_template.py     # 爬虫模板
│   ├── viz_master.py           # 可视化主引擎
│   └── word_reporter.py        # Word 文档生成器
├── references/                 # 参考资料
│   ├── viz-showcase.md         # 优秀可视化案例库
│   └── word-template-guide.md  # Word 排版规范
├── templates/                  # Word 模板 / 代码模板
│   └── report_template.py      # 报告生成骨架代码
└── output/                     # 输出目录（自动创建）
    ├── charts/                 # 图表文件
    └── reports/                # Word 文档
```

## 使用流程

### 完整流程（一键运行）

```bash
cd ~/.openclaw/workspace
source .venv/bin/activate

# 1. 爬取数据
python3 skills/data-viz/scripts/scraper_template.py --url "目标URL" --output data/raw.csv

# 2. 数据可视化
python3 skills/data-viz/scripts/viz_master.py --input data/raw.csv --output output/charts/

# 3. 生成 Word 报告
python3 skills/data-viz/scripts/word_reporter.py --charts output/charts/ --output output/reports/report.docx
```

### 单步运行

```bash
# 只看可视化
python3 skills/data-viz/scripts/viz_master.py --input data.csv --output charts/

# 仅生成 Word
python3 skills/data-viz/scripts/word_reporter.py --charts charts/ --output report.docx --title "报告标题"
```

## 环境

```bash
# 激活虚拟环境
source ~/.openclaw/workspace/.venv/bin/activate

# Python 依赖（.venv 中已预装）
pip list | grep -E "matplotlib|seaborn|plotly|pyecharts|python-docx|wordcloud|beautifulsoup4|lxml|pandas|numpy|requests"
```
