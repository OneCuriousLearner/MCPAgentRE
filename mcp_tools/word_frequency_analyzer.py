"""
TAPD数据词频统计分析器

用于分析TAPD数据中的词频分布，为搜索功能提供关键词参考
"""

import json
import re
from collections import Counter
from typing import Dict, List, Tuple, Any
import jieba
import os


class TAPDWordFrequencyAnalyzer:
    """TAPD数据词频分析器"""
    
    def __init__(self, data_file_path: str = "local_data/msg_from_fetcher.json"):
        """
        初始化词频分析器
        
        参数:
            data_file_path (str): TAPD数据文件路径
        """
        self.data_file_path = data_file_path
        
        # 停用词列表 - 过滤掉无意义的词汇
        self.stop_words = {
            '的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '与', '和', '或',
            '但', '而', '因为', '所以', '如果', '就', '都', '很', '还', '也', '不', '没有', '有',
            '能', '会', '要', '可以', '需要', '应该', '可能', '已经', '正在', '将要', '一个', '一些',
            '其他', '其它', '等等', '等', '及', '以及', '包括', '含有', '具有', '进行', '实现',
            '完成', '处理', '操作', '执行', '运行', '使用', '采用', '通过', '基于', '根据',
            '按照', '依据', '相关', '关于', '对于', '针对', '关联', '涉及', '影响', '导致',
            '产生', '出现', '发生', '存在', '位于', '来自', '来源', '来源于', '属于', '归属',
            '当前', '目前', '现在', '当时', '之前', '之后', '以前', '以后', '最后', '最终',
            '首先', '然后', '接着', '最后', '同时', '此外', '另外', '除了', '除此之外',
            '问题', '解决', '修复', 'bug', 'Bug', 'BUG', '缺陷', '错误', '异常', '故障',
            '需求', '功能', '特性', '模块', '系统', '平台', '服务', '接口', 'api', 'API',
            '用户', '客户', '管理员', '开发', '测试', '运维', '产品', '业务', '流程', '步骤'
        }
        
        # 关键字段列表
        self.key_fields = ['name', 'description', 'test_focus', 'label']
        
        # 扩展字段列表 - 可能包含有用信息的其他字段
        self.extended_fields = ['acceptance', 'comment', 'status', 'priority', 'iteration_id']
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        参数:
            text (str): 原始文本
            
        返回:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', str(text))
        
        # 移除特殊字符，保留中文、英文、数字
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_words(self, text: str) -> List[str]:
        """
        从文本中提取词汇
        
        参数:
            text (str): 输入文本
            
        返回:
            List[str]: 提取的词汇列表
        """
        if not text:
            return []
        
        # 清理文本
        cleaned_text = self._clean_text(text)
        
        # 使用jieba进行中文分词
        words = jieba.lcut(cleaned_text)
        
        # 过滤条件：长度大于1且不在停用词中
        filtered_words = [
            word.strip() for word in words
            if len(word.strip()) > 1 and word.strip() not in self.stop_words
        ]
        
        return filtered_words
    
    def _extract_text_from_item(self, item: Dict[str, Any], use_extended_fields: bool = True) -> str:
        """
        从单个数据条目中提取文本内容
        
        参数:
            item (Dict[str, Any]): 数据条目
            use_extended_fields (bool): 是否使用扩展字段
            
        返回:
            str: 合并的文本内容
        """
        texts = []
        
        # 提取主要字段
        for field in self.key_fields:
            value = item.get(field, '')
            if value:
                texts.append(str(value))
        
        # 如果启用扩展字段，也提取这些字段
        if use_extended_fields:
            for field in self.extended_fields:
                value = item.get(field, '')
                if value:
                    texts.append(str(value))
        
        return ' '.join(texts)
    
    def analyze_word_frequency(self, min_frequency: int = 3, use_extended_fields: bool = True) -> Dict[str, Any]:
        """
        分析TAPD数据的词频分布
        
        参数:
            min_frequency (int): 最小词频阈值，默认3
            use_extended_fields (bool): 是否使用扩展字段，默认True
            
        返回:
            Dict[str, Any]: 词频分析结果
        """
        try:
            # 检查数据文件是否存在
            if not os.path.exists(self.data_file_path):
                return {
                    "status": "error",
                    "message": f"数据文件不存在: {self.data_file_path}",
                    "suggestion": "请先调用 get_tapd_data 工具获取数据"
                }
            
            # 读取数据文件
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stories = data.get('stories', [])
            bugs = data.get('bugs', [])
            
            # 收集所有词汇
            all_words = []
            
            # 处理需求数据
            for story in stories:
                text = self._extract_text_from_item(story, use_extended_fields)
                words = self._extract_words(text)
                all_words.extend(words)
            
            # 处理缺陷数据
            for bug in bugs:
                text = self._extract_text_from_item(bug, use_extended_fields)
                words = self._extract_words(text)
                all_words.extend(words)
            
            # 统计词频
            word_counter = Counter(all_words)
            
            # 过滤低频词
            filtered_words = {
                word: count for word, count in word_counter.items()
                if count >= min_frequency
            }
            
            # 按频次排序
            sorted_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)
            
            # 生成统计信息
            total_words = len(all_words)
            unique_words = len(word_counter)
            high_freq_words = len(filtered_words)
            
            # 计算频次分布
            frequency_distribution = {}
            for word, count in word_counter.items():
                freq_range = self._get_frequency_range(count)
                frequency_distribution[freq_range] = frequency_distribution.get(freq_range, 0) + 1
            
            # 提取高频关键词（用于搜索建议）
            search_keywords = [word for word, count in sorted_words[:50]]  # 取前50个高频词
            
            return {
                "status": "success",
                "analysis_config": {
                    "min_frequency": min_frequency,
                    "use_extended_fields": use_extended_fields,
                    "analyzed_fields": self.key_fields + (self.extended_fields if use_extended_fields else [])
                },
                "statistics": {
                    "total_words": total_words,
                    "unique_words": unique_words,
                    "high_frequency_words": high_freq_words,
                    "stories_count": len(stories),
                    "bugs_count": len(bugs),
                    "total_items": len(stories) + len(bugs)
                },
                "word_frequency": {
                    "high_frequency_words": dict(sorted_words),
                    "frequency_distribution": frequency_distribution,
                    "top_20_words": dict(sorted_words[:20])
                },
                "search_suggestions": {
                    "recommended_keywords": search_keywords[:20],
                    "category_keywords": self._categorize_keywords(sorted_words[:30])
                }
            }
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"JSON文件解析错误: {str(e)}",
                "suggestion": "请检查数据文件格式是否正确"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"词频分析失败: {str(e)}"
            }
    
    def _get_frequency_range(self, count: int) -> str:
        """
        根据词频获取频次范围标签
        
        参数:
            count (int): 词频
            
        返回:
            str: 频次范围标签
        """
        if count >= 100:
            return "100+"
        elif count >= 50:
            return "50-99"
        elif count >= 20:
            return "20-49"
        elif count >= 10:
            return "10-19"
        elif count >= 5:
            return "5-9"
        else:
            return "1-4"
    
    def _categorize_keywords(self, word_freq_pairs: List[Tuple[str, int]]) -> Dict[str, List[str]]:
        """
        将关键词按类别分组
        
        参数:
            word_freq_pairs (List[Tuple[str, int]]): 词频对列表
            
        返回:
            Dict[str, List[str]]: 分类后的关键词
        """
        categories = {
            "技术相关": [],
            "业务功能": [],
            "状态描述": [],
            "其他": []
        }
        
        # 技术相关关键词
        tech_keywords = {'接口', '数据库', '缓存', '算法', '框架', '代码', '配置', '部署', 
                        '服务器', '网络', '安全', '性能', '优化', '架构', '设计'}
        
        # 业务功能关键词
        business_keywords = {'订单', '支付', '用户', '商品', '购物车', '物流', '评价', 
                           '客服', '营销', '推荐', '搜索', '登录', '注册', '认证'}
        
        # 状态描述关键词
        status_keywords = {'完成', '待处理', '进行中', '暂停', '取消', '成功', '失败', 
                         '正常', '异常', '有效', '无效', '开启', '关闭'}
        
        for word, freq in word_freq_pairs:
            if any(keyword in word for keyword in tech_keywords):
                categories["技术相关"].append(word)
            elif any(keyword in word for keyword in business_keywords):
                categories["业务功能"].append(word)
            elif any(keyword in word for keyword in status_keywords):
                categories["状态描述"].append(word)
            else:
                categories["其他"].append(word)
        
        # 移除空分类
        return {k: v for k, v in categories.items() if v}


# 异步包装函数
async def analyze_tapd_word_frequency(
    min_frequency: int = 3,
    use_extended_fields: bool = True,
    data_file_path: str = "local_data/msg_from_fetcher.json"
) -> Dict[str, Any]:
    """
    异步分析TAPD数据词频的包装函数
    
    参数:
        min_frequency (int): 最小词频阈值
        use_extended_fields (bool): 是否使用扩展字段
        data_file_path (str): 数据文件路径
        
    返回:
        Dict[str, Any]: 词频分析结果
    """
    analyzer = TAPDWordFrequencyAnalyzer(data_file_path)
    return analyzer.analyze_word_frequency(min_frequency, use_extended_fields)
