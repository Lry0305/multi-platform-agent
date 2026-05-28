#!/usr/bin/env python3
"""
Excel 读写工具 — 商业模拟决策用
支持 .xlsx / .xls 格式的读取、写入、更新
"""

import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter
from typing import Optional
import json
import sys
import os

def read_excel(filepath: str, sheet_name: Optional[str] = None, header_row: int = 0) -> dict:
    """
    读取 Excel 文件，返回结构化 JSON
    - filepath: 文件路径
    - sheet_name: 指定 sheet（可选，默认返回所有 sheet）
    - header_row: 表头行号（0-indexed）
    """
    result = {}
    
    if sheet_name:
        sheets = [sheet_name]
    else:
        xl = pd.ExcelFile(filepath, engine='openpyxl')
        sheets = xl.sheet_names
    
    for sheet in sheets:
        df = pd.read_excel(filepath, sheet_name=sheet, header=header_row)
        # 将 NaN 转为 None（JSON 会变成 null）
        df = df.where(pd.notnull(df), None)
        result[sheet] = {
            "columns": list(df.columns),
            "rows": df.values.tolist(),
            "shape": list(df.shape),
            "data": df.to_dict(orient='records')
        }
    
    return result

def write_excel(filepath: str, data: dict, sheet_name: str = "Sheet1"):
    """
    写入 Excel 文件
    - data: {"columns": [...], "rows": [[...], ...]} 格式
    - 或直接传入 DataFrame 可用的 dict
    """
    if "columns" in data and "rows" in data:
        df = pd.DataFrame(data["rows"], columns=data["columns"])
    else:
        df = pd.DataFrame(data)
    
    # 如果文件已存在，追加 sheet；否则新建
    if os.path.exists(filepath):
        with pd.ExcelWriter(filepath, engine='openpyxl', mode='a') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df.to_excel(filepath, sheet_name=sheet_name, index=False)
    
    return {"status": "ok", "file": filepath, "sheet": sheet_name, "rows": len(df)}

def update_cell(filepath: str, sheet: str, row: int, col: int, value):
    """
    更新 Excel 中指定单元格的值（1-indexed row/col）
    """
    wb = openpyxl.load_workbook(filepath)
    ws = wb[sheet]
    ws.cell(row=row, column=col, value=value)
    wb.save(filepath)
    return {"status": "ok", "cell": f"{get_column_letter(col)}{row}", "value": value}

def list_sheets(filepath: str) -> list:
    """列出 Excel 文件中的所有 sheet 名称"""
    xl = pd.ExcelFile(filepath, engine='openpyxl')
    return xl.sheet_names

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if command == "read" and len(sys.argv) >= 3:
        result = read_excel(sys.argv[2], sheet_name=sys.argv[3] if len(sys.argv) > 3 else None)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    elif command == "list" and len(sys.argv) >= 3:
        sheets = list_sheets(sys.argv[2])
        print(json.dumps(sheets, ensure_ascii=False, indent=2))
    elif command == "write" and len(sys.argv) >= 4:
        data = json.loads(sys.argv[3])
        result = write_excel(sys.argv[2], data, sheet_name=sys.argv[4] if len(sys.argv) > 4 else "Sheet1")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage:")
        print("  excel_reader.py read <filepath> [sheet_name]   — 读取 Excel")
        print("  excel_reader.py list <filepath>                — 列出 sheets")
        print("  excel_reader.py write <filepath> <json_data> [sheet] — 写入 Excel")
