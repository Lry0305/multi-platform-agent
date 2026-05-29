# 3 分钟上手

## 准备工作

去硅基流动（https://cloud.siliconflow.cn/）注册个账号，拿 API Key。新用户有免费额度。

## 跑起来

```bash
git clone https://github.com/Lry0305/multi-platform-agent.git
cd multi-platform-agent
cp .env.example .env
```

编辑 .env，把 API Key 填进去：

```
SILICONFLOW_API_KEY=sk-你的key
```

然后跑：

```bash
python3 agent.py --topic "最近用了两周的护手霜，手真的变嫩了"
```

几十秒后去 `output/posts/` 看草稿，配图在 `output/images/`。

## 更多用法

```bash
# 探店
python3 agent.py --topic "巷子里的咖啡馆" --category checkin --vibe 温暖

# 只看文案不出图
python3 agent.py --topic "3款平价面膜" --dry-run

# 交互模式，一条一条出
python3 agent.py --interactive

# 发到微信公众号（需先配好 AppID 和 Secret）
python3 agent.py --topic "..." --platform wechat --images 1
```

## 发布

小红书没有开放 API，目前只能手动复制到 App 发。

微信公众号已对接到 API。配好 AppID 和 AppSecret 后，agent 会自动创建草稿并提交发布。
