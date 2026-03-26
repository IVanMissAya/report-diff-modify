from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from typing import Optional
from report_diff_modify import report_diff_modify, print_differences_table
import uuid
import shutil

# 初始化 FastAPI 应用
app = FastAPI(
    title="Report Diff Modify API",
    description="PDF报告对比、差异分析、自动修改并生成新文件的API服务",
    version="1.0.0",
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# 硬编码输出目录（你指定的路径）
# --------------------------
from config import FIXED_OUTPUT_DIR, TEMP_DIR, HOST, PORT

# 自动创建目录（不存在则新建）
os.makedirs(FIXED_OUTPUT_DIR, exist_ok=True)

# 临时文件目录（存储上传的PDF，避免污染输出目录）
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)


@app.post("/api/report-diff-modify", summary="PDF报告对比修改接口")
async def report_diff_modify_api(
    file: UploadFile = File(..., description="要处理的PDF报告文件"),
    api_json: str = Form(..., description="对比用的标准JSON字符串"),
    extract_rules: Optional[str] = Form(
        None, description="可选：自定义提取规则JSON字符串"
    ),
    output_prefix: Optional[str] = Form(
        "", description="新文件前缀，为空则用时间戳命名"
    ),
):
    try:
        print(f"[INFO] 收到请求，文件名：{file.filename}")

        # 1. 解析 api_json（严格校验）
        try:
            api_json_obj = json.loads(api_json)
            print(
                f"[INFO] api_json 解析成功：{json.dumps(api_json_obj, ensure_ascii=False)}"
            )
        except json.JSONDecodeError as e:
            print(f"[ERROR] api_json 解析失败：{str(e)}")
            raise HTTPException(
                status_code=400, detail=f"api_json 不是合法JSON: {str(e)}"
            )

        # 2. 解析 extract_rules（可选）
        extract_rules_obj = None
        if extract_rules:
            try:
                extract_rules_obj = json.loads(extract_rules)
                print(
                    f"[INFO] extract_rules 解析成功：{json.dumps(extract_rules_obj, ensure_ascii=False)}"
                )
            except json.JSONDecodeError as e:
                print(f"[ERROR] extract_rules 解析失败：{str(e)}")
                raise HTTPException(
                    status_code=400, detail=f"extract_rules 不是合法JSON: {str(e)}"
                )

        # 3. 保存上传的PDF到临时目录（避免污染输出目录）
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        temp_pdf_path = os.path.join(TEMP_DIR, unique_filename)

        with open(temp_pdf_path, "wb") as f:
            f.write(await file.read())
        print(f"[INFO] 上传文件已保存到临时目录：{temp_pdf_path}")

        # 4. 调用核心业务逻辑（完全遵循report_diff_modify的文件名规则）
        print(f"[INFO] 调用 report_diff_modify 函数，参数：pdf_path={temp_pdf_path}")
        result = report_diff_modify(
            pdf_path=temp_pdf_path,
            api_json=api_json_obj,
            extract_rules=extract_rules_obj,
            output_prefix=output_prefix,
        )
        print(
            f"[INFO] 函数返回结果：{json.dumps(result, ensure_ascii=False, indent=2)}"
        )

        # 5. 检查执行结果
        if not result.get("success", False):
            print(f"[ERROR] 函数执行失败：{result.get('message', '未知错误')}")
            raise HTTPException(
                status_code=500, detail=result.get("message", "处理失败")
            )

        # 6. 【修复】正确获取函数生成的临时文件路径（修正key拼写错误）
        original_new_path = result.get("new_file_path")
        if not original_new_path or not os.path.exists(original_new_path):
            print(f"[ERROR] 函数生成的临时文件不存在：{original_new_path}")
            raise HTTPException(status_code=500, detail="函数未生成有效新文件")

        # 7. 【修复】直接用函数生成的文件名，复制到固定目录（完全遵循你的文件名规则）
        new_file_name = os.path.basename(original_new_path)
        new_pdf_path = os.path.join(FIXED_OUTPUT_DIR, new_file_name)

        # 复制到硬编码目录
        shutil.copy2(original_new_path, new_pdf_path)
        print(f"[INFO] 新文件已复制到硬编码目录：{new_pdf_path}")

        # 8. 验证新文件
        if not os.path.exists(new_pdf_path):
            print(f"[ERROR] 硬编码目录下文件不存在：{new_pdf_path}")
            raise HTTPException(status_code=500, detail="新文件生成失败")

        # 9. 清理临时文件（可选，避免占用空间）
        os.remove(temp_pdf_path)
        os.remove(original_new_path)
        print(f"[INFO] 临时文件已清理")

        # 10. 构造返回响应
        response_data = {
            "success": True,
            "message": f"处理成功，修改后文件地址为：{new_pdf_path}",
            "differences": result.get("differences", []),
            "extracted_json": result.get("extracted_json", {}),
            "new_file_name": new_file_name,
            "new_file_full_path": new_pdf_path,
            "download_url": f"/api/download/{new_file_name}",
        }

        # 保存文件路径映射（用于下载接口）
        app.state.file_map = getattr(app.state, "file_map", {})
        app.state.file_map[new_file_name] = new_pdf_path

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"[ERROR] 服务器内部错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.get("/api/download/{file_name}", summary="下载生成的新PDF文件")
async def download_file(file_name: str):
    file_map = getattr(app.state, "file_map", {})
    file_path = file_map.get(file_name)

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")

    return FileResponse(file_path, media_type="application/pdf", filename=file_name)


@app.get("/api/health", summary="服务健康检查")
async def health_check():
    return {
        "status": "healthy",
        "service": "report-diff-modify-api",
        "output_dir": FIXED_OUTPUT_DIR,
        "dir_exists": os.path.exists(FIXED_OUTPUT_DIR),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)