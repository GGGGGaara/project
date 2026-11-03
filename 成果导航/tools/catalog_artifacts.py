"""Inventory research artifacts and verify this documentation-only organization.

Run from any working directory. Uses only the Python standard library.
Does not execute simulation, import its modules, or modify experiment output.
"""
from pathlib import Path
from collections import Counter
from urllib.parse import unquote, urlsplit
import csv
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
NAV = ROOT / '成果导航'
ROOT_ITEMS = (
    'README.md', '.gitignore', '.gitattributes', '成果导航', 'STV_ED_motion_study',
    'STV_ED_reproducible_pilot_bundle', 'STV_ED_reproducible_pilot_bundle.zip',
    'STV_ED_review_20261103', 'acc_observation_gap',
    'market_decision_research', 'timetrap_translation',
    '智能车辆_ITSC_ICMA文献与选题分析报告.md',
)
EXCLUDED_DIRS = {'__pycache__', 'python_packages', '.git'}
GENERATED = {'成果导航/文件清单.csv', '成果导航/分类统计.json', '成果导航/整理校验.json'}
ALLOWED_CHANGED = {'STV_ED_motion_study/WORK_LOG.md'}
BASELINE_PATH = NAV / '整理前文件快照.json'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan():
    paths = []
    for name in ROOT_ITEMS:
        item = ROOT / name
        candidates = item.rglob('*') if item.is_dir() else [item]
        for path in candidates:
            if not path.is_file():
                continue
            if EXCLUDED_DIRS.intersection(path.relative_to(ROOT).parts):
                continue
            if path.relative_to(ROOT).as_posix() not in GENERATED:
                paths.append(path)
    return sorted(set(paths))


def stage_for(rel):
    parts = rel.parts
    top = parts[0]
    if top.startswith('STV_ED_reproducible_pilot_bundle'):
        return 'S00 原始调度'
    if top == 'STV_ED_review_20261103':
        return 'S00-R 审阅复现'
    if top in ('acc_observation_gap', 'market_decision_research', 'timetrap_translation'):
        return {'acc_observation_gap': 'H-ACC 观测中断',
                'market_decision_research': 'H-MARKET 等待位姿',
                'timetrap_translation': 'H-TIMETRAP 阅读翻译'}[top]
    if top != 'STV_ED_motion_study':
        return 'INDEX 导航与管理'
    if rel.name in ('requirements.txt', 'environment_snapshot.json', 'WORK_LOG.md', 'README.md') and len(parts) == 2:
        return 'MAIN 主线说明'
    if len(parts) < 2 or parts[1] != 'bev':
        return 'S01 运动机制' if rel.suffix != '.md' or rel.name.startswith('研究方案') else 'MAIN 主线说明'
    name = rel.name
    if 'results_crossing_uncertain' in parts or 'crossing_uncertain' in name or name.startswith('观测预测'):
        return 'S05 观测误差与更新'
    if 'results_crossing_2d' in parts or 'crossing_2d' in name or name.startswith('二维横穿'):
        return 'S04 二维横穿'
    if 'results_stopping_v2' in parts or 'stopping_v2' in name or name.startswith('停车模块'):
        return 'S03 停车v2'
    if name == 'README.md' and len(parts) == 3:
        return 'MAIN 主线说明'
    return 'S02 BEV初版与共享定义'


def classify(path):
    rel = path.relative_to(ROOT)
    parts = rel.parts
    stage = stage_for(rel)
    ext = path.suffix.lower()
    name = path.name
    if 'clock_boundary_diagnostic' in parts or name == 'diagnostics_before_regularization.json':
        return '03 实验结果', stage, '历史诊断，不并入最终统计', '失败与修复证据'
    if name == 'README.md' or parts[0] == '成果导航' or name in ('WORK_LOG.md','requirements.txt','requirements-review.txt','environment_snapshot.json'):
        return '06 复现与交接', stage, '导航/管理', '说明、清单或运行记录'
    if parts[0].startswith('STV_ED_reproducible_pilot_bundle'):
        return '05 历史探索', stage, '原始快照', '保留原交付文件；具体用途见原README'
    if parts[0] == 'timetrap_translation':
        return '04 文献与查新', stage, '历史阅读材料', '译文、提炼或原文核对材料'
    if ext in ('.pdf', '.bib') or 'papers' in parts or name in ('paper_downloads.json','crossref_metadata.json','manifest.json'):
        return '04 文献与查新', stage, '文献证据', '原文、引用、下载或提取记录'
    if parts[0] in ('acc_observation_gap','market_decision_research'):
        if ext == '.md':
            return '04 文献与查新', stage, '历史候选', '可行性与重合分析'
        return '05 历史探索', stage, '非当前模型', '独立历史探针与输出'
    if ext == '.py':
        role = '单元测试' if name.startswith('test_') else '核对/辅助脚本' if name.startswith(('verify_','inspect_','extract_')) else '绘图' if name.startswith('plot_') else '模型/实验入口'
        return '02 仿真代码', stage, '可执行源码', role
    if ext == '.md':
        category = '04 文献与查新' if '审阅' in name or '文献' in name else '01 研究说明'
        return category, stage, '阶段报告（注意日期）', '结论、边界与研究假设'
    if 'results' in '/'.join(parts) or ext in ('.csv', '.json', '.png', '.gif'):
        return '03 实验结果', stage, '阶段输出/审阅记录', '数据、配置、哈希或图'
    return '05 历史探索', stage, '保留材料', '草稿、提取内容或历史附件'


def check_links(docs):
    checked = 0
    failures = []
    pattern = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^)\s]+)(?:\s+"[^"]*")?\)')
    for doc in docs:
        content = doc.read_text(encoding='utf-8-sig')
        for match in pattern.finditer(content):
            target = match.group(1).strip('<>')
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            target = unquote(target.split('#', 1)[0].split('?', 1)[0])
            if not target:
                continue
            checked += 1
            if not (doc.parent / target).resolve().exists():
                failures.append({'document': doc.relative_to(ROOT).as_posix(), 'target': target})
    return {'documents_checked': len(docs), 'local_links_checked': checked, 'broken_links': failures}


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    files = scan()
    baseline = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))['files']
    baseline_names = {r['path'] for r in baseline}
    missing, unexpected_changes, allowed_changes = [], [], []
    records = []
    hashes = {}
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        hashes[rel] = digest
        category, stage, status, purpose = classify(path)
        records.append({'path': rel, 'category': category, 'stage': stage,
                        'status': status, 'purpose': purpose,
                        'bytes': path.stat().st_size, 'sha256': digest})
    for item in baseline:
        rel = item['path']
        path = ROOT / rel
        if not path.is_file():
            missing.append(rel)
        elif hashes.get(rel, sha256(path)) != item['sha256']:
            (allowed_changes if rel in ALLOWED_CHANGED else unexpected_changes).append(rel)

    original_root = ROOT / 'STV_ED_reproducible_pilot_bundle/rural_narrow_road_research'
    original = json.loads((ROOT / 'STV_ED_review_20261103/source_manifest.json').read_text(encoding='utf-8'))
    original_issues = []
    for item in original:
        path = original_root / Path(item['path'].replace('\\', '/'))
        if not path.is_file() or sha256(path) != item['sha256']:
            original_issues.append(item['path'])
    original_paths = {p.relative_to(original_root).as_posix() for p in original_root.rglob('*')
                      if p.is_file() and '__pycache__' not in p.parts}
    original_expected = {r['path'].replace('\\', '/') for r in original}

    bev = ROOT / 'STV_ED_motion_study/bev'
    latest_manifest = json.loads((bev / 'results_crossing_uncertain/source_manifest.json').read_text(encoding='utf-8'))
    source_issues = [name for name, expected in latest_manifest.items()
                     if not (bev/name).is_file() or sha256(bev/name) != expected]
    latest_out = bev / 'results_crossing_uncertain'
    episodes = json.loads((latest_out/'episodes.json').read_text(encoding='utf-8'))
    episode_names = [r['case'] for r in episodes]
    episode_issues = [name + suffix for name in episode_names
                      for suffix in ('_trace.csv','_events.json','_observations.json')
                      if not (latest_out/(name+suffix)).is_file()]

    docs = [p for p in files if p.suffix == '.md' and
            (p.relative_to(ROOT).as_posix() not in baseline_names or
             p.relative_to(ROOT).as_posix() in ALLOWED_CHANGED)]
    with (NAV/'文件清单.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['path','category','stage','status','purpose','bytes','sha256'])
        writer.writeheader()
        writer.writerows(records)
    stats = {
        'date': '2026-11-03', 'scope': 'Known research roots and organization documents; inventory snapshot',
        'excluded_directory_names': sorted(EXCLUDED_DIRS),
        'self_excluded_outputs': sorted(GENERATED),
        'files': len(records), 'bytes': sum(r['bytes'] for r in records),
        'by_category': dict(sorted(Counter(r['category'] for r in records).items())),
        'by_stage': dict(sorted(Counter(r['stage'] for r in records).items())),
        'by_root': dict(sorted(Counter(r['path'].split('/')[0] for r in records).items())),
    }
    # Create all generated link targets before validating the new documents.
    write_json(NAV/'分类统计.json', stats)
    write_json(NAV/'整理校验.json', {'status': 'verification_in_progress'})
    links = check_links(docs)
    passed = not (missing or unexpected_changes or original_issues or source_issues or
                  original_paths != original_expected or links['broken_links'] or episode_issues or
                  len(episodes) != 72 or len(set(episode_names)) != 72)
    verification = {
        'date': '2026-11-03', 'passed': passed,
        'organization_scope': 'Documentation and catalog only; no physical simulations rerun',
        'preexisting_files_checked': len(baseline),
        'missing_preexisting_files': missing, 'unexpected_content_changes': unexpected_changes,
        'allowed_content_changes': allowed_changes,
        'allowed_change_explanation': 'WORK_LOG gains links to organization results; prior research sections preserved',
        'original_bundle_files_checked': len(original),
        'original_bundle_hash_issues': original_issues,
        'original_bundle_exact_file_set': original_paths == original_expected,
        'latest_source_hashes_checked': len(latest_manifest), 'latest_source_hash_issues': source_issues,
        'latest_episodes': len(episodes), 'latest_unique_cases': len(set(episode_names)),
        'latest_expected_episode_files': len(episodes)*3, 'latest_missing_episode_files': episode_issues,
        'readme_links': links,
    }
    write_json(NAV/'整理校验.json', verification)
    print(json.dumps({'passed': passed, 'cataloged_files': len(records),
                      'preexisting_files': len(baseline), 'original_bundle_files': len(original),
                      'latest_source_hashes': len(latest_manifest),
                      'readme_documents': len(docs), 'local_links_checked': links['local_links_checked'],
                      'broken_links': links['broken_links'], 'unexpected_changes': unexpected_changes},
                     ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
