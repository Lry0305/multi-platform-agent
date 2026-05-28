# Business Simulation Decision Agent Skill

**用途：** 基于 Jessie 8.1 商业模拟的 Excel/PDF 数据做决策分析与建议。
**适用企业：** BRK.A（Company 7，G2 组）

---

## ⚠️ Negative Triggers（不适用场景）

- ❌ 不用于真实商业决策（此 skill 为课堂 Jessie 8.1 模拟专用）
- ❌ 不用于小红书内容/图文生成
- ❌ 不用于代码开发或系统配置任务
- ❌ 不用于金融投资建议或股票分析

---

## 标准工作流程

### Step 1 — 读取数据文件

读取用户传来的 Excel（决策表 + 结果表）。

```bash
# 读取所有 sheet
python3 scripts/excel_reader.py read <filepath>

# 读取指定 sheet
python3 scripts/excel_reader.py read <filepath> "Decisions P1"
python3 scripts/excel_reader.py read <filepath> "Results P1"
```

**如果用户发的是 PDF**（如手册、规则文档）：

```bash
# 提取全文
python3 scripts/pdf_reader.py all <filepath>

# 仅提取表格
python3 scripts/pdf_reader.py tables <filepath>
```

### Step 2 — 参考知识库

根据任务阶段，读取对应的 reference：

| 场景 | 读哪个 reference |
|------|-----------------|
| 理解决策表结构 | `references/jessie8-manual-summary.md`（第1-2节） |
| 需要具体参数/系数 | `references/jessie8-handbook.txt`（第10节系数表） |
| 需要产品定位区间 | `references/jessie8-manual-summary.md`（S1-S6 定位表） |
| 需要常见避坑 | `references/jessie8-manual-summary.md`（第9节常见错误） |
| 需要 FAQ / 策略要点 | `references/jessie8-handbook.txt`（第7节 FAQ） |

### Step 3 — 数据分析

读取 Results 数据后，分析以下关键指标：

1. **财务状况**
   - 现金变化（Cash）
   - 收入 vs 成本
   - 利润/亏损
   - 固定资产与折旧

2. **各产品表现**
   - 销量 vs 产量 → 库存情况
   - 价格 vs 竞品 → 定价合理性
   - 广告投放 vs 竞品
   - 定位 vs 竞品

3. **竞品监控**
   - 各公司产品定价
   - 广告预算
   - 定位策略

4. **市场格局**
   - 各 segment 竞争密集度
   - 是否有蓝海定位空间

### Step 4 — 生成决策建议

基于分析结果，输出结构化建议：

```
┌─────────────────────────────────────┐
│  P{X} 决策建议 — BRK.A               │
├─────────────────────────────────────┤
│ 1. 现状总结                          │
│    - 财务状况: ...                   │
│    - 产品表现: ...                   │
│    - 竞品格局: ...                   │
│                                     │
│ 2. 本期关键决策                       │
│    □ 新品上市？ → 定位/参数           │
│    □ 撤产品？                         │
│    □ 价格调整？                       │
│    □ 广告调整？                       │
│    □ 产量调整 + 投资                  │
│    □ 贷款需求？                       │
│                                     │
│ 3. 决策表填写建议（可直接填入）         │
│    - New product: N°_ X__ Y__        │
│    - Product 1: 产量__ 质量__ 价格__ 广告__
│    - Salesmen: __  Credit: __        │
│    - Investment: __                  │
│    - Loan: __ @ __%                  │
│                                     │
│ 4. 风险提醒                          │
│    - ...                             │
└─────────────────────────────────────┘
```

### Step 5 — 如果用户要求，写入 Excel

```bash
# 更新指定单元格
python3 -c "
from openpyxl import load_workbook
wb = load_workbook('file.xlsx')
ws = wb['Decisions P3']
# ... fill cells
wb.save('file.xlsx')
"
```

---

## 输出要求（Output Contract）

- ✅ 所有建议必须有数据支撑（引用 Result sheet 中的具体数字）
- ✅ 决策值必须为整数（Jessie 8.1 规则要求）
- ✅ 每个调整必须附简短 rationale（为什么调）
- ✅ 格式使用 GFM 表格或列表，便于阅读
- ❌ 不做没有数据支撑的主观建议

---

## 脚本速查

```bash
# Excel
scripts/excel_reader.py read <file> [sheet]    # 读数据
scripts/excel_reader.py list <file>             # 列 sheets
scripts/excel_reader.py write <file> <json>     # 写数据

# PDF
scripts/pdf_reader.py text <file>               # 提取文本
scripts/pdf_reader.py tables <file>             # 提取表格
scripts/pdf_reader.py all <file>                # 全部提取

# 决策引擎
scripts/decision_engine.py                      # 分析框架
```

## 依赖

- Python 3.8+ · openpyxl · pandas · pdfplumber
