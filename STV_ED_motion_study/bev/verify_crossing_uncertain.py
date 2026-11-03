from pathlib import Path
import csv,json,math
from crossing_uncertain import OUT,WORLDS,SENSORS,World,Sensor,Vehicle,forecast,Snapshot,execute
from crossing_2d import circle_clearance,corners,rectangle_hit,STALLS

def main():
    rows=json.loads((OUT/'episodes.json').read_text());assert len(rows)==72
    assert len({r['case'] for r in rows})==72
    worlds={w.name:w for w in WORLDS};sensors={s.name:s for s in SENSORS}
    failures=[];checked=0
    for r in rows:
        data=list(csv.DictReader((OUT/(r['case']+'_trace.csv')).open()))
        observations=json.loads((OUT/(r['case']+'_observations.json')).read_text())
        events=json.loads((OUT/(r['case']+'_events.json')).read_text())
        assert len(data)==r['samples'] and len(observations)==r['observations']
        assert r['collision_free_completion']==(r['status']=='completed')
        assert (r['finish_s'] is not None)==(r['status']=='completed')
        w=worlds[r['world']];sensor=sensors[r['sensor']]
        for snap in observations:
            assert snap['measured_t']<=snap['received_t']+1e-9
            px,py,vy=w.at(snap['measured_t'])
            assert abs(snap['y']-py-sensor.y_bias_m)<1e-9
            assert abs(snap['vy']-vy-sensor.speed_bias_m_s)<1e-9
        frozen=events[0]['forecast_used']
        for event in events:
            if r['policy']=='frozen':assert event['forecast_used']==frozen
            else:assert event['forecast_used']==vars(forecast(Snapshot(**event['observation'])))
        actual_collision=False
        for d in data:
            t=float(d['t_s']);px,py,vy=w.at(t)
            assert abs(py-float(d['actual_ped_y_m']))<1e-9
            car=Vehicle(x=float(d['x_m']),y=float(d['y_m']),yaw=float(d['yaw_rad']))
            gap=circle_clearance(car,px,py,w.radius)
            static=any(rectangle_hit(corners(car),b) for b in STALLS)
            road=any(abs(y)>3. for x,y in corners(car))
            assert abs(gap-float(d['clearance_m']))<1e-9
            assert (gap<=0)==(d['ped_collision']=='True')
            actual_collision|=gap<=0 or static or road
        assert actual_collision==(r['status']=='collision')
        if r['policy']=='rolling' and r['status']=='collision':
            emergencies=[e for e in events if e['action']=='emergency_unverified']
            first=emergencies[0] if emergencies else None
            pose=min(data,key=lambda d:abs(float(d['t_s'])-(first['t_s'] if first else r['sim_end_s'])))
            car=Vehicle(x=float(pose['x_m']),y=float(pose['y_m']),yaw=float(pose['yaw_rad']))
            front=max(x for x,y in corners(car));v=float(pose['v_m_s'])
            failures.append({'case':r['case'],'contact_time_s':r['sim_end_s'],
                             'first_emergency_t_s':first['t_s'] if first else None,
                             'emergency_reason':first.get('reason') if first else None,
                             'speed_at_trigger_m_s':v,'front_x_at_trigger_m':front,
                             'actual_acceleration_at_trigger_m_s2':float(pose['a_actual_m_s2']),
                             'motor_torque_at_trigger_nm':float(pose['motor_nm']),
                             'friction_capacity_at_trigger_n':float(pose['brake_capacity_n']),
                             'longitudinal_gap_to_ped_strip_m':w.x-w.radius-front,
                             'ideal_constant_2_5m_s2_stop_distance_m':v*v/5.,
                             'interpretation':'Diagnostic geometry and ideal constant-deceleration estimate; not a proof that collision was physically inevitable.'})
        checked+=1
    refinement=[]
    selected=[('constant17','ideal','normal','rolling'),('speedup_early','ideal','cold_slow','rolling'),
              ('pause_in_road','ideal','normal','refresh_hold'),('speedup_late','delay_negative_bias','normal','rolling')]
    for wn,sn,condition,policy in selected:
        name=f'{wn}_{sn}_{condition}_{policy}'
        coarse=next(r for r in rows if r['case']==name)
        fine=execute(policy,worlds[wn],sensors[sn],coarse['temperature_c'],coarse['tau_s'],dt=.01)
        assert coarse['status']==fine['status'],(name,coarse,fine)
        refinement.append({'case':name,'status_dt002':coarse['status'],'status_dt001':fine['status'],
                           'end_time_difference_s':abs(coarse['sim_end_s']-fine['sim_end_s']),
                           'min_clearance_difference_m':abs(coarse['min_clearance_m']-fine['min_clearance_m'])})
    report={'episodes_checked':checked,'observation_truth_and_forecast_isolation':'passed',
            'collision_and_failure_classification':'passed','selected_dt_refinement':refinement,
            'rolling_failures':failures,'scope':'Specified replay and causality checks only; no safety guarantee.'}
    (OUT/'verification_failure_analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
