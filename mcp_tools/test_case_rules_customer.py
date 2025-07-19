"""
测试用例评估规则自定义配置

本脚本用于配置测试用例AI评估的规则参数，支持以下配置项：
1. 标题长度限制
2. 步骤数上限
3. 三类优先级占比范围

配置操作说明：
1. 查看当前配置：运行 python test_case_rules_customer.py
2. 修改配置：运行 python test_case_rules_customer.py --config
3. 重置为默认：运行 python test_case_rules_customer.py --reset
4. 查看配置项说明：运行 python test_case_rules_customer.py --help

配置文件存储位置：local_data/test_case_rules.json
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_tools.common_utils import get_config, get_file_manager


class TestCaseRulesCustomer:
    """测试用例规则自定义配置管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.file_manager = get_file_manager()
        self.config_file = self.config.local_data_path / "test_case_rules.json"
        
        # 默认配置（来自原始提示词）
        self.default_config = {
            "title_max_length": 40,  # 标题最大长度
            "max_steps": 10,         # 步骤数上限
            "priority_ratios": {     # 优先级占比
                "P0": {"min": 10, "max": 20},  # P0占比10%-20%
                "P1": {"min": 60, "max": 70},  # P1占比60%-70%
                "P2": {"min": 10, "max": 30}   # P2占比10%-30%
            },
            "version": "1.0",
            "last_updated": None
        }
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        返回:
            配置字典，如果文件不存在则返回默认配置
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                # 验证配置完整性
                if self._validate_config(config_data):
                    return config_data
                else:
                    print("配置文件格式错误，使用默认配置")
                    return self.default_config.copy()
            else:
                print("配置文件不存在，创建默认配置")
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            return self.default_config.copy()
    
    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """
        保存配置到文件
        
        参数:
            config_data: 配置数据
            
        返回:
            是否保存成功
        """
        try:
            # 添加时间戳
            from datetime import datetime
            config_data["last_updated"] = datetime.now().isoformat()
            
            self.file_manager.save_json_data(config_data, str(self.config_file))
            print(f"配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def _validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        验证配置数据的完整性和有效性
        
        参数:
            config_data: 要验证的配置数据
            
        返回:
            是否有效
        """
        try:
            # 检查必需的键
            required_keys = ["title_max_length", "max_steps", "priority_ratios"]
            for key in required_keys:
                if key not in config_data:
                    print(f"缺少必需的配置项: {key}")
                    return False
            
            # 验证数值范围
            if not (1 <= config_data["title_max_length"] <= 200):
                print("标题长度限制应在1-200之间")
                return False
            
            if not (1 <= config_data["max_steps"] <= 50):
                print("步骤数上限应在1-50之间")
                return False
            
            # 验证优先级占比
            priority_ratios = config_data["priority_ratios"]
            for priority in ["P0", "P1", "P2"]:
                if priority not in priority_ratios:
                    print(f"缺少优先级配置: {priority}")
                    return False
                
                ratio_config = priority_ratios[priority]
                if "min" not in ratio_config or "max" not in ratio_config:
                    print(f"{priority}缺少min或max配置")
                    return False
                
                min_val, max_val = ratio_config["min"], ratio_config["max"]
                if not (0 <= min_val <= max_val <= 100):
                    print(f"{priority}占比配置无效: min={min_val}, max={max_val}")
                    return False
            
            return True
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
    
    def interactive_config(self):
        """交互式配置界面"""
        print("\n=== 测试用例评估规则配置 ===")
        print("当前配置项修改（直接回车保持当前值）：\n")
        
        current_config = self.load_config()
        new_config = current_config.copy()
        
        # 1. 配置标题长度
        current_title_length = current_config["title_max_length"]
        while True:
            try:
                title_input = input(f"标题最大长度 (当前: {current_title_length}字符): ").strip()
                if not title_input:
                    break
                
                title_length = int(title_input)
                if 1 <= title_length <= 200:
                    new_config["title_max_length"] = title_length
                    break
                else:
                    print("标题长度应在1-200之间，请重新输入")
            except ValueError:
                print("请输入有效的数字")
        
        # 2. 配置步骤数上限
        current_max_steps = current_config["max_steps"]
        while True:
            try:
                steps_input = input(f"步骤数上限 (当前: {current_max_steps}步): ").strip()
                if not steps_input:
                    break
                
                max_steps = int(steps_input)
                if 1 <= max_steps <= 50:
                    new_config["max_steps"] = max_steps
                    break
                else:
                    print("步骤数上限应在1-50之间，请重新输入")
            except ValueError:
                print("请输入有效的数字")
        
        # 3. 配置优先级占比
        print("\n优先级占比配置（格式：最小值-最大值，如：10-20）：")
        priority_ratios = new_config["priority_ratios"].copy()
        
        for priority in ["P0", "P1", "P2"]:
            current_ratio = priority_ratios[priority]
            current_range = f"{current_ratio['min']}-{current_ratio['max']}"
            
            while True:
                ratio_input = input(f"{priority}占比% (当前: {current_range}%): ").strip()
                if not ratio_input:
                    break
                
                try:
                    if '-' in ratio_input:
                        min_str, max_str = ratio_input.split('-', 1)
                        min_val, max_val = int(min_str.strip()), int(max_str.strip())
                        
                        if 0 <= min_val <= max_val <= 100:
                            priority_ratios[priority] = {"min": min_val, "max": max_val}
                            break
                        else:
                            print("占比应在0-100之间，且最小值不大于最大值，请重新输入")
                    else:
                        print("格式错误，请使用'最小值-最大值'格式，如：10-20")
                except ValueError:
                    print("请输入有效的数字范围")
        
        new_config["priority_ratios"] = priority_ratios
        
        # 4. 确认并保存
        print("\n新配置预览：")
        self._display_config(new_config)
        
        confirm = input("\n确认保存此配置？(y/n): ").strip().lower()
        if confirm in ['y', 'yes', '是']:
            if self.save_config(new_config):
                print("配置保存成功！")
            else:
                print("配置保存失败！")
        else:
            print("配置未保存")
    
    def reset_to_default(self):
        """重置为默认配置"""
        print("重置为默认配置...")
        if self.save_config(self.default_config.copy()):
            print("已重置为默认配置")
            self._display_config(self.default_config)
        else:
            print("重置失败")
    
    def _display_config(self, config_data: Dict[str, Any]):
        """显示配置信息"""
        print(f"标题最大长度: {config_data['title_max_length']}字符")
        print(f"步骤数上限: {config_data['max_steps']}步")
        print("优先级占比:")
        for priority, ratio in config_data["priority_ratios"].items():
            print(f"  {priority}: {ratio['min']}-{ratio['max']}%")
        if config_data.get("last_updated"):
            print(f"最后更新: {config_data['last_updated']}")
    
    def display_current_config(self):
        """显示当前配置"""
        print("\n=== 当前测试用例评估规则配置 ===")
        config_data = self.load_config()
        self._display_config(config_data)
        print(f"\n配置文件位置: {self.config_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="测试用例评估规则自定义配置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python test_case_rules_customer.py              # 查看当前配置
  python test_case_rules_customer.py --config     # 交互式配置
  python test_case_rules_customer.py --reset      # 重置为默认配置
        """
    )
    
    parser.add_argument('--config', action='store_true', help='进入交互式配置模式')
    parser.add_argument('--reset', action='store_true', help='重置为默认配置')
    
    args = parser.parse_args()
    
    customer = TestCaseRulesCustomer()
    
    if args.config:
        customer.interactive_config()
    elif args.reset:
        customer.reset_to_default()
    else:
        customer.display_current_config()


# 供其他模块调用的接口函数
def get_test_case_rules() -> Dict[str, Any]:
    """
    获取当前测试用例评估规则配置
    
    返回:
        配置字典
    """
    customer = TestCaseRulesCustomer()
    return customer.load_config()


if __name__ == "__main__":
    print(" _____         _                        _____     _         ")
    print("|     |_ _ ___| |_ ___ _____ ___ ___   | __  |_ _| |___ ___ ")
    print("|   --| | |_ -|  _| . |     | -_|  _|  |    -| | | | -_|_ -|")
    print("|_____|___|___|_| |___|_|_|_|___|_|    |__|__|___|_|___|___|")
    main()
