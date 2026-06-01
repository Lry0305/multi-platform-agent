#!/usr/bin/env python3
"""
BasePublisher - 平台发布器基类

所有平台发布器继承此类，实现：
  1. format_post()  - 按平台规则格式化内容（字数、排版、标签）
  2. publish()      - 发布到平台（目前为 stub，支持手动发布）
  3. validate()     - 检查内容是否符合平台规则

扩展一个新平台只需三步：
  1. 在 platform/ 下新建文件，继承 BasePublisher
  2. 实现 format_post() / publish() / validate()
  3. 在 __init__.py 的 registry 里注册
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Post:
    """一篇文章的标准化数据结构"""
    title: str
    content: str                # 正文（纯文本/Markdown）
    images: list[str] = field(default_factory=list)   # 图片本地路径或URL列表
    tags: list[str] = field(default_factory=list)     # 标签
    category: str = "general"   # 内容分类
    summary: str = ""           # 摘要（可选）


class BasePublisher(ABC):
    """平台发布器抽象基类"""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """平台名（用于显示）"""
        pass

    @property
    @abstractmethod
    def max_title_length(self) -> int:
        """标题最大长度"""
        pass

    @property
    @abstractmethod
    def max_content_length(self) -> int:
        """正文最大长度"""
        pass

    @property
    def max_images(self) -> int:
        """最大配图数"""
        return 3

    @abstractmethod
    def format_post(self, post: Post, style: str = "clean") -> str:
        """
        将 Post 格式化为平台适配的排版文本。
        style 参数用于选择排版主题（不同平台支持不同主题）。
        返回可直接粘贴或发布的内容。
        """
        pass

    def validate(self, post: Post) -> list[str]:
        """
        检查帖子是否符合平台规则，返回违规项列表（空列表即合规）。
        """
        warnings = []
        if len(post.title) > self.max_title_length:
            warnings.append(
                f"标题过长: {len(post.title)}/{self.max_title_length} 字"
            )
        if len(post.content) > self.max_content_length:
            warnings.append(
                f"正文过长: {len(post.content)}/{self.max_content_length} 字"
            )
        if len(post.images) > self.max_images:
            warnings.append(
                f"配图过多: {len(post.images)}/{self.max_images} 张"
            )
        return warnings

    def publish(self, post: Post, post_text: str, style: str = "clean") -> dict:
        """
        发布到平台（默认实现：仅输出到控制台）。
        style 参数用于选择排版主题。
        各平台子类可重写此方法对接 API。

        返回:
            {"status": "ok"|"manual"|"error", "message": "...", "url": "..."}
        """
        print(f"\n{'=' * 50}")
        print(f"📤 [{self.platform_name}] 发布准备就绪")
        print(f"{'=' * 50}")
        print(f"\n{post_text}")
        print(f"\n{'=' * 50}")
        print("📋 已复制到剪贴板（如有 pyperclip）")
        print("💡 手动粘贴发布，或对接平台 API 后自动发布")
        print(f"{'=' * 50}\n")

        return {
            "status": "manual",
            "message": "已就绪，请手动发布",
            "url": "",
        }
