#!/usr/bin/env python3
"""
viz_master.py — 数据可视化主引擎
支持：折线图、柱状图、饼图、散点图、箱线图、热力图、雷达图、词云等

用法：
  python3 viz_master.py --input data.csv --output output/charts/
  python3 viz_master.py --input data.csv --output charts/ --type line,bar,pie
  python3 viz_master.py --demo --output output/charts/
"""

import argparse
import os
import warnings
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # 非交互模式（服务器可用）
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

warnings.filterwarnings("ignore")

# ─── 中文字体配置 ──────────────────────────
# macOS 常见中文字体
CHINESE_FONTS = [
    "/System/Library/Fonts/PingFang.ttc",           # PingFang
    "/System/Library/Fonts/Supplemental/Songti.ttc",  # 宋体
    "/System/Library/Fonts/STHeiti Light.ttc",       # 黑体
    "/System/Library/Fonts/Supplemental/STHeiti.ttf",
]

def setup_chinese_font():
    """设置中文字体"""
    for font_path in CHINESE_FONTS:
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams["font.family"] = font_prop.get_name()
            plt.rcParams["axes.unicode_minus"] = False
            print(f"✅ 中文字体: {font_prop.get_name()}")
            return
    # 回退方案
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "STHeiti", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    print("⚠️ 使用回退字体配置")


def setup_style():
    """设置全局图表风格"""
    sns.set_style("whitegrid", {
        "axes.grid": True,
        "grid.color": "#E8E8E8",
        "grid.alpha": 0.6,
    })
    sns.set_context("paper", font_scale=1.2)
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
    })


# ─── 配色方案 ──────────────────────────────
PALETTES = {
    "business": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B"],
    "soft": ["#6C5B7B", "#C06C84", "#F67280", "#F8B195", "#355C7D"],
    "warm": ["#FF6B6B", "#FFE66D", "#4ECDC4", "#45B7D1", "#96CEB4"],
    "nature": ["#2D6A4F", "#40916C", "#52B788", "#95D5B2", "#D8F3DC"],
}

# ─── 图表生成函数 ──────────────────────────

def draw_line_chart(df, x_col, y_cols, hue_col=None, title="趋势图",
                    output="line_chart.png"):
    """折线图 — 时间序列趋势"""
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = PALETTES["business"]

    if hue_col:
        for i, (name, group) in enumerate(df.groupby(hue_col)):
            color = colors[i % len(colors)]
            ax.plot(group[x_col], group[y_cols[0]], marker="o", linewidth=2,
                    label=name, color=color, markersize=5)
            # 标注最后一个点
            last = group.iloc[-1]
            ax.annotate(f"{last[y_cols[0]]:.1f}",
                        (last[x_col], last[y_cols[0]]),
                        textcoords="offset points", xytext=(0, 10),
                        ha="center", fontsize=9, color=color)
    else:
        for y_col in y_cols:
            color = colors[len(ax.lines) % len(colors)]
            ax.plot(df[x_col], df[y_col], marker="o", linewidth=2,
                    label=y_col, color=color, markersize=5)
            # 标注最大值点
            max_idx = df[y_col].idxmax()
            ax.annotate(f"{df[y_col].max():.1f}",
                        (df[x_col][max_idx], df[y_col].max()),
                        textcoords="offset points", xytext=(0, 10),
                        ha="center", fontsize=9, color=color,
                        arrowprops=dict(arrowstyle="->", color=color, lw=0.8))

    ax.set_xlabel(x_col)
    ax.set_ylabel(" / ".join(y_cols))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="best", frameon=True, facecolor="white", edgecolor="#ddd")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 折线图: {output}")


def draw_bar_chart(df, x_col, y_col, hue_col=None, title="柱状图",
                   output="bar_chart.png", stacked=False):
    """柱状图 — 分类对比"""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = PALETTES["soft"]

    if hue_col:
        pivot = df.pivot_table(index=x_col, columns=hue_col, values=y_col,
                                aggfunc="mean").fillna(0)
        pivot.plot(kind="bar", ax=ax, color=colors[:len(pivot.columns)],
                    stacked=stacked, width=0.75)
    else:
        bars = ax.bar(df[x_col], df[y_col], color=colors[0], width=0.6,
                       edgecolor="white", linewidth=0.5)
        # 柱顶标数值
        for bar, val in zip(bars, df[y_col]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val:.1f}", ha="center", va="bottom", fontsize=9)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="best", frameon=True, facecolor="white", edgecolor="#ddd")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 柱状图: {output}")


def draw_pie_chart(df, label_col, value_col, title="占比图",
                   output="pie_chart.png"):
    """环形占比图（推荐环形而非饼图）"""
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = PALETTES["nature"]

    values = df[value_col].values
    labels = df[label_col].values

    # 环形图: 中间放总数
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%",
        colors=colors[:len(values)],
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=1.5),
        textprops=dict(fontsize=10)
    )
    # 中间显示总数
    total = sum(values)
    ax.text(0, 0, f"总数\n{total:.0f}", ha="center", va="center",
            fontsize=14, fontweight="bold")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 环形图: {output}")


def draw_scatter(df, x_col, y_col, hue_col=None, title="散点图",
                 output="scatter.png"):
    """散点图 — 相关性分析"""
    fig, ax = plt.subplots(figsize=(10, 7))

    if hue_col:
        sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col,
                        s=80, alpha=0.7, ax=ax, palette="Set2")
    else:
        sns.regplot(data=df, x=x_col, y=y_col, ax=ax,
                     scatter_kws={"s": 60, "alpha": 0.6, "color": "#2E86AB"},
                     line_kws={"color": "#C73E1D", "lw": 2})
        # 标注相关系数
        corr = df[x_col].corr(df[y_col])
        ax.text(0.05, 0.95, f"R = {corr:.3f}", transform=ax.transAxes,
                fontsize=12, fontweight="bold", va="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 散点图: {output}")


def draw_boxplot(df, x_col, y_col, title="箱线图", output="boxplot.png"):
    """箱线图 — 数据分布"""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = PALETTES["business"]

    sns.boxplot(data=df, x=x_col, y=y_col, palette=colors[:df[x_col].nunique()],
                ax=ax, linewidth=1.2)
    # 叠加散点（蜂群图）
    sns.stripplot(data=df, x=x_col, y=y_col, color="black", alpha=0.3,
                  size=4, ax=ax, jitter=True)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 箱线图: {output}")


def draw_heatmap(df, title="热力图", output="heatmap.png"):
    """热力图 — 矩阵相关性"""
    # 只取数值列
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) < 2:
        print("  ⚠️ 数值列不足，跳过热力图")
        return

    corr = df[num_cols].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))  # 隐藏上三角

    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
                cmap="RdBu_r", center=0, square=True,
                linewidths=0.5, ax=ax,
                cbar_kws={"shrink": 0.8, "label": "相关系数"})

    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 热力图: {output}")


def draw_radar(df, categories_col, value_cols, title="雷达图",
               output="radar.png"):
    """雷达图 — 多维度对比"""
    categories = df[categories_col].tolist()
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    colors = PALETTES["soft"]

    for i, val_col in enumerate(value_cols):
        values = df[val_col].tolist()
        values += values[:1]
        ax.fill(angles, values, alpha=0.1, color=colors[i % len(colors)])
        ax.plot(angles, values, "o-", linewidth=2, label=val_col,
                color=colors[i % len(colors)], markersize=6)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, max([df[c].max() for c in value_cols]) * 1.1)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.1))
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 雷达图: {output}")


def draw_wordcloud(text, title="词云图", output="wordcloud.png"):
    """词云图 — 文本关键词可视化"""
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("  ⚠️ wordcloud 未安装，跳过词云")
        return

    # 尝试中文分词（简单版 — 按字数拆分）
    wc = WordCloud(
        font_path="/System/Library/Fonts/STHeiti Medium.ttc",
        width=1200, height=800,
        background_color="white",
        max_words=200,
        max_font_size=120,
        min_font_size=12,
        colormap="viridis",
        random_state=42,
        collocations=False
    )
    wc.generate(text)

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 词云图: {output}")


def draw_histogram(df, col, hue_col=None, title="分布直方图",
                   output="histogram.png"):
    """直方图 + KDE — 数据分布"""
    fig, ax = plt.subplots(figsize=(10, 5))

    if hue_col:
        for name, group in df.groupby(hue_col):
            sns.histplot(group[col], label=name, alpha=0.5, kde=True, ax=ax)
    else:
        sns.histplot(df[col], kde=True, ax=ax,
                     color="#2E86AB", alpha=0.6, bins=20)
        # 标注均值和中位数
        mean_val = df[col].mean()
        med_val = df[col].median()
        ax.axvline(mean_val, color="#C73E1D", linestyle="--", linewidth=2,
                   label=f"均值={mean_val:.1f}")
        ax.axvline(med_val, color="#A23B72", linestyle=":", linewidth=2,
                   label=f"中位数={med_val:.1f}")

    ax.set_xlabel(col)
    ax.set_ylabel("频数")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)
    print(f"  ✅ 分布直方图: {output}")


# ─── 主控 ────────────────────────────────

def auto_visualize(df, output_dir, prefix=""):
    """自动根据数据特征生成合适的图表"""
    files = []
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = [c for c in df.columns if "月" in c or "年" in c or "日期" in c
                 or "时间" in c]

    # 1. 有时间列 → 折线图
    time_col = None
    for c in date_cols:
        if c in df.columns:
            time_col = c
            break
    if not time_col and cat_cols:
        # 尝试找类似月份的列
        for c in cat_cols:
            if any(k in c for k in ["月", "季度", "年", "week", "month", "year"]):
                time_col = c
                break

    if time_col and num_cols:
        out = os.path.join(output_dir, f"{prefix}01_趋势图.png")
        draw_line_chart(df, time_col, [num_cols[0]], title=f"{prefix}趋势图", output=out)
        files.append(out)

    # 2. 有分类+数值 → 柱状图
    if cat_cols and num_cols:
        cat_col = cat_cols[0]
        out = os.path.join(output_dir, f"{prefix}02_对比图.png")
        draw_bar_chart(df, cat_col, num_cols[0],
                       hue_col=cat_cols[1] if len(cat_cols) > 1 else None,
                       title=f"{prefix}对比图", output=out)
        files.append(out)

    # 3. 分类+单个数值 → 环形图（不超过8类）
    if cat_cols and len(df[cat_cols[0]].unique()) <= 8:
        out = os.path.join(output_dir, f"{prefix}03_占比图.png")
        draw_pie_chart(df, cat_cols[0], num_cols[0],
                       title=f"{prefix}占比图", output=out)
        files.append(out)

    # 4. 至少2个数值列 → 热力图
    if len(num_cols) >= 3:
        out = os.path.join(output_dir, f"{prefix}04_热力图.png")
        draw_heatmap(df[num_cols], title=f"{prefix}相关性热力图", output=out)
        files.append(out)

    # 5. 至少2个数值列 → 散点图
    if len(num_cols) >= 2:
        out = os.path.join(output_dir, f"{prefix}05_相关性散点图.png")
        draw_scatter(df, num_cols[0], num_cols[1],
                     hue_col=cat_cols[0] if cat_cols else None,
                     title=f"{prefix}相关性分析", output=out)
        files.append(out)

    # 6. 分类+数值 → 箱线图
    if cat_cols and num_cols:
        out = os.path.join(output_dir, f"{prefix}06_分布箱线图.png")
        draw_boxplot(df, cat_cols[0], num_cols[0],
                     title=f"{prefix}分布箱线图", output=out)
        files.append(out)

    # 7. 单个数值列 → 直方图
    if num_cols:
        out = os.path.join(output_dir, f"{prefix}07_分布直方图.png")
        draw_histogram(df, num_cols[0],
                       hue_col=cat_cols[0] if cat_cols else None,
                       title=f"{prefix}分布直方图", output=out)
        files.append(out)

    return files


def generate_demo_charts(output_dir):
    """生成示例图表"""
    print("🎨 生成示例图表...")
    os.makedirs(output_dir, exist_ok=True)

    # 生成模拟数据
    import random
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    categories = ["电子产品", "服装", "食品", "家居", "书籍", "运动器材"]
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]

    # 月度销售数据
    sales_data = []
    for m, month in enumerate(months):
        for cat in categories:
            trend = 1 + 0.1 * (m / 12)
            seasonal = 1 + 0.3 * (m in [6, 7, 8, 11, 12])
            sales = int(100 * trend * seasonal * random.uniform(0.8, 1.2))
            sales_data.append({"月份": month, "类别": cat, "销售额(万元)": sales})
    df_sales = pd.DataFrame(sales_data)

    # 城市满意度数据
    sat_data = []
    for city in cities:
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            sat_data.append({"城市": city, "季度": q,
                             "满意度": round(random.uniform(70, 98), 1)})
    df_sat = pd.DataFrame(sat_data)

    # 市场份额
    share_data = []
    for cat in categories:
        share_data.append({"类别": cat,
                           "市场份额(%)": round(random.uniform(5, 25), 1)})
    df_share = pd.DataFrame(share_data)

    # 生成各种图表
    draw_line_chart(df_sales[df_sales["类别"] == "电子产品"],
                    "月份", ["销售额(万元)"],
                    title="电子产品月度销售额趋势", output=os.path.join(output_dir, "01_折线图示例.png"))
    draw_bar_chart(df_sales.groupby("月份")["销售额(万元)"].sum().reset_index(),
                   "月份", "销售额(万元)",
                   title="各月总销售额", output=os.path.join(output_dir, "02_柱状图示例.png"))
    draw_pie_chart(df_share, "类别", "市场份额(%)",
                   title="市场份额占比", output=os.path.join(output_dir, "03_环形图示例.png"))
    draw_scatter(df_sat, "季度", "满意度", hue_col="城市",
                 title="各城市满意度分布", output=os.path.join(output_dir, "04_散点图示例.png"))
    draw_boxplot(df_sales, "类别", "销售额(万元)",
                 title="各品类销售额分布", output=os.path.join(output_dir, "05_箱线图示例.png"))
    draw_heatmap(df_sales.pivot_table(index="月份", columns="类别",
                                       values="销售额(万元)", aggfunc="mean"),
                 title="销售热力图", output=os.path.join(output_dir, "06_热力图示例.png"))

    # 雷达图
    avg_sales = df_sales.groupby("类别")["销售额(万元)"].mean().reset_index()
    avg_sales.columns = ["类别", "平均销售额"]
    draw_radar(avg_sales, "类别", ["平均销售额"],
               title="各品类销售能力雷达图", output=os.path.join(output_dir, "07_雷达图示例.png"))

    # 词云图
    text = " ".join(categories * 20) + "数据 分析 可视化 Python 图表 作业 报告"
    draw_wordcloud(text, title="关键词词云", output=os.path.join(output_dir, "08_词云示例.png"))

    print(f"\n✅ 示例图表已生成至: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="🎨 数据可视化引擎")
    parser.add_argument("--input", help="输入 CSV 文件路径")
    parser.add_argument("--output", default="output/charts/", help="图表输出目录")
    parser.add_argument("--type", default="auto",
                        help="图表类型: auto/line/bar/pie/scatter/box/heatmap/radar/wordcloud"
                             "（逗号分隔可生成多种）")
    parser.add_argument("--title", default=None, help="图表标题前缀")
    parser.add_argument("--demo", action="store_true", help="生成示例图表")
    args = parser.parse_args()

    # 基础设置
    setup_chinese_font()
    setup_style()
    os.makedirs(args.output, exist_ok=True)

    if args.demo:
        generate_demo_charts(args.output)
        return

    if not args.input:
        print("请指定 --input 或使用 --demo")
        parser.print_help()
        return

    # 读取数据
    df = pd.read_csv(args.input, encoding="utf-8-sig")
    print(f"📊 数据加载: {args.input}")
    print(f"   {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"   列: {', '.join(df.columns.tolist())}")

    # 图表前缀
    prefix = f"{args.title}_" if args.title else ""

    # 生成图表
    chart_types = args.type.split(",")

    if "auto" in chart_types:
        auto_visualize(df, args.output, prefix)
    else:
        for ct in chart_types:
            ct = ct.strip()
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

            if ct == "line" and cat_cols and num_cols:
                draw_line_chart(df, cat_cols[0], [num_cols[0]],
                                title=f"{prefix}趋势图",
                                output=os.path.join(args.output, f"{prefix}折线图.png"))
            elif ct == "bar" and cat_cols and num_cols:
                draw_bar_chart(df, cat_cols[0], num_cols[0],
                               title=f"{prefix}对比图",
                               output=os.path.join(args.output, f"{prefix}柱状图.png"))
            elif ct == "pie" and cat_cols and num_cols:
                draw_pie_chart(df, cat_cols[0], num_cols[0],
                               title=f"{prefix}占比图",
                               output=os.path.join(args.output, f"{prefix}占比图.png"))
            elif ct == "scatter" and len(num_cols) >= 2:
                draw_scatter(df, num_cols[0], num_cols[1],
                             title=f"{prefix}相关性分析",
                             output=os.path.join(args.output, f"{prefix}散点图.png"))
            elif ct == "box" and cat_cols and num_cols:
                draw_boxplot(df, cat_cols[0], num_cols[0],
                             title=f"{prefix}分布箱线图",
                             output=os.path.join(args.output, f"{prefix}箱线图.png"))
            elif ct == "heatmap" and len(num_cols) >= 3:
                draw_heatmap(df[num_cols], title=f"{prefix}相关性热力图",
                             output=os.path.join(args.output, f"{prefix}热力图.png"))
            elif ct == "radar" and cat_cols and num_cols:
                draw_radar(df, cat_cols[0], num_cols,
                           title=f"{prefix}雷达图",
                           output=os.path.join(args.output, f"{prefix}雷达图.png"))
            else:
                print(f"  ⚠️ 图表类型'{ct}'无法处理（数据列不匹配）")

    print(f"\n📁 所有图表已保存至: {args.output}")


if __name__ == "__main__":
    main()
