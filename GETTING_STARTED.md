# 🚀 3 分钟上手

## 准备

你需要一个 [硅基流动](https://cloud.siliconflow.cn/) 账号和 API Key。

注册免费，新用户有额度。

## 安装

### 1. 克隆

```bash
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent
```

### 2. 配置

```bash
cp .env.example .env
```

编辑 `.env`，把 API Key 填进去：

```
SILICONFLOW_API_KEY=sk-你的key
```

### 3. 搞定，不需要装任何包

本项目用 **Python 3.8+ 标准库**，唯一的外部依赖是硅基流动 API。

如果你想用 pyperclip（复制到剪贴板功能）：

```bash
pip install pyperclip
```

## 跑第一个帖子

```bash
python3 agent.py --topic "最近用了两周的护手霜，手真的变嫩了"
```

等几十秒，你会看到：
1. ✍️ LLM 自动写文案
2. 🎨 生成配图 prompt
3. 🖼️ 调用 API 出图
4. 💾 草稿保存到 `output/posts/`

## 查看草稿

```bash
cat output/posts/draft_*.md
```

## 更多用法

```bash
# 探店风格
python3 agent.py --topic "巷子里的咖啡馆" --category checkin --vibe 温暖

# 只出文案不出图
python3 agent.py --topic "3款平价面膜" --dry-run

# 交互模式，慢慢聊
python3 agent.py --interactive

# 使用旧版 pipeline（自定义正文内容）
python3 agents/xiaohongshu/scripts/xiaohongshu_pipeline.py generate \
    --title "我的标题" \
    --content "正文内容" \
    --category recommend \
    --images 2
```

## 发布

目前小红书没有开放 API 给个人开发者，生成草稿后请 **手动复制** 到小红书 App 发布。

微信和抖音的 API 对接开发中。

## 有问题？

看 `CONTRIBUTING.md` 或直接提 issue。
