SKILL.md — Word 排版规范指南

## python-docx 常用操作速查

### 段落样式
```python
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# 各级标题
doc.add_heading("一级标题", level=1)  # 自动粗体大号
doc.add_heading("二级标题", level=2)
doc.add_heading("三级标题", level=3)

# 正文
p = doc.add_paragraph()
p.paragraph_format.first_line_indent = Pt(22)  # 首行缩进
run = p.add_run("这是正文内容")
run.font.size = Pt(11)
run.font.name = "PingFang SC"
```

### 表格
```python
table = doc.add_table(rows=3, cols=4)
table.style = "Light Grid Accent 1"  # 内置样式

# 或者自定义样式
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2E86AB"/>')
cell._tc.get_or_add_tcPr().append(shading)
```

### 图片
```python
doc.add_picture("chart.png", width=Inches(5.5))
# 居中需要在段落层面设置
```

### 页面设置
```python
section = doc.sections[0]
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.17)
section.right_margin = Cm(3.17)
```

### 页码
```python
# 使用 PAGE 域代码（可读性不如直接设置）
# 详见 word_reporter.py 中的 add_page_number()
```

## 排版规范建议

| 元素 | 推荐设置 |
|------|---------|
| 封面标题 | 26pt 粗体，居中 |
| 一级标题 | 18pt 粗体，左对齐 |
| 二级标题 | 14pt 粗体，左对齐 |
| 正文 | 11pt，行距1.35，首行缩进2字符 |
| 图片 | 宽度5-5.5英寸，居中 |
| 图注 | 10.5pt 粗体，居中 |
| 表格 | 10pt 居中，表头深色底白色字 |
| 页边距 | 上下2.54cm，左右3.17cm |
| 页码 | 页脚居中，"第 X 页" |
