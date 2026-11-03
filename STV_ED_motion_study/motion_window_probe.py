"""Mechanism probe, not a novel certified planner or an obstacle-avoidance controller.

Rear-axle kinematic bicycle + speed feedback + pure pursuit + actuator limits.
Projects the full rectangular vehicle onto two full-width conflict strips.
Calibration extrema are empirical, NOT guaranteed tracking/reachability bounds.
"""
from pathlib import Path
import csv
import json
import math
import numpy as np

OUT = Path(__file__).resolve().parent / 'results'
L, HALF_WIDTH, FRONT, REAR = 2.7, .9, 3.5, -1.0
DT, HORIZON = .04, 30.
GATES = [(14., 15.), (26., 27.)]

def path_y(x, offset):
    return offset * math.sin(math.pi * min(max(x, 0.), 36.) / 36.)**2

def simulate(speed, offset, perturbation, dt=DT, trace=False):
    gain, delay, bias, y0, psi0, tau = perturbation
    x, y, psi, v, a, delta = 0., y0, psi0, 1., 0., 0.
    windows = [[None, None], [None, None]]
    max_steer = max_rate = max_accel = max_lat = max_body_y = max_error = 0.
    history = []
    steps = int(HORIZON/dt)+1
    completed = False
    for k in range(steps):
        t = k*dt
        c, s = math.cos(psi), math.sin(psi)
        corners = [(x+xx*c-yy*s, y+xx*s+yy*c) for xx in (REAR, FRONT) for yy in (-HALF_WIDTH, HALF_WIDTH)]
        min_x, max_x = min(p[0] for p in corners), max(p[0] for p in corners)
        max_body_y = max(max_body_y, max(abs(p[1]) for p in corners))
        max_error = max(max_error, abs(y-path_y(x, offset)))
        for j, (lo, hi) in enumerate(GATES):
            if max_x >= lo and min_x <= hi:
                if windows[j][0] is None:
                    windows[j][0] = t
                windows[j][1] = t+dt  # conservative sampled-bin convention
        if trace:
            history.append([t,x,y,psi,v,a,delta])
        if min_x > 36.:
            completed = True
            break
        look = max(3., 1.2*v)
        tx, ty = x+look, path_y(x+look, offset)
        alpha = math.atan2(ty-y,tx-x)-psi
        desired_delta = float(np.clip(math.atan2(2*L*math.sin(alpha), look), -.45, .45))
        change = float(np.clip(desired_delta-delta, -.5*dt, .5*dt))
        delta += change
        requested_a = float(np.clip(1.5*(speed+bias-v), -3., 2.)) if t >= delay else 0.
        a += dt*(gain*requested_a-a)/tau
        a = float(np.clip(a,-3.,2.))
        max_steer, max_rate = max(max_steer,abs(delta)), max(max_rate,abs(change/dt))
        max_accel = max(max_accel,abs(a))
        max_lat = max(max_lat,abs(v*v*math.tan(delta)/L))
        x += dt*v*math.cos(psi)
        y += dt*v*math.sin(psi)
        psi += dt*v*math.tan(delta)/L
        v = max(0.,v+dt*a)
    return {'windows':windows, 'completed':completed, 'finish_s':t,
            'max_steer_rad':max_steer,'max_steer_rate_rad_s':max_rate,
            'max_abs_accel_m_s2':max_accel,'max_lateral_accel_m_s2':max_lat,
            'max_body_abs_y_m':max_body_y,'max_path_error_m':max_error,
            'trace':history}

def sample_parameters(rng,n):
    return [(float(rng.uniform(.8,1.2)),float(rng.uniform(0,.25)),
             float(rng.uniform(-.15,.15)),float(rng.uniform(-.1,.1)),
             float(rng.uniform(-.02,.02)),float(rng.uniform(.2,.4))) for _ in range(n)]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(20261103)
    nominal=(1.,0.,0.,0.,0.,.3)
    calibration=sample_parameters(rng,40)
    heldout=sample_parameters(rng,120)
    rows=[]
    checks={'all_simulations_complete':True,'all_sampled_footprints_inside_4m_road':True,
            'actuator_limits_satisfied':True}
    simulations=0
    for speed in (2.,3.,4.):
        for offset in (-.35,0.,.35):
            base=simulate(speed,offset,nominal,trace=True)
            assert base['completed'] and all(w[0] is not None for w in base['windows'])
            name=f'v{speed:g}_offset{offset:+.2f}'
            if speed==3.:
                with (OUT/(name+'.csv')).open('w',newline='') as f:
                    writer=csv.writer(f);writer.writerow(['t_s','x_m','y_m','yaw_rad','v_m_s','a_m_s2','steer_rad']);writer.writerows(base['trace'])
            cal=[simulate(speed,offset,p) for p in calibration]
            test=[simulate(speed,offset,p) for p in heldout]
            simulations += len(cal)+len(test)+1
            for run in [base]+cal+test:
                checks['all_simulations_complete'] &= run['completed']
                checks['all_sampled_footprints_inside_4m_road'] &= run['max_body_abs_y_m']<2.
                checks['actuator_limits_satisfied'] &= (run['max_steer_rad']<=.45+1e-10 and run['max_steer_rate_rad_s']<=.5+1e-10 and run['max_abs_accel_m_s2']<=3.+1e-10)
            lower=[min(r['windows'][g][0] for r in cal) for g in range(2)]
            upper=[max(r['windows'][g][1] for r in cal) for g in range(2)]
            for g in range(2):
                enter,leave=base['windows'][g]
                rows.append({'speed_m_s':speed,'path_offset_m':offset,'gate':g+1,
                             'nominal_enter_s':enter,'nominal_leave_s':leave,
                             'calibration_earliest_enter_s':lower[g],'calibration_latest_leave_s':upper[g],
                             'empirical_early_margin_s':max(0.,enter-lower[g]),
                             'empirical_late_margin_s':max(0.,upper[g]-leave),
                             'heldout_outside_empirical_envelope_n':sum(r['windows'][g][0]<lower[g]-1e-9 or r['windows'][g][1]>upper[g]+1e-9 for r in test),
                             'heldout_n':len(test)})
    global_pad=max(max(r['empirical_early_margin_s'],r['empirical_late_margin_s']) for r in rows)
    for r in rows:
        r['global_empirical_padding_s']=global_pad
    with (OUT/'occupancy_windows.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    coarse=simulate(3.,.35,nominal)
    fine=simulate(3.,.35,nominal,dt=.02)
    checks['selected_case_dt_refinement_max_endpoint_difference_s']=max(abs(a-b) for w1,w2 in zip(coarse['windows'],fine['windows']) for a,b in zip(w1,w2))
    report={'seed':20261103,'dt_s':DT,'candidate_count':9,'calibration_parameter_draws':40,
            'heldout_parameter_draws':120,'candidate_simulations':simulations,
            'global_empirical_padding_s':global_pad,'checks':checks,
            'model':'kinematic bicycle; rear axle reference; 4.5m x 1.8m full footprint; wheelbase 2.7m; straight 4m road; full-width conflict strips',
            'limitations':['No interaction with pedestrians, no dynamic collision trial, no replanning, and no stopping/refuge maneuver implemented.',
                          'Forward simulations use feedback tracking, but candidate choice is not an online closed-loop planner.',
                          'Empirical extrema from 40 parameter draws are not certified bounds or calibrated confidence intervals.',
                          'Sampled footprint checks do not certify continuous-time collision avoidance.',
                          'Held-out tests share the specified parameter distribution; no real-world calibration.',
                          'This is a mechanism probe, not a novelty demonstration or a reproduction of FaSTrack/RTD.']}
    (OUT/'probe_summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    print('WINDOWS: speed, offset, gate, early margin, late margin, heldout misses')
    for r in rows:
        print(r['speed_m_s'],r['path_offset_m'],r['gate'],round(r['empirical_early_margin_s'],3),round(r['empirical_late_margin_s'],3),r['heldout_outside_empirical_envelope_n'])
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(8,4))
        for speed in (2.,3.,4.):
            rr=[r for r in rows if r['speed_m_s']==speed and r['gate']==2]
            ax.plot([r['path_offset_m'] for r in rr],[r['empirical_late_margin_s'] for r in rr],marker='o',label=f'{speed:g} m/s')
        ax.set(xlabel='Path lateral offset (m)',ylabel='Empirical late margin at gate 2 (s)',title='Execution-dependent occupancy timing: mechanism probe')
        ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(OUT/'timing_margin_probe.png',dpi=160);plt.close(fig)
    except ImportError:
        pass

if __name__=='__main__':
    main()
