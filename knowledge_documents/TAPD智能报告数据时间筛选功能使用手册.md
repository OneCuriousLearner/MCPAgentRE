# TAPD智能报告数据时间筛选功能使用手册

## 功能概述

TAPD MCP服务器现已支持按时间范围筛选需求和缺陷数据。通过 `generate_tapd_overview` 工具的 `since` 和 `until` 参数，用户可以精确获取指定时间段内的数据分析报告。

## 新增功能

### 1. 时间筛选函数

在 `tapd_data_fetcher.py` 中新增了以下函数：

- `filter_data_by_time()`: 核心时间筛选函数
- `get_local_story_msg_filtered()`: 本地需求数据时间筛选
- `get_local_bug_msg_filtered()`: 本地缺陷数据时间筛选  
- `get_story_msg_filtered()`: API需求数据时间筛选
- `get_bug_msg_filtered()`: API缺陷数据时间筛选

### 2. 筛选逻辑

- **筛选字段**: 默认使用 `created` 字段（创建时间）进行筛选
- **时间格式**: 支持 `YYYY-MM-DD HH:MM:SS` 和 `YYYY-MM-DD` 两种格式
- **筛选范围**: 包含起始日期和结束日期（闭区间）
- **错误处理**: 时间格式无法解析的数据会被跳过，不会中断整个筛选过程

## 使用方法

### 1. 通过MCP工具使用

```python
# 生成2025年5-6月的TAPD数据概览
result = await generate_tapd_overview(
    since="2025-05-01",
    until="2025-06-30", 
    use_local_data=True
)
```

### 2. 参数说明

- `since` (str): 开始时间，格式为 YYYY-MM-DD，默认 "2025-01-01"
- `until` (str): 结束时间，格式为 YYYY-MM-DD，默认为当前系统日期
- `use_local_data` (bool): 是否使用本地数据，默认True

### 3. 数据源选择

- **本地数据** (`use_local_data=True`): 从 `local_data/msg_from_fetcher.json` 筛选数据
- **API数据** (`use_local_data=False`): 从TAPD API获取最新数据后筛选

## 筛选逻辑详解

### 1. 时间字段优先级

对于需求(stories)数据，筛选字段为：
- `created`: 创建时间（主要筛选字段）

对于缺陷(bugs)数据，筛选字段为：
- `created`: 创建时间（主要筛选字段）

### 2. 时间解析

系统支持以下时间格式：
- `2025-05-26 19:56:44`（完整时间戳）
- `2025-05-26`（仅日期）

解析时会自动提取日期部分进行比较。

### 3. 筛选范围

- **包含边界**: 筛选结果包含 `since` 和 `until` 指定的日期
- **日期比较**: 只比较日期部分，忽略具体时间

## 示例用法

### 1. 查看当年所有数据

```python
result = await generate_tapd_overview(
    since="2025-01-01",
    until="2025-12-31"
)
```

### 2. 查看特定月份数据

```python
# 查看7月数据
result = await generate_tapd_overview(
    since="2025-07-01", 
    until="2025-07-31"
)
```

### 3. 查看最近一周数据

```python
from datetime import datetime, timedelta

today = datetime.now()
week_ago = today - timedelta(days=7)

result = await generate_tapd_overview(
    since=week_ago.strftime("%Y-%m-%d"),
    until=today.strftime("%Y-%m-%d")
)
```

## 测试验证

使用 `test/test_time_filter.py` 可以测试时间筛选功能：

```bash
uv run test/test_time_filter.py
```

该测试会验证：
- 不同时间范围的筛选结果
- 筛选数据的准确性
- 边界条件的处理

## 注意事项

1. **数据格式**: 确保数据中的时间字段格式正确
2. **时区处理**: 当前不处理时区转换，按原始时间进行筛选
3. **性能考虑**: 大量数据筛选时可能需要一定时间
4. **错误恢复**: 时间解析失败的条目会被跳过，不影响其他数据的筛选

## 更新说明

- **版本**: 2025-07-14
- **更新内容**: 新增时间筛选功能，支持 since/until 参数精确筛选数据
- **兼容性**: 向下兼容，不影响现有功能的使用
