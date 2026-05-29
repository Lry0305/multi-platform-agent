#!/usr/bin/env python3
"""
🍒 多平台内容发布 Agent

核心流程（端到端）：
  主题/灵感 → LLM 写文案 → 自动配图 prompt → 生成配图 → 
  平台格式化 → 生成草稿 → (可选)自动发布

这是真正的 "agent" 大脑。pipeline 是工具，agent 是做决策的那个。

用法:
  # 完整流程：给个主题，自动出一篇
  python3 agent.py \
      --topic "最近入了这款护手霜，真的惊艳到我了" \
      --platform xiaohongshu \
      --images 2

  # 指定分类和氛围
  python3 agent.py \
      --topic "周末去了一家藏在巷子里的咖啡馆" \
      --platform xiaohongshu \
      --category checkin \
      --vibe 温暖

  # 只出文案+配图prompt，不出图
  python3 agent.py \
      --topic "推荐3款平价好用的面膜" \
      --platform xiaohongshu \
      --dry-run

  # 交互模式：agent 主动问你要什么
  python3 agent.py --interactive

环境变量: 见 .env.example
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional

# 加载配置
from config import get_config, validate_config

# 平台 SDK
from platform import get_publisher, list_supported_platforms
from platform.base import Post


# ============================================================
# LLM 文案生成（硅基流动 API）
# ============================================================

class ContentGenerator:
    """文案生成器 - 使用 LLM 从主题生成小红书风格文案"""

    # 各内容方向的写作风格
    SYSTEM_PROMPTS = {
        "recommend": """你扮演一个会写小红书文案的助手。根据用户主题，输出三部分内容。

写作规则：
- 第一人称，口语化，像朋友安利
- 每段不超过3行，多分段多留白
- 适度使用 emoji（每段1-2个）
- 有真实体验感，不写空洞广告词
- 结尾有互动
- 总字数300-600字

输出格式（必须严格按以下标记）：
【TITLE】
一行标题

【CONTENT】
正文，多段落

【TAGS】
#标签1 #标签2 #标签3""",

        "checkin": """你扮演一个会写小红书探店文案的助手。根据用户主题，输出三部分内容。

写作规则：
- 第一人称，像刚去过在跟朋友说
- 写具体：店在哪、环境、点了什么、味道、价格
- 每段不超过3行
- 适度使用 emoji
- 结尾给出推荐程度
- 总字数300-600字

输出格式（必须严格按以下标记）：
【TITLE】
一行标题

【CONTENT】
正文，多段落

【TAGS】
#标签1 #标签2 #标签3""",

        "daily": """你扮演一个会写小红书日常分享文案的助手。根据用户主题，输出三部分内容。

写作规则：
- 第一人称，像发朋友圈
- 日常感、真实感
- 每段短，有画面感
- 适度使用 emoji
- 总字数200-500字

输出格式（必须严格按以下标记）：
【TITLE】
一行标题

【CONTENT】
正文，多段落

【TAGS】
#标签1 #标签2 #标签3""",

        "knowledge": """你扮演一个会写小红书知识科普文案的助手。根据用户主题，输出三部分内容。

写作规则：
- 第一人称，像在跟朋友讲
- 深入浅出，不要堆术语
- 每段短，重点加**加粗**
- 适度使用 emoji
- 总字数400-800字

输出格式（必须严格按以下标记）：
【TITLE】
一行标题

【CONTENT】
正文，多段落

【TAGS】
#标签1 #标签2 #标签3""",
    }

    def __init__(self, api_key: str, model: str = "Qwen/Qwen2.5-7B-Instruct"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"

    def generate(self, topic: str, category: str = "recommend",
                 extra_instructions: str = "") -> dict:
        """
        从主题生成完整文案。
        返回: {"title": str, "content": str, "tags": list[str]}
        """
        system_prompt = self.SYSTEM_PROMPTS.get(
            category, self.SYSTEM_PROMPTS["recommend"]
        )

        if extra_instructions:
            system_prompt += f"\n\n额外要求：{extra_instructions}"

        user_prompt = f"主题：{topic}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 1500,
        }

        import urllib.request
        import json as _json

        data = _json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.api_url, data=data, method="POST"
        )
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            resp = urllib.request.urlopen(req, timeout=60)
            result = _json.loads(resp.read().decode("utf-8"))
            raw_text = result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"⚠️  LLM 调用失败: {e}")
            print("   回退到基础模板...")
            return self._fallback(topic, category)

        return self._parse_output(raw_text, topic, category)

    def _parse_output(self, raw: str, fallback_topic: str,
                      fallback_category: str) -> dict:
        """解析 LLM 输出，提取标题、正文、标签

        支持多种标记格式：
          - 中文：【TITLE】【CONTENT】【TAGS】
          - 英文：[TITLE][CONTENT][TAGS]
          - Markdown：---标题 ---正文 ---标签
        """
        title = ""
        content = ""
        tags = []

        lines = raw.strip().split("\n")
        current_section = None

        for line in lines:
            stripped = line.strip()
            low = stripped.lower()

            if not stripped:
                if current_section == "content":
                    content += "\n"
                continue

            # 跳过不关心的分区
            if re.search(r'【\s*(价格|ending|结尾|总结|summary)\s*】', low) or \
               re.match(r'^---\s*(价格|ending|结尾|总结|summary)', low):
                current_section = None
                continue

            # 检测分区标记
            switched = False
            if re.search(r'【\s*title\s*】|【\s*标题\s*】|\[\s*title\s*\]', low) or \
               re.match(r'^---\s*标题|^---\s*title', low):
                current_section = "title"
                switched = True
            elif re.search(r'【\s*content\s*】|【\s*正文\s*】|\[\s*content\s*\]', low) or \
                 re.match(r'^---\s*正文|^---\s*content', low):
                current_section = "content"
                switched = True
            elif re.search(r'【\s*tags\s*】|【\s*标签\s*】|\[\s*tags\s*\]', low) or \
                 re.match(r'^---\s*标签|^---\s*tags?', low):
                current_section = "tags"
                switched = True
            if switched:
                continue

            # 按当前分区收集内容
            if current_section == "title":
                if title:
                    title += " " + stripped
                else:
                    title = stripped
            elif current_section == "content":
                content += stripped + "\n"
            elif current_section == "tags":
                found = re.findall(r'#(\S+)', stripped)
                tags.extend(found)

        # 如果标记解析失败（模型完全没按格式走）
        # 尝试直接解析：第一行为标题，其余为正文，末尾找#标签
        if not title and not content:
            # 找到第一个含#的行前面的内容作为正文
            tag_line_idx = -1
            for i, line in enumerate(lines):
                if '#' in line and re.search(r'#\S+', line):
                    tag_line_idx = i
                    break

            if tag_line_idx > 0:
                title = lines[0].strip()[:40]
                content = "\n".join(lines[1:tag_line_idx]).strip()
                tags = re.findall(r'#(\S+)', "\n".join(lines[tag_line_idx:]))
            elif len(lines) > 0:
                title = lines[0].strip()[:40]
                content = "\n".join(lines[1:]).strip()

        # 清理
        title = _clean_title(title)
        content = content.strip()
        tags = tags[:10]

        # 如果解析出来是空的或太短，回退
        if len(content) < 10:
            return self._fallback(fallback_topic, fallback_category)

        if not title:
            title = fallback_topic[:30]

        if not tags:
            tags = [fallback_category, "好物推荐", "日常分享"]

        return {"title": title, "content": content, "tags": tags}


def _clean_title(title: str) -> str:
    """清理标题：去除非标题内容（语气词、多余空格）"""
    # 去掉像 "2 user 可以了，继续 assistant" 这样的奇怪注入
    title = re.sub(r'\d+\s*(user|assistant|system)\s*[：，,。.!！?？]*', '', title)
    # 去掉过长结尾（模型有时候会在标题后塞整段文字）
    if len(title) > 50:
        # 尝试在第一个句号/感叹号处截断
        match = re.search(r'^(.+?[。！？])', title)
        if match:
            title = match.group(1)
    return title.strip()[:60]

    def _fallback(self, topic: str, category: str) -> dict:
        """回退方案：当 LLM 调用失败时使用模板"""
        emoji_map = {
            "recommend": "🏆",
            "checkin": "📍",
            "daily": "☀️",
            "knowledge": "📖",
        }
        emoji = emoji_map.get(category, "📝")

        return {
            "title": f"{emoji} {topic[:19]}",
            "content": f"{topic}\n\n（LLM 暂时不可用，这是自动生成的基础版本）\n\n大家有没有什么好推荐？评论区告诉我吧～ 💬",
            "tags": [category, "好物推荐", "日常分享"],
        }


# ============================================================
# 配图场景推断
# ============================================================

def infer_scene(title: str, content: str, category: str) -> str:
    """从文案推断配图场景"""
    # 取前几句最有画面感的
    lines = [l.strip() for l in content.split("\n") if l.strip()][:5]

    # 优先用包含具体物品/场景的句子
    keywords = ["入", "买", "用", "吃", "去", "店", "瓶", "盒", "袋"]
    for line in lines:
        if any(k in line for k in keywords):
            return line[:60]

    # 回退到标题
    return title[:60] if title else "产品展示"


# ============================================================
# 草稿保存 & 发布 (整合 pipeline)
# ============================================================

from agents.xiaohongshu.scripts.xiaohongshu_pipeline import (
    auto_generate_multi_prompts,
    generate_and_save_images,
    save_draft as pipeline_save_draft,
    show_preview,
)


def run_agent(topic: str, platform: str = "xiaohongshu",
              category: str = "recommend", vibe: str = "温暖",
              image_count: int = 2, model: str = "Qwen/Qwen-Image",
              dry_run: bool = False, extra_instructions: str = "",
              no_image: bool = False, interactive: bool = False):
    """
    运行 agent 完整流程：
    主题 → 写文案 → 配图prompt → 出图 → 平台格式化 → 存草稿 → 发布
    """
    cfg = get_config()
    missing = validate_config(cfg)
    if missing:
        print(f"❌ 缺少必要配置: {', '.join(missing)}")
        print(f"   请先设置环境变量或复制 .env.example 为 .env")
        return

    api_key = cfg.api_key
    out_dir = cfg.output_dir

    # 同步到环境变量（各模块直接从 os.environ 读）
    if api_key:
        os.environ["SILICONFLOW_API_KEY"] = api_key
    if cfg.weixin_app_id:
        os.environ["WEIXIN_APP_ID"] = cfg.weixin_app_id
    if cfg.weixin_app_secret:
        os.environ["WEIXIN_APP_SECRET"] = cfg.weixin_app_secret

    # ── 1. 写文案 ──
    print(f"\n✍️  正在写文案...（主题：{topic[:50]}...）")
    generator = ContentGenerator(api_key, cfg.default_text_model)
    result = generator.generate(topic, category, extra_instructions)

    title = result["title"]
    content = result["content"]
    tags = result["tags"]

    print(f"\n📌 标题: {title}")
    print(f"🏷️  标签: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
    print(f"📄 正文: {len(content)} 字")

    # ── 2. 配图场景推断 ──
    scene = infer_scene(title, content, category)
    print(f"\n🎨 配图场景: {scene}")

    # ── 3. 生成配图 prompt ──
    prompts = auto_generate_multi_prompts(scene, category, title, vibe, image_count)
    for i, p in enumerate(prompts, 1):
        print(f"   prompt {i}: {p[:60]}...")

    # ── 4. 出图 ──
    url_list = []
    local_list = []
    if not no_image and not dry_run:
        url_list, local_list = generate_and_save_images(prompts, model)
    elif dry_run:
        print("\n⏭️  Dry-run 模式：跳过出图")

    # ── 5. 平台格式化 ──
    publisher = get_publisher(platform)
    post = Post(
        title=title,
        content=content,
        images=local_list or url_list,
        tags=tags,
        category=category,
    )

    # 校验
    warnings = publisher.validate(post)
    if warnings:
        print("\n⚠️  平台规则提醒:")
        for w in warnings:
            print(f"   • {w}")

    formatted = publisher.format_post(post)

    # ── 6. 预览 ──
    print(f"\n📱 [{publisher.platform_name}] 预览:")
    show_preview(title, content, tags, url_list, local_list)

    # ── 7. 存草稿 ──
    if not dry_run:
        draft_path = pipeline_save_draft(
            title, content, tags, url_list, local_list, category, prompts
        )
        print(f"\n💾 草稿已保存: {os.path.relpath(draft_path, os.getcwd())}")
    else:
        print("\n⏭️  Dry-run 模式：跳过保存")

    # ── 8. 发布 ──
    pub_result = publisher.publish(post, formatted)

    return {
        "title": title,
        "content": content,
        "tags": tags,
        "images": local_list or url_list,
        "draft_path": draft_path if not dry_run else None,
        "publish_result": pub_result,
    }


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="🍒 多平台内容发布 Agent - 端到端内容生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 快速出一篇小红书帖子
  python3 agent.py --topic "最近用的护手霜" --platform xiaohongshu

  # 指定分类和氛围
  python3 agent.py --topic "周末探店" --category checkin --vibe 复古

  # 只出文案和prompt，不出图
  python3 agent.py --topic "3款面膜推荐" --dry-run

  # 交互模式
  python3 agent.py --interactive

  # 指定平台（开发中，仅小红书可用）
  python3 agent.py --topic "..." --platform wechat
        """)

    parser.add_argument("--topic", help="主题/灵感（一句话）")
    parser.add_argument("--platform", default="xiaohongshu",
                        choices=["xiaohongshu", "wechat", "douyin", "微信", "公众号"],
                        help="目标平台")
    parser.add_argument("--category", default="recommend",
                        choices=["recommend", "checkin", "daily", "knowledge"],
                        help="内容分类")
    parser.add_argument("--vibe", default="温暖",
                        choices=["温暖", "清新", "复古", "高级", "活泼", "治愈"],
                        help="配图氛围")
    parser.add_argument("--images", type=int, default=2,
                        help="配图数量 (1-3)")
    parser.add_argument("--model", default="Qwen/Qwen-Image",
                        help="配图模型")
    parser.add_argument("--dry-run", action="store_true",
                        help="只生成文案和 prompt，不出图/不保存")
    parser.add_argument("--no-image", action="store_true",
                        help="不出图（仅文案）")
    parser.add_argument("--extra", default="",
                        help="额外写作指令（如：语气更活泼、突出性价比）")
    parser.add_argument("--interactive", action="store_true",
                        help="交互模式")

    args = parser.parse_args()

    if args.interactive:
        print("\n🍒 小红内容 Agent - 交互模式")
        print("输入你的灵感/主题，我来帮你写一篇帖子。")
        print("输入 q 退出。\n")
        while True:
            try:
                topic = input("📝 灵感 > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 拜拜～")
                break
            if not topic or topic.lower() == "q":
                print("👋 拜拜～")
                break

            platform = input(f"  平台 [{args.platform}] > ").strip() or args.platform
            category = input(f"  分类 [{args.category}] > ").strip() or args.category
            vibe = input(f"  氛围 [{args.vibe}] > ").strip() or args.vibe

            run_agent(
                topic=topic,
                platform=platform,
                category=category,
                vibe=vibe,
                image_count=args.images,
                model=args.model,
                dry_run=args.dry_run,
                no_image=args.no_image,
            )
            print()
    else:
        if not args.topic:
            parser.print_help()
            sys.exit(1)

        run_agent(
            topic=args.topic,
            platform=args.platform,
            category=args.category,
            vibe=args.vibe,
            image_count=args.images,
            model=args.model,
            dry_run=args.dry_run,
            no_image=args.no_image,
            extra_instructions=args.extra,
        )


if __name__ == "__main__":
    main()
