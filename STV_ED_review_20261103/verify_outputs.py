"""Compare untouched supplied data with the independent rerun."""
from pathlib import Path
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import sys

SOURCE = Path(r"E:\Documents\ChatGPT\New project\STV_ED_reproducible_pilot_bundle\rural_narrow_road_research")
OUT = Path(__file__).resolve().parent
RUN = OUT / 'rerun' / 'results'
result = {'environment': {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(), 'packages': {name: importlib.metadata.version(name) for name in ('numpy', 'pandas', 'matplotlib')}}}
comparisons = []
for name in ('episode_results.csv', 'summary.csv', 'paired_bootstrap.csv', 'padding_sensitivity.csv'):
    left = list(csv.DictReader((SOURCE / 'results' / name).open(newline='', encoding='utf-8-sig')))
    right = list(csv.DictReader((RUN / name).open(newline='', encoding='utf-8-sig')))
    differences = []
    max_numeric_diff = 0.0
    if len(left) != len(right):
        differences.append({'row_count': [len(left), len(right)]})
    for index, (a, b) in enumerate(zip(left, right)):
        if a.keys() != b.keys():
            differences.append({'row': index, 'columns_differ': True})
            continue
        for key in a:
            if a[key] == b[key]:
                continue
            try:
                aa, bb = float(a[key]), float(b[key])
                max_numeric_diff = max(max_numeric_diff, abs(aa-bb))
                same = math.isclose(aa, bb, rel_tol=1e-12, abs_tol=1e-12) or (math.isnan(aa) and math.isnan(bb))
            except ValueError:
                same = False
            if not same:
                differences.append({'row': index + 2, 'column': key, 'original': a[key], 'rerun': b[key]})
    comparisons.append({'file': name, 'original_rows': len(left), 'rerun_rows': len(right), 'differences': differences[:20], 'max_numeric_difference': max_numeric_diff, 'matches': not differences})
result['csv_comparisons'] = comparisons
result['json_comparisons'] = {name: json.loads((SOURCE / 'results' / name).read_text()) == json.loads((RUN / name).read_text()) for name in ('config.json', 'example_episode.json')}
manifest = json.loads((OUT / 'source_manifest.json').read_text(encoding='utf-8'))
result['original_file_count'] = len(manifest)
result['original_files_changed'] = [r['path'] for r in manifest if hashlib.sha256((SOURCE / r['path']).read_bytes()).hexdigest() != r['sha256']]
result['copied_scripts_identical'] = {name: (SOURCE/name).read_bytes() == (OUT/'rerun'/name).read_bytes() for name in ('pilot_simulation.py', 'analysis_extra.py', 'test_pilot.py')}
(OUT/'reproduction_verification.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, indent=2, ensure_ascii=False))
