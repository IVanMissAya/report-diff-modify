# Report Diff & Modify Skill

报告差异比对与自动修改技能

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from report_diff_modify import report_diff_modify

# 调用技能
result = report_diff_modify(
    pdf_path="path/to/your/report.pdf",
    api_json={
        "reportNo": "NEW-001",
        "goodsName1": "新产品名称",
        "aCompanyName": "新公司名称",
        "issueTime": "2026-01-01"
    }
)

# 查看结果
print(result)
```

### 在 OpenClaw 中使用

将此技能目录放置在 `~/.openclaw/workspace/skills/report-diff-modify` 下，然后在对话中调用即可。

## API 参考

### report_diff_modify()

```python
def report_diff_modify(
    pdf_path: str,
    api_json: Dict[str, str],
    extract_rules: List[Dict] = None,
    output_prefix: str = "修改后_"
) -> Dict[str, Any]
```

**参数:**
- `pdf_path`: PDF 文件路径
- `api_json`: 用于比对的外部 JSON 数据
- `extract_rules`: 提取规则（可选）
- `output_prefix`: 输出文件前缀（可选）

**返回:**
```json
{
  "success": true,
  "extracted_json": {...},
  "differences": [...],
  "new_file_path": "path/to/new/file.pdf",
  "message": "操作成功"
}
```

## 文件结构

```
report-diff-modify/
├── SKILL.md              # 技能描述（OpenClaw 读取）
├── report_diff_modify.py # 核心功能代码
├── example_usage.py      # 使用示例
├── requirements.txt      # Python 依赖
└── README.md             # 本文件
```

## 注意事项

1. PDF 文件需要有文本层（非扫描图片）
2. 确保文件没有被其他程序占用
3. 修改后的文件保存在原文件同目录下

## 版本历史

- v1.0.0 - 初始版本
