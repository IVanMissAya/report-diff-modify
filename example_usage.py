#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例 - 报告差异比对与修改技能
"""

import sys
import os
import json

# 添加技能目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_diff_modify import report_diff_modify, print_differences_table


def example_basic():
    """基本使用示例"""
    print("=" * 60)
    print("Example 1: Basic Usage (Default Rules)")
    print("=" * 60)
    
    pdf_path = r"D:\code_files\anci_work\报告审核\模板\危险特性分类鉴别报告\S03A25070727W00201 尚行 PB14SG5000-PDM 危险特性分类鉴别报告_20250804173658.pdf"
    
    api_json = {
        "reportNo": "ABC123",
        "goodsName1": "新型移动电源",
        "aCompanyName": "新公司名称",
        "issueTime": "2026-01-01"
    }
    
    result = report_diff_modify(pdf_path, api_json)
    
    print("\n[EXTRACTED JSON]:")
    print(json.dumps(result.get("extracted_json", {}), ensure_ascii=False, indent=2))
    
    print("\n[DIFFERENCES TABLE]:")
    print(print_differences_table(result.get("differences", [])))
    
    print(f"\n[STATUS]: {result.get('message', '')}")
    print(f"[NEW FILE]: {result.get('new_file_path', '')}")
    
    return result


def example_custom_rules():
    """自定义提取规则示例"""
    print("\n" + "=" * 60)
    print("Example 2: Custom Rules")
    print("=" * 60)
    
    pdf_path = r"D:\code_files\anci_work\报告审核\模板\危险特性分类鉴别报告\S03A25070727W00201 尚行 PB14SG5000-PDM 危险特性分类鉴别报告_20250804173658.pdf"
    
    api_json = {
        "reportNo": "NEW-REPORT-001",
        "goodsName1": "定制产品名称"
    }
    
    custom_rules = [
        {
            "field": "reportNo",
            "match_keywords": ["报告编号", "Report No.", "No."],
            "value_rule": "extract_after_keyword"
        },
        {
            "field": "goodsName1",
            "match_keywords": ["产品名称", "物品名称"],
            "value_rule": "extract_line"
        }
    ]
    
    result = report_diff_modify(
        pdf_path=pdf_path,
        api_json=api_json,
        extract_rules=custom_rules,
        output_prefix="custom_"
    )
    
    print("\n[EXTRACTED JSON]:")
    print(json.dumps(result.get("extracted_json", {}), ensure_ascii=False, indent=2))
    
    print("\n[DIFFERENCES TABLE]:")
    print(print_differences_table(result.get("differences", [])))
    
    print(f"\n[STATUS]: {result.get('message', '')}")
    
    return result


if __name__ == "__main__":
    example_basic()
