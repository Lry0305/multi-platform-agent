# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## 商业模拟决策（BusinessSim 模式）

### 数据读写
- **Skill 路径：** `skills/business-sim/`
- **Excel 工具：** `python3 skills/business-sim/scripts/excel_reader.py`
- **PDF 工具：** `python3 skills/business-sim/scripts/pdf_reader.py`
- **决策引擎：** `python3 skills/business-sim/scripts/decision_engine.py`

### Python 依赖
| 库 | 用途 |
|------|------|
| `openpyxl` | Excel 读写 |
| `pandas` | 数据表格处理 |
| `pdfplumber` | PDF 文本/表格提取 |

### 常用命令速查
```bash
# 读取 Excel
python3 skills/business-sim/scripts/excel_reader.py read data.xlsx

# 读取 PDF
python3 skills/business-sim/scripts/pdf_reader.py all rules.pdf

# 列出 sheets
python3 skills/business-sim/scripts/excel_reader.py list data.xlsx
```

---

## Image Generation（小红专用）

- **Provider:** 硅基流动 (SiliconFlow)
- **API Endpoint:** `https://api.siliconflow.cn/v1/images/generations`
- **API Key:** `sk-sbcsqgshydexdjkdoyglqmodgfvenhrqbrvpelfmsenjxlgc`
- **Auth Header:** `Authorization: Bearer <API_KEY>`
- **Format:** OpenAI-compatible `POST /v1/images/generations`

### Available Image Models

| Model | 说明 |
|-------|------|
| `Qwen/Qwen-Image` | 通义千问图片生成，适合通用场景 |
| `Kwai-Kolors/Kolors` | 快手可图，中文理解强 |
| `Tongyi-MAI/Z-Image` | 通义万相 |
| `Tongyi-MAI/Z-Image-Turbo` | 通义万相快速版 |
| `baidu/ERNIE-Image-Turbo` | 百度ERNIE图片生成 |

### 请求格式

```json
POST /v1/images/generations
{
  "model": "Qwen/Qwen-Image",
  "prompt": "prompt内容",
  "n": 1,
  "size": "1024x1024"
}
```

响应返回 `images[0].url` 为图片临时链接（24h有效）。

### 小红文件位置

所有内容在 `agents/xiaohongshu/` 下：

```bash
agents/xiaohongshu/
├── scripts/          # 脚本
│   ├── gen_image.py          # 图片生成
│   └── xiaohongshu_pipeline.py  # 主流程（文案+配图+草稿）
├── references/       # 文案/配图体系
│   ├── xiaohongshu-copywriting.md
│   └── xiaohongshu-image-prompts.md
├── skills/           # 技能定义
│   └── xiaohongshu-content/
├── output/           # 产出
│   ├── posts/        # 帖子草稿
│   └── images/       # 配图文件
└── memory/           # 记忆
```

### 常用命令

```bash
# 完整流程：文案+配图+存草稿
python3 agents/xiaohongshu/scripts/xiaohongshu_pipeline.py generate --title "标题" --file content.txt --category recommend --images 2

# 完整流程 + HTML预览
python3 agents/xiaohongshu/scripts/xiaohongshu_pipeline.py generate --title "标题" --file content.txt --category recommend --html

# 查看草稿
python3 agents/xiaohongshu/scripts/xiaohongshu_pipeline.py list

# 发布就绪：格式化 + 复制到剪贴板
python3 agents/xiaohongshu/scripts/xiaohongshu_pipeline.py publish draft_xxx.md

# 查看 HTML 预览
python3 agents/xiaohongshu/scripts/preview_post.py open output/posts/draft_xxx.md

# 单张出图
python3 agents/xiaohongshu/scripts/gen_image.py "场景描述"
```

---

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
