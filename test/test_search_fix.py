"""
测试simple_search_data功能的脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_tools.simple_vectorizer import simple_search_data

async def test_search():
    """测试搜索功能"""
    print("开始测试搜索功能...")
    
    # 测试查询
    query = "高优先级的开发任务"
    top_k = 5
    
    print(f"查询: {query}")
    print(f"返回数量: {top_k}")
    print("-" * 50)
    
    try:
        result = await simple_search_data(query, top_k)
        print("搜索结果:")
        print(f"状态: {result.get('status')}")
        print(f"消息: {result.get('message')}")
        
        if result.get('status') == 'success':
            results = result.get('results', [])
            print(f"找到 {len(results)} 个结果:")
            for i, item in enumerate(results, 1):
                print(f"\n结果 {i}:")
                print(f"  相关度: {item.get('relevance_score', 0):.4f}")
                print(f"  类型: {item.get('chunk_type')}")
                print(f"  条目数: {item.get('item_count')}")
                
                items = item.get('items', [])
                print(f"  包含项目数: {len(items)}")
                for j, subitem in enumerate(items[:2], 1):  # 只显示前2个
                    name = subitem.get('name') or subitem.get('title', '未知')
                    priority = subitem.get('priority', '未知')
                    print(f"    {j}. {name} (优先级: {priority})")
        else:
            print("搜索失败!")
            if 'error_detail' in result:
                print("错误详情:")
                print(result['error_detail'])
                
    except Exception as e:
        print(f"测试过程出现异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
