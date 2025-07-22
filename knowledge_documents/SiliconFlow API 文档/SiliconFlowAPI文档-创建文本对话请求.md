# 创建文本对话请求

Creates a model response for the given chat conversation.

## POST

```url
https://api.siliconflow.cn/v1/chat/completions
```

### cURL

```curl
curl --request POST \
  --url https://api.siliconflow.cn/v1/chat/completions \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "model": "Qwen/QwQ-32B",
  "messages": [
    {
      "role": "user",
      "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
    }
  ],
  "stream": false,
  "max_tokens": 512,
  "enable_thinking": false,
  "thinking_budget": 4096,
  "min_p": 0.05,
  "stop": null,
  "temperature": 0.7,
  "top_p": 0.7,
  "top_k": 50,
  "frequency_penalty": 0.5,
  "n": 1,
  "response_format": {
    "type": "text"
  },
  "tools": [
    {
      "type": "function",
      "function": {
        "description": "<string>",
        "name": "<string>",
        "parameters": {},
        "strict": false
      }
    }
  ]
}'
```

### Python

```python
import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "Qwen/QwQ-32B",
    "messages": [
        {
            "role": "user",
            "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
        }
    ],
    "stream": False,
    "max_tokens": 512,
    "enable_thinking": False,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "stop": None,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "response_format": {"type": "text"},
    "tools": [
        {
            "type": "function",
            "function": {
                "description": "<string>",
                "name": "<string>",
                "parameters": {},
                "strict": False
            }
        }
    ]
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)
```

### JavaScript

```JavaScript
const options = {
  method: 'POST',
  headers: {Authorization: 'Bearer <token>', 'Content-Type': 'application/json'},
  body: '{"model":"Qwen/QwQ-32B","messages":[{"role":"user","content":"What opportunities and challenges will the Chinese large model industry face in 2025?"}],"stream":false,"max_tokens":512,"enable_thinking":false,"thinking_budget":4096,"min_p":0.05,"stop":null,"temperature":0.7,"top_p":0.7,"top_k":50,"frequency_penalty":0.5,"n":1,"response_format":{"type":"text"},"tools":[{"type":"function","function":{"description":"<string>","name":"<string>","parameters":{},"strict":false}}]}'
};

fetch('https://api.siliconflow.cn/v1/chat/completions', options)
  .then(response => response.json())
  .then(response => console.log(response))
  .catch(err => console.error(err));
```

## Authorization

### Authorization

`string` `header` `required`
Use the following format for authentication: `Bearerg <your api key>`

## Body

application/json

### LLM

#### model

`enum<string>` `default:Qwen/QwQ-32B` `required`

Corresponding Model Name. To better enhance service quality, we will make periodic changes to the models provided by this service, including but not limited to model on/offlining and adjustments to model service capabilities. We will notify you of such changes through appropriate means such as announcements or message pushes where feasible.

Available options:

* baidu/ERNIE-4.5-300B-A47B
* moonshotai/Kimi-K2-Instruct
* ascend-tribe/pangu-pro-moe
* tencent/Hunyuan-A13B-Instruct
* MiniMaxAI/MiniMax-M1-80k
* Tongyi-Zhiwen/QwenLong-L1-32B
* Qwen/Qwen3-30B-A3B
* Qwen/Qwen3-32B
* Qwen/Qwen3-14B
* Qwen/Qwen3-8B
* Qwen/Qwen3-235B-A22B
* THUDM/GLM-Z1-32B-0414
* THUDM/GLM-4-32B-0414
* THUDM/GLM-Z1-Rumination-32B-0414
* THUDM/GLM-4-9B-0414
* THUDM/GLM-4-9B-0414
* Qwen/QwQ-32B
* Pro/deepseek-ai/DeepSeek-R1
* Pro/deepseek-ai/DeepSeek-V3
* deepseek-ai/DeepSeek-R1
* deepseek-ai/DeepSeek-V3
* deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
* deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
* deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
* deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
* Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
* deepseek-ai/DeepSeek-V2.5
* Qwen/Qwen2.5-72B-Instruct-128K
* Qwen/Qwen2.5-72B-Instruct
* Qwen/Qwen2.5-32B-Instruct
* Qwen/Qwen2.5-14B-Instruct
* Qwen/Qwen2.5-7B-Instruct
* Qwen/Qwen2.5-Coder-32B-Instruct
* Qwen/Qwen2.5-Coder-7B-Instruct
* Qwen/Qwen2-7B-Instruct
* TeleAI/TeleChat2
* THUDM/glm-4-9b-chat
* Vendor-A/Qwen/Qwen2.5-72B-Instruct
* internlm/internlm2_5-7b-chat
* Pro/Qwen/Qwen2.5-7B-Instruct
* Pro/Qwen/Qwen2-7B-Instruct
* Pro/THUDM/glm-4-9b-chat

**Example:**
"Qwen/QwQ-32B"

#### messages

`object[]` `required`
A list of messages comprising the conversation so far.
Required array length: `1 - 10` elements

##### role

`enum<string>` `default:user` `required`
The role of the messages author. Choice between: system, user, or assistant.
Available options: `user`, `assistant`, `system`

**Example:**
"user"

##### content

`string` `default:What opportunities and challenges will the Chinese large model industry face in 2025?` `required`
The contents of the message.

**Example:**
"What opportunities and challenges will the Chinese large model industry face in 2025?"
​
#### stream

`boolean` `default:true`
If set, tokens are returned as Server-Sent Events as they are made available. Stream terminates with `data: [DONE]`

**Example:**
false

#### max_tokens

`integer` `default:512`
The maximum number of tokens to generate.
Required range: `1 <= x <= 16384`

**Example:**
512

#### enable_thinking

`boolean` `default:true`
Switches between thinking and non-thinking modes. Default is True. This field only applies to Qwen3.

**Example:**
false

#### thinking_budget

`integer` `default:4096`
Maximum number of tokens for chain-of-thought output. This field applies to all Reasoning models.
Required range: `128 <= x <= 32768`

**Example:**
4096

#### min_p

`number` `default:0.05`
Dynamic filtering threshold that adapts based on token probabilities.This field only applies to Qwen3.
Required range: `0 <= x <= 1`

**Example:**
0.05

#### stop

`string | null` or `string[] | null`
Up to 4 sequences where the API will stop generating further tokens. The returned text will not contain the stop sequence.

**Example:**
null

#### temperature

`number` `default:0.7`
Determines the degree of randomness in the response.

**Example:**
0.7

#### top_p

`number` `default:0.7`
The `top_p` (nucleus) parameter is used to dynamically adjust the number of choices for each predicted token based on the cumulative probabilities.

**Example:**
0.7

#### top_k

`number` `default:50`

**Example:**
50

#### frequency_penalty

`number` `default:0.5`

**Example:**
0.5

#### n

`integer` `default:1`
Number of generations to return

**Example:**
1

#### response_format

`object`
An object specifying the format that the model must output.

##### response_format.type

`string`
The type of the response format.

**Example:**
"text"

#### tools

`object[]`
A list of tools the model may call. Currently, only functions are supported as a tool. Use this to provide a list of functions the model may generate JSON inputs for. A max of 128 functions are supported.

##### type

`enum<string>` `required`
The type of the tool. Currently, only `function` is supported.

**Available options:**
function

##### function

`object` `required`

###### function.name

`string` `required`
The name of the function to be called. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 64.

###### function.description

`string`
A description of what the function does, used by the model to choose when and how to call the function.

###### function.parameters

`object`
The parameters the functions accepts, described as a JSON Schema object. See the [guide](https://docs.siliconflow.cn/guides/function_calling) for examples, and the [JSON Schema reference](https://json-schema.org/understanding-json-schema/) for documentation about the format.
Omitting `parameters` defines a function with an empty parameter list.

###### function.strict

`boolean | null` `default:false`
Whether to enable strict schema adherence when generating the function call. If set to true, the model will follow the exact schema defined in the `parameters` field. Only a subset of JSON Schema is supported when `strict` is `true`. Learn more about Structured Outputs in the [function calling guide](https://docs.siliconflow.cn/cn/api-reference/chat-completions/docs/guides/function-calling).

---

## Response

### 200

```json
{
  "id": "<string>",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<string>",
        "reasoning_content": "<string>",
        "tool_calls": [
          {
            "id": "<string>",
            "type": "function",
            "function": {
              "name": "<string>",
              "arguments": "<string>"
            }
          }
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 123,
    "completion_tokens": 123,
    "total_tokens": 123
  },
  "created": 123,
  "model": "<string>",
  "object": "chat.completion"
}
```

### 400

```json
{
  "code": 20012,
  "message": "<string>",
  "data": "<string>"
}
```

### 401

```json
"Invalid token"
```

### 404

```json
"404 page not found"
```

### 429

```json
{
  "message": "Request was rejected due to rate limiting. If you want more, please contact contact@siliconflow.cn. Details:TPM limit reached.",
  "data": "<string>"
}
```

### 503

```json
{
  "code": 50505,
  "message": "Model service overloaded. Please try again later.",
  "data": "<string>"
}
```

### 504

```json
"<string>"
```
