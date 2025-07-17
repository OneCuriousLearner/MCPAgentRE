"""
增强的测试用例质量评分引擎
支持灵活的自定义评分规则和多套评分标准
"""

import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .enhanced_scoring_config import (
    EnhancedScoringConfigManager, 
    ScoringProfile, 
    ScoringStrategy,
    ScoreLevel,
    get_enhanced_config_manager
)
import jieba


class EnhancedTestCaseQualityScorer:
    """增强的测试用例质量评分引擎"""
    
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.config_manager: Optional[EnhancedScoringConfigManager] = None
        self.current_profile: Optional[ScoringProfile] = None
        
    async def initialize(self, profile_name: str = None):
        """初始化评分器"""
        if profile_name:
            self.profile_name = profile_name
            
        if not self.config_manager:
            self.config_manager = await get_enhanced_config_manager()
            
        self.current_profile = await self.config_manager.load_profile(self.profile_name)
    
    async def switch_profile(self, profile_name: str) -> bool:
        """切换评分配置档案"""
        try:
            if not self.config_manager:
                await self.initialize()
            
            self.current_profile = await self.config_manager.load_profile(profile_name)
            self.profile_name = profile_name
            return True
        except Exception as e:
            print(f"切换配置档案失败: {str(e)}")
            return False
    
    async def score_single_testcase(self, testcase_data: dict, 
                                   profile_name: str = None) -> dict:
        """对单个测试用例进行评分"""
        if profile_name and profile_name != self.profile_name:
            await self.switch_profile(profile_name)
        
        if not self.current_profile:
            await self.initialize()
        
        # 提取测试用例字段
        title = testcase_data.get("title", "")
        precondition = testcase_data.get("precondition", "")
        steps = testcase_data.get("steps", "")
        expected_result = testcase_data.get("expected_result", "")
        priority = testcase_data.get("priority", "")
        testcase_id = testcase_data.get("id", "")
        
        # 分项评分
        dimension_scores = {}
        total_weighted_score = 0
        total_weight = 0
        
        for dim_name, dim_rule in self.current_profile.dimensions.items():
            if not dim_rule.enabled:
                continue
                
            if dim_name == "title":
                score_result = await self.score_title(title, dim_rule)
            elif dim_name == "precondition":
                score_result = await self.score_precondition(precondition, dim_rule)
            elif dim_name == "steps":
                score_result = await self.score_steps(steps, dim_rule)
            elif dim_name == "expected_result":
                score_result = await self.score_expected_result(expected_result, dim_rule)
            elif dim_name == "priority":
                score_result = await self.score_priority(priority, dim_rule)
            else:
                # 对于自定义维度，提供基础评分
                score_result = await self.score_custom_dimension(
                    testcase_data.get(dim_name, ""), dim_rule
                )
            
            dimension_scores[dim_name] = score_result
            total_weighted_score += score_result["score"] * dim_rule.weight
            total_weight += dim_rule.weight
        
        # 计算总分
        if total_weight > 0:
            total_score = total_weighted_score / total_weight
        else:
            total_score = 0
        
        # 应用评分策略调整
        adjusted_score = self._apply_scoring_strategy(total_score, dimension_scores)
        
        # 获取评分等级
        score_level = self.current_profile.thresholds.get_level(adjusted_score)
        
        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions(dimension_scores)
        
        return {
            "testcase_id": testcase_id,
            "total_score": round(adjusted_score, 2),
            "raw_score": round(total_score, 2),
            "score_level": score_level.value,
            "score_level_cn": self._get_score_level_cn(score_level),
            "profile_name": self.profile_name,
            "strategy": self.current_profile.strategy.value,
            "detailed_scores": dimension_scores,
            "improvement_suggestions": improvement_suggestions,
            "scored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def score_title(self, title: str, rule) -> dict:
        """评分标题质量"""
        if not title:
            return {
                "score": rule.min_score,
                "reason": "标题为空",
                "suggestions": ["请添加测试用例标题"],
                "details": {"length": 0}
            }
        
        title_length = len(title.strip())
        params = rule.custom_params
        
        # 根据评分范围计算分数
        score = self._calculate_score_from_ranges(title_length, rule.scoring_ranges)
        
        # 应用维度限制
        score = max(rule.min_score, min(rule.max_score, score))
        
        reason = f"标题长度{title_length}字符"
        suggestions = []
        
        # 生成建议
        if title_length > params.get("max_length", 40):
            suggestions.append(f"标题过长({title_length}字符)，建议缩短到{params.get('max_length', 40)}字符以内")
        elif title_length < params.get("min_length", 5):
            suggestions.append(f"标题过短({title_length}字符)，建议增加到{params.get('min_length', 5)}字符以上")
        
        # 检查是否包含操作动词
        if params.get("require_action_words", True):
            action_words = params.get("action_words", [])
            if not any(word in title for word in action_words):
                suggestions.append("标题建议包含操作动词，如：登录、查询、创建等")
                score = max(rule.min_score, score - 1)
        
        return {
            "score": round(score, 2),
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "length": title_length,
                "max_allowed": params.get("max_length", 40),
                "min_required": params.get("min_length", 5)
            }
        }
    
    async def score_precondition(self, precondition: str, rule) -> dict:
        """评分前置条件"""
        params = rule.custom_params
        
        if not precondition or precondition.strip() == "":
            if params.get("allow_empty", True):
                return {
                    "score": 6.0,
                    "reason": "无前置条件",
                    "suggestions": ["考虑是否需要添加前置条件"],
                    "details": {"count": 0}
                }
            else:
                return {
                    "score": rule.min_score,
                    "reason": "缺少前置条件",
                    "suggestions": ["请添加前置条件"],
                    "details": {"count": 0}
                }
        
        # 分析前置条件数量
        precondition_items = self._parse_precondition_items(precondition)
        item_count = len(precondition_items)
        
        # 根据评分范围计算分数
        score = self._calculate_score_from_ranges(item_count, rule.scoring_ranges)
        score = max(rule.min_score, min(rule.max_score, score))
        
        reason = f"前置条件{item_count}项"
        suggestions = []
        
        # 生成建议
        max_count = params.get("max_count", 2)
        if item_count > max_count:
            suggestions.append(f"前置条件过多({item_count}项)，建议精简到{max_count}项以内")
        
        # 检查模糊描述
        vague_keywords = params.get("vague_keywords", [])
        vague_conditions = [item for item in precondition_items 
                           if any(keyword in item for keyword in vague_keywords) and len(item) < 15]
        if vague_conditions:
            suggestions.append(f"以下前置条件描述不够具体：{', '.join(vague_conditions[:3])}")
        
        return {
            "score": round(score, 2),
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "count": item_count,
                "max_allowed": max_count,
                "items": precondition_items
            }
        }
    
    async def score_steps(self, steps: str, rule) -> dict:
        """评分测试步骤"""
        params = rule.custom_params
        
        if not steps or steps.strip() == "":
            return {
                "score": rule.min_score,
                "reason": "缺少测试步骤",
                "suggestions": ["请添加详细的测试步骤"],
                "details": {"count": 0}
            }
        
        # 分析测试步骤
        step_items = self._parse_test_steps(steps)
        step_count = len(step_items)
        
        # 根据评分范围计算分数
        score = self._calculate_score_from_ranges(step_count, rule.scoring_ranges)
        score = max(rule.min_score, min(rule.max_score, score))
        
        reason = f"测试步骤{step_count}项"
        suggestions = []
        
        # 检查步骤编号
        if params.get("require_numbered_steps", True):
            if not self._has_numbered_steps(steps):
                score = max(rule.min_score, score - 2)
                suggestions.append("建议使用数字编号（1、2、3）来组织测试步骤")
        
        # 检查步骤质量
        vague_keywords = params.get("vague_keywords", [])
        vague_steps = [step for step in step_items 
                      if any(keyword in step for keyword in vague_keywords) and len(step) < 20]
        if vague_steps:
            suggestions.append(f"以下步骤描述不够具体：{', '.join(vague_steps[:3])}")
        
        # 检查逻辑性
        if params.get("require_logical_order", True):
            if not self._check_step_logic(step_items):
                suggestions.append("测试步骤逻辑性有待改进，建议按操作顺序排列")
        
        return {
            "score": round(score, 2),
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "count": step_count,
                "min_required": params.get("min_steps", 1),
                "max_allowed": params.get("max_steps", 10),
                "has_numbering": self._has_numbered_steps(steps),
                "items": step_items
            }
        }
    
    async def score_expected_result(self, expected_result: str, rule) -> dict:
        """评分预期结果"""
        params = rule.custom_params
        
        if not expected_result or expected_result.strip() == "":
            return {
                "score": rule.min_score,
                "reason": "缺少预期结果",
                "suggestions": ["请添加明确的预期结果"],
                "details": {"length": 0}
            }
        
        result_length = len(expected_result.strip())
        
        # 基础分数
        score = (rule.min_score + rule.max_score) / 2
        reason = "预期结果描述合适"
        suggestions = []
        
        # 检查长度
        min_length = params.get("min_length", 5)
        max_length = params.get("max_length", 200)
        
        if result_length < min_length:
            score = rule.min_score + 1
            reason = f"预期结果过短({result_length}字符)"
            suggestions.append(f"预期结果描述过短，建议增加到{min_length}字符以上")
        elif result_length > max_length:
            score = rule.max_score - 2
            reason = f"预期结果过长({result_length}字符)"
            suggestions.append(f"预期结果描述过长，建议精简到{max_length}字符以内")
        
        # 检查模糊描述
        avoid_terms = params.get("avoid_vague_terms", [])
        vague_terms_found = [term for term in avoid_terms if term in expected_result]
        
        if vague_terms_found:
            score = max(rule.min_score, score - len(vague_terms_found))
            suggestions.append(f"避免使用模糊词汇：{', '.join(vague_terms_found)}，建议使用具体的描述")
        
        # 检查验证点
        if params.get("require_verification_points", True):
            if not self._has_specific_verification_points(expected_result):
                score = max(rule.min_score, score - 1)
                suggestions.append("建议增加具体的验证点，如：页面元素、数据状态、错误信息等")
        
        score = max(rule.min_score, min(rule.max_score, score))
        
        return {
            "score": round(score, 2),
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "length": result_length,
                "min_required": min_length,
                "max_allowed": max_length,
                "vague_terms": vague_terms_found
            }
        }
    
    async def score_priority(self, priority: str, rule) -> dict:
        """评分优先级"""
        params = rule.custom_params
        valid_priorities = params.get("valid_priorities", ["P0", "P1", "P2", "P3"])
        case_sensitive = params.get("case_sensitive", False)
        
        if not priority or priority.strip() == "":
            return {
                "score": rule.min_score,
                "reason": "缺少优先级标注",
                "suggestions": [f"请设置优先级，可选值：{', '.join(valid_priorities)}"],
                "details": {"value": "", "valid_options": valid_priorities}
            }
        
        priority_clean = priority.strip() if case_sensitive else priority.strip().upper()
        valid_priorities_check = valid_priorities if case_sensitive else [p.upper() for p in valid_priorities]
        
        if priority_clean in valid_priorities_check:
            score = rule.max_score
            reason = f"优先级标注正确：{priority_clean}"
            suggestions = []
        else:
            if params.get("allow_custom_priorities", False):
                score = rule.max_score - 2
                reason = f"自定义优先级：{priority_clean}"
                suggestions = [f"建议使用标准优先级：{', '.join(valid_priorities)}"]
            else:
                score = rule.min_score + 1
                reason = f"优先级标注不规范：{priority_clean}"
                suggestions = [f"请使用标准优先级：{', '.join(valid_priorities)}"]
        
        return {
            "score": round(score, 2),
            "reason": reason,
            "suggestions": suggestions,
            "details": {
                "value": priority_clean,
                "valid_options": valid_priorities
            }
        }
    
    async def score_custom_dimension(self, value: str, rule) -> dict:
        """评分自定义维度"""
        if not value:
            return {
                "score": rule.min_score,
                "reason": f"缺少{rule.name}内容",
                "suggestions": [f"请添加{rule.name}内容"],
                "details": {"value": ""}
            }
        
        # 基于长度的简单评分
        value_length = len(value.strip())
        if rule.scoring_ranges:
            score = self._calculate_score_from_ranges(value_length, rule.scoring_ranges)
        else:
            # 默认评分逻辑
            if value_length < 5:
                score = rule.min_score + 1
            elif value_length > 200:
                score = rule.max_score - 1
            else:
                score = (rule.min_score + rule.max_score) / 2
        
        score = max(rule.min_score, min(rule.max_score, score))
        
        return {
            "score": round(score, 2),
            "reason": f"{rule.name}内容长度{value_length}字符",
            "suggestions": [],
            "details": {"length": value_length}
        }
    
    def _calculate_score_from_ranges(self, value: float, scoring_ranges: List) -> float:
        """根据评分范围计算分数"""
        for scoring_range in scoring_ranges:
            if scoring_range.min_value <= value <= scoring_range.max_value:
                return scoring_range.score * scoring_range.weight_multiplier
        
        # 如果没有匹配的范围，返回中等分数
        return 5.0
    
    def _apply_scoring_strategy(self, base_score: float, dimension_scores: dict) -> float:
        """应用评分策略"""
        if self.current_profile.strategy == ScoringStrategy.STRICT:
            # 严格模式：降低分数
            return base_score * 0.9
        elif self.current_profile.strategy == ScoringStrategy.LENIENT:
            # 宽松模式：提高分数
            return min(10.0, base_score * 1.1)
        else:
            # 标准模式：保持原分数
            return base_score
    
    def _generate_improvement_suggestions(self, dimension_scores: dict) -> List[str]:
        """生成综合改进建议"""
        all_suggestions = []
        
        for dim_name, score_info in dimension_scores.items():
            if score_info["score"] < 7:
                dim_suggestions = [f"【{dim_name}】{s}" for s in score_info["suggestions"]]
                all_suggestions.extend(dim_suggestions)
        
        return all_suggestions[:10]  # 限制建议数量
    
    def _get_score_level_cn(self, score_level: ScoreLevel) -> str:
        """获取中文评分等级"""
        level_map = {
            ScoreLevel.EXCELLENT: "优秀",
            ScoreLevel.GOOD: "良好",
            ScoreLevel.FAIR: "及格",
            ScoreLevel.POOR: "需要改进"
        }
        return level_map.get(score_level, "未知")
    
    # 保持原有的辅助方法
    def _parse_precondition_items(self, precondition: str) -> List[str]:
        """解析前置条件项目"""
        lines = [line.strip() for line in precondition.split('\n') if line.strip()]
        items = []
        for line in lines:
            sub_items = re.split(r'[;；。]', line)
            items.extend([item.strip() for item in sub_items if item.strip()])
        return items
    
    def _parse_test_steps(self, steps: str) -> List[str]:
        """解析测试步骤"""
        lines = [line.strip() for line in steps.split('\n') if line.strip()]
        step_items = []
        for line in lines:
            clean_line = re.sub(r'^\d+[、。\.\)]\s*', '', line)
            if clean_line:
                step_items.append(clean_line)
        return step_items
    
    def _has_numbered_steps(self, steps: str) -> bool:
        """检查是否有数字编号"""
        return bool(re.search(r'^\d+[、。\.\)]', steps, re.MULTILINE))
    
    def _check_step_logic(self, steps: List[str]) -> bool:
        """检查步骤逻辑性"""
        has_operation = any(any(op in step for op in ["点击", "输入", "选择", "提交"]) for step in steps)
        return has_operation
    
    def _has_specific_verification_points(self, result: str) -> bool:
        """检查是否有具体的验证点"""
        specific_keywords = ["页面", "按钮", "文本", "消息", "数据", "状态", "错误", "成功", "失败", "显示", "隐藏"]
        return any(keyword in result for keyword in specific_keywords)
    
    async def score_batch_testcases(self, testcases: List[dict], 
                                  batch_size: int = 10,
                                  profile_name: str = None) -> dict:
        """批量评分测试用例"""
        if profile_name and profile_name != self.profile_name:
            await self.switch_profile(profile_name)
        
        if not self.current_profile:
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
                    batch_results.append({
                        "testcase_id": testcase.get("id", "unknown"),
                        "error": f"评分失败: {str(e)}",
                        "total_score": 0
                    })
                    processed_count += 1
            
            results.extend(batch_results)
            await asyncio.sleep(0.1)  # 短暂休息
        
        # 生成统计信息
        successful_scores = [r for r in results if "error" not in r]
        if successful_scores:
            scores = [r["total_score"] for r in successful_scores]
            avg_score = sum(scores) / len(scores)
            
            # 使用当前配置的阈值计算分布
            thresholds = self.current_profile.thresholds
            score_distribution = {
                "优秀": len([s for s in scores if s >= thresholds.excellent_min]),
                "良好": len([s for s in scores if thresholds.good_min <= s < thresholds.excellent_min]),
                "及格": len([s for s in scores if thresholds.fair_min <= s < thresholds.good_min]),
                "需要改进": len([s for s in scores if s < thresholds.fair_min])
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
            "profile_name": self.profile_name,
            "strategy": self.current_profile.strategy.value,
            "results": results,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# 全局增强评分器实例
_enhanced_scorer = None

async def get_enhanced_quality_scorer(profile_name: str = "default") -> EnhancedTestCaseQualityScorer:
    """获取增强的全局评分器实例"""
    global _enhanced_scorer
    if _enhanced_scorer is None:
        _enhanced_scorer = EnhancedTestCaseQualityScorer(profile_name)
        await _enhanced_scorer.initialize()
    elif _enhanced_scorer.profile_name != profile_name:
        await _enhanced_scorer.switch_profile(profile_name)
    return _enhanced_scorer