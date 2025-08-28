"""
时间趋势分析工具
支持分析TAPD需求和缺陷数据的时间趋势，生成可视化图表
"""
import os
import json
import sys
import asyncio
from datetime import datetime, timedelta
import matplotlib
# Use non-GUI backend to avoid Tkinter in background threads
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from typing import Dict, List, Optional, Literal

from mcp_tools.common_utils import get_config, get_file_manager

# 设置中文字体支持（在 Agg 后端下仅影响渲染，不会引入 GUI）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def create_time_trend_directory():
    """创建时间趋势分析目录"""
    config = get_config()
    time_trend_dir = os.path.join(config.get_data_file_path(""), "time_trend")
    os.makedirs(time_trend_dir, exist_ok=True)
    return time_trend_dir


def parse_tapd_time(time_str: str) -> Optional[datetime]:
    """解析TAPD时间字符串"""
    if not time_str:
        return None
    
    try:
        # 处理TAPD时间格式：YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD
        if ' ' in time_str:
            return datetime.strptime(time_str.split(' ')[0], "%Y-%m-%d")
        else:
            return datetime.strptime(time_str, "%Y-%m-%d")
    except ValueError:
        return None


def generate_daily_statistics(data_list: List[Dict], 
                             time_field: str = 'created',
                             data_type: Literal['story', 'bug'] = 'story') -> Dict:
    """生成每日统计数据"""
    daily_stats = {}
    
    for item in data_list:
        # 处理不同的时间字段情况
        time_str = None
        
        # 对于需求数据，支持多种时间字段
        if data_type == 'story':
            if time_field == 'begin' and item.get('begin'):
                time_str = item.get('begin')
            elif time_field == 'due' and item.get('due'):
                time_str = item.get('due')
            else:
                time_str = item.get(time_field)
        else:
            # 对于缺陷数据，使用指定的时间字段
            time_str = item.get(time_field)
        
        if not time_str:
            continue
            
        date_obj = parse_tapd_time(time_str)
        if not date_obj:
            continue
            
        date_key = date_obj.strftime("%Y-%m-%d")
        
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                'date': date_key,  # 存储字符串格式的日期，而不是datetime对象
                'total_count': 0,
                'completed_count': 0,   # 新增：完成数量（基于状态推断）
                'new_count': 0,         # 新增：新建数量（基于状态推断）
                'high_priority_count': 0,
                'medium_priority_count': 0,
                'low_priority_count': 0,
                'status_counts': {}  # 动态统计所有状态字段
            }
        
        # 统计总数
        daily_stats[date_key]['total_count'] += 1
        
        # 统计优先级
        priority = item.get('priority', '').lower()
        if 'high' in priority or '紧急' in priority or '1' in str(priority):
            daily_stats[date_key]['high_priority_count'] += 1
        elif 'medium' in priority or '中' in priority or '2' in str(priority):
            daily_stats[date_key]['medium_priority_count'] += 1
        elif 'low' in priority or '低' in priority or '3' in str(priority):
            daily_stats[date_key]['low_priority_count'] += 1
        
        # 动态统计状态字段
        status = item.get('status', '')
        if status:
            if status not in daily_stats[date_key]['status_counts']:
                daily_stats[date_key]['status_counts'][status] = 0
            daily_stats[date_key]['status_counts'][status] += 1

            # 基于常见状态值推断 completed/new 计数（尽量宽松匹配）
            st_lower = str(status).lower()
            if any(k in st_lower for k in ['closed', 'resolved', 'done', '完成', '已解决', '已关闭']):
                daily_stats[date_key]['completed_count'] += 1
            if any(k in st_lower for k in ['new', 'open', '创建', '新建']):
                daily_stats[date_key]['new_count'] += 1
    
    return daily_stats


def plot_time_trend_chart(daily_stats: Dict, 
                         chart_type: Literal['count', 'priority', 'status'] = 'count',
                         data_type: str = 'story',
                         time_field: str = 'created',
                         time_range: Optional[str] = None,
                         chart_title: Optional[str] = None,
                         output_path: Optional[str] = None) -> str:
    """绘制时间趋势图表"""
    
    if not daily_stats:
        return "无数据可绘制图表"
    
    # 按日期排序
    sorted_dates = sorted(daily_stats.keys())
    # 将字符串日期转换为datetime对象用于绘图
    date_objs = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in sorted_dates]
    # Convert to numbers for type checkers while matplotlib accepts datetime
    dates = mdates.date2num(date_objs)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if chart_type == 'count':
        # 总数趋势图
        total_counts = [daily_stats[date]['total_count'] for date in sorted_dates]
        ax.plot(dates, total_counts, 'b-o', linewidth=2, markersize=6, label='总数')
        ax.set_ylabel('数量', fontsize=12)
        title = chart_title or f'{data_type}每日数量趋势 (按{time_field})'
        
    elif chart_type == 'priority':
        # 优先级趋势图
        high_counts = [daily_stats[date]['high_priority_count'] for date in sorted_dates]
        medium_counts = [daily_stats[date]['medium_priority_count'] for date in sorted_dates]
        low_counts = [daily_stats[date]['low_priority_count'] for date in sorted_dates]
        
        ax.plot(dates, high_counts, 'r-o', linewidth=2, markersize=6, label='高优先级')
        ax.plot(dates, medium_counts, 'y-s', linewidth=2, markersize=6, label='中优先级')
        ax.plot(dates, low_counts, 'g-^', linewidth=2, markersize=6, label='低优先级')
        ax.set_ylabel('数量', fontsize=12)
        title = chart_title or f'{data_type}优先级分布趋势 (按{time_field})'
        
    elif chart_type == 'status':
        # 状态趋势图 - 动态处理所有状态字段
        status_data = {}
        all_statuses = set()
        
        # 收集所有出现的状态
        for date in sorted_dates:
            for status in daily_stats[date]['status_counts'].keys():
                all_statuses.add(status)
        
        # 为每个状态初始化数据列表
        for status in all_statuses:
            status_data[status] = []
        
        # 填充每个状态在每个日期的计数（没有则为0）
        for date in sorted_dates:
            for status in all_statuses:
                count = daily_stats[date]['status_counts'].get(status, 0)
                status_data[status].append(count)
        
        # 为每个状态绘制趋势线
        colors = ['g-o', 'r-s', 'b-^', 'y-d', 'm-*', 'c-p', 'k-h']
        color_index = 0
        
        for status, counts in status_data.items():
            color = colors[color_index % len(colors)]
            ax.plot(dates, counts, color, linewidth=2, markersize=6, label=status)
            color_index += 1
        
        ax.set_ylabel('数量', fontsize=12)
        title = chart_title or f'{data_type}状态分布趋势 (按{time_field})'
    
    # 设置图表样式
    if time_range:
        title = f"{title}\n{time_range}"
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('日期', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    # 设置x轴日期格式
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # 保存图表
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_path
    else:
        return "未指定输出路径"


async def analyze_time_trends(
    data_type: Literal['story', 'bug'] = 'story',
    chart_type: Literal['count', 'priority', 'status'] = 'count',
    time_field: str = 'created',
    since: Optional[str] = None,
    until: Optional[str] = None,
    chart_title: Optional[str] = None,
    data_file_path: str = "local_data/msg_from_fetcher.json"
) -> Dict:
    """
    分析TAPD数据的时间趋势
    
    参数:
        data_type: 数据类型，'story'或'bug'
        chart_type: 图表类型，'count'(总数)、'priority'(优先级)、'status'(状态)
        time_field: 时间字段，默认为'created'
        since: 开始时间，格式YYYY-MM-DD
        until: 结束时间，格式YYYY-MM-DD
        data_file_path: 数据文件路径
    
    返回:
        包含统计信息和图表路径的字典
    """
    
    # 加载数据
    file_manager = get_file_manager()
    data = file_manager.load_tapd_data(data_file_path)
    
    if not data:
        return {
            'status': 'error',
            'message': '数据加载失败或数据为空'
        }
    
    # 获取指定类型的数据
    if data_type == 'story':
        data_list = data.get('stories', [])
    elif data_type == 'bug':
        data_list = data.get('bugs', [])
    else:
        return {
            'status': 'error',
            'message': f'不支持的数据类型: {data_type}'
        }
    
    if not data_list:
        return {
            'status': 'error',
            'message': f'{data_type}数据为空'
        }
    
    # 时间筛选
    if since and until:
        from tapd_data_fetcher import filter_data_by_time
        filtered_data = filter_data_by_time(data_list, since, until, time_field)
    else:
        filtered_data = data_list
    
    if not filtered_data:
        return {
            'status': 'error',
            'message': '筛选后数据为空，请检查时间范围'
        }
    
    # 生成统计信息
    daily_stats = generate_daily_statistics(filtered_data, time_field, data_type)
    
    if not daily_stats:
        return {
            'status': 'error',
            'message': '无法生成统计信息，请检查时间字段格式'
        }
    
    # 创建输出目录
    output_dir = create_time_trend_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{data_type}_{chart_type}_{timestamp}.png"
    output_path = os.path.join(output_dir, filename)
    
    # 生成图表
    time_range_str = f"{since} 到 {until}" if since and until else "全部时间"
    chart_path = plot_time_trend_chart(daily_stats, chart_type, data_type, time_field, time_range_str, chart_title, output_path)
    
    # 计算总体统计
    total_count = len(filtered_data)
    date_range = list(daily_stats.keys())
    
    print('[TimeTrend] Sample daily stats preview:', file=sys.stderr, flush=True)
    for date_key, daily_data in daily_stats.items():
        print(f'Date: {date_key}', file=sys.stderr, flush=True)
        print(f'  Total: {daily_data["total_count"]}', file=sys.stderr, flush=True)
        print(f'  Status counts: {daily_data["status_counts"]}', file=sys.stderr, flush=True)
        print('', file=sys.stderr, flush=True)
    
    result = {
        'status': 'success',
        'data_type': data_type,
        'chart_type': chart_type,
        'time_field': time_field,
        'time_range': f"{since} 到 {until}" if since and until else "全部时间",
        'total_count': total_count,
        'date_range': {
            'start': min(date_range) if date_range else None,
            'end': max(date_range) if date_range else None,
            'days_count': len(date_range)
        },
        # daily_stats中的date字段已经是字符串格式，无需再次转换
        'daily_stats': daily_stats,
        'chart_path': chart_path,
        'chart_url': f"file:///{chart_path.replace(os.sep, '/')}",
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result