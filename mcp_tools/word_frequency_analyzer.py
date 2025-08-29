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
# 兼容导入：既支持作为包导入，也支持脚本直接运行
try:
    from .common_utils import get_config, get_file_manager  # type: ignore
except Exception:
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from mcp_tools.common_utils import get_config, get_file_manager  # type: ignore


class TAPDWordFrequencyAnalyzer:
    """TAPD数据词频分析器"""
    
    def __init__(self, data_file_path: str = "local_data/msg_from_fetcher.json"):
        """
        初始化词频分析器
        
        参数:
            data_file_path (str): TAPD数据文件路径
        """
        self.config = get_config()
        self.file_manager = get_file_manager()
        
        # 使用统一的路径处理
        if data_file_path == "local_data/msg_from_fetcher.json":
            self.data_file_path = self.config.get_data_file_path()
        else:
            # 如果不是绝对路径，转换为相对于项目根目录的路径
            if not os.path.isabs(data_file_path):
                self.data_file_path = self.config.get_data_file_path(data_file_path)
            else:
                self.data_file_path = data_file_path
        
        # 停用词列表 - 只过滤真正无意义的高频词汇
        # 保留了所有对TAPD缺陷和需求分析有价值的词汇
        self.stop_words = {
            # 基础语言连词和代词
            '的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '与', '和', '或',
            '但', '而', '因为', '所以', '如果', '就', '都', '很', '还', '也', '不', '没有', '有',
            '能', '会', '要', '可以', '应该', '可能', '已经', '正在', '将要', '一个', '一些',
            
            # 通用描述词汇（保留技术和业务相关词汇）
            '其他', '其它', '等等', '等', '及', '以及', '包括', '含有', '具有',
            '按照', '依据', '来自', '来源', '来源于', '属于', '归属',
            '首先', '然后', '接着', '同时', '此外', '另外', '除了', '除此之外',
            
            # 时间相关的通用词汇
            '当前', '目前', '现在', '当时', '之前', '之后', '以前', '以后', '最后', '最终'
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
            
            # 使用统一的文件管理器读取数据
            try:
                data = self.file_manager.load_tapd_data(self.data_file_path)
            except FileNotFoundError as e:
                return {
                    "status": "error",
                    "message": str(e),
                    "suggestion": "请先调用 get_tapd_data 工具获取数据"
                }
            
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
            "问题缺陷类": [],
            "需求功能类": [],
            "技术实现类": [],
            "角色人员类": [],
            "业务流程类": [],
            "状态描述类": [],
            "其他": []
        }
        
        # 问题缺陷相关关键词
        defect_keywords = {'问题', '解决', '修复', 'bug', 'Bug', 'BUG', '缺陷', '错误', '异常', '故障',
                          '失败', '崩溃', '阻塞', '影响', '风险', '漏洞'}
        
        # 需求功能相关关键词
        requirement_keywords = {'需求', '功能', '特性', '优化', '改进', '新增', '删除', '变更',
                              '升级', '扩展', '配置', '设置'}
        
        # 技术实现相关关键词
        tech_keywords = {'模块', '系统', '平台', '服务', '接口', 'api', 'API', '数据库', '缓存',
                        '算法', '框架', '代码', '部署', '服务器', '网络', '安全', '性能', '架构',
                        '进行', '实现', '完成', '处理', '操作', '执行', '运行', '使用', '采用',
                        '通过', '基于', '根据', '相关', '关于', '对于', '针对', '关联', '涉及',
                        '产生', '出现', '发生', '存在', '位于'}
        
        # 角色人员相关关键词
        role_keywords = {'用户', '客户', '管理员', '开发', '测试', '运维', '产品', '设计师',
                        '分析师', '架构师', '项目经理'}
        
        # 业务流程相关关键词
        process_keywords = {'业务', '流程', '步骤', '环节', '阶段', '过程', '方案', '策略',
                          '规则', '逻辑', '条件', '判断', '验证', '审核'}
        
        # 状态描述相关关键词
        status_keywords = {'完成', '待处理', '进行中', '暂停', '取消', '成功', '失败', 
                         '正常', '异常', '有效', '无效', '开启', '关闭', '启用', '禁用'}
        
        for word, freq in word_freq_pairs:
            if any(keyword in word for keyword in defect_keywords):
                categories["问题缺陷类"].append(word)
            elif any(keyword in word for keyword in requirement_keywords):
                categories["需求功能类"].append(word)
            elif any(keyword in word for keyword in tech_keywords):
                categories["技术实现类"].append(word)
            elif any(keyword in word for keyword in role_keywords):
                categories["角色人员类"].append(word)
            elif any(keyword in word for keyword in process_keywords):
                categories["业务流程类"].append(word)
            elif any(keyword in word for keyword in status_keywords):
                categories["状态描述类"].append(word)
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


if __name__ == "__main__":
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description="TAPD 数据词频统计分析器")
    parser.add_argument("--data", "-f", default="local_data/msg_from_fetcher.json", help="TAPD 数据文件路径（JSON）")
    parser.add_argument("--min", dest="min_freq", type=int, default=3, help="最小词频阈值，默认3")
    parser.add_argument("--no-extended", action="store_true", help="不使用扩展字段参与统计")
    parser.add_argument("--out", "-o", default="local_data/logs/word_frequency.json", help="结果输出文件（JSON）")
    args = parser.parse_args()

    analyzer = TAPDWordFrequencyAnalyzer(args.data)
    result = analyzer.analyze_word_frequency(min_frequency=args.min_freq, use_extended_fields=not args.no_extended)

    # 打印简要结果
    if result.get("status") == "success":
        stats = result.get("statistics", {})
        top20 = result.get("word_frequency", {}).get("top_20_words", {})
        print("[词频分析完成]")
        print(f"需求: {stats.get('stories_count', 0)}, 缺陷: {stats.get('bugs_count', 0)}, 合计: {stats.get('total_items', 0)}")
        print(f"总词数: {stats.get('total_words', 0)}, 不重复词: {stats.get('unique_words', 0)}")
        print("Top 20 关键词:")
        for w, c in list(top20.items())[:20]:
            print(f"  {w}: {c}")
    else:
        print(f"[错误] {result.get('message')}")
        if result.get("suggestion"):
            print("建议:", result["suggestion"])

    # 保存到文件
    try:
        # 使用统一文件管理器以确保目录存在
        fm = get_file_manager()
        out_path = args.out
        # 处理相对路径：允许传入 local_data/xxx 或文件名
        if not os.path.isabs(out_path):
            if out_path.replace("\\", "/").startswith("local_data/"):
                out_abs = get_config().get_data_file_path(out_path)
            else:
                out_abs = get_config().get_data_file_path(out_path)
        else:
            out_abs = out_path
        fm.save_json_data(result, out_abs)
        print(f"结果已保存: {out_abs}")
    except Exception as e:
        print(f"保存结果失败: {e}")
