#!/usr/bin/env python3
"""
小红书内容生成主流程 v2（🍒 小红专用）

功能（完整 Pipeline）:
  1. 文案 → 自动多角度配图 prompt → 多图生成 → 下载到本地
  2. 保存完整帖子草稿（Markdown + 图片本地路径）
  3. 批量生成：从 JSON/YAML 文件一次产多篇
  4. 草稿管理与查看

用法:
  # 单篇完整生成（推荐）
  python3 scripts/xiaohongshu_pipeline.py generate \\
      --title "标题" --file content.txt --category recommend --vibe 温暖 --images 2

  # 只生成配图 prompt
  python3 scripts/xiaohongshu_pipeline.py prompt --scene "面霜瓶子" --category recommend

  # 批量生成（从 recipes.json 读多个主题）
  python3 scripts/xiaohongshu_pipeline.py batch recipes.json

  # 草稿管理
  python3 scripts/xiaohongshu_pipeline.py list              # 列出所有
  python3 scripts/xiaohongshu_pipeline.py view draft_xxx.md  # 查看单篇

输出:
  - output/posts/*.md    ← 帖子草稿（含图片本地路径）
  - output/images/*.png  ← 下载的配图
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
import subprocess
import importlib.util
import sys as _sys

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.dirname(AGENT_DIR)

# ============================================================
# 1. 配图 Prompt 体系
# ============================================================

# 内容方向 → 摄影风格
CONTENT_STYLE_MAP = {
    "recommend": "ins风静物摄影，产品特写，干净背景，自然光，小红书美学，有质感",
    "checkin":   "探店摄影，环境氛围，有生活气息，暖色调，景深感，真实感",
    "daily":     "日常感，生活化记录，自然光线，平实温馨，真实氛围",
    "knowledge": "简洁清晰，明亮通透，干净构图，教育感，有条理",
}

# 氛围 → 色调描述
VIBE_COLOR_MAP = {
    "温暖":  "暖色调，奶油色系，柔光",
    "清新":  "清新色调，青绿色系，亮调，干净通透",
    "复古":  "胶片感，暖黄调，轻微颗粒感",
    "高级":  "冷色调，低饱和，质感光影，极简",
    "活泼":  "明亮色彩，高饱和度，欢快氛围",
    "治愈":  "柔光暖调，软糯色系，舒适放松",
}

# 多图场景模板（不同角度/构图）
MULTI_ANGLE_TEMPLATES = {
    "recommend": [
        "{scene}，主体居中特写，景深虚化背景，{style}，{color}，小红书风格",
        "{scene}，俯拍45度角，桌面平铺展示，自然光从左上方照射，{style}，{color}",
        "{scene}，使用场景实拍，有人的手部入镜，生活化构图，{style}，{color}",
    ],
    "checkin": [
        "{scene}，环境全景展示，氛围感，有纵深感，{style}，{color}",
        "{scene}，主体特写，背景虚化，暖色灯光氛围，{style}，{color}",
        "{scene}，人视角第一人称拍摄，真实探店视角，{style}，{color}",
    ],
    "daily": [
        "{scene}，第一人称视角，自然光，真实抓拍感，{style}，{color}",
        "{scene}，生活场景俯拍，日常感，暖色调，{style}，{color}",
        "{scene}，细节特写，微距，生活碎片感，{style}，{color}",
    ],
    "knowledge": [
        "{scene}，平铺俯拍，布局整洁，明亮清晰，{style}，{color}",
        "{scene}，排版整洁，有标注感，极简背景，{style}，{color}",
        "{scene}，前后对比或步骤展示，清晰明了，{style}，{color}",
    ],
}


def auto_generate_prompt(scene, category="recommend", product_name="", vibe="温暖"):
    """生成单张配图 prompt"""
    style = CONTENT_STYLE_MAP.get(category, CONTENT_STYLE_MAP["recommend"])
    color = VIBE_COLOR_MAP.get(vibe, VIBE_COLOR_MAP["温暖"])
    product = f"，{product_name}" if product_name else ""
    return f"{scene}{product}，{style}，{color}，高清"


def auto_generate_multi_prompts(scene, category="recommend", product_name="", vibe="温暖", count=2):
    """生成多张不同角度的配图 prompt"""
    templates = MULTI_ANGLE_TEMPLATES.get(category, MULTI_ANGLE_TEMPLATES["recommend"])
    style = CONTENT_STYLE_MAP.get(category, CONTENT_STYLE_MAP["recommend"])
    color = VIBE_COLOR_MAP.get(vibe, VIBE_COLOR_MAP["温暖"])
    
    prompts = []
    for i in range(min(count, len(templates))):
        prompt = templates[i].format(
            scene=scene,
            product=product_name or "",
            style=style,
            color=color,
        )
        prompt = re.sub(r'，+', '，', prompt).strip('，')
        prompts.append(prompt)
    return prompts


# ============================================================
# 2. 图片生成（硅基流动 API）
# ============================================================

def _get_api_key():
    env_key = os.environ.get("SILICONFLOW_API_KEY")
    if env_key:
        return env_key
    tools_path = os.path.join(WORKSPACE, "TOOLS.md")
    if os.path.exists(tools_path):
        with open(tools_path) as f:
            for line in f:
                match = re.search(r'(sk-[a-zA-Z0-9]+)', line)
                if match and not line.strip().startswith("#"):
                    return match.group(1)
    return None


def download_image(url, output_dir=None):
    """下载图片到本地，返回本地路径"""
    if output_dir is None:
        output_dir = os.path.join(AGENT_DIR, "output", "images")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time() * 1000)
    filename = f"img_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=30)
        with open(filepath, "wb") as f:
            f.write(resp.read())
        return os.path.relpath(filepath, WORKSPACE)
    except Exception as e:
        return f"[下载失败: {e}]"


def generate_image(prompt, model="Qwen/Qwen-Image", size="1024x1024", retry=1):
    """调用 API 生成图片，失败自动重试"""
    api_key = _get_api_key()
    if not api_key:
        print("⚠️  未找到 API Key")
        return []

    api_url = "https://api.siliconflow.cn/v1/images/generations"
    payload = json.dumps({"model": model, "prompt": prompt, "n": 1, "size": size}).encode("utf-8")

    for attempt in range(retry + 1):
        try:
            req = urllib.request.Request(api_url, data=payload, method="POST")
            req.add_header("Authorization", f"Bearer {api_key}")
            req.add_header("Content-Type", "application/json")
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read().decode("utf-8"))
            images = data.get("images", data.get("data", []))
            return [img.get("url", "") for img in images]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if attempt < retry:
                print(f"  ⚠️  失败，重试中... ({e.code})")
                time.sleep(1)
            else:
                print(f"  ❌ HTTP {e.code}: {body[:150]}")
        except Exception as e:
            if attempt < retry:
                print(f"  ⚠️  失败，重试中... ({e})")
                time.sleep(1)
            else:
                print(f"  ❌ {e}")
    return []


def generate_and_save_images(prompts, model="Qwen/Qwen-Image"):
    """批量生成并下载图片，返回(URL列表, 本地路径列表)"""
    url_list = []
    local_list = []
    total = len(prompts)

    for i, prompt in enumerate(prompts, 1):
        print(f"\n  🖼️  配图 {i}/{total}: 生成中...")
        urls = generate_image(prompt, model)
        if urls:
            url_list.append(urls[0])
            local = download_image(urls[0])
            local_list.append(local)
            print(f"     ✅ 已下载: {local}")
        else:
            url_list.append("")
            local_list.append("")
    return url_list, local_list


# ============================================================
# 3. 草稿管理
# ============================================================

def save_draft(title, content, tags, image_urls, image_locals=None, category="general",
               prompts_used=None, seed=None):
    """保存完整帖子草稿（含元数据）"""
    posts_dir = os.path.join(AGENT_DIR, "output", "posts")
    os.makedirs(posts_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"draft_{timestamp}.md"
    filepath = os.path.join(posts_dir, filename)

    tags_str = " ".join([f"#{t}" for t in tags])
    emoji_map = {"recommend": "🏆", "checkin": "📍", "daily": "☀️", "knowledge": "📖", "general": "📝"}
    emoji = emoji_map.get(category, "📝")

    lines = [f"# {emoji} {title}", "",
             "---",
             f"- **分类:** {category}",
             f"- **创建:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             f"- **状态:** 草稿",
             f"- **配图数:** {len(image_urls)}",
             "---", "",
             content, "",
             "---", "",
             tags_str, "",
             "## 🖼️ 配图", ""]

    for i, url in enumerate(image_urls, 1):
        lines.append(f"### 配图 {i}")
        if image_locals and i <= len(image_locals) and image_locals[i-1]:
            lines.append(f"- 本地: {image_locals[i-1]}")
        if url:
            lines.append(f"- URL: {url}")
            lines.append(f"  ![配图{i}]({url})")
        lines.append("")

    if prompts_used:
        lines.extend(["---", "## 📝 生成记录", ""])
        for i, p in enumerate(prompts_used, 1):
            lines.append(f"- prompt {i}: {p[:80]}...")
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


def list_drafts(show_detail=False):
    """列出所有草稿"""
    posts_dir = os.path.join(AGENT_DIR, "output", "posts")
    if not os.path.exists(posts_dir):
        print("📭 还没有草稿")
        return

    drafts = sorted([f for f in os.listdir(posts_dir) if f.endswith(".md")], reverse=True)
    if not drafts:
        print("📭 还没有草稿")
        return

    print(f"\n📋 共有 {len(drafts)} 篇草稿:\n")
    for d in drafts:
        fp = os.path.join(posts_dir, d)
        with open(fp, encoding="utf-8") as f:
            first = f.readline().strip().lstrip("# ")
        size = os.path.getsize(fp)
        ctime = os.path.getctime(fp)
        print(f"  📄 {d}")
        print(f"     标题: {first[:55]}{'...' if len(first) > 55 else ''}")
        print(f"     大小: {size}B  |  创建: {datetime.fromtimestamp(ctime).strftime('%m-%d %H:%M')}")
        print()


def view_draft(filename):
    """查看单篇草稿完整内容"""
    posts_dir = os.path.join(AGENT_DIR, "output", "posts")
    fp = os.path.join(posts_dir, filename)
    if not os.path.exists(fp):
        # 尝试自动补全路径
        fp = filename if os.path.exists(filename) else None
    if not fp or not os.path.exists(fp):
        print(f"❌ 未找到: {filename}")
        return
    with open(fp, encoding="utf-8") as f:
        print(f.read())


# ============================================================
# 4. 批量生成
# ============================================================

def batch_generate(recipes):
    """从 recipes 列表批量生成帖子"""
    total = len(recipes)
    results = []
    for i, r in enumerate(recipes, 1):
        print(f"\n{'='*50}")
        print(f"📝 [{i}/{total}] {r.get('title', '(无标题)')}")
        print(f"{'='*50}")

        content = r.get("content", "")
        if not content and r.get("file"):
            fp = os.path.join(AGENT_DIR, r["file"]) if not os.path.isabs(r["file"]) else r["file"]
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    content = f.read()

        if not content:
            print("  ⚠️  跳过：无内容")
            continue

        scene = r.get("scene")
        if not scene:
            first_lines = [l.strip() for l in content.split("\n") if l.strip()][:2]
            scene = "，".join(first_lines)[:60] or "产品展示"

        category = r.get("category", "recommend")
        vibe = r.get("vibe", "温暖")
        image_count = r.get("images", 1)
        model = r.get("model", "Qwen/Qwen-Image")

        prompts = auto_generate_multi_prompts(scene, category, r.get("title", ""), vibe, image_count)

        print(f"  场景: {scene}")
        print(f"  分类: {category} | 氛围: {vibe} | 配图: {image_count} 张")

        url_list, local_list = generate_and_save_images(prompts, model)

        fp = save_draft(r.get("title", ""), content, r.get("tags", []),
                        url_list, local_list, category, prompts)
        print(f"\n  ✅ 草稿: {os.path.relpath(fp, WORKSPACE)}")
        results.append(fp)

    return results


# ============================================================
# 5. 预览
# ============================================================

def show_preview(title, content, tags, image_urls, image_locals=None):
    print("\n" + "=" * 56)
    print("  📱 小红书帖子预览")
    print("=" * 56)
    print(f"\n  📌 {title}\n")
    for line in content.split("\n"):
        print(f"  {line}")
    print()
    print("  " + " ".join([f"#{t}" for t in tags]))
    if image_urls:
        print()
        for i, (url, local) in enumerate(
            zip(image_urls, image_locals or [""] * len(image_urls)), 1
        ):
            status = f"📁 {local}" if local else f"🔗 {url[:50]}..."
            print(f"  🖼️  配图 {i}: {status}")
    print("=" * 56)


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="🍒 小红书内容生成 Pipeline v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
快速开始:
  # 单篇完整生成
  python3 scripts/xiaohongshu_pipeline.py generate --title "标题" \\
      --file content.txt --category recommend --images 2

  # 批量生成
  python3 scripts/xiaohongshu_pipeline.py batch recipes.json

  # 查看草稿
  python3 scripts/xiaohongshu_pipeline.py list
        """)
    sub = parser.add_subparsers(dest="command")

    # ── generate ──
    gp = sub.add_parser("generate", help="完整流程：文案+多图生成+存草稿")
    gp.add_argument("--title", required=True)
    gp.add_argument("--content", help="正文（可选，未提供则从stdin）")
    gp.add_argument("--file", help="从文件读正文")
    gp.add_argument("--tags", nargs="+", default=[])
    gp.add_argument("--category", default="recommend",
                    choices=["recommend", "checkin", "daily", "knowledge"])
    gp.add_argument("--scene", help="配图场景（自动推断或手动指定）")
    gp.add_argument("--vibe", default="温暖",
                    choices=["温暖", "清新", "复古", "高级", "活泼", "治愈"])
    gp.add_argument("--images", type=int, default=1, help="配图数量 (1-3)")
    gp.add_argument("--model", default="Qwen/Qwen-Image",
                    choices=["Qwen/Qwen-Image", "Kwai-Kolors/Kolors",
                             "Tongyi-MAI/Z-Image", "Tongyi-MAI/Z-Image-Turbo",
                             "baidu/ERNIE-Image-Turbo"])
    gp.add_argument("--no-image", action="store_true", help="只存文案不出图")
    gp.add_argument("--preview-only", action="store_true", help="只预览不保存")
    gp.add_argument("--html", action="store_true", help="同时生成 HTML 预览页面")

    # ── prompt ──
    pp = sub.add_parser("prompt", help="生成配图 prompt 预览")
    pp.add_argument("--scene", required=True)
    pp.add_argument("--category", default="recommend",
                    choices=["recommend", "checkin", "daily", "knowledge"])
    pp.add_argument("--product", default="")
    pp.add_argument("--vibe", default="温暖",
                    choices=["温暖", "清新", "复古", "高级", "活泼", "治愈"])
    pp.add_argument("--images", type=int, default=2, help="生成几个角度的 prompt")

    # ── image ──
    ip = sub.add_parser("image", help="单张出图（已有 prompt）")
    ip.add_argument("prompt")
    ip.add_argument("--model", default="Qwen/Qwen-Image",
                    choices=["Qwen/Qwen-Image", "Kwai-Kolors/Kolors",
                             "Tongyi-MAI/Z-Image", "Tongyi-MAI/Z-Image-Turbo",
                             "baidu/ERNIE-Image-Turbo"])
    ip.add_argument("--size", default="1024x1024")
    ip.add_argument("--save", action="store_true", help="下载到本地")

    # ── list ──
    sub.add_parser("list", help="列出草稿")

    # ── view ──
    vp = sub.add_parser("view", help="查看草稿内容")
    vp.add_argument("filename", help="草稿文件名或路径")

    # ── publish ──
    pp = sub.add_parser("publish", help="发布就绪：格式化草稿+复制到剪贴板")
    pp.add_argument("draft", help="草稿文件名或路径")
    pp.add_argument("--no-copy", action="store_true", help="不复制到剪贴板")

    # ── batch ──
    bp = sub.add_parser("batch", help="批量生成（从 JSON 文件）")
    bp.add_argument("file", help="JSON 配置文件路径")
    bp.add_argument("--model", default="Qwen/Qwen-Image")

    args = parser.parse_args()

    # ────────── generate ──────────
    if args.command == "generate":
        content = args.content
        if not content and args.file:
            fp = os.path.join(WORKSPACE, args.file) if not os.path.isabs(args.file) else args.file
            with open(fp, encoding="utf-8") as f:
                content = f.read()
        if not content:
            print("⌨️  输入正文（Ctrl+D 结束）:")
            content = sys.stdin.read()
        if not content.strip():
            print("❌ 正文不能为空")
            sys.exit(1)

        # 推断场景
        scene = args.scene
        if not scene:
            first = [l.strip() for l in content.split("\n") if l.strip()][:3]
            scene = "，".join(first)[:80] or "产品展示"

        # 生成多角度 prompts
        image_count = min(max(args.images, 1), 3)
        prompts = auto_generate_multi_prompts(scene, args.category, args.title, args.vibe, image_count)

        print(f"\n📝 配图 Prompts ({len(prompts)} 张):")
        for i, p in enumerate(prompts, 1):
            print(f"   [{i}] {p[:70]}...")

        # 出图
        url_list = []
        local_list = []
        if not args.no_image:
            print(f"\n🖼️  正在生成 {len(prompts)} 张配图...")
            url_list, local_list = generate_and_save_images(prompts, args.model)

        # 预览
        show_preview(args.title, content, args.tags, url_list, local_list)

        if args.preview_only:
            print("\n🔍 预览模式，未保存")
            return

        # 保存
        fp = save_draft(args.title, content, args.tags, url_list, local_list,
                       args.category, prompts)
        print(f"\n✅ 草稿已保存: {os.path.relpath(fp, WORKSPACE)}")
        
        # 可选：生成 HTML 预览
        if args.html:
            preview_script = os.path.join(AGENT_DIR, "scripts", "preview_post.py")
            if os.path.exists(preview_script):
                result = subprocess.run(
                    ["python3", preview_script, "render", fp],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    print("   📄 HTML 预览已生成")
                else:
                    print(f"   ⚠️  HTML 生成失败: {result.stderr.strip()}")

    # ────────── prompt ──────────
    elif args.command == "prompt":
        count = min(max(args.images, 1), 3)
        prompts = auto_generate_multi_prompts(args.scene, args.category, args.product, args.vibe, count)
        print(f"\n📝 配图 Prompts ({count} 张):\n")
        for i, p in enumerate(prompts, 1):
            print(f"  [{i}] {p}")
            print()

    # ────────── image ──────────
    elif args.command == "image":
        print(f"🖼️  生成中: {args.prompt[:60]}...")
        urls = generate_image(args.prompt, args.model, args.size)
        if urls:
            print(f"   ✅ URL: {urls[0]}")
            if args.save:
                local = download_image(urls[0])
                print(f"   📁 已下载: {local}")

    # ────────── list ──────────
    elif args.command == "list":
        list_drafts()

    # ────────── view ──────────
    elif args.command == "view":
        view_draft(args.filename)

    # ────────── publish ──────────
    elif args.command == "publish":
        draft_path = args.draft
        if not os.path.isabs(draft_path):
            draft_path = os.path.join(os.getcwd(), draft_path)
        if not os.path.exists(draft_path):
            posts_path = os.path.join(AGENT_DIR, "output", "posts", args.draft)
            if os.path.exists(posts_path):
                draft_path = posts_path
        if not os.path.exists(draft_path):
            print(f"❌ 未找到草稿: {args.draft}")
            sys.exit(1)
        
        text, info, copied = publish_draft(draft_path, copy_clipboard=not args.no_copy)
        show_publish_output(text, info, copied)

    # ────────── batch ──────────
    elif args.command == "batch":
        fp = args.file if os.path.isabs(args.file) else os.path.join(WORKSPACE, args.file)
        if not os.path.exists(fp):
            print(f"❌ 文件不存在: {fp}")
            sys.exit(1)
        with open(fp, encoding="utf-8") as f:
            if fp.endswith(".json"):
                data = json.load(f)
            else:
                print("❌ 仅支持 JSON 格式")
                sys.exit(1)
        recipes = data if isinstance(data, list) else [data]
        print(f"\n📦 批量生成: {len(recipes)} 篇帖子\n")
        results = batch_generate(recipes)
        print(f"\n{'='*50}")
        print(f"✅ 批量完成: {len(results)}/{len(recipes)} 篇成功")

    else:
        parser.print_help()


def format_for_publish(title, content, tags, image_paths=None):
    """
    格式化帖子为"小红书发布就绪"格式。
    
    返回:
      text: str - 可直接粘贴到小红书编辑器的文本
      info: dict - 发布辅助信息
    """
    # 构建发布文本（标题 + 空行 + 正文 + 空行 + 标签）
    tags_str = " ".join([f"#{t}" for t in tags])
    text = title + "\n\n" + content + "\n\n" + tags_str
    
    # 辅助信息
    char_count = len(text.replace("\n", "").replace(" ", ""))
    line_count = len(text.strip().split("\n"))
    
    info = {
        "char_count": char_count,
        "line_count": line_count,
        "image_count": len(image_paths) if image_paths else 0,
        "xhs_limit_ok": char_count <= 1000,
        "images": image_paths or [],
    }
    
    return text, info


def publish_draft(filepath, copy_clipboard=True):
    """
    将草稿格式化为发布就绪格式并输出。
    
    参数:
      filepath: str - 草稿路径
      copy_clipboard: bool - macOS 下复制到剪贴板
    
    返回:
      str - 格式化后的发布文本
    """
    # 使用已有的 parse 逻辑读草稿
    # 直接解析 markdown 文件提取内容
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    
    # 提取标题（第一个 # 开头的行）
    title = ""
    for line in raw.split("\n"):
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m:
            title = m.group(1).strip()
            # 去掉 emoji 前缀
            title = re.sub(r'^[🏆📍☀️📖📝]\s+', '', title)
            break
    
    # 提取正文（去掉 frontmatter 和 # 行，停到 ## 配图）
    body_parts = []
    in_frontmatter = False
    in_body = False
    in_images = False
    
    for line in raw.split("\n"):
        stripped = line.strip()
        
        if stripped == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                in_frontmatter = False
                in_body = True
                continue
        
        if in_frontmatter:
            continue
        
        if stripped.startswith("## 配图") or stripped.startswith("### 配图") or stripped.startswith("## 📝 生成记录"):
            in_images = True
            break
        
        if stripped.startswith("# "):
            continue  # 跳过标题行
        
        if stripped.startswith("!["):
            continue
        
        # 跳过标签行
        tag_line = re.match(r'^(#[^\s#]+[\s#]*)+\s*$', stripped)
        if tag_line:
            continue
        
        if stripped.startswith("- **") or stripped.startswith("---"):
            continue
        
        if in_body:
            body_parts.append(stripped)
    
    # 合并多余空行（最多保留一个连续空行）
    body = "\n".join(body_parts)
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    body = body.strip()
    
    # 提取标签
    tags = []
    for line in raw.split("\n"):
        tags_found = re.findall(r'#([\u4e00-\u9fa5\w]+)', line)
        tags.extend(t for t in tags_found if t not in ['配图', '分类', '创建', '状态', '配图数', '生成记录'])
    tags = list(dict.fromkeys(tags))  # 去重保序
    
    # 提取本地图片路径
    image_paths = []
    for line in raw.split("\n"):
        m = re.search(r'本地: (.*\.png)', line)
        if m:
            image_paths.append(os.path.join(AGENT_DIR, m.group(1)))
    
    # 格式化
    text, info = format_for_publish(title, body, tags, image_paths)
    
    # macOS 剪贴板
    if copy_clipboard and sys.platform == "darwin":
        try:
            import subprocess
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
            proc.communicate(text)
            copied = True
        except:
            copied = False
    else:
        copied = False
    
    return text, info, copied


def show_publish_output(text, info, copied):
    """显示发布就绪输出"""
    print("\n" + "=" * 56)
    print("  📤 小红书发布就绪")
    print("=" * 56)
    
    print("\n  📝 正文（可直接复制）:\n")
    for line in text.split("\n"):
        print(f"  {line}")
    
    print(f"\n  {'='*52}")
    print(f"  📊 发布信息")
    print(f"  {'='*52}")
    print(f"  字符数: {info['char_count']} / 1000 ", end="")
    print("✅" if info['char_count'] <= 1000 else f"⚠️  超了 {info['char_count'] - 1000} 字")
    print(f"  行数: {info['line_count']}")
    print(f"  配图: {info['image_count']} 张")
    
    if info['images']:
        print(f"  图片路径:")
        for img in info['images']:
            print(f"    📁 {img}")
    
    if copied:
        print(f"  📋 已复制到剪贴板 ✅")
    else:
        print(f"  💡 使用: python3 -c \"import pyperclip; pyperclip.copy(open('...').read())\"")
    
    print("=" * 56)
    print("  📱 手动发布步骤:")
    print(f"  1. 打开小红书 App")
    print(f"  2. 点击 + 号 → 上传图片")
    print(f"  3. 粘贴正文到编辑框")
    print(f"  4. 检查格式后发布")
    print("=" * 56)


if __name__ == "__main__":
    main()
