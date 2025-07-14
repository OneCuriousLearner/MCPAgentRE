"""
测试 get_tapd_data 工具的功能
"""
import asyncio
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tapd_mcp_server import mcp

async def test_get_tapd_data():
    """测试 get_tapd_data 工具"""
    print("测试 get_tapd_data 工具...")
    
    try:
        # 导入具体的工具函数进行测试
        from tapd_mcp_server import get_tapd_data
        
        print("✓ get_tapd_data 工具已成功注册并可导入")
        
        # 检查函数是否为异步函数
        if asyncio.iscoroutinefunction(get_tapd_data):
            print("✓ get_tapd_data 是异步函数")
        else:
            print("✗ get_tapd_data 不是异步函数")
            
        print("\n注意: 实际调用需要有效的 API 配置文件 (api.txt)")
        print("工具注册验证完成!")
        
        # 检查本地数据目录
        local_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_data')
        if os.path.exists(local_data_dir):
            print(f"✓ 本地数据目录存在: {local_data_dir}")
        else:
            print(f"! 本地数据目录不存在，将在首次运行时创建: {local_data_dir}")
            
    except ImportError as e:
        print(f"✗ 导入失败: {str(e)}")
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_get_tapd_data())
