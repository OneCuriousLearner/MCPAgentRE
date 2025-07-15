#!/usr/bin/env python3
"""
检查MCP服务器注册的工具
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tapd_mcp_server import mcp


async def check_mcp_tools():
    """检查MCP服务器注册的工具"""
    try:
        tools = await mcp.list_tools()
        print(f"✅ MCP服务器启动成功！")
        print(f"📊 已注册工具数量: {len(tools)}")
        print(f"\n🛠️ 已注册的工具列表:")
        
        for i, tool in enumerate(tools, 1):
            tool_name = tool.name if hasattr(tool, 'name') else 'Unknown'
            description = tool.description if hasattr(tool, 'description') else '无描述'
            description = description or '无描述'  # 处理None值
            # 截取描述的前50个字符
            short_desc = description[:50] + "..." if len(description) > 50 else description
            print(f"   {i:2d}. {tool_name} - {short_desc}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查MCP工具时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(check_mcp_tools())
