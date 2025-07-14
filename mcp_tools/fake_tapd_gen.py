# fake_tapd_gen.py
"""
TAPD 数据生成器 - 用于生成模拟的 TAPD 需求和缺陷数据

功能：
- 生成模拟的需求（故事）数据，包含算法策略类和功能决策类
- 生成模拟的缺陷数据，包含简单缺陷和详细复现步骤的缺陷
- 支持自定义生成数据量和输出文件路径
- 为每条数据添加优先级、状态、创建时间、负责人、标签等公共字段
"""
from faker import Faker
import random, uuid, json, pathlib, datetime

fk = Faker("zh_CN")

# ——— 模板列表 ———
DOC_LINK_TPL = "https://doc.weixin.qq.com/doc/{}_?scode=AJEAIQ{}".format
IMG_URL = lambda : f"https://picsum.photos/seed/{uuid.uuid4().hex[:6]}/800/400"
VIDEO_URL = "https://samplelib.com/mp4/sample-5s.mp4"

def fake_doc_link():
    return DOC_LINK_TPL(uuid.uuid4().hex[:6].upper(), uuid.uuid4().hex[:6].upper())

def fake_demand_A():
    return {
        "id": f"STORY_{uuid.uuid4().hex[:8]}",
        "type": "story",
        "title": f"[算法策略] {fk.word()}接入元宝需求",
        "description": f"需求文档：{fake_doc_link()}",
        "attachments": [],
    }

def fake_demand_B():
    desc = (
        f"## 背景\n{fk.paragraph(nb_sentences=3)}\n\n"
        f"## 方案\n{fk.paragraph(nb_sentences=4)}\n\n"
        f"![需求示意图]({IMG_URL()})"
    )
    return {
        "id": f"STORY_{uuid.uuid4().hex[:8]}",
        "type": "story",
        "title": f"{fk.word()} 根据{fk.word()}结果决定是否请求读书接口",
        "description": desc,
        "attachments": [{"name": "方案图.png", "type": "image", "url": IMG_URL()}],
    }

def fake_bug_A():
    return {
        "id": f"BUG_{uuid.uuid4().hex[:8]}",
        "type": "bug",
        "title": f"{fk.word()}按钮点击无反应",
        "description": f"只有一张截图复现：\n\n![截图]({IMG_URL()})",
        "attachments": [{"name": "bug.png", "type": "image", "url": IMG_URL()}],
    }

def fake_bug_B():
    desc = (
        "【后台环境】正式\n"
        "【分支】发布分支\n"
        f"【机型】{fk.random_element(elements=['小米10','iPhone15'])} Android13\n\n"
        "【复现步骤】\n"
        "1. 升级 2.29 → 2.30\n"
        "2. 使用帮助无法上传日志\n\n"
        "【预期结果】\n日志可正常上传\n\n"
        f"【复现视频】\n{VIDEO_URL}"
    )
    att = [{"name": "复现视频.mp4", "type": "video", "url": VIDEO_URL}]
    return {
        "id": f"BUG_{uuid.uuid4().hex[:8]}",
        "type": "bug",
        "title": "[Android] 升级测试使用帮助无法上传日志",
        "description": desc,
        "attachments": att,
    }

# ——— 入口 ———
def generate(n_story_A=300, n_story_B=200,
             n_bug_A=400, n_bug_B=300, path="../local_data/msg_from_fetcher.json"):
    # 分别生成需求和缺陷数据
    stories = [fake_demand_A() for _ in range(n_story_A)] + [fake_demand_B() for _ in range(n_story_B)]
    bugs = [fake_bug_A() for _ in range(n_bug_A)] + [fake_bug_B() for _ in range(n_bug_B)]
    
    # 为需求数据添加公共字段
    for story in stories:
        story.update({
            "priority": random.choice(["P0","P1","P2"]),
            "status": random.choice(["open","resolved","closed"]),
            "created": fk.date_time_between("-120d").isoformat(),
            "owner": fk.name(),
            "tags": random.sample(["性能", "安全", "核心流程", "上线前"], k=random.randint(0,2))
        })
    
    # 为缺陷数据添加公共字段
    for bug in bugs:
        bug.update({
            "priority": random.choice(["P0","P1","P2"]),
            "status": random.choice(["open","resolved","closed"]),
            "created": fk.date_time_between("-120d").isoformat(),
            "owner": fk.name(),
            "tags": random.sample(["性能", "安全", "核心流程", "上线前"], k=random.randint(0,2))
        })
    
    # 构建与其他模块一致的数据格式
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

if __name__ == "__main__":
    generate()
