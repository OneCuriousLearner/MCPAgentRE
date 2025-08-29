#!/usr/bin/env python3
"""
测试TAPD数据精确搜索工具
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_tools.data_precise_searcher import TAPDDataPreciseSearcher

def test_precise_searcher():
    """测试精确搜索器的各种功能"""
    print("=== 测试TAPD数据精确搜索工具 ===")
    
    searcher = TAPDDataPreciseSearcher()
    
    # 测试1: ID精确搜索
    print("\n1. 测试ID精确搜索")
    try:
        results = searcher.search_by_field("1148591566001000001", "id")
        print(f"   搜索ID '1148591566001000001' 找到 {results['summary']['total_items']} 个结果")
        if results['summary']['total_items'] > 0:
            print(f"   匹配的需求数: {results['summary']['total_stories']}")
            print(f"   匹配的缺陷数: {results['summary']['total_bugs']}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试2: 创建者搜索
    print("\n2. 测试创建者搜索")
    try:
        results = searcher.search_by_field("张凯晨", "creator")
        print(f"   搜索创建者 '张凯晨' 找到 {results['summary']['total_items']} 个结果")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试3: 模糊搜索
    print("\n3. 测试模糊搜索")
    try:
        results = searcher.search_by_field("登录", "name", exact_match=False)
        print(f"   模糊搜索标题包含 '登录' 找到 {results['summary']['total_items']} 个结果")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试4: 高优先级搜索
    print("\n4. 测试高优先级搜索")
    try:
        results = searcher.search_by_priority("high")
        print(f"   搜索高优先级项目找到 {results['summary']['total_items']} 个结果")
        print(f"   高优先级需求: {results['summary']['total_stories']}")
        print(f"   高优先级缺陷: {results['summary']['total_bugs']}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试5: 统计信息
    print("\n5. 测试统计信息")
    try:
        stats = searcher.get_statistics()
        if 'stories' in stats:
            print(f"   需求总数: {stats['stories']['total_count']}")
            print(f"   高优先级需求: {stats['stories']['high_priority_items']}")
        if 'bugs' in stats:
            print(f"   缺陷总数: {stats['bugs']['total_count']}")
            print(f"   高优先级缺陷: {stats['bugs']['high_priority_items']}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试6: 高级搜索
    print("\n6. 测试高级搜索")
    try:
        search_params = {
            'text_search': '前端',
            'search_fields': ['name', 'description'],
            'data_type': 'both',
            'priority_filter': 'high',
            'exact_match': False,
            'case_sensitive': False,
            'sort_by': 'created',
            'sort_order': 'desc',
            'limit': 5
        }
        results = searcher.advanced_search(search_params)
        print(f"   高级搜索找到 {results['summary']['total_items']} 个结果（限制5个）")
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_precise_searcher()
