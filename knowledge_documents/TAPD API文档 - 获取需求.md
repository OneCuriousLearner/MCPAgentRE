# 说明

批量查询所有符合条件的需求（story）单列表（分页显示，默认一页30条） 支持通过ID查询单个需求（story）单的信息，结果以列表形式返回

# url

`https://api.tapd.cn/stories`

# 支持格式

JSON/XML（默认JSON格式）

# HTTP请求方式

GET

# 请求数限制

默认返回 30 条。可通过传 limit 参数设置，最大取 200。也可以传 page 参数翻页

# 请求参数

|字段名|必选|类型及范围|说明|特殊规则|
|---|---|---|---|---|
|id|否|integer|ID|支持多ID查询|
|name|否|string|标题|支持模糊匹配|
|priority|否|string|优先级。为了兼容自定义优先级，`请使用 priority_label 字段`，详情参考：[如何兼容自定义优先级](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/subject/custom_priority/)||
|priority_label|否|string|优先级。推荐使用这个字段||
|business_value|否|integer|业务价值||
|status|否|string|状态|支持枚举查询|
|v_status|否|string|状态(支持传入中文状态名称)||
|with_v_status|否|string|值=1可以返回中文状态||
|label|否|string|标签查询|支持枚举查询|
|workitem_type_id|否|string|需求类别ID|支持枚举查询|
|version|否|string|版本||
|module|否|string|模块||
|feature|否|string|特性||
|test_focus|否|string|测试重点||
|size|否|integer|规模||
|owner|否|string|处理人|支持模糊匹配|
|cc|否|string|抄送人|支持模糊匹配|
|creator|否|string|创建人|支持多人员查询|
|developer|否|string|开发人员||
|begin|否|date|预计开始|支持时间查询|
|due|否|date|预计结束|支持时间查询|
|created|否|datetime|创建时间|支持时间查询|
|modified|否|datetime|最后修改时间|支持时间查询|
|completed|否|datetime|完成时间|支持时间查询|
|iteration_id|否|string|迭代ID|支持不等于查询或枚举查询|
|effort|否|string|预估工时||
|effort_completed|否|string|完成工时||
|remain|否|float|剩余工时||
|exceed|否|float|超出工时||
|category_id|否|integer|需求分类|支持枚举查询|
|release_id|否|integer|发布计划||
|source|否|string|需求来源||
|type|否|string|需求类型||
|ancestor_id|否|integer|祖先需求，查询指定需求下所有子需求||
|parent_id|否|integer|父需求||
|children_id|否|string|子需求|为空查询传：丨|
|description|否|string|详细描述|支持模糊匹配|
|workspace_id|`是`|integer|项目ID||
|custom_field_*|否|string或者integer|自定义字段参数，具体字段名通过接口 [获取需求自定义字段配置](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/api_reference/story/get_story_custom_fields_settings.html) 获取|支持枚举查询|
|custom_plan_field_*|否|string或者integer|自定义计划应用参数，具体字段名通过接口 [获取自定义计划应用](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/api_reference/iteration/get_plan_apps.html) 获取||
|limit|否|integer|设置返回数量限制，默认为30||
|page|否|integer|返回当前数量限制下第N页的数据，默认为1（第一页）||
|order|否|string|排序规则，规则：字段名 ASC或者DESC，然后 urlencode|如按创建时间逆序：order=created%20desc|
|fields|否|string|设置获取的字段，多个字段间以','逗号隔开||

# 调用示例及返回结果

## 获取项目下需求

### curl 使用 Basic Auth 鉴权调用示例

`curl -u 'api_user:api_password' 'https://api.tapd.cn/stories?workspace_id=10158231'`

### 返回结果

```
{
    "status": 1,
    "data": [
        {
            "Story": {
                "id": "1110104801855935679",
                "workitem_type_id": "1010104801000022091",
                "name": "oyctest20190919AB",
                "description": null,
                "workspace_id": "10104801",
                "creator": null,
                "created": "2019-09-16 20:46:38",
                "modified": "2019-09-17 11:15:38",
                "status": null,
                "owner": null,
                "cc": null,
                "begin": null,
                "due": null,
                "size": null,
                "priority": "",
                "developer": null,
                "iteration_id": "0",
                "test_focus": null,
                "type": null,
                "source": null,
                "module": null,
                "version": "",
                "completed": null,
                "category_id": "-1",
                "path": null,
                "parent_id": "0",
                "children_id": null,
                "ancestor_id": null,
                "business_value": null,
                "effort": "0",
                "effort_completed": "0",
                "exceed": "0",
                "remain": "0",
                "release_id": "0",
				"label": "设计阻塞|重点关注",
                "custom_field_one": null,
                "custom_field_two": null,
                "custom_field_three": null,
                "custom_field_four": null,
                "custom_field_five": null,
                "custom_field_six": null,
                "custom_field_seven": null,
                "custom_field_eight": null,
                "custom_field_9": null,
                "custom_field_10": null,
                "custom_field_11": null,
                "custom_field_12": null,
                "custom_field_13": null,
                "custom_field_14": null,
                "custom_field_15": null,
                "custom_field_16": null,
                "custom_field_17": null,
                "custom_field_18": null,
                "custom_field_19": null,
                "custom_field_20": null,
                "custom_field_21": null,
                "custom_field_22": null,
                "custom_field_23": null,
                "custom_field_24": null,
                "custom_field_25": null,
                "custom_field_26": null,
                "custom_field_27": null,
                "custom_field_28": null,
                "custom_field_29": null,
                "custom_field_30": null,
                "custom_field_31": null,
                "custom_field_32": null,
                "custom_field_33": null,
                "custom_field_34": null,
                "custom_field_35": null,
                "custom_field_36": null,
                "custom_field_37": null,
                "custom_field_38": null,
                "custom_field_39": null,
                "custom_field_40": null,
                "custom_field_41": null,
                "custom_field_42": null,
                "custom_field_43": null,
                "custom_field_44": null,
                "custom_field_45": null,
                "custom_field_46": null,
                "custom_field_47": null,
                "custom_field_48": null,
                "custom_field_49": null,
                "custom_field_50": null,
                "custom_field_51": null,
                "custom_field_52": null,
                "custom_field_53": null,
                "custom_field_54": null,
                "custom_field_55": null,
                "custom_field_56": null,
                "custom_field_57": null,
                "custom_field_58": null,
                "custom_field_59": null,
                "custom_field_60": null,
                "custom_field_61": null,
                "custom_field_62": null,
                "custom_field_63": null,
                "custom_field_64": null,
                "custom_field_65": null,
                "custom_field_66": null,
                "custom_field_67": null,
                "custom_field_68": null,
                "custom_field_69": null,
                "custom_field_70": null,
                "custom_field_71": null,
                "custom_field_72": null,
                "custom_field_73": null,
                "custom_field_74": null,
                "custom_field_75": null,
                "custom_field_76": null,
                "custom_field_77": null,
                "custom_field_78": null,
                "custom_field_79": null,
                "custom_field_80": null,
                "custom_field_81": null,
                "custom_field_82": null,
                "custom_field_83": null,
                "custom_field_84": null,
                "custom_field_85": null,
                "custom_field_86": null,
                "custom_field_87": null,
                "custom_field_88": null,
                "custom_field_89": null,
                "custom_field_90": null,
                "custom_field_91": null,
                "custom_field_92": null,
                "custom_field_93": null,
                "custom_field_94": null,
                "custom_field_95": null,
                "custom_field_96": null,
                "custom_field_97": null,
                "custom_field_98": null,
                "custom_field_99": null,
                "custom_field_100": null
            }
        }
    ],
    "info": "success"
}
```

## 获取需求ID为 1010104801869398419 的需求 id,name,status,owner 字段

### [#](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/api_reference/story/get_stories.html#curl-%E4%BD%BF%E7%94%A8-basic-auth-%E9%89%B4%E6%9D%83%E8%B0%83%E7%94%A8%E7%A4%BA%E4%BE%8B-2)curl 使用 Basic Auth 鉴权调用示例

`curl -u 'api_user:api_password' 'https://api.tapd.cn/stories?workspace_id=10104801&id=1010104801869398419&fields=id,name,status,owner'`

### [#](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/api_reference/story/get_stories.html#%E8%BF%94%E5%9B%9E%E7%BB%93%E6%9E%9C-2)返回结果

```
{
    "status": 1,
    "data": [
        {
            "Story": {
                "id": "1010104801869398419",
                "name": "abbbb",
                "status": "planning",
                "owner": ""
            }
        }
    ],
    "info": "success"
}
```

# 需求字段说明

## 需求重要字段说明

|字段|说明|
|---|---|
|id|ID|
|name|标题|
|priority|优先级|
|priority_label|优先级|
|business_value|业务价值|
|status|状态|
|version|版本|
|module|模块|
|feature|特性|
|test_focus|测试重点|
|size|规模|
|owner|处理人|
|cc|抄送人|
|creator|创建人|
|developer|开发人员|
|begin|预计开始|
|due|预计结束|
|created|创建时间|
|modified|最后修改时间|
|completed|完成时间|
|iteration_id|迭代ID|
|templated_id|模板ID|
|effort|预估工时|
|effort_completed|完成工时|
|remain|剩余工时|
|exceed|超出工时|
|category_id|需求分类(取 -1 时，为未分类)|
|release_id|发布计划|
|is_archived|是否归档|
|source|来源|
|type|类型|
|parent_id|父需求|
|children_id|子需求|
|ancestor_id|祖先ID|
|description|详细描述|
|workspace_id|项目ID|
|workitem_type_id|需求类别|
|confidential|是否保密|
|created_from|需求创建来源（为空时代表web创建）|
|level|层级|
|bug_id|缺陷ID（当缺陷转需求时才会有值）|

## 需求优先级(priority)取值字段说明

为了兼容自定义优先级，`请使用 priority_label 字段`，详情参考：[如何兼容自定义优先级](https://open.tapd.cn/document/api-doc/API%E6%96%87%E6%A1%A3/subject/custom_priority/) 。`下面取值将不再使用`。

|取值|字面值|
|---|---|
|4|High|
|3|Middle|
|2|Low|
|1|Nice To Have|
