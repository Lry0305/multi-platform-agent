# Hermes + 多平台 Agent CLI 集成方案

Hermes 不需要 import 代码，直接通过命令行调用就行。

---

## 基本结构

```
Hermes brain
    │
    ├── python3 agent.py --topic "..."         → 出文案+配图+草稿
    ├── python3 scripts/comfyui_video.py ...    → 出视频（连 AutoDL）
    ├── python3 scripts/xiaohongshu_pipeline.py → 管线细粒度控制
    └── python3 scripts/gen_image.py ...        → 单张出图
```

Hermes 只用 `subprocess.run()` 或 `os.system()` 就能调用，不涉及代码侵入。

---

## 命令大全

### 1. 完整生成一条帖子（文案+配图+排版+存草稿）

```bash
python3 agent.py \
  --topic "用了两周的护手霜，手嫩到被同事追问" \
  --platform xiaohongshu \
  --category recommend \
  --vibe 温暖 \
  --images 2
```

**Hermes 调用：**
```python
import subprocess
result = subprocess.run([
    "python3", "agent.py",
    "--topic", "用了两周的护手霜，手嫩到被同事追问",
    "--platform", "xiaohongshu",
    "--category", "recommend",
    "--vibe", "温暖",
    "--images", "2"
], capture_output=True, text=True)
print(result.stdout)
```

### 2. 只出文案，不出图（快速预览）

```bash
python3 agent.py --topic "..." --dry-run
```

### 3. 出视频（连 AutoDL ComfyUI）

```bash
python3 scripts/comfyui_video.py \
  --host "http://你的AutoDLIP:8188" \
  --prompt "护手霜在阳光下，产品展示视频" \
  --model wan \
  --output output/videos
```

**Hermes 调用：**
```python
subprocess.run([
    "python3", "scripts/comfyui_video.py",
    "--host", "http://你的AutoDLIP:8188",
    "--prompt", "护手霜产品展示视频",
    "--model", "wan",
    "--output", "output/videos"
])
```

### 4. 多平台分发

```bash
# 同上内容，发公众号
python3 agent.py --topic "..." --platform wechat --style tech

# 发抖音
python3 agent.py --topic "..." --platform douyin
```

### 5. 批量生成（从 JSON 配置）

```bash
python3 scripts/xiaohongshu_pipeline.py batch recipes.json
```

---

## Hermes 完整工作流示例

```python
import subprocess, json

def generate_and_publish(topic, platform="xiaohongshu"):
    # 1. 生成内容
    r = subprocess.run([
        "python3", "agent.py",
        "--topic", topic,
        "--platform", platform,
        "--images", "2"
    ], capture_output=True, text=True)
    
    # 2. 如果需要视频
    r2 = subprocess.run([
        "python3", "scripts/comfyui_video.py",
        "--host", "http://你的AutoDLIP:8188",
        "--prompt", topic,
        "--model", "wan"
    ], capture_output=True, text=True)
    
    return {"content": r.stdout, "video": r2.stdout}

# Hermes 只要调用这个函数就行
result = generate_and_publish("护手霜推荐")
```

---

## 注意事项

- Hermes 和 agent 需要在**同一台机器**或同一网络
- 调用前要先 `cd` 到项目目录（或命令里写绝对路径）
- 视频生成需要 AutoDL GPU 实例开机状态
- 输出文件在 `output/posts/`（文案草稿）和 `output/images/`（图片）和 `output/videos/`（视频）
