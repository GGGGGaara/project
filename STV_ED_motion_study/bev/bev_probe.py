"""Generic BEV mechanism study; all numeric vehicle maps are research assumptions.
Not a calibrated production vehicle, safety proof, collision study or brake ECU.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import json
import math

OUT=Path(__file__).resolve().parent/'results'

def clip(x,lo,hi): return min(hi,max(lo,x))

@dataclass(frozen=True)
class Parameters:
    mass_kg: float=1900.
    equivalent_mass_kg: float=1976.
    wheel_radius_m: float=.31
    ratio: float=9.
    motor_max_nm: float=320.
    motor_max_w: float=150000.
    regen_max_nm: float=120.
    charge_max_w: float=50000.
    discharge_max_w: float=170000.
    battery_j: float=60.*3.6e6
    drive_efficiency: float=.90
    regen_efficiency: float=.75
    aux_w: float=500.
    rolling_coefficient: float=.012
    drag_area_m2: float=.65
    motor_tau_s: float=.04
    motor_slew_nm_s: float=2000.
    friction_tau_s: float=.18
    regen_zero_m_s: float=.3
    regen_full_m_s: float=1.5
    mu: float=.85

@dataclass
class State:
    motor_nm: float=0.
    friction_n: float=0.
    soc_energy_fraction: float=.55

def limits(v,soc,temp,p):
    omega=abs(v)*p.ratio/p.wheel_radius_m
    # Smooth, synthetic SOC/temperature maps, NOT universal vehicle thresholds.
    discharge_factor=clip((soc-.03)/.07,0.,1.)*clip((temp+20.)/30.,.3,1.)
    charge_factor=clip((1.-soc)/.10,0.,1.)*clip((temp+5.)/20.,0.,1.)
    drive=min(p.motor_max_nm,p.motor_max_w/max(omega,1.),p.discharge_max_w*discharge_factor*p.drive_efficiency/max(omega,1.))
    low_speed=clip((abs(v)-p.regen_zero_m_s)/(p.regen_full_m_s-p.regen_zero_m_s),0.,1.)
    regen=min(p.regen_max_nm*low_speed,p.charge_max_w*charge_factor/(p.regen_efficiency*max(omega,1.)))
    return drive,regen,omega

def step(v,a_request,temp,state,p,dt):
    resistance=p.mass_kg*9.81*p.rolling_coefficient*clip(v/.1,0.,1.)+.5*1.225*p.drag_area_m2*v*v
    force_request=p.equivalent_mass_kg*a_request+resistance
    drive_cap,regen_cap,omega=limits(v,state.soc_energy_fraction,temp,p)
    desired_nm=clip(force_request*p.wheel_radius_m/p.ratio,-regen_cap,drive_cap)
    motor_change=(1.-math.exp(-dt/p.motor_tau_s))*(desired_nm-state.motor_nm)
    state.motor_nm += clip(motor_change,-p.motor_slew_nm_s*dt,p.motor_slew_nm_s*dt)
    state.motor_nm=clip(state.motor_nm,-regen_cap,drive_cap)
    motor_force=state.motor_nm*p.ratio/p.wheel_radius_m
    # Track total wheel force. Friction compensates for ACTUAL electric braking,
    # including residual positive motor torque while switching into braking.
    friction_request=max(0.,motor_force-force_request)
    state.friction_n += (1.-math.exp(-dt/p.friction_tau_s))*(friction_request-state.friction_n)
    state.friction_n=clip(state.friction_n,0.,p.mass_kg*7.)
    tire_force=clip(motor_force-state.friction_n,-p.mu*p.mass_kg*9.81,p.mu*p.mass_kg*9.81)
    acceleration=(tire_force-resistance)/p.equivalent_mass_kg
    shaft_w=state.motor_nm*omega
    electric_w=(shaft_w/p.drive_efficiency if shaft_w>=0 else shaft_w*p.regen_efficiency)
    battery_w=electric_w+p.aux_w
    state.soc_energy_fraction=clip(state.soc_energy_fraction-battery_w*dt/p.battery_j,0.,1.)
    return {'a_m_s2':acceleration,'motor_nm':state.motor_nm,'motor_limit_nm':drive_cap,
            'regen_limit_nm':regen_cap,'regen_force_n':max(0.,-motor_force),
            'friction_n':state.friction_n,'battery_w':battery_w,
            'regen_electric_w':max(0.,-electric_w),'shaft_w':shaft_w,
            'resistance_n':resistance,'wheel_force_n':tire_force,
            'force_request_n':force_request,'soc':state.soc_energy_fraction}

def target(x,v,t,mode,hold_until):
    # Same high-level longitudinal controller for ideal and BEV plants.
    # Two spatial stop targets and a 2s intermediate hold; no dynamic obstacle.
    if mode=='first_stop':
        ref=min(3.,math.sqrt(2.*.65*max(0.,10.-x)))
        if v<.04 and x>9.5: mode,hold_until='hold',t+2.
    elif mode=='hold':
        ref=0.
        if t>=hold_until: mode='second_stop'
    else:
        ref=min(3.,math.sqrt(2.*.65*max(0.,40.-x)))
    return ref,mode,hold_until

def run(name,soc,temp,p,ideal=False,dt=.02):
    state=State(soc_energy_fraction=soc)
    x=y=psi=v=delta=0.
    mode,hold_until='first_stop',0.
    windows=[[None,None],[None,None]]
    trace=[]
    first_stop=None
    draw_j=regen_j=friction_j=net_j=0.
    max_lat=0.
    previous_request=0.
    for k in range(int(60./dt)):
        t=k*dt
        ref,mode,hold_until=target(x,v,t,mode,hold_until)
        if mode=='hold' and first_stop is None: first_stop=x
        requested_a=clip(1.8*(ref-v),-2.5,1.5)
        # Simple near-zero hold abstraction, not a detailed hill-hold system.
        if ref==0. and v<.02: requested_a=min(requested_a,-.1)
        requested_a=clip(requested_a,previous_request-1.5*dt,previous_request+1.5*dt)
        previous_request=requested_a
        look=max(3.,1.2*v)
        target_y=.25*math.sin(math.pi*clip((x+look)/42.,0.,1.))**2
        alpha=math.atan2(target_y-y,look)-psi
        desired_delta=clip(math.atan2(5.4*math.sin(alpha),look),-.45,.45)
        delta+=clip(desired_delta-delta,-.5*dt,.5*dt)
        outputs=step(v,requested_a,temp,state,p,dt)
        a=requested_a if ideal else outputs['a_m_s2']
        next_v=max(0.,v+a*dt)
        actual_a=(next_v-v)/dt
        mid_v=.5*(v+next_v)
        c,s=math.cos(psi),math.sin(psi)
        corners=[(x+xx*c-yy*s,y+xx*s+yy*c) for xx in (-1.,3.5) for yy in (-.9,.9)]
        for g,(lo,hi) in enumerate(((14.,15.),(26.,27.))):
            if max(z[0] for z in corners)>=lo and min(z[0] for z in corners)<=hi:
                if windows[g][0] is None: windows[g][0]=t
                windows[g][1]=t+dt
        draw_j+=max(0.,outputs['battery_w'])*dt
        net_j+=outputs['battery_w']*dt
        regen_j+=outputs['regen_electric_w']*dt
        friction_j+=outputs['friction_n']*v*dt
        max_lat=max(max_lat,abs(v*v*math.tan(delta)/2.7))
        trace.append({'t_s':t,'x_m':x,'y_m':y,'yaw_rad':psi,'v_m_s':v,
                      'v_ref_m_s':ref,'a_request_m_s2':requested_a,'a_actual_m_s2':actual_a,
                      'steer_rad':delta,'mode':mode,**outputs})
        x+=dt*mid_v*c; y+=dt*mid_v*s; psi+=dt*mid_v*math.tan(delta)/2.7; v=next_v
        if mode=='second_stop' and x>39.5 and v<.02: break
    completed=(mode=='second_stop' and x>39.5 and v<.02)
    with (OUT/(name+'_trace.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)
    jerks=[abs((b['a_actual_m_s2']-a['a_actual_m_s2'])/dt) for a,b in zip(trace,trace[1:])]
    moving_jerks=[abs((b['a_actual_m_s2']-a['a_actual_m_s2'])/dt) for a,b in zip(trace,trace[1:]) if min(a['v_m_s'],b['v_m_s'])>.2]
    return {'case':name,'ideal_acceleration_override':ideal,'initial_soc':soc,'battery_temperature_c':temp,
            'completed':completed,'duration_s':trace[-1]['t_s'],'first_stop_x_m':first_stop,
            'final_stop_x_m':x,'gate1_enter_s':windows[0][0],'gate1_leave_s':windows[0][1],
            'first_stop_error_m':None if first_stop is None else first_stop-10.,
            'final_stop_error_m':x-40.,
            'gate2_enter_s':windows[1][0],'gate2_leave_s':windows[1][1],
            'max_jerk_m_s3':max(jerks),'max_lateral_accel_m_s2':max_lat,
            'max_jerk_moving_v_above_0_2_m_s3':max(moving_jerks,default=0.),
            'battery_draw_wh':None if ideal else draw_j/3600.,
            'net_battery_wh':None if ideal else net_j/3600.,
            'ending_soc_energy_fraction':None if ideal else state.soc_energy_fraction,
            'gross_regenerated_wh':None if ideal else regen_j/3600.,
            'friction_dissipated_wh':None if ideal else friction_j/3600.,
            'energy_note':'For ideal case actuator outputs are diagnostic only; energy not applicable.' if ideal else 'Lossless fixed-ratio gear; constant motor efficiencies; energy-based SOC proxy.'}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    p=Parameters()
    cases=[('ideal_acceleration',.55,25.,p,True),('bev_normal',.55,25.,p,False),
           ('bev_near_full',1.,25.,p,False),('bev_cold',.55,-5.,p,False),
           ('bev_cold_slow_friction',.55,-5.,Parameters(friction_tau_s=.35),False)]
    rows=[run(*case) for case in cases]
    with (OUT/'case_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    maps=[]
    for rpm in range(0,12001,200):
        v=rpm*2*math.pi/60*p.wheel_radius_m/p.ratio
        drive,regen,omega=limits(v,.55,25,p)
        maps.append({'rpm':rpm,'speed_m_s':v,'drive_torque_nm':drive,'regen_torque_nm':regen,'drive_shaft_power_kw':drive*omega/1000.})
    with (OUT/'assumed_motor_map.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(maps[0]));w.writeheader();w.writerows(maps)
    config={'vehicle':'generic single-motor battery electric passenger car, not manufacturer calibrated',
            'numeric_parameters_status':'ALL numeric values and maps are research assumptions, not Tesla specifications.',
            'parameters':asdict(p),'dt_s':.02,'held_temperature':True,
            'soc_definition':'energy fraction proxy, not an electrochemical coulomb-counting battery model',
            'scope':'Feedback-tracked prescribed stop-go maneuver; no obstacle prediction, collision comparison, online motion selection, reverse or wheel slip/ABS model.',
            'cases':rows}
    (OUT/'config_and_results.json').write_text(json.dumps(config,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(rows,indent=2,ensure_ascii=False))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
        for color_index,row in enumerate(rows):
            with (OUT/(row['case']+'_trace.csv')).open() as f: data=list(csv.DictReader(f))
            tt=[float(z['t_s']) for z in data]
            color=f'C{color_index}'
            axs[0].plot(tt,[float(z['v_m_s']) for z in data],label=row['case'],color=color)
            if not row['ideal_acceleration_override']:
                axs[1].plot(tt,[float(z['regen_force_n']) for z in data],label=row['case'],color=color)
                axs[2].plot(tt,[float(z['friction_n']) for z in data],label=row['case'],color=color)
        for ax in axs: ax.grid(alpha=.2)
        axs[0].set_ylabel('Speed (m/s)');axs[1].set_ylabel('Regen force (N)');axs[2].set_ylabel('Friction force (N)')
        axs[2].set_xlabel('Time (s)');axs[0].legend(fontsize=8,ncol=2)
        fig.suptitle('Assumed BEV stop-go model: friction compensates limited regeneration')
        fig.tight_layout();fig.savefig(OUT/'bev_stop_go.png',dpi=150);plt.close(fig)
    except ImportError: pass

if __name__=='__main__': main()
