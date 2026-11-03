"""Actuator-aware stop tracking baseline. Synthetic maps; no novel-control claim.

Seventh-order position reference -> position/speed feedback -> torque/brake
allocation with nominal actuator inversion -> independent BEV actuator plant.
No position snapping. Forward-only standstill is an explicit hybrid mode.
"""
from dataclasses import asdict, replace
from functools import lru_cache
from pathlib import Path
import csv
import json
import math
import numpy as np
from bev_probe import Parameters, State, limits, clip

OUT=Path(__file__).resolve().parent/'results_stopping_v2'
BRAKE_REGULARIZATION_M_S=.03

def resistance(v,p):
    return p.mass_kg*9.81*p.rolling_coefficient*clip(v/.1,0.,1.)+.5*1.225*p.drag_area_m2*v*v

def motor_next(v,state,cmd,temp,p,dt):
    drive,regen,_=limits(v,state.soc_energy_fraction,temp,p)
    cmd=clip(cmd,-regen,drive)
    change=(1-math.exp(-dt/p.motor_tau_s))*(cmd-state.motor_nm)
    return clip(state.motor_nm+clip(change,-p.motor_slew_nm_s*dt,p.motor_slew_nm_s*dt),-regen,drive)

def effective_brake(v,capacity,regularization=None):
    # Smooth approximation to sliding friction near rest, not a measured brake map.
    scale=BRAKE_REGULARIZATION_M_S if regularization is None else regularization
    return capacity*math.tanh(max(0.,v)/scale)

def plant(v,state,torque_cmd,brake_cmd,temp,p,dt):
    state.motor_nm=motor_next(v,state,torque_cmd,temp,p,dt)
    ab=1-math.exp(-dt/p.friction_tau_s)
    state.friction_n+=ab*(clip(brake_cmd,0,p.mass_kg*7)-state.friction_n)
    motor_force=state.motor_nm*p.ratio/p.wheel_radius_m
    delivered_brake=effective_brake(v,state.friction_n)
    force=clip(motor_force-delivered_brake,-p.mu*p.mass_kg*9.81,p.mu*p.mass_kg*9.81)-resistance(v,p)
    free_a=force/p.equivalent_mass_kg
    next_v=max(0.,v+free_a*dt)
    actual_a=(next_v-v)/dt
    # Within-step event integration with numerically frozen force.
    if free_a<0 and v+free_a*dt<0:
        stop_time=v/(-free_a)
        distance=.5*v*stop_time
    else:
        distance=.5*(v+next_v)*dt
    _,_,omega=limits(v,state.soc_energy_fraction,temp,p)
    shaft=state.motor_nm*omega
    electrical=shaft/p.drive_efficiency if shaft>=0 else shaft*p.regen_efficiency
    battery=electrical+p.aux_w
    state.soc_energy_fraction=clip(state.soc_energy_fraction-battery*dt/p.battery_j,0,1)
    return next_v,distance,actual_a,free_a,battery

@lru_cache(maxsize=100)
def reference(distance,initial_v):
    """Choose duration satisfying sampled reference speed/acceleration/jerk limits."""
    mat=np.array([[1,1,1,1],[4,5,6,7],[12,20,30,42],[24,60,120,210]],float)
    for T in np.arange(max(1.,distance/max(3.,initial_v)),45.,.05):
        coef=np.zeros(8);coef[1]=initial_v*T
        coef[4:]=np.linalg.solve(mat,[distance-coef[1],-coef[1],0.,0.])
        poly=np.polynomial.Polynomial(coef)
        ss=np.linspace(0,1,301)
        vv=poly.deriv(1)(ss)/T;aa=poly.deriv(2)(ss)/T**2;jj=poly.deriv(3)(ss)/T**3
        if vv.min()>=-1e-8 and vv.max()<=max(3.,initial_v)+1e-8 and max(abs(aa))<=1.1 and max(abs(jj))<=1.5:
            return float(T),tuple(coef)
    raise ValueError('No reference in supplied search range')

@lru_cache(maxsize=100)
def polynomials(coef):
    poly=np.polynomial.Polynomial(coef)
    return poly,poly.deriv(1),poly.deriv(2)

def ref_values(elapsed,T,coef,start):
    s=clip(elapsed/T,0,1)
    poly,velocity,acceleration=polynomials(coef)
    return start+float(poly(s)),float(velocity(s)/T),float(acceleration(s)/T**2)

def commands(x,v,a_ref,x_ref,v_ref,state,temp,p,dt,previous_a,hold=False):
    if hold: return 0.,300.,0.
    # Nominal inverse actuator feedforward; actual parameters may differ.
    model=Parameters()
    desired_a=clip(a_ref+.8*(x_ref-x)+1.8*(v_ref-v),-2.5,1.5)
    desired_a=clip(desired_a,previous_a-2.*dt,previous_a+2.*dt)
    requested_force=p.equivalent_mass_kg*desired_a+resistance(v,p)
    drive,regen,_=limits(v,state.soc_energy_fraction,temp,p)
    desired_torque=clip(requested_force*p.wheel_radius_m/p.ratio,-regen,drive)
    am=1-math.exp(-dt/model.motor_tau_s)
    torque_cmd=clip((desired_torque-(1-am)*state.motor_nm)/am,-regen,drive)
    predicted=motor_next(v,state,torque_cmd,temp,model,dt)*p.ratio/p.wheel_radius_m
    brake_needed=max(0.,predicted-requested_force)
    ab=1-math.exp(-dt/model.friction_tau_s)
    brake_cmd=clip((brake_needed-(1-ab)*state.friction_n)/ab,0.,p.mass_kg*7.)
    return torque_cmd,brake_cmd,desired_a

def simulate(name,initial_v=0.,soc=.55,temp=25.,friction_tau=.18,dt=.02,save=False,first_target=10.,final_target=40.):
    p=replace(Parameters(),friction_tau_s=friction_tau)
    state=State(soc_energy_fraction=soc)
    x,v=0.,initial_v
    try:
        T,coef=reference(first_target,initial_v)
    except ValueError:
        return {'case':name,'initial_v_m_s':initial_v,'initial_soc':soc,'temperature_c':temp,
                'actual_friction_tau_s':friction_tau,'controller_friction_tau_s':.18,'dt_s':dt,
                'completed':False,'reference_available':False,'reason':'No seventh-order reference satisfies the specified sampled comfort constraints and duration search. Not a proof of physical infeasibility.',
                'first_stop_error_m':None,'final_stop_error_m':None,'max_raw_jerk_m_s3':None,
                'hold_drift_m':None,'duration_s':0.,'stop_events':[]}
    start,phase_start=0.,0.
    phase='first'
    hold_start=0.
    previous_a=0.
    first_stop=final_stop=None
    data=[];stop_events=[];end=False
    for k in range(int(100/dt)):
        t=k*dt
        holding=phase in ('hold','final_hold')
        if holding:
            xr,vr,ar=(first_target if phase=='hold' else final_target),0.,0.
        else:
            xr,vr,ar=ref_values(t-phase_start,T,coef,start)
        tc,bc,desired_a=commands(x,v,ar,xr,vr,state,temp,p,dt,previous_a,holding)
        previous_a=desired_a
        nv,dx,a,free_a,power=plant(v,state,tc,bc,temp,p,dt)
        data.append([t,x,v,xr,vr,ar,a,free_a,tc,state.motor_nm,bc,state.friction_n,state.soc_energy_fraction,phase,power])
        if v>0 and nv==0: stop_events.append({'t_s':t,'v_before_m_s':v,'free_a_m_s2':free_a,'kinetic_energy_j':.5*p.equivalent_mass_kg*v*v})
        x+=dx;v=nv
        # All pose integration remains physical; target position is never assigned.
        if phase in ('first','second') and t-phase_start>=T and v<.002 and abs(x-xr)<.05 and abs(a)<.05:
            if phase=='first': first_stop=x;phase='hold'
            else: final_stop=x;phase='final_hold'
            hold_start=t
        elif phase=='hold' and t-hold_start>=2.:
            phase='second';start=x;phase_start=t+dt
            T,coef=reference(round(final_target-x,9),v)
            previous_a=0.
        elif phase=='final_hold' and t-hold_start>=1.:
            end=True;break
    jerk=[abs((b[6]-a[6])/dt) for a,b in zip(data,data[1:])]
    stationary_hold_drift=0.
    for label in ('hold','final_hold'):
        positions=[r[1] for r in data if r[13]==label]
        if positions: stationary_hold_drift=max(stationary_hold_drift,max(positions)-min(positions))
    result={'case':name,'initial_v_m_s':initial_v,'initial_soc':soc,'temperature_c':temp,'actual_friction_tau_s':friction_tau,
            'reference_available':True,'reason':'' if end else 'Tracking did not satisfy terminal criteria within 100s',
            'controller_friction_tau_s':.18,'dt_s':dt,'completed':end,
            'first_stop_error_m':None if first_stop is None else first_stop-first_target,
            'final_stop_error_m':None if final_stop is None else final_stop-final_target,
            'max_raw_jerk_m_s3':max(jerk,default=0.),'hold_drift_m':stationary_hold_drift,
            'duration_s':data[-1][0],'stop_events':stop_events}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        with (OUT/(name+'_trace.csv')).open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['t_s','x_m','v_m_s','x_ref_m','v_ref_m_s','a_ref_m_s2','a_actual_m_s2','a_free_m_s2','motor_cmd_nm','motor_actual_nm','brake_cmd_n','brake_actual_n','soc','phase','battery_power_w']);w.writerows(data)
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for v0 in (0.,1.5,3.,4.):
        for soc in (.55,1.):
            for temp in (25.,-5.):
                for tau in (.12,.18,.35):
                    name=f'v{v0:g}_soc{soc:g}_temp{temp:g}_tau{tau:g}'
                    rows.append(simulate(name,v0,soc,temp,tau,save=(v0==0 and soc==.55 and tau in (.18,.35))))
    (OUT/'sweep.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    fields=[k for k in rows[0] if k!='stop_events']
    with (OUT/'sweep.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
    valid=[r for r in rows if r['completed']]
    summary={'cases':len(rows),'completed':len(valid),
             'within_010m':sum(max(abs(r['first_stop_error_m']),abs(r['final_stop_error_m']))<=.1 for r in valid),
             'max_abs_stop_error_m':max((max(abs(r['first_stop_error_m']),abs(r['final_stop_error_m'])) for r in valid),default=None),
             'max_raw_jerk_m_s3':max(r['max_raw_jerk_m_s3'] for r in rows if r['reference_available']),
             'max_hold_drift_m':max(r['hold_drift_m'] for r in rows if r['reference_available']),
             'reference_not_found_n':sum(not r['reference_available'] for r in rows),
             'failed_cases':[r['case'] for r in rows if not r['completed']],
             'brake_velocity_regularization_m_s':BRAKE_REGULARIZATION_M_S,
             'hold_entry_limits':{'speed_m_s':.002,'position_error_m':.05,'actual_acceleration_m_s2':.05},
             'reference_limits':{'max_speed_m_s':'max(3, initial speed)','max_abs_acceleration_m_s2':1.1,'max_abs_jerk_m_s3':1.5,'derivative_check_samples':301},
             'scope':'Synthetic longitudinal tracking baseline; no collision experiment, real-car calibration, slope or innovation claim.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
