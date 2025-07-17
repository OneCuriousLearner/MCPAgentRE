# DeepSeek API 环境变量配置指南

## API密钥配置

为了使用智能摘要功能，您需要配置DeepSeek API密钥。

### 1. 获取API密钥

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册账号并登录
3. 在控制台中创建API密钥
4. 复制您的API密钥

### 2. 设置环境变量

#### Windows PowerShell

```powershell
# 临时设置（仅当前会话有效）
$env:DS_KEY = "your-api-key-here"

# 永久设置（推荐）
[Environment]::SetEnvironmentVariable("DS_KEY", "your-api-key-here", "User")
```

#### Windows CMD

```cmd
# 临时设置
set DS_KEY=your-api-key-here

# 永久设置
setx DS_KEY "your-api-key-here"
```

#### Linux/macOS

```bash
# 临时设置
export DS_KEY="your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export DS_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 可选配置

您还可以配置以下可选环境变量：

```powershell
# API端点（默认: https://api.deepseek.com/v1）
$env:DS_EP = "https://api.deepseek.com/v1"

# 模型名称（默认: deepseek-chat）
$env:DS_MODEL = "deepseek-chat"
```

### 4. 验证配置

您可以使用以下命令验证环境变量是否设置成功：

#### Windows PowerShell

```powershell
echo $env:DS_KEY
```

#### Linux/macOS

```bash
echo $DS_KEY
```

### 5. 常见问题

**Q: 为什么我设置了环境变量但MCP工具仍然报错？**

A: 请确保：

1. 环境变量名称正确（`DS_KEY`）
2. 重启您的编辑器和MCP客户端
3. API密钥没有前后空格
4. API密钥有效且有足够的配额

**Q: 如何使用其他兼容的API服务？**

A: 您可以设置不同的端点和模型：

```powershell
# 使用OpenAI兼容的API
$env:DS_EP = "https://your-api-endpoint.com/v1"
$env:DS_MODEL = "gpt-3.5-turbo"
$env:DS_KEY = "your-openai-compatible-key"
```

**Q: 如何在不同项目中使用不同的API密钥？**

A: 您可以在项目根目录创建`.env`文件：

```text
DS_KEY=your-project-specific-key
DS_EP=https://api.deepseek.com/v1
DS_MODEL=deepseek-chat
```

### 6. 安全注意事项

- 不要将API密钥提交到版本控制系统
- 定期轮换API密钥
- 监控API使用量和费用
- 确保API密钥权限最小化

### 7. 测试配置

设置完成后，您可以运行以下测试：

```powershell
# 进入项目目录
cd "d:\Coder\Gits\MiniProject\MCPAgentRE"

# 测试API配置
python test_api_key_fix.py
```

如果配置正确，您应该看到智能摘要功能正常工作。
