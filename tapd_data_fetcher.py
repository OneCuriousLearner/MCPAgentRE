import aiohttp
import json
import os
import sys
from datetime import datetime

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
    print(f"成功加载配置: 用户={API_USER}, 工作区={WORKSPACE_ID}", file=sys.stderr)
except Exception as e:
    print(f"配置加载失败: {e}", file=sys.stderr)
    raise

# 获取需求数据（支持分页）的函数
async def get_story_msg(clean_empty_fields: bool = True):
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
                    # 根据参数决定是否清洗空数据字段（None/空字符串）
                    if clean_empty_fields:
                        processed_story = {k: v for k, v in story_data.items() if v not in (None, "")}
                    else:
                        processed_story = story_data
                    stories_list.append(processed_story)
        page += 1  # 页码递增
    print(f'需求数据获取完成，共获取{len(stories_list)}条')
    return stories_list

# 获取缺陷数据（支持分页）的函数
async def get_bug_msg(clean_empty_fields: bool = True):
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
                    # 根据参数决定是否清洗空数据字段（None/空字符串）
                    if clean_empty_fields:
                        processed_bug = {k: v for k, v in bug_data.items() if v not in (None, "")}
                    else:
                        processed_bug = bug_data
                    bugs_list.append(processed_bug)
        page += 1  # 页码递增
    print(f'缺陷数据获取完成，共获取{len(bugs_list)}条')
    return bugs_list

# 从本地文件读取数据的函数
async def get_local_story_msg():
    """从本地文件读取需求数据"""
    try:
        local_file_path = os.path.join('local_data', 'msg_from_fetcher.json')
        if not os.path.exists(local_file_path):
            print('本地数据文件不存在，请先运行数据获取或生成假数据')
            return []
        
        with open(local_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # 如果是旧格式（直接的数组），筛选出story类型的数据
            stories = [item for item in data if item.get('type') == 'story']
        elif isinstance(data, dict) and 'stories' in data:
            # 如果是新格式（包含stories和bugs键的字典）
            stories = data['stories']
        else:
            # 如果格式不识别，返回空列表
            stories = []
        
        print(f'从本地文件加载需求数据，共{len(stories)}条')
        return stories
    except Exception as e:
        print(f'读取本地需求数据失败: {str(e)}')
        return []

async def get_local_bug_msg():
    """从本地文件读取缺陷数据"""
    try:
        local_file_path = os.path.join('local_data', 'msg_from_fetcher.json')
        if not os.path.exists(local_file_path):
            print('本地数据文件不存在，请先运行数据获取或生成假数据')
            return []
        
        with open(local_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # 如果是旧格式（直接的数组），筛选出bug类型的数据
            bugs = [item for item in data if item.get('type') == 'bug']
        elif isinstance(data, dict) and 'bugs' in data:
            # 如果是新格式（包含stories和bugs键的字典）
            bugs = data['bugs']
        else:
            # 如果格式不识别，返回空列表
            bugs = []
        
        print(f'从本地文件加载缺陷数据，共{len(bugs)}条')
        return bugs
    except Exception as e:
        print(f'读取本地缺陷数据失败: {str(e)}')
        return []

def filter_data_by_time(data_list, since_str, until_str, time_field='created'):
    """
    根据时间范围筛选数据
    
    参数:
        data_list: 数据列表
        since_str: 开始时间字符串，格式为 YYYY-MM-DD
        until_str: 结束时间字符串，格式为 YYYY-MM-DD
        time_field: 用于筛选的时间字段名，默认为 'created'
    
    返回:
        筛选后的数据列表
    """
    if not data_list:
        return []
    
    try:
        # 解析时间字符串
        since_date = datetime.strptime(since_str, "%Y-%m-%d")
        until_date = datetime.strptime(until_str, "%Y-%m-%d")
        
        filtered_data = []
        for item in data_list:
            # 检查时间字段是否存在
            if time_field not in item:
                continue
            
            # 解析数据中的时间
            item_time_str = item[time_field]
            if not item_time_str:
                continue
            
            try:
                # 处理TAPD时间格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD
                if ' ' in item_time_str:
                    item_time = datetime.strptime(item_time_str.split(' ')[0], "%Y-%m-%d")
                else:
                    item_time = datetime.strptime(item_time_str, "%Y-%m-%d")
                
                # 检查是否在时间范围内
                if since_date <= item_time <= until_date:
                    filtered_data.append(item)
                    
            except ValueError:
                # 如果时间格式无法解析，跳过这条数据
                continue
        
        return filtered_data
        
    except ValueError as e:
        print(f'时间格式解析错误: {str(e)}')
        return data_list  # 如果时间解析失败，返回原始数据

async def get_local_story_msg_filtered(since_str=None, until_str=None):
    """从本地文件读取需求数据并按时间筛选"""
    try:
        # 先获取所有数据
        all_stories = await get_local_story_msg()
        
        # 如果没有指定时间范围，返回所有数据
        if not since_str or not until_str:
            return all_stories
        
        # 按创建时间筛选数据
        filtered_stories = filter_data_by_time(all_stories, since_str, until_str, 'created')
        
        print(f'按时间筛选需求数据：{since_str} 到 {until_str}，筛选后共{len(filtered_stories)}条')
        return filtered_stories
        
    except Exception as e:
        print(f'筛选本地需求数据失败: {str(e)}')
        return []

async def get_local_bug_msg_filtered(since_str=None, until_str=None):
    """从本地文件读取缺陷数据并按时间筛选"""
    try:
        # 先获取所有数据
        all_bugs = await get_local_bug_msg()
        
        # 如果没有指定时间范围，返回所有数据
        if not since_str or not until_str:
            return all_bugs
        
        # 按创建时间筛选数据
        filtered_bugs = filter_data_by_time(all_bugs, since_str, until_str, 'created')
        
        print(f'按时间筛选缺陷数据：{since_str} 到 {until_str}，筛选后共{len(filtered_bugs)}条')
        return filtered_bugs
        
    except Exception as e:
        print(f'筛选本地缺陷数据失败: {str(e)}')
        return []

async def get_story_msg_filtered(since_str=None, until_str=None):
    """从TAPD API获取需求数据并按时间筛选"""
    try:
        # 先获取所有数据
        all_stories = await get_story_msg()
        
        # 如果没有指定时间范围，返回所有数据
        if not since_str or not until_str:
            return all_stories
        
        # 按创建时间筛选数据
        filtered_stories = filter_data_by_time(all_stories, since_str, until_str, 'created')
        
        print(f'按时间筛选API需求数据：{since_str} 到 {until_str}，筛选后共{len(filtered_stories)}条')
        return filtered_stories
        
    except Exception as e:
        print(f'筛选API需求数据失败: {str(e)}')
        return []

async def get_bug_msg_filtered(since_str=None, until_str=None):
    """从TAPD API获取缺陷数据并按时间筛选"""
    try:
        # 先获取所有数据
        all_bugs = await get_bug_msg()
        
        # 如果没有指定时间范围，返回所有数据
        if not since_str or not until_str:
            return all_bugs
        
        # 按创建时间筛选数据
        filtered_bugs = filter_data_by_time(all_bugs, since_str, until_str, 'created')
        
        print(f'按时间筛选API缺陷数据：{since_str} 到 {until_str}，筛选后共{len(filtered_bugs)}条')
        return filtered_bugs
        
    except Exception as e:
        print(f'筛选API缺陷数据失败: {str(e)}')
        return []

if __name__ == '__main__':
    import asyncio
    print('===== 开始获取需求数据 =====')
    stories_data = asyncio.run(get_story_msg(clean_empty_fields=True))
    print('===== 开始获取缺陷数据 =====')
    bugs_data = asyncio.run(get_bug_msg(clean_empty_fields=True))

    data_to_save = {
        'stories': stories_data,
        'bugs': bugs_data
    }
    
    os.makedirs('local_data', exist_ok=True)
    with open(os.path.join('local_data', 'msg_from_fetcher.json'), 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

    print('数据已成功保存至local_data/msg_from_fetcher.json文件。')