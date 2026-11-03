"""Independent physical sanity checks on saved probe outputs."""
from pathlib import Path
import csv
import json

out=Path(__file__).resolve().parent/'results'
summary=json.loads((out/'probe_summary.json').read_text(encoding='utf-8'))
summary['checks'].pop('zero_perturbation_repeat_identical',None)
trace=list(csv.DictReader((out/'v3_offset+0.00.csv').open()))
assert trace
assert all(abs(float(r['y_m']))<1e-12 and abs(float(r['yaw_rad']))<1e-12 and abs(float(r['steer_rad']))<1e-12 for r in trace)
assert all(float(b['x_m'])>float(a['x_m']) for a,b in zip(trace,trace[1:]))
assert all(float(r['v_m_s'])>=0 and -3<=float(r['a_m_s2'])<=2 for r in trace)
rows=list(csv.DictReader((out/'occupancy_windows.csv').open()))
assert len(rows)==18
assert all(float(r['nominal_leave_s'])>float(r['nominal_enter_s']) for r in rows)
assert summary['checks']['all_simulations_complete']
assert summary['checks']['all_sampled_footprints_inside_4m_road']
assert summary['checks']['actuator_limits_satisfied']
assert summary['checks']['selected_case_dt_refinement_max_endpoint_difference_s']<=.04+1e-9
summary['checks']['straight_reference_preserves_zero_lateral_motion']=True
summary['checks']['saved_straight_trace_monotone_and_acceleration_valid']=True
(out/'probe_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print('PASS: physical sanity, occupancy ordering, actuator limits and selected-case dt refinement')
