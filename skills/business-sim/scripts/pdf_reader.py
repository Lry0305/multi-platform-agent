#!/usr/bin/env python3
"""
PDF 读写工具 — 商业模拟决策用
支持提取文本、表格数据
"""

import pdfplumber
import json
import sys
from typing import Optional

def extract_text(filepath: str, page_numbers: Optional[list] = None) -> dict:
    """
    提取 PDF 文本内容
    - filepath: PDF 文件路径
    - page_numbers: 指定页码列表（0-indexed），默认全部
    返回: { "pages": [...], "total_pages": N, "full_text": "..." }
    """
    pages_data = []
    full_text_parts = []
    
    with pdfplumber.open(filepath) as pdf:
        total = len(pdf.pages)
        pages_to_read = page_numbers if page_numbers else range(total)
        
        for i in pages_to_read:
            if i >= total:
                continue
            page = pdf.pages[i]
            text = page.extract_text() or ""
            pages_data.append({
                "page_number": i + 1,
                "text": text,
                "chars_count": len(text)
            })
            full_text_parts.append(f"--- Page {i+1} ---\n{text}")
    
    return {
        "total_pages": total,
        "pages": pages_data,
        "full_text": "\n\n".join(full_text_parts)
    }

def extract_tables(filepath: str, page_numbers: Optional[list] = None) -> dict:
    """
    提取 PDF 中的表格数据
    返回: { "tables": [ { "page": N, "table_index": M, "data": [[...], ...] }, ... ] }
    """
    tables_data = []
    
    with pdfplumber.open(filepath) as pdf:
        total = len(pdf.pages)
        pages_to_read = page_numbers if page_numbers else range(total)
        
        for i in pages_to_read:
            if i >= total:
                continue
            page = pdf.pages[i]
            tables = page.extract_tables()
            for t_idx, table in enumerate(tables):
                tables_data.append({
                    "page": i + 1,
                    "table_index": t_idx,
                    "data": table
                })
    
    return {
        "total_pages": total,
        "tables": tables_data,
        "table_count": len(tables_data)
    }

def extract_all(filepath: str) -> dict:
    """同时提取文本和表格"""
    text_result = extract_text(filepath)
    table_result = extract_tables(filepath)
    
    return {
        "file": filepath,
        "text": text_result,
        "tables": table_result
    }

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    
    if command == "text" and len(sys.argv) >= 3:
        result = extract_text(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif command == "tables" and len(sys.argv) >= 3:
        result = extract_tables(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif command == "all" and len(sys.argv) >= 3:
        result = extract_all(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print("Usage:")
        print("  pdf_reader.py text <filepath>      — 提取文本")
        print("  pdf_reader.py tables <filepath>    — 提取表格")
        print("  pdf_reader.py all <filepath>       — 提取全部内容")
