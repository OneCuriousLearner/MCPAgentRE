"""
增强的测试用例质量评分规则配置管理器
支持更灵活的自定义评分规则和多套评分标准
"""

import json
import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import asyncio


class ScoringStrategy(Enum):
    """评分策略枚举"""
    STRICT = "strict"      # 严格模式
    STANDARD = "standard"  # 标准模式
    LENIENT = "lenient"    # 宽松模式


class ScoreLevel(Enum):
    """评分等级枚举"""
    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"           # 良好
    FAIR = "fair"           # 及格
    POOR = "poor"           # 需要改进


@dataclass
class ScoringRange:
    """评分范围配置"""
    min_value: Union[int, float]
    max_value: Union[int, float]
    score: Union[int, float]
    description: str = ""
    weight_multiplier: float = 1.0  # 权重倍数，可用于动态调整
    
    def __post_init__(self):
        if self.min_value > self.max_value:
            raise ValueError(f"最小值 {self.min_value} 不能大于最大值 {self.max_value}")
        if not (0 <= self.score <= 10):
            raise ValueError(f"评分 {self.score} 必须在0-10之间")


@dataclass
class ScoreThresholds:
    """评分阈值配置"""
    excellent_min: float = 9.0    # 优秀最低分
    good_min: float = 7.0         # 良好最低分
    fair_min: float = 5.0         # 及格最低分
    poor_max: float = 4.9         # 需要改进最高分
    
    def __post_init__(self):
        # 验证阈值的逻辑性
        if not (self.poor_max < self.fair_min <= self.good_min <= self.excellent_min <= 10.0):
            raise ValueError("评分阈值设置不合理，应满足：poor_max < fair_min <= good_min <= excellent_min <= 10.0")
    
    def get_level(self, score: float) -> ScoreLevel:
        """根据分数获取等级"""
        if score >= self.excellent_min:
            return ScoreLevel.EXCELLENT
        elif score >= self.good_min:
            return ScoreLevel.GOOD
        elif score >= self.fair_min:
            return ScoreLevel.FAIR
        else:
            return ScoreLevel.POOR


@dataclass
class DimensionRule:
    """评分维度规则基类"""
    name: str
    weight: float
    enabled: bool = True
    min_score: float = 0.0
    max_score: float = 10.0
    scoring_ranges: List[ScoringRange] = field(default_factory=list)
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not (0 <= self.weight <= 1.0):
            raise ValueError(f"权重 {self.weight} 必须在0-1之间")
        if self.min_score >= self.max_score:
            raise ValueError(f"最小分数 {self.min_score} 不能大于等于最大分数 {self.max_score}")
    
    def validate_scoring_ranges(self) -> List[str]:
        """验证评分范围配置"""
        errors = []
        if not self.scoring_ranges:
            errors.append(f"维度 {self.name} 缺少评分范围配置")
            return errors
        
        # 检查范围是否有重叠
        sorted_ranges = sorted(self.scoring_ranges, key=lambda x: x.min_value)
        for i in range(len(sorted_ranges) - 1):
            if sorted_ranges[i].max_value >= sorted_ranges[i + 1].min_value:
                errors.append(f"维度 {self.name} 的评分范围存在重叠")
        
        return errors


@dataclass
class TitleRule(DimensionRule):
    """标题评分规则"""
    def __post_init__(self):
        super().__post_init__()
        if not self.custom_params:
            self.custom_params = {
                "max_length": 40,
                "min_length": 5,
                "require_action_words": True,
                "action_words": ["登录", "查询", "搜索", "创建", "删除", "修改", "更新", "添加", "上传", "下载", "提交", "取消", "确认", "验证", "检查", "测试"]
            }
        
        # 确保有默认的评分范围
        if not self.scoring_ranges:
            self.scoring_ranges = [
                ScoringRange(5, 20, 10, "简洁明了"),
                ScoringRange(21, 40, 8, "较为合适"),
                ScoringRange(41, 100, 5, "过长"),
                ScoringRange(0, 4, 3, "过短")
            ]


@dataclass
class PreconditionRule(DimensionRule):
    """前置条件评分规则"""
    def __post_init__(self):
        super().__post_init__()
        if not self.custom_params:
            self.custom_params = {
                "max_count": 2,
                "min_count": 0,
                "allow_empty": True,
                "vague_keywords": ["已经", "正常", "可用", "有效", "合法"]
            }
        
        # 确保有默认的评分范围
        if not self.scoring_ranges:
            self.scoring_ranges = [
                ScoringRange(1, 1, 10, "前置条件清晰"),
                ScoringRange(2, 2, 8, "前置条件较多但可接受"),
                ScoringRange(0, 0, 6, "缺少前置条件"),
                ScoringRange(3, 10, 4, "前置条件过多")
            ]


@dataclass
class StepsRule(DimensionRule):
    """测试步骤评分规则"""
    def __post_init__(self):
        super().__post_init__()
        if not self.custom_params:
            self.custom_params = {
                "min_steps": 1,
                "max_steps": 10,
                "require_numbered_steps": True,
                "require_logical_order": True,
                "vague_keywords": ["点击", "输入", "选择", "等待", "检查"]
            }
        
        # 确保有默认的评分范围
        if not self.scoring_ranges:
            self.scoring_ranges = [
                ScoringRange(2, 5, 10, "步骤数量合适"),
                ScoringRange(6, 8, 8, "步骤较多但可接受"),
                ScoringRange(1, 1, 7, "步骤过少"),
                ScoringRange(9, 20, 5, "步骤过多")
            ]


@dataclass
class ExpectedResultRule(DimensionRule):
    """预期结果评分规则"""
    def __post_init__(self):
        super().__post_init__()
        if not self.custom_params:
            self.custom_params = {
                "min_length": 5,
                "max_length": 200,
                "avoid_vague_terms": ["正常", "成功", "没问题", "可以", "应该"],
                "require_verification_points": True
            }
        
        # 确保有默认的评分范围
        if not self.scoring_ranges:
            self.scoring_ranges = [
                ScoringRange(5, 50, 10, "描述合适"),
                ScoringRange(51, 200, 8, "描述详细"),
                ScoringRange(0, 4, 3, "描述过短"),
                ScoringRange(201, 500, 5, "描述过长")
            ]


@dataclass
class PriorityRule(DimensionRule):
    """优先级评分规则"""
    def __post_init__(self):
        super().__post_init__()
        if not self.custom_params:
            self.custom_params = {
                "valid_priorities": ["P0", "P1", "P2", "P3"],
                "allow_custom_priorities": False,
                "case_sensitive": False
            }
        
        # 确保有默认的评分范围
        if not self.scoring_ranges:
            self.scoring_ranges = [
                ScoringRange(0, 3, 10, "优先级标准"),  # P0-P3对应0-3
                ScoringRange(4, 10, 5, "优先级非标准")
            ]


@dataclass
class ScoringProfile:
    """评分配置档案"""
    name: str
    description: str = ""
    strategy: ScoringStrategy = ScoringStrategy.STANDARD
    thresholds: ScoreThresholds = field(default_factory=ScoreThresholds)
    dimensions: Dict[str, DimensionRule] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    author: str = ""
    version: str = "1.0"
    
    def __post_init__(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = current_time
        self.updated_at = current_time
        
        # 初始化默认维度
        if not self.dimensions:
            self.dimensions = {
                "title": TitleRule("title", 0.2),
                "precondition": PreconditionRule("precondition", 0.15),
                "steps": StepsRule("steps", 0.25),
                "expected_result": ExpectedResultRule("expected_result", 0.25),
                "priority": PriorityRule("priority", 0.15)
            }
    
    def get_total_weight(self) -> float:
        """获取总权重"""
        return sum(dim.weight for dim in self.dimensions.values() if dim.enabled)
    
    def normalize_weights(self) -> None:
        """归一化权重"""
        total_weight = self.get_total_weight()
        if total_weight > 0:
            for dim in self.dimensions.values():
                if dim.enabled:
                    dim.weight = dim.weight / total_weight
    
    def validate(self) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 检查权重
        total_weight = self.get_total_weight()
        if abs(total_weight - 1.0) > 0.01:
            warnings.append(f"权重总和为 {total_weight:.3f}，建议调整为 1.0")
        
        # 检查维度配置
        for dim_name, dim_rule in self.dimensions.items():
            dim_errors = dim_rule.validate_scoring_ranges()
            errors.extend(dim_errors)
        
        # 检查是否有启用的维度
        enabled_dims = [dim for dim in self.dimensions.values() if dim.enabled]
        if not enabled_dims:
            errors.append("至少需要启用一个评分维度")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_weight": total_weight,
            "enabled_dimensions": len(enabled_dims)
        }


class EnhancedScoringConfigManager:
    """增强的评分配置管理器"""
    
    def __init__(self, config_dir: str = "local_data/scoring_profiles"):
        self.config_dir = config_dir
        self.current_profile: Optional[ScoringProfile] = None
        self.available_profiles: Dict[str, str] = {}  # name -> file_path
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
    
    async def load_profile(self, profile_name: str = "default") -> ScoringProfile:
        """加载评分配置档案"""
        profile_path = os.path.join(self.config_dir, f"{profile_name}.json")
        
        try:
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                self.current_profile = self._dict_to_profile(profile_data)
            else:
                # 创建默认配置
                self.current_profile = ScoringProfile(
                    name=profile_name,
                    description="默认评分配置",
                    strategy=ScoringStrategy.STANDARD
                )
                await self.save_profile(self.current_profile)
            
            return self.current_profile
        except Exception as e:
            print(f"加载配置档案失败，使用默认配置: {str(e)}")
            self.current_profile = ScoringProfile(name=profile_name)
            return self.current_profile
    
    async def save_profile(self, profile: ScoringProfile) -> None:
        """保存评分配置档案"""
        profile_path = os.path.join(self.config_dir, f"{profile.name}.json")
        
        try:
            profile_dict = self._profile_to_dict(profile)
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, ensure_ascii=False, indent=2)
            
            # 更新可用配置列表
            self.available_profiles[profile.name] = profile_path
            
        except Exception as e:
            raise Exception(f"保存配置档案失败: {str(e)}")
    
    async def create_profile(self, name: str, description: str = "", 
                           strategy: ScoringStrategy = ScoringStrategy.STANDARD,
                           base_profile: Optional[str] = None) -> ScoringProfile:
        """创建新的评分配置档案"""
        if base_profile and base_profile in self.available_profiles:
            # 基于现有配置创建
            base = await self.load_profile(base_profile)
            profile = ScoringProfile(
                name=name,
                description=description,
                strategy=strategy,
                thresholds=base.thresholds,
                dimensions=base.dimensions.copy()
            )
        else:
            # 创建全新配置
            profile = ScoringProfile(
                name=name,
                description=description,
                strategy=strategy
            )
        
        await self.save_profile(profile)
        return profile
    
    async def list_profiles(self) -> List[Dict[str, Any]]:
        """列出所有可用的评分配置档案"""
        profiles = []
        
        for filename in os.listdir(self.config_dir):
            if filename.endswith('.json'):
                profile_path = os.path.join(self.config_dir, filename)
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                    
                    profiles.append({
                        "name": profile_data.get("name", filename[:-5]),
                        "description": profile_data.get("description", ""),
                        "strategy": profile_data.get("strategy", "standard"),
                        "created_at": profile_data.get("created_at", ""),
                        "updated_at": profile_data.get("updated_at", ""),
                        "author": profile_data.get("author", ""),
                        "version": profile_data.get("version", "1.0")
                    })
                except Exception as e:
                    print(f"读取配置档案 {filename} 失败: {str(e)}")
        
        return profiles
    
    async def delete_profile(self, profile_name: str) -> bool:
        """删除评分配置档案"""
        if profile_name == "default":
            raise ValueError("不能删除默认配置档案")
        
        profile_path = os.path.join(self.config_dir, f"{profile_name}.json")
        if os.path.exists(profile_path):
            os.remove(profile_path)
            self.available_profiles.pop(profile_name, None)
            return True
        return False
    
    def _profile_to_dict(self, profile: ScoringProfile) -> Dict[str, Any]:
        """将配置档案转换为字典"""
        dimensions_dict = {}
        for dim_name, dim_rule in profile.dimensions.items():
            dimensions_dict[dim_name] = {
                "name": dim_rule.name,
                "weight": dim_rule.weight,
                "enabled": dim_rule.enabled,
                "min_score": dim_rule.min_score,
                "max_score": dim_rule.max_score,
                "scoring_ranges": [asdict(sr) for sr in dim_rule.scoring_ranges],
                "custom_params": dim_rule.custom_params
            }
        
        return {
            "name": profile.name,
            "description": profile.description,
            "strategy": profile.strategy.value,
            "thresholds": asdict(profile.thresholds),
            "dimensions": dimensions_dict,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "author": profile.author,
            "version": profile.version
        }
    
    def _dict_to_profile(self, profile_dict: Dict[str, Any]) -> ScoringProfile:
        """将字典转换为配置档案"""
        # 转换阈值
        thresholds_data = profile_dict.get("thresholds", {})
        thresholds = ScoreThresholds(**thresholds_data)
        
        # 转换维度规则
        dimensions = {}
        dimensions_data = profile_dict.get("dimensions", {})
        
        for dim_name, dim_data in dimensions_data.items():
            # 转换评分范围
            scoring_ranges = []
            for sr_data in dim_data.get("scoring_ranges", []):
                scoring_ranges.append(ScoringRange(**sr_data))
            
            # 根据维度类型创建相应的规则对象
            if dim_name == "title":
                dim_rule = TitleRule(
                    name=dim_data["name"],
                    weight=dim_data["weight"],
                    enabled=dim_data.get("enabled", True),
                    min_score=dim_data.get("min_score", 0.0),
                    max_score=dim_data.get("max_score", 10.0),
                    scoring_ranges=scoring_ranges,
                    custom_params=dim_data.get("custom_params", {})
                )
            elif dim_name == "precondition":
                dim_rule = PreconditionRule(
                    name=dim_data["name"],
                    weight=dim_data["weight"],
                    enabled=dim_data.get("enabled", True),
                    min_score=dim_data.get("min_score", 0.0),
                    max_score=dim_data.get("max_score", 10.0),
                    scoring_ranges=scoring_ranges,
                    custom_params=dim_data.get("custom_params", {})
                )
            elif dim_name == "steps":
                dim_rule = StepsRule(
                    name=dim_data["name"],
                    weight=dim_data["weight"],
                    enabled=dim_data.get("enabled", True),
                    min_score=dim_data.get("min_score", 0.0),
                    max_score=dim_data.get("max_score", 10.0),
                    scoring_ranges=scoring_ranges,
                    custom_params=dim_data.get("custom_params", {})
                )
            elif dim_name == "expected_result":
                dim_rule = ExpectedResultRule(
                    name=dim_data["name"],
                    weight=dim_data["weight"],
                    enabled=dim_data.get("enabled", True),
                    min_score=dim_data.get("min_score", 0.0),
                    max_score=dim_data.get("max_score", 10.0),
                    scoring_ranges=scoring_ranges,
                    custom_params=dim_data.get("custom_params", {})
                )
            elif dim_name == "priority":
                dim_rule = PriorityRule(
                    name=dim_data["name"],
                    weight=dim_data["weight"],
                    enabled=dim_data.get("enabled", True),
                    min_score=dim_data.get("min_score", 0.0),
                    max_score=dim_data.get("max_score", 10.0),
                    scoring_ranges=scoring_ranges,
                    custom_params=dim_data.get("custom_params", {})
                )
            else:
                # 通用维度规则
                dim_rule = DimensionRule(
                    name=dim_data["name"],
                    weight=dim_data["weight"],
                    enabled=dim_data.get("enabled", True),
                    min_score=dim_data.get("min_score", 0.0),
                    max_score=dim_data.get("max_score", 10.0),
                    scoring_ranges=scoring_ranges,
                    custom_params=dim_data.get("custom_params", {})
                )
            
            dimensions[dim_name] = dim_rule
        
        return ScoringProfile(
            name=profile_dict.get("name", "default"),
            description=profile_dict.get("description", ""),
            strategy=ScoringStrategy(profile_dict.get("strategy", "standard")),
            thresholds=thresholds,
            dimensions=dimensions,
            created_at=profile_dict.get("created_at", ""),
            updated_at=profile_dict.get("updated_at", ""),
            author=profile_dict.get("author", ""),
            version=profile_dict.get("version", "1.0")
        )


# 全局配置管理器实例
_enhanced_config_manager = None

async def get_enhanced_config_manager() -> EnhancedScoringConfigManager:
    """获取增强的全局配置管理器实例"""
    global _enhanced_config_manager
    if _enhanced_config_manager is None:
        _enhanced_config_manager = EnhancedScoringConfigManager()
    return _enhanced_config_manager