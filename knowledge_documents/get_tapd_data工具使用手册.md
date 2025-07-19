# get_tapd_data 工具使用手册

## 工具概述

`get_tapd_data` 是 TAPD MCP 服务器中新增的数据获取和本地存储工具，它集成了需求和缺陷数据的完整获取流程，并将数据保存到本地文件中以供后续分析使用。

## 功能特性

- **完整数据获取**: 一次性获取 TAPD 项目的所有需求和缺陷数据
- **本地数据存储**: 自动将数据保存到 `local_data/msg_from_fetcher.json` 文件
- **数量统计**: 返回获取到的需求和缺陷数量统计信息
- **错误处理**: 提供详细的错误信息和解决建议
- **目录自动创建**: 自动创建 `local_data` 目录（如不存在）

## 使用方法

### 在 MCP 客户端中调用

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_tapd_data"
  }
}
```

### 返回数据格式

#### 成功响应

```json
{
  "status": "success",
  "message": "数据已成功保存至local_data/msg_from_fetcher.json文件",
  "statistics": {
    "stories_count": 125,
    "bugs_count": 89,
    "total_count": 214
  },
  "file_path": "local_data/msg_from_fetcher.json"
}
```

#### 错误响应

```json
{
  "status": "error",
  "message": "获取和保存TAPD数据失败：API认证失败",
  "suggestion": "请检查API密钥配置和网络连接"
}
```

## 本地数据文件格式

保存的数据文件 `local_data/msg_from_fetcher.json` 包含以下结构：

```json
{
  "stories": [
    {
      "id": "1001",
      "name": "用户登录功能",
      "status": "已完成",
      "priority": "高",
      "creator": "张三",
      "created": "2025-01-01 10:00:00",
      // ...其他需求字段
    }
  ],
  "bugs": [
    {
      "id": "2001",
      "title": "登录页面样式错乱",
      "priority": "中",
      "severity": "一般",
      "status": "已解决",
      "reporter": "李四",
      "created": "2025-01-02 14:30:00",
      // ...其他缺陷字段
    }
  ]
}
```

## 配置要求

在使用此工具前，请确保以下配置正确：

1. **API 配置文件**: 项目根目录下的 `api.txt` 文件包含有效的 TAPD API 配置
2. **网络连接**: 确保服务器能够访问 TAPD API
3. **文件权限**: 确保程序有权限在 `local_data` 目录下创建和写入文件

## 使用场景

### 1. 初始化数据

首次使用项目时，运行此工具获取最新的 TAPD 数据：

```text
调用 get_tapd_data() → 获取完整数据集 → 本地文件准备就绪
```

### 2. 定期数据更新

定期运行此工具以保持本地数据与 TAPD 平台同步：

```text
定时任务 → 调用 get_tapd_data() → 更新本地缓存 → 继续分析
```

### 3. 离线分析准备

在进行大量数据分析前，先获取最新数据：

```text
get_tapd_data() → 向量化数据 → 智能搜索 → 生成报告
```

## 与其他工具的协作

### 配合向量化工具使用

```text
1. get_tapd_data()           # 获取最新数据
2. vectorize_data()          # 向量化数据
3. search_data()             # 智能搜索
```

### 配合生成工具使用

```text
1. get_tapd_data()           # 获取真实数据
2. generate_overview()       # 生成数据概览
3. build_quality_report()    # 生成质量报告
```

## 注意事项

1. **API 频率限制**: TAPD API 可能有调用频率限制，建议合理安排调用时间
2. **数据量考虑**: 大型项目的数据量可能较大，请确保有足够的磁盘空间
3. **数据隐私**: 本地存储的数据包含项目敏感信息，请妥善保管
4. **版本兼容**: 确保本地数据格式与其他工具兼容

## 故障排除

### 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| API认证失败 | API密钥配置错误 | 检查 `api.txt` 文件配置 |
| 网络连接超时 | 网络问题 | 检查网络连接和防火墙设置 |
| 文件写入失败 | 权限不足 | 确保程序有写入 `local_data` 目录的权限 |
| 数据格式错误 | API响应异常 | 检查 TAPD 服务状态，重试操作 |

## 开发信息

- **实现文件**: `tapd_mcp_server.py`
- **依赖模块**: `tapd_data_fetcher.py`
- **测试文件**: `test/test_get_tapd_data.py`
- **数据存储**: `local_data/msg_from_fetcher.json`

## 更新历史

- **v1.0** (2025-07-14): 初始版本，基于 `tapd_data_fetcher.py` 的主函数逻辑实现
