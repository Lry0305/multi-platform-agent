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

完整流程（主题 -> 文案 -> 配图 -> 存草稿）：
```bash
python3 agent.py --topic "周末去的咖啡馆" --category checkin --vibe 温暖
python3 agent.py --topic "推荐3款面膜" --images 3
python3 agent.py --topic "我的书桌布置" --dry-run  # 只看文案，不出图
python3 agent.py --interactive                       # 交互模式
```

指定平台：
```bash
python3 agent.py --topic "..." --platform wechat --images 1
# 需要先配好 WEIXIN_APP_ID 和 WEIXIN_APP_SECRET
```

支持的分类：
- `recommend`：好物推荐
- `checkin`：探店打卡
- `daily`：日常分享
- `knowledge`：知识科普

## 平台支持

| 平台 | 状态 |
|------|------|
| 小红书 | 文案+配图+草稿，需手动复制到 App 发 |
| 微信公众号 | API 已对接，支持自动创建草稿和发布 |
| 抖音 | 开发中 |

## 项目结构

```
multi-platform-agent/
├── agent.py              入口，从主题到出图一条龙
├── config.py             配置，读 .env 和环境变量
├── .env.example          配置模板
├── platform/             平台发布 SDK
│   ├── base.py           发布器的基类
│   ├── xiaohongshu.py    小红书
│   ├── wechat.py         微信公众号
│   └── douyin.py         抖音（开发中）
├── agents/xiaohongshu/   小红书内容生成（prompt、出图、草稿管理）
├── openclaw/             OpenClaw agent 配置
└── GETTING_STARTED.md / CONTRIBUTING.md
```

## 环境要求

- Python 3.8+
- 一个硅基流动 API Key（注册：https://cloud.siliconflow.cn/）
- 不需要装任何第三方包，全用标准库

## 说明

- 文案走第一人称，短段落，适配小红书风格
- 配图自动从不同角度生成（特写、俯拍、场景），不是一模一样来三张
- API Key 放 .env，已加 .gitignore
- 想跑 OpenClaw 版本看 openclaw/ 目录
