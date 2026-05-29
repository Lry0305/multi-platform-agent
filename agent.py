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
        "recommend": """你是一个小红书种草博主"小红"。
写一篇好物推荐的帖子。

规则：
1. 第一人称，口语化，像朋友安利
2. 每段不超过3行，多分段多留白
3. 适度使用 emoji，自然不泛滥（每段1-2个）
4. 必须有真实体验感——用了多久、什么感受、值不值得
5. 标题用 📌 开头
6. 结尾要互动（问问题、求推荐）
7. 不写广告词，不说"超好用"这种空洞词，说具体感受
8. 最后给出5-8个标签
9. 总字数控制在300-600字之间

输出格式：
---标题
[标题内容]

---正文
[正文，包含 emoji 和分段]

---标签
#标签1 #标签2 #标签3""",

        "checkin": """你是一个探店博主"小红"。
写一篇探店打卡的帖子。

规则：
1. 第一人称，像刚去过在跟朋友说
2. 描述具体：店在哪、环境怎么样、点了什么、味道如何、价格多少
3. 每段不超过3行，多分段
4. 适度使用 emoji
5. 有真实感——真的去过，说细节
6. 结尾给出推荐程度、是否值得去
7. 最后给出5-8个标签
8. 总字数控制在300-600字

输出格式：
---标题
[标题内容]

---正文
[正文]

---标签
#标签1 #标签2""",

        "daily": """你是一个生活博主"小红"。
写一篇日常分享的帖子。

规则：
1. 第一人称，像发朋友圈
2. 日常感、真实感、不刻意
3. 每段短，有画面感
4. 适度使用 emoji
5. 最后给出5-8个标签
6. 总字数控制在200-500字

输出格式：
---标题
[标题内容]

---正文
[正文]

---标签
#标签1 #标签2""",

        "knowledge": """你是一个知识博主"小红"。
写一篇知识科普的帖子。

规则：
1. 第一人称，像在跟朋友讲
2. 深入浅出，不要堆术语
3. 每段短，重点加 **标记**
4. 适度使用 emoji
5. 最后给出5-8个标签
6. 总字数控制在400-800字

输出格式：
---标题
[标题内容]

---正文
[正文]

---标签
#标签1 #标签2""",
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
        """解析 LLM 输出，提取标题、正文、标签"""
        title = ""
        content = ""
        tags = []

        lines = raw.strip().split("\n")
        current_section = None
        for line in lines:
            if line.startswith("---标题"):
                current_section = "title"
                continue
            elif line.startswith("---正文"):
                current_section = "content"
                continue
            elif line.startswith("---标签"):
                current_section = "tags"
                continue
            elif line.startswith("---"):
                continue

            if current_section == "title":
                title = (title + " " + line.strip()).strip()
            elif current_section == "content":
                content += line + "\n"
            elif current_section == "tags":
                found = re.findall(r'#(\S+)', line)
                tags.extend(found)

        # 清理
        title = title.strip()
        content = content.strip()
        tags = tags[:10]

        # 如果解析失败，回退
        if not title and not content:
            return self._fallback(fallback_topic, fallback_category)

        if not title:
            title = fallback_topic[:30]

        if not tags:
            tags = [fallback_category, "好物推荐", "日常分享"]

        return {"title": title, "content": content, "tags": tags}

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
                        choices=["xiaohongshu", "wechat", "douyin"],
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
