"""
测试MCP服务器中的simple search data工具
"""
import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入并测试MCP工具
from tapd_mcp_server import mcp

async def test_mcp_search():
    """测试MCP服务器中的搜索工具"""
    print("开始测试MCP服务器中的simple search data工具...")
    print("-" * 50)
    
    # 直接测试调用
    try:
        # 通过MCP调用工具
        result = await mcp.call_tool(
            'simple_search_data',
            {
                'query': '高优先级的开发任务',
                'top_k': 5
            }
        )
        
        print("MCP工具调用结果:")
        # 结果是JSON字符串，需要解析
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
                print(f"状态: {parsed_result.get('status')}")
                print(f"消息: {parsed_result.get('message')}")
                
                if parsed_result.get('status') == 'success':
                    results = parsed_result.get('results', [])
                    print(f"找到 {len(results)} 个结果")
                    for i, item in enumerate(results[:2], 1):  # 只显示前2个
                        print(f"\n结果 {i}:")
                        print(f"  相关度: {item.get('relevance_score', 0):.4f}")
                        print(f"  类型: {item.get('chunk_type')}")
                        print(f"  条目数: {item.get('item_count')}")
                else:
                    print("搜索失败!")
                    if 'error_detail' in parsed_result:
                        print("错误详情:")
                        print(parsed_result['error_detail'])
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始结果: {result}")
        else:
            print(f"意外的结果类型: {type(result)}")
            print(f"结果: {result}")
            
    except Exception as e:
        print(f"MCP工具调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_search())
