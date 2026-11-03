from pathlib import Path
import csv
import json
from bev_probe import Parameters,run

root=Path(__file__).resolve().parent/'results'
rows=list(csv.DictReader((root/'case_summary.csv').open()))
checks=[]
for r in rows:
    assert r['completed']=='True'
    assert float(r['gate1_leave_s'])>float(r['gate1_enter_s'])
    assert float(r['gate2_leave_s'])>float(r['gate2_enter_s'])
    trace=list(csv.DictReader((root/(r['case']+'_trace.csv')).open()))
    assert all(float(x['v_m_s'])>=0 for x in trace)
    assert all(abs(float(x['steer_rad']))<=.45+1e-10 for x in trace)
    if r['ideal_acceleration_override']=='False':
        assert all(-float(x['regen_limit_nm'])-1e-8<=float(x['motor_nm'])<=float(x['motor_limit_nm'])+1e-8 for x in trace)
        expected=float(r['initial_soc'])-float(r['net_battery_wh'])/60000.
        assert abs(expected-float(r['ending_soc_energy_fraction']))<1e-10
    peaks=sorted([(abs((float(b['a_actual_m_s2'])-float(a['a_actual_m_s2']))/.02),float(b['t_s']),min(float(a['v_m_s']),float(b['v_m_s']))) for a,b in zip(trace,trace[1:])],reverse=True)
    checks.append({'case':r['case'],'peak_raw_jerk':peaks[0], 'peak_scope':'raw peak includes zero-speed clamp and is not a validated ride-comfort metric'})

refinement=[]
for name,soc,temp in [('bev_normal',.55,25.),('bev_cold',.55,-5.)]:
    fine=run(name+'_dt001',soc,temp,Parameters(),dt=.01)
    coarse=next(r for r in rows if r['case']==name)
    maximum=max(abs(float(coarse[k])-fine[k]) for k in ('gate1_enter_s','gate1_leave_s','gate2_enter_s','gate2_leave_s'))
    stop_diff=abs(float(coarse['first_stop_x_m'])-fine['first_stop_x_m'])
    assert maximum<.15 and stop_diff<.05
    refinement.append({'case':name,'max_gate_endpoint_difference_s':maximum,'first_stop_position_difference_m':stop_diff})
result={'case_checks':checks,'dt_002_vs_001':refinement,'status':'passed',
        'scope':'case and model consistency checks, not continuous safety or vehicle calibration'}
(root/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
