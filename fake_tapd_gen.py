# fake_tapd_gen.py
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
             n_bug_A=400, n_bug_B=300, path="fake_tapd.json"):
    items = (
        [fake_demand_A() for _ in range(n_story_A)] +
        [fake_demand_B() for _ in range(n_story_B)] +
        [fake_bug_A() for _ in range(n_bug_A)] +
        [fake_bug_B() for _ in range(n_bug_B)]
    )
    # 公共字段
    for itm in items:
        itm.update({
            "priority": random.choice(["P0","P1","P2"]),
            "status": random.choice(["open","resolved","closed"]),
            "created": fk.date_time_between("-120d").isoformat(),
            "owner": fk.name(),
            "tags": random.sample(["性能", "安全", "核心流程", "上线前"], k=random.randint(0,2))
        })
    pathlib.Path(path).write_text(json.dumps(items, ensure_ascii=False, indent=2))
    print(f"✅ 生成 {len(items)} 条数据 → {path}")

if __name__ == "__main__":
    generate()
