"""
AI 测试用例评估器

本脚本提供了一个完整的解决方案，用于从 Excel 文件中读取测试用例，
利用大型语言模型（LLM）进行自动化评估，并生成详细的改进建议。
它集成了动态token管理、自定义评估规则和需求单知识库，以实现高效、准确的评估流程。

核心功能：
1.  **数据处理**：从 Excel 文件读取测试用例，并将其转换为结构化的 JSON 格式。
2.  **Token管理**：内置精确的 Token 计数器（优先使用 `transformers` 库），并根据动态计算的
    提示词长度自动将大量测试用例分割成适合模型上下文窗口的批次。
3.  **动态提示词**：基于 `test_case_rules_customer.py` 中的自定义规则（如标题长度、步骤数）
    构建评估提示词，确保评估标准的一致性和灵活性。
4.  **知识库集成**：关联 `test_case_require_list_knowledge_base.py` 中的需求单知识库，
    在评估时为 LLM 提供相关的需求背景信息，提高评估的准确性。
5.  **异步评估**：使用 `aiohttp` 进行异步 API 调用，并行处理多个评估请求，提高处理效率。
6.  **结果解析**：能够解析 LLM 返回的 Markdown 表格格式的评估结果，并将其转换为结构化的
    JSON 数据，便于后续分析和存储。

类与模块说明：
- `TokenCounter`: 负责计算文本的 token 数量。优先使用本地的 `transformers` tokenizer
  进行精确计算，如果失败则回退到改进的预估模式。
- `TestCaseProcessor`: 处理测试用例数据。主要功能是将 Excel 文件转换为 JSON 格式，
  并进行必要的字段映射和数据清理。
- `TestCaseEvaluator`: 核心评估器类。
    - `__init__`: 初始化评估器，加载规则配置和需求单知识库，并根据模型上下文限制计算
      token 分配策略。
    - `_build_dynamic_prompt_template`: 根据规则动态构建发送给 LLM 的提示词模板。
    - `estimate_batch_tokens`: 估算一个批次的测试用例在组合成单个请求后所需的 token 总量。
    - `split_test_cases_by_tokens`: 根据 token 阈值将所有用例分割成多个批次。
    - `evaluate_batch`: 对单个批次的测试用例执行 AI 评估，发送异步请求并获取结果。
    - `parse_evaluation_result`: 解析 AI 返回的 Markdown 格式的评估结果。
    - `evaluate_test_cases`: 编排整个评估流程，从批次分割到结果汇总。

处理流程：
1.  `main_process` 函数启动处理流程。
2.  `TestCaseProcessor` 读取 Excel 文件并转换为 JSON。
3.  `TestCaseEvaluator` 加载所有测试用例。
4.  `split_test_cases_by_tokens` 方法根据 `token_threshold` 将用例分割成多个批次。
5.  对于每个批次，`evaluate_batch` 方法构建一个包含该批次所有用例的提示词，并异步调用
    LLM API。
6.  `parse_evaluation_result` 方法解析返回的 Markdown 表格，提取每个用例的评分和建议。
7.  所有批次处理完成后，结果被汇总并保存到 `Proceed_TestCase_...json` 文件中。
"""

import os
import re
import json
import asyncio
import aiohttp
import pandas as pd
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# 添加项目根目录和mcp_tools目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
mcp_tools_path = project_root / "mcp_tools"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(mcp_tools_path) not in sys.path:
    sys.path.insert(0, str(mcp_tools_path))

# 导入公共工具
from common_utils import get_config, get_api_manager, get_file_manager
from test_case_rules_customer import get_test_case_rules
from test_case_require_list_knowledge_base import RequirementKnowledgeBase


class TokenCounter:
    """Token计数器 - 支持transformers tokenizer和改进的预估模式"""
    
    def __init__(self):
        self.config = get_config()
        self.tokenizer = None
        self._try_load_tokenizer()
    
    def _try_load_tokenizer(self):
        """尝试加载DeepSeek tokenizer"""
        try:
            # 尝试使用transformers库加载tokenizer
            import transformers
            
            tokenizer_path = self.config.models_path / "deepseek_v3_tokenizer" / "deepseek_v3_tokenizer"
            
            if tokenizer_path.exists():
                self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                    str(tokenizer_path), 
                    trust_remote_code=True
                )
                print("已加载DeepSeek tokenizer（transformers），将使用精确token计数")
                return
            else:
                print(f"DeepSeek tokenizer路径不存在: {tokenizer_path}")
                
        except ImportError as e:
            print(f"transformers库未安装: {e}")
        except Exception as e:
            print(f"加载DeepSeek tokenizer失败: {e}")
        
        print("将使用改进的预估模式进行token计数")
        self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量
        
        参数:
            text: 要计算的文本
            
        返回:
            token数量
        """
        if self.tokenizer:
            try:
                tokens = self.tokenizer.encode(text)
                return len(tokens)
            except Exception as e:
                print(f"使用tokenizer计数失败: {e}，转为预估模式")
        
        # 改进的预估模式：基于测试结果优化参数
        # 测试结果显示：
        # - 样本文本平均比率: 0.98 (预估vs实际)
        # - 真实用例平均比率: 0.91 (预估vs实际)
        # - 预估模式总体偏低约10%，需要调整系数
        
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        digits = len(re.findall(r'[0-9]', text))
        punctuation = len(re.findall(r'[^\w\s]', text))
        spaces = len(re.findall(r'\s', text))
        other_chars = len(text) - chinese_chars - english_chars - digits - punctuation - spaces
        
        # 基于测试结果调整的系数
        estimated_tokens = int(
            chinese_chars * 0.7 +      # 中文字符（从0.6调整到0.7）
            english_chars * 0.35 +     # 英文字符（从0.3调整到0.35）
            digits * 0.3 +             # 数字
            punctuation * 0.4 +        # 标点符号
            spaces * 0.1 +             # 空格
            other_chars * 0.4          # 其他字符
        )
        
        # 添加10%的修正系数，因为测试显示预估偏低
        estimated_tokens = int(estimated_tokens * 1.1)
        
        return estimated_tokens


class TestCaseProcessor:
    """Excel测试用例处理器"""
    
    def __init__(self):
        self.config = get_config()
        self.file_manager = get_file_manager()
        
    def excel_to_json(self, excel_file_path: str, json_file_path: str) -> List[Dict[str, Any]]:
        """
        将Excel文件转换为JSON格式
        
        参数:
            excel_file_path: Excel文件路径
            json_file_path: 输出JSON文件路径
            
        返回:
            转换后的数据列表
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file_path)
            
            # 定义列名映射
            column_mapping = {
                '用例ID': 'test_case_id',
                'UUID': 'UUID',
                '用例标题': 'test_case_title',
                '用例目录': 'test_case_menu',
                '是否自动化': 'is_automatic',
                '等级': 'level',
                '前置条件': 'prerequisites',
                '步骤描述类型': 'step_description_type',
                '步骤描述': 'step_description',
                '预期结果': 'expected_result'
            }
            
            # 转换数据
            json_data = []
            for _, row in df.iterrows():
                test_case = {}
                for excel_col, json_key in column_mapping.items():
                    value = row.get(excel_col, "")
                    # 处理NaN值
                    if pd.isna(value):
                        value = ""
                    else:
                        value = str(value).strip()
                    test_case[json_key] = value
                
                json_data.append(test_case)
            
            # 保存JSON文件
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"成功转换 {len(json_data)} 条测试用例数据到 {json_file_path}")
            
            return json_data
            
        except Exception as e:
            raise RuntimeError(f"Excel转JSON失败: {str(e)}")


class TestCaseEvaluator:
    """测试用例AI评估器"""
    
    def __init__(self, max_context_tokens: int = 10000):
        self.config = get_config()
        self.api_manager = get_api_manager()
        self.file_manager = get_file_manager()
        self.token_counter = TokenCounter()
        
        # 初始化需求单知识库
        self.requirement_kb = RequirementKnowledgeBase()
        
        # 加载自定义规则配置
        self.rules_config = get_test_case_rules()
        print(f"已加载测试用例评估规则配置: 标题长度≤{self.rules_config['title_max_length']}字符, "
              f"步骤数≤{self.rules_config['max_steps']}步")
        print(f"需求单知识库: 已加载 {len(self.requirement_kb.requirements)} 个需求单")
        
        # 上下文管理：总context = 请求tokens + 响应tokens + 提示词模板 + 缓冲
        # 为了安全，设置请求tokens为总上下文的25%，响应tokens为50%，留25%缓冲
        self.max_context_tokens = max_context_tokens
        
        # 构建动态评估提示词模板
        self.evaluation_prompt_template = self._build_dynamic_prompt_template()
        
        # 计算提示词模板的基础token数量（包括已替换的规则参数，但不包括动态内容）
        # 先替换掉规则参数（这些在实际使用时已经被替换），但保留动态占位符
        template_with_rules = self.evaluation_prompt_template
        # 动态占位符保持不变，用于后续替换
        template_base = template_with_rules.replace('{test_case_id}', '').replace('{test_case_title}', '').replace('{prerequisites}', '').replace('{step_description}', '').replace('{expected_result}', '').replace('{test_cases_json}', '').replace('{requirement_info}', '')
        self.template_base_tokens = self.token_counter.count_tokens(template_base)
        
        # 重新计算token配置，将模板tokens纳入考虑
        available_tokens = max_context_tokens - self.template_base_tokens  # 减去模板占用的tokens
        self.max_request_tokens = int(available_tokens * 0.25)  # 25%用于请求（用例数据部分）
        self.max_response_tokens = int(available_tokens * 0.50)  # 50%用于响应
        self.token_threshold = int(self.max_request_tokens * 0.75)  # 75%阈值，确保安全

        print(f"Token配置: 总上下文={max_context_tokens}, 模板基础tokens={self.template_base_tokens}, 可用tokens={available_tokens}")
        print(f"请求限制={self.max_request_tokens}, 响应限制={self.max_response_tokens}, 请求阈值={self.token_threshold}")

    def _build_dynamic_prompt_template(self) -> str:
        """
        根据自定义规则配置构建动态提示词模板
        
        返回:
            str: 动态生成的提示词模板
        """
        title_max_length = self.rules_config['title_max_length']
        max_steps = self.rules_config['max_steps']
        priority_ratios = self.rules_config['priority_ratios']
        
        # 构建优先级占比说明
        p0_range = f"{priority_ratios['P0']['min']}%~{priority_ratios['P0']['max']}%"
        p1_range = f"{priority_ratios['P1']['min']}%~{priority_ratios['P1']['max']}%"
        p2_range = f"{priority_ratios['P2']['min']}%~{priority_ratios['P2']['max']}%"
        
        template = f"""请为以下测试用例分别生成评估表格。每个用例应该有自己独立的表格。

重要提示：
1. 请为每个用例生成一个完整的表格
2. 每个表格都应该包含表头 "| 用例信息 | 分数 | 改进建议 |"
3. 每个表格之间用空行分隔
4. 严格按照提供的表格格式输出
5. **除此以外不需要任何分析或解释**

评分规则：

| 用例要素 | 是否必须 | 要求                                                                                                                         |
| ---- | ---- | -------------------------------------------------------------------------------------------------------------------------- |
| 关联需求 | 是    | 1. 用例应当与需求单中的一条或多条有关                                                                                                       |
| 用例标题 | 是    | 1. 标题长度不超过 {title_max_length} 字符，且描述测试功能点<br>2. 语言清晰，简洁易懂<br>3. 避免在用例评分中出现步骤                                               |
| 前置条件 | 否    | 1. 列出所有前提：账号类型，灰度等<br>2. 避免过度复杂：每个条件不超过 2 项描述，必要时分点列出                                                                      |
| 测试步骤 | 是    | 1. 步骤用编号链接：使用 1、2、3... 结构，每步描述一个动作<br>2. 步骤具体化：包含用户操作、输入值和上下文说明<br>3. 步骤数合理：不超过 {max_steps} 步，否则需分解为多个用例。<br>4. 避免步骤中带有检查点 |
| 预期结果 | 是    | 1. 描述明确结果：明确的结果，确切的检查<br>2. 避免模棱两可的词（如功能正常，跟现网一致等）                                                                         |
| 优先级  | 是    | 1. 等级划分标准：采用 P0-P2<br>2. 明确标注：每个用例必须有优先级字段。<br>3. 优先级比例：P0占比应在 {p0_range} 之间，P1占比 {p0_range}，P2占比 {p0_range}               |

需求单信息：
{{requirement_info}}

* 所有评分满分为 10 分，未提供必须提供的字段给0分，每有一点要求未满足则酌情扣1-2分，最低 0 分。
* 若用例与需求单中任何一条需求都无关，则给0分。若与某一条需求相关程度较高，则根据相关程度给出分数。若同时与多条需求相关，则根据相关程度综合评分。
* 对低于 10 分的要素给出准确的建议。给出的每一条建议都应当一针见血，字数在10-30之间。

对于每一条用例，在你的回答中评分与建议的格式如下（你的回答只需提供此类表格，应严格按照此标准执行）：

| 用例信息                           | 分数  | 改进建议                |
| ------------------------------ | --- | ------------------- |
| **用例ID**<br>{{test_case_id}}     | -   | -                   |
| **用例标题**<br>{{test_case_title}}  | 8   | 改为"验证错误密码登录的失败提示"   |
| **前置条件**<br>{{prerequisites}}    | 8   | 补充系统版本要求            |
| **测试步骤**<br>{{step_description}} | 6   | 步骤3增加"等待3秒"         |
| **预期结果**<br>{{expected_result}}  | 7   | 明确提示位置（如：输入框下方红色文字） |

测试用例：
{{test_cases_json}}
"""
        return template

    def estimate_batch_tokens(self, test_cases: List[Dict[str, Any]]) -> int:
        """
        估算一批测试用例在批量处理时需要的token数量
        
        参数:
            test_cases: 测试用例列表
            
        返回:
            预计token数量
        """
        if not test_cases:
            return 0
            
        # 获取需求单信息
        requirement_info = self.requirement_kb.get_requirements_for_evaluation()
        
        # 构建与evaluate_batch一致的批量提示词
        test_cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)
        
        prompt = self.evaluation_prompt_template.format(
            test_case_id="[批量处理]",
            test_case_title="[批量处理]",
            prerequisites="[批量处理]",
            step_description="[批量处理]",
            expected_result="[批量处理]",
            requirement_info=requirement_info,
            test_cases_json=test_cases_json
        )
        
        # 计算token数量
        return self.token_counter.count_tokens(prompt)
    
    def split_test_cases_by_tokens(self, test_cases: List[Dict[str, Any]], 
                                 start_index: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        根据token限制分割测试用例
        
        参数:
            test_cases: 全部测试用例列表
            start_index: 开始索引
            
        返回:
            (当前批次的测试用例, 下一批次的开始索引)
        """
        current_batch = []
        current_tokens = 0
        
        for i in range(start_index, len(test_cases)):
            # 尝试添加下一个测试用例
            candidate_batch = current_batch + [test_cases[i]]
            candidate_tokens = self.estimate_batch_tokens(candidate_batch)
            
            if candidate_tokens > self.token_threshold and current_batch:
                # 超过阈值且当前批次不为空，停止添加
                break
            
            # 添加到当前批次
            current_batch.append(test_cases[i])
            current_tokens = candidate_tokens
            
        next_index = start_index + len(current_batch)
        
        # 显示当前批次包含的测试用例ID
        batch_ids = [case.get('test_case_id', 'N/A') for case in current_batch]
        print(f"当前批次包含 {len(current_batch)} 个测试用例，预计使用 {current_tokens} tokens")
        print(f"批次包含的用例ID: {', '.join(batch_ids)}")
        
        return current_batch, next_index
    
    async def evaluate_batch(self, test_cases: List[Dict[str, Any]], 
                           session: aiohttp.ClientSession) -> str:
        """
        评估一批测试用例
        
        参数:
            test_cases: 测试用例列表
            session: HTTP会话
            
        返回:
            AI评估结果
        """
        # 构建批量提示词 - 一次性处理多个测试用例
        test_cases_json = json.dumps(test_cases, ensure_ascii=False, indent=2)
        
        # 获取需求单信息
        requirement_info = self.requirement_kb.get_requirements_for_evaluation()
        
        # 直接使用模板构建最终提示词（模板已包含所有必要指令）
        final_prompt = self.evaluation_prompt_template.format(
            test_case_id="[批量处理]",
            test_case_title="[批量处理]",
            prerequisites="[批量处理]",
            step_description="[批量处理]",
            expected_result="[批量处理]",
            requirement_info=requirement_info,
            test_cases_json=test_cases_json
        )
        
        # 计算请求token数量，动态设置响应token限制
        request_tokens = self.token_counter.count_tokens(final_prompt)
        # 响应token应该与请求token大致相等，但不超过最大响应限制
        dynamic_response_tokens = min(request_tokens * 2, self.max_response_tokens)  # 批量处理需要更多响应空间
        
        print(f"批量处理 {len(test_cases)} 个用例: 请求tokens={request_tokens}, 响应tokens限制={dynamic_response_tokens}")
        
        # 显示正在处理的测试用例ID
        processing_ids = [case.get('test_case_id', 'N/A') for case in test_cases]
        print(f"🔄 正在处理的测试用例: {', '.join(processing_ids)}")
        print("📤 正在调用AI进行评估...")
        
        # 调用AI API
        result = await self.api_manager.call_llm(
            prompt=final_prompt,
            session=session,
            max_tokens=dynamic_response_tokens
        )
        
        print("✅ AI评估完成，开始解析结果...")
        return result
    
    def parse_evaluation_result(self, ai_response: str) -> List[Dict[str, Any]]:
        """
        解析AI评估结果，将Markdown表格转换为JSON
        支持解析多个表格（当AI返回多个表格时）
        
        参数:
            ai_response: AI返回的Markdown表格
            
        返回:
            解析后的评估结果列表
        """
        evaluations = []
        
        # 清理响应，找到所有表格部分
        lines = ai_response.split('\n')
        all_tables = []
        current_table_lines = []
        table_started = False
        
        for line in lines:
            line = line.strip()
            
            # 检测表格开始
            if '| 用例信息 |' in line or '| --- |' in line:
                # 如果已经在处理表格，先保存当前表格
                if table_started and current_table_lines:
                    all_tables.append(current_table_lines[:])
                    current_table_lines = []
                table_started = True
                continue
            
            # 表格内容行
            elif table_started and line.startswith('|') and len(line.split('|')) >= 4:
                current_table_lines.append(line)
            
            # 表格结束（空行或非表格行）
            elif table_started and (not line or not line.startswith('|')):
                if current_table_lines:
                    all_tables.append(current_table_lines[:])
                    current_table_lines = []
                table_started = False
        
        # 处理最后一个表格
        if table_started and current_table_lines:
            all_tables.append(current_table_lines)
        
        print(f"找到 {len(all_tables)} 个表格")
        print("🔍 开始解析表格数据...")
        
        if not all_tables:
            print("❌ 未找到有效的表格数据")
            return evaluations
        
        # 解析每个表格
        for table_index, table_lines in enumerate(all_tables):
            print(f"📋 解析第 {table_index + 1} 个表格，包含 {len(table_lines)} 行")
            
            current_case = None
            case_id = None
            
            for line in table_lines:
                parts = [part.strip() for part in line.split('|')[1:-1]]
                if len(parts) >= 3:
                    field_info = parts[0]
                    score = parts[1]
                    suggestion = parts[2]
                    
                    # 检查是否包含用例ID
                    if '**用例ID**' in field_info:
                        # 提取用例ID
                        if '<br>' in field_info:
                            id_part = field_info.split('<br>')[-1].strip()
                        else:
                            # 处理没有<br>的情况，直接从field_info中提取
                            id_part = field_info.replace('**用例ID**', '').strip()
                        
                        case_id = id_part
                        print(f"  📝 正在解析用例ID: {case_id}")
                        
                        # 保存之前的用例
                        if current_case:
                            evaluations.append(current_case)
                        
                        # 开始新用例
                        current_case = {
                            'test_case_id': case_id,
                            'evaluations': []
                        }
                        
                    elif current_case and '**' in field_info:
                        # 提取字段名和内容，正确处理多行内容（<br>分隔）
                        if '<br>' in field_info:
                            field_parts = field_info.split('<br>')
                            field_name = field_parts[0].replace('**', '').strip()
                            # 合并所有内容部分，用换行符连接
                            field_content = '<br>'.join(field_parts[1:]).strip() if len(field_parts) > 1 else ''
                            # 将<br>转换为实际换行符，便于阅读
                            field_content = field_content.replace('<br>', '\n')
                        else:
                            # 处理没有<br>的情况
                            field_name = field_info.replace('**', '').strip()
                            field_content = ''
                        
                        print(f"    📊 解析字段: {field_name} (分数: {score.strip() if score.strip() != '-' else '无'})")
                        
                        evaluation_item = {
                            'field': field_name,
                            'content': field_content,
                            'score': score.strip() if score.strip() != '-' else None,
                            'suggestion': suggestion.strip() if suggestion.strip() != '-' else None
                        }
                        
                        current_case['evaluations'].append(evaluation_item)
            
            # 添加当前表格的最后一个用例
            if current_case:
                evaluations.append(current_case)
                print(f"  ✅ 完成用例解析: {current_case['test_case_id']}")
        
        print(f"🎉 成功解析 {len(evaluations)} 个用例的评估结果")
        if evaluations:
            # 输出解析结果的示例
            first_case = evaluations[0]
            print(f"📊 示例解析结果 - 用例ID: {first_case['test_case_id']}, 评估项数: {len(first_case['evaluations'])}")
            for item in first_case['evaluations'][:2]:  # 显示前两个评估项
                print(f"    - {item['field']}: 分数={item['score']}, 建议={item['suggestion']}")
        
        return evaluations
    
    async def evaluate_test_cases(self, test_cases: List[Dict[str, Any]], 
                                test_batch_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        评估测试用例
        
        参数:
            test_cases: 测试用例列表
            test_batch_count: 测试数据批次，1表示只处理第一批
            
        返回:
            评估结果列表
        """
        all_evaluations = []
        current_index = 0
        batch_number = 1
        
        async with aiohttp.ClientSession() as session:
            while current_index < len(test_cases):
                # 如果设置了测试批次限制，检查是否超过
                if test_batch_count and batch_number > test_batch_count:
                    print(f"🛑 达到测试批次限制 ({test_batch_count})，停止处理")
                    break
                
                # 显示总体进度
                remaining_cases = len(test_cases) - current_index
                progress_percent = (current_index / len(test_cases)) * 100
                print(f"\n📊 总体进度: {current_index}/{len(test_cases)} ({progress_percent:.1f}%), 剩余 {remaining_cases} 个用例")
                print(f"🚀 开始处理第 {batch_number} 批次...")
                
                # 分割当前批次
                batch_cases, next_index = self.split_test_cases_by_tokens(
                    test_cases, current_index
                )
                
                if not batch_cases:
                    print("✅ 没有更多测试用例可处理")
                    break
                
                try:
                    # 评估当前批次
                    ai_result = await self.evaluate_batch(batch_cases, session)
                    print(f"📄 AI返回结果长度: {len(ai_result)}")
                    print(f"🔍 AI返回结果前1000字符预览: ========================================")
                    print(f"\n{ai_result[:1000]}\n......")
                    print("============================================================")
                    
                    # 解析结果
                    batch_evaluations = self.parse_evaluation_result(ai_result)
                    all_evaluations.extend(batch_evaluations)
                    
                    # 显示本批次处理的用例ID
                    processed_ids = [eval_result['test_case_id'] for eval_result in batch_evaluations]
                    print(f"✅ 第 {batch_number} 批次处理完成，评估了 {len(batch_evaluations)} 个用例")
                    print(f"📋 已完成评估的用例ID: {', '.join(processed_ids)}")
                    
                    # 如果是测试模式且第一批次完成，询问是否继续
                    if test_batch_count == 1 and batch_number == 1:
                        print(f"\n🧪 第一批次测试完成，评估结果预览:")
                        if batch_evaluations:
                            first_eval = batch_evaluations[0]
                            print(f"📊 用例ID: {first_eval['test_case_id']}")
                            print(f"📈 评估项数量: {len(first_eval['evaluations'])}")
                        else:
                            print("❌ 解析评估结果失败，可能需要调整解析逻辑")
                            print(f"🔍 AI原始返回: {ai_result[:1000]}...")
                        print("\n💡 如需处理更多批次，请修改 test_batch_count 参数")
                        break
                    
                except Exception as e:
                    print(f"❌ 第 {batch_number} 批次处理失败: {str(e)}")
                    if test_batch_count == 1:
                        print("🔧 测试批次失败，请检查API配置和网络连接")
                        break
                    else:
                        print("⏭️ 跳过当前批次，继续处理下一批次")
                
                current_index = next_index
                batch_number += 1
                
                # 批次间延迟，避免API限制
                await asyncio.sleep(1)
        
        return all_evaluations


async def main_process(test_batch_count: Optional[int] = None):
    """
    主处理流程
    
    参数:
        test_batch_count: 测试数据批次限制，None表示处理所有数据
    """
    from datetime import datetime
    from collections import Counter
    start_time = datetime.now()
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⏱️ 开始处理时间: {start_time_str}")
    
    config = get_config()
    processor = TestCaseProcessor()
    # 12K总上下文：3.6K请求 + 7.2K响应 + 2.4K缓冲
    evaluator = TestCaseEvaluator(max_context_tokens=12000)
    
    # 获取规则配置中的优先级比例要求
    rules_config = get_test_case_rules()
    priority_ratios = rules_config['priority_ratios']
    
    # 文件路径
    excel_file = config.local_data_path / "TestCase_20250717141033-32202633.xlsx"
    json_file = config.local_data_path / "TestCase_20250717141033-32202633.json"
    result_file = config.local_data_path / "Proceed_TestCase_20250717141033-32202633.json"
    
    try:
        # 步骤1: 检查Excel文件是否存在
        if not excel_file.exists():
            raise FileNotFoundError(f"Excel文件不存在: {excel_file}")
        
        # 步骤2: 将Excel转换为JSON（如果JSON文件不存在）
        if not json_file.exists():
            print("开始转换Excel文件为JSON格式...")
            test_cases = processor.excel_to_json(str(excel_file), str(json_file))
        else:
            print("JSON文件已存在，直接加载...")
            with open(json_file, 'r', encoding='utf-8') as f:
                test_cases = json.load(f)
        
        print(f"加载了 {len(test_cases)} 条测试用例数据")
        
        # 分析测试用例的优先级分布
        level_counter = Counter()
        for test_case in test_cases:
            level = test_case.get('level', '').strip().upper()
            if level:
                # 标准化优先级表示，例如P0、P1、P2
                if level.startswith('P') and len(level) > 1 and level[1].isdigit():
                    level_counter[level] += 1
                else:
                    level_counter['其他'] += 1
            else:
                level_counter['未设置'] += 1
        
        # 计算各优先级占比
        total_cases = len(test_cases)
        level_percentages = {}
        level_compliance = {}
        
        print("\n📊 测试用例优先级分布分析：")
        for level, count in level_counter.items():
            percentage = (count / total_cases) * 100
            level_percentages[level] = percentage
            
            # 检查是否符合规则配置
            is_compliant = False
            reason = "未找到对应规则"
            
            if level in ['P0', 'P1', 'P2']:
                level_key = level  # 使用原始的P0、P1、P2作为键
                if level_key in priority_ratios:
                    min_percent = priority_ratios[level_key]['min']
                    max_percent = priority_ratios[level_key]['max']
                    is_compliant = min_percent <= percentage <= max_percent
                    if is_compliant:
                        reason = f"符合要求：{min_percent}% ~ {max_percent}%"
                    else:
                        if percentage < min_percent:
                            reason = f"低于最小要求：{percentage:.1f}% < {min_percent}%"
                        else:
                            reason = f"超过最大要求：{percentage:.1f}% > {max_percent}%"
            
            level_compliance[level] = {
                "count": count,
                "percentage": percentage,
                "is_compliant": is_compliant,
                "reason": reason
            }
            
            compliance_icon = "✅" if is_compliant else "❌"
            print(f"{compliance_icon} {level}: {count} 条 ({percentage:.1f}%) - {reason}")
        
        # 步骤3: AI评估
        batch_limit_text = f"，测试批次限制: {test_batch_count}" if test_batch_count else "，将处理所有数据"
        print(f"\n🚀 开始AI评估{batch_limit_text}")
        print(f"📊 总计需要评估 {len(test_cases)} 个测试用例")
        evaluations = await evaluator.evaluate_test_cases(test_cases, test_batch_count)
        
        # 步骤4: 保存评估结果
        if evaluations:
            file_manager = get_file_manager()
            # 包装为字典格式以符合save_json_data的接口，并添加优先级分析结果
            result_data = {
                "evaluation_results": evaluations,
                "total_count": len(evaluations),
                "generated_at": str(json_file).split('_')[-1].replace('.json', ''),
                "process_start_time": start_time_str,
                "process_end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "priority_analysis": {
                    "distribution": level_percentages,
                    "compliance": level_compliance,
                    "rules": priority_ratios
                }
            }
            file_manager.save_json_data(result_data, str(result_file))
            print(f"\n🎉 评估完成！结果已保存到: {result_file}")
            print(f"📈 共评估了 {len(evaluations)} 个测试用例")
        else:
            print("\n❌ 没有生成评估结果")
            
    except Exception as e:
        print(f"处理失败: {str(e)}")
        raise
    
    # 计算处理时间
    end_time = datetime.now()
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    total_seconds = (end_time - start_time).total_seconds()
    
    print(f"\n⏱️ 结束处理时间: {end_time_str}")
    print(f"⏱️ 总处理时间: {total_seconds:.2f} 秒")
    
    # 计算平均每条数据的处理时间
    if evaluations and len(evaluations) > 0:
        avg_time_per_case = total_seconds / len(evaluations)
        print(f"⏱️ 平均每条数据处理时间: {avg_time_per_case:.2f} 秒/条")
    else:
        print("⏱️ 无法计算平均处理时间：没有成功处理的数据")


if __name__ == "__main__":
    print(r" ______     __        ______     __   __   ______     __         __  __     ______     ______   ______     ______    ")
    print(r"/\  __ \   /\ \      /\  ___\   /\ \ / /  /\  __ \   /\ \       /\ \/\ \   /\  __ \   /\__  _\ /\  __ \   /\  == \   ")
    print(r"\ \  __ \  \ \ \     \ \  __\   \ \ \'/   \ \  __ \  \ \ \____  \ \ \_\ \  \ \  __ \  \/_/\ \/ \ \ \/\ \  \ \  __<   ")
    print(r" \ \_\ \_\  \ \_\     \ \_____\  \ \__|    \ \_\ \_\  \ \_____\  \ \_____\  \ \_\ \_\    \ \_\  \ \_____\  \ \_\ \_\ ")
    print(r"  \/_/\/_/   \/_/      \/_____/   \/_/      \/_/\/_/   \/_____/   \/_____/   \/_/\/_/     \/_/   \/_____/   \/_/ /_/ ")

    # 测试模式：处理3批数据
    # asyncio.run(main_process(test_batch_count=3))

    # 正式模式：处理所有数据
    asyncio.run(main_process())  # 不传入test_batch_count参数，将处理所有数据
