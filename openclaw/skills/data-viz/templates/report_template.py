#!/usr/bin/env python3
"""
report_template.py — 报告生成骨架代码
这是一个可以快速修改适配的完整报告生成模板。
修改以下标注区即可适配不同作业主题。
"""

import os
import sys
from datetime import datetime

# ─── 魔改区（根据你的作业修改这里） ──────────────────────────
JOB_TITLE = "数据可视化作业"                    # 报告标题
JOB_SUBTITLE = "基于Python的数据采集与可视化分析"  # 副标题
JOB_AUTHOR = "你的名字"                         # 作者
JOB_DATA_FILE = "data/raw.csv"                 # 数据文件路径
JOB_CHARTS_DIR = "output/charts"               # 图表输出目录
JOB_REPORT_FILE = "output/reports/report.docx"  # 报告输出路径
# ──────────────────────────────────────────────────────────

# 添加脚本路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from viz_master import (setup_chinese_font, setup_style, auto_visualize,
                        draw_line_chart, draw_bar_chart, draw_pie_chart,
                        draw_scatter, draw_boxplot, draw_heatmap, draw_radar)
from word_reporter import WordReporter
import pandas as pd


def run_pipeline():
    """完整流程：数据 → 可视化 → Word 报告"""
    print(f"📊 开始执行: {JOB_TITLE}")
    print("=" * 50)

    # 1. 数据加载
    if not os.path.exists(JOB_DATA_FILE):
        print(f"❌ 数据文件不存在: {JOB_DATA_FILE}")
        print("   请先运行 scraper_template.py 或修改 JOB_DATA_FILE")
        return

    df = pd.read_csv(JOB_DATA_FILE, encoding="utf-8-sig")
    print(f"✅ 数据加载完成: {df.shape[0]} 行 × {df.shape[1]} 列")

    # 2. 数据分析摘要
    print(f"\n📈 数据概览:")
    print(df.describe().to_string())
    print(f"\n数据类型:\n{df.dtypes}")

    # 3. 生成图表
    print(f"\n🎨 生成可视化图表...")
    setup_chinese_font()
    setup_style()
    os.makedirs(JOB_CHARTS_DIR, exist_ok=True)

    chart_files = auto_visualize(df, JOB_CHARTS_DIR, prefix="")

    # 4. 生成 Word 报告
    print(f"\n📝 生成 Word 报告...")
    reporter = WordReporter(JOB_TITLE)

    # 封面
    reporter.add_title_page(
        subtitle=JOB_SUBTITLE,
        author=JOB_AUTHOR,
        date=datetime.now().strftime("%Y年%m月%d日")
    )

    # 第一章：数据来源
    reporter.add_heading("一、数据来源与方法", level=1)
    reporter.add_paragraph(
        "本次分析使用的数据来源于公开数据采集，"
        "数据字段包含：{}。共采集 {} 条有效样本。".format(
            "、".join(df.columns.tolist()), df.shape[0]
        ),
        indent=True
    )

    # 第二章：数据概览
    reporter.add_heading("二、数据概览", level=1)
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if num_cols:
        stats = df[num_cols].describe().round(2)
        rows = [[idx] + [str(v) for v in row]
                for idx, row in stats.iterrows()]
        reporter.add_table(
            headers=["统计量"] + num_cols,
            data=rows,
            caption="描述性统计"
        )

    # 第三章：可视化分析
    reporter.add_heading("三、可视化分析", level=1)
    reporter.add_paragraph(
        "以下通过多张图表对数据进行可视化分析：",
        indent=True
    )
    reporter.add_charts_from_dir(JOB_CHARTS_DIR)

    # 第四章：结论
    reporter.add_heading("四、结论与建议", level=1)
    reporter.add_paragraph(
        "通过本次数据分析，可以得出以下结论：",
        indent=True
    )
    reporter.add_numbered_list([
        "结论一（请根据实际数据补充）",
        "结论二（请根据实际数据补充）",
        "结论三（请根据实际数据补充）",
    ])

    reporter.add_footer()
    reporter.add_page_number()
    reporter.save(JOB_REPORT_FILE)

    print(f"\n🎉 全流程完成!")
    print(f"   图表目录: {os.path.abspath(JOB_CHARTS_DIR)}")
    print(f"   报告文件: {os.path.abspath(JOB_REPORT_FILE)}")


if __name__ == "__main__":
    run_pipeline()
