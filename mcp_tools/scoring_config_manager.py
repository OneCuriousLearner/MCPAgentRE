"""
测试用例质量评分规则配置管理器
支持自定义评分规则和动态配置管理
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio


@dataclass
class ScoringRange:
    """评分范围配置"""
    min_value: int
    max_value: int
    score: int
    description: str = ""


@dataclass
class TitleRule:
    """标题评分规则"""
    max_length: int = 40
    min_length: int = 5
    weight: float = 0.2
    scoring_ranges: List[ScoringRange] = None
    
    def __post_init__(self):
        if self.scoring_ranges is None:
            self.scoring_ranges = [
                ScoringRange(5, 20, 10, "简洁明了"),
                ScoringRange(21, 40, 8, "较为合适"),
                ScoringRange(41, 100, 5, "过长"),
                ScoringRange(0, 4, 3, "过短")
            ]


@dataclass
class PreconditionRule:
    """前置条件评分规则"""
    max_count: int = 2
    min_count: int = 0
    weight: float = 0.15
    scoring_ranges: List[ScoringRange] = None
    
    def __post_init__(self):
        if self.scoring_ranges is None:
            self.scoring_ranges = [
                ScoringRange(1, 1, 10, "前置条件清晰"),
                ScoringRange(2, 2, 8, "前置条件较多但可接受"),
                ScoringRange(0, 0, 6, "缺少前置条件"),
                ScoringRange(3, 10, 4, "前置条件过多")
            ]


@dataclass
class StepsRule:
    """测试步骤评分规则"""
    min_steps: int = 1
    max_steps: int = 10
    weight: float = 0.25
    require_numbered_steps: bool = True
    scoring_ranges: List[ScoringRange] = None
    
    def __post_init__(self):
        if self.scoring_ranges is None:
            self.scoring_ranges = [
                ScoringRange(2, 5, 10, "步骤数量合适"),
                ScoringRange(6, 8, 8, "步骤较多但可接受"),
                ScoringRange(1, 1, 7, "步骤过少"),
                ScoringRange(9, 20, 5, "步骤过多")
            ]


@dataclass
class ExpectedResultRule:
    """预期结果评分规则"""
    min_length: int = 5
    max_length: int = 200
    weight: float = 0.25
    avoid_vague_terms: List[str] = None
    
    def __post_init__(self):
        if self.avoid_vague_terms is None:
            self.avoid_vague_terms = ["正常", "成功", "没问题", "可以", "应该"]


@dataclass
class PriorityRule:
    """优先级评分规则"""
    weight: float = 0.15
    valid_priorities: List[str] = None
    
    def __post_init__(self):
        if self.valid_priorities is None:
            self.valid_priorities = ["P0", "P1", "P2", "P3"]


@dataclass
class ScoringConfig:
    """完整的评分配置"""
    version: str = "1.0"
    title_rule: TitleRule = None
    precondition_rule: PreconditionRule = None
    steps_rule: StepsRule = None
    expected_result_rule: ExpectedResultRule = None
    priority_rule: PriorityRule = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.title_rule is None:
            self.title_rule = TitleRule()
        if self.precondition_rule is None:
            self.precondition_rule = PreconditionRule()
        if self.steps_rule is None:
            self.steps_rule = StepsRule()
        if self.expected_result_rule is None:
            self.expected_result_rule = ExpectedResultRule()
        if self.priority_rule is None:
            self.priority_rule = PriorityRule()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time


class ScoringConfigManager:
    """评分配置管理器"""
    
    def __init__(self, config_path: str = "local_data/scoring_config.json"):
        self.config_path = config_path
        self.config: Optional[ScoringConfig] = None
        
    async def load_config(self) -> ScoringConfig:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = self._dict_to_config(config_data)
            else:
                # 如果配置文件不存在，创建默认配置
                self.config = ScoringConfig()
                await self.save_config()
                
            return self.config
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {str(e)}")
            self.config = ScoringConfig()
            return self.config
    
    async def save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            dir_path = os.path.dirname(self.config_path)
            if dir_path:  # 只有当目录路径不为空时才创建
                os.makedirs(dir_path, exist_ok=True)
            
            # 转换为字典并保存
            config_dict = self._config_to_dict(self.config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"保存配置失败: {str(e)}")
    
    def _config_to_dict(self, config: ScoringConfig) -> dict:
        """将配置对象转换为字典"""
        return {
            "version": config.version,
            "title_rule": asdict(config.title_rule),
            "precondition_rule": asdict(config.precondition_rule),
            "steps_rule": asdict(config.steps_rule),
            "expected_result_rule": asdict(config.expected_result_rule),
            "priority_rule": asdict(config.priority_rule),
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }
    
    def _dict_to_config(self, config_dict: dict) -> ScoringConfig:
        """将字典转换为配置对象"""
        # 转换scoring_ranges
        def convert_scoring_ranges(ranges_data):
            if not ranges_data:
                return None
            return [ScoringRange(**range_data) for range_data in ranges_data]
        
        title_data = config_dict.get("title_rule", {})
        if "scoring_ranges" in title_data:
            title_data["scoring_ranges"] = convert_scoring_ranges(title_data["scoring_ranges"])
        
        precondition_data = config_dict.get("precondition_rule", {})
        if "scoring_ranges" in precondition_data:
            precondition_data["scoring_ranges"] = convert_scoring_ranges(precondition_data["scoring_ranges"])
        
        steps_data = config_dict.get("steps_rule", {})
        if "scoring_ranges" in steps_data:
            steps_data["scoring_ranges"] = convert_scoring_ranges(steps_data["scoring_ranges"])
        
        return ScoringConfig(
            version=config_dict.get("version", "1.0"),
            title_rule=TitleRule(**title_data),
            precondition_rule=PreconditionRule(**precondition_data),
            steps_rule=StepsRule(**steps_data),
            expected_result_rule=ExpectedResultRule(**config_dict.get("expected_result_rule", {})),
            priority_rule=PriorityRule(**config_dict.get("priority_rule", {})),
            created_at=config_dict.get("created_at", ""),
            updated_at=config_dict.get("updated_at", "")
        )
    
    async def update_rule(self, rule_name: str, rule_config: dict):
        """更新特定规则"""
        if not self.config:
            await self.load_config()
        
        if rule_name == "title":
            self.config.title_rule = TitleRule(**rule_config)
        elif rule_name == "precondition":
            self.config.precondition_rule = PreconditionRule(**rule_config)
        elif rule_name == "steps":
            self.config.steps_rule = StepsRule(**rule_config)
        elif rule_name == "expected_result":
            self.config.expected_result_rule = ExpectedResultRule(**rule_config)
        elif rule_name == "priority":
            self.config.priority_rule = PriorityRule(**rule_config)
        else:
            raise ValueError(f"未知的规则类型: {rule_name}")
        
        # 更新时间戳
        self.config.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        await self.save_config()
    
    async def get_config_summary(self) -> dict:
        """获取配置摘要"""
        if not self.config:
            await self.load_config()
        
        return {
            "version": self.config.version,
            "created_at": self.config.created_at,
            "updated_at": self.config.updated_at,
            "rules_summary": {
                "title": {
                    "max_length": self.config.title_rule.max_length,
                    "weight": self.config.title_rule.weight
                },
                "precondition": {
                    "max_count": self.config.precondition_rule.max_count,
                    "weight": self.config.precondition_rule.weight
                },
                "steps": {
                    "min_steps": self.config.steps_rule.min_steps,
                    "max_steps": self.config.steps_rule.max_steps,
                    "weight": self.config.steps_rule.weight
                },
                "expected_result": {
                    "weight": self.config.expected_result_rule.weight
                },
                "priority": {
                    "weight": self.config.priority_rule.weight,
                    "valid_priorities": self.config.priority_rule.valid_priorities
                }
            }
        }
    
    async def validate_config(self, config_dict: dict) -> dict:
        """验证配置的有效性"""
        errors = []
        warnings = []
        
        try:
            # 验证权重总和
            total_weight = 0
            for rule_name in ["title_rule", "precondition_rule", "steps_rule", "expected_result_rule", "priority_rule"]:
                if rule_name in config_dict:
                    weight = config_dict[rule_name].get("weight", 0)
                    total_weight += weight
            
            if abs(total_weight - 1.0) > 0.01:
                warnings.append(f"权重总和为 {total_weight:.2f}，建议调整为 1.0")
            
            # 验证数值范围
            if "title_rule" in config_dict:
                title_rule = config_dict["title_rule"]
                if title_rule.get("max_length", 0) <= 0:
                    errors.append("标题最大长度必须大于0")
                if title_rule.get("min_length", 0) < 0:
                    errors.append("标题最小长度不能小于0")
            
            # 验证评分范围
            for rule_name in ["title_rule", "precondition_rule", "steps_rule"]:
                if rule_name in config_dict and "scoring_ranges" in config_dict[rule_name]:
                    ranges = config_dict[rule_name]["scoring_ranges"]
                    for i, range_data in enumerate(ranges):
                        if range_data.get("min_value", 0) > range_data.get("max_value", 0):
                            errors.append(f"{rule_name} 第{i+1}个评分范围的最小值大于最大值")
                        if not (0 <= range_data.get("score", 0) <= 10):
                            errors.append(f"{rule_name} 第{i+1}个评分范围的分数必须在0-10之间")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"配置验证失败: {str(e)}"],
                "warnings": []
            }
    
    async def reset_to_default(self):
        """重置为默认配置"""
        self.config = ScoringConfig()
        await self.save_config()
        return self.config


# 全局配置管理器实例
_config_manager = None

async def get_config_manager() -> ScoringConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ScoringConfigManager()
    return _config_manager