#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic 模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class ExtractRule(BaseModel):
    """提取规则模型"""
    field: str = Field(..., description="字段名")
    match_keywords: List[str] = Field(..., description="匹配关键词列表")
    value_rule: str = Field(default="extract_after_colon", description="提取规则类型")


class ReportDiffRequest(BaseModel):
    """请求体模型"""
    pdf_path: str = Field(..., description="PDF 文件路径", examples=["D:/reports/test.pdf"])
    api_json: Dict[str, str] = Field(..., description="API 数据 JSON", examples=[
        {"reportNo": "ABC123", "goodsName1": "产品", "aCompanyName": "公司", "issueTime": "2026-01-01"}
    ])
    extract_rules: Optional[List[ExtractRule]] = Field(None, description="自定义提取规则（可选）")
    output_prefix: Optional[str] = Field("修改后_", description="输出文件前缀", examples=["修改后_"])


class DifferenceItem(BaseModel):
    """差异项模型"""
    field: str = Field(..., description="字段名")
    doc_value: str = Field(..., description="文档中的值")
    api_value: str = Field(..., description="API 中的值")


class ReportDiffResponse(BaseModel):
    """响应体模型"""
    success: bool = Field(..., description="操作是否成功")
    extracted_json: Dict[str, str] = Field(default={}, description="从 PDF 中提取的 JSON 数据")
    differences: List[DifferenceItem] = Field(default=[], description="差异列表")
    new_file_path: str = Field(default="", description="修改后的新文件路径")
    message: str = Field(default="", description="状态消息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    service: str = "report-diff-modify-api"
    version: str = "1.0.0"


class DiffTableResponse(BaseModel):
    """差异表格响应（HTML 格式）"""
    html_table: str = Field(..., description="HTML 格式的差异表格")
    differences_count: int = Field(..., description="差异数量")
