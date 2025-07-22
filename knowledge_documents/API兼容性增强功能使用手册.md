# API兼容性增强功能使用手册

## 概述

本项目的 `common_utils.py` 中的 `APIManager` 类现已支持两种大型语言模型API：

1. **DeepSeek API** - 默认API提供商
2. **SiliconFlow API** - 新增的API提供商

该增强功能使得项目能够灵活地在不同的API提供商之间切换，提高了系统的可靠性和可扩展性。

## 环境变量配置

### DeepSeek API配置

```bash
# DeepSeek API密钥（必需）
DS_KEY=your_deepseek_api_key

# DeepSeek API端点（可选，默认值）
DS_EP=https://api.deepseek.com/v1

# DeepSeek 默认模型（可选，默认值）
DS_MODEL=deepseek-chat
```

### SiliconFlow API配置

```bash
# SiliconFlow API密钥（使用SiliconFlow时必需）
SF_KEY=your_siliconflow_api_key
```

## 使用方法

### 1. 默认使用 DeepSeek API

```python
from mcp_tools.common_utils import get_api_manager
import aiohttp

async def example():
    api_manager = get_api_manager()
    
    async with aiohttp.ClientSession() as session:
        # 使用默认配置（DeepSeek API）
        result = await api_manager.call_llm(
            prompt="你好",
            session=session,
            max_tokens=100
        )
```

### 2. 显式指定 DeepSeek API

```python
async def example():
    api_manager = get_api_manager()
    
    async with aiohttp.ClientSession() as session:
        result = await api_manager.call_llm(
            prompt="你好",
            session=session,
            model="deepseek-chat",  # 或 "deepseek-reasoner"
            endpoint="https://api.deepseek.com/v1",
            max_tokens=100
        )
```

### 3. 使用 SiliconFlow API

```python
async def example():
    api_manager = get_api_manager()
    
    async with aiohttp.ClientSession() as session:
        result = await api_manager.call_llm(
            prompt="你好",
            session=session,
            model="moonshotai/Kimi-K2-Instruct",  # SiliconFlow模型
            endpoint="https://api.siliconflow.cn/v1",
            max_tokens=100
        )
```

### 4. 使用 SiliconFlow 默认模型

```python
async def example():
    api_manager = get_api_manager()
    
    async with aiohttp.ClientSession() as session:
        # 只指定endpoint，会自动使用默认的 moonshotai/Kimi-K2-Instruct 模型
        result = await api_manager.call_llm(
            prompt="你好",
            session=session,
            endpoint="https://api.siliconflow.cn/v1",
            max_tokens=100
        )
```

## API自动检测机制

系统会根据 `endpoint` 参数自动检测使用哪种API：

- 如果 `endpoint` 包含 "siliconflow"，则使用 SiliconFlow API配置
- 否则使用 DeepSeek API配置

## 支持的模型

### DeepSeek 模型

- `deepseek-chat` - 通用对话模型（默认）
- `deepseek-reasoner` - 推理模型，支持 reasoning_content 字段

### SiliconFlow 模型

- `moonshotai/Kimi-K2-Instruct` - 默认模型
- `Qwen/QwQ-32B` - 通义千问推理模型
- `deepseek-ai/DeepSeek-V3` - DeepSeek V3模型
- `THUDM/GLM-4-9B-0414` - 智谱GLM模型
- 其他支持的模型请参考 SiliconFlow API 文档

## 错误处理增强

### 针对不同API的专门错误处理

#### DeepSeek API错误（根据官方文档）

- `400` - 格式错误：请求体格式错误
- `401` - 认证失败：API key错误，检查 DS_KEY
- `402` - 余额不足：账号余额不足，需要充值
- `422` - 参数错误：请求体参数错误  
- `429` - 请求速率达到上限：TPM或RPM达到上限
- `500` - 服务器故障：服务器内部故障，等待后重试
- `503` - 服务器繁忙：服务器负载过高，稍后重试

#### SiliconFlow API错误（根据官方文档）

- `400` - 请求参数错误：请求体参数格式错误
- `401` - 认证失败：Invalid token，检查 SF_KEY
- `404` - 页面未找到：可能是模型不存在或API路径错误  
- `429` - 请求速率达到上限：TPM limit reached，需要合理规划请求速率
- `503` - 服务过载：模型服务过载，请稍后重试
- `504` - 网关超时：请求超时，请稍后重试

### 错误示例

```python
try:
    result = await api_manager.call_llm(...)
except RuntimeError as e:
    if "API认证失败" in str(e):
        print("请检查API密钥配置")
    elif "请求过于频繁" in str(e):
        print("请降低请求频率")
    else:
        print(f"其他错误: {e}")
```

## 测试用例评估器更新

`test_case_evaluator.py` 已更新为默认使用 SiliconFlow 的 `moonshotai/Kimi-K2-Instruct` 模型：

```python
# 原来的调用
result = await self.api_manager.call_llm(
    prompt=final_prompt,
    session=session,
    model="deepseek-reasoner",
    endpoint="https://api.deepseek.com/v1",
    max_tokens=dynamic_response_tokens
)

# 更新后的调用
result = await self.api_manager.call_llm(
    prompt=final_prompt,
    session=session,
    model="moonshotai/Kimi-K2-Instruct",
    endpoint="https://api.siliconflow.cn/v1",
    max_tokens=dynamic_response_tokens
)
```

## 测试方法

使用提供的测试脚本验证API兼容性：

```bash
cd "d:\Coder\Gits\MiniProject\MCPAgentRE"
uv run test\test_api_compatibility.py
```

## 注意事项

1. **API密钥安全**: 请确保API密钥的安全，不要在代码中硬编码
2. **网络连接**: 确保能够访问对应的API端点
3. **模型限制**: 不同API提供商的模型参数和限制可能不同
4. **成本考虑**: 不同API提供商的收费标准可能不同，请根据需要选择

## 兼容性说明

- 完全向后兼容，现有代码无需修改即可继续使用 DeepSeek API
- 新功能通过参数选择性启用，不会影响现有功能
- 支持在运行时动态切换不同的API提供商
