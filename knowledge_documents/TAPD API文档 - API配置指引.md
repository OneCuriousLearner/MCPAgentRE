# 概述

在 HTTP 中，基础认证是一种以HTTP请求头部为载体来传递账号和口令信息的规范。

用户在向 TAPD API 发送请求时，需要依照 HTTP 基础认证的规范，在`HTTP请求头`中带上API账号和口令信息，

TAPD 会根据 HTTP 请求头中的API账号和口令校验请求是否合法。

在发送之前是以用户名追加一个冒号然后串接上口令，并将得出的结果字符串再用`Base64`算法编码。

例如，提供的用户名是`Aladdin`、口令是`open sesame`，则拼接后的结果就是`Aladdin:open sesame`，

然后再将其用`Base64`编码，得到`QWxhZGRpbjpvcGVuIHNlc2FtZQ==`。

最终将`Base64`编码的字符串发送出去，由接收者解码得到一个由冒号分隔的用户名和口令的字符串。

# 参数说明

目前帐号申请成功后公司管理员可以在`公司管理`->`开放平台` 里面可以看到。

|参数|说明|
|---|---|
|api_user|API 帐号|
|api_password|API 口令|

# 过程

## HTTP Header 信息

以下是使用HTTP基本认证方法调用REST API时，部分HTTP头部信息：

```
GET /quickstart/testauth HTTP/1.1
Host: api.tapd.cn
Authorization: Basic [auth_key]
```

Authorization 部分用于传递身份验证信息。其中，`[auth_key]`字段是`BASE64`编码后的

`api_user:password` 串。

## HTTP 基础认证 HTTP Header 拼接示例

当调用 RESTful API 时，将 `BASE64` 编码的 `api_user:password` 替换 `[auth_key]` 部分，举例如下：

1. `api_user:api_password` 通过 `BASE64` 编码为：`YXBpX3VzZXI6YXBpX3Bhc3N3b3Jk`
    
2. 写入 HTTP 头部的 Authorization 信息为：
    
`Authorization: Basic YXBpX3VzZXI6YXBpX3Bhc3N3b3Jk`

# 常用语言调用示例

## curl 方式调用

如果用户是通过curl方式调用，请求时只需简单把API账号和口令作为调用参数提供即可。使用 curl 的调用例子如下：

`curl -u 'api_user:api_password' 'https://api.tapd.cn/quickstart/testauth'`

## PHP 调用

```
<?php
$url = "https://api.tapd.cn/quickstart/testauth";
$curl = curl_init();
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl, CURLOPT_USERPWD, "api_user:api_password"); # 设置 API 帐号密码
curl_setopt($curl, CURLOPT_URL, $url);
$ret = curl_exec($curl); # 获取接口返回结果
curl_close($curl);
var_dump($ret); # 输出结果
```

示例返回结果

```
{"status":1,"data":{"api_user":"api_user","api_password":"api.password","request_ip":"172.8.8.8"},"info":"success"}
```

## [#](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/API%E9%85%8D%E7%BD%AE%E6%8C%87%E5%BC%95.html#python-%E8%B0%83%E7%94%A8)Python 调用

使用 Python 语言调用 TAPD API，推荐使用 `requests` 库，[requests安装文档 (opens new window)](https://requests.readthedocs.io/en/latest/user/install/#install)及 [requests快速上手文档 (opens new window)](https://requests.readthedocs.io/en/latest/user/quickstart/)，下面是 Python 环境下使用 requests 来请求 TAPD API 的例子：

```
import requests
r = requests.get('https://api.tapd.cn/quickstart/testauth', auth=('api_user', 'api_password'))
ret = r.text # 获取接口返回结果
print(ret) # Python 3
print ret # Python 2
```

示例返回：

```
{"status":1,"data":{"api_user":"api_user","api_password":"api.password","request_ip":"172.8.8.8"},"info":"success"}
```
