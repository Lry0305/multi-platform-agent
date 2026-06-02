# 多平台内容发布 Agent

## 概述

输入一个主题，自动生成文案和配图，按平台格式输出。目前支持小红书、微信公众号、抖音。通过命令行调用，也可以对接其他智能体。

## 基于 OpenClaw 做了什么

OpenClaw 提供 Agent 框架和基础设施，在这个基础上做了几层东西：

**文案生成**
11 套写作模板，每套对应一个内容方向（推荐、探店、科普、测评、吐槽等）。输入主题后，由 LLM 生成标题、正文、标签。每个方向控制了语气、段落长度、emoji 密度。

**配图系统**
根据内容类型和氛围风格（温暖/清新/复古/高级/活泼/治愈），自动拼接不同角度的图片描述。一次生成 1-3 张，每张构图不同（特写、俯拍、场景、细节），不是简单复制。

**多平台适配**
统一的数据结构，分别对接了小红书、公众号、抖音的格式。同一份内容换平台会按对应规则重新排版。

**配置管理**
API Key 走环境变量或 .env 文件。启动时检查配置完整性，缺什么提示什么。

**视频生成（实验）**
通过 ComfyUI 接口生成视频，支持远程 GPU 实例调用。

**部署脚本**
一个 setup.sh，处理依赖安装、目录创建、配置检查。

**其他实用功能**
草稿管理、批量生成、HTML 预览、交互模式。

## 项目结构

```
multi-platform-agent/
├── agent.py                   # 主入口
├── config.py                  # 配置
├── setup.sh                   # 环境配置
├── .env                       # API Key
├── platform/                  # 各平台发布器
│   ├── base.py
│   ├── xiaohongshu.py
│   ├── wechat.py
│   └── douyin.py
├── scripts/
│   ├── xiaohongshu_pipeline.py
│   ├── gen_image.py
│   ├── comfyui_video.py
│   └── preview_post.py
├── references/
│   ├── xiaohongshu-copywriting.md
│   └── xiaohongshu-image-prompts.md
├── output/
│   ├── posts/
│   ├── images/
│   └── videos/
└── docs/
    ├── hermes-integration.md
    └── usage-guide.md
```

## 快速开始

需要 Python 3.8+，以及一个硅基流动的 API Key（https://cloud.siliconflow.cn/）。

```bash
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent
bash setup.sh
```

然后编辑 .env 填入 SILICONFLOW_API_KEY。

```bash
python3 agent.py --topic "用了两周的护手霜" --platform xiaohongshu --category recommend --vibe 温暖 --images 2
```

## 功能说明

### 文案

| 参数 | 说明 |
|------|------|
| --topic | 输入主题 |
| --category | 内容方向。可选：recommend, checkin, daily, knowledge, compare, collection, anti_haul, tutorial, unboxing, qa, story |
| --extra | 额外写作指令 |
| --dry-run | 纯文案，不出图 |

### 配图

| 参数 | 说明 |
|------|------|
| --images | 数量，最多 3 张 |
| --vibe | 氛围：温暖、清新、复古、高级、活泼、治愈 |
| --model | 生成模型，默认 Qwen/Qwen-Image |
| --no-image | 不出图 |

### 多平台

```bash
python3 agent.py --topic "..." --platform xiaohongshu
python3 agent.py --topic "..." --platform wechat --style tech
python3 agent.py --topic "..." --platform douyin
```

### 视频（需要 ComfyUI）

```bash
python3 scripts/comfyui_video.py --host "http://<AutoDL实例IP>:8188" --prompt "..." --model wan
```

### 管线脚本

```bash
python3 scripts/xiaohongshu_pipeline.py generate --title "标题" --file content.txt --category recommend --vibe 温暖 --images 2
python3 scripts/xiaohongshu_pipeline.py batch recipes.json
python3 scripts/xiaohongshu_pipeline.py list
python3 scripts/xiaohongshu_pipeline.py view draft_xxx.md
```

### 交互模式

```bash
python3 agent.py --interactive
```

然后按提示输入内容、选平台和风格。

## Hermes 集成

其他智能体直接调命令行即可：

```python
import subprocess
subprocess.run(["python3", "agent.py", "--topic", "...", "--platform", "xiaohongshu", "--images", "2"])
subprocess.run(["python3", "scripts/comfyui_video.py", "--host", "http://<IP>:8188", "--prompt", "..."])
```

详细说明见 docs/hermes-integration.md。

## ComfyUI 实例

AutoDL 上有一台 RTX 5090 的实例，安装了 ComfyUI。演示前开机，获取 IP 和端口，在命令中通过 --host 指定。

- 实例 ID：611b489072-57ec2218
- GPU：RTX 5090 × 1
- 费用：约 2.78 元/小时

## 注意

- 图片通过硅基流动 API 生成
- 公众号已对接微信 API，配置好 AppID 和 Secret 后可自动发布
- 小红书和抖音目前只输出排版后的文本，需手动粘贴
- 视频需要 AutoDL 实例开机
- 草稿保存在 output/posts/，纯 Markdown
