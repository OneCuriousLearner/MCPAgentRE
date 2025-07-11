import aiohttp
import json
import os

# 从配置文件读取API配置
def load_api_config():
    config_file = './api.txt'
    config = {}
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"配置文件 {config_file} 不存在")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('//'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")  # 移除可能的引号
                    config[key] = value
        
        # 验证必需的配置项
        required_keys = ['API_USER', 'API_PASSWORD', 'WORKSPACE_ID']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件中缺少必需的配置项: {key}")
        
        return config
    except Exception as e:
        raise Exception(f"读取配置文件失败: {e}")

# 加载配置
try:
    config = load_api_config()
    API_USER = config['API_USER']
    API_PASSWORD = config['API_PASSWORD']
    WORKSPACE_ID = config['WORKSPACE_ID']
    print(f"成功加载配置: 用户={API_USER}, 工作区={WORKSPACE_ID}")
except Exception as e:
    print(f"配置加载失败: {e}")
    raise

# 获取需求数据（支持分页）的函数
async def get_story_msg():
    url = 'https://api.tapd.cn/stories'  # TAPD需求API地址
    stories_list = []  # 存储所有需求数据的列表
    page = 1  # 初始页码
    while True:
        params = {
            'workspace_id': WORKSPACE_ID,
            # 若需要获取所有字段，请注释下面的fields参数
            # 'fields': 'id,workitem_type_id,name,description,workspace_id,creator,created,modified,status,step,owner,cc,begin,due,size,priority,developer,iteration_id,test_focus,type,source,module,version,completed,category_id,path,parent_id,children_id,ancestor_id,level,business_value,effort,effort_completed,exceed,remain,release_id,bug_id,templated_id,created_from,feature,label,progress,is_archived,tech_risk,flows,priority_label',
            'page': page
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=aiohttp.BasicAuth(API_USER, API_PASSWORD), params=params) as response:
                if response.status != 200:
                    print(f'获取需求第{page}页失败: {await response.text()}')
                    break
                result = await response.json()
                if result.get('status') != 1:
                    print(f'获取需求第{page}页失败: {result.get("info")}')
                    break
                current_page_data = result.get('data', [])
                if not current_page_data:  # 无更多数据时结束循环
                    break
                for story in current_page_data:  # 遍历当前页的每条需求数据，提取Story字段
                    story_data = story.get('Story', {})
                    if not story_data.get('id'):  # 检查需求id是否为空
                        print(f'发现需求数据id为空（第{page}页），结束获取')
                        return stories_list  # 遇到空值立即终止并返回已有数据
                    # 清洗空数据字段（None/空字符串）
                    cleaned_story = {k: v for k, v in story_data.items() if v not in (None, "")}
                    stories_list.append(cleaned_story)
        page += 1  # 页码递增
    print(f'需求数据获取完成，共获取{len(stories_list)}条')
    return stories_list

# 获取缺陷数据（支持分页）的函数
async def get_bug_msg():
    url = 'https://api.tapd.cn/bugs'  # TAPD缺陷API地址
    bugs_list = []  # 存储所有缺陷数据的列表
    page = 1  # 初始页码
    while True:
        params = {
            'workspace_id': WORKSPACE_ID,
            # 若需要获取所有字段，请注释下面的fields参数
            # 'fields': 'id,title,description,priority,severity,module,status,reporter,created,bugtype,resolved,closed,modified,lastmodify,auditer,de,fixer,version_test,version_report,version_close,version_fix,baseline_find,baseline_join,baseline_close,baseline_test,sourcephase,te,current_owner,iteration_id,resolution,source,originphase,confirmer,milestone,participator,closer,platform,os,testtype,testphase,frequency,cc,regression_number,flows,feature,testmode,estimate,issue_id,created_from,release_id,verify_time,reject_time,reopen_time,audit_time,suspend_time,due,begin,deadline,in_progress_time,assigned_time,template_id,story_id,label,size,effort,effort_completed,exceed,remain,secret_root_id,priority_label,workspace_id',
            'page': page
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=aiohttp.BasicAuth(API_USER, API_PASSWORD), params=params) as response:
                if response.status != 200:
                    print(f'获取缺陷第{page}页失败: {await response.text()}')
                    break
                result = await response.json()
                if result.get('status') != 1:
                    print(f'获取缺陷第{page}页失败: {result.get("info")}')
                    break
                current_page_data = result.get('data', [])
                if not current_page_data:  # 无更多数据时结束循环
                    break
                for bug in current_page_data:  # 遍历当前页的每条缺陷数据，提取Bug字段
                    bug_data = bug.get('Bug', {})
                    if not bug_data.get('title'):  # 检查缺陷title是否为空
                        print(f'发现缺陷数据title为空（第{page}页），结束获取')
                        return bugs_list  # 遇到空值立即终止并返回已有数据
                    # 清洗空数据字段（None/空字符串）
                    cleaned_bug = {k: v for k, v in bug_data.items() if v not in (None, "")}
                    bugs_list.append(cleaned_bug)
        page += 1  # 页码递增
    print(f'缺陷数据获取完成，共获取{len(bugs_list)}条')
    return bugs_list

if __name__ == '__main__':
    import asyncio
    print('===== 开始获取需求数据 =====')
    stories_data = asyncio.run(get_story_msg())
    print('===== 开始获取缺陷数据 =====')
    bugs_data = asyncio.run(get_bug_msg())
    
    data_to_save = {
        'stories': stories_data,
        'bugs': bugs_data
    }
    
    os.makedirs('local_data', exist_ok=True)
    with open(os.path.join('local_data', 'msg_from_fetcher.json'), 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

    print('数据已成功保存至local_data/msg_from_fetcher.json文件。')