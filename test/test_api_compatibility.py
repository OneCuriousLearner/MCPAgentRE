"""
测试API兼容性的脚本

测试SiliconFlow和DeepSeek两种API的调用
注意：现在默认使用SiliconFlow的'deepseek-ai/DeepSeek-V3.1'模型
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
        
        # 测试SiliconFlow API（默认配置）
        print("\n🧪 测试1: SiliconFlow API 默认调用（默认使用deepseek-ai/DeepSeek-V3.1）")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                max_tokens=100
            )
            print(f"✅ SiliconFlow API默认调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ SiliconFlow API默认调用失败: {e}")
        print("=" * 50)
        
        # 测试SiliconFlow API（显式指定）
        print("\n🧪 测试2: SiliconFlow API 显式指定")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                model="deepseek-ai/DeepSeek-V3.1",
                endpoint="https://api.siliconflow.cn/v1",
                max_tokens=100
            )
            print(f"✅ SiliconFlow API显式调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ SiliconFlow API显式调用失败: {e}")
        print("=" * 50)
        
        # 测试DeepSeek API（需要显式指定endpoint）
        print("\n🧪 测试3: DeepSeek API 调用（显式指定endpoint）")
        try:
            result = await api_manager.call_llm(
                prompt=test_prompt,
                session=session,
                model="deepseek-chat",
                endpoint="https://api.deepseek.com/v1",
                max_tokens=100
            )
            print(f"✅ DeepSeek API调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ DeepSeek API调用失败: {e}")
        print("=" * 50)
        
        # 测试DeepSeek Reasoner模型
        print("\n🧪 测试4: DeepSeek Reasoner 模型")
        try:
            result = await api_manager.call_llm(
                prompt="请简单解释一下人工智能的基本概念。",
                session=session,
                model="deepseek-reasoner",
                endpoint="https://api.deepseek.com/v1",
                max_tokens=150
            )
            print(f"✅ DeepSeek Reasoner模型调用成功")
            print(f"📤 响应: {result[:200]}...")
        except Exception as e:
            print(f"❌ DeepSeek Reasoner模型调用失败: {e}")
        print("=" * 50)


if __name__ == "__main__":
    print("🚀 开始API兼容性测试...")
    print("\n📋 环境变量检查:")
    print(f"SF_KEY: {'已设置' if os.getenv('SF_KEY') else '未设置'}")
    print(f"DS_KEY: {'已设置' if os.getenv('DS_KEY') else '未设置'}")
    print(f"SF_MODEL: {os.getenv('SF_MODEL', 'deepseek-ai/DeepSeek-V3.1 (默认)')}")
    print("\n💡 注意：现在默认使用SiliconFlow API的'deepseek-ai/DeepSeek-V3.1'模型")
    print("    只有显式指定DeepSeek endpoint时才会调用DeepSeek API")
    
    asyncio.run(test_api_calls())
    print("\n✅ 测试完成!")
