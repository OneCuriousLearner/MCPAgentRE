"""
测试时间筛选功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tapd_data_fetcher import (
    get_local_story_msg_filtered, 
    get_local_bug_msg_filtered,
    filter_data_by_time
)

async def test_time_filter():
    """测试时间筛选功能"""
    
    print("=== 测试本地需求数据时间筛选 ===")
    
    # 测试不同时间范围
    test_cases = [
        ("2025-01-01", "2025-12-31", "全年数据"),
        ("2025-05-01", "2025-06-30", "5-6月数据"),
        ("2025-07-01", "2025-07-31", "7月数据"),
    ]
    
    for since, until, desc in test_cases:
        print(f"\n--- {desc} ({since} 到 {until}) ---")
        
        # 测试需求数据筛选
        stories = await get_local_story_msg_filtered(since, until)
        print(f"筛选到需求数据：{len(stories)} 条")
        if stories:
            # 显示前3条的创建时间
            for i, story in enumerate(stories[:3]):
                print(f"  需求 {i+1}: {story.get('name', 'N/A')} - 创建时间: {story.get('created', 'N/A')}")
        
        # 测试缺陷数据筛选
        bugs = await get_local_bug_msg_filtered(since, until)
        print(f"筛选到缺陷数据：{len(bugs)} 条")
        if bugs:
            # 显示前3条的创建时间
            for i, bug in enumerate(bugs[:3]):
                print(f"  缺陷 {i+1}: {bug.get('title', 'N/A')} - 创建时间: {bug.get('created', 'N/A')}")

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_time_filter())
