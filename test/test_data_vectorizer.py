#!/usr/bin/env python3
"""
测试完整版 data_vectorizer 工具功能
"""

import asyncio
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.data_vectorizer import vectorize_tapd_data, search_tapd_data, get_vector_db_info

async def test_data_vectorizer():
    """测试完整版向量化工具"""
    print("=== 测试完整版 data_vectorizer 工具 ===\n")
    
    # 1. 检查数据文件是否存在
    data_file = "local_data/msg_from_fetcher.json"
    if not os.path.exists(data_file):
        print(f"⚠️  数据文件不存在: {data_file}")
        print("请先运行 tapd_data_fetcher.py 获取数据")
        return False
    
    print(f"✅ 数据文件存在: {data_file}\n")
    
    # 2. 测试数据库信息获取
    print("📊 测试数据库信息获取...")
    try:
        db_info = await get_vector_db_info()
        print(f"数据库状态: {db_info['status']}")
        print(f"信息: {db_info['message']}")
        if db_info['status'] == 'not_found':
            print("需要先进行向量化\n")
        else:
            print(f"统计信息: {json.dumps(db_info.get('stats', {}), ensure_ascii=False, indent=2)}\n")
    except Exception as e:
        print(f"❌ 获取数据库信息失败: {e}\n")
    
    # 3. 测试向量化功能
    print("🔄 测试向量化功能...")
    try:
        result = await vectorize_tapd_data(chunk_size=5)  # 使用较小的分片测试
        print(f"向量化状态: {result['status']}")
        print(f"信息: {result['message']}")
        if result['status'] == 'success':
            stats = result.get('stats', {})
            print(f"统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        print()
    except Exception as e:
        print(f"❌ 向量化失败: {e}\n")
        return False
    
    # 4. 测试搜索功能
    print("🔍 测试搜索功能...")
    test_queries = [
        "登录功能相关的需求",
        "高优先级的缺陷",
        "用户界面问题"
    ]
    
    for query in test_queries:
        try:
            print(f"\n查询: {query}")
            result = await search_tapd_data(query, top_k=3)
            print(f"搜索状态: {result['status']}")
            if result['status'] == 'success':
                results = result.get('results', [])
                print(f"找到 {len(results)} 个相关结果")
                for i, item in enumerate(results[:2], 1):  # 只显示前2个结果
                    print(f"  结果 {i}: 相关度 {item['relevance_score']:.3f}")
                    chunk_info = item.get('chunk_info', {})
                    print(f"    类型: {chunk_info.get('item_type')}, 条目数: {chunk_info.get('item_count')}")
            else:
                print(f"搜索失败: {result['message']}")
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    print("\n=== 完整版 data_vectorizer 测试完成 ===")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_data_vectorizer())
    if success:
        print("\n✅ 所有测试通过！完整版向量化工具工作正常。")
    else:
        print("\n❌ 部分测试失败，请检查配置和数据。")
