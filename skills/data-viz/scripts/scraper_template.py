#!/usr/bin/env python3
"""
scraper_template.py — 数据爬虫模板
支持：静态页面(requests+BS4)、动态页面(直接配置)、API接口

用法：
  python3 scraper_template.py --url "https://example.com/data" --selector "table" --output data.csv
  python3 scraper_template.py --api "https://api.example.com/data" --output api_data.csv
  python3 scraper_template.py --demo  # 生成示例数据用于测试
"""

import argparse
import csv
import json
import sys
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ─── 配置区（根据作业修改） ──────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT = 30
# ────────────────────────────────────────────


def fetch_page(url):
    """获取网页 HTML"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding  # 自动检测编码
        return resp.text
    except Exception as e:
        print(f"❌ 页面获取失败: {e}")
        sys.exit(1)


def parse_table(html, selector="table"):
    """解析 HTML 表格 -> List[Dict]"""
    soup = BeautifulSoup(html, "lxml")
    tables = soup.select(selector)
    if not tables:
        print(f"❌ 未找到匹配选择器 '{selector}' 的表格")
        return []

    rows = []
    for table in tables[:1]:  # 取第一个匹配表格
        trs = table.find_all("tr")
        if not trs:
            continue
        # 表头
        headers = [th.get_text(strip=True) for th in trs[0].find_all(["th", "td"])]
        if not headers:
            headers = [f"col_{i}" for i in range(len(trs[1].find_all("td")))] if len(trs) > 1 else []

        for tr in trs[1:]:
            cells = tr.find_all("td")
            if len(cells) == len(headers):
                row = {h: c.get_text(strip=True) for h, c in zip(headers, cells)}
                rows.append(row)
            elif len(cells) > 0:
                # 自动填充/截断
                row = {}
                for i, c in enumerate(cells):
                    key = headers[i] if i < len(headers) else f"col_{i}"
                    row[key] = c.get_text(strip=True)
                rows.append(row)

    print(f"✅ 解析到 {len(rows)} 行数据")
    return rows


def fetch_api(url, params=None):
    """调用 JSON API"""
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ API 请求失败: {e}")
        sys.exit(1)


def save_csv(data, filepath):
    """保存为 CSV"""
    if not data:
        print("❌ 无数据可保存")
        return
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ 数据已保存: {filepath} ({len(data)} 行)")


def generate_demo_data(output="data/demo_data.csv"):
    """生成示例数据（用于测试可视化流程）"""
    import random
    import pandas as pd

    categories = ["电子产品", "服装", "食品", "家居", "书籍", "运动器材"]
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    cities = ["北京", "上海", "广州", "深圳", "杭州", "成都"]

    # 模拟数据集1: 月度销售额
    data1 = []
    base = 100
    for m, month in enumerate(months):
        for cat in categories:
            trend = 1 + 0.1 * (m / 12)  # 上升趋势
            seasonal = 1 + 0.3 * (m in [6, 7, 8, 11, 12])  # 旺季
            noise = random.uniform(0.8, 1.2)
            sales = int(base * trend * seasonal * noise)
            data1.append({"月份": month, "类别": cat, "销售额(万元)": sales})

    # 模拟数据集2: 各城市季度用户满意度
    data2 = []
    for city in cities:
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            score = round(random.uniform(70, 98), 1)
            data2.append({"城市": city, "季度": q, "满意度评分": score})

    # 模拟数据集3: 市场份额占比
    data3 = []
    for cat in categories:
        share = random.uniform(5, 25)
        data3.append({"类别": cat, "市场份额(%)": round(share, 1)})

    dirpath = os.path.dirname(output)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    pd.DataFrame(data1).to_csv(output, index=False, encoding="utf-8-sig")
    pd.DataFrame(data2).to_csv(output.replace(".csv", "_city.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(data3).to_csv(output.replace(".csv", "_share.csv"), index=False, encoding="utf-8-sig")

    print(f"✅ 示例数据已生成:")
    print(f"   {output} ({len(data1)} 行)")
    print(f"   {output.replace('.csv', '_city.csv')} ({len(data2)} 行)")
    print(f"   {output.replace('.csv', '_share.csv')} ({len(data3)} 行)")


def main():
    parser = argparse.ArgumentParser(description="🌐 数据爬虫工具")
    parser.add_argument("--url", help="目标网页 URL")
    parser.add_argument("--api", help="API 接口 URL")
    parser.add_argument("--selector", default="table", help="CSS 选择器（默认 table）")
    parser.add_argument("--output", default="data/raw.csv", help="输出文件路径")
    parser.add_argument("--demo", action="store_true", help="生成示例数据")
    args = parser.parse_args()

    if args.demo:
        generate_demo_data(args.output)
        return

    if args.api:
        js = fetch_api(args.api)
        if isinstance(js, list) and js and isinstance(js[0], dict):
            save_csv(js, args.output)
        else:
            print("API 返回数据格式不支持直接转 CSV，请手动处理")
            print(json.dumps(js, ensure_ascii=False, indent=2)[:500])
        return

    if args.url:
        html = fetch_page(args.url)
        data = parse_table(html, args.selector)
        if data:
            save_csv(data, args.output)
        return

    print("请指定 --url 或 --api 或 --demo")
    parser.print_help()


if __name__ == "__main__":
    main()
