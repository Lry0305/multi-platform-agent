# 🍒 多平台内容发布 Agent

**给一个灵感/主题，自动写好文案、配好图、格式化成目标平台样式。**

已适配小红书，微信和抖音适配开发中。

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 SILICONFLOW_API_KEY
# 注册获取：https://cloud.siliconflow.cn/

# 3. 跑一篇试试
python3 agent.py --topic "最近入了这款护手霜，手嫩到被同事追问"
```

完事去 `output/posts/` 找草稿，配图在 `output/images/` 里。

---

## 能干嘛

### 🧠 **端到端内容生成**（新！）
```bash
# 完整流程：主题→文案→配图→草稿
python3 agent.py --topic "周末去了一家藏在巷子里的咖啡馆" --category checkin --vibe 温暖

# 自定义配图数
python3 agent.py --topic "推荐3款面膜" --images 3

# 先看看文案效果，不出图
python3 agent.py --topic "我的书桌布置" --dry-run

# 交互模式
python3 agent.py --interactive
```

### ✍️ **文案生成**
使用 LLM（硅基流动 API）自动生成小红书风格文案，支持四种内容方向：

| 分类 | 适合什么 |
|------|---------|
| `recommend` | 好物推荐 |
| `checkin` | 探店打卡 |
| `daily` | 日常分享 |
| `knowledge` | 知识科普 |

### 🎨 **智能配图**
根据文案内容自动推断场景，生成多个角度的配图描述（特写/俯拍/场景），调用硅基流动 API 出图。

支持模型：
- `Qwen/Qwen-Image` — 通义千问，日常够用
- `Kwai-Kolors/Kolors` — 快手可图，中文理解好
- `Tongyi-MAI/Z-Image` — 通义万相
- `Tongyi-MAI/Z-Image-Turbo` — 通义万相快速版
- `baidu/ERNIE-Image-Turbo` — 百度的

### 📐 **平台格式化**
同一篇内容，自动按不同平台的规则格式化：

| 平台 | 状态 | 说明 |
|------|------|------|
| 小红书 | ✅ | 标题≤20字，正文短段落+emoji，标签5-8个 |
| 微信公众平台 | 🚧 | 开发中，API 对接待完成 |
| 抖音 | 🚧 | 开发中，API 对接待完成 |

### 📦 **批量生成**
一次跑好几篇：

```bash
python3 agent.py batch recipes.json
```

`recipes.json` 示例见 `agents/xiaohongshu/output/recipes_sample.json`。

---

## 项目结构

```
multi-platform-agent/
├── agent.py                    # 🆕 Agent 大脑：端到端内容生成
├── config.py                   # 🆕 配置加载（.env + 环境变量）
├── .env.example                # 🆕 环境变量模板
├── platform/                   # 🆕 平台发布 SDK
│   ├── base.py                 #   抽象基类
│   ├── xiaohongshu.py          #   小红书发布器
│   ├── wechat.py               #   微信发布器（🚧）
│   └── douyin.py               #   抖音发布器（🚧）
├── agents/
│   └── xiaohongshu/            # 小红书内容生成核心
│       ├── scripts/
│       │   ├── xiaohongshu_pipeline.py  # 主流程（prompt/出图/存草稿）
│       │   ├── gen_image.py             # 图片生成工具
│       │   └── preview_post.py          # HTML 预览
│       ├── references/                  # 写作参考
│       └── output/                      # 产出（草稿 + 配图）
├── openclaw/                   # 🆕 OpenClaw agent 配置（使用 OpenClaw 时引用）
├── skills/                     # 其他工具技能
└── requirements.txt            # Python 依赖
```

---

## 开发计划

- [x] 配置系统（.env + config.py）
- [x] 平台发布 SDK 抽象层
- [x] Agent 端到端流程
- [x] 解耦 OpenClaw
- [ ] 微信公众平台 API 对接
- [ ] 抖音 API 对接
- [ ] Web UI 界面
- [ ] 定时发布 / 内容日历

---

## 几句废话

- 文案走第一人称，短段落，多 emoji，小红书上常见的那个风格
- 配图描述会自动生成多个角度，不是一模一样来三张
- API Key 放 `.env` 文件，已加 `.gitignore`，别写代码里
- 想跑 OpenClaw 版本？看 `openclaw/` 目录下的配置
