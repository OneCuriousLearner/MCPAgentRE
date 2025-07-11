"""
示例工具模块

该模块包含一个示例函数，用于演示如何扩展MCP Server功能
"""
async def example_function(param1: str, param2: int) -> dict:
    """
    示例函数
    
    参数:
        param1: 字符串参数
        param2: 整型参数
        
    返回:
        包含处理结果的字典
    """
    # 这里是一个示例处理逻辑
    result = {
        "processed_param1": param1.upper(),
        "processed_param2": param2 * 2,
        "status": "success"
    }
    
    return result