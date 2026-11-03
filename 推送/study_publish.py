"""Codex每日专题的补发检查与单日发布；不会自行调用模型或设置系统任务。"""
import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
import subprocess
from study_plan import ROOT, DEST, START, plans

END = START + timedelta(days=31)
REMOTE = 'origin'
BRANCH = 'master'

def today_shanghai():
    return datetime.now(timezone(timedelta(hours=8))).date()

def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, text=True,
                          encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

def marker(day):
    return f'<!-- study-materials:{day.isoformat()} -->'

def validate(content, day):
    if marker(day) not in content:
        raise ValueError('缺少当日资料完成标记；禁止将占位页当作已生成资料')
    required = ('## 今日四科任务', '## 今日联网资料', '## 配套练习', '## 参考答案与解析', '## 来源与核验', '实际检索日期：')
    if any(section not in content for section in required):
        raise ValueError('缺少任务、资料、练习、解析、来源或实际检索日期')
    source_section = content.split('## 来源与核验', 1)[1]
    sources = set(re.findall(r'https?://[^\s)<>]+', source_section))
    if len(sources) < 3:
        raise ValueError('来源与核验区至少需要3个不同的实际阅读页面链接')
    if '待生成' in content.split('## 今日联网资料', 1)[1].split('## 配套练习', 1)[0]:
        raise ValueError('今日联网资料仍为占位内容')

def due_days(today):
    limit = min(today, END)
    return [START+timedelta(days=i) for i in range(32) if START+timedelta(days=i) <= limit]

def relative(day):
    if not START <= day <= END:
        raise ValueError('日期不属于32天计划')
    return (DEST / f'{day.isoformat()}.md').relative_to(ROOT).as_posix()

def pending(today, fetch=True):
    if fetch:
        git('fetch', REMOTE, BRANCH)
    missing = []
    for day in due_days(today):
        path = relative(day)
        # ls-tree空输出表示远端没有该页；其他Git错误必须显式报告。
        exists = git('ls-tree', '--name-only', f'{REMOTE}/{BRANCH}', '--', path).strip()
        if not exists:
            missing.append(day)
            continue
        content = git('show', f'{REMOTE}/{BRANCH}:{path}')
        try:
            validate(content, day)
        except ValueError:
            missing.append(day)
    return missing

def publish(day):
    if day > today_shanghai():
        raise ValueError('不能提前发布未来日期的“当日检索”资料')
    path = relative(day)
    content = (ROOT/path).read_text(encoding='utf-8')
    validate(content, day)
    git('fetch', REMOTE, BRANCH)
    if git('symbolic-ref', '--short', 'HEAD').strip() != BRANCH:
        raise ValueError('当前不在发布分支master；请人工处理，脚本不切换分支')
    staged = git('diff', '--cached', '--name-only').splitlines()
    if staged:
        raise ValueError('暂存区已有内容；请先处理，脚本不会提交其他人的改动')
    remote_tip = git('rev-parse', f'{REMOTE}/{BRANCH}').strip()
    # 远端前进或分叉时停止；不自动重置、合并或变基工作区。
    git('merge-base', '--is-ancestor', remote_tip, 'HEAD')
    git('add', '--', path)
    if git('diff', '--cached', '--name-only').strip():
        git('commit', '-m', f'docs: publish study materials for {day.isoformat()}', '--', path)
    git('push', REMOTE, f'HEAD:{BRANCH}')
    git('fetch', REMOTE, BRANCH)
    remote_content = git('show', f'{REMOTE}/{BRANCH}:{path}')
    validate(remote_content, day)
    if remote_content != content:
        raise ValueError('远端内容与本地不一致，需要人工检查')
    print(f'已验证远端发布：{day.isoformat()}')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    listing = sub.add_parser('pending', help='联网检查截至北京时间今天的未发布日期')
    listing.add_argument('--as-of', type=date.fromisoformat)
    listing.add_argument('--no-fetch', action='store_true', help='仅用于离线预览，不代表已核验远端')
    checking = sub.add_parser('validate')
    checking.add_argument('date', type=date.fromisoformat)
    publishing = sub.add_parser('publish')
    publishing.add_argument('date', type=date.fromisoformat)
    args = parser.parse_args()
    if args.command == 'pending':
        days = pending(args.as_of or today_shanghai(), fetch=not args.no_fetch)
        for day in days:
            print(day.isoformat())
        if not days:
            print('没有待补发日期')
    elif args.command == 'validate':
        validate((ROOT/relative(args.date)).read_text(encoding='utf-8'), args.date)
        print('资料结构检查通过；来源真实性仍须由生成者逐条核验')
    else:
        publish(args.date)

if __name__ == '__main__':
    main()
