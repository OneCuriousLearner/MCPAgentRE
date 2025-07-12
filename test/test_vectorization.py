#!/usr/bin/env python3
"""测试向量化功能集成"""

import asyncio
import json
import sys
import os

# 添加父目录到Python路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tapd_mcp_server import (
    vectorize_data, 
    search_data, 
    get_vector_info
)

async def test_vectorization():
    """测试向量化功能"""
    print("=== 测试向量化功能 ===")
    
    # 测试获取数据库信息
    print("1. 检查向量数据库状态...")
    info_result = await get_vector_info()
    print(f"数据库状态: {json.loads(info_result)['status']}")
    
    # 测试搜索功能
    print("\n2. 测试搜索功能...")
    search_result = await search_data("订单相关功能", 3)
    result_data = json.loads(search_result)
    print(f"搜索状态: {result_data['status']}")
    if result_data['status'] == 'success':
        print(f"找到结果数: {len(result_data['results'])}")
        for i, result in enumerate(result_data['results']):
            print(f"  结果{i+1}: 相关度={result['relevance_score']:.3f}, "
                  f"类型={result['chunk_type']}, "
                  f"条目数={result['item_count']}")
    
    print("\n3. 测试另一个搜索...")
    search_result2 = await search_data("页面异常缺陷", 2)
    result_data2 = json.loads(search_result2)
    print(f"搜索状态: {result_data2['status']}")
    if result_data2['status'] == 'success':
        print(f"找到结果数: {len(result_data2['results'])}")
        for i, result in enumerate(result_data2['results']):
            print(f"  结果{i+1}: 相关度={result['relevance_score']:.3f}, "
                  f"类型={result['chunk_type']}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_vectorization())
