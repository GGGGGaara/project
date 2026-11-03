"""Causal observer + CV forecast + moving risk monitor, for mechanism validation.
Actual world is never an input to forecast/risk functions. No safety guarantee.
"""
from dataclasses import dataclass,asdict,replace
from pathlib import Path
import csv,json,math,hashlib,sys
import numpy as np
from crossing_2d import Vehicle,END,STOP,XGRID,YGRID,SGRID,corners,rectangle_hit,STALLS,circle_clearance,make_plan
from stopping_v2 import Parameters,State,plant,commands,ref_values
from bev_probe import clip

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results_crossing_uncertain';DT=.02

@dataclass(frozen=True)
class World:
    name:str='constant'
    center_nominal_s:float=17.
    changes:tuple=()
    x:float=20.
    radius:float=.3
    def at(self,t):
        y=-self.center_nominal_s;speed=1.;last=0.
        for when,new_speed in self.changes:
            if t<when-1e-10:break
            y+=speed*(when-last);last=when;speed=new_speed
        return self.x,y+speed*(t-last),speed

@dataclass(frozen=True)
class Sensor:
    name:str='ideal';delay_s:float=0.;y_bias_m:float=0.;speed_bias_m_s:float=0.

@dataclass(frozen=True)
class Snapshot:
    received_t:float;measured_t:float;x:float;y:float;vy:float;radius:float

@dataclass(frozen=True)
class Forecast:
    epoch:float;x:float;y:float;vy:float;radius:float
    def at(self,t):return self.x,self.y+self.vy*(t-self.epoch)

def observe(world,sensor,now):
    measured=round(max(0.,now-sensor.delay_s),10)
    x,y,vy=world.at(measured)
    return Snapshot(now,measured,x,y+sensor.y_bias_m,vy+sensor.speed_bias_m_s,world.radius)

def forecast(snapshot):
    # Time-stamped CV compensation, not access to the current hidden truth.
    age=snapshot.received_t-snapshot.measured_t
    return Forecast(snapshot.received_t,snapshot.x,snapshot.y+snapshot.vy*age,snapshot.vy,snapshot.radius)

def path_pose(s,lateral_error=0.,heading_error=0.):
    s=clip(s,0.,END)
    x=float(np.interp(s,SGRID,XGRID));y=float(np.interp(s,SGRID,YGRID))
    eps=.03
    a=max(0.,s-eps);b=min(END,s+eps)
    heading=math.atan2(float(np.interp(b,SGRID,YGRID)-np.interp(a,SGRID,YGRID)),float(np.interp(b,SGRID,XGRID)-np.interp(a,SGRID,XGRID)))
    return x,y+lateral_error,heading+heading_error

def risk(car,plan,started,now,prediction,margin=.25):
    """Nominal path/time prediction only; does NOT propagate EV actuator uncertainty."""
    sr,_,_=ref_values(now-started,plan[2],plan[3],plan[0])
    offset=car.s-sr
    _,path_y,path_heading=path_pose(car.s)
    ey,epsi=car.y-path_y,car.yaw-path_heading
    minimum=math.inf
    horizon=max(0.,started+plan[2]-now)+1.
    for ahead in np.arange(0.,horizon+.001,.2):
        if ahead==0.:probe=car
        else:
            s,_,_=ref_values(now+ahead-started,plan[2],plan[3],plan[0])
            x,y,yaw=path_pose(s+offset,ey,epsi);probe=Vehicle(x=x,y=y,yaw=yaw)
        px,py=prediction.at(now+ahead)
        minimum=min(minimum,circle_clearance(probe,px,py,prediction.radius))
    return minimum<margin,minimum

def move(car,plan,started,t,p,temp,dt,mode):
    if mode=='emergency':sr,vr,ar=car.s,0.,-2.5
    elif mode=='hold':sr,vr,ar=car.s,0.,0.
    else:sr,vr,ar=ref_values(t-started,plan[2],plan[3],plan[0])
    tc,bc,request=commands(car.s,car.v,ar,sr,vr,car.ev,temp,p,dt,car.request,mode=='hold')
    car.request=request
    look=max(3.,1.2*car.v)
    tx,ty,_=path_pose(car.s+look)
    alpha=math.atan2(ty-car.y,tx-car.x)-car.yaw
    target=clip(math.atan2(5.4*math.sin(alpha),look),-.45,.45)
    car.delta+=clip(target-car.delta,-.5*dt,.5*dt)
    nv,ds,a,free,power=plant(car.v,car.ev,tc,bc,temp,p,dt)
    dyaw=ds*math.tan(car.delta)/2.7
    car.x+=ds*math.cos(car.yaw+.5*dyaw);car.y+=ds*math.sin(car.yaw+.5*dyaw)
    car.yaw+=dyaw;car.s+=ds;car.v=nv
    return a,{'a_actual_m_s2':a,'a_free_m_s2':free,'motor_nm':car.ev.motor_nm,
              'brake_capacity_n':car.ev.friction_n,'battery_power_w':power,'steer_rad':car.delta}

def choose_stop(car,now,prediction):
    if STOP-car.s<=.1:return None,'past_stop_target'
    try:plan=make_plan(car,STOP,3.)
    except ValueError:return None,'reference_not_found'
    dangerous,_=risk(car,plan,now,now,prediction)
    return (None,'predicted_stop_conflict') if dangerous else (plan,'stop_candidate')

def execute(policy,world,sensor,temp=25.,tau=.18,dt=DT,save=False,name='case'):
    car=Vehicle(ev=State(soc_energy_fraction=.55));p=replace(Parameters(),friction_tau_s=tau)
    plan=make_plan(car,END,3.);started=0.;mode='proceed';t=0.;next_check=0.
    initial=observe(world,sensor,0.);frozen=forecast(initial)
    observations=[];events=[];trace=[];status='timeout';emergency_count=0;replans=0
    for k in range(int(90./dt)):
        t=round(k*dt,10)
        if t+1e-9>=next_check:
            snap=observe(world,sensor,t);observations.append(asdict(snap))
            prediction=frozen if policy=='frozen' else forecast(snap)
            next_check+=.5
            event={'t_s':t,'mode_before':mode,'observation':asdict(snap),'forecast_used':asdict(prediction),'action':'keep'}
            # All strategies receive observations; their update rules differ explicitly.
            check_moving=(t<dt or policy=='rolling')
            if mode=='proceed' and check_moving:
                dangerous,gap=risk(car,plan,started,t,prediction);event['predicted_min_gap_m']=gap
                if dangerous:
                    stop,reason=choose_stop(car,t,prediction)
                    if stop is not None:
                        plan,started,mode=stop,t,'stop';replans+=1;event['action']='replan_stop'
                    elif car.v<.002:
                        mode='hold';event['action']='refuse_enter';event['reason']=reason
                    else:
                        mode='emergency';emergency_count+=1;event['action']='emergency_unverified';event['reason']=reason
            elif mode=='hold':
                try:resume=make_plan(car,END,3.)
                except ValueError:resume=None
                if resume is not None:
                    dangerous,gap=risk(car,resume,t,t,prediction);event['predicted_min_gap_m']=gap
                    if not dangerous:
                        plan,started,mode=resume,t,'proceed';replans+=1;event['action']='resume'
            events.append(event)
        a,outputs=move(car,plan,started,t,p,temp,dt,mode)
        t=round((k+1)*dt,10)
        px,py,vy=world.at(t)
        gap=circle_clearance(car,px,py,world.radius);poly=corners(car)
        static=any(rectangle_hit(poly,box) for box in STALLS);road=any(abs(y)>3. for x,y in poly)
        trace.append({'t_s':t,'x_m':car.x,'y_m':car.y,'yaw_rad':car.yaw,'s_m':car.s,'v_m_s':car.v,
                      'mode':mode,'actual_ped_x_m':px,'actual_ped_y_m':py,'actual_ped_vy_m_s':vy,
                      'clearance_m':gap,'ped_collision':gap<=0.,'static_collision':static,'road_exit':road,
                      'soc':car.ev.soc_energy_fraction,**outputs})
        # Collision is retained and terminates the episode; no impact dynamics claimed.
        if gap<=0 or static or road:status='collision';break
        if mode=='stop' and t-started>=plan[2] and car.v<.002 and abs(car.s-plan[1])<.05 and abs(a)<.05:
            mode='hold'
        elif mode=='emergency' and car.v<.002 and abs(a)<.05:mode='hold'
        elif mode=='proceed' and t-started>=plan[2] and car.v<.002 and abs(car.s-END)<.05 and abs(a)<.05:
            status='completed';break
    if status=='timeout' and car.s<.05 and car.v<.002:status='no_progress'
    row={'case':name,'policy':policy,'world':world.name,'sensor':sensor.name,'temperature_c':temp,'tau_s':tau,
         'status':status,'collision_free_completion':status=='completed','sim_end_s':t,
         'finish_s':t if status=='completed' else None,'min_clearance_m':min(r['clearance_m'] for r in trace),
         'replan_count':replans,'emergency_attempts':emergency_count,'observations':len(observations),'samples':len(trace),
         'dt_s':dt,'observation_period_s':.5}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        with (OUT/(name+'_trace.csv')).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)
        (OUT/(name+'_events.json')).write_text(json.dumps(events,indent=2),encoding='utf-8')
        (OUT/(name+'_observations.json')).write_text(json.dumps(observations,indent=2),encoding='utf-8')
    return row

WORLDS=[World('constant17',17.),World('speedup_early',17.,((9.,2.),)),
        World('speedup_late',17.,((12.,3.),)),World('pause_in_road',14.,((13.5,0.),(18.,1.)))]
SENSORS=[Sensor(),Sensor('delay_positive_bias',.4,.1,.12),Sensor('delay_negative_bias',.4,-.1,-.12)]

def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    for world in WORLDS:
        for sensor in SENSORS:
            for condition,temp,tau in [('normal',25.,.18),('cold_slow',-5.,.35)]:
                for policy in ('frozen','refresh_hold','rolling'):
                    name=f'{world.name}_{sensor.name}_{condition}_{policy}'
                    rows.append(execute(policy,world,sensor,temp,tau,save=True,name=name))
    (OUT/'episodes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    with (OUT/'episodes.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    stats=[]
    for policy in ('frozen','refresh_hold','rolling'):
        rr=[r for r in rows if r['policy']==policy]
        stats.append({'policy':policy,'n':len(rr),'statuses':{s:sum(r['status']==s for r in rr) for s in ('completed','collision','timeout','no_progress')},
                      'mean_success_finish_s':float(np.mean([r['finish_s'] for r in rr if r['finish_s'] is not None])) if any(r['finish_s'] is not None for r in rr) else None,
                      'emergency_episodes':sum(r['emergency_attempts']>0 for r in rr)})
    metadata={'worlds':[asdict(w) for w in WORLDS],'sensors':[asdict(s) for s in SENSORS],
              'initial_soc':.55,'dt_s':DT,'observation_period_s':.5,'prediction_margin_m':.25,
              'prediction_time_sampling_s':.2,'results':stats,
              'scope':'Hand-designed causal pipeline tests; nominal execution in risk prediction; no certified emergency safety, joint lateral optimization or innovation claim.',
              'python':sys.version,'numpy':np.__version__,
              'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('crossing_uncertain.py','crossing_2d.py','stopping_v2.py','bev_probe.py')}}
    (OUT/'config_summary.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
