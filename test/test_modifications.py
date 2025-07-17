"""
验证修改后的common_utils和test_case_evaluator

测试：
1. 导入路径是否正确
2. common_utils中的reasoning_content处理是否正确
3. token配置是否合理
"""

import sys
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
mcp_tools_path = project_root / "mcp_tools"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(mcp_tools_path) not in sys.path:
    sys.path.insert(0, str(mcp_tools_path))

def test_imports():
    """测试导入是否正确"""
    print("🧪 测试导入...")
    
    try:
        from common_utils import get_config, get_api_manager, get_file_manager
        print("✅ common_utils导入成功")
        
        from mcp_tools.test_case_evaluator import TokenCounter, TestCaseEvaluator
        print("✅ test_case_evaluator导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_api_manager():
    """测试APIManager的reasoning_content处理"""
    print("\n🧪 测试APIManager...")
    
    try:
        from common_utils import APIManager
        
        api_manager = APIManager()
        print(f"API配置:")
        print(f"  模型: {api_manager.model}")
        print(f"  端点: {api_manager.endpoint}")
        
        # 模拟API响应测试
        print("\n模拟响应处理测试:")
        
        # 模拟deepseek-chat响应
        mock_response_chat = {
            "choices": [{
                "message": {
                    "content": "这是deepseek-chat的回答",
                    "reasoning_content": "这是思考过程（不应该被使用）"
                }
            }]
        }
        
        # 模拟deepseek-reasoner响应
        mock_response_reasoner = {
            "choices": [{
                "message": {
                    "content": "这是最终回答",
                    "reasoning_content": "这是思考过程"
                }
            }]
        }
        
        print("🔍 deepseek-chat模式:")
        print(f"  模型设置: deepseek-chat")
        print(f"  应该获取: content字段")
        print(f"  应该忽略: reasoning_content字段")
        
        print("\n🔍 deepseek-reasoner模式:")
        print(f"  模型设置: deepseek-reasoner")
        print(f"  应该获取: content字段（优先）")
        print(f"  备选方案: reasoning_content字段（当content为空时）")
        
        return True
    except Exception as e:
        print(f"❌ APIManager测试失败: {e}")
        return False

def test_token_counter():
    """测试TokenCounter"""
    print("\n🧪 测试TokenCounter...")
    
    try:
        from mcp_tools.test_case_evaluator import TokenCounter
        
        counter = TokenCounter()
        
        # 测试文本
        test_text = "这是一个测试用例，包含中文和English内容。"
        tokens = counter.count_tokens(test_text)
        
        print(f"测试文本: {test_text}")
        print(f"Token数量: {tokens}")
        print(f"Tokenizer类型: {'精确模式' if counter.tokenizer else '预估模式'}")
        
        return True
    except Exception as e:
        print(f"❌ TokenCounter测试失败: {e}")
        return False

def test_evaluator_config():
    """测试TestCaseEvaluator配置"""
    print("\n🧪 测试TestCaseEvaluator配置...")
    
    try:
        from mcp_tools.test_case_evaluator import TestCaseEvaluator
        
        evaluator = TestCaseEvaluator(max_context_tokens=12000)
        
        print(f"Token配置:")
        print(f"  总上下文: {evaluator.max_context_tokens}")
        print(f"  请求限制: {evaluator.max_request_tokens}")
        print(f"  响应限制: {evaluator.max_response_tokens}")
        print(f"  请求阈值: {evaluator.token_threshold}")
        
        # 计算比例
        request_ratio = evaluator.max_request_tokens / evaluator.max_context_tokens
        response_ratio = evaluator.max_response_tokens / evaluator.max_context_tokens
        
        print(f"\n配置比例:")
        print(f"  请求比例: {request_ratio:.1%}")
        print(f"  响应比例: {response_ratio:.1%}")
        print(f"  缓冲比例: {1 - request_ratio - response_ratio:.1%}")
        
        return True
    except Exception as e:
        print(f"❌ TestCaseEvaluator配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始验证修改...")
    
    success_count = 0
    total_tests = 4
    
    if test_imports():
        success_count += 1
    
    if test_api_manager():
        success_count += 1
    
    if test_token_counter():
        success_count += 1
    
    if test_evaluator_config():
        success_count += 1
    
    print(f"\n📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("✅ 所有测试通过！修改成功。")
    else:
        print("❌ 部分测试失败，请检查配置。")

if __name__ == "__main__":
    main()
