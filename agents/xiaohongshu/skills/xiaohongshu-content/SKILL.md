---
name: xiaohongshu-content
description: "小红书内容生成技能（小红专用）：文案 + 配图 + 完整帖子产出"
---

# 小红书内容生成（🍒 小红）

## 核心原则

1. 用户给一个**主题** → 小红产出一整套小红书帖子（文案 + 图片 + 标签）
2. 文案风格参考 `references/xiaohongshu-copywriting.md` 模板体系
3. 配图调用 `scripts/gen_image.py` 生成
4. 默认使用 `Qwen/Qwen-Image` 模型，支持切换

## 工作流程

### 1️⃣ 接收需求
- 主题/产品/地点
- 内容方向（好物推荐 / 探店 / 日常 / 科普）
- 特别要求（语气、侧重点）

### 2️⃣ 写文案
参考 copywriting 体系，按模板产出：
- 标题（备选3个）
- 正文（分段 + emoji + 第一人称）
- 标签

### 3️⃣ 出配图 prompt
根据文案内容，生成匹配的图片 prompt，调用 gen_image.py

### 4️⃣ 输出完整帖子
组合文案 + 图片 URL + 标签，输出为一个帖子单元

## 内容方向

当前支持：
- `recommend` — 好物推荐/测评
- `checkin` — 探店打卡
- `daily` — 日常分享/Vlog
- `knowledge` — 知识科普/教程

## 文件结构

```
skills/xiaohongshu-content/
  SKILL.md               ← 本文件（技能定义）

references/
  xiaohongshu-copywriting.md  ← 文案体系模板

scripts/
  gen_image.py           ← 图片生成工具
  xiaohongshu_pipeline.py     ← 主流程（文案+配图+完整帖子）

output/                  ← 生成的图片和帖子草稿
```
