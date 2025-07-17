"""
测试用例质量评分引擎
基于配置规则对测试用例进行自动质量评分
"""

import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .scoring_config_manager import ScoringConfig, ScoringConfigManager, get_config_manager
import jieba
import aiohttp
import os


class TestCaseQualityScorer:
    """测试用例质量评分引擎"""
    
    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config
        self.config_manager = None
        
    async def initialize(self):
        """初始化评分器"""
        if not self.config:
            self.config_manager = await get_config_manager()
            self.config = await self.config_manager.load_config()
    
    async def score_single_testcase(self, testcase_data: dict) -> dict:
        """对单个测试用例进行评分"""
        if not self.config:
            await self.initialize()
        
        # 提取测试用例字段
        title = testcase_data.get("title", "")
        precondition = testcase_data.get("precondition", "")
        steps = testcase_data.get("steps", "")
        expected_result = testcase_data.get("expected_result", "")
        priority = testcase_data.get("priority", "")
        testcase_id = testcase_data.get("id", "")
        
        # 分项评分
        title_score = await self.score_title(title)
        precondition_score = await self.score_precondition(precondition)
        steps_score = await self.score_steps(steps)
        expected_result_score = await self.score_expected_result(expected_result)
        priority_score = await self.score_priority(priority)
        
        # 计算总分
        total_score = (
            title_score["score"] * self.config.title_rule.weight +
            precondition_score["score"] * self.config.precondition_rule.weight +
            steps_score["score"] * self.config.steps_rule.weight +
            expected_result_score["score"] * self.config.expected_result_rule.weight +
            priority_score["score"] * self.config.priority_rule.weight
        )
        
        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions(
            title_score, precondition_score, steps_score, 
            expected_result_score, priority_score
        )
        
        return {
            "testcase_id": testcase_id,
            "total_score": round(total_score, 2),
            "detailed_scores": {
                "title": title_score,
                "precondition": precondition_score,
                "steps": steps_score,
                "expected_result": expected_result_score,
                "priority": priority_score
            },
            "improvement_suggestions": improvement_suggestions,
            "score_level": self._get_score_level(total_score),
            "scored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def score_title(self, title: str) -> dict:
        """评分标题质量"""
        if not title:
            return {
                "score": 0,
                "reason": "标题为空",
                "suggestions": ["请添加测试用例标题"]
            }
        
        title_length = len(title.strip())
        rule = self.config.title_rule
        
        # 根据长度查找对应的评分范围
        score = 5  # 默认分数
        reason = "标题长度合适"
        suggestions = []
        
        for scoring_range in rule.scoring_ranges:
            if scoring_range.min_value <= title_length <= scoring_range.max_value:
                score = scoring_range.score
                reason = f"标题长度{title_length}字符，{scoring_range.description}"
                break
        
        # 生成建议
        if title_length > rule.max_length:
            suggestions.append(f"标题过长({title_length}字符)，建议缩短到{rule.max_length}字符以内")
        elif title_length < rule.min_length:
            suggestions.append(f"标题过短({title_length}字符)，建议增加到{rule.min_length}字符以上")
        
        # 检查标题是否包含关键信息
        if not self._contains_action_words(title):
            suggestions.append("标题建议包含操作动词，如：登录、查询、创建等")
        
        return {
            "score": score,
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "length": title_length,
                "max_allowed": rule.max_length,
                "min_required": rule.min_length
            }
        }
    
    async def score_precondition(self, precondition: str) -> dict:
        """评分前置条件"""
        if not precondition or precondition.strip() == "":
            return {
                "score": 6,
                "reason": "无前置条件",
                "suggestions": ["考虑是否需要添加前置条件"],
                "details": {"count": 0}
            }
        
        # 分析前置条件数量
        precondition_items = self._parse_precondition_items(precondition)
        item_count = len(precondition_items)
        rule = self.config.precondition_rule
        
        score = 5  # 默认分数
        reason = "前置条件数量合适"
        suggestions = []
        
        # 根据数量查找对应的评分范围
        for scoring_range in rule.scoring_ranges:
            if scoring_range.min_value <= item_count <= scoring_range.max_value:
                score = scoring_range.score
                reason = f"前置条件{item_count}项，{scoring_range.description}"
                break
        
        # 生成建议
        if item_count > rule.max_count:
            suggestions.append(f"前置条件过多({item_count}项)，建议精简到{rule.max_count}项以内")
        
        # 检查前置条件质量
        vague_conditions = self._check_vague_preconditions(precondition_items)
        if vague_conditions:
            suggestions.append(f"以下前置条件描述不够具体：{', '.join(vague_conditions)}")
        
        return {
            "score": score,
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "count": item_count,
                "max_allowed": rule.max_count,
                "items": precondition_items
            }
        }
    
    async def score_steps(self, steps: str) -> dict:
        """评分测试步骤"""
        if not steps or steps.strip() == "":
            return {
                "score": 0,
                "reason": "缺少测试步骤",
                "suggestions": ["请添加详细的测试步骤"],
                "details": {"count": 0}
            }
        
        # 分析测试步骤
        step_items = self._parse_test_steps(steps)
        step_count = len(step_items)
        rule = self.config.steps_rule
        
        score = 5  # 默认分数
        reason = "测试步骤数量合适"
        suggestions = []
        
        # 根据步骤数量查找对应的评分范围
        for scoring_range in rule.scoring_ranges:
            if scoring_range.min_value <= step_count <= scoring_range.max_value:
                score = scoring_range.score
                reason = f"测试步骤{step_count}项，{scoring_range.description}"
                break
        
        # 检查步骤编号
        if rule.require_numbered_steps:
            if not self._has_numbered_steps(steps):
                score = max(0, score - 2)
                suggestions.append("建议使用数字编号（1、2、3）来组织测试步骤")
        
        # 检查步骤质量
        vague_steps = self._check_vague_steps(step_items)
        if vague_steps:
            suggestions.append(f"以下步骤描述不够具体：{', '.join(vague_steps[:3])}")
        
        # 检查步骤逻辑性
        if not self._check_step_logic(step_items):
            suggestions.append("测试步骤逻辑性有待改进，建议按操作顺序排列")
        
        return {
            "score": score,
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "count": step_count,
                "min_required": rule.min_steps,
                "max_allowed": rule.max_steps,
                "has_numbering": self._has_numbered_steps(steps),
                "items": step_items
            }
        }
    
    async def score_expected_result(self, expected_result: str) -> dict:
        """评分预期结果"""
        if not expected_result or expected_result.strip() == "":
            return {
                "score": 0,
                "reason": "缺少预期结果",
                "suggestions": ["请添加明确的预期结果"],
                "details": {"length": 0}
            }
        
        result_length = len(expected_result.strip())
        rule = self.config.expected_result_rule
        
        score = 8  # 默认分数
        reason = "预期结果描述合适"
        suggestions = []
        
        # 检查长度
        if result_length < rule.min_length:
            score = 4
            reason = f"预期结果过短({result_length}字符)"
            suggestions.append(f"预期结果描述过短，建议增加到{rule.min_length}字符以上")
        elif result_length > rule.max_length:
            score = 6
            reason = f"预期结果过长({result_length}字符)"
            suggestions.append(f"预期结果描述过长，建议精简到{rule.max_length}字符以内")
        
        # 检查模糊描述
        vague_terms_found = []
        for term in rule.avoid_vague_terms:
            if term in expected_result:
                vague_terms_found.append(term)
        
        if vague_terms_found:
            score = max(0, score - len(vague_terms_found))
            suggestions.append(f"避免使用模糊词汇：{', '.join(vague_terms_found)}，建议使用具体的描述")
        
        # 检查是否包含具体的验证点
        if not self._has_specific_verification_points(expected_result):
            score = max(0, score - 1)
            suggestions.append("建议增加具体的验证点，如：页面元素、数据状态、错误信息等")
        
        return {
            "score": score,
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "length": result_length,
                "min_required": rule.min_length,
                "max_allowed": rule.max_length,
                "vague_terms": vague_terms_found
            }
        }
    
    async def score_priority(self, priority: str) -> dict:
        """评分优先级"""
        rule = self.config.priority_rule
        
        if not priority or priority.strip() == "":
            return {
                "score": 0,
                "reason": "缺少优先级标注",
                "suggestions": [f"请设置优先级，可选值：{', '.join(rule.valid_priorities)}"],
                "details": {"value": "", "valid_options": rule.valid_priorities}
            }
        
        priority_clean = priority.strip().upper()
        
        if priority_clean in rule.valid_priorities:
            score = 10
            reason = f"优先级标注正确：{priority_clean}"
            suggestions = []
        else:
            score = 3
            reason = f"优先级标注不规范：{priority_clean}"
            suggestions = [f"请使用标准优先级：{', '.join(rule.valid_priorities)}"]
        
        return {
            "score": score,
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "value": priority_clean,
                "valid_options": rule.valid_priorities
            }
        }
    
    def _contains_action_words(self, title: str) -> bool:
        """检查标题是否包含操作动词"""
        action_words = ["登录", "查询", "搜索", "创建", "删除", "修改", "更新", "添加", "上传", "下载", "提交", "取消", "确认", "验证", "检查", "测试"]
        return any(word in title for word in action_words)
    
    def _parse_precondition_items(self, precondition: str) -> List[str]:
        """解析前置条件项目"""
        # 按行分割，过滤空行
        lines = [line.strip() for line in precondition.split('\n') if line.strip()]
        
        # 按标点符号分割
        items = []
        for line in lines:
            # 按分号、句号分割
            sub_items = re.split(r'[;；。]', line)
            items.extend([item.strip() for item in sub_items if item.strip()])
        
        return items
    
    def _check_vague_preconditions(self, items: List[str]) -> List[str]:
        """检查模糊的前置条件"""
        vague_keywords = ["已经", "正常", "可用", "有效", "合法"]
        vague_items = []
        
        for item in items:
            if any(keyword in item for keyword in vague_keywords) and len(item) < 15:
                vague_items.append(item[:20] + "..." if len(item) > 20 else item)
        
        return vague_items
    
    def _parse_test_steps(self, steps: str) -> List[str]:
        """解析测试步骤"""
        # 按行分割，过滤空行
        lines = [line.strip() for line in steps.split('\n') if line.strip()]
        
        # 移除编号，提取步骤内容
        step_items = []
        for line in lines:
            # 移除开头的数字编号
            clean_line = re.sub(r'^\d+[、。\.\)]\s*', '', line)
            if clean_line:
                step_items.append(clean_line)
        
        return step_items
    
    def _has_numbered_steps(self, steps: str) -> bool:
        """检查是否有数字编号"""
        return bool(re.search(r'^\d+[、。\.\)]', steps, re.MULTILINE))
    
    def _check_vague_steps(self, steps: List[str]) -> List[str]:
        """检查模糊的测试步骤"""
        vague_keywords = ["点击", "输入", "选择", "等待", "检查"]
        vague_steps = []
        
        for step in steps:
            if any(keyword in step for keyword in vague_keywords) and len(step) < 20:
                vague_steps.append(step[:30] + "..." if len(step) > 30 else step)
        
        return vague_steps
    
    def _check_step_logic(self, steps: List[str]) -> bool:
        """检查步骤逻辑性"""
        # 简单的逻辑检查：是否有登录->操作->验证的基本流程
        has_login = any("登录" in step for step in steps)
        has_operation = any(any(op in step for op in ["点击", "输入", "选择", "提交"]) for step in steps)
        has_verification = any(any(ver in step for ver in ["检查", "验证", "确认"]) for step in steps)
        
        return has_operation  # 至少要有操作步骤
    
    def _has_specific_verification_points(self, result: str) -> bool:
        """检查是否有具体的验证点"""
        specific_keywords = ["页面", "按钮", "文本", "消息", "数据", "状态", "错误", "成功", "失败", "显示", "隐藏"]
        return any(keyword in result for keyword in specific_keywords)
    
    def _generate_improvement_suggestions(self, title_score: dict, precondition_score: dict, 
                                        steps_score: dict, expected_result_score: dict, 
                                        priority_score: dict) -> List[str]:
        """生成综合改进建议"""
        all_suggestions = []
        
        # 收集所有低分项的建议
        if title_score["score"] < 7:
            all_suggestions.extend([f"【标题】{s}" for s in title_score["suggestions"]])
        if precondition_score["score"] < 7:
            all_suggestions.extend([f"【前置条件】{s}" for s in precondition_score["suggestions"]])
        if steps_score["score"] < 7:
            all_suggestions.extend([f"【测试步骤】{s}" for s in steps_score["suggestions"]])
        if expected_result_score["score"] < 7:
            all_suggestions.extend([f"【预期结果】{s}" for s in expected_result_score["suggestions"]])
        if priority_score["score"] < 7:
            all_suggestions.extend([f"【优先级】{s}" for s in priority_score["suggestions"]])
        
        # 限制建议数量
        return all_suggestions[:10]
    
    def _get_score_level(self, score: float) -> str:
        """获取分数等级"""
        if score >= 9.0:
            return "优秀"
        elif score >= 7.0:
            return "良好"
        elif score >= 5.0:
            return "及格"
        else:
            return "需要改进"
    
    async def score_batch_testcases(self, testcases: List[dict], 
                                  batch_size: int = 10) -> dict:
        """批量评分测试用例"""
        if not self.config:
            await self.initialize()
        
        results = []
        total_count = len(testcases)
        processed_count = 0
        
        # 分批处理
        for i in range(0, total_count, batch_size):
            batch = testcases[i:i + batch_size]
            batch_results = []
            
            for testcase in batch:
                try:
                    result = await self.score_single_testcase(testcase)
                    batch_results.append(result)
                    processed_count += 1
                except Exception as e:
                    # 记录错误但继续处理
                    batch_results.append({
                        "testcase_id": testcase.get("id", "unknown"),
                        "error": f"评分失败: {str(e)}",
                        "total_score": 0
                    })
                    processed_count += 1
            
            results.extend(batch_results)
            
            # 短暂休息，避免过度占用资源
            await asyncio.sleep(0.1)
        
        # 生成统计信息
        successful_scores = [r for r in results if "error" not in r]
        if successful_scores:
            scores = [r["total_score"] for r in successful_scores]
            avg_score = sum(scores) / len(scores)
            score_distribution = {
                "优秀": len([s for s in scores if s >= 9.0]),
                "良好": len([s for s in scores if 7.0 <= s < 9.0]),
                "及格": len([s for s in scores if 5.0 <= s < 7.0]),
                "需要改进": len([s for s in scores if s < 5.0])
            }
        else:
            avg_score = 0
            score_distribution = {}
        
        return {
            "total_count": total_count,
            "processed_count": processed_count,
            "success_count": len(successful_scores),
            "error_count": total_count - len(successful_scores),
            "average_score": round(avg_score, 2),
            "score_distribution": score_distribution,
            "results": results,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# 全局评分器实例
_scorer = None

async def get_quality_scorer() -> TestCaseQualityScorer:
    """获取全局评分器实例"""
    global _scorer
    if _scorer is None:
        _scorer = TestCaseQualityScorer()
        await _scorer.initialize()
    return _scorer