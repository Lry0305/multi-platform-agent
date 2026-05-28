# 小红书内容生成 Agent

发小红书用的。给个主题，自动写文案、配图、标签。

---

## 能干嘛

- 写文案：好物推荐、探店、日常、科普，四种方向
- 出配图：根据文案内容自动生成图片描述，调硅基流动的 API 出图
- 批量产：写一个 JSON 配置，一次跑好几篇
- 管理草稿：生成的东西自动存档，翻出来就能用

---

## 上手

### 需要什么

- Python 3.8+
- 一个硅基流动的 API Key（去注册：https://cloud.siliconflow.cn/）

```bash
# 下载
git clone https://github.com/Lry0305/xiaohongshu-agent.git
cd xiaohongshu-agent

# 设环境变量（建议写进 ~/.zshrc 省得每次输）
export SILICONFLOW_API_KEY="xxx"
```

### 跑一篇试试

新建一个文本文件，写点内容，比如 `content.txt`：

```
最近入了这款护手霜，真的惊艳到我了
质地很润但是不油，涂完打字也不会留印
味道是淡淡的柑橘调，很高级
用了两周，手明显嫩了
```

然后跑：

```bash
cd agents/xiaohongshu
python3 scripts/xiaohongshu_pipeline.py generate \
    --title "用了两周的护手霜，手嫩到被同事追问" \
    --file content.txt \
    --category recommend \
    --images 2
```

完事去 `output/posts/` 找草稿，配图在 `output/images/` 里。

---

## 常用命令

### 完整生成一条

```bash
python3 scripts/xiaohongshu_pipeline.py generate \
    --title "标题" \
    --file content.txt \
    --category recommend \
    --vibe 温暖 \
    --images 2
```

参数说明：

| 参数 | 说明 |
|------|------|
| `--title` | 帖子标题 |
| `--file` | 正文文件 |
| `--content` | 直接写正文，用引号包起来 |
| `--category` | 内容方向：recommend / checkin / daily / knowledge |
| `--vibe` | 配图氛围：温暖 / 清新 / 复古 / 高级 / 活泼 / 治愈 |
| `--images` | 配图数量，最多3张 |
| `--model` | 出图模型，默认 Qwen/Qwen-Image |
| `--no-image` | 只存文案不出图 |
| `--html` | 额外生成一个 HTML 预览 |

### 只看配图描述长啥样

```bash
python3 scripts/xiaohongshu_pipeline.py prompt \
    --scene "面霜瓶子在阳光下" \
    --category recommend \
    --images 2
```

### 已有 prompt，单张出图

```bash
python3 scripts/xiaohongshu_pipeline.py image \
    "你的 prompt 描述" \
    --save
```

### 看草稿

```bash
python3 scripts/xiaohongshu_pipeline.py list            # 全部
python3 scripts/xiaohongshu_pipeline.py view draft_xxx.md  # 某一篇
```

### 准备发布

排版成可以直接粘贴的格式，顺便复制到剪贴板：

```bash
python3 scripts/xiaohongshu_pipeline.py publish draft_xxx.md
```

### 批量生成

适合一次搞多篇。写个 JSON，比如 `recipes.json`：

```json
[
  {
    "title": "最近爱用的3款面膜",
    "file": "content_mask.txt",
    "category": "recommend",
    "vibe": "清新",
    "images": 2,
    "tags": ["面膜推荐", "护肤"]
  },
  {
    "title": "周末去的咖啡馆",
    "file": "content_cafe.txt",
    "category": "checkin",
    "vibe": "温暖",
    "images": 3,
    "tags": ["探店", "咖啡"]
  }
]
```

跑一下：

```bash
python3 scripts/xiaohongshu_pipeline.py batch recipes.json
```

---

## 图片模型

默认用通义千问：

- `Qwen/Qwen-Image` — 通义千问，日常够用
- `Kwai-Kolors/Kolors` — 快手可图，中文理解好
- `Tongyi-MAI/Z-Image` — 通义万相
- `Tongyi-MAI/Z-Image-Turbo` — 通义万相快速版
- `baidu/ERNIE-Image-Turbo` — 百度的

---

## 文件结构

```
agents/xiaohongshu/
├── scripts/
│   ├── xiaohongshu_pipeline.py    # 主逻辑
│   ├── gen_image.py               # 调 API 出图
│   └── preview_post.py            # HTML 预览
├── references/
│   ├── xiaohongshu-copywriting.md    # 文案怎么写
│   └── xiaohongshu-image-prompts.md  # 配图描述体系
├── output/
│   ├── posts/                      # 草稿
│   └── images/                     # 配图
└── skills/                         # agent 技能定义
---

## 几句废话

- 文案走第一人称，短段落，多 emoji，小红书上常见的那个风格
- 配图描述会自动生成多个角度（特写、俯拍、场景），不是一模一样来三张
- 草稿是纯文本 Markdown，想改直接改
- API Key 放环境变量，别写代码里——我一开始就踩了这坑，git push 完才想起来
