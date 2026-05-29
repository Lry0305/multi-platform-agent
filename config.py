#!/usr/bin/env python3
"""
多平台内容发布 Agent - 配置加载模块

读取顺序：
  1. 环境变量（最高优先级）
  2. .env 文件（如果存在）
  3. 默认值

用法：
  from config import get_config, Config
  cfg = get_config()
  print(cfg.api_key)
"""

import os
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """全局配置"""
    # 必须
    api_key: str = ""
    
    # 输出
    output_dir: str = "./output"
    
    # 配图
    default_image_model: str = "Qwen/Qwen-Image"
    default_image_size: str = "1024x1024"
    
    # 微信发布（开发中）
    weixin_app_id: str = ""
    weixin_app_secret: str = ""
    
    # 抖音发布（开发中）
    douyin_access_token: str = ""
    
    # 文案生成
    default_text_model: str = "Qwen/Qwen2.5-7B-Instruct"


def _load_dotenv(path: str = ".env") -> dict:
    """加载 .env 文件，返回键值对"""
    if not os.path.exists(path):
        return {}
    
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r'^([^=]+)=(.*)$', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                # 去掉引号
                value = value.strip("'\"")
                env[key] = value
    return env


def get_config(env_path: str = ".env") -> Config:
    """
    加载配置。
    优先级：环境变量 > .env 文件 > 默认值
    """
    dotenv = _load_dotenv(env_path)
    
    def _get(key: str, default: str = "") -> str:
        return os.environ.get(key, dotenv.get(key, default))
    
    cfg = Config(
        api_key=_get("SILICONFLOW_API_KEY"),
        output_dir=_get("OUTPUT_DIR", "./output"),
        default_image_model=_get("DEFAULT_IMAGE_MODEL", "Qwen/Qwen-Image"),
        default_image_size=_get("DEFAULT_IMAGE_SIZE", "1024x1024"),
        weixin_app_id=_get("WEIXIN_APP_ID"),
        weixin_app_secret=_get("WEIXIN_APP_SECRET"),
        douyin_access_token=_get("DOUYIN_ACCESS_TOKEN"),
        default_text_model=_get("DEFAULT_TEXT_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
    )
    
    return cfg


def validate_config(cfg: Config) -> list[str]:
    """检查配置是否完整，返回缺失项列表"""
    missing = []
    if not cfg.api_key:
        missing.append("SILICONFLOW_API_KEY")
    return missing


if __name__ == "__main__":
    cfg = get_config()
    missing = validate_config(cfg)
    if missing:
        print(f"⚠️  缺少必要配置: {', '.join(missing)}")
        print(f"   请复制 .env.example 为 .env 并填入 API Key")
    else:
        print("✅ 配置加载成功")
        print(f"   API Key: {cfg.api_key[:8]}...{cfg.api_key[-4:] if len(cfg.api_key) > 12 else ''}")
        print(f"   输出目录: {cfg.output_dir}")
        print(f"   配图模型: {cfg.default_image_model}")
