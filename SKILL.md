# report-diff-modify

报告差异比对与自动修改技能

## 功能描述

本技能用于自动提取 PDF 报告中的关键信息，与外部传入的 JSON 数据进行比对，并将差异值自动修改到原文件中，生成新文件。

## 使用场景

- 报告审核与数据校验
- 批量修改报告中的关键字段
- API 数据与文档数据一致性比对

## 输入参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `pdf_path` | string | 是 | PDF 报告文件的完整路径 |
| `api_json` | object | 是 | 外部传入的 JSON 数据，用于比对 |
| `extract_rules` | array | 否 | 提取规则配置（使用默认规则可省略） |
| `output_prefix` | string | 否 | 输出文件前缀，默认为"修改后_" |

## 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `extracted_json` | object | 从 PDF 中提取的 JSON 数据 |
| `differences` | array | 差异列表，包含 field、doc_value、api_value |
| `new_file_path` | string | 修改后的新文件路径 |
| `success` | boolean | 操作是否成功 |

## 默认提取规则

```json
{
  "extract_rules": [
    {
      "field": "goodsName1",
      "match_keywords": ["物品名称", "测试样品", "样品名称", "产品名称"],
      "value_rule": "提取整行内容（去除关键词）"
    },
    {
      "field": "aCompanyName",
      "match_keywords": ["委托单位", "测试单位", "申请单位"],
      "value_rule": "提取冒号后的内容，去除前后空格"
    },
    {
      "field": "issueTime",
      "match_keywords": ["签发日期", "发证日期", "出具日期"],
      "value_rule": "提取冒号后的内容，去除前后空格"
    },
    {
      "field": "reportNo",
      "match_keywords": ["报告编号", "Report No.", "报告号"],
      "value_rule": "提取冒号后或关键词后的内容，去除前后空格"
    }
  ]
}
```

## 使用示例

### 示例 1：基本使用（使用默认规则）

```json
{
  "pdf_path": "D:/reports/test_report.pdf",
  "api_json": {
    "reportNo": "ABC123",
    "goodsName1": "新产品名称",
    "aCompanyName": "新公司名称",
    "issueTime": "2026-01-01"
  }
}
```

### 示例 2：自定义提取规则

```json
{
  "pdf_path": "D:/reports/test_report.pdf",
  "api_json": {
    "reportNo": "ABC123",
    "goodsName1": "新产品名称"
  },
  "extract_rules": [
    {
      "field": "reportNo",
      "match_keywords": ["报告编号", "Report No."],
      "value_rule": "extract_after_keyword"
    },
    {
      "field": "goodsName1",
      "match_keywords": ["产品名称"],
      "value_rule": "extract_after_colon"
    }
  ],
  "output_prefix": "updated_"
}
```

## 工作流程

1. **读取 PDF** - 使用 PyMuPDF 读取 PDF 文件内容
2. **提取数据** - 根据提取规则从 PDF 中提取关键字段
3. **比对差异** - 将提取的 JSON 与 api_json 进行比对
4. **生成差异表** - 输出差异对比结果
5. **修改文件** - 将差异值写入新 PDF 文件
6. **返回结果** - 返回提取数据、差异列表和新文件路径

## 依赖

- Python 3.8+
- PyMuPDF (fitz)
- pypdf

## 注意事项

1. PDF 文件需要有文本层（非扫描图片）
2. 修改后的文件会保留原格式，但字体可能略有差异
3. 如果 PDF 中找不到对应字段，会跳过该字段的修改
4. 新文件保存在原文件同目录下

## 错误处理

- 文件不存在：返回错误信息
- PDF 无法读取：返回错误信息
- 提取失败：返回空提取结果，但仍进行比对
- 无差异：不生成新文件，返回提示

## 版本

- v1.0.0 - 初始版本
