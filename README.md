# 多平台内容发布 Agent

给个主题，自动写文案、出配图、按平台格式排好版。目前接入了小红书和微信公众号。

## 快速上手

```bash
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent
cp .env.example .env
# 编辑 .env，填入 SILICONFLOW_API_KEY
python3 agent.py --topic "用了两周的护手霜，手真的不干了"
```

去 `output/posts/` 找草稿，配图在 `output/images/` 里。

## 用法

```bash
# 基础
python3 agent.py --topic "周末去的咖啡馆" --category checkin --vibe 温暖
python3 agent.py --topic "推荐3款面膜" --images 3
python3 agent.py --topic "我的书桌布置" --dry-run

# 交互模式
python3 agent.py --interactive

# 公众号（需配好 AppID 和 Secret）
python3 agent.py --topic "..." --platform wechat --images 1

# 选排版风格
python3 agent.py --topic "..." --style chatty
python3 agent.py --topic "..." --platform wechat --style tech
```

## 内容分类（11 种）

| 分类 | 说明 | 示例 |
|------|------|------|
| `recommend` | 好物推荐 | 护手霜测评 |
| `checkin` | 探店打卡 | 咖啡馆探店 |
| `daily` | 日常分享 | 周末日常 |
| `knowledge` | 知识科普 | 护肤误区 |
| `compare` | 测评对比 | A vs B |
| `collection` | 合集盘点 | 年度爱用 |
| `anti_haul` | 踩雷吐槽 | 拔草劝退 |
| `tutorial` | 教程步骤 | 3步搞定 |
| `unboxing` | 开箱体验 | 快递开箱 |
| `qa` | 问答答疑 | 常见问题 |
| `story` | 情绪故事 | 人生感悟 |

## 排版风格

### 小红书

| 参数 | 风格 |
|------|------|
| `--style clean` | 简洁 |
| `--style chatty` | 聊天 |
| `--style bold` | 重点加粗 |
| `--style diary` | 日记 |

### 公众号

| 参数 | 风格 |
|------|------|
| `--style clean` | 简洁 |
| `--style tech` | 科技 |
| `--style literary` | 文艺 |
| `--style business` | 商务 |

## 项目结构

```
multi-platform-agent/
├── agent.py                入口
├── config.py               配置
├── .env.example            配置模板
├── platform/               平台发布 SDK
│   ├── base.py             基类
│   ├── xiaohongshu.py      小红书
│   ├── wechat.py           公众号
│   └── douyin.py           抖音（开发中）
├── agents/xiaohongshu/     内容生成（prompt、出图、草稿管理）
├── openclaw/               OpenClaw agent 配置
└── GETTING_STARTED.md / CONTRIBUTING.md
```

## 环境要求

- Python 3.8+
- 硅基流动 API Key（https://cloud.siliconflow.cn/）
- 全用标准库，不需要第三方包

## 说明

- 文案第一人称，短段落
- 配图自动多角度（特写、俯拍、场景），不是一模一样的来三张
- API Key 放 .env，已加 .gitignore
- 想跑 OpenClaw 版本看 openclaw/ 目录
