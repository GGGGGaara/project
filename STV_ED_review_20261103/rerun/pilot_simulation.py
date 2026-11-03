#!/usr/bin/env python3
"""Reproducible 1-D temporal bottleneck admission test.

IMPORTANT: This is a *decision-level abstract simulator*, not a vehicle
kinematics/collision dynamics model. An unsafe exposure event means that
preselected crossing times or refuge use overlap realized occupation.
It does NOT establish physical collision, safety guarantees, or full AV behavior.

No real-world data are used. Synthetic scenarios and a stochastic forecast-error
model are explicitly specified below. All five decision policies share the same per-episode scenario realization
and the same temporal travel abstraction; the reactive baseline uses only
current gate occupancy, while other policies use noisy forecast schedules.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import numpy as np

# Vehicle center travels 18 m per stage at fixed 3 m/s (6 s each).
# Each conflict area is exposed over [2.2, 3.8] s after stage departure;
# the exposure time includes simplified vehicle-length + clearance allowance.
STEP = 0.5
STAGE_DURATION = 6.0
EXPOSURE = (2.2, 3.8)
REFUGE_TOL = 0.2
MAX_ENTRY_TIME = 50.0
MAX_STAGE_WAIT = 30.0
MAX_TIME = 90.0
ROBUST_PADDING = 1.25

@dataclass(frozen=True)
class Plan:
    entry: float
    second_departure: float  # entry+6 for through-passage
    mode: str                 # through / refuge
    finish: float


def actual_events(rng: np.random.Generator):
    # Event windows imitate localized temporary occupation from crossing actors
    # and a refuge occupied by deliveries/shoppers. These are intentionally
    # synthetic distributions, not inferred from measured rural traffic.
    out = {}
    for key, ranges in {
        'gate_1': [(1.0, 13.0), (17.0, 33.0)],
        'gate_2': [(5.0, 22.0), (24.0, 42.0)],
        'refuge': [(4.0, 23.0), (25.0, 38.0)],
    }.items():
        ivals = []
        for lo, hi in ranges:
            # Some windows may be absent, mimicking lower activity.
            chance = 0.82 if key != 'refuge' else 0.65
            if rng.random() < chance:
                st = float(rng.uniform(lo, hi))
                dur = float(rng.uniform(2.0, 5.5 if key != 'refuge' else 7.0))
                ivals.append((st, st + dur))
        out[key] = sorted(ivals)
    return out


def perceived_events(actual, rng, sigma):
    # Each event interval is shifted by a single timing error; no false detections.
    result = {}
    for key, intervals in actual.items():
        forecast = []
        for st, en in intervals:
            shift = float(rng.normal(0, sigma))
            forecast.append((st + shift, en + shift))
        result[key] = sorted(forecast)
    return result


def intersects(intervals, start, end, pad=0.0):
    """True iff inclusive intervals overlap after occupying-space padding."""
    return any((start < hi + pad) and (end > lo - pad)
               for lo, hi in intervals)


def gate_safe(ivs, depart, pad):
    return not intersects(ivs, depart + EXPOSURE[0],
                          depart + EXPOSURE[1], pad)


def refuge_safe(ivs, arrival, departure, pad):
    # For a through-pass no refuge is occupied (checked only for staged plans).
    return not intersects(ivs, arrival - REFUGE_TOL,
                          departure + REFUGE_TOL, pad)


def find_stage_departure(forecast, t0, pad, use_refuge=True):
    arrival = t0 + STAGE_DURATION
    t2 = arrival
    while t2 <= min(MAX_TIME-STAGE_DURATION, arrival+MAX_STAGE_WAIT)+1e-8:
        if use_refuge and not refuge_safe(forecast['refuge'], arrival, t2, pad):
            # Refuge occupation interval only grows in the future.
            break
        if gate_safe(forecast['gate_2'], t2, pad):
            return t2
        t2 += STEP
    return None


def plan_for_policy(policy, forecast, robust_pad):
    if policy == 'reactive':
        # Ignores future gate/bay occupation; checks that gate 1 is free *now*.
        for t in np.arange(0, MAX_ENTRY_TIME+STEP/2, STEP):
            if not intersects(forecast['gate_1'], t, t+STEP, 0):
                return Plan(float(t), float(t+STAGE_DURATION), 'through',
                            float(t+2*STAGE_DURATION))
        return None

    if policy == 'local_prediction':
        # Predict gate 1, but do not assess bay availability at entry.
        for t in np.arange(0, MAX_ENTRY_TIME+STEP/2, STEP):
            t = float(t)
            if gate_safe(forecast['gate_1'], t, 0):
                if gate_safe(forecast['gate_2'], t+STAGE_DURATION, 0):
                    return Plan(t, t+STAGE_DURATION, 'through', t+12)
                t2 = find_stage_departure(forecast, t, 0, use_refuge=False)
                if t2 is not None:
                    return Plan(t, t2, 'refuge', t2+STAGE_DURATION)
        return None

    pad = robust_pad if policy in ('joint_robust', 'robust_no_refuge') else 0.0
    use_refuge = policy != 'robust_no_refuge'
    best = None
    for t in np.arange(0, MAX_ENTRY_TIME+STEP/2, STEP):
        t = float(t)
        if not gate_safe(forecast['gate_1'], t, pad):
            continue
        second = t+STAGE_DURATION
        if gate_safe(forecast['gate_2'], second, pad):
            candidate = Plan(t, second, 'through', t+12.0)
            if best is None or candidate.finish < best.finish:
                best = candidate
        # A staged route is legitimate only if an actual intermediate stop
        # location can be kept available for the required waiting interval.
        t2 = find_stage_departure(forecast, t, pad, use_refuge=use_refuge)
        if t2 is not None and t2 > second+1e-9:
            candidate = Plan(t, t2, 'refuge', t2+STAGE_DURATION)
            if best is None or candidate.finish < best.finish:
                best = candidate
    return best


def evaluate(plan, actual):
    if plan is None:
        return {'exposure': True, 'cause': 'no_plan', 'completion': False,
                'finish': None, 'entry': None, 'used_refuge': False}
    if not gate_safe(actual['gate_1'], plan.entry, 0):
        cause = 'gate_1'
    elif plan.mode == 'refuge' and not refuge_safe(
        actual['refuge'], plan.entry+STAGE_DURATION,
        plan.second_departure, 0):
        cause = 'refuge'
    elif not gate_safe(actual['gate_2'], plan.second_departure, 0):
        cause = 'gate_2'
    else:
        cause = 'none'
    exposure = (cause != 'none')
    return {'exposure': exposure, 'cause': cause,
            'completion': not exposure,
            'finish': plan.finish if not exposure else None,
            'entry': plan.entry, 'used_refuge': plan.mode == 'refuge'}


def wilson_95(k, n):
    if n == 0: return (math.nan, math.nan)
    p = k/n
    z = 1.959963984540054
    d = 1 + z*z/n
    ctr = (p+z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return ctr-half,ctr+half


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--episodes', type=int, default=500)
    ap.add_argument('--seed', type=int, default=20261102)
    ap.add_argument('--output', default='pilot_results')
    ap.add_argument('--padding', type=float, default=ROBUST_PADDING)
    args = ap.parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True,exist_ok=True)
    policies = ['reactive','local_prediction','joint_nominal',
                'robust_no_refuge','joint_robust']
    noise_levels = [0.4, 1.0, 1.6]
    rng = np.random.default_rng(args.seed)
    rows=[]
    example = None
    for sigma in noise_levels:
        for episode in range(args.episodes):
            actual = actual_events(rng)
            forecast = perceived_events(actual,rng,sigma)
            if sigma == 1.0 and episode == 3:
                example = {'actual': actual,'forecast':forecast}
            for p in policies:
                # Myopic policy observes only current realized occupancy,
                # never the future event schedule.
                policy_input = actual if p == "reactive" else forecast
                plan = plan_for_policy(p, policy_input, args.padding)
                observation = evaluate(plan,actual)
                rows.append({'sigma_s': sigma, 'episode':episode,
                             'policy':p, **observation,
                             'planned_finish':plan.finish if plan else None,
                             'planned_refuge':plan.mode == 'refuge' if plan else None})
        print('Completed sigma =',sigma,flush=True)
    with (out_dir/'episode_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader();w.writerows(rows)
    stats=[]
    for sigma in noise_levels:
        for p in policies:
            group = [x for x in rows if x['sigma_s'] == sigma and x['policy']==p]
            n=len(group)
            bad=sum(x['exposure'] for x in group)
            valid=[x['finish'] for x in group if x['completion']]
            ci = wilson_95(bad,n)
            causes={key:sum(x['cause']==key for x in group)
                    for key in ('gate_1','gate_2','refuge','no_plan')}
            stats.append({'sigma_s':sigma,'policy':p,'n':n,
                          'exposure_n':bad,'exposure_rate':bad/n,
                          'risk_ci_low':ci[0], 'risk_ci_high':ci[1],
                          'completion_rate':len(valid)/n,
                          'mean_success_finish_s':float(np.mean(valid)) if valid else None,
                          'median_success_finish_s':float(np.median(valid)) if valid else None,
                          'mean_planned_finish_s':float(np.mean([x['planned_finish'] for x in group if x['planned_finish'] is not None])),
                          **{f'cause_{k}_n':v for k,v in causes.items()}})
    with (out_dir/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(stats[0].keys()))
        w.writeheader();w.writerows(stats)
    cfg={'seed':args.seed,'episodes_per_sigma':args.episodes,'noise_std_s':noise_levels,
         'padding_s':args.padding,'step_s':STEP, 'stage_duration_s':STAGE_DURATION,
         'crossing_window_offset_s':EXPOSURE,'refuge_margin_s':REFUGE_TOL,
         'max_entry_s':MAX_ENTRY_TIME,'max_wait_in_refuge_s':MAX_STAGE_WAIT,
         'remark':'Synthesized windows. Decision-level idealized constant-speed timing; no vehicle motion dynamics, geometry, calibrated sensor models, or collision simulation.'}
    (out_dir/'config.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False))
    (out_dir/'example_episode.json').write_text(json.dumps(example,indent=2,ensure_ascii=False))
    print('\nSUMMARY')
    for r in stats:
        print(f"sigma={r['sigma_s']:.1f} {r['policy']:<20} risk={r['exposure_rate']:.3f} CI=[{r['risk_ci_low']:.3f},{r['risk_ci_high']:.3f}] completion={r['completion_rate']:.3f} t_success={r['mean_success_finish_s']:.2f}")
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['font.family']='DejaVu Sans'
        # Fair group comparison: share episode and forecast; plot exposure.
        fig,ax=plt.subplots(figsize=(9.4,4.4))
        xx=np.arange(len(noise_levels))
        width=.16
        for j,p in enumerate(policies):
            yy=[100*next(r['exposure_rate'] for r in stats if r['sigma_s']==sig and r['policy']==p) for sig in noise_levels]
            ax.bar(xx+(j-2)*width,yy,width,label=p.replace('_',' '))
        ax.set_xticks(xx,[str(s) for s in noise_levels]);ax.set_xlabel('Forecast timing error (Gaussian sigma, s)')
        ax.set_ylabel('Realized exposure / unavailable refuge (%)')
        ax.set_title('Simplified temporal bottleneck pilot (synthetic data)')
        ax.legend(ncol=2,fontsize=8,loc='upper left')
        ax.grid(axis='y',alpha=.18)
        fig.tight_layout();fig.savefig(out_dir/'pilot_exposure.png',dpi=170);plt.close(fig)
    except Exception as exc:
        print('Plot unavailable',exc)

if __name__ == '__main__':
    main()
