#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告差异比对与自动修改技能
Report Diff & Modify Skill

功能：
1. 从 PDF 报告中提取关键信息
2. 与外部传入的 JSON 数据进行比对
3. 将差异值自动修改到原文件中，生成新文件
"""

import fitz  # PyMuPDF
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


# 默认提取规则
DEFAULT_EXTRACT_RULES = [
    {
        "field": "goodsName1",
        "match_keywords": ["物品名称", "测试样品", "样品名称", "产品名称"],
        "value_rule": "extract_line"
    },
    {
        "field": "aCompanyName",
        "match_keywords": ["委托单位", "测试单位", "申请单位"],
        "value_rule": "extract_after_colon"
    },
    {
        "field": "issueTime",
        "match_keywords": ["签发日期", "发证日期", "出具日期", "日期"],
        "value_rule": "extract_after_colon"
    },
    {
        "field": "reportNo",
        "match_keywords": ["报告编号", "Report No.", "报告号", "No."],
        "value_rule": "extract_after_keyword"
    }
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """从 PDF 中提取所有文本内容"""
    doc = None
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text
    except Exception as e:
        print(f"[ERROR] 提取PDF文本失败：{e}")
        return ""
    finally:
        if doc:
            doc.close()
            print(f"[INFO] 已释放PDF文件句柄：{pdf_path}")


def extract_field_value(text: str, rule: Dict) -> Optional[str]:
    """根据规则从文本中提取字段值"""
    field = rule.get("field", "")
    keywords = rule.get("match_keywords", [])
    value_rule = rule.get("value_rule", "extract_after_colon")
    
    for keyword in keywords:
        # 查找关键词位置
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            continue
        
        # 获取关键词所在行及上下文
        start = max(0, keyword_pos - 50)
        end = min(len(text), keyword_pos + 200)
        context = text[start:end]
        
        if value_rule == "extract_after_colon":
            # 提取冒号后的内容
            match = re.search(rf'{re.escape(keyword)}[:：]\s*([^\n\r]+)', context)
            if match:
                return match.group(1).strip()
        
        elif value_rule == "extract_after_keyword":
            # 提取关键词后的内容（可能是空格或冒号分隔）
            match = re.search(rf'{re.escape(keyword)}[:：\s]*([^\n\r]+)', context)
            if match:
                return match.group(1).strip()
        
        elif value_rule == "extract_line":
            # 提取整行内容（去除关键词）
            lines = context.split('\n')
            for line in lines:
                if keyword in line:
                    # 移除关键词本身
                    value = line.replace(keyword, '').strip(' :：')
                    return value.strip()
    
    return None


def extract_json_from_pdf(pdf_path: str, extract_rules: List[Dict] = None) -> Dict[str, str]:
    """从 PDF 中提取 JSON 数据"""
    if extract_rules is None:
        extract_rules = DEFAULT_EXTRACT_RULES
    
    text = extract_text_from_pdf(pdf_path)
    result = {}
    
    for rule in extract_rules:
        field = rule.get("field", "")
        value = extract_field_value(text, rule)
        if value:
            result[field] = value
    
    return result


def compare_json(extracted: Dict[str, str], api_json: Dict[str, str]) -> List[Dict[str, str]]:
    """比对两个 JSON，返回差异列表"""
    differences = []
    
    # 找出共同的键
    common_keys = set(extracted.keys()) & set(api_json.keys())
    
    for key in common_keys:
        doc_value = extracted.get(key, "")
        api_value = api_json.get(key, "")
        
        if doc_value != api_value:
            differences.append({
                "field": key,
                "doc_value": doc_value,
                "api_value": api_value
            })
    
    return differences


def modify_pdf(pdf_path: str, new_pdf_path: str, replacements: List[Tuple[str, str]]) -> bool:
    """
    【核心修复】正确的PDF修改逻辑
    直接打开原文件，修改后保存到新路径，彻底避免增量保存报错和文件锁
    """
    # 先删除目标文件（如果存在），避免残留
    if os.path.exists(new_pdf_path):
        try:
            os.remove(new_pdf_path)
            print(f"[INFO] 已删除旧目标文件：{new_pdf_path}")
        except Exception as e:
            print(f"[ERROR] 删除旧文件失败：{e}")
            return False
    
    doc = None
    try:
        print(f"[INFO] 开始修改PDF，原文件：{pdf_path}，新文件：{new_pdf_path}")
        # 【关键】直接打开原文件，不复制，避免文件占用
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"[INFO] 正在处理第 {page_num+1} 页")
            
            for old_text, new_text in replacements:
                if not old_text:
                    continue
                    
                # 查找文本位置
                text_instances = page.search_for(old_text)
                if text_instances:
                    print(f"[INFO] 找到匹配文本：{old_text} → 替换为：{new_text}，共 {len(text_instances)} 处")
                
                for inst in text_instances:
                    # 添加白色矩形覆盖原文本
                    page.draw_rect(inst, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # 计算合适的字体大小
                    rect_height = abs(inst.y1 - inst.y0)
                    font_size = max(8, min(rect_height * 0.7, 12))
                    
                    # 在相同位置写入新文本
                    page.insert_text(
                        (inst.x0, inst.y0 + rect_height * 0.8),
                        new_text,
                        fontsize=font_size,
                        color=(0, 0, 0)
                    )
        
        # 【关键】直接保存到新路径，全新文件，不需要增量保存
        doc.save(new_pdf_path)
        print(f"[INFO] PDF修改完成，已保存到：{new_pdf_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 修改 PDF 失败：{e}")
        # 清理失败的文件
        if os.path.exists(new_pdf_path):
            try:
                os.remove(new_pdf_path)
            except:
                pass
        return False
    finally:
        if doc:
            doc.close()
            print(f"[INFO] 已释放PDF文件句柄")


def report_diff_modify(
    pdf_path: str,
    api_json: Dict[str, str],
    extract_rules: List[Dict] = None,
    output_prefix: str = ""
) -> Dict[str, Any]:
    """
    主函数：报告差异比对与修改
    
    参数:
        pdf_path: PDF 文件路径
        api_json: 外部传入的 JSON 数据
        extract_rules: 提取规则（可选，使用默认规则）
        output_prefix: 输出文件前缀（为空则用时间戳命名）
    
    返回:
        {
            "success": bool,
            "extracted_json": dict,
            "differences": list,
            "new_file_path": str,
            "message": str
        }
    """
    result = {
        "success": False,
        "extracted_json": {},
        "differences": [],
        "new_file_path": "",
        "message": ""
    }
    
    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        result["message"] = f"文件不存在：{pdf_path}"
        print(f"[ERROR] {result['message']}")
        return result
    
    # 检查文件是否为 PDF
    if not pdf_path.lower().endswith('.pdf'):
        result["message"] = "文件不是 PDF 格式"
        print(f"[ERROR] {result['message']}")
        return result
    
    try:
        print(f"[INFO] 开始处理PDF文件：{pdf_path}")
        # 1. 从 PDF 中提取数据
        extracted_json = extract_json_from_pdf(pdf_path, extract_rules)
        result["extracted_json"] = extracted_json
        print(f"[INFO] 从PDF中提取到数据：{json.dumps(extracted_json, ensure_ascii=False)}")
        
        if not extracted_json:
            result["message"] = "未能从 PDF 中提取到任何数据"
            print(f"[ERROR] {result['message']}")
            return result
        
        # 2. 比对差异
        differences = compare_json(extracted_json, api_json)
        result["differences"] = differences
        print(f"[INFO] 比对到差异：{json.dumps(differences, ensure_ascii=False)}")
        
        if not differences:
            result["success"] = True
            result["message"] = "没有发现差异，无需修改文件"
            print(f"[INFO] {result['message']}")
            return result
        
        # 3. 准备替换列表
        replacements = []
        for diff in differences:
            field = diff["field"]
            doc_value = diff["doc_value"]
            api_value = diff["api_value"]
            if doc_value and api_value:
                replacements.append((doc_value, api_value))
        print(f"[INFO] 生成替换列表：{replacements}")
        
        # ==============================
        # 文件名生成逻辑，彻底避免重名
        # ==============================
        base_name = os.path.basename(pdf_path)
        file_dir = os.path.dirname(pdf_path)
        
        # 生成文件名：无前缀用时间戳，有前缀用前缀，绝对不和原文件重名
        if not output_prefix or output_prefix.strip() == "":
            # 格式：年月日时分秒_原文件名
            time_str = datetime.now().strftime("%Y%m%d%H%M%S")
            new_file_name = f"{time_str}_{base_name}"
        else:
            # 格式：前缀_原文件名（自动补全下划线）
            prefix_clean = output_prefix.strip()
            if not prefix_clean.endswith("_"):
                prefix_clean += "_"
            new_file_name = f"{prefix_clean}{base_name}"
        
        new_pdf_path = os.path.join(file_dir, new_file_name)
        print(f"[INFO] 生成新文件路径：{new_pdf_path}")

        # 5. 修改 PDF
        if modify_pdf(pdf_path, new_pdf_path, replacements):
            # 二次验证文件是否生成成功
            if os.path.exists(new_pdf_path) and os.path.getsize(new_pdf_path) > 0:
                result["new_file_path"] = new_pdf_path
                result["success"] = True
                result["message"] = f"修改完成，新文件已保存至：{new_pdf_path}"
                print(f"[SUCCESS] {result['message']}")
            else:
                result["message"] = "PDF文件生成失败，文件为空或不存在"
                print(f"[ERROR] {result['message']}")
        else:
            result["message"] = "修改 PDF 文件失败"
            print(f"[ERROR] {result['message']}")
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        result["message"] = f"处理过程中发生错误：{str(e)}"
        print(f"[ERROR] {result['message']}")
        return result


def print_differences_table(differences: List[Dict]) -> str:
    """将差异列表格式化为表格字符串"""
    if not differences:
        return "没有发现差异"
    
    # 计算列宽
    field_width = max(len("field"), max((len(d["field"]) for d in differences), default=0))
    doc_width = max(len("doc_value"), max((len(str(d["doc_value"])) for d in differences), default=0))
    api_width = max(len("api_value"), max((len(str(d["api_value"])) for d in differences), default=0))
    
    # 构建表格
    lines = []
    lines.append(f"| {'field'.ljust(field_width)} | {'doc_value'.ljust(doc_width)} | {'api_value'.ljust(api_width)} |")
    lines.append(f"| {'-' * field_width} | {'-' * doc_width} | {'-' * api_width} |")
    
    for diff in differences:
        lines.append(f"| {diff['field'].ljust(field_width)} | {str(diff['doc_value']).ljust(doc_width)} | {str(diff['api_value']).ljust(api_width)} |")
    
    return "\n".join(lines)


# CLI 入口
if __name__ == "__main__":
    # 测试示例
    test_pdf = r"D:\code_files\anci_work\报告审核\模板\危险特性分类鉴别报告\S03A25070727W00201 尚行 PB14SG5000-PDM 危险特性分类鉴别报告_20250804173658.pdf"
    test_api_json = {
        "reportNo": "ABC",
        "goodsName1": "QWER",
        "aCompanyName": "尚行智造科技（东莞）有限公司",
        "issueTime": "2026-03-24"
    }
    
    result = report_diff_modify(test_pdf, test_api_json, output_prefix="")
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result["differences"]:
        print("\n差异对比表：")
        print(print_differences_table(result["differences"]))