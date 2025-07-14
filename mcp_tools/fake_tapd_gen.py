# fake_tapd_gen.py
"""
TAPD 数据生成器 - 用于生成模拟的 TAPD 需求和缺陷数据

功能：
- 生成模拟的需求（故事）数据，包含算法策略类和功能决策类
- 生成模拟的缺陷数据，包含简单缺陷和详细复现步骤的缺陷
- 支持自定义生成数据量和输出文件路径
- 完全匹配真实TAPD API返回的数据结构
"""
from faker import Faker
import random, uuid, json, pathlib, datetime

fk = Faker("zh_CN")

# 生成长数字ID（匹配TAPD格式）
def generate_tapd_id():
    return f"113785767800100{random.randint(1000, 9999)}"

# 生成TAPD格式的时间字符串
def generate_tapd_time():
    dt = fk.date_time_between(start_date='-1y', end_date='now')
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# ——— 模板列表 ———
DOC_LINK_TPL = "https://docs.qq.com/sheet/DVkt0TGZaTXhWcVZC?tab={}"
IMG_URL_TPL = "/tfl/pictures/202507/tapd_37857678_{}_521.png"
VIDEO_URL = "https://samplelib.com/mp4/sample-5s.mp4"

def fake_doc_link():
    return f"https://docs.qq.com/doc/DZmZnc0JubVpGc0{uuid.uuid4().hex[:2]}"

def fake_img_url():
    return IMG_URL_TPL.format(random.randint(1000000, 9999999))

def fake_demand_A():
    """生成算法策略类需求"""
    created_time = generate_tapd_time()
    modified_time = generate_tapd_time()
    story_id = generate_tapd_id()
    
    base_story = {
        "id": story_id,
        "workitem_type_id": "1137857678001000007",
        "name": f"【算法策略】{fk.word()}接入元宝需求",
        "workspace_id": "37857678",
        "creator": "TAPD",
        "created": created_time,
        "modified": modified_time,
        "status": random.choice(["planning", "developing", "resolved", "status_2", "status_3"]),
        "begin": fk.date_between(start_date='-6m', end_date='+1m').strftime('%Y-%m-%d'),
        "due": fk.date_between(start_date='+1m', end_date='+6m').strftime('%Y-%m-%d'),
        "priority": str(random.randint(1, 4)),
        "iteration_id": random.choice(["0", "1137857678001000003", "1137857678001000004", "1137857678001000005", "1137857678001000006"]),
        "completed": created_time if random.choice([True, False]) else None,
        "category_id": random.choice(["-1", "1137857678001000010"]),
        "path": f"{story_id}:",
        "parent_id": "0",
        "children_id": "|",
        "ancestor_id": story_id,
        "level": "0",
        "effort": str(random.randint(1, 5)),
        "effort_completed": "0",
        "exceed": str(random.randint(-5, 5)),
        "remain": str(random.randint(0, 5)),
        "release_id": "0",
        "templated_id": "1137857678001000010",
        "created_from": "mindmap",
        "label": random.choice(["", "阻塞", "有风险"]),
        "progress": str(random.randint(0, 100)),
        "is_archived": "0",
        "secret_root_id": "0",
        "progress_manual": "0",
        "custom_plan_field_1": "0",
        "custom_plan_field_2": "0",
        "custom_plan_field_3": "0",
        "custom_plan_field_4": "0",
        "custom_plan_field_5": "0",
        "custom_plan_field_6": "0",
        "custom_plan_field_7": "0",
        "custom_plan_field_8": "0",
        "custom_plan_field_9": "0",
        "custom_plan_field_10": "0",
        "priority_label": random.choice(["High", "Middle", "Low", "Nice To Have"])
    }
    
    # 只有约12.5%的需求有description字段（根据真实数据：2/16）
    if random.random() < 0.125:
        description = f"""<p>测试需求腾讯文档链接：</p><p>【腾讯文档】{fk.word()}算法策略文档</p><p><a href="{fake_doc_link()}" target="_blank" rel="noopener">{fake_doc_link()}</a></p><p><br  /></p><p>需求示意图：</p><p class="tox-clear-float"><img src="{fake_img_url()}" style="width: 80%;"  /></p>"""
        base_story["description"] = description
    
    # 约43.75%的需求有owner字段（根据真实数据：7/16）
    if random.random() < 0.4375:
        base_story["owner"] = f"{fk.name()};"
    
    return base_story

def fake_demand_B():
    """生成功能决策类需求"""
    created_time = generate_tapd_time()
    modified_time = generate_tapd_time()
    story_id = generate_tapd_id()
    
    base_story = {
        "id": story_id,
        "workitem_type_id": "1137857678001000007", 
        "name": f"{fk.word()} 根据{fk.word()}结果决定是否请求读书接口",
        "workspace_id": "37857678",
        "creator": "TAPD",
        "created": created_time,
        "modified": modified_time,
        "status": random.choice(["planning", "developing", "resolved", "status_2", "status_3"]),
        "begin": fk.date_between(start_date='-6m', end_date='+1m').strftime('%Y-%m-%d'),
        "due": fk.date_between(start_date='+1m', end_date='+6m').strftime('%Y-%m-%d'),
        "priority": str(random.randint(1, 4)),
        "iteration_id": random.choice(["0", "1137857678001000003", "1137857678001000004", "1137857678001000005", "1137857678001000006"]),
        "completed": created_time if random.choice([True, False]) else None,
        "category_id": random.choice(["-1", "1137857678001000010"]),
        "path": f"{story_id}:",
        "parent_id": "0",
        "children_id": "|",
        "ancestor_id": story_id,
        "level": "0",
        "effort": str(random.randint(1, 5)),
        "effort_completed": "0",
        "exceed": str(random.randint(-5, 5)),
        "remain": str(random.randint(0, 5)),
        "release_id": "0",
        "templated_id": "1137857678001000010",
        "created_from": "mindmap",
        "label": random.choice(["", "阻塞", "有风险"]),
        "progress": str(random.randint(0, 100)),
        "is_archived": "0",
        "secret_root_id": "0",
        "progress_manual": "0",
        "custom_plan_field_1": "0",
        "custom_plan_field_2": "0",
        "custom_plan_field_3": "0",
        "custom_plan_field_4": "0",
        "custom_plan_field_5": "0",
        "custom_plan_field_6": "0",
        "custom_plan_field_7": "0",
        "custom_plan_field_8": "0",
        "custom_plan_field_9": "0",
        "custom_plan_field_10": "0",
        "priority_label": random.choice(["High", "Middle", "Low", "Nice To Have"])
    }
    
    # 只有约12.5%的需求有description字段（根据真实数据：2/16）
    if random.random() < 0.125:
        desc = f"""<p>## 背景</p><p>{fk.paragraph(nb_sentences=3)}</p><p><br /></p><p>## 方案</p><p>{fk.paragraph(nb_sentences=4)}</p><p><br /></p><p>方案文档链接：</p><p><a href="{fake_doc_link()}" target="_blank" rel="noopener">{fake_doc_link()}</a></p><p><br /></p><p>方案示意图：</p><p class="tox-clear-float"><img src="{fake_img_url()}" style="width: 80%;"  /></p>"""
        base_story["description"] = desc
    
    # 约43.75%的需求有owner字段（根据真实数据：7/16）
    if random.random() < 0.4375:
        base_story["owner"] = f"{fk.name()};"
    
    return base_story

def fake_bug_A():
    """生成简单缺陷"""
    created_time = generate_tapd_time()
    modified_time = generate_tapd_time()
    bug_id = generate_tapd_id()
    
    # 为缺陷添加description字段，包含HTML格式的链接和图片
    description = f"""<p>测试腾讯文档链接：</p><p>【腾讯文档】{fk.word()}缺陷报告文档</p><p><a href="{fake_doc_link()}" target="_blank" rel="noopener">{fake_doc_link()}</a></p><p><br  /></p><p>测试图片：</p><p class="tox-clear-float"><img src="{fake_img_url()}" style="width: 80%;"  /></p>"""
    
    return {
        "id": bug_id,
        "title": f"{fk.word()}按钮点击无反应",
        "description": description,
        "priority": random.choice(["medium", "high", "low"]),
        "severity": random.choice(["normal", "serious", "slight"]),
        "status": random.choice(["new", "closed", "resolved"]),
        "reporter": "TAPD",
        "created": created_time,
        "modified": modified_time,
        "lastmodify": fk.name(),
        "version_report": f"版本{random.randint(1, 3)}",
        "iteration_id": random.choice(["1137857678001000003", "1137857678001000004", "1137857678001000005"]),
        "regression_number": str(random.randint(0, 3)),
        "release_id": "0",
        "template_id": random.choice(["0", "1137857678001000013"]),
        "size": str(random.randint(1, 3)),
        "effort": str(random.randint(1, 3)),
        "effort_completed": "0",
        "exceed": str(random.randint(-3, 3)),
        "remain": str(random.randint(0, 3)),
        "secret_root_id": "0",
        "custom_plan_field_1": "0",
        "custom_plan_field_2": "0",
        "custom_plan_field_3": "0",
        "custom_plan_field_4": "0",
        "custom_plan_field_5": "0",
        "custom_plan_field_6": "0",
        "custom_plan_field_7": "0",
        "custom_plan_field_8": "0",
        "custom_plan_field_9": "0",
        "custom_plan_field_10": "0",
        "priority_label": random.choice(["medium", "high", "low"]),
        "workspace_id": "37857678"
    }

def fake_bug_B():
    """生成详细复现步骤的缺陷"""
    created_time = generate_tapd_time()
    modified_time = generate_tapd_time()
    bug_id = generate_tapd_id()
    
    # 详细的复现描述，包含HTML格式的文档链接和图片
    desc = f"""<p>【后台环境】正式</p><p>【分支】发布分支</p><p>【机型】{fk.random_element(elements=['小米10','iPhone15'])} Android13</p><p><br /></p><p>【复现步骤】</p><p>1. 升级 2.29 → 2.30</p><p>2. 使用帮助无法上传日志</p><p><br /></p><p>【预期结果】</p><p>日志可正常上传</p><p><br /></p><p>测试腾讯文档链接：</p><p>【腾讯文档】{fk.word()}复现测试报告</p><p><a href="{fake_doc_link()}" target="_blank" rel="noopener">{fake_doc_link()}</a></p><p><br /></p><p>复现截图：</p><p class="tox-clear-float"><img src="{fake_img_url()}" style="width: 80%;"  /></p>"""
    
    return {
        "id": bug_id,
        "title": f"[Android] 升级测试使用帮助无法上传日志",
        "description": desc,
        "priority": random.choice(["medium", "high", "low"]),
        "severity": random.choice(["normal", "serious", "slight"]),
        "status": random.choice(["new", "closed", "resolved"]),
        "reporter": "TAPD",
        "created": created_time,
        "resolved": modified_time if random.choice([True, False]) else None,
        "closed": modified_time if random.choice([True, False]) else None,
        "modified": modified_time,
        "lastmodify": fk.name(),
        "version_report": f"版本{random.randint(1, 3)}",
        "iteration_id": random.choice(["1137857678001000003", "1137857678001000004", "1137857678001000005"]),
        "resolution": random.choice(["fixed", "duplicate", "wontfix", ""]),
        "regression_number": str(random.randint(0, 3)),
        "release_id": "0",
        "verify_time": modified_time if random.choice([True, False]) else None,
        "template_id": random.choice(["0", "1137857678001000013"]),
        "label": random.choice(["", "有风险", "阻塞"]),
        "size": str(random.randint(1, 3)),
        "effort": str(random.randint(1, 3)),
        "effort_completed": "0",
        "exceed": str(random.randint(-3, 3)),
        "remain": str(random.randint(0, 3)),
        "secret_root_id": "0",
        "custom_plan_field_1": "0",
        "custom_plan_field_2": "0",
        "custom_plan_field_3": "0",
        "custom_plan_field_4": "0",
        "custom_plan_field_5": "0",
        "custom_plan_field_6": "0",
        "custom_plan_field_7": "0",
        "custom_plan_field_8": "0",
        "custom_plan_field_9": "0",
        "custom_plan_field_10": "0",
        "priority_label": random.choice(["medium", "high", "low"]),
        "workspace_id": "37857678"
    }

# ——— 入口 ———
def generate(n_story_A=300, n_story_B=200,
             n_bug_A=400, n_bug_B=300, path="../local_data/msg_from_fetcher.json"):
    """
    生成TAPD测试数据
    
    参数:
        n_story_A: 算法策略类需求数量
        n_story_B: 功能决策类需求数量
        n_bug_A: 简单缺陷数量
        n_bug_B: 详细缺陷数量
        path: 输出文件路径
    """
    # 生成需求和缺陷数据（已经包含完整的字段结构）
    stories = [fake_demand_A() for _ in range(n_story_A)] + [fake_demand_B() for _ in range(n_story_B)]
    bugs = [fake_bug_A() for _ in range(n_bug_A)] + [fake_bug_B() for _ in range(n_bug_B)]
    
    # 构建与TAPD API一致的数据格式
    data_to_save = {
        'stories': stories,
        'bugs': bugs
    }
    
    # 确保目标目录存在
    import os
    dir_path = os.path.dirname(path)
    if dir_path:  # 只有当路径包含目录时才创建
        os.makedirs(dir_path, exist_ok=True)
    
    # 强制覆盖写入文件（确保不是追加模式）
    try:
        # 使用 pathlib.Path().write_text() 默认就是覆盖模式
        pathlib.Path(path).write_text(json.dumps(data_to_save, ensure_ascii=False, indent=4), encoding='utf-8')
        # 使用安全的输出格式，避免emoji字符
        print(f"[SUCCESS] Generated {len(stories)} stories and {len(bugs)} bugs -> {path}")
    except UnicodeEncodeError as e:
        # 如果仍有编码问题，使用ASCII安全的JSON输出
        pathlib.Path(path).write_text(json.dumps(data_to_save, ensure_ascii=True, indent=4), encoding='utf-8')
        print(f"[SUCCESS] Generated {len(stories)} stories and {len(bugs)} bugs -> {path} (ASCII mode)")
    except Exception as e:
        # 如果还有其他问题，抛出详细错误
        raise RuntimeError(f"Failed to write file {path}: {str(e)}")

# ——— 提供给MCP工具调用的异步函数 ———
async def generate_fake_tapd_data(n_story_A: int = 50, n_story_B: int = 30, 
                                 n_bug_A: int = 40, n_bug_B: int = 20,
                                 output_path: str = "local_data/msg_from_fetcher.json") -> dict:
    """
    生成模拟TAPD数据的异步函数，供MCP工具调用
    
    参数:
        n_story_A: 算法策略类需求数量
        n_story_B: 功能决策类需求数量  
        n_bug_A: 简单缺陷数量
        n_bug_B: 详细缺陷数量
        output_path: 输出文件路径
        
    返回:
        生成结果字典
    """
    try:
        # 如果不是绝对路径，转换为相对于项目根目录的路径
        if not pathlib.Path(output_path).is_absolute():
            base_dir = pathlib.Path(__file__).parent.parent
            output_path = str(base_dir / output_path)
        
        generate(n_story_A, n_story_B, n_bug_A, n_bug_B, output_path)
        
        return {
            "status": "success",
            "message": f"成功生成 {n_story_A + n_story_B} 个需求和 {n_bug_A + n_bug_B} 个缺陷",
            "details": {
                "stories": {
                    "algorithm_strategy": n_story_A,
                    "functional_decision": n_story_B,
                    "total": n_story_A + n_story_B
                },
                "bugs": {
                    "simple": n_bug_A,
                    "detailed": n_bug_B,
                    "total": n_bug_A + n_bug_B
                },
                "output_path": output_path
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"生成数据失败: {str(e)}"
        }

if __name__ == "__main__":
    generate()
