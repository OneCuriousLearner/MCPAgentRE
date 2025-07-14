"""
测试 generate_tapd_overview 工具的API数据获取模式
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tapd_mcp_server import generate_tapd_overview

async def test_api_mode():
    """测试概览生成工具的API数据获取模式"""
    
    print("=== 测试 generate_tapd_overview API数据获取模式 ===")
    
    try:
        # 测试API模式（注意：这需要有效的API配置）
        result = await generate_tapd_overview(
            since="2025-05-01",
            until="2025-06-30",
            use_local_data=False,  # 使用API数据
            max_total_tokens=1000  # 小一点避免太多LLM调用
        )
        
        print("API模式概览生成结果:")
        print(result[:800] + "..." if len(result) > 800 else result)
        
    except Exception as e:
        print(f"API模式测试失败（这可能是正常的，如果没有配置API密钥）: {str(e)}")
        
        # 再次测试本地模式确保基本功能正常
        print("\n=== 回退到本地模式测试 ===")
        result = await generate_tapd_overview(
            since="2025-05-01", 
            until="2025-06-30",
            use_local_data=True,  # 使用本地数据
            max_total_tokens=1000
        )
        print("本地模式概览生成结果:")
        print(result[:500] + "..." if len(result) > 500 else result)

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_api_mode())
