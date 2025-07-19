# TAPD数据预处理工具使用手册

## 工具概述

TAPD数据预处理工具是一个MCP工具，专门用于优化TAPD平台的需求和缺陷数据中的`description`字段。该工具能够清理HTML样式信息、提取有效内容，并通过AI进行内容复述，大幅提升数据质量和后续分析效率。

## 主要功能

### 1. HTML样式清理

- 移除无用的CSS样式属性（margin、padding、color、font-family等）
- 保留有意义的HTML标签和属性（href、src、alt、title）
- 提取纯文本内容，去除冗余信息

### 2. 内容智能复述

- 使用DeepSeek API对清理后的内容进行准确复述
- 保留关键业务信息和技术细节
- 压缩冗余内容，提升信息密度
- 通常可将内容长度压缩60-80%

### 3. 资源链接提取

- 自动识别和提取腾讯文档链接
- 提取TAPD图片路径信息
- 为未来的文档和图片处理预留接口

## 工具列表

### preprocess_tapd_description

主要的数据预处理工具，支持完整的description字段优化。

**参数说明：**

- `data_file_path` (str): 输入数据文件路径，默认"local_data/msg_from_fetcher.json"
- `output_file_path` (str): 输出文件路径，默认"local_data/preprocessed_data.json"
- `use_api` (bool): 是否使用DeepSeek API进行内容复述，默认True
- `process_documents` (bool): 是否处理腾讯文档链接（预留功能），默认False
- `process_images` (bool): 是否处理图片内容（预留功能），默认False

**返回结果：**

```json
{
  "status": "success",
  "message": "数据预处理完成",
  "statistics": {
    "processed_items": 15,
    "api_calls": 12,
    "errors": 0,
    "output_file": "local_data/preprocessed_data.json"
  }
}
```

### preview_tapd_description_cleaning

预览工具，展示清理效果而不实际修改数据。

**参数说明：**

- `data_file_path` (str): 数据文件路径，默认"local_data/msg_from_fetcher.json"
- `item_count` (int): 预览的条目数量，默认3条

**返回结果：**

```json
{
  "status": "success",
  "preview_count": 3,
  "results": [
    {
      "id": "1137857678001000041",
      "type": "story",
      "name": "用户创建的测试需求",
      "original_length": 4753,
      "cleaned_length": 72,
      "original_preview": "原始内容预览...",
      "cleaned_preview": "清理后内容预览...",
      "document_links": [],
      "image_paths": []
    }
  ]
}
```

## 使用流程

### 1. 准备工作

```bash
# 确保已获取TAPD数据
# 在MCP客户端中调用
get_tapd_data()
```

### 2. 预览清理效果

```bash
# 预览3条数据的清理效果
preview_tapd_description_cleaning(item_count=3)
```

### 3. 执行预处理

```bash
# 使用API进行完整预处理
preprocess_tapd_description(use_api=True)

# 或者仅进行样式清理（不使用API）
preprocess_tapd_description(use_api=False)
```

### 4. 后续分析

```bash
# 使用预处理后的数据进行词频分析
analyze_tapd_word_frequency(data_file_path="local_data/preprocessed_data.json")

# 或进行向量化处理
vectorize_data()
```

## 环境配置

### DeepSeek API配置

如果要使用AI复述功能，需要配置DeepSeek API：

```bash
# 设置环境变量
set DS_KEY=your_deepseek_api_key
set DS_EP=https://api.deepseek.com/v1
set DS_MODEL=deepseek-reasoner
```

### 依赖包

工具依赖以下Python包（已包含在项目中）：

- `aiohttp` - 异步HTTP请求
- `beautifulsoup4` - HTML解析
- `python-docx` - 文档处理（预留功能）
- `mcp` - MCP框架

## 处理效果示例

### 原始数据（4753字符）

```html
<div style="word-break: break-word; margin: 0px 0px 1em; padding: 0px; line-height: inherit; color: #182b50; font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif; ...">
  <b style="word-break: break-word; font-weight: bold;">
    <span style="word-break: break-word; line-height: inherit; color: #444444;">
      【用户故事（User Story）】
    </span>
  </b>
  ...大量样式代码...
</div>
```

### 清理后数据（72字符）

```text
【用户故事（User Story）】 作为 我希望 以便 【验收标准】 这是一个测试需求，我会尽可能多使用各类字段，作为后续数据参考。
```

**压缩率：98.5%，内容完整保留！**

## 注意事项

1. **API使用**：使用DeepSeek API会产生费用，建议先预览再决定是否使用
2. **数据备份**：工具会创建新的输出文件，不会覆盖原始数据
3. **处理时间**：大量数据处理可能需要较长时间，特别是使用API时
4. **错误处理**：工具具有错误重试机制，API失败时会使用清理后的内容
5. **预留功能**：文档和图片处理功能已预留接口，等待专人提供具体实现

## 最佳实践

1. **先预览后处理**：始终先使用预览功能了解数据质量
2. **分批处理**：数据量大时考虑分批处理，避免API限制
3. **版本管理**：保留原始数据和预处理后数据的多个版本
4. **质量检查**：处理后检查统计信息，确保数据完整性
5. **配合使用**：与词频分析、向量化等工具配合使用，最大化效果

## 故障排除

### 常见问题

1. **API配置错误**：检查DS_KEY环境变量是否正确设置
2. **数据文件不存在**：确保先调用get_tapd_data获取数据
3. **网络连接问题**：检查网络连接和API端点可访问性
4. **内存不足**：处理大量数据时可能需要增加系统内存

### 错误代码

- `API配置错误`：未设置或错误设置DeepSeek API密钥
- `数据文件不存在`：指定的输入文件路径不存在
- `网络请求失败`：API调用网络错误
- `解析API响应失败`：API返回格式异常

---

*本工具是TAPD平台MCP分析助手项目的重要组成部分，为后续的AI驱动分析奠定基础。*
