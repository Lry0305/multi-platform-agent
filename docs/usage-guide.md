# 多平台内容发布 Agent — 说明文档

## 这东西干嘛的

给个主题，自动写文案、出配图、排好版，能直接发小红书/公众号/抖音。也可以连 ComfyUI 出视频。Hermes 或其他智能体通过命令行调用就行。

---

## 基于 OpenClaw 做了什么

OpenClaw 本身是个 Agent 框架，提供了基础设施。在这之上主要做了几件事：

**文案生成**
写了 11 套写作模板，每套对应不同内容方向（推荐、探店、科普、测评、吐槽……）。输入一句话，AI 自动出标题、正文、标签。会控制语气、段落长度、emoji 密度，不至于写成机器人。

**配图系统**
做了个映射表——根据内容类型+氛围风格（温暖/清新/复古/高级/活泼/治愈），自动组出不同角度的图片描述。一次生成 1-3 张，每张角度不一样（特写、俯拍、场景、细节），不会三张长一样。

**多平台适配**
统一的数据结构，分别适配了小红书、公众号、抖音的排版规则。小红书控制字数+emoji，公众号走富文本，抖音短文案。同一个内容换平台就换输出格式，不用重新写。

**配置体系**
API Key 走环境变量或 .env 文件，不写死在代码里。启动时会检测配置完整度，缺什么提示什么。

**视频生成（实验性）**
对接了 ComfyUI 的文生视频能力。可以远程连 AutoDL 上的 ComfyUI 实例出视频，指定 host 就行。

**一键部署**
一个 setup.sh，装依赖、建目录、检查配置，clone 完跑一行就能用。

**其他**
草稿管理、批量生成、HTML 预览、交互模式——都是围绕"方便用"做的。

---

## 项目结构

```
multi-platform-agent/
├── agent.py                   # 主入口，端到端流程
├── config.py                  # 配置加载
├── setup.sh                   # 一键环境配置
├── .env                       # API Key 配置文件
├── platform/                  # 各平台发布器（小红书/公众号/抖音）
│   ├── base.py                # 抽象基类
│   ├── xiaohongshu.py
│   ├── wechat.py
│   └── douyin.py
├── scripts/
│   ├── xiaohongshu_pipeline.py    # 管线脚本（单篇/批量/草稿管理）
│   ├── gen_image.py               # 单张出图
│   ├── comfyui_video.py           # ComfyUI 视频生成
│   └── preview_post.py            # HTML 预览
├── references/                    # 文案+配图知识库
│   ├── xiaohongshu-copywriting.md
│   └── xiaohongshu-image-prompts.md
├── output/                        # 输出
│   ├── posts/                     # 草稿
│   ├── images/                    # 配图
│   └── videos/                    # 视频
└── docs/
    └── hermes-integration.md      # Hermes 调用文档
```

---

## 快速上手

### 环境

需要 Python 3.8+，和一个硅基流动的 API Key（注册：https://cloud.siliconflow.cn/）。

```bash
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent
bash setup.sh
```

完事编辑 `.env`，把 API Key 填进去。

### 跑一条试试

```bash
python3 agent.py --topic "用了两周的护手霜，手真的不干了" \
  --platform xiaohongshu \
  --category recommend \
  --vibe 温暖 \
  --images 2
```

输出：文案（标题+正文+标签）+ 配图 2 张 + 存草稿。

也可以交互模式，像聊天一样用：

```bash
python3 agent.py --interactive
```

---

## 功能清单

### 文案生成

| 参数 | 说明 |
|------|------|
| `--topic` | 输入主题 |
| `--category` | 内容方向：recommend / checkin / daily / knowledge / compare / collection / anti_haul / tutorial / unboxing / qa / story |
| `--extra` | 额外写作指令，比如"语气更活泼" |
| `--dry-run` | 只出文案，不出图 |

### 配图

| 参数 | 说明 |
|------|------|
| `--images` | 数量 1-3 张 |
| `--vibe` | 氛围：温暖 / 清新 / 复古 / 高级 / 活泼 / 治愈 |
| `--model` | 模型：默认 Qwen/Qwen-Image，可选 Kwai-Kolors/Kolors 等 |
| `--no-image` | 纯文案不出图 |

### 多平台

| 参数 | 说明 |
|------|------|
| `--platform xiaohongshu` | 小红书，默认 |
| `--platform wechat --style tech` | 公众号，可选手法风格 |
| `--platform douyin` | 抖音 |

### 视频（需 ComfyUI 服务）

```bash
python3 scripts/comfyui_video.py \
  --host "http://AutoDL实例IP:8188" \
  --prompt "护手霜在阳光下" \
  --model wan \
  --output output/videos
```

### 管线脚本

```bash
# 单篇完整生成
python3 scripts/xiaohongshu_pipeline.py generate \
  --title "标题" --file content.txt --category recommend --vibe 温暖 --images 2

# 批量生成（JSON 配置）
python3 scripts/xiaohongshu_pipeline.py batch recipes.json

# 看草稿
python3 scripts/xiaohongshu_pipeline.py list
python3 scripts/xiaohongshu_pipeline.py view draft_xxx.md
```

---

## Hermes 怎么调

Hermes 在自己那边跑命令行，不用改这个项目的代码。

```python
# Hermes 里这样调
import subprocess

# 出帖子
subprocess.run([
    "python3", "agent.py",
    "--topic", "好用的护手霜",
    "--platform", "xiaohongshu",
    "--images", "2"
])

# 出视频（连 AutoDL）
subprocess.run([
    "python3", "scripts/comfyui_video.py",
    "--host", "http://AutoDL_IP:8188",
    "--prompt", "护手霜产品展示",
    "--model", "wan"
])
```

Hermes 和这个项目放在同一台机器上，或者把项目路径写绝对地址就行。完整例子见 `docs/hermes-integration.md`。

---

## ComfyUI 视频（备查）

AutoDL 上有一台 RTX 5090 的实例，装的 ComfyUI 镜像。
要出视频时开机，拿到 IP 端口，在命令里 `--host` 指定就行。

已有实例信息：
- 实例 ID：611b489072-57ec2218
- GPU：RTX 5090 × 1
- 镜像：comfyanonymous/ComfyUI （已有）
- 费用：￥2.78/时

这台实例目前关机状态，演示前开机即可。

---

## 一些说明

- 配图走了硅基流动的文生图 API，日常够用
- 公众号那条线已经接好了微信 API，配好 AppID 和 Secret 就能自动发
- 小红书和抖音目前只能排好版等你自己发（平台 API 限制）
- 视频要走 ComfyUI，AutoDL 实例开机才能用
- 草稿在 `output/posts/`，纯 Markdown，要改直接改
- API Key 放 `.env`，别写代码里
