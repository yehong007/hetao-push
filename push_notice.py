#!/usr/bin/env python3
"""
企微群机器人定时推送 - GitHub Actions 版本
用法: python3 push_notice.py <slot>
slot: morning | noon-after | evening | night | night2 | tcm
"""
import sys
import os
import base64
import hashlib
import json
import urllib.request
from datetime import datetime

WEBHOOK = os.environ.get("WQ_WEBHOOK")
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
# Actions 自带日志，不用本地 log

SLOTS = {
    "morning":     {"img": "12-45.png", "text": "午会前工作卡打卡",                                                                                       "title": "12:45 午会起飞前"},
    "noon-after":  {"img": "13-00.png", "text": "午会后工作卡打卡",                                                                                       "title": "13:00 午会后"},
    "evening":     {"img": "18-00.png", "text": "高峰期晚间工作卡打卡",                                                                                   "title": "18:00 夕会后"},
    "night":       {"img": "22-00.png", "text": "一天收官准备打卡，全量培养代替局部筛选",                                                                 "title": "22:00 晚间落地收官"},
    "night2":      {"img": "22-30.png", "text": "全量培养代替局部筛选，每天回收团队目前在三阶段的客户数，改变伙伴行为，建立全量培养的意识",         "title": "22:30 晚间落地收官"},
    "tcm":         {"img": "tcm.png",    "text": "老中医们，四诊望闻问切执行了吗？",                                                                       "title": "中医四诊望闻问切"},
}

WEEK_CN = ["日", "一", "二", "三", "四", "五", "六"]


def post(payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def push_image(img_path: str) -> dict:
    with open(img_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    md5 = hashlib.md5(data).hexdigest()
    return post({"msgtype": "image", "image": {"base64": b64, "md5": md5}})


def push_text(title: str, text: str) -> dict:
    now = datetime.now()
    dow = WEEK_CN[int(now.strftime("%w"))]
    today = now.strftime(f"%Y-%m-%d 星期{dow} %H:%M")
    content = f"## {title}\n> {today}\n\n**{text}**"
    return post({"msgtype": "markdown", "markdown": {"content": content}})


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SLOTS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(SLOTS.keys())}>", file=sys.stderr)
        sys.exit(2)

    if not WEBHOOK:
        print("ERROR: WQ_WEBHOOK env var not set", file=sys.stderr)
        sys.exit(1)

    slot = sys.argv[1]
    cfg = SLOTS[slot]
    img_path = os.path.join(IMG_DIR, cfg["img"])

    if not os.path.isfile(img_path):
        print(f"ERROR: image not found: {img_path}", file=sys.stderr)
        sys.exit(1)

    # 1) 图片在前
    img_resp = push_image(img_path)
    print(f"IMAGE -> {img_resp}")

    # 2) 文字在后
    txt_resp = push_text(cfg["title"], cfg["text"])
    print(f"TEXT  -> {txt_resp}")

    if img_resp.get("errcode") == 0 and txt_resp.get("errcode") == 0:
        print(f"OK [{slot}] 推送成功")
        sys.exit(0)
    else:
        print(f"FAIL [{slot}] 推送失败", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
