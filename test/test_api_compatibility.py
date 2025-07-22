"""
测试API兼容性的脚本

测试DeepSeek和SiliconFlow两种API的调用
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_tools.common_utils import get_api_manager


async def test_api_calls():
    """测试不同API的调用"""
    api_manager = get_api_manager()
    
    test_prompt = "你好，请简单介绍一下自己。"
    
    async with aiohttp.ClientSession() as session:
        print("测试API兼容性...")
        print("=" * 50)
        
        # 测试DeepSeek API（默认配置）
        print("\n🧪 测试1: DeepSeek API 默认调用")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                max_tokens=100
            )
            print(f"✅ DeepSeek API调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ DeepSeek API调用失败: {e}")
        print("=" * 50)
        
        # 测试DeepSeek API（显式指定）
        print("\n🧪 测试2: DeepSeek API 显式指定")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                model="deepseek-chat",
                endpoint="https://api.deepseek.com/v1",
                max_tokens=100
            )
            print(f"✅ DeepSeek API显式调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ DeepSeek API显式调用失败: {e}")
        print("=" * 50)
        
        # 测试SiliconFlow API
        print("\n🧪 测试3: SiliconFlow API 调用")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                model="moonshotai/Kimi-K2-Instruct",
                endpoint="https://api.siliconflow.cn/v1",
                max_tokens=100
            )
            print(f"✅ SiliconFlow API调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ SiliconFlow API调用失败: {e}")
        print("=" * 50)
        
        # 测试SiliconFlow API（默认模型）
        print("\n🧪 测试4: SiliconFlow API 默认模型")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                endpoint="https://api.siliconflow.cn/v1",
                max_tokens=100
            )
            print(f"✅ SiliconFlow API默认模型调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ SiliconFlow API默认模型调用失败: {e}")
        print("=" * 50)


if __name__ == "__main__":
    print("🚀 开始API兼容性测试...")
    print("\n📋 环境变量检查:")
    print(f"DS_KEY: {'已设置' if os.getenv('DS_KEY') else '未设置'}")
    print(f"SF_KEY: {'已设置' if os.getenv('SF_KEY') else '未设置'}")
    
    asyncio.run(test_api_calls())
    print("\n✅ 测试完成!")
