#!/usr/bin/env python3
"""
TAPD数据精确搜索工具

此模块提供了强大的TAPD数据搜索功能，支持对需求和缺陷进行精确匹配搜索。
支持多种搜索条件和过滤选项，提供灵活的数据检索能力。

功能特性：
1. 精确字段匹配搜索
2. 优先级筛选
3. 状态筛选
4. 时间范围筛选
5. 创建者筛选
6. 模糊搜索支持
7. 搜索结果排序和分页
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from .common_utils import get_file_manager


class TAPDDataPreciseSearcher:
    """TAPD数据精确搜索器"""
    
    def __init__(self):
        self.file_manager = get_file_manager()
        
        # 需求字段映射
        self.story_fields = {
            'id': 'ID',
            'name': '需求名称',
            'description': '需求描述',
            'creator': '创建者',
            'priority': '优先级数值',
            'priority_label': '优先级标签',
            'status': '状态',
            'created': '创建时间',
            'modified': '修改时间',
            'begin': '开始时间',
            'due': '截止时间',
            'workspace_id': '工作空间ID',
            'parent_id': '父级ID',
            'level': '层级',
            'progress': '进度'
        }
        
        # 缺陷字段映射
        self.bug_fields = {
            'id': 'ID',
            'title': '缺陷标题',
            'description': '缺陷描述',
            'reporter': '报告者',
            'priority': '优先级',
            'priority_label': '优先级标签',
            'severity': '严重程度',
            'status': '状态',
            'created': '创建时间',
            'modified': '修改时间',
            'lastmodify': '最后修改者',
            'current_owner': '当前处理人',
            'fixer': '修复者',
            'workspace_id': '工作空间ID'
        }
        
        # 优先级映射（数字越大越紧急）
        self.priority_mapping = {
            'stories': {
                '1': 'Nice To Have',
                '2': 'Low', 
                '3': 'Middle',
                '4': 'High'
            },
            'bugs': {
                'insignificant': '微不足道',
                'low': '低',
                'medium': '中',
                'high': '高',
                'urgent': '紧急'
            }
        }
        
        # 高优先级定义
        self.high_priority_stories = ['3', '4']  # Middle, High
        self.high_priority_bugs = ['high', 'urgent']
    
    def load_tapd_data(self, file_path: str = "msg_from_fetcher.json") -> Dict[str, Any]:
        """加载TAPD数据"""
        return self.file_manager.load_tapd_data(file_path)
    
    def search_by_field(self, 
                       search_value: str,
                       search_field: Optional[str] = None,
                       data_type: str = "both",
                       exact_match: bool = True,
                       case_sensitive: bool = False) -> Dict[str, Any]:
        """
        按字段精确搜索
        
        Args:
            search_value: 搜索值
            search_field: 搜索字段，None表示搜索所有字段
            data_type: 数据类型 ('stories', 'bugs', 'both')
            exact_match: 是否精确匹配
            case_sensitive: 是否区分大小写
        """
        data = self.load_tapd_data()
        results = {'stories': [], 'bugs': [], 'summary': {}}
        
        # 准备搜索值
        search_val = search_value if case_sensitive else search_value.lower()
        
        # 搜索需求
        if data_type in ['stories', 'both'] and 'stories' in data:
            results['stories'] = self._search_in_items(
                data['stories'], search_val, search_field, 
                self.story_fields, exact_match, case_sensitive
            )
        
        # 搜索缺陷
        if data_type in ['bugs', 'both'] and 'bugs' in data:
            results['bugs'] = self._search_in_items(
                data['bugs'], search_val, search_field,
                self.bug_fields, exact_match, case_sensitive
            )
        
        # 生成摘要
        results['summary'] = {
            'total_stories': len(results['stories']),
            'total_bugs': len(results['bugs']),
            'total_items': len(results['stories']) + len(results['bugs']),
            'search_params': {
                'search_value': search_value,
                'search_field': search_field or '所有字段',
                'data_type': data_type,
                'exact_match': exact_match,
                'case_sensitive': case_sensitive
            }
        }
        
        return results
    
    def search_by_priority(self,
                          priority_filter: Optional[str] = "high",
                          data_type: str = "both") -> Dict[str, Any]:
        """
        按优先级搜索
        
        Args:
            priority_filter: 优先级过滤器 ('high', 'medium', 'low', 'all', 或具体值)
            data_type: 数据类型 ('stories', 'bugs', 'both')
        """
        data = self.load_tapd_data()
        results = {'stories': [], 'bugs': [], 'summary': {}}
        
        # 如果没有指定优先级过滤器，使用默认值
        if priority_filter is None:
            priority_filter = "high"
        
        # 搜索需求
        if data_type in ['stories', 'both'] and 'stories' in data:
            results['stories'] = self._filter_by_priority(
                data['stories'], priority_filter, 'stories'
            )
        
        # 搜索缺陷
        if data_type in ['bugs', 'both'] and 'bugs' in data:
            results['bugs'] = self._filter_by_priority(
                data['bugs'], priority_filter, 'bugs'
            )
        
        # 生成摘要
        results['summary'] = {
            'total_stories': len(results['stories']),
            'total_bugs': len(results['bugs']),
            'total_items': len(results['stories']) + len(results['bugs']),
            'priority_filter': priority_filter,
            'data_type': data_type
        }
        
        return results
    
    def advanced_search(self,
                       search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        高级搜索功能
        
        Args:
            search_params: 搜索参数字典，包含：
                - text_search: 文本搜索值
                - search_fields: 搜索字段列表
                - data_type: 数据类型
                - priority_filter: 优先级过滤器
                - status_filter: 状态过滤器
                - creator_filter: 创建者过滤器
                - date_range: 日期范围 {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
                - exact_match: 是否精确匹配
                - case_sensitive: 是否区分大小写
                - sort_by: 排序字段
                - sort_order: 排序顺序 ('asc', 'desc')
                - limit: 结果限制数量
        """
        data = self.load_tapd_data()
        results = {'stories': [], 'bugs': [], 'summary': {}}
        
        # 提取搜索参数
        text_search = search_params.get('text_search', '')
        search_fields = search_params.get('search_fields', [])
        data_type = search_params.get('data_type', 'both')
        priority_filter = search_params.get('priority_filter')
        status_filter = search_params.get('status_filter')
        creator_filter = search_params.get('creator_filter')
        date_range = search_params.get('date_range')
        exact_match = search_params.get('exact_match', True)
        case_sensitive = search_params.get('case_sensitive', False)
        sort_by = search_params.get('sort_by')
        sort_order = search_params.get('sort_order', 'desc')
        limit = search_params.get('limit')
        
        # 搜索需求
        if data_type in ['stories', 'both'] and 'stories' in data:
            stories = data['stories']
            
            # 文本搜索
            if text_search:
                stories = self._apply_text_filter(
                    stories, text_search, search_fields or list(self.story_fields.keys()),
                    exact_match, case_sensitive
                )
            
            # 优先级过滤
            if priority_filter:
                stories = self._filter_by_priority(stories, priority_filter, 'stories')
            
            # 状态过滤
            if status_filter:
                stories = [s for s in stories if s.get('status', '').lower() == status_filter.lower()]
            
            # 创建者过滤
            if creator_filter:
                stories = [s for s in stories if creator_filter.lower() in s.get('creator', '').lower()]
            
            # 日期范围过滤
            if date_range:
                stories = self._filter_by_date_range(stories, date_range, 'created')
            
            results['stories'] = stories
        
        # 搜索缺陷（类似处理）
        if data_type in ['bugs', 'both'] and 'bugs' in data:
            bugs = data['bugs']
            
            # 文本搜索
            if text_search:
                bugs = self._apply_text_filter(
                    bugs, text_search, search_fields or list(self.bug_fields.keys()),
                    exact_match, case_sensitive
                )
            
            # 优先级过滤
            if priority_filter:
                bugs = self._filter_by_priority(bugs, priority_filter, 'bugs')
            
            # 状态过滤
            if status_filter:
                bugs = [b for b in bugs if b.get('status', '').lower() == status_filter.lower()]
            
            # 创建者过滤（缺陷使用reporter字段）
            if creator_filter:
                bugs = [b for b in bugs if creator_filter.lower() in b.get('reporter', '').lower()]
            
            # 日期范围过滤
            if date_range:
                bugs = self._filter_by_date_range(bugs, date_range, 'created')
            
            results['bugs'] = bugs
        
        # 排序
        if sort_by:
            results['stories'] = self._sort_items(results['stories'], sort_by, sort_order)
            results['bugs'] = self._sort_items(results['bugs'], sort_by, sort_order)
        
        # 限制结果数量
        if limit:
            results['stories'] = results['stories'][:limit]
            results['bugs'] = results['bugs'][:limit]
        
        # 生成摘要
        results['summary'] = {
            'total_stories': len(results['stories']),
            'total_bugs': len(results['bugs']),
            'total_items': len(results['stories']) + len(results['bugs']),
            'search_params': search_params
        }
        
        return results
    
    def get_statistics(self, data_type: str = "both") -> Dict[str, Any]:
        """获取数据统计信息"""
        data = self.load_tapd_data()
        stats = {}
        
        if data_type in ['stories', 'both'] and 'stories' in data:
            stories = data['stories']
            stats['stories'] = {
                'total_count': len(stories),
                'priority_distribution': self._get_priority_distribution(stories, 'stories'),
                'status_distribution': self._get_status_distribution(stories),
                'creator_distribution': self._get_creator_distribution(stories, 'creator'),
                'recent_items': len([s for s in stories if self._is_recent(s.get('created', ''))]),
                'completed_items': len([s for s in stories if s.get('status') == 'status_6']),
                'high_priority_items': len(self._filter_by_priority(stories, 'high', 'stories'))
            }
        
        if data_type in ['bugs', 'both'] and 'bugs' in data:
            bugs = data['bugs']
            stats['bugs'] = {
                'total_count': len(bugs),
                'priority_distribution': self._get_priority_distribution(bugs, 'bugs'),
                'severity_distribution': self._get_severity_distribution(bugs),
                'status_distribution': self._get_status_distribution(bugs),
                'reporter_distribution': self._get_creator_distribution(bugs, 'reporter'),
                'recent_items': len([b for b in bugs if self._is_recent(b.get('created', ''))]),
                'resolved_items': len([b for b in bugs if b.get('status') in ['resolved', 'closed']]),
                'high_priority_items': len(self._filter_by_priority(bugs, 'high', 'bugs'))
            }
        
        return stats
    
    def _search_in_items(self, items: List[Dict], search_val: str, 
                        search_field: Optional[str], field_mapping: Dict[str, str],
                        exact_match: bool, case_sensitive: bool) -> List[Dict]:
        """在数据项中搜索"""
        if not search_val:
            return items
        
        results = []
        search_fields = [search_field] if search_field else list(field_mapping.keys())
        
        for item in items:
            if self._item_matches(item, search_val, search_fields, exact_match, case_sensitive):
                # 添加匹配信息
                item_copy = item.copy()
                item_copy['_match_info'] = self._get_match_info(
                    item, search_val, search_fields, exact_match, case_sensitive
                )
                results.append(item_copy)
        
        return results
    
    def _item_matches(self, item: Dict, search_val: str, search_fields: List[str],
                     exact_match: bool, case_sensitive: bool) -> bool:
        """检查数据项是否匹配搜索条件"""
        for field in search_fields:
            field_value = str(item.get(field, ''))
            
            if not case_sensitive:
                field_value = field_value.lower()
            
            if exact_match:
                if search_val == field_value:
                    return True
            else:
                if search_val in field_value:
                    return True
        
        return False
    
    def _get_match_info(self, item: Dict, search_val: str, search_fields: List[str],
                       exact_match: bool, case_sensitive: bool) -> Dict[str, Any]:
        """获取匹配信息"""
        matches = []
        
        for field in search_fields:
            field_value = str(item.get(field, ''))
            original_value = field_value
            
            if not case_sensitive:
                field_value = field_value.lower()
            
            if exact_match:
                if search_val == field_value:
                    matches.append({
                        'field': field,
                        'value': original_value,
                        'match_type': 'exact'
                    })
            else:
                if search_val in field_value:
                    matches.append({
                        'field': field,
                        'value': original_value,
                        'match_type': 'partial'
                    })
        
        return {
            'matched_fields': matches,
            'match_count': len(matches)
        }
    
    def _filter_by_priority(self, items: List[Dict], priority_filter: str, 
                           item_type: str) -> List[Dict]:
        """按优先级过滤"""
        if priority_filter == 'all':
            return items
        
        if item_type == 'stories':
            if priority_filter == 'high':
                return [item for item in items if item.get('priority', '') in self.high_priority_stories]
            elif priority_filter == 'medium':
                return [item for item in items if item.get('priority', '') == '3']
            elif priority_filter == 'low':
                return [item for item in items if item.get('priority', '') in ['1', '2']]
            else:
                # 具体优先级值
                return [item for item in items if item.get('priority', '') == priority_filter or 
                       item.get('priority_label', '').lower() == priority_filter.lower()]
        
        elif item_type == 'bugs':
            if priority_filter == 'high':
                return [item for item in items if item.get('priority', '') in self.high_priority_bugs]
            elif priority_filter == 'medium':
                return [item for item in items if item.get('priority', '') == 'medium']
            elif priority_filter == 'low':
                return [item for item in items if item.get('priority', '') in ['low', 'insignificant']]
            else:
                # 具体优先级值
                return [item for item in items if item.get('priority', '') == priority_filter]
        
        return items
    
    def _apply_text_filter(self, items: List[Dict], text_search: str, 
                          search_fields: List[str], exact_match: bool, 
                          case_sensitive: bool) -> List[Dict]:
        """应用文本过滤"""
        search_val = text_search if case_sensitive else text_search.lower()
        return [item for item in items if self._item_matches(
            item, search_val, search_fields, exact_match, case_sensitive
        )]
    
    def _filter_by_date_range(self, items: List[Dict], date_range: Dict[str, str],
                             date_field: str) -> List[Dict]:
        """按日期范围过滤"""
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        
        filtered_items = []
        
        for item in items:
            item_date = item.get(date_field, '')
            if not item_date:
                continue
            
            try:
                # 解析日期（支持多种格式）
                if ' ' in item_date:
                    item_datetime = datetime.strptime(item_date, '%Y-%m-%d %H:%M:%S')
                else:
                    item_datetime = datetime.strptime(item_date, '%Y-%m-%d')
                
                item_date_str = item_datetime.strftime('%Y-%m-%d')
                
                # 检查日期范围
                if start_date and item_date_str < start_date:
                    continue
                if end_date and item_date_str > end_date:
                    continue
                
                filtered_items.append(item)
                
            except ValueError:
                # 日期格式无法解析，跳过
                continue
        
        return filtered_items
    
    def _sort_items(self, items: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
        """排序数据项"""
        if not items:
            return items
        
        reverse = sort_order.lower() == 'desc'
        
        # 处理数字字段
        numeric_fields = ['priority', 'progress', 'effort', 'remain']
        
        if sort_by in numeric_fields:
            return sorted(items, key=lambda x: int(x.get(sort_by, 0) or 0), reverse=reverse)
        
        # 处理日期字段
        date_fields = ['created', 'modified', 'begin', 'due', 'resolved', 'closed']
        
        if sort_by in date_fields:
            return sorted(items, key=lambda x: self._parse_date(x.get(sort_by, '')), reverse=reverse)
        
        # 处理字符串字段
        return sorted(items, key=lambda x: str(x.get(sort_by, '')).lower(), reverse=reverse)
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析日期字符串"""
        if not date_str:
            return datetime.min
        
        try:
            if ' ' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return datetime.min
    
    def _get_priority_distribution(self, items: List[Dict], item_type: str) -> Dict[str, int]:
        """获取优先级分布"""
        distribution = {}
        
        for item in items:
            priority = item.get('priority', '未知')
            label = item.get('priority_label', priority)
            
            key = f"{priority} ({label})" if label != priority else str(priority)
            distribution[key] = distribution.get(key, 0) + 1
        
        return distribution
    
    def _get_status_distribution(self, items: List[Dict]) -> Dict[str, int]:
        """获取状态分布"""
        distribution = {}
        
        for item in items:
            status = item.get('status', '未知')
            distribution[status] = distribution.get(status, 0) + 1
        
        return distribution
    
    def _get_severity_distribution(self, items: List[Dict]) -> Dict[str, int]:
        """获取严重程度分布（仅缺陷）"""
        distribution = {}
        
        for item in items:
            severity = item.get('severity', '未知')
            distribution[severity] = distribution.get(severity, 0) + 1
        
        return distribution
    
    def _get_creator_distribution(self, items: List[Dict], field: str) -> Dict[str, int]:
        """获取创建者分布"""
        distribution = {}
        
        for item in items:
            creator = item.get(field, '未知')
            distribution[creator] = distribution.get(creator, 0) + 1
        
        return distribution
    
    def _is_recent(self, date_str: str, days: int = 7) -> bool:
        """检查是否为最近的数据"""
        if not date_str:
            return False
        
        try:
            item_date = self._parse_date(date_str)
            now = datetime.now()
            
            return (now - item_date).days <= days
        except:
            return False
    
    def export_results(self, results: Dict[str, Any], 
                      file_path: str = "search_results.json") -> Dict[str, Any]:
        """导出搜索结果"""
        try:
            # 添加导出时间戳
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'results': results
            }
            
            self.file_manager.save_json_data(export_data, file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'total_items': results['summary']['total_items']
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 全局实例
_searcher_instance = None

def get_searcher():
    """获取全局搜索器实例"""
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = TAPDDataPreciseSearcher()
    return _searcher_instance


def search_tapd_data(search_value: str,
                    search_field: Optional[str] = None,
                    data_type: str = "both",
                    exact_match: bool = True,
                    case_sensitive: bool = False) -> Dict[str, Any]:
    """
    搜索TAPD数据（简化接口）
    
    Args:
        search_value: 搜索值
        search_field: 搜索字段，None表示搜索所有字段
        data_type: 数据类型 ('stories', 'bugs', 'both')
        exact_match: 是否精确匹配
        case_sensitive: 是否区分大小写
    """
    searcher = get_searcher()
    return searcher.search_by_field(search_value, search_field, data_type, exact_match, case_sensitive)


def search_by_priority(priority_filter: str = "high",
                      data_type: str = "both") -> Dict[str, Any]:
    """
    按优先级搜索TAPD数据（简化接口）
    
    Args:
        priority_filter: 优先级过滤器 ('high', 'medium', 'low', 'all', 或具体值)
        data_type: 数据类型 ('stories', 'bugs', 'both')
    """
    searcher = get_searcher()
    return searcher.search_by_priority(priority_filter, data_type)


def get_tapd_statistics(data_type: str = "both") -> Dict[str, Any]:
    """
    获取TAPD数据统计信息（简化接口）
    
    Args:
        data_type: 数据类型 ('stories', 'bugs', 'both')
    """
    searcher = get_searcher()
    return searcher.get_statistics(data_type)


if __name__ == "__main__":
    # 测试代码
    searcher = TAPDDataPreciseSearcher()
    
    # 测试精确搜索
    print("=== 测试ID精确搜索 ===")
    results = searcher.search_by_field("1148591566001000001", "id")
    print(f"找到 {results['summary']['total_items']} 个结果")
    
    # 测试优先级搜索
    print("\n=== 测试高优先级搜索 ===")
    results = searcher.search_by_priority("high")
    print(f"找到 {results['summary']['total_items']} 个高优先级项目")
    
    # 测试统计信息
    print("\n=== 测试统计信息 ===")
    stats = searcher.get_statistics()
    print(f"统计信息: {stats}")
