#!/usr/bin/env python3
"""
小红书图片生成工具 (小红专用)
利用硅基流动 API 生成小红书风格的配图

用法:
  python3 scripts/gen_image.py "一只橘猫在阳台晒太阳"
  python3 scripts/gen_image.py "prompt" --model Qwen/Qwen-Image --size 1024x1024 --n 1

输出: 打印图片URL，并下载到本地。
"""

import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse

API_KEY = "sk-sbcsqgshydexdjkdoyglqmodgfvenhrqbrvpelfmsenjxlgc"
API_URL = "https://api.siliconflow.cn/v1/images/generations"

def generate_image(prompt, model="Qwen/Qwen-Image", size="1024x1024", n=1):
    """调用硅基流动 API 生成图片"""
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "n": n,
        "size": size
    }).encode("utf-8")

    req = Request(API_URL, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")

    try:
        resp = urlopen(req, timeout=60)
        data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception as e:
        # Try to read error body
        error_body = ""
        if hasattr(e, 'read'):
            try:
                error_body = e.read().decode("utf-8")
            except:
                pass
        return {"error": str(e), "detail": error_body}


def download_image(url, output_dir="output"):
    """下载图片到本地"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    filename = f"xiaohongshu_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)

    try:
        req = Request(url)
        resp = urlopen(req, timeout=30)
        with open(filepath, "wb") as f:
            f.write(resp.read())
        return filepath
    except Exception as e:
        return f"下载失败: {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书图片生成")
    parser.add_argument("prompt", help="图片描述 prompt")
    parser.add_argument("--model", default="Qwen/Qwen-Image",
                        choices=["Qwen/Qwen-Image", "Kwai-Kolors/Kolors",
                                 "Tongyi-MAI/Z-Image", "Tongyi-MAI/Z-Image-Turbo",
                                 "baidu/ERNIE-Image-Turbo"],
                        help="图片模型")
    parser.add_argument("--size", default="1024x1024",
                        choices=["1024x1024", "768x1024", "1024x768"],
                        help="图片尺寸")
    parser.add_argument("--n", type=int, default=1, help="生成数量")
    parser.add_argument("--save", action="store_true", help="下载到本地")
    parser.add_argument("--output", default="output", help="下载目录")

    args = parser.parse_args()

    print(f"🖼️  正在生成: {args.prompt}")
    print(f"📐 模型: {args.model} | 尺寸: {args.size}")
    print("⏳ 等待中...")

    result = generate_image(args.prompt, args.model, args.size, args.n)

    if "error" in result:
        print(f"❌ 错误: {result['error']}")
        if result.get("detail"):
            print(f"   详情: {result['detail']}")
        sys.exit(1)

    images = result.get("images", result.get("data", []))
    for i, img in enumerate(images):
        url = img.get("url", "")
        print(f"\n✅ 图片 {i+1}:")
        print(f"   URL: {url}")

        if args.save:
            filepath = download_image(url, args.output)
            print(f"   💾 已保存: {filepath}")

    print(f"\n✨ 种子值: {result.get('seed', 'N/A')}")
    print(f"⚡ 推理耗时: {result.get('timings', {}).get('inference', 'N/A')}s")
