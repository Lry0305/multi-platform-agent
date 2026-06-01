# 多平台内容发布 Agent — 使用手册

> 给个主题，自动写文案、出配图、按平台格式排好版。

---

## 1. 环境准备

### 前提

- macOS / Linux
- Python 3.8+
- 已注册 [硅基流动](https://cloud.siliconflow.cn/) 并获取 API Key

### 安装

```bash
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent
cp .env.example .env
```

编辑 `.env`，填入 API Key：

```
SILICONFLOW_API_KEY=sk-你的key
```

### 验证安装

```bash
python3 agent.py --topic "测试" --dry-run
```

能看到文案输出就说明装好了。

---

## 2. 快速上手

出一篇小红书帖子：

```bash
python3 agent.py \\
  --topic "最近一直在用的护手霜，质地太舒服了" \\
  --images 2
```

几十秒后去 `output/posts/` 看草稿，配图在 `output/images/` 里。

完整流程：写文案 → 生成配图 → 平台格式化 → 存草稿。

---

## 3. 所有命令

### 3.1 基础用法

```bash
# 出一篇帖子
python3 agent.py --topic "你的灵感"

# 出两篇配图
python3 agent.py --topic "..." --images 2

# 只看文案不出图
python3 agent.py --topic "..." --dry-run

# 交互模式（一条一条出）
python3 agent.py --interactive
```

### 3.2 内容分类

`--category` 参数选内容方向，目前有 11 种：

| 参数 | 类型 | 示例主题 |
|------|------|---------|
| `recommend` | 好物推荐 | 用了两周的护手霜 |
| `checkin` | 探店打卡 | 藏在巷子里的咖啡馆 |
| `daily` | 日常分享 | 周末宅家的一天 |
| `knowledge` | 知识科普 | 新手护肤误区 |
| `compare` | 测评对比 | 兰蔻 vs 欧莱雅 |
| `collection` | 合集盘点 | 年度爱用8件好物 |
| `anti_haul` | 踩雷吐槽 | 跟风买的后悔单品 |
| `tutorial` | 教程步骤 | 3步搞定早餐摆盘 |
| `unboxing` | 开箱体验 | 期待已久的快递 |
| `qa` | 问答答疑 | 被问最多的10个问题 |
| `story` | 情绪故事 | 28岁才明白的事 |

### 3.3 氛围（配图色调）

`--vibe` 参数控制配图的色彩氛围：

| 参数 | 效果 |
|------|------|
| `温暖` | 暖色调，奶油色系（默认） |
| `清新` | 青绿色系，干净通透 |
| `复古` | 胶片感，暖黄调 |
| `高级` | 冷色调，低饱和 |
| `活泼` | 高饱和，明亮色彩 |
| `治愈` | 柔光暖调，软糯色系 |

### 3.4 排版风格

小红书风格：

| 参数 | 说明 |
|------|------|
| `--style clean` | 简洁（默认） |
| `--style chatty` | 聊天风，像发微信 |
| `--style bold` | 重点加粗 |
| `--style diary` | 日记风，带日期尾巴 |

公众号风格：

| 参数 | 说明 |
|------|------|
| `--style clean` | 简洁 |
| `--style tech` | 科技风，深色代码感 |
| `--style literary` | 文艺风，暖色衬线 |
| `--style business` | 商务风，蓝调专业 |

### 3.5 完整示例

```bash
# 小红书·好物推荐·温暖氛围·聊天风
python3 agent.py --topic "用了两周的护手霜" \\
  --category recommend --vibe 温暖 --style chatty

# 小红书·踩雷吐槽·复古氛围
python3 agent.py --topic "跟风买的雷品" \\
  --category anti_haul --vibe 复古

# 公众号·知识科普·科技风
python3 agent.py --topic "2024前端趋势" \\
  --platform wechat --category knowledge --style tech
```

---

## 4. 产出文件

| 路径 | 内容 |
|------|------|
| `output/posts/draft_*.md` | 帖子草稿（含配图路径） |
| `output/images/img_*.png` | 生成的配图 |
| `output/html/draft_*.html` | 手机框 HTML 预览 |
| `output/images/screenshot_*.png` | 预览截图 |

生成的帖子是 markdown 格式，可以直接复制到小红书 App 发。

---

## 5. 公众号发布

配好微信公众平台的 AppID 和 AppSecret：

```bash
# .env 里加上
WEIXIN_APP_ID=wx你的AppID
WEIXIN_APP_SECRET=你的Secret
```

然后：

```bash
python3 agent.py --topic "..." --platform wechat --images 1
```

会自动创建图文草稿并提交发布。发布状态去公众号后台看。

---

## 6. 草稿管理

```bash
# 列出所有草稿
python3 scripts/xiaohongshu_pipeline.py list

# 查看某篇草稿
python3 scripts/xiaohongshu_pipeline.py view draft_xxx.md

# 生成 HTML 预览
python3 scripts/preview_post.py render output/posts/draft_xxx.md
```

---

## 7. 常见问题

**Q: 提示 "API Key 未找到"**
A: 检查 `.env` 文件是否有 `SILICONFLOW_API_KEY=sk-...`，确认 key 完整没有多余字符。

**Q: 出图失败**
A: 检查网络是否能访问 `api.siliconflow.cn`，API Key 余额是否充足（去硅基流动后台看）。

**Q: 文案太长或太短**
A: 不同分类有不同字数控制，可以试试切换 `--category`。

**Q: 公众号发布失败**
A: 确认 `.env` 里的 `WEIXIN_APP_ID` 和 `WEIXIN_APP_SECRET` 正确。个人订阅号可能没有草稿箱权限。

**Q: 怎么只看文案不出图？**
A: 加 `--dry-run` 或 `--no-image`。

---

## 8. 项目结构

```
multi-platform-agent/
├── agent.py              入口，一条龙出内容
├── config.py             配置加载
├── .env                  你的 API Key（不提交）
├── .env.example          模板
├── platform/             各平台发布器
│   ├── base.py           基类
│   ├── xiaohongshu.py    小红书
│   ├── wechat.py         公众号
│   └── douyin.py         抖音（开发中）
├── agents/xiaohongshu/   内容生成模块
│   ├── scripts/          脚本（pipeline、预览、出图）
│   ├── references/       文案模板、配图 prompt 体系
│   ├── output/           产出（草稿、配图、HTML）
│   └── skills/           OpenClaw 技能
├── openclaw/             OpenClaw agent 配置
└── output/               （可选）全局产出目录
```
