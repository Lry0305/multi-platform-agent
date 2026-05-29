#!/usr/bin/env python3
"""
小红书草稿排版与 HTML 预览工具

功能:
  1. 将 markdown 草稿渲染成小红书风格的 HTML 预览页面
  2. 排版优化（emoji间距、分段、换行）
  3. 一键在浏览器打开

用法:
  # 渲染单篇草稿
  python3 agents/xiaohongshu/scripts/preview_post.py render output/posts/draft_xxx.md

  # 渲染并打开浏览器
  python3 agents/xiaohongshu/scripts/preview_post.py open output/posts/draft_xxx.md

  # 从 generate 管道直接输出 HTML
  python3 agents/xiaohongshu/scripts/xiaohongshu_pipeline.py generate ... --html
"""

import os
import re
import sys
import webbrowser
from datetime import datetime

# 项目路径
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(AGENT_DIR, "output")
POSTS_DIR = os.path.join(OUTPUT_DIR, "posts")
HTML_DIR = os.path.join(OUTPUT_DIR, "html")


# ─── 排版优化 ─────────────────────────────────────────

def optimize_layout(text):
    """
    小红书风格排版优化：
    - 连续空行只保留一个
    - emoji 前后加空格
    - 短句自动分行
    - 标点符号规范
    """
    # 确保 emoji 与文字之间有空格
    # 匹配常见 emoji
    emoji_pattern = re.compile(
        r'([\U0001F300-\U0001FAFF]|[\U0001F600-\U0001F64F]|[\U0001F680-\U0001F6FF]|'
        r'[\U0001F1E0-\U0001F1FF]|[\U00002702-\U000027B0]|[\U000024C2-\U0001F251]|'
        r'[\U0000200D-\U0000200F]|[\U0000FE00-\U0000FE0F]|[\U0000FE0E-\U0000FE0F]|'
        r'[\U0001F900-\U0001F9FF]|[\U0001FA00-\U0001FA6F]|[\U0001FA70-\U0001FAFF]|'
        r'[\U00002600-\U000026FF]|[\U00002700-\U000027BF])'
    )

    # emoji 前后加空格（但避免重复空格）
    text = emoji_pattern.sub(r' \1 ', text)
    text = re.sub(r'  +', ' ', text)

    # 箭头符号美化
    text = text.replace('→ ', '➡️ ')

    # 段落间的空行规范化
    lines = text.split('\n')
    result = []
    prev_empty = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_empty:
                result.append('')
            prev_empty = True
        else:
            result.append(stripped)
            prev_empty = False

    return '\n'.join(result)


def parse_draft(filepath):
    """解析草稿文件，提取元数据和内容"""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # 解析 frontmatter 区域
    meta = {}
    body_start = 0
    lines = raw.split('\n')
    in_meta = False
    meta_lines = []
    body_lines = []

    for i, line in enumerate(lines):
        if line.strip() == '---':
            if not in_meta:
                in_meta = True
                continue
            else:
                in_meta = False
                body_start = i + 1
                break
        if in_meta:
            meta_lines.append(line)

    body = '\n'.join(lines[body_start:])

    # 解析元数据
    for ml in meta_lines:
        ml = ml.strip().lstrip('- ')
        if ':' in ml:
            key, val = ml.split(':', 1)
            meta[key.strip()] = val.strip()

    # 提取标题
    title = ""
    title_match = re.search(r'^#\s+(.+?)$', raw, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
        # 去掉 emoji 前缀
        title = re.sub(r'^[🏆📍☀️📖📝]\s+', '', title)

    # 提取标签
    tags = []
    tag_section = re.search(r'(#[\u4e00-\u9fa5\w]+[\s#\u4e00-\u9fa5\w]*)', body)
    if tag_section:
        tag_line = tag_section.group(0)
        tags = re.findall(r'#([\u4e00-\u9fa5a-zA-Z][\u4e00-\u9fa5\w]*)', tag_line)

    # 提取配图链接
    images = re.findall(r'!\[.*?\]\((.*?)\)', body)

    # 提取图片本地路径
    local_images = []
    for line in lines:
        m = re.search(r'本地: (output/images/img_\d+\.png)', line)
        if m:
            local_images.append(os.path.join(AGENT_DIR, m.group(1)))

    # 清理 body（去掉 frontmatter 区域、标签行、配图部分）
    body_clean = []
    in_images_section = False
    for line in body.split('\n'):
        stripped = line.strip()
        if stripped.startswith('## 配图') or stripped.startswith('### 配图'):
            in_images_section = True
            break
        if in_images_section:
            continue
        if stripped.startswith('#') and not stripped.startswith('## '):
            continue  # 跳过标题行
        if stripped.startswith('!['):
            continue
        # 跳过标签行（一堆#开头的）
        tag_match = re.match(r'^(#[^\s#]+[\s#]*)+\s*$', stripped)
        if tag_match:
            continue
        # 跳过元数据行
        if stripped.startswith('- **'):
            continue
        body_clean.append(stripped)

    body_text = '\n'.join(filter(None, body_clean))

    return {
        'title': title,
        'content': optimize_layout(body_text),
        'tags': tags,
        'images': images,
        'local_images': local_images,
        'meta': meta,
        'raw': raw,
    }


# ─── HTML 渲染 ─────────────────────────────────────────

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - 小红书预览</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
    background: #f0f0f0;
    display: flex;
    justify-content: center;
    padding: 20px;
  }}

  .phone-frame {{
    width: 375px;
    max-width: 100%;
    background: white;
    border-radius: 20px;
    box-shadow: 0 0 30px rgba(0,0,0,0.1);
    overflow: hidden;
    position: relative;
  }}

  .header {{
    padding: 16px 16px 12px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  .avatar {{
    width: 36px; height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff6b6b, #ffa94d);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: white;
    flex-shrink: 0;
  }}

  .user-info {{
    flex: 1;
  }}

  .username {{
    font-weight: 600;
    font-size: 14px;
    color: #222;
  }}

  .user-bio {{
    font-size: 11px;
    color: #999;
    margin-top: 1px;
  }}

  .more-btn {{
    font-size: 20px;
    color: #999;
    cursor: default;
  }}

  .images-section {{
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    background: #fafafa;
  }}

  .images-section img {{
    width: 100%;
    flex-shrink: 0;
    scroll-snap-align: start;
    object-fit: cover;
    max-height: 460px;
  }}

  .images-section::-webkit-scrollbar {{
    display: none;
  }}

  .image-dots {{
    display: flex;
    justify-content: center;
    gap: 5px;
    padding: 8px 0;
  }}

  .image-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #ddd;
  }}

  .image-dot.active {{
    background: #ff6b6b;
    width: 18px;
    border-radius: 3px;
  }}

  .content {{
    padding: 12px 16px;
  }}

  .title {{
    font-size: 16px;
    font-weight: 700;
    color: #222;
    line-height: 1.4;
    margin-bottom: 8px;
  }}

  .body-text {{
    font-size: 14px;
    line-height: 1.7;
    color: #333;
    white-space: pre-wrap;
    word-break: break-word;
  }}

  .body-text p {{
    margin-bottom: 8px;
  }}

  .tags {{
    padding: 8px 16px 4px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px 8px;
  }}

  .tag {{
    font-size: 12px;
    color: #ff6b6b;
    font-weight: 500;
  }}

  .actions {{
    padding: 8px 16px;
    display: flex;
    gap: 20px;
    border-top: 1px solid #f5f5f5;
  }}

  .action-btn {{
    font-size: 13px;
    color: #666;
    display: flex;
    align-items: center;
    gap: 4px;
  }}

  .meta-info {{
    padding: 12px 16px;
    font-size: 11px;
    color: #bbb;
    border-top: 1px solid #f5f5f5;
  }}

  .no-image-placeholder {{
    height: 200px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #adb5bd;
    font-size: 14px;
  }}

  .image-count {{
    position: absolute;
    top: 12px;
    right: 12px;
    background: rgba(0,0,0,0.5);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
  }}
</style>
</head>
<body>
<div class="phone-frame">
  <div class="header">
    <div class="avatar">🍒</div>
    <div class="user-info">
      <div class="username">小红</div>
      <div class="user-bio">内容创作者 · {category_label}</div>
    </div>
    <div class="more-btn">⋯</div>
  </div>

  <div class="images-section" id="imageContainer">
    {images_html}
  </div>

  <div class="image-dots" id="imageDots">
    {dots_html}
  </div>

  <div class="content">
    <div class="title">{display_title}</div>
    <div class="body-text">{body_html}</div>
  </div>

  <div class="tags">
    {tags_html}
  </div>

  <div class="actions">
    <span class="action-btn">❤️ {likes}</span>
    <span class="action-btn">💬 {comments}</span>
    <span class="action-btn">⭐ {saves}</span>
    <span class="action-btn">💬 {shares}</span>
  </div>

  <div class="meta-info">
    🕐 发布于 {created_time} · 草稿预览
  </div>
</div>

<script>
  // 图片滑动指示器
  const container = document.getElementById('imageContainer');
  const dots = document.getElementById('imageDots');
  if (container && dots) {{
    container.addEventListener('scroll', function() {{
      const idx = Math.round(this.scrollLeft / this.clientWidth);
      dots.querySelectorAll('.image-dot').forEach((d, i) => {{
        d.classList.toggle('active', i === idx);
      }});
    }});
  }}
</script>
</body>
</html>
'''


def render_html(post_data, category_label="好物推荐"):
    """渲染小红书风格的 HTML"""

    # 图片
    all_images = post_data.get('images', [])
    local_images = post_data.get('local_images', [])

    if all_images:
        images_html = '\n'.join(
            f'<img src="{img}" alt="配图{i+1}" loading="lazy">'
            for i, img in enumerate(all_images)
        )
        count = len(all_images)
        count_html = f'<div class="image-count">{count}/{count}</div>' if count > 1 else ''
        dots_html = '\n'.join(
            f'<div class="image-dot{" active" if i == 0 else ""}"></div>'
            for i in range(count)
        )
    elif local_images:
        # 使用本地路径 - 需要转换为 file:// 或相对路径
        images_html = '\n'.join(
            f'<img src="file://{img}" alt="配图{i+1}" loading="lazy">'
            for i, img in enumerate(local_images)
        )
        count = len(local_images)
        dots_html = '\n'.join(
            f'<div class="image-dot{" active" if i == 0 else ""}"></div>'
            for i in range(count)
        )
    else:
        images_html = '<div class="no-image-placeholder">📷 暂无配图</div>'
        dots_html = ''

    # 标签
    tags = post_data.get('tags', [])
    tags_html = '\n'.join(f'<span class="tag">#{t}</span>' for t in tags)

    # 正文 - 分段渲染
    body_text = post_data.get('content', '')
    paragraphs = [p for p in body_text.split('\n') if p.strip()]
    body_html = '\n'.join(f'<p>{p}</p>' for p in paragraphs)

    # 标题（显示用 - 保留 emoji）
    display_title = post_data.get('title', '无标题')
    # 标题（页面标签用 - 去掉 emoji）
    title_clean = re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF\uFE00-\uFE0F]', '', display_title).strip()

    # 元数据
    meta = post_data.get('meta', {})
    created_time = meta.get('创建', meta.get('创建时间', '刚刚'))

    return HTML_TEMPLATE.format(
        title=title_clean,
        display_title=display_title,
        body_html=body_html,
        tags_html=tags_html,
        images_html=images_html,
        dots_html=dots_html,
        category_label=category_label,
        likes='0',
        comments='0',
        saves='0',
        shares='0',
        created_time=created_time,
    )


def save_html(html_content, filename=None):
    """保存 HTML 文件"""
    os.makedirs(HTML_DIR, exist_ok=True)
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"preview_{timestamp}.html"
    filepath = os.path.join(HTML_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filepath


def render_draft(draft_path):
    """从草稿文件渲染 HTML"""
    post = parse_draft(draft_path)
    category = post['meta'].get('分类', 'general')
    category_map = {
        'recommend': '好物推荐',
        'checkin': '探店打卡',
        'daily': '日常分享',
        'knowledge': '知识科普',
        'general': '内容创作',
    }
    html = render_html(post, category_map.get(category, '内容创作'))
    basename = os.path.basename(draft_path).replace('.md', '.html')
    html_path = save_html(html, basename)
    return html_path


# ─── 入口 ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书草稿预览工具")
    sub = parser.add_subparsers(dest="command")

    rp = sub.add_parser("render", help="渲染草稿为 HTML")
    rp.add_argument("draft", help="草稿文件路径")

    op = sub.add_parser("open", help="渲染并打开浏览器")
    op.add_argument("draft", help="草稿文件路径")

    args = parser.parse_args()

    if args.command in ("render", "open"):
        draft_path = args.draft
        if not os.path.isabs(draft_path):
            draft_path = os.path.join(os.getcwd(), draft_path)
        if not os.path.exists(draft_path):
            # 尝试在 posts 目录下找
            posts_path = os.path.join(POSTS_DIR, args.draft)
            if os.path.exists(posts_path):
                draft_path = posts_path
        if not os.path.exists(draft_path):
            print(f"❌ 未找到草稿: {args.draft}")
            sys.exit(1)

        print(f"📄 渲染: {os.path.basename(draft_path)}")
        html_path = render_draft(draft_path)
        print(f"✅ HTML 已生成: {html_path}")

        if args.command == "open":
            webbrowser.open(f"file://{html_path}")
            print(f"🌐 已打开浏览器")
    else:
        parser.print_help()
