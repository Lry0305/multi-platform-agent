#!/usr/bin/env python3
"""
XiaohongshuPublisher - 小红书发布器

排版规则：
  - 标题：≤20字，引人注目
  - 正文：≤1000字，多分段，每段≤3行
  - 标签：5-8个，用 # 号
  - 图片：≤3张

风格：
  - 第一人称
  - 自然口语化
  - emoji 适度使用
"""

import re
from typing import Optional
from .base import BasePublisher, Post


class XiaohongshuPublisher(BasePublisher):
    """小红书内容格式适配器"""

    @property
    def platform_name(self) -> str:
        return "小红书"

    @property
    def max_title_length(self) -> int:
        return 20

    @property
    def max_content_length(self) -> int:
        return 1000

    @property
    def max_images(self) -> int:
        return 3

    # 排版风格映射
    STYLE_NAMES = {
        "clean": "简洁风",
        "chatty": "聊天风",
        "bold": "重点加粗风",
        "diary": "日记风",
    }

    def format_post(self, post: Post, style: str = "clean") -> str:
        """
        按小红书风格排版，支持多种排版风格。

        style 可选: clean(简洁/默认), chatty(聊天), bold(加粗), diary(日记)
        """
        parts = []

        # 1. 标题（加 emoji 装饰）
        title = post.title.strip()
        title_emoji = re.match(r'^([📌📍🏆☀️📖📝🍒⚖️🎯😤🔧📦🙋💭])', title)
        if not title_emoji:
            title = f"📌 {title}"
        parts.append(title)
        parts.append("")

        # 2. 正文 - 根据风格处理
        content = post.content.strip()

        if style == "clean":
            # 简洁风：短段落、干净（默认）
            content = self._ensure_short_paragraphs(content)

        elif style == "chatty":
            # 聊天风：碎片化、多语气词
            content = self._ensure_short_paragraphs(content)
            # 在段落间插入语气词
            lines = content.split("\n\n")
            chatty_inserts = ["对，就是这种感觉",
                              "真的真的强烈安利",
                              "谁懂啊！",
                              "你们是不是也这样"]
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if i < len(lines) - 1 and i < len(chatty_inserts) and len(line.strip()) > 10:
                    new_lines.append(chatty_inserts[i])
            content = "\n\n".join(new_lines)

        elif style == "bold":
            # 重点加粗风：关键句加 **
            content = self._ensure_short_paragraphs(content)
            lines = content.split("\n\n")
            for i, line in enumerate(lines):
                line = line.strip()
                if len(line) > 15 and i < len(lines) - 1:
                    # 第一句加粗作为核心结论
                    sentences = re.split(r'[，。！？]', line, 1)
                    if len(sentences) > 1:
                        lines[i] = f"**{sentences[0]}**，{sentences[1]}"
                    elif len(line) > 10:
                        lines[i] = f"**{line}**"
            content = "\n\n".join(lines)

        elif style == "diary":
            # 日记风：日期开头 + 小尾巴
            from datetime import datetime
            today = datetime.now().strftime("%Y.%m.%d")
            content = self._ensure_short_paragraphs(content)
            content = f"📅 {today}\n\n{content}\n\n—— 今天也要开心呀 ✨"

        parts.append(content)
        parts.append("")

        # 3. 标签
        if post.tags:
            tags_str = " ".join([f"#{t}" for t in post.tags])
            parts.append(tags_str)
            parts.append("")

        # 4. 图片标记（路径提示）
        if post.images:
            parts.append("🖼️ 配图:")
            for i, img in enumerate(post.images, 1):
                parts.append(f"  [{i}] {img}")

        return "\n".join(parts)

    def validate(self, post: Post) -> list[str]:
        """小红书特定校验规则"""
        warnings = super().validate(post)

        # 标题不能太短
        if len(post.title) < 4:
            warnings.append(f"标题过短 ({len(post.title)}字)，建议至少4个字")

        # 标签数量
        if len(post.tags) < 3:
            warnings.append(f"标签太少 ({len(post.tags)}个)，建议5-8个")
        elif len(post.tags) > 10:
            warnings.append(f"标签太多 ({len(post.tags)}个)，建议不超过8个")

        # 是否有 emoji
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "\U00002600-\U000026FF"
            "\U0000FE00-\U0000FE0F"
            "]+")
        if not emoji_pattern.search(post.content):
            warnings.append("正文没有 emoji，小红书风格建议适度使用 emoji")

        return warnings

    def _ensure_short_paragraphs(self, text: str) -> str:
        """确保每段不超过3行，超过则按句号/逗号拆分"""
        paragraphs = text.split("\n")
        result = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            lines = len(para) // 30 + 1  # 大约每30字一行估算
            if lines > 3 and "。" in para or "，" in para:
                # 按句号拆分
                sentences = re.split(r'[。！？]', para)
                new_para = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(new_para) + len(sent) > 50:
                        result.append(new_para.rstrip("，"))
                        new_para = sent + "，"
                    else:
                        new_para += sent + "，"
                if new_para:
                    result.append(new_para.rstrip("，"))
            else:
                result.append(para)
        return "\n\n".join(result)
