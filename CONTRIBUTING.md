# 🤝 贡献指南

## 加一个新平台

只需三步：

### 1. 继承 BasePublisher

在 `platform/` 下新建文件，比如 `bilibili.py`：

```python
from .base import BasePublisher, Post

class BilibiliPublisher(BasePublisher):
    @property
    def platform_name(self):
        return "哔哩哔哩"

    @property
    def max_title_length(self):
        return 32

    @property
    def max_content_length(self):
        return 2000

    def format_post(self, post: Post):
        # 按 B 站风格排版
        ...
```

### 2. 注册

在 `platform/__init__.py` 的 `registry` 字典里加上：

```python
from .bilibili import BilibiliPublisher

def get_publisher(platform):
    registry = {
        ...
        "bilibili": BilibiliPublisher,
    }
```

### 3. 使用

```bash
python3 agent.py --topic "..." --platform bilibili
```

## 代码规范

- Python 3.8+，优先用标准库
- 函数/类加 docstring
- 文件名小写+下划线
- 提交信息用中文，说清做了什么

## 提 PR

1. Fork 仓库
2. 新建分支
3. 改代码 + 加测试（如果适用）
4. 提交 PR，描述清楚改了什么、为什么

## 开发环境

```bash
# 不需要虚拟环境，标准库就够了
python3 --version  # ≥ 3.8

# 可选：测试用
pip install pyperclip  # 剪贴板
pip install Pillow     # 图片处理
```
