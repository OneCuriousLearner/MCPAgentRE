#!/usr/bin/env python3
"""
TAPD向量化功能快速启动脚本
用于快速初始化和测试向量化功能
"""

import asyncio
import sys
import os

# 添加父目录到Python路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.data_vectorizer import vectorize_tapd_data, search_tapd_data, get_vector_db_info

async def quick_start():
    """快速启动向量化功能"""
    print("🚀 TAPD向量化功能快速启动")
    print("=" * 50)
    
    # 检查数据文件
    data_file = "local_data/msg_from_fetcher.json"
    if not os.path.exists(data_file):
        print(f"❌ 错误: 未找到数据文件 {data_file}")
        print("📋 请先运行 TAPD 数据获取功能")
        return
    
    print("✅ 数据文件检查通过")
    
    # 检查向量数据库状态
    print("\n🔍 检查向量数据库状态...")
    db_info = await get_vector_db_info()
    
    if db_info['status'] == 'not_found':
        print("📦 向量数据库不存在，开始初始化...")
        
        # 执行向量化
        result = await vectorize_tapd_data(chunk_size=10)
        if result['status'] == 'success':
            print("✅ 向量化完成!")
            stats = result['stats']
            print(f"   • 总分片数: {stats['total_chunks']}")
            print(f"   • 总条目数: {stats['total_items']}")
            print(f"   • 向量维度: {stats['vector_dimension']}")
        else:
            print(f"❌ 向量化失败: {result['message']}")
            return
    else:
        print("✅ 向量数据库已就绪")
        if db_info['status'] == 'ready':
            stats = db_info['stats']
            print(f"   • 总分片数: {stats['total_chunks']}")
            print(f"   • 总条目数: {stats['total_items']}")
    
    # 演示搜索功能
    print("\n🔍 演示搜索功能...")
    
    demo_queries = [
        "订单相关功能",
        "页面异常缺陷", 
        "商品评价"
    ]
    
    for query in demo_queries:
        print(f"\n🔎 搜索: '{query}'")
        search_result = await search_tapd_data(query, 2)
        
        if search_result['status'] == 'success':
            results = search_result['results']
            print(f"   找到 {len(results)} 个结果:")
            
            for i, result in enumerate(results, 1):
                score = result['relevance_score']
                chunk_info = result['chunk_info']
                chunk_type = chunk_info['item_type']
                items = result['items']
                
                if items:
                    title = items[0].get('name') or items[0].get('title', '未知')
                    print(f"   {i}. [{chunk_type}] {title} (相关度: {score:.3f})")
                else:
                    print(f"   {i}. [{chunk_type}] (相关度: {score:.3f})")
        else:
            print(f"   ❌ 搜索失败: {search_result['message']}")
    
    print("\n" + "=" * 50)
    print("🎉 快速启动完成!")
    print("\n💡 使用提示:")
    print("   1. 在 Claude Desktop 中测试 MCP 工具:")
    print("      • vectorize_data - 向量化数据")
    print("      • search_data - 智能搜索")
    print("      • get_vector_info - 获取数据库信息")
    print("\n   2. 查看详细文档:")
    print("      knowledge_documents\\TAPD数据向量化功能使用手册.md")

if __name__ == "__main__":
    asyncio.run(quick_start())
