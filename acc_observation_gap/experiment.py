"""Feasibility probe, not a paper benchmark or a verified safety controller.
Python standard library only. Run: python experiment.py
Positions are bumper coordinates; gap = lead rear - ego front.
"""
import csv
import itertools
import json
import math
import time
from pathlib import Path

DT = 0.1
BE, BL = 8.0, 6.0
BUFFER = 2.0
ROOT = Path(__file__).resolve().parent

def step(x, v, a, dt=DT):
    if a < 0 and v + a * dt < 0:
        return x + v * v / (-2 * a), 0.0
    return x + v * dt + .5 * a * dt * dt, max(0., v + a * dt)

def lead_lower(obs, age):
    return step(obs[0], obs[1], -BL, age)

def backup_margin(x, v, a, lx, lv, command, jerk):
    """Sampled rollout of one command then jerk-limited max braking.
    BL is an assumed bound, not an estimated/known future actual brake.
    """
    margin = lx - x - BUFFER
    for k in range(140):
        a = command if k == 0 else max(-BE, a - jerk * DT)
        x, v = step(x, v, a)
        lx, lv = step(lx, lv, -BL)
        margin = min(margin, lx - x - BUFFER)
        if v == 0 and lv == 0:
            break
    return margin

def filtered(x, v, a, lx, lv, nominal, jerk):
    lo = max(-BE, a - jerk * DT)
    hi = min(2., a + jerk * DT, nominal)
    hi = max(lo, hi)
    if backup_margin(x, v, a, lx, lv, lo, jerk) < 0:
        return lo, False
    if backup_margin(x, v, a, lx, lv, hi, jerk) >= 0:
        return hi, True
    for _ in range(9):
        mid = .5 * (lo + hi)
        if backup_margin(x, v, a, lx, lv, mid, jerk) >= 0:
            lo = mid
        else:
            hi = mid
    return lo, True

def run(v0, gap0, outage, brake_offset, policy, braking=True, actual_brake=BL):
    # All controllers receive the same availability pattern. Ground truth is
    # used for evaluation only; no controller sees the hidden lead trajectory.
    x, v, a = 0., v0, 0.
    lx, lv = gap0, v0
    obs, stamp = (lx, lv), 0.
    min_gap, sum_j2, sum_speed, peak_j = gap0, 0., 0., 0.
    infeasible, emergency_steps = 0, 0
    trace = []
    for k in range(round(14 / DT)):
        t = k * DT
        available = not (2. <= t < 2. + outage)
        if available:
            obs, stamp = (lx, lv), t
        age = t - stamp
        # Constant-velocity estimate for nominal controller.
        est_lx = obs[0] + obs[1] * age
        nominal = max(-BE, min(2., .25 * (est_lx - x - (5. + 1.2 * v))
                               + .8 * (obs[1] - v)))
        comfortable = max(a - 2 * DT, min(a + 2 * DT, nominal))
        if policy == 'nominal_cv':
            command = comfortable
        elif policy == 'timeout_0.5':
            command = max(-BE, a - 30 * DT) if age >= .5 else comfortable
        elif policy == 'immediate_brake':
            command = max(-BE, a - 30 * DT) if not available else comfortable
        else:
            low_x, low_v = lead_lower(obs, age)
            jerk = 30. if policy == 'robust_hard' else 2.
            command, feasible = filtered(x, v, a, low_x, low_v, nominal, jerk)
            if not feasible and policy == 'robust_comfort':
                command, feasible = filtered(x, v, a, low_x, low_v, nominal, 30.)
                emergency_steps += 1
            infeasible += int(not feasible)
        j = (command - a) / DT
        sum_j2 += j * j
        peak_j = max(peak_j, abs(j))
        # Exact integration for constant acceleration in each sample.
        x, v = step(x, v, command)
        lead_a = -actual_brake if braking and t >= 2. + brake_offset else 0.
        lx, lv = step(lx, lv, lead_a)
        a = command
        min_gap = min(min_gap, lx - x)
        sum_speed += v
        trace.append([t, lx-x, v, lv, a, age])
    return dict(policy=policy, speed=v0, gap=gap0, outage=outage,
                brake_offset=brake_offset, braking=braking,
                collision=min_gap <= 0, min_gap=min_gap,
                jerk_rms=math.sqrt(sum_j2/len(trace)), peak_jerk=peak_j,
                mean_speed=sum_speed/len(trace), infeasible_steps=infeasible,
                emergency_steps=emergency_steps), trace

def checks():
    assert step(0, 10, -5, 3) == (10., 0.)
    assert step(0, 10, 0, 2) == (20., 10.)
    assert lead_lower((20, 10), 2) == step(20, 10, -BL, 2)
    # Back-up margin decreases with a more aggressive first acceleration.
    assert backup_margin(0,20,0,40,20,-1,2) >= backup_margin(0,20,0,40,20,1,2)

def main():
    checks()
    policies = ['nominal_cv','timeout_0.5','immediate_brake','robust_hard','robust_comfort']
    rows = []
    started = time.perf_counter()
    for speed, headway, outage, offset, braking in itertools.product(
            [20.,30.], [.8,1.2,1.8], [.2,.8,1.5], [0.,.3], [False,True]):
        for policy in policies:
            row, trace = run(speed, 5+headway*speed, outage, offset, policy, braking)
            rows.append(row)
            if speed == 30 and headway == 1.2 and outage == 1.5 and offset == 0 and braking:
                with (ROOT / ('trace_'+policy+'.csv')).open('w',newline='') as f:
                    w = csv.writer(f); w.writerow(['time','gap','ego_speed','lead_speed','acceleration','observation_age']); w.writerows(trace)
    with (ROOT/'results.csv').open('w',newline='') as f:
        w = csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    summary = {'runtime_seconds':time.perf_counter()-started,
               'scenario_count':len(rows)//len(policies), 'runs':len(rows),
               'dt_seconds':DT, 'policies':{}}
    for policy in policies:
        subset = [r for r in rows if r['policy']==policy]
        summary['policies'][policy] = dict(
            collisions=sum(r['collision'] for r in subset),
            below_2m=sum(r['min_gap']<2-1e-6 for r in subset),
            mean_jerk_rms=sum(r['jerk_rms'] for r in subset)/len(subset),
            worst_gap=min(r['min_gap'] for r in subset),
            mean_speed_nonbraking=sum(r['mean_speed'] for r in subset if not r['braking'])/sum(not r['braking'] for r in subset),
            scenarios_with_infeasibility=sum(r['infeasible_steps']>0 for r in subset))
    (ROOT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__ == '__main__':
    main()
