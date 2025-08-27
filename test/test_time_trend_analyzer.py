"""
测试时间趋势分析功能
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.time_trend_analyzer import analyze_time_trends

def print_result(result: dict):
    """打印分析结果"""
    print(f"状态: {result.get('status')}")
    print(f"数据类型: {result.get('data_type')}")
    print(f"图表类型: {result.get('chart_type')}")
    print(f"时间范围: {result.get('time_range')}")
    print(f"总数量: {result.get('total_count')}")
    print(f"日期范围: {result.get('date_range', {}).get('start')} 到 {result.get('date_range', {}).get('end')}")
    print(f"天数: {result.get('date_range', {}).get('days_count')}")
    print(f"图表路径: {result.get('chart_path')}")
    print(f"图表URL: {result.get('chart_url')}")
    print(f"生成时间: {result.get('generated_at')}")
    
    # 打印每日统计摘要
    daily_stats = result.get('daily_stats', {})
    if daily_stats:
        print(f"\n每日统计摘要 (共{len(daily_stats)}天):")
        for i, (date, stats) in enumerate(list(daily_stats.items())[:3]):  # 只显示前3天
            print(f"  {date}: 总数={stats['total_count']}, 高优先级={stats['high_priority_count']}, "
                  f"中优先级={stats['medium_priority_count']}, 低优先级={stats['low_priority_count']}, "
                  f"已完成={stats['completed_count']}, 新建={stats['new_count']}")
        if len(daily_stats) > 3:
            print(f"  ... 还有{len(daily_stats)-3}天数据")

async def test_time_trend_analysis():
    """测试时间趋势分析功能"""
    
    print("=== 测试时间趋势分析功能 ===")
    
    # 测试用例
    test_cases = [
        {
            "name": "需求总数趋势(创建时间)",
            "data_type": "story",
            "chart_type": "count",
            "time_field": "created",
            "since": "2025-01-01",
            "until": "2025-12-31"
        },
        {
            "name": "需求优先级分布(创建时间)",
            "data_type": "story",
            "chart_type": "priority",
            "time_field": "created",
            "since": "2025-01-01",
            "until": "2025-12-31"
        },
        {
            "name": "需求状态分布(创建时间)",
            "data_type": "story",
            "chart_type": "status",
            "time_field": "created",
            "since": "2025-01-01",
            "until": "2025-12-31"
        },
        {
            "name": "需求总数趋势(开始时间)",
            "data_type": "story",
            "chart_type": "count",
            "time_field": "begin",
            "since": "2025-01-01",
            "until": "2025-12-31"
        },
        {
            "name": "需求总数趋势(截止时间)",
            "data_type": "story",
            "chart_type": "count",
            "time_field": "due",
            "since": "2025-01-01",
            "until": "2025-12-31"
        },
        {
            "name": "缺陷总数趋势",
            "data_type": "bug",
            "chart_type": "count",
            "since": "2025-01-01",
            "until": "2025-12-31"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        
        try:
            result = await analyze_time_trends(
                data_type=test_case['data_type'],
                chart_type=test_case['chart_type'],
                time_field=test_case.get('time_field', 'created'),
                since=test_case['since'],
                until=test_case['until'],
                chart_title=test_case['name']
            )
            
            if result.get('status') == 'success':
                print("✓ 测试成功")
                print_result(result)
            else:
                print(f"✗ 测试失败: {result.get('message')}")
                print(f"建议: {result.get('suggestion', '无')}")
                
        except Exception as e:
            print(f"✗ 测试异常: {str(e)}")
    
    print("\n=== 测试完成 ===")

async def test_custom_time_range():
    """测试自定义时间范围"""
    
    print("\n=== 测试自定义时间范围 ===")
    
    # 测试不同的时间范围
    time_ranges = [
        ("2025-07-01", "2025-07-31", "7月数据"),
        ("2025-08-01", "2025-08-31", "8月数据"),
        ("2025-09-01", "2025-09-30", "9月数据")
    ]
    
    for since, until, desc in time_ranges:
        print(f"\n--- {desc} ({since} 到 {until}) ---")
        
        try:
            result = await analyze_time_trends(
                data_type="story",
                chart_type="count",
                since=since,
                until=until
            )
            
            if result.get('status') == 'success':
                print(f"✓ 成功获取{result.get('total_count')}条数据")
                print(f"  日期范围: {result.get('date_range', {}).get('start')} 到 {result.get('date_range', {}).get('end')}")
            else:
                print(f"✗ 失败: {result.get('message')}")
                
        except Exception as e:
            print(f"✗ 异常: {str(e)}")
    
    # 测试开始时间字段
    print("\n--- 开始时间字段分析 (2025-08-01 到 2025-09-30) ---")
    try:
        result = await analyze_time_trends(
            data_type="story",
            chart_type="count",
            time_field="begin",
            since="2025-08-01",
            until="2025-09-30"
        )
        
        if result.get('status') == 'success':
            print(f"✓ 成功获取{result.get('total_count')}条数据")
            print(f"  日期范围: {result.get('date_range', {}).get('start')} 到 {result.get('date_range', {}).get('end')}")
        else:
            print(f"✗ 失败: {result.get('message')}")
            
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
    
    # 测试截止时间字段
    print("\n--- 截止时间字段分析 (2025-08-01 到 2025-09-30) ---")
    try:
        result = await analyze_time_trends(
            data_type="story",
            chart_type="count",
            time_field="due",
            since="2025-08-01",
            until="2025-09-30"
        )
        
        if result.get('status') == 'success':
            print(f"✓ 成功获取{result.get('total_count')}条数据")
            print(f"  日期范围: {result.get('date_range', {}).get('start')} 到 {result.get('date_range', {}).get('end')}")
        else:
            print(f"✗ 失败: {result.get('message')}")
            
    except Exception as e:
        print(f"✗ 异常: {str(e)}")

if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_time_trend_analysis())
    asyncio.run(test_custom_time_range())