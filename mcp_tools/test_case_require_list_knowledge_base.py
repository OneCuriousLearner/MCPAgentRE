"""
测试用例需求单知识库管理器

该脚本用于管理测试用例评估中使用的需求单知识库，提供以下功能：

=== 配置需求单的具体操作指南 ===

1. 【从本地数据提取需求单】
   - 自动从 local_data/msg_from_fetcher.json 中提取需求单信息
   - 提取字段包括：需求ID、需求标题、需求描述、状态、优先级、创建者等
   - 适用于初次配置或批量导入场景

2. 【手动输入需求单】
   - 手动输入需求单的关键信息
   - 包括：需求ID、标题、描述、业务价值、验收标准等
   - 适用于特定测试场景或补充需求信息

3. 【查看现有需求单】
   - 以列表形式展示所有已配置的需求单
   - 显示需求单的索引编号、ID、标题和简要描述
   - 便于了解当前知识库内容

4. 【添加新需求单】
   - 在现有需求单基础上添加新的需求单
   - 自动分配新的索引编号
   - 支持批量添加

5. 【删除指定需求单】
   - 通过索引编号删除指定需求单
   - 支持批量删除（输入多个索引编号）
   - 有确认机制防止误删

6. 【清除所有需求单】
   - 清空整个需求单知识库
   - 需要双重确认防止误操作

=== 使用建议 ===
- 首次使用建议先从本地数据提取需求单，建立基础知识库
- 根据测试需要手动添加特定需求单
- 定期检查和清理不再需要的需求单
- 每次操作都会自动保存到 local_data/require_list_config.json

=== 数据格式说明 ===
需求单数据结构：
{
    "requirement_id": "需求ID",
    "title": "需求标题", 
    "description": "需求描述",
    "status": "需求状态",
    "priority": "优先级",
    "creator": "创建者",
    "business_value": "业务价值",
    "acceptance_criteria": "验收标准",
    "local_created_time": "本地创建时间（YYYY-MM-DD HH:MM:SS）"
}
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.common_utils import get_config, get_file_manager


class RequirementKnowledgeBase:
    """需求单知识库管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.file_manager = get_file_manager()
        self.config_file = self.config.local_data_path / "require_list_config.json"
        self.requirements = self._load_requirements()
    
    def _load_requirements(self) -> List[Dict[str, Any]]:
        """加载需求单配置"""
        try:
            if self.config_file.exists():
                data = self.file_manager.load_json_data(str(self.config_file))
                requirements = data.get('requirements', [])
                
                # 为旧数据添加本地创建时间字段（向后兼容）
                for req in requirements:
                    if 'local_created_time' not in req:
                        req['local_created_time'] = req.get('created', '未知时间')
                
                return requirements
            return []
        except Exception as e:
            print(f"❌ 加载需求单配置失败: {e}")
            return []
    
    def _save_requirements(self):
        """保存需求单配置"""
        try:
            data = {
                'requirements': self.requirements,
                'total_count': len(self.requirements),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.file_manager.save_json_data(data, str(self.config_file))
            print(f"✅ 需求单配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存需求单配置失败: {e}")
    
    def _extract_text_from_html(self, html_text: str) -> str:
        """从HTML文本中提取纯文本内容"""
        if not html_text:
            return ""
        
        # 简单的HTML标签清理
        text = re.sub(r'<[^>]+>', '', html_text)
        # 处理HTML实体
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # 清理多余空白
        text = ' '.join(text.split())
        return text.strip()
    
    def extract_from_local_data(self, data_file: str = "local_data/msg_from_fetcher.json") -> int:
        """从本地数据文件中提取需求单"""
        try:
            print(f"🔍 正在从 {data_file} 提取需求单...")
            
            # 加载TAPD数据
            tapd_data = self.file_manager.load_tapd_data(data_file)
            stories = tapd_data.get('stories', [])
            
            if not stories:
                print("❌ 未找到需求单数据")
                return 0
            
            extracted_count = 0
            
            for story in stories:
                # 检查是否已存在（根据ID）
                story_id = story.get('id', '')
                if any(req.get('requirement_id') == story_id for req in self.requirements):
                    continue
                
                # 提取关键信息
                requirement = {
                    'requirement_id': story_id,
                    'title': story.get('name', ''),
                    'description': self._extract_text_from_html(story.get('description', '')),
                    'status': story.get('status', ''),
                    'priority': story.get('priority', ''),
                    'creator': story.get('creator', ''),
                    'business_value': story.get('business_value', ''),
                    'acceptance_criteria': '',  # 从description中提取
                    'module': story.get('module', ''),
                    'version': story.get('version', ''),
                    'created': story.get('created', ''),
                    'modified': story.get('modified', ''),
                    'local_created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 添加本地创建时间
                }
                
                # 尝试从描述中提取验收标准
                desc = requirement['description']
                if '验收标准' in desc or '验收条件' in desc:
                    # 简单的验收标准提取
                    lines = desc.split('\n')
                    acceptance_lines = []
                    in_acceptance = False
                    for line in lines:
                        if '验收标准' in line or '验收条件' in line:
                            in_acceptance = True
                            continue
                        if in_acceptance and line.strip():
                            if line.startswith('-') or line.startswith('•') or '。' in line:
                                acceptance_lines.append(line.strip())
                            elif len(acceptance_lines) > 0:  # 遇到空行或其他内容，停止提取
                                break
                    requirement['acceptance_criteria'] = '\n'.join(acceptance_lines)
                
                self.requirements.append(requirement)
                extracted_count += 1
            
            print(f"✅ 成功提取 {extracted_count} 个需求单")
            return extracted_count
            
        except Exception as e:
            print(f"❌ 提取需求单失败: {e}")
            return 0
    
    def add_manual_requirement(self) -> bool:
        """手动添加需求单"""
        print("\n📝 手动添加需求单")
        print("请输入需求单信息（输入 'q' 退出）：")
        
        try:
            # 需求ID
            req_id = input("需求ID: ").strip()
            if req_id.lower() == 'q':
                return False
            
            # 检查是否已存在
            if any(req.get('requirement_id') == req_id for req in self.requirements):
                print(f"❌ 需求ID {req_id} 已存在")
                return False
            
            # 需求标题
            title = input("需求标题: ").strip()
            if title.lower() == 'q':
                return False
            
            # 需求描述
            print("需求描述（支持多行，输入空行结束）:")
            description_lines = []
            while True:
                line = input().strip()
                if not line:
                    break
                if line.lower() == 'q':
                    return False
                description_lines.append(line)
            description = '\n'.join(description_lines)
            
            # 其他字段
            status = input("需求状态 (默认: planning): ").strip() or "planning"
            priority = input("优先级 (1-5, 默认: 3): ").strip() or "3"
            creator = input("创建者 (默认: 手动输入): ").strip() or "手动输入"
            business_value = input("业务价值: ").strip()
            
            print("验收标准（支持多行，输入空行结束）:")
            acceptance_lines = []
            while True:
                line = input().strip()
                if not line:
                    break
                if line.lower() == 'q':
                    return False
                acceptance_lines.append(line)
            acceptance_criteria = '\n'.join(acceptance_lines)
            
            # 构建需求单
            requirement = {
                'requirement_id': req_id,
                'title': title,
                'description': description,
                'status': status,
                'priority': priority,
                'creator': creator,
                'business_value': business_value,
                'acceptance_criteria': acceptance_criteria,
                'module': '',
                'version': '',
                'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'local_created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 添加本地创建时间
            }
            
            # 确认添加
            print(f"\n请确认您的操作：")
            print(f"新增需求单: {req_id} - {title}")
            print(f"描述: {description[:100]}{'...' if len(description) > 100 else ''}")
            confirm = input("确定添加吗？(y/n): ").strip().lower()
            
            if confirm == 'y':
                self.requirements.append(requirement)
                print(f"✅ 成功添加需求单: {req_id}")
                return True
            else:
                print("❌ 已取消添加")
                return False
                
        except KeyboardInterrupt:
            print("\n❌ 操作被中断")
            return False
        except Exception as e:
            print(f"❌ 添加需求单失败: {e}")
            return False
    
    def show_requirements(self):
        """显示所有需求单"""
        if not self.requirements:
            print("📭 当前没有需求单")
            return
        
        print(f"\n📋 当前需求单列表 (共 {len(self.requirements)} 个):")
        print("-" * 100)
        
        for i, req in enumerate(self.requirements):
            title = req.get('title', '无标题')
            req_id = req.get('requirement_id', '无ID')
            status = req.get('status', '未知')
            priority = req.get('priority', '未知')
            desc = req.get('description', '')
            desc_preview = desc[:50] + '...' if len(desc) > 50 else desc
            local_created_time = req.get('local_created_time', '未知')
            
            print(f"[{i+1:2d}] ID: {req_id}")
            print(f"     标题: {title}")
            print(f"     状态: {status} | 优先级: {priority}")
            print(f"     描述: {desc_preview}")
            print(f"     创建时间: {local_created_time}")
            print("-" * 100)
    
    def delete_requirements(self):
        """删除指定需求单"""
        if not self.requirements:
            print("📭 当前没有需求单可删除")
            return
        
        self.show_requirements()
        
        try:
            print("\n🗑️ 删除需求单")
            indices_input = input("请输入要删除的需求单序号（多个用逗号分隔，输入 'q' 退出）: ").strip()
            
            if indices_input.lower() == 'q':
                return
            
            # 解析输入的序号
            indices = []
            for idx_str in indices_input.split(','):
                try:
                    idx = int(idx_str.strip()) - 1  # 转换为0-based索引
                    if 0 <= idx < len(self.requirements):
                        indices.append(idx)
                    else:
                        print(f"❌ 序号 {idx_str.strip()} 超出范围")
                except ValueError:
                    print(f"❌ 无效序号: {idx_str.strip()}")
            
            if not indices:
                print("❌ 没有有效的序号")
                return
            
            # 显示将要删除的需求单
            print("\n请确认您的操作：")
            for idx in sorted(indices, reverse=True):
                req = self.requirements[idx]
                print(f"删除需求单: [{idx+1}] {req.get('requirement_id', '')} - {req.get('title', '')}")
            
            confirm = input("确定删除吗？(y/n): ").strip().lower()
            
            if confirm == 'y':
                # 从后往前删除，避免索引变化
                for idx in sorted(indices, reverse=True):
                    deleted_req = self.requirements.pop(idx)
                    print(f"✅ 已删除: {deleted_req.get('requirement_id', '')} - {deleted_req.get('title', '')}")
                print(f"✅ 成功删除 {len(indices)} 个需求单")
            else:
                print("❌ 已取消删除")
                
        except KeyboardInterrupt:
            print("\n❌ 操作被中断")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
    
    def clear_all_requirements(self):
        """清除所有需求单"""
        if not self.requirements:
            print("📭 当前没有需求单")
            return
        
        print(f"\n⚠️ 警告：即将清除所有 {len(self.requirements)} 个需求单")
        print("这将删除所有需求单数据，此操作不可恢复！")
        
        confirm1 = input("确定要清除所有需求单吗？(y/n): ").strip().lower()
        if confirm1 != 'y':
            print("❌ 已取消清除操作")
            return
        
        confirm2 = input("请再次确认，真的要清除所有需求单吗？(yes/no): ").strip().lower()
        if confirm2 != 'yes':
            print("❌ 已取消清除操作")
            return
        
        self.requirements.clear()
        print("✅ 已清除所有需求单")
    
    def get_requirements_for_evaluation(self) -> str:
        """获取用于测试用例评估的需求单信息"""
        if not self.requirements:
            return "当前没有可用的需求单信息。"
        
        # 构建需求单摘要
        summary_lines = ["需求单信息摘要："]
        
        for i, req in enumerate(self.requirements[:5], 1):  # 最多显示5个需求单
            title = req.get('title', '无标题')
            req_id = req.get('requirement_id', '无ID')
            desc = req.get('description', '')
            desc_brief = desc[:100] + '...' if len(desc) > 100 else desc
            acceptance = req.get('acceptance_criteria', '')
            local_created_time = req.get('local_created_time', '未知')
            
            summary_lines.append(f"\n{i}. 需求ID: {req_id}")
            summary_lines.append(f"   标题: {title}")
            summary_lines.append(f"   描述: {desc_brief}")
            summary_lines.append(f"   创建时间: {local_created_time}")
            if acceptance:
                summary_lines.append(f"   验收标准: {acceptance[:100]}{'...' if len(acceptance) > 100 else ''}")
        
        if len(self.requirements) > 5:
            summary_lines.append(f"\n... 还有 {len(self.requirements) - 5} 个需求单")
        
        return '\n'.join(summary_lines)


def show_menu():
    """显示主菜单"""
    print("\n" + "="*50)
    print(" _____             _            _____             ")
    print("| __  |___ ___ _ _|_|___ ___   | __  |___ ___ ___ ")
    print("|    -| -_| . | | | |  _| -_|  | __ -| .'|_ -| -_|")
    print("|__|__|___|_  |___|_|_| |___|  |_____|__,|___|___|")
    print("            |_|                                   ")
    print("🎯 测试用例需求单知识库管理器")
    print("="*50)
    print("请选择功能：")
    print("1. 从本地数据提取需求单")
    print("2. 手动输入需求单")
    print("3. 查看现有需求单")
    print("4. 在现有基础上添加需求单")
    print("5. 删除指定需求单")
    print("6. 清除所有需求单")
    print("7. 查看需求单配置文件路径")
    print("0. 安全退出")
    print("-"*50)


def main():
    """主程序"""
    kb = RequirementKnowledgeBase()
    
    print("🎯 测试用例需求单知识库管理器")
    print(f"配置文件: {kb.config_file}")
    print(f"当前需求单数量: {len(kb.requirements)}")
    
    while True:
        try:
            show_menu()
            choice = input("请输入功能编号: ").strip()
            
            if choice == '0':
                print("💾 正在保存并退出...")
                kb._save_requirements()
                print("👋 再见！")
                break
            
            elif choice == '1':
                print("\n🔍 从本地数据提取需求单")
                count = kb.extract_from_local_data()
                if count > 0:
                    kb._save_requirements()
            
            elif choice == '2':
                print("\n📝 手动输入需求单")
                if kb.add_manual_requirement():
                    kb._save_requirements()
            
            elif choice == '3':
                kb.show_requirements()
            
            elif choice == '4':
                print("\n➕ 添加新需求单")
                added = False
                while True:
                    if kb.add_manual_requirement():
                        added = True
                        continue_add = input("是否继续添加？(y/n): ").strip().lower()
                        if continue_add != 'y':
                            break
                    else:
                        break
                if added:
                    kb._save_requirements()
            
            elif choice == '5':
                kb.delete_requirements()
                if kb.requirements:  # 如果还有需求单，保存
                    kb._save_requirements()
                else:  # 如果删除了所有需求单，也要保存（清空文件）
                    kb._save_requirements()
            
            elif choice == '6':
                kb.clear_all_requirements()
                kb._save_requirements()
            
            elif choice == '7':
                print(f"\n📁 需求单配置文件路径: {kb.config_file}")
                print(f"📊 当前需求单数量: {len(kb.requirements)}")
                if kb.config_file.exists():
                    print(f"📅 文件最后修改时间: {kb.config_file.stat().st_mtime}")
                else:
                    print("⚠️ 配置文件尚未创建")
            
            else:
                print("❌ 无效选择，请重新输入")
            
            # 询问是否继续
            if choice != '0':
                input("\n按 Enter 键继续...")
                
        except KeyboardInterrupt:
            print("\n\n💾 检测到 Ctrl+C，正在保存并退出...")
            kb._save_requirements()
            print("👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            input("按 Enter 键继续...")


if __name__ == "__main__":
    main()
