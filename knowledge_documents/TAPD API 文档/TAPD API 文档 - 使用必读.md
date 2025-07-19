# 请求地址

`https://api.tapd.cn`

# 参数格式

- 如果是 GET 请求，参数统一放 URL里面，并做 urlencode。比如 order=id%20desc
- 如果是 POST 请求，支持 application/x-www-form-urlencoded Key-Value 格式 或者 application/json json 格式，其中要注意：
    1. 如果POST参数是 json 格式，请求头要加上： `Content-Type: application/json`
    2. 如果POST参数是 Key-Value 格式，请求头注意加上： `Content-Type: application/x-www-form-urlencoded`
    3. 如果是文件上传的接口，请求头注意加上：`Content-Type: multipart/form-data`

# 如何查看项目ID

Tapd.woa.com进入对应项目空间，点击左上角项目名称，查看项目id

# 返回值

返回值支持 json 及 xml格式，默认是 json，可通过在URL中传入 __format参数来控制。返回值结构都由 status、info、data 三个字段组成，具体作用如下表：

|字段|说明|
|---|---|
|status|返回的状态。1 代表请求成功，其它代表失败|
|info|返回说明。如果出错，这里会给出出错信息|
|data|数据部分|

# 认证

面对企业用户，TAPD API 采用 HTTP BASIC AUTH 认证。HTTP BASIC AUTH使用具体可看这里：[API配置指引](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/API%E9%85%8D%E7%BD%AE%E6%8C%87%E5%BC%95.html)

# 帐号申请

目前TAPD API是TAPD的商业化模块，TAPD企业版的公司管理员可以在公司管理>开放集成>API账号管理中申请试用90天。

# 数据查询接口特别说明

## 时间字段

时间类型支持 `<`、`>` 和 `~` 操作符 调用方式为： `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories/count?workspace_id=20003271&created=<2016-01-01'` `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories/count?workspace_id=20003271&created=>2016-01-01'` `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories/count?workspace_id=20003271&created=2016-02-01~2016-02-29'`

要特别注意`等号的位置`和`日期格式`，支持时间段查询如：`created=2024-12-23 14:00:00~2024-12-23 23:59:00`

## 枚举字段

枚举类型支持 `|` 操作符，调用方式为： `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories/count?workspace_id=20003271&status=new|in_progress'`

## 多选字段

需求、缺陷、任务类型对象中，针对多选下拉、复选框类型的多选自定义字段，提供CONTAINS和CONTAIONS_OR语法，支持查询包含部分候选值的对象

### CONTAINS

查询包含所有指定候选值的对象，如找出custom_field_1字段同时选中value1、value2、value3的对象:

`curl –u 'api_user:api_password' 'https://api.tapd.cn/stories?workspace_id=20003271&custom_field_1=CONTAINS<value1|value2|value3>'`

### CONTAINS_OR

查询包含任一指定候选值的对象，如找出custom_field_1字段选中value1或value2或value3的对象:

`curl –u 'api_user:api_password' 'https://api.tapd.cn/stories?workspace_id=20003271&custom_field_1=CONTAINS_OR<value1|value2|value3>'`

## 模糊匹配

就是 `like` 查询，调用方式为： `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories/count?workspace_id=20003271&title=api'`

## 不等于查询

支持 `<>` 查询，调用方式为： `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories.json?workspace_id=20003271&iteration_id=<>1120003271001000275'`

## 多ID查询

使用英文逗号 `,` 分开，调用方式为： `curl –u 'api_user:api_password' 'https://api.tapd.cn/stories?workspace_id=20003271&id=1120003271001000042,1120003271001000043,1120003271001000044'`

## 多人员查询

使用 `|` 表示或，如找出缺陷参与人是 A 或者 B 的： `curl –u 'api_user:api_password' 'https://api.tapd.cn/bugs?workspace_id=20003271&participator=A|B'` 使用 `;` 表示与，如找出缺陷参与人是 A 并且是B 的： `curl –u 'api_user:api_password' 'https://api.tapd.cn/bugs?workspace_id=20003271&participator=A;B'`

## 分页及翻页

获取数据接口，基本默认是只取 30 条数据。可以通过传递 `limit` 参数获取更多，比如：limit=100。但 limit 的上限是 200，超过这个上限的数据，可以传递 `page` 参数来翻页。比如 limit=10&page=2，则是数据每页10条数据，取第二页的。数据的总条目数，一般可以通过对应的 count 计数接口来获取。

## Python 语言调用 TAPD API

使用 Python 语言调用 TAPD API，推荐使用 requests 库。 requests 安装文档：https://requests.readthedocs.io/en/latest/user/install/#install requests 快速上手文档：https://requests.readthedocs.io/en/latest/user/quickstart/ 下面是 Python 环境下使用 requests 来请求 TAPD API 的例子：

```
import requests
r = requests.get('[api地址]/quickstart/testauth', auth=('api_user', 'api_password'))
ret = r.text # 获取接口返回结果
print(ret) # Python 3
print ret # Python 2
```