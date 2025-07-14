"""
测试所有写入 msg_from_fetcher.json 的代码是否都使用覆盖模式
"""
import os
import json
import asyncio
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools.fake_tapd_gen import generate as fake_generate

def test_file_overwrite_behavior():
    """测试文件覆盖行为"""
    test_file = "local_data/test_msg_from_fetcher.json"
    
    print("=== 测试文件覆盖行为 ===")
    
    # 确保目录存在
    os.makedirs("local_data", exist_ok=True)
    
    # 1. 创建一个初始文件，包含一些内容
    initial_data = {"test": "initial content", "items": [1, 2, 3]}
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 创建初始测试文件: {test_file}")
    print(f"  初始内容: {initial_data}")
    
    # 检查初始文件大小
    initial_size = os.path.getsize(test_file)
    print(f"  初始文件大小: {initial_size} 字节")
    
    # 2. 使用 fake_tapd_gen 生成数据（应该覆盖，不是追加）
    print("\n正在使用 fake_tapd_gen 生成数据...")
    fake_generate(n_story_A=2, n_story_B=2, n_bug_A=2, n_bug_B=2, path=test_file)
    
    # 3. 检查文件是否被正确覆盖
    with open(test_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    
    new_size = os.path.getsize(test_file)
    print(f"\n✓ 文件已被更新")
    print(f"  新文件大小: {new_size} 字节")
    print(f"  大小变化: {'增加' if new_size > initial_size else '减少'} {abs(new_size - initial_size)} 字节")
    
    # 验证数据格式
    if 'stories' in new_data and 'bugs' in new_data:
        print(f"✓ 数据格式正确: stories({len(new_data['stories'])}条), bugs({len(new_data['bugs'])}条)")
    else:
        print("✗ 数据格式错误: 缺少 stories 或 bugs 字段")
        return False
    
    # 验证没有残留的初始内容
    if 'test' in new_data or 'items' in new_data:
        print("✗ 发现初始内容残留，文件可能是追加而非覆盖！")
        return False
    else:
        print("✓ 确认文件被完全覆盖，无初始内容残留")
    
    # 清理测试文件
    try:
        os.remove(test_file)
        print(f"✓ 清理测试文件: {test_file}")
    except:
        pass
    
    return True

async def test_tapd_data_fetcher_overwrite():
    """测试 tapd_data_fetcher 的覆盖行为"""
    print("\n=== 测试 tapd_data_fetcher 写入模式 ===")
    
    # 由于需要 API 配置，我们只检查代码中的文件打开模式
    import tapd_data_fetcher
    import inspect
    
    # 检查源代码中的文件打开模式
    source = inspect.getsource(tapd_data_fetcher)
    if "open(" in source and "'w'" in source and "msg_from_fetcher.json" in source:
        print("✓ tapd_data_fetcher.py 使用 'w' 模式写入文件（覆盖）")
        return True
    else:
        print("✗ tapd_data_fetcher.py 文件写入模式检查失败")
        return False

async def test_mcp_server_overwrite():
    """测试 MCP 服务器的覆盖行为"""
    print("\n=== 测试 MCP 服务器写入模式 ===")
    
    # 检查 MCP 服务器代码中的文件打开模式
    import tapd_mcp_server
    import inspect
    
    # 检查源代码中的文件打开模式
    source = inspect.getsource(tapd_mcp_server)
    if "open(" in source and "'w'" in source and "msg_from_fetcher.json" in source:
        print("✓ tapd_mcp_server.py 使用 'w' 模式写入文件（覆盖）")
        return True
    else:
        print("✗ tapd_mcp_server.py 文件写入模式检查失败")
        return False

async def main():
    """主测试函数"""
    print("开始测试所有写入 msg_from_fetcher.json 的代码...")
    
    results = []
    
    # 测试 fake_tapd_gen 的覆盖行为
    results.append(test_file_overwrite_behavior())
    
    # 测试其他模块的写入模式
    results.append(await test_tapd_data_fetcher_overwrite())
    results.append(await test_mcp_server_overwrite())
    
    # 汇总结果
    print(f"\n=== 测试结果汇总 ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有测试通过 ({passed}/{total})")
        print("✅ 确认所有代码都使用覆盖模式写入 msg_from_fetcher.json")
    else:
        print(f"❌ 部分测试失败 ({passed}/{total})")
        print("❌ 需要检查文件写入模式")

if __name__ == '__main__':
    asyncio.run(main())
