"""
Token管理逻辑验证脚本

验证修改后的动态token分配策略
"""

import sys
import json
import asyncio
import aiohttp
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加mcp_tools目录到sys.path
mcp_tools_path = project_root / "mcp_tools"
if str(mcp_tools_path) not in sys.path:
    sys.path.insert(0, str(mcp_tools_path))

from common_utils import get_config
from mcp_tools.test_case_evaluator import TokenCounter, TestCaseEvaluator


async def test_token_management():
    """测试token管理逻辑"""
    print("🧪 测试动态token管理策略...")
    
    # 初始化
    config = get_config()
    evaluator = TestCaseEvaluator(max_context_tokens=12000)
    
    print(f"配置信息:")
    print(f"  总上下文: {evaluator.max_context_tokens}")
    print(f"  请求限制: {evaluator.max_request_tokens}")
    print(f"  响应限制: {evaluator.max_response_tokens}")
    print(f"  请求阈值: {evaluator.token_threshold}")
    
    # 加载测试用例
    json_file = config.local_data_path / "TestCase_20250717141033-32202633.json"
    
    if not json_file.exists():
        print(f"❌ 文件不存在: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"\n📋 加载了 {len(test_cases)} 条测试用例，测试前3条")
    
    # 测试前3个测试用例的token分配
    for i in range(min(3, len(test_cases))):
        test_case = test_cases[i]
        
        print(f"\n--- 测试用例 {i+1} (ID: {test_case.get('test_case_id', 'N/A')}) ---")
        
        # 构建提示词
        test_cases_json = json.dumps([test_case], ensure_ascii=False, indent=2)
        
        case_id = test_case.get('test_case_id', 'N/A')
        title = test_case.get('test_case_title', '未提供')
        prerequisites = test_case.get('prerequisites', '未提供') 
        steps = test_case.get('step_description', '未提供')
        expected = test_case.get('expected_result', '未提供')
        
        prompt = evaluator.evaluation_prompt_template.format(
            test_case_id=case_id,
            test_case_title=title,
            prerequisites=prerequisites,
            step_description=steps,
            expected_result=expected,
            test_cases_json=test_cases_json
        )
        
        # 计算token数量
        request_tokens = evaluator.token_counter.count_tokens(prompt)
        dynamic_response_tokens = min(request_tokens, evaluator.max_response_tokens)
        total_estimated_tokens = request_tokens + dynamic_response_tokens
        
        print(f"📊 Token分析:")
        print(f"  请求tokens: {request_tokens}")
        print(f"  响应tokens限制: {dynamic_response_tokens}")
        print(f"  总计预估: {total_estimated_tokens}")
        print(f"  上下文利用率: {total_estimated_tokens / evaluator.max_context_tokens * 100:.1f}%")
        
        # 检查是否超过限制
        if request_tokens > evaluator.max_request_tokens:
            print(f"⚠️  请求tokens超过限制 ({evaluator.max_request_tokens})")
        
        if total_estimated_tokens > evaluator.max_context_tokens:
            print(f"⚠️  总tokens超过上下文限制")
        else:
            print(f"✅ Token分配合理")
        
        # 显示提示词的前200字符
        print(f"📝 提示词预览: {prompt[:200]}...")


def test_batch_splitting():
    """测试批次分割逻辑"""
    print("\n🔄 测试批次分割逻辑...")
    
    config = get_config()
    evaluator = TestCaseEvaluator(max_context_tokens=12000)
    
    # 加载测试用例
    json_file = config.local_data_path / "TestCase_20250717141033-32202633.json"
    
    if not json_file.exists():
        print(f"❌ 文件不存在: {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"📋 使用 {len(test_cases)} 条测试用例进行批次分割测试")
    
    # 模拟批次分割
    current_index = 0
    batch_number = 1
    total_cases_processed = 0
    
    while current_index < len(test_cases) and batch_number <= 5:  # 限制测试5个批次
        print(f"\n--- 批次 {batch_number} ---")
        
        # 分割当前批次
        batch_cases, next_index = evaluator.split_test_cases_by_tokens(
            test_cases, current_index
        )
        
        if not batch_cases:
            print("没有更多测试用例可处理")
            break
        
        # 统计批次信息
        batch_tokens = evaluator.estimate_batch_tokens(batch_cases)
        cases_in_batch = len(batch_cases)
        avg_tokens_per_case = batch_tokens // cases_in_batch if cases_in_batch > 0 else 0
        
        print(f"  📦 批次大小: {cases_in_batch} 个用例")
        print(f"  📊 总tokens: {batch_tokens}")
        print(f"  📈 平均每用例: {avg_tokens_per_case} tokens")
        print(f"  📋 用例范围: {current_index} - {next_index-1}")
        
        # 检查是否在阈值内
        if batch_tokens <= evaluator.token_threshold:
            print(f"  ✅ 在阈值内 ({evaluator.token_threshold})")
        else:
            print(f"  ⚠️  超过阈值 ({evaluator.token_threshold})")
        
        total_cases_processed += cases_in_batch
        current_index = next_index
        batch_number += 1
    
    print(f"\n📈 批次分割总结:")
    print(f"  总批次数: {batch_number - 1}")
    print(f"  处理用例数: {total_cases_processed}")
    print(f"  剩余用例数: {len(test_cases) - total_cases_processed}")


def main():
    """主函数"""
    print("🚀 开始Token管理逻辑验证...")
    
    # 测试token管理
    asyncio.run(test_token_management())
    
    # 测试批次分割
    test_batch_splitting()
    
    print("\n✅ Token管理逻辑验证完成！")


if __name__ == "__main__":
    main()
