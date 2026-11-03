"""Independent review probes, not modifications to the supplied experiment."""
from pathlib import Path
import csv
import hashlib
import json
import math
import sys
import time

import numpy as np

SOURCE = Path(r"E:\Documents\ChatGPT\New project\STV_ED_reproducible_pilot_bundle\rural_narrow_road_research")
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
import pilot_simulation as pilot

def brute_force(forecast, pad):
    """Enumerate every allowed departure pair, independently of planner helpers."""
    best = None
    def disjoint(events, lo, hi):
        return all(hi <= st - pad or lo >= en + pad for st, en in events)
    for t0 in np.arange(0, 50.001, 0.5):
        if not disjoint(forecast['gate_1'], t0 + 2.2, t0 + 3.8):
            continue
        for t1 in np.arange(t0 + 6.0, min(84.0, t0 + 36.0) + .001, .5):
            if not disjoint(forecast['gate_2'], t1 + 2.2, t1 + 3.8):
                continue
            if t1 > t0 + 6 and not disjoint(forecast['refuge'], t0 + 5.8, t1 + .2):
                continue
            if best is None or t1 + 6 < best:
                best = float(t1 + 6)
    return best

checks = {}
blocked = {'gate_1': [(0, 100)], 'gate_2': [(0, 100)], 'refuge': [(0, 100)]}
no_plan = pilot.plan_for_policy('joint_robust', blocked, 1.25)
checks['safe_refusal_scored_as_exposure'] = {'plan': no_plan, 'evaluation': pilot.evaluate(no_plan, blocked)}
checks['touching_endpoints'] = {'events': [[2, 3]], 'usage': [3, 4], 'overlap': pilot.intersects([(2, 3)], 3, 4)}
empty = {'gate_1': [], 'gate_2': [], 'refuge': []}
imminent = {**empty, 'gate_1': [(.25, .4)]}
checks['reactive_future_half_second_query'] = {'events': imminent, 'chosen_entry': pilot.plan_for_policy('reactive', imminent, 1.25).entry}

rows = list(csv.DictReader((SOURCE / 'results' / 'episode_results.csv').open(newline='')))
reactive = [r for r in rows if r['policy'] == 'reactive']
checks['delivered_reactive_results'] = {'episodes': len(reactive), 'unique_entry': sorted(set(r['entry'] for r in reactive)), 'unique_planned_finish': sorted(set(r['planned_finish'] for r in reactive))}
checks['delivered_no_plan_events'] = sum(r['cause'] == 'no_plan' for r in rows)

rng = np.random.default_rng(816052)
disagreements = []
durations = []
for i in range(60):
    actual = pilot.actual_events(rng)
    forecast = pilot.perceived_events(actual, rng, 1.0)
    for policy, pad in [('joint_nominal', 0.0), ('joint_robust', 1.25)]:
        t = time.perf_counter()
        p = pilot.plan_for_policy(policy, forecast, pad)
        durations.append(time.perf_counter() - t)
        exhaustive = brute_force(forecast, pad)
        if (p.finish if p else None) != exhaustive:
            disagreements.append({'scene': i, 'policy': policy, 'planner': p.finish if p else None, 'exhaustive': exhaustive})
checks['grid_optimality_probe'] = {'scenes': 60, 'policy_runs': 120, 'disagreements': disagreements, 'mean_ms': 1000 * float(np.mean(durations)), 'max_ms': 1000 * float(np.max(durations)), 'timing_scope': 'small two-gate scheduler only; not vehicle-planning runtime benchmark'}

latest = {'gate_1': 33.0 + 5.5, 'gate_2': 42.0 + 5.5, 'refuge': 38.0 + 7.0}
safe_entry = math.ceil(max(latest['gate_1'] - 2.2, latest['gate_2'] - 6.0 - 2.2) / .5) * .5
wait_plan = pilot.Plan(safe_entry, safe_entry + 6, 'through', safe_entry + 12)
wait_bad = 0
rng = np.random.default_rng(730151)
for _ in range(10000):
    wait_bad += pilot.evaluate(wait_plan, pilot.actual_events(rng))['exposure']
checks['finite_generator_support'] = {'latest_possible_end_s': latest, 'fixed_actual_safe_entry_s': safe_entry, 'fixed_actual_safe_finish_s': safe_entry + 12, 'random_scenes': 10000, 'conflicts': int(wait_bad), 'interpretation': 'uses known finite support of synthetic generator, not an operational AV policy'}

q = math.erf(1.25 / math.sqrt(2))
checks['padding_coverage_at_sigma_1'] = {'single_event_shift_coverage': q, 'six_present_independent_events_coverage': q**6, 'every_corresponding_event_shift_within_padding_probability': (.18 + .82*q)**4 * (.35 + .65*q)**2, 'interpretation': 'probability that every present event shift is within padding; sufficient for envelope containment, not the exact probability of union containment or collision avoidance; assumes exactly the supplied independent timing-error model'}

original = json.loads((OUT / 'source_manifest.json').read_text(encoding='utf-8'))
changed = [item['path'] for item in original if hashlib.sha256((SOURCE / item['path']).read_bytes()).hexdigest() != item['sha256']]
checks['original_file_hash_changes'] = changed
(OUT / 'model_probe_results.json').write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(checks, indent=2, ensure_ascii=False))
