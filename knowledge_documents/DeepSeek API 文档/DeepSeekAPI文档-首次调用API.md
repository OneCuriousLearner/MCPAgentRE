# DeepSeekAPI文档-首次调用API

DeepSeek API 使用与 OpenAI 兼容的 API 格式，通过修改配置，您可以使用 OpenAI SDK 来访问 DeepSeek API，或使用与 OpenAI API 兼容的软件。

|PARAM|VALUE|
|---|---|
|base_url *|`https://api.deepseek.com`|
|api_key|apply for an [API key](https://platform.deepseek.com/api_keys)|

* 出于与 OpenAI 兼容考虑，您也可以将 `base_url` 设置为 `https://api.deepseek.com/v1` 来使用，但注意，此处 `v1` 与模型版本无关。
* **`deepseek-chat`模型指向`DeepSeek-V3-0324`**，通过指定 `model='deepseek-chat'` 调用。
* **`deepseek-reasoner`模型指向`DeepSeek-R1-0528`**，通过指定 `model='deepseek-reasoner'` 调用。

## 调用对话 API

在创建 API key 之后，你可以使用以下样例脚本的来访问 DeepSeek API。样例为非流式输出，您可以将 stream 设置为 true 来使用流式输出。

### curl 示例

```curl
curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <DeepSeek API Key>" \
  -d '{
        "model": "deepseek-chat",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Hello!"}
        ],
        "stream": false
      }'
```

### Python 示例

```python
# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)
```

### Node.js 示例

```javascript
// Please install OpenAI SDK first: `npm install openai`

import OpenAI from "openai";

const openai = new OpenAI({
        baseURL: 'https://api.deepseek.com',
        apiKey: '<DeepSeek API Key>'
});

async function main() {
  const completion = await openai.chat.completions.create({
    messages: [{ role: "system", content: "You are a helpful assistant." }],
    model: "deepseek-chat",
  });

  console.log(completion.choices[0].message.content);
}

main();
```

## Temperature 设置

`temperature` 参数默认为 1.0。

* 我们建议您根据如下表格，按使用场景设置 `temperature`。

|场景|温度|
|---|---|
|代码生成/数学解题|0.0|
|数据抽取/分析|1.0|
|通用对话|1.3|
|翻译|1.3|
|创意类写作/诗歌创作|1.5|

## 限速

DeepSeek API **不限制用户并发量**，我们会尽力保证您所有请求的服务质量。

但请注意，当我们的服务器承受高流量压力时，您的请求发出后，可能需要等待一段时间才能获取服务器的响应。在这段时间里，您的 HTTP 请求会保持连接，并持续收到如下格式的返回内容：

* 非流式请求：持续返回空行
* 流式请求：持续返回 SSE keep-alive 注释（`: keep-alive`）

这些内容不影响 OpenAI SDK 对响应的 JSON body 的解析。如果您在自己解析 HTTP 响应，请注意处理这些空行或注释。

如果 30 分钟后，请求仍未完成，服务器将关闭连接。

## 错误码

您在调用 DeepSeek API 时，可能会遇到以下错误。这里列出了相关错误的原因及其解决方法。

|错误码|描述|
|---|---|
|400 - 格式错误|**原因**：请求体格式错误  <br>**解决方法**：请根据错误信息提示修改请求体|
|401 - 认证失败|**原因**：API key 错误，认证失败  <br>**解决方法**：请检查您的 API key 是否正确，如没有 API key，请先 [创建 API key](https://platform.deepseek.com/api_keys)|
|402 - 余额不足|**原因**：账号余额不足  <br>**解决方法**：请确认账户余额，并前往 [充值](https://platform.deepseek.com//top_up) 页面进行充值|
|422 - 参数错误|**原因**：请求体参数错误  <br>**解决方法**：请根据错误信息提示修改相关参数|
|429 - 请求速率达到上限|**原因**：请求速率（TPM 或 RPM）达到上限  <br>**解决方法**：请合理规划您的请求速率。|
|500 - 服务器故障|**原因**：服务器内部故障  <br>**解决方法**：请等待后重试。若问题一直存在，请联系我们解决|
|503 - 服务器繁忙|**原因**：服务器负载过高  <br>**解决方法**：请稍后重试您的请求|
