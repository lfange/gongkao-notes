#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公考日报 · 每日定时推送脚本
================================================================
- 当日学习任务：按【日期 / 阶段 / 星期】模板生成（来自总体计划，零依赖）
- 知识点 / 每日一题 / 时政热点：调用 OpenAI 兼容 LLM API 生成
- 推送渠道：Server酱 或 PushPlus（二选一，在 config.json 配置）

用法:
  python3 daily_push.py            # 正常生成并推送当日日报
  python3 daily_push.py --test     # 发送一条测试消息（验证推送配置）
  python3 daily_push.py --dry-run  # 只打印内容到屏幕，不推送

部署说明见同目录 README.md（配合 cron 每天定时运行）。
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

# ==================== 计划阶段（与 计划/总体计划.md 保持一致）====================
# 如调整阶段时间，同步修改这里。
PHASES = [
    (date(2026, 7, 14),  date(2026, 9, 30),  "基础筑基",         "系统过完行测+申论知识点，建立框架"),
    (date(2026, 10, 1),  date(2026, 11, 30), "专项突破·国考冲刺", "模块刷题提速，11月底国考实战"),
    (date(2026, 12, 1),  date(2027, 2, 28),  "国考复盘·省考巩固", "复盘找差距，申论大作文成型"),
    (date(2027, 3, 1),   date(2027, 4, 15),  "省考冲刺",         "套卷模考，省考笔试"),
]

START_DATE = date(2026, 7, 14)
GUOKAO_DATE = date(2026, 11, 29)    # 国考笔试（约，以公告为准）
SHENGKAO_DATE = date(2027, 3, 28)   # 省考笔试（约，因省而异，以公告为准）

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
# 工作日（周一~周五）主攻模块轮转
WEEKDAY_MODULES = ["资料分析", "判断推理", "言语理解", "资料分析", "判断推理"]


def get_phase(today):
    for start, end, name, desc in PHASES:
        if start <= today <= end:
            return name, desc
    return "休整/待规划", "暂无阶段任务，可自主复习或调整计划"


def get_today_task(today):
    """返回 (weekday_str, task_text, est_hours, module_label)"""
    phase_name, _ = get_phase(today)
    wd = today.weekday()  # 0=周一
    weekday_str = WEEKDAY_CN[wd]

    if wd < 5:  # 工作日
        module = WEEKDAY_MODULES[wd]
        if phase_name.startswith("基础"):
            task = (f"{module} · 基础学习（看网课/教材，笔记记到 行测/{module}/笔记.md）\n"
                    f"+ 常识碎片积累 15 分钟\n"
                    f"+ 当日错题记入错题本")
        elif phase_name.startswith("专项"):
            task = (f"{module} · 专项限时刷题（卡时间，错题复盘）\n"
                    f"+ 常识碎片 15 分钟")
        elif phase_name.startswith("国考复盘"):
            task = (f"{module} · 弱项专项突破 + 套卷片段限时\n"
                    f"+ 错题二刷")
        else:  # 省考冲刺
            task = (f"{module} · 省考真题专项 + 限时训练\n"
                    f"+ 时政热点速记")
        hours = "约 2 小时"
        return weekday_str, task, hours, module

    if wd == 5:  # 周六
        module = "数量关系/申论"
        if phase_name.startswith("基础"):
            task = "数量关系 · 高频题型（工程/利润/容斥）\n申论 · 1 篇小题练习"
        elif phase_name.startswith("专项"):
            task = "数量关系 · 专项 + 申论小题/半篇大作文"
        elif phase_name.startswith("国考复盘"):
            task = "申论 · 1 篇完整大作文（限时 50 分钟）\n数量关系 · 查漏"
        else:
            task = "申论 · 大作文 + 时政素材背诵"
        hours = "约 3 小时"
        return weekday_str, task, hours, module

    # 周日
    module = "套卷/申论"
    task = "周测 / 模考（行测 120 分钟限时）\n申论小题 + 周复盘（填 计划/每日打卡.md）"
    hours = "约 3 小时"
    return weekday_str, task, hours, module


# ==================== 配置 ====================
def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"❌ 找不到配置文件：{CONFIG_PATH}\n"
                 f"   请复制 config.example.json 为 config.json 并填入密钥。")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================== LLM（OpenAI 兼容）====================
def call_llm(cfg, prompt):
    """调用 OpenAI 兼容 chat/completions 接口，返回文本；失败返回 None。"""
    base = cfg.get("llm_base_url", "https://api.deepseek.com").rstrip("/")
    url = base + "/chat/completions"
    payload = {
        "model": cfg.get("llm_model", "deepseek-chat"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1800,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + cfg.get("llm_api_key", ""),
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️  LLM 调用失败: {e}", file=sys.stderr)
        return None


def build_llm_prompt(today, phase_name, module):
    return (
        f"你是公考辅导老师。今天是 {today.isoformat()}，学生处于【{phase_name}】阶段，"
        f"今日主攻【{module}】。请用 Markdown 输出三部分（标题用 ## ）：\n\n"
        f"## 📖 每日知识点\n围绕【{module}】讲一个核心考点，150 字以内，含解题方法。\n\n"
        f"## ✏️ 每日一题\n出一道【{module}】的练习题，先给题干和选项，再用 > 引用块给出解析。\n\n"
        f"## 📰 时政热点\n列出近期 3 条时政要点，每条一句话，服务于申论和常识积累。\n\n"
        f"只输出这三部分，不要额外寒暄。"
    )


# ==================== 推送 ====================
def push_serverchan(key, title, content):
    url = f"https://sctapi.ftqq.com/{key}.send"
    data = urllib.parse.urlencode({"title": title, "desp": content}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def push_pushplus(token, title, content):
    url = "https://www.pushplus.plus/send"
    payload = {"token": token, "title": title, "content": content, "template": "markdown"}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def push(cfg, title, content):
    channel = cfg.get("push_channel", "serverchan").lower()
    try:
        if channel == "pushplus":
            res = push_pushplus(cfg.get("pushplus_token", ""), title, content)
            ok = res.get("code") == 200
        else:  # serverchan
            res = push_serverchan(cfg.get("serverchan_key", ""), title, content)
            ok = res.get("code") == 0
        print(f"推送结果（{channel}）: {res}")
        return ok
    except Exception as e:
        print(f"❌ 推送失败: {e}", file=sys.stderr)
        return False


# ==================== 主流程 ====================
def main():
    ap = argparse.ArgumentParser(description="日报每日推送")
    ap.add_argument("--test", action="store_true", help="发送测试消息，验证推送配置")
    ap.add_argument("--dry-run", action="store_true", help="只打印内容，不推送")
    args = ap.parse_args()

    cfg = load_config()
    today = date.today()

    # ---- 测试模式 ----
    if args.test:
        title = "✅ 日报推送测试"
        content = ("这是一条测试消息。如果你在微信里看到它，说明推送配置成功！\n\n"
                   "- 渠道配置 ✅\n"
                   "- 接下来设置 cron 每天定时运行，就能自动收到公考日报了。")
        if args.dry_run:
            print(content)
            return
        sys.exit(0 if push(cfg, title, content) else 1)

    # ---- 模板部分：今日任务 ----
    phase_name, phase_desc = get_phase(today)
    weekday_str, task, hours, module = get_today_task(today)
    day_n = (today - START_DATE).days + 1
    d_gk = (GUOKAO_DATE - today).days
    d_sk = (SHENGKAO_DATE - today).days

    header = (
        f"# 📚 公考日报 · {today.isoformat()}（第 {day_n} 天）\n\n"
        f"⏰ 距国考 **{d_gk}** 天 ｜ 距省考 **{d_sk}** 天\n"
        f"📍 当前阶段：**{phase_name}** — {phase_desc}\n\n---\n\n"
        f"## 🎯 今日任务（{weekday_str}）\n{task}\n\n"
        f"⏱️ 预计 {hours}\n\n---\n"
    )

    # ---- LLM 部分：知识点 + 一题 + 时政 ----
    prompt = build_llm_prompt(today, phase_name, module)
    llm_text = call_llm(cfg, prompt)
    if not llm_text:
        llm_text = (f"## ⚠️ 今日 AI 内容生成失败\n"
                    f"LLM 调用出错，请手动学习【{module}】并自行浏览时政。\n"
                    f"（检查 config.json 的 llm_api_key / llm_base_url / llm_model）\n")

    footer = ("\n---\n\n"
              "📝 打卡：`计划/每日打卡.md` ｜ 错题：`错题本.md`\n"
              "💪 坚持就是上岸，今天也要动手！\n")

    content = header + "\n" + llm_text + footer
    title = f"公考日报 {today.isoformat()} · {phase_name} · {module}"

    if args.dry_run:
        print("=" * 30 + " DRY RUN " + "=" * 30)
        print(f"TITLE: {title}\n")
        print(content)
        return

    sys.exit(0 if push(cfg, title, content) else 1)


if __name__ == "__main__":
    main()
