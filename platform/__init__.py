"""
Platform SDK - 多平台内容发布抽象层

提供统一的发布接口，各平台继承 BasePublisher 实现具体逻辑。

当前已实现:
  - XiaohongshuPublisher  ✅

开发中:
  - WechatPublisher       🚧
  - DouyinPublisher       🚧
"""

from .base import BasePublisher
from .xiaohongshu import XiaohongshuPublisher
from .wechat import WechatPublisher


def get_publisher(platform: str) -> BasePublisher:
    """工厂方法：根据平台名获取发布器实例"""
    registry = {
        "xiaohongshu": XiaohongshuPublisher,
        "小红书": XiaohongshuPublisher,
        "wechat": WechatPublisher,
        "微信": WechatPublisher,
        "公众号": WechatPublisher,
    }
    if platform not in registry:
        available = ", ".join(registry.keys())
        raise ValueError(f"不支持的平台: '{platform}'。当前支持: {available}")
    return registry[platform]()


def list_supported_platforms() -> list[str]:
    """列出所有已注册的平台"""
    return ["xiaohongshu", "wechat", "douyin"]
