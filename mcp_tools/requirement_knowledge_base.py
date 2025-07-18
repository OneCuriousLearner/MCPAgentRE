"""
历史需求知识库系统

为新测试用例编写提供历史需求参考和智能推荐
支持需求存储、语义搜索、关联分析和测试用例模板推荐
"""

import json
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys
import re

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.common_utils import (
    get_config, get_api_manager, get_file_manager, 
    get_model_manager, get_text_processor
)


class RequirementKnowledgeBase:
    """历史需求知识库管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.file_manager = get_file_manager()
        self.api_manager = get_api_manager()
        self.model_manager = get_model_manager()
        self.text_processor = get_text_processor()
        
        # 知识库文件路径
        self.knowledge_base_file = self.config.local_data_path / "requirement_knowledge_base.json"
        self.evolution_map_file = self.config.local_data_path / "feature_evolution_map.json"
        self.test_templates_file = self.config.local_data_path / "test_case_templates.json"
        
        # 向量数据库文件
        self.vector_db_path = self.config.local_data_path / "kb_vector_data"
        self.vector_db_path.mkdir(exist_ok=True)
        
        # 初始化知识库
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """初始化知识库结构"""
        # 创建基础知识库结构
        if not self.knowledge_base_file.exists():
            initial_kb = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "requirements": [],
                "metadata": {
                    "total_requirements": 0,
                    "feature_types": [],
                    "last_updated": datetime.now().isoformat()
                }
            }
            self.file_manager.save_json_data(initial_kb, str(self.knowledge_base_file))
        
        # 创建功能演化图谱
        if not self.evolution_map_file.exists():
            initial_evolution = {
                "feature_evolution": {},
                "evolution_patterns": [],
                "common_changes": []
            }
            self.file_manager.save_json_data(initial_evolution, str(self.evolution_map_file))
        
        # 创建测试用例模板库
        if not self.test_templates_file.exists():
            initial_templates = {
                "templates": [],
                "template_categories": {},
                "usage_statistics": {}
            }
            self.file_manager.save_json_data(initial_templates, str(self.test_templates_file))
    
    def add_requirement_to_knowledge_base(self, requirement_data: Dict[str, Any]) -> bool:
        """
        添加需求到知识库
        
        参数:
            requirement_data: 需求数据，包含必要的字段
            
        返回:
            bool: 是否成功添加
        """
        try:
            # 验证必要字段
            required_fields = ["req_id", "title", "description", "feature_type"]
            for field in required_fields:
                if field not in requirement_data:
                    raise ValueError(f"缺少必要字段: {field}")
            
            # 加载当前知识库
            kb_data = self.file_manager.load_json_data(str(self.knowledge_base_file))
            
            # 检查是否已存在
            existing_req = next(
                (req for req in kb_data["requirements"] if req["req_id"] == requirement_data["req_id"]), 
                None
            )
            
            if existing_req:
                # 更新现有需求
                existing_req.update(requirement_data)
                existing_req["last_updated"] = datetime.now().isoformat()
                print(f"更新现有需求: {requirement_data['req_id']}")
            else:
                # 添加新需求
                requirement_data["created_at"] = datetime.now().isoformat()
                requirement_data["last_updated"] = datetime.now().isoformat()
                kb_data["requirements"].append(requirement_data)
                print(f"添加新需求: {requirement_data['req_id']}")
            
            # 更新元数据
            kb_data["metadata"]["total_requirements"] = len(kb_data["requirements"])
            kb_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # 更新特性类型列表
            all_types = set(req.get("feature_type", "") for req in kb_data["requirements"])
            kb_data["metadata"]["feature_types"] = list(all_types)
            
            # 保存知识库
            self.file_manager.save_json_data(kb_data, str(self.knowledge_base_file))
            
            return True
            
        except Exception as e:
            print(f"添加需求到知识库失败: {str(e)}")
            return False
    
    def search_similar_requirements(self, query: str, feature_type: str = None, 
                                  top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相似需求
        
        参数:
            query: 搜索查询
            feature_type: 功能类型过滤
            top_k: 返回结果数量
            
        返回:
            相似需求列表
        """
        try:
            # 加载知识库
            kb_data = self.file_manager.load_json_data(str(self.knowledge_base_file))
            requirements = kb_data["requirements"]
            
            if not requirements:
                return []
            
            # 按功能类型过滤
            if feature_type:
                requirements = [req for req in requirements if req.get("feature_type") == feature_type]
            
            # 构建搜索文本
            search_candidates = []
            for req in requirements:
                # 组合标题、描述和关键词进行搜索
                search_text = f"{req['title']} {req['description']} "
                search_text += " ".join(req.get("technical_keywords", []))
                search_text += " ".join(req.get("business_scenario", []))
                
                search_candidates.append({
                    "requirement": req,
                    "search_text": search_text
                })
            
            # 使用语义搜索
            results = self._semantic_search(query, search_candidates, top_k)
            
            return results
            
        except Exception as e:
            print(f"搜索相似需求失败: {str(e)}")
            return []
    
    def _semantic_search(self, query: str, candidates: List[Dict], top_k: int) -> List[Dict[str, Any]]:
        """
        执行语义搜索
        
        参数:
            query: 搜索查询
            candidates: 候选项列表
            top_k: 返回数量
            
        返回:
            搜索结果
        """
        try:
            # 简单的关键词匹配搜索（可以后续升级为向量搜索）
            results = []
            query_lower = query.lower()
            query_keywords = set(re.findall(r'\w+', query_lower))
            
            for candidate in candidates:
                text_lower = candidate["search_text"].lower()
                text_keywords = set(re.findall(r'\w+', text_lower))
                
                # 计算关键词匹配度
                common_keywords = query_keywords.intersection(text_keywords)
                if common_keywords:
                    match_score = len(common_keywords) / len(query_keywords)
                    results.append({
                        "requirement": candidate["requirement"],
                        "match_score": match_score,
                        "matched_keywords": list(common_keywords)
                    })
            
            # 按匹配度排序
            results.sort(key=lambda x: x["match_score"], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"语义搜索失败: {str(e)}")
            return []
    
    def get_requirement_evolution_path(self, feature_id: str) -> Dict[str, Any]:
        """
        获取需求演化路径
        
        参数:
            feature_id: 功能ID
            
        返回:
            演化路径信息
        """
        try:
            evolution_data = self.file_manager.load_json_data(str(self.evolution_map_file))
            
            if feature_id in evolution_data["feature_evolution"]:
                return evolution_data["feature_evolution"][feature_id]
            else:
                return {"message": f"未找到功能 {feature_id} 的演化路径"}
                
        except Exception as e:
            print(f"获取演化路径失败: {str(e)}")
            return {"error": str(e)}
    
    def update_requirement_evolution(self, feature_id: str, evolution_data: Dict[str, Any]) -> bool:
        """
        更新需求演化记录
        
        参数:
            feature_id: 功能ID
            evolution_data: 演化数据
            
        返回:
            bool: 是否成功更新
        """
        try:
            # 加载演化图谱
            evolution_map = self.file_manager.load_json_data(str(self.evolution_map_file))
            
            # 更新演化数据
            evolution_map["feature_evolution"][feature_id] = evolution_data
            
            # 保存更新
            self.file_manager.save_json_data(evolution_map, str(self.evolution_map_file))
            
            print(f"更新功能 {feature_id} 的演化记录")
            return True
            
        except Exception as e:
            print(f"更新演化记录失败: {str(e)}")
            return False
    
    async def recommend_test_cases_for_requirement(self, requirement_data: Dict[str, Any], 
                                                 use_ai: bool = True) -> List[Dict[str, Any]]:
        """
        为需求推荐测试用例
        
        参数:
            requirement_data: 需求数据
            use_ai: 是否使用AI推荐
            
        返回:
            推荐的测试用例列表
        """
        try:
            recommendations = []
            
            # 1. 基于相似需求的推荐
            similar_reqs = self.search_similar_requirements(
                requirement_data.get("description", ""), 
                requirement_data.get("feature_type"),
                top_k=3
            )
            
            for sim_req in similar_reqs:
                req_data = sim_req["requirement"]
                if "test_case_templates" in req_data:
                    for template in req_data["test_case_templates"]:
                        recommendations.append({
                            "source": "similar_requirement",
                            "source_req_id": req_data["req_id"],
                            "template": template,
                            "match_score": sim_req["match_score"]
                        })
            
            # 2. AI智能推荐
            if use_ai:
                ai_recommendations = await self._generate_ai_test_recommendations(requirement_data)
                recommendations.extend(ai_recommendations)
            
            # 3. 基于模板库的推荐
            template_recommendations = self._get_template_recommendations(requirement_data)
            recommendations.extend(template_recommendations)
            
            return recommendations
            
        except Exception as e:
            print(f"推荐测试用例失败: {str(e)}")
            return []
    
    async def _generate_ai_test_recommendations(self, requirement_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        使用AI生成测试用例推荐
        
        参数:
            requirement_data: 需求数据
            
        返回:
            AI推荐的测试用例列表
        """
        try:
            # 构建AI推荐的提示词
            prompt = f"""
基于以下需求信息，请推荐相关的测试场景和测试用例框架：

需求标题: {requirement_data.get('title', '')}
需求描述: {requirement_data.get('description', '')}
功能类型: {requirement_data.get('feature_type', '')}
技术关键词: {', '.join(requirement_data.get('technical_keywords', []))}
业务场景: {', '.join(requirement_data.get('business_scenario', []))}

请返回JSON格式的测试用例推荐，包含：
1. 正常流程测试场景
2. 异常处理测试场景
3. 边界条件测试场景
4. 性能和安全测试考虑点

格式如下：
{{
    "recommendations": [
        {{
            "scenario": "测试场景名称",
            "test_type": "功能测试/异常测试/边界测试/性能测试/安全测试",
            "title_template": "测试用例标题模板",
            "steps_template": ["步骤1", "步骤2", "步骤3"],
            "expected_template": "预期结果模板",
            "test_data_requirements": "测试数据要求",
            "priority": "P0/P1/P2"
        }}
    ]
}}
"""
            
            # 调用AI API
            async with aiohttp.ClientSession() as session:
                ai_response = await self.api_manager.call_llm(
                    prompt=prompt,
                    session=session,
                    max_tokens=2000
                )
            
            # 解析AI返回结果
            try:
                ai_data = json.loads(ai_response)
                ai_recommendations = []
                
                for rec in ai_data.get("recommendations", []):
                    ai_recommendations.append({
                        "source": "ai_recommendation",
                        "template": rec,
                        "match_score": 1.0  # AI推荐给最高分
                    })
                
                return ai_recommendations
                
            except json.JSONDecodeError:
                print("AI返回结果解析失败，使用文本解析")
                return self._parse_ai_text_response(ai_response)
                
        except Exception as e:
            print(f"AI推荐失败: {str(e)}")
            return []
    
    def _parse_ai_text_response(self, ai_response: str) -> List[Dict[str, Any]]:
        """
        解析AI的文本回复
        
        参数:
            ai_response: AI返回的文本
            
        返回:
            解析后的推荐列表
        """
        # 简单的文本解析逻辑
        recommendations = []
        
        # 查找测试场景
        scenarios = re.findall(r'场景[：:]?\s*(.+)', ai_response)
        for scenario in scenarios:
            recommendations.append({
                "source": "ai_text_recommendation",
                "template": {
                    "scenario": scenario.strip(),
                    "test_type": "功能测试",
                    "title_template": f"验证{scenario.strip()}",
                    "steps_template": ["待细化"],
                    "expected_template": "功能正常",
                    "priority": "P1"
                },
                "match_score": 0.8
            })
        
        return recommendations
    
    def _get_template_recommendations(self, requirement_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        基于模板库获取推荐
        
        参数:
            requirement_data: 需求数据
            
        返回:
            模板推荐列表
        """
        try:
            template_data = self.file_manager.load_json_data(str(self.test_templates_file))
            recommendations = []
            
            feature_type = requirement_data.get("feature_type", "")
            
            # 查找匹配的模板
            for template in template_data["templates"]:
                if template.get("applicable_features"):
                    if feature_type in template["applicable_features"]:
                        recommendations.append({
                            "source": "template_library",
                            "template": template,
                            "match_score": 0.9
                        })
            
            return recommendations
            
        except Exception as e:
            print(f"模板推荐失败: {str(e)}")
            return []
    
    def analyze_requirement_test_coverage(self, requirement_id: str) -> Dict[str, Any]:
        """
        分析需求的测试覆盖度
        
        参数:
            requirement_id: 需求ID
            
        返回:
            覆盖度分析结果
        """
        try:
            # 加载知识库
            kb_data = self.file_manager.load_json_data(str(self.knowledge_base_file))
            
            # 找到目标需求
            target_req = next(
                (req for req in kb_data["requirements"] if req["req_id"] == requirement_id), 
                None
            )
            
            if not target_req:
                return {"error": f"未找到需求 {requirement_id}"}
            
            # 分析覆盖度
            coverage_analysis = {
                "requirement_id": requirement_id,
                "requirement_title": target_req["title"],
                "test_case_count": len(target_req.get("test_case_templates", [])),
                "coverage_areas": [],
                "missing_areas": [],
                "recommendations": []
            }
            
            # 分析已有测试用例覆盖的领域
            existing_templates = target_req.get("test_case_templates", [])
            covered_types = set()
            
            for template in existing_templates:
                test_type = template.get("test_type", "功能测试")
                covered_types.add(test_type)
                coverage_analysis["coverage_areas"].append({
                    "scenario": template.get("scenario", ""),
                    "test_type": test_type
                })
            
            # 识别缺失的测试类型
            standard_test_types = ["功能测试", "异常测试", "边界测试", "性能测试", "安全测试"]
            missing_types = [t for t in standard_test_types if t not in covered_types]
            coverage_analysis["missing_areas"] = missing_types
            
            # 生成建议
            for missing_type in missing_types:
                coverage_analysis["recommendations"].append(
                    f"建议添加{missing_type}相关的测试用例"
                )
            
            return coverage_analysis
            
        except Exception as e:
            print(f"覆盖度分析失败: {str(e)}")
            return {"error": str(e)}
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        返回:
            知识库统计数据
        """
        try:
            kb_data = self.file_manager.load_json_data(str(self.knowledge_base_file))
            evolution_data = self.file_manager.load_json_data(str(self.evolution_map_file))
            template_data = self.file_manager.load_json_data(str(self.test_templates_file))
            
            stats = {
                "total_requirements": len(kb_data["requirements"]),
                "feature_types": kb_data["metadata"]["feature_types"],
                "evolution_features": len(evolution_data["feature_evolution"]),
                "template_count": len(template_data["templates"]),
                "last_updated": kb_data["metadata"]["last_updated"]
            }
            
            # 按功能类型统计
            type_stats = {}
            for req in kb_data["requirements"]:
                feature_type = req.get("feature_type", "未分类")
                type_stats[feature_type] = type_stats.get(feature_type, 0) + 1
            
            stats["requirements_by_type"] = type_stats
            
            return stats
            
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
            return {"error": str(e)}


# 异步辅助函数
async def build_knowledge_base_from_tapd_data(data_file_path: str = None) -> Dict[str, Any]:
    """
    从TAPD数据构建知识库
    
    参数:
        data_file_path: TAPD数据文件路径
        
    返回:
        构建结果
    """
    try:
        kb = RequirementKnowledgeBase()
        
        if data_file_path is None:
            data_file_path = str(kb.config.local_data_path / "msg_from_fetcher.json")
        
        # 加载TAPD数据
        tapd_data = kb.file_manager.load_json_data(data_file_path)
        
        # 处理需求数据
        processed_count = 0
        for story in tapd_data.get("stories", []):
            # 转换TAPD需求为知识库格式
            requirement_data = {
                "req_id": f"TAPD_STORY_{story.get('id', '')}",
                "title": story.get('name', ''),
                "description": story.get('description', ''),
                "feature_type": story.get('category_name', '功能需求'),
                "complexity": story.get('priority', '中等'),
                "business_scenario": [story.get('category_name', '')],
                "technical_keywords": kb.text_processor.extract_keywords(story.get('description', '')),
                "change_history": [],
                "related_requirements": [],
                "test_case_templates": []
            }
            
            # 添加到知识库
            if kb.add_requirement_to_knowledge_base(requirement_data):
                processed_count += 1
        
        return {
            "success": True,
            "processed_count": processed_count,
            "total_stories": len(tapd_data.get("stories", [])),
            "message": f"成功构建知识库，处理了 {processed_count} 个需求"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"构建知识库失败: {str(e)}"
        }


if __name__ == "__main__":
    # 测试知识库功能
    async def test_knowledge_base():
        # 测试添加需求
        kb = RequirementKnowledgeBase()
        
        test_requirement = {
            "req_id": "REQ_LOGIN_001",
            "title": "用户登录功能",
            "description": "支持手机号、邮箱登录，包含密码强度验证和多因子认证",
            "feature_type": "认证授权",
            "complexity": "中等",
            "business_scenario": ["用户管理", "安全验证"],
            "technical_keywords": ["登录", "验证", "Token", "Session", "MFA"],
            "change_history": [],
            "related_requirements": [],
            "test_case_templates": [
                {
                    "scenario": "正常登录流程",
                    "test_type": "功能测试",
                    "title_template": "验证{登录方式}正常登录功能",
                    "steps_template": ["打开登录页面", "输入有效凭证", "点击登录", "验证跳转"],
                    "expected_template": "成功登录并跳转到主页",
                    "priority": "P0"
                }
            ]
        }
        
        # 添加需求
        success = kb.add_requirement_to_knowledge_base(test_requirement)
        print(f"添加需求结果: {success}")
        
        # 搜索相似需求
        similar_reqs = kb.search_similar_requirements("用户登录验证")
        print(f"相似需求数量: {len(similar_reqs)}")
        
        # 推荐测试用例
        recommendations = await kb.recommend_test_cases_for_requirement(test_requirement)
        print(f"推荐测试用例数量: {len(recommendations)}")
        
        # 统计信息
        stats = kb.get_knowledge_base_stats()
        print(f"知识库统计: {stats}")
    
    # 运行测试
    asyncio.run(test_knowledge_base())