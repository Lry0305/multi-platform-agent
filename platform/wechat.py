#!/usr/bin/env python3
"""
WechatPublisher - 微信公众平台发布器

对接了微信公众平台 API，支持：
  - 自动获取/刷新 access_token
  - 上传图片到微信 CDN
  - 创建图文草稿
  - 发布已保存的草稿

用法：
  先在 .env 配好：
    WEIXIN_APP_ID=wx...
    WEIXIN_APP_SECRET=...

  然后：
    python3 agent.py --topic "..." --platform wechat --images 1

注意：
  1. 需要已认证的公众号（个人订阅号可能没有草稿箱权限）
  2. 封面图会自动用第一张配图
  3. 正文支持 HTML 标签（微信编辑器是富文本）
"""

import json
import os
import time
import urllib.request
import urllib.error
from typing import Optional

from .base import BasePublisher, Post


class WechatPublisher(BasePublisher):
    """微信公众平台发布器"""

    API_BASE = "https://api.weixin.qq.com/cgi-bin"

    def __init__(self):
        self._token = ""
        self._token_expires_at = 0
        self._app_id = os.environ.get("WEIXIN_APP_ID", "")
        self._app_secret = os.environ.get("WEIXIN_APP_SECRET", "")

    @property
    def platform_name(self) -> str:
        return "微信公众平台"

    @property
    def max_title_length(self) -> int:
        return 64

    @property
    def max_content_length(self) -> int:
        return 20000

    @property
    def max_images(self) -> int:
        return 10

    # ── Token 管理 ──

    def _get_access_token(self) -> str:
        """获取 access_token，带缓存和自动刷新"""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        if not self._app_id or not self._app_secret:
            raise ValueError(
                "请在 .env 中配置 WEIXIN_APP_ID 和 WEIXIN_APP_SECRET"
            )

        url = (f"{self.API_BASE}/token"
               f"?grant_type=client_credential"
               f"&appid={self._app_id}"
               f"&secret={self._app_secret}")

        resp = self._get_json(url)
        if "access_token" not in resp:
            raise RuntimeError(f"获取 token 失败: {resp.get('errmsg', resp)}")

        self._token = resp["access_token"]
        self._token_expires_at = time.time() + resp.get("expires_in", 6000) - 300
        return self._token

    # ── HTTP 请求 ──

    def _get_json(self, url: str) -> dict:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post_json(self, url: str, data: dict) -> dict:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _check_error(self, resp: dict):
        """检查微信 API 返回的错误码"""
        errcode = resp.get("errcode", 0)
        if errcode != 0:
            raise RuntimeError(
                f"微信 API 错误 [{errcode}]: {resp.get('errmsg', '未知错误')}"
            )

    # ── 图片上传 ──

    def _upload_image(self, image_path: str) -> str:
        """
        上传图片到微信永久素材库。
        返回微信的图片 URL。
        """
        token = self._get_access_token()
        url = f"{self.API_BASE}/material/add_material?access_token={token}&type=image"

        # 判断是本地文件还是 URL
        if image_path.startswith("http://") or image_path.startswith("https://"):
            # 下载到临时文件再上传
            import tempfile
            req = urllib.request.Request(image_path)
            with urllib.request.urlopen(req, timeout=30) as resp:
                img_data = resp.read()
            suffix = ".png"
            if resp.headers.get("Content-Type", "").startswith("image/jpeg"):
                suffix = ".jpg"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(img_data)
                tmp_path = tmp.name
            try:
                return self._upload_local_image(url, tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            # 本地文件
            if not os.path.exists(image_path):
                # 尝试从项目根目录拼接
                alt_path = os.path.join(os.getcwd(), image_path)
                if os.path.exists(alt_path):
                    image_path = alt_path
                else:
                    print(f"  ⚠️  找不到图片: {image_path}")
                    return ""
            return self._upload_local_image(url, image_path)

    def _upload_local_image(self, url: str, filepath: str) -> str:
        """上传本地图片文件到微信"""
        import uuid
        boundary = "----" + str(uuid.uuid4()).replace("-", "")
        filename = os.path.basename(filepath)

        with open(filepath, "rb") as f:
            file_data = f.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
            f"Content-Type: image/png\r\n\r\n"
        ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if "url" not in result:
            print(f"  ⚠️  上传图片失败: {result.get('errmsg', result)}")
            return ""
        return result["url"]

    # ── 草稿管理 ──

    def _create_draft(self, post: Post, cover_url: str = "", theme: str = "clean") -> str:
        """
        创建图文草稿。
        返回 media_id。
        """
        token = self._get_access_token()
        url = f"{self.API_BASE}/draft/add?access_token={token}"

        # 正文：把 Markdown 转成微信支持的 HTML（按主题排版）
        content_html = self._md_to_wechat_html(post.content, theme=theme)

        article = {
            "title": post.title,
            "content": content_html,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }

        if cover_url:
            article["thumb_media_id"] = cover_url
        else:
            # 用正文第一张图做封面
            article["thumb_media_id"] = ""

        if post.summary:
            article["digest"] = post.summary[:120]

        payload = {
            "articles": [article]
        }

        result = self._post_json(url, payload)
        self._check_error(result)

        media_id = result.get("media_id", "")
        print(f"  ✅ 草稿已创建: media_id={media_id}")
        return media_id

    # ── 发布 ──

    def _submit_publish(self, media_id: str) -> str:
        """
        提交发布草稿。
        返回 publish_id（可用于查询发布状态）。
        """
        token = self._get_access_token()
        url = f"{self.API_BASE}/freepublish/submit?access_token={token}"

        payload = {"media_id": media_id}
        result = self._post_json(url, payload)
        self._check_error(result)

        publish_id = result.get("publish_id", "")
        print(f"  ✅ 已提交发布: publish_id={publish_id}")
        return publish_id

    # ── 排版主题 ──

    THEMES = {
        "clean": {
            "name": "简洁风",
            "bg": "#FFFFFF",
            "section_bg": "#F8F8F8",
            "title_color": "#333333",
            "text_color": "#555555",
            "accent_color": "#07C160",
            "border_color": "#E8E8E8",
            "font_family": "-apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif",
            "title_size": "18px",
            "body_size": "15px",
            "decoration": "minimal",
        },
        "tech": {
            "name": "科技风",
            "bg": "#0A1628",
            "section_bg": "#112240",
            "title_color": "#64FFDA",
            "text_color": "#CCD6F6",
            "accent_color": "#64FFDA",
            "border_color": "#1D3A5C",
            "font_family": "'SF Mono', 'Fira Code', 'PingFang SC', monospace",
            "title_size": "20px",
            "body_size": "14px",
            "decoration": "code_blocks",
        },
        "literary": {
            "name": "文艺风",
            "bg": "#FDF8F0",
            "section_bg": "#FAF3E6",
            "title_color": "#8B4513",
            "text_color": "#5D4037",
            "accent_color": "#D4A574",
            "border_color": "#EDE0D4",
            "font_family": "'Georgia', 'Noto Serif SC', 'STSong', serif",
            "title_size": "19px",
            "body_size": "15px",
            "decoration": "ornate",
        },
        "business": {
            "name": "商务风",
            "bg": "#FFFFFF",
            "section_bg": "#F0F4F8",
            "title_color": "#1A365D",
            "text_color": "#2D3748",
            "accent_color": "#3182CE",
            "border_color": "#CBD5E0",
            "font_family": "'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif",
            "title_size": "18px",
            "body_size": "14px",
            "decoration": "structured",
        },
    }

    def get_theme_css(self, theme: str) -> str:
        t = self.THEMES.get(theme, self.THEMES["clean"])
        return t

    def _md_to_wechat_html(self, md: str, theme: str = "clean") -> str:
        t = self.THEMES.get(theme, self.THEMES["clean"])

        html_parts = []
        para_count = 0

        for line in md.split("\n"):
            stripped = line.strip()

            if not stripped:
                continue

            para_count += 1
            is_odd = para_count % 2 == 1
            bg = t["section_bg"] if is_odd else t["bg"]
            padding_style = 'padding: 12px 16px;'
            bg_style = f'background: {bg};'

            if stripped.startswith("## "):
                text = stripped[3:]
                html_parts.append(
                    f'<section style="text-align: center; margin: 20px 0 12px; {padding_style}">'
                    f'<h2 style="color: {t["title_color"]}; '
                    f'font-size: {t["title_size"]}; '
                    f'font-family: {t["font_family"]}; '
                    f'font-weight: bold; margin: 0; '
                    f'border-bottom: 2px solid {t["accent_color"]}; '
                    f'padding-bottom: 8px; display: inline-block;">'
                    f'{text}</h2></section>'
                )
                continue

            if stripped.startswith("# "):
                text = stripped[2:]
                html_parts.append(
                    f'<section style="text-align: center; margin: 24px 0 16px; {padding_style}">'
                    f'<h1 style="color: {t["title_color"]}; '
                    f'font-size: 22px; '
                    f'font-family: {t["font_family"]}; '
                    f'font-weight: bold; margin: 0; '
                    f'letter-spacing: 1px;">'
                    f'{text}</h1></section>'
                )
                continue

            # 处理 **加粗** 和普通段落
            processed = self._process_inline(stripped, t)

            # 主题特殊装饰
            decoration_html = ""
            if t["decoration"] == "code_blocks" and stripped.startswith("`"):
                # 代码块风格
                html_parts.append(
                    f'<section style="{bg_style} border-left: 3px solid {t["accent_color"]}; '
                    f'border-radius: 4px; margin: 8px 0; padding: 12px 16px;">'
                    f'<code style="color: {t["accent_color"]}; '
                    f'font-family: \'SF Mono\', monospace; font-size: 13px;">'
                    f'{processed}</code></section>'
                )
            elif t["decoration"] == "ornate" and para_count % 5 == 0:
                # 文艺风分隔装饰
                html_parts.append(
                    f'<section style="text-align: center; color: {t["accent_color"]}; '
                    f'font-size: 18px; margin: 16px 0; opacity: 0.6;">'
                    f'✦ ✦ ✦</section>'
                )
                html_parts.append(
                    f'<section style="{bg_style} {padding_style} '
                    f'border-radius: 4px; margin: 4px 0;">'
                    f'<p style="color: {t["text_color"]}; '
                    f'font-size: {t["body_size"]}; '
                    f'font-family: {t["font_family"]}; '
                    f'line-height: 1.8; margin: 0;">{processed}</p></section>'
                )
            elif t["decoration"] == "structured" and (
                stripped.startswith("-") or stripped.startswith("•")
            ):
                # 商务风列表
                html_parts.append(
                    f'<section style="{bg_style} {padding_style} '
                    f'margin: 2px 0; padding-left: 24px;">'
                    f'<p style="color: {t["text_color"]}; '
                    f'font-size: {t["body_size"]}; '
                    f'font-family: {t["font_family"]}; '
                    f'line-height: 1.7; margin: 0;">'
                    f'<span style="color: {t["accent_color"]}; font-weight: bold;">▸</span> '
                    f'{processed.lstrip("-• ").strip()}</p></section>'
                )
            else:
                # 默认段落
                html_parts.append(
                    f'<section style="{bg_style} {padding_style} '
                    f'border-radius: 4px; margin: 4px 0;">'
                    f'<p style="color: {t["text_color"]}; '
                    f'font-size: {t["body_size"]}; '
                    f'font-family: {t["font_family"]}; '
                    f'line-height: 1.8; margin: 0;">{processed}</p></section>'
                )

        # 整体内容包装
        content = "\n".join(html_parts)

        # 科技风特殊：开头加个装饰条
        if t["decoration"] == "code_blocks":
            content = (
                f'<section style="background: {t["section_bg"]}; '
                f'border-radius: 8px; padding: 4px 0; margin-bottom: 8px;">'
                f'<pre style="color: {t["accent_color"]}; '
                f'font-family: \'SF Mono\', monospace; font-size: 12px; '
                f'text-align: center; margin: 4px 0;">'
                f'╔══════════════════════╗\n'
                f'║   T E C H          ║\n'
                f'╚══════════════════════╝</pre></section>'
                f'{content}'
            )

        return content

    def _process_inline(self, text: str, theme: dict) -> str:
        """处理行内格式：**加粗** *斜体* `代码` 等"""
        # **加粗**
        text = text.replace("**", "<strong>", 1)
        text = text.replace("**", "</strong>", 1)
        while "**" in text:
            text = text.replace("**", "<strong>", 1)
            text = text.replace("**", "</strong>", 1)
        # `行内代码`
        import re as _re
        text = _re.sub(r'`([^`]+)`',
                       lambda m: f'<code style="background: {theme["section_bg"]}; '
                                 f'color: {theme["accent_color"]}; '
                                 f'padding: 2px 6px; border-radius: 3px; '
                                 f'font-size: 13px;">{m.group(1)}</code>',
                       text)
        return text

    # ── 格式转换 ──

    def _md_to_wechat_html_original(self, md: str) -> str:
        """
        原版简单 Markdown → HTML（保留作 fallback）
        """
        html_parts = []
        for line in md.split("\n"):
            stripped = line.strip()
            if not stripped:
                html_parts.append("<p><br/></p>")
                continue
            if stripped.startswith("## "):
                html_parts.append(f"<h2>{stripped[3:]}</h2>")
            elif stripped.startswith("# "):
                html_parts.append(f"<h1>{stripped[2:]}</h1>")
            elif "**" in stripped:
                processed = stripped
                while "**" in processed:
                    processed = processed.replace("**", "<strong>", 1)
                    processed = processed.replace("**", "</strong>", 1)
                html_parts.append(f"<p>{processed}</p>")
            else:
                html_parts.append(f"<p>{stripped}</p>")
        return "\n".join(html_parts)

    # ── 对外接口 ──

    def format_post(self, post: Post, style: str = "clean") -> str:
        """微信格式排版（Markdown 预览用，标注当前主题）"""
        t = self.THEMES.get(style, self.THEMES["clean"])
        parts = []
        parts.append(f"# {post.title}")
        parts.append("")
        parts.append(f"> 排版主题：{t['name']}")
        parts.append("")
        if post.images:
            parts.append(f"![封面]({post.images[0]})")
            parts.append("")
        parts.append(post.content)
        if post.tags:
            parts.append("")
            parts.append("---")
            parts.append(" ".join([f"#{t}" for t in post.tags]))
        return "\n".join(parts)

    def publish(self, post: Post, post_text: str, style: str = "clean") -> dict:
        """发布到微信公众平台，支持排版主题"""
        if not self._app_id or not self._app_secret:
            print("\n⚠️  未配置 WEIXIN_APP_ID 和 WEIXIN_APP_SECRET")
            print("   请在 .env 中配置后重试")
            return {"status": "error", "message": "缺少微信配置"}

        try:
            print(f"\n📤 [微信公众平台] 开始发布: {post.title}")
            print("─" * 40)

            # 1. 上传封面图
            cover_url = ""
            if post.images:
                print("  📷 上传封面图...")
                cover_url = self._upload_image(post.images[0])
                if cover_url:
                    print(f"     ✅ 上传成功")

            # 2. 创建草稿
            print("  📝 创建图文草稿...")
            media_id = self._create_draft(post, cover_url, theme=style)

            # 3. 发布
            print("  🚀 提交发布...")
            publish_id = self._submit_publish(media_id)

            result = {
                "status": "ok",
                "message": f"已提交发布，publish_id={publish_id}",
                "url": f"https://mp.weixin.qq.com/",
                "media_id": media_id,
                "publish_id": publish_id,
            }

            print(f"\n{'=' * 40}")
            print(f"✅ 发布成功！publish_id={publish_id}")
            print(f"   去公众号后台查看发布状态")
            print(f"{'=' * 40}\n")

            return result

        except ValueError as e:
            print(f"\n⚠️  {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            print(f"\n❌ 发布失败: {e}")
            return {"status": "error", "message": str(e)}

    def validate(self, post: Post) -> list[str]:
        """微信平台校验"""
        warnings = super().validate(post)
        if len(post.title) < 2:
            warnings.append("标题太短")
        if not self._app_id:
            warnings.append("未配置 WEIXIN_APP_ID")
        if not self._app_secret:
            warnings.append("未配置 WEIXIN_APP_SECRET")
        return warnings
