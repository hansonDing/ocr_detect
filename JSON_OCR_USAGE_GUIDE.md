# JSON格式OCR结果处理使用指南

本指南介绍如何使用OCR系统处理JSON格式的OCR识别结果，并将提取的信息存储到数据库中。

## 功能概述

系统现在支持处理包含`natural_text`字段的JSON格式OCR结果，能够自动提取客户信息、交易数据等关键信息并存储到数据库中。

## 支持的数据格式

### 1. JSON格式OCR结果

```json
{
  "primary_language": "en",
  "is_rotation_valid": true,
  "rotation_correction": 0,
  "is_table": true,
  "is_diagram": false,
  "natural_text": "| Field Name       | Value                  |\n|------------------|------------------------|\n| Customer Name    | Zhang Wei              |\n| Customer ID      | 1058901                |\n| Transaction ID   | 5000067890             |\n| Transaction Amount | 8888.88              |\n| Payment Date     | 2025-01-15             |\n| Document Timestamp | 2025-01-15 14:30:25   |\n| Customer Country | CN                     |"
}
```

### 2. 完整OCR结果文本格式

```
Recognition Time: 2025-01-15T16:45:30.123456
Original Filename: client_data_4.pdf - Page 1
Recognition Model: OCR API
Processing Status: Success

Recognition Result:
{"primary_language":"en","is_rotation_valid":true,"rotation_correction":0,"is_table":true,"is_diagram":false,"natural_text":"| Field Name       | Value                  |\n|------------------|------------------------|\n| Customer Name    | Sun Hong               |\n| Customer ID      | 1057805                |\n| Transaction ID   | 5000056583             |\n| Transaction Amount | 6651.00              |\n| Payment Date     | 2025-11-21             |\n| Document Timestamp | 2025-07-08 18:50:52   |\n| Customer Country | HK                     |"}
```

## 使用方法

### 方法1: 使用命令行脚本

#### 1.1 处理单个OCR结果文件

```bash
python parse_ocr_result.py
```

脚本会自动处理当前目录下的`ocr_test.txt`文件。

#### 1.2 批量处理OCR结果文件

```bash
python batch_process_ocr_results.py
```

选择处理模式：
- 1: 处理当前目录中的所有OCR结果文件
- 2: 处理指定文件
- 3: 处理指定目录

### 方法2: 使用API接口

#### 2.1 API端点

```
POST /api/process-json-ocr
```

#### 2.2 请求参数

**方式1: 直接提交JSON结果**

```json
{
  "json_result": "{\"primary_language\":\"en\",\"natural_text\":\"| Field Name | Value |\\n| Customer Name | Zhang Wei |\\n| Customer ID | 1058901 |\"}",
  "filename": "document.pdf",
  "file_path": "/path/to/document.pdf",
  "model_used": "OCR API"
}
```

**方式2: 提交完整OCR结果文本**

```json
{
  "ocr_text": "Recognition Time: 2025-01-15T16:45:30.123456\nOriginal Filename: document.pdf\nRecognition Model: OCR API\nProcessing Status: Success\n\nRecognition Result:\n{\"natural_text\":\"...\"}\n",
  "filename": "document.pdf",
  "file_path": "/path/to/document.pdf"
}
```

#### 2.3 响应格式

**成功响应:**

```json
{
  "success": true,
  "message": "OCR result processed and saved successfully",
  "record_id": 26,
  "extracted_info": {
    "customer_name": "Zhang Wei",
    "customer_id": "1058901",
    "transaction_id": "5000067890",
    "transaction_amount": "8888.88",
    "payment_date": "2025-01-15",
    "document_timestamp": "2025-01-15 14:30:25",
    "customer_country": "CN"
  },
  "formatted_info": "客户姓名: Zhang Wei\n客户ID: 1058901\n交易ID: 5000067890\n交易金额: 8888.88\n支付日期: 2025-01-15\n文档时间戳: 2025-01-15 14:30:25\n客户国家: CN"
}
```

**错误响应:**

```json
{
  "success": false,
  "message": "Either json_result or ocr_text must be provided",
  "details": {}
}
```

### 方法3: 使用Python函数

```python
from json_ocr_processor import process_json_ocr_result, process_ocr_result_text

# 处理JSON格式结果
json_str = '{"natural_text":"| Customer Name | Zhang Wei |"}'
success, record_id, info = process_json_ocr_result(
    json_str=json_str,
    filename='document.pdf',
    file_path='/path/to/document.pdf'
)

# 处理完整OCR结果文本
ocr_text = "Recognition Time: ...\nRecognition Result:\n{...}"
success, record_id, info = process_ocr_result_text(
    ocr_result_text=ocr_text,
    filename='document.pdf'
)
```

## 支持的字段提取

系统能够从`natural_text`中的表格数据提取以下信息：

- **客户姓名** (Customer Name)
- **客户ID** (Customer ID)
- **交易ID** (Transaction ID)
- **交易金额** (Transaction Amount)
- **支付日期** (Payment Date)
- **文档时间戳** (Document Timestamp)
- **客户国家** (Customer Country)

## 数据库存储

提取的信息会自动存储到`ocr_records`表中，包含以下字段：

- `id`: 记录ID（自增）
- `filename`: 文件名
- `file_path`: 文件路径
- `processing_time`: 处理时间
- `customer_name`: 客户姓名
- `customer_id`: 客户ID
- `transaction_id`: 交易ID
- `transaction_amount`: 交易金额
- `payment_date`: 支付日期
- `document_timestamp`: 文档时间戳
- `customer_country`: 客户国家
- `raw_ocr_text`: 原始OCR文本
- `model_used`: 使用的OCR模型
- `extraction_confidence`: 提取置信度

## 测试示例

运行测试脚本验证功能：

```bash
python test_json_api.py
```

该脚本会测试：
1. JSON格式OCR结果处理
2. 完整OCR结果文本处理
3. 错误处理
4. 数据库记录查询

## 注意事项

1. **数据格式**: 确保`natural_text`包含表格格式的数据
2. **字段匹配**: 系统使用模式匹配提取信息，字段名称应与预定义模式匹配
3. **编码**: 确保文本使用UTF-8编码
4. **API限制**: API请求大小限制为5MB
5. **数据库**: 确保数据库已正确初始化

## 故障排除

### 常见问题

1. **提取不到信息**
   - 检查`natural_text`格式是否正确
   - 确认字段名称是否匹配
   - 查看原始OCR文本内容

2. **API调用失败**
   - 确认服务器正在运行
   - 检查请求格式是否正确
   - 查看服务器日志

3. **数据库错误**
   - 确认数据库文件存在
   - 检查数据库表结构
   - 验证数据库权限

### 调试方法

```python
# 查看提取的信息
from database import extract_key_information

natural_text = "| Customer Name | Zhang Wei |"
info = extract_key_information(natural_text)
print(info)

# 查看数据库记录
from database import get_all_records

records = get_all_records()
for record in records[-3:]:
    print(f"ID: {record['id']}, Customer: {record['customer_name']}")
```

## 更新日志

- **v1.0** (2025-01-08): 初始版本，支持JSON格式OCR结果处理
- 添加API端点 `/api/process-json-ocr`
- 添加命令行处理脚本
- 添加批量处理功能
- 支持完整OCR结果文本解析