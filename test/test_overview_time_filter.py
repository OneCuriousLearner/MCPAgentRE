"""
测试 generate_tapd_overview 工具的时间筛选功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tapd_mcp_server import generate_tapd_overview

async def test_overview_time_filter():
    """测试概览生成工具的时间筛选功能"""
    
    print("=== 测试 generate_tapd_overview 时间筛选功能 ===")
    
    # 测试不同时间范围
    test_cases = [
        ("2025-05-01", "2025-06-30", "5-6月数据"),
        ("2025-07-01", "2025-07-31", "7月数据（应该没有数据）"),
    ]
    
    for since, until, desc in test_cases:
        print(f"\n--- {desc} ({since} 到 {until}) ---")
        
        try:
            # 测试概览生成（不调用LLM，避免API依赖）
            result = await generate_tapd_overview(
                since=since,
                until=until,
                use_local_data=True,
                max_total_tokens=1000  # 小一点避免调用LLM
            )
            
            print("概览生成结果:")
            print(result[:500] + "..." if len(result) > 500 else result)
            
        except Exception as e:
            print(f"测试失败: {str(e)}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_overview_time_filter())
