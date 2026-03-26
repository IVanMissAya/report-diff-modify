#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Diff & Modify API - FastAPI 接口服务

报告差异比对与自动修改技能的 FastAPI 封装
"""

import sys
import os
import json

# 添加父目录到路径，以便导入 report_diff_modify 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from api.models import (
    ReportDiffRequest,
    ReportDiffResponse,
    DifferenceItem,
    HealthResponse,
    DiffTableResponse,
    ExtractRule
)
from report_diff_modify import (
    report_diff_modify,
    print_differences_table,
    DEFAULT_EXTRACT_RULES
)

# 创建 FastAPI 应用
app = FastAPI(
    title="Report Diff & Modify API",
    description="报告差异比对与自动修改技能 API 接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """根路径 - 返回 API 信息"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Report Diff & Modify API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { display: inline-block; padding: 3px 8px; border-radius: 3px; font-weight: bold; margin-right: 10px; }
            .get { background: #61affe; color: white; }
            .post { background: #49cc90; color: white; }
            a { color: #49cc90; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>📄 Report Diff & Modify API</h1>
        <p>报告差异比对与自动修改技能 API 接口</p>
        
        <h2>📚 API 端点</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/health</strong> - 健康检查
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/diff</strong> - 执行报告差异比对与修改
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v1/diff/table</strong> - 获取 HTML 格式的差异表格
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v1/rules</strong> - 获取默认提取规则
        </div>
        
        <h2>📖 文档</h2>
        <p><a href="/docs" target="_blank">Swagger UI</a> | <a href="/redoc" target="_blank">ReDoc</a></p>
    </body>
    </html>
    """
    return html


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查接口"""
    return HealthResponse()


@app.post("/api/v1/diff", response_model=ReportDiffResponse, tags=["Diff"])
async def diff_report(request: ReportDiffRequest):
    """
    执行报告差异比对与修改
    
    从 PDF 报告中提取数据，与 API JSON 比对，并生成修改后的文件
    """
    try:
        # 转换提取规则格式
        extract_rules = None
        if request.extract_rules:
            extract_rules = [
                {
                    "field": rule.field,
                    "match_keywords": rule.match_keywords,
                    "value_rule": rule.value_rule
                }
                for rule in request.extract_rules
            ]
        
        # 调用核心功能
        result = report_diff_modify(
            pdf_path=request.pdf_path,
            api_json=request.api_json,
            extract_rules=extract_rules,
            output_prefix=request.output_prefix
        )
        
        # 转换差异项为 Pydantic 模型
        differences = [
            DifferenceItem(
                field=d["field"],
                doc_value=d["doc_value"],
                api_value=d["api_value"]
            )
            for d in result.get("differences", [])
        ]
        
        return ReportDiffResponse(
            success=result.get("success", False),
            extracted_json=result.get("extracted_json", {}),
            differences=differences,
            new_file_path=result.get("new_file_path", ""),
            message=result.get("message", "")
        )
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件未找到：{str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败：{str(e)}"
        )


@app.post("/api/v1/diff/table", response_model=DiffTableResponse, tags=["Diff"])
async def diff_table(request: ReportDiffRequest):
    """
    获取 HTML 格式的差异表格
    
    返回可直接在网页中显示的差异对比表格
    """
    try:
        # 转换提取规则格式
        extract_rules = None
        if request.extract_rules:
            extract_rules = [
                {
                    "field": rule.field,
                    "match_keywords": rule.match_keywords,
                    "value_rule": rule.value_rule
                }
                for rule in request.extract_rules
            ]
        
        # 调用核心功能
        result = report_diff_modify(
            pdf_path=request.pdf_path,
            api_json=request.api_json,
            extract_rules=extract_rules,
            output_prefix=request.output_prefix
        )
        
        differences = result.get("differences", [])
        
        # 生成 HTML 表格
        if not differences:
            html_table = "<p>没有发现差异</p>"
        else:
            html_table = """
            <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th>Field (字段名)</th>
                        <th>Doc Value (文档值)</th>
                        <th>API Value (接口值)</th>
                    </tr>
                </thead>
                <tbody>
            """
            for diff in differences:
                html_table += f"""
                    <tr>
                        <td>{diff['field']}</td>
                        <td>{diff['doc_value']}</td>
                        <td style="color: #0066cc; font-weight: bold;">{diff['api_value']}</td>
                    </tr>
                """
            html_table += """
                </tbody>
            </table>
            """
        
        return DiffTableResponse(
            html_table=html_table,
            differences_count=len(differences)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成表格失败：{str(e)}"
        )


@app.get("/api/v1/rules", tags=["Config"])
async def get_default_rules():
    """获取默认提取规则配置"""
    return {
        "success": True,
        "rules": DEFAULT_EXTRACT_RULES
    }


@app.get("/api/v1/example", tags=["Example"])
async def get_example():
    """获取示例请求体"""
    return {
        "pdf_path": "D:/reports/test_report.pdf",
        "api_json": {
            "reportNo": "ABC123",
            "goodsName1": "产品名称",
            "aCompanyName": "公司名称",
            "issueTime": "2026-01-01"
        },
        "output_prefix": "修改后_"
    }


# 错误处理器
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"success": False, "message": "接口未找到"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "服务器内部错误"}
    )


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
