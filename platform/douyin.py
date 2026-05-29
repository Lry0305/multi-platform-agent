#!/usr/bin/env python3
"""
DouyinPublisher - 抖音发布器 🚧 开发中

TODO:
  - 对接抖音开放平台 API
  - 支持视频/图文发布
  - 话题标签格式化
"""

from .base import BasePublisher, Post


class DouyinPublisher(BasePublisher):
    """抖音适配器（开发中）"""

    @property
    def platform_name(self) -> str:
        return "抖音"

    @property
    def max_title_length(self) -> int:
        return 55  # 抖音标题限制

    @property
    def max_content_length(self) -> int:
        return 1000

    @property
    def max_images(self) -> int:
        return 35  # 抖音图文最多35张

    def format_post(self, post: Post) -> str:
        """抖音格式排版（开发中）"""
        parts = []
        parts.append(post.title)
        parts.append("")

        # 抖音正文一般较短
        parts.append(post.content[:500])
        parts.append("")

        # 话题标签
        if post.tags:
            tags_str = " ".join([f"#{t}" for t in post.tags])
            parts.append(tags_str)

        return "\n".join(parts)

    def publish(self, post: Post, post_text: str) -> dict:
        """
        发布到抖音（开发中，暂未对接 API）
        """
        print("\n🚧 [抖音] API 对接开发中，暂不能自动发布")
        print("   请手动复制内容到抖音。")
        print(f"\n{post_text}\n")
        return {
            "status": "manual",
            "message": "抖音发布 API 开发中，请手动发布",
            "url": "",
        }
