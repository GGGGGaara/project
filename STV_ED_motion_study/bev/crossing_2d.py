"""2-D BEV + one scripted pedestrian; a validation baseline, not a new planner.
Perfect current pedestrian position/velocity; constant-velocity prediction.
Collision checks are sampled, not a continuous-time safety certificate.
"""
from dataclasses import dataclass,field,replace,asdict
from functools import lru_cache
from pathlib import Path
import copy,csv,hashlib,json,math,sys
import numpy as np
from stopping_v2 import Parameters,State,plant,commands,ref_values
from bev_probe import clip

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results_crossing_2d'
DT=.02
XGRID=np.linspace(0.,40.,2001)
YGRID=.25*np.sin(np.pi*XGRID/40.)**2
SGRID=np.concatenate(([0.],np.cumsum(np.hypot(np.diff(XGRID),np.diff(YGRID)))))
END=float(SGRID[-1]);STOP=float(np.interp(15.4,XGRID,SGRID))
STALLS=[(13.,24.,1.6,3.),(13.,24.,-3.,-1.6)]

@dataclass
class Vehicle:
    s:float=0.;x:float=0.;y:float=0.;yaw:float=0.;v:float=0.;delta:float=0.;request:float=0.
    ev:State=field(default_factory=State)

@dataclass(frozen=True)
class Scene:
    center_time_s:float=14.
    pedestrian_speed_m_s:float=1.
    pedestrian_x_m:float=20.
    pedestrian_radius_m:float=.3

def pedestrian(scene,t):
    return scene.pedestrian_x_m,scene.pedestrian_speed_m_s*(t-scene.center_time_s)

def corners(car):
    c,s=math.cos(car.yaw),math.sin(car.yaw)
    return [(car.x+xx*c-yy*s,car.y+xx*s+yy*c) for xx,yy in ((-1.,-.9),(3.5,-.9),(3.5,.9),(-1.,.9))]

def circle_clearance(car,px,py,r):
    c,s=math.cos(car.yaw),math.sin(car.yaw)
    dx,dy=px-car.x,py-car.y
    xx,yy=dx*c+dy*s,-dx*s+dy*c
    return math.hypot(max(-1.-xx,0.,xx-3.5),max(abs(yy)-.9,0.))-r

def rectangle_hit(poly,box):
    x0,x1,y0,y1=box
    other=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    axes=[(1.,0.),(0.,1.)]
    for a,b in zip(poly,poly[1:]+poly[:1]): axes.append((-(b[1]-a[1]),b[0]-a[0]))
    for ax,ay in axes:
        a=[ax*x+ay*y for x,y in poly];b=[ax*x+ay*y for x,y in other]
        if max(a)<min(b) or max(b)<min(a):return False
    return True

def geometry(car,scene,t):
    px,py=pedestrian(scene,t);poly=corners(car)
    gap=circle_clearance(car,px,py,scene.pedestrian_radius_m)
    static=any(rectangle_hit(poly,b) for b in STALLS)
    road=any(abs(y)>3. for x,y in poly)
    return gap,static,road

@lru_cache(maxsize=256)
def make_reference(distance,initial_v,speed_limit):
    matrix=np.array([[1,1,1,1],[4,5,6,7],[12,20,30,42],[24,60,120,210]],float)
    for T in np.arange(max(1.,distance/max(speed_limit,initial_v,.1)),90.,.05):
        coef=np.zeros(8);coef[1]=initial_v*T
        coef[4:]=np.linalg.solve(matrix,[distance-coef[1],-coef[1],0.,0.])
        poly=np.polynomial.Polynomial(coef);ss=np.linspace(0,1,301)
        vel=poly.deriv(1)(ss)/T;acc=poly.deriv(2)(ss)/T**2;jerk=poly.deriv(3)(ss)/T**3
        if min(vel)>=-1e-8 and max(vel)<=max(initial_v,speed_limit)+1e-8 and max(abs(acc))<=1.1 and max(abs(jerk))<=1.5:
            return float(T),tuple(coef)
    raise ValueError('No candidate reference in searched family')

def advance(car,t,plan,elapsed,p,temp,dt,hold=False):
    start,target,T,coef=plan
    sr,vr,ar=(target,0.,0.) if hold else ref_values(elapsed,T,coef,start)
    tc,bc,req=commands(car.s,car.v,ar,sr,vr,car.ev,temp,p,dt,car.request,hold)
    car.request=req
    look=max(3.,1.2*car.v)
    tx=float(np.interp(min(END,car.s+look),SGRID,XGRID))
    ty=float(np.interp(min(END,car.s+look),SGRID,YGRID))
    alpha=math.atan2(ty-car.y,tx-car.x)-car.yaw
    desired=clip(math.atan2(5.4*math.sin(alpha),look),-.45,.45)
    car.delta+=clip(desired-car.delta,-.5*dt,.5*dt)
    nv,ds,a,free,power=plant(car.v,car.ev,tc,bc,temp,p,dt)
    dyaw=ds*math.tan(car.delta)/2.7
    mid=car.yaw+.5*dyaw
    car.x+=ds*math.cos(mid);car.y+=ds*math.sin(mid);car.yaw+=dyaw;car.s+=ds;car.v=nv
    return {'a_actual_m_s2':a,'a_free_m_s2':free,'motor_nm':car.ev.motor_nm,'brake_capacity_n':car.ev.friction_n,
            'battery_power_w':power,'s_ref_m':sr,'v_ref_m_s':vr,'steer_rad':car.delta}

def make_plan(car,target,speed):
    T,coef=make_reference(round(target-car.s,8),round(car.v,8),speed)
    return car.s,target,T,coef

def segment(car,t,plan,p,temp,scene,dt=DT,trace=None,mode='proceed'):
    elapsed=0.;min_gap=math.inf;static_hit=road_hit=ped_hit=False
    rows=[] if trace is None else trace
    initial_gap,si,ro=geometry(car,scene,t)
    min_gap=min(min_gap,initial_gap);static_hit|=si;road_hit|=ro;ped_hit|=initial_gap<=0.
    for _ in range(int((plan[2]+12.)/dt)+2):
        outputs=advance(car,t,plan,elapsed,p,temp,dt)
        t+=dt;elapsed+=dt
        gap,si,ro=geometry(car,scene,t)
        min_gap=min(min_gap,gap);ped_hit|=gap<=0;static_hit|=si;road_hit|=ro
        px,py=pedestrian(scene,t)
        rows.append({'t_s':t,'s_m':car.s,'x_m':car.x,'y_m':car.y,'yaw_rad':car.yaw,'v_m_s':car.v,
                     'ped_x_m':px,'ped_y_m':py,'clearance_m':gap,'ped_collision':gap<=0.,
                     'static_collision':si,'road_exit':ro,'phase':mode,'soc':car.ev.soc_energy_fraction,**outputs})
        if elapsed>=plan[2] and car.v<.002 and abs(car.s-plan[1])<.05 and abs(outputs['a_actual_m_s2'])<.05:
            return t,{'complete':True,'min_gap':min_gap,'ped_hit':ped_hit,'static_hit':static_hit,'road_hit':road_hit}
    return t,{'complete':False,'min_gap':min_gap,'ped_hit':ped_hit,'static_hit':static_hit,'road_hit':road_hit}

def safe_trial(car,t,target,speed,temp,scene,margin=.25):
    trial=copy.deepcopy(car)
    try:plan=make_plan(trial,target,speed)
    except ValueError:return False,None,math.inf
    finish,check=segment(trial,t,plan,Parameters(),temp,scene)
    safe=check['complete'] and not check['static_hit'] and not check['road_hit'] and check['min_gap']>=margin
    return safe,plan,finish

def execute(policy,scene,soc=.55,temp=25.,tau=.18,dt=DT,save=False,name='case'):
    car=Vehicle(ev=State(soc_energy_fraction=soc));p=replace(Parameters(),friction_tau_s=tau)
    t=0.;trace=[];decisions=[];checks=[];chosen=policy;wait=0.
    if policy=='candidate':
        candidates=[]
        for label,speed in [('proceed',3.),('slow',1.5)]:
            safe,plan,finish=safe_trial(car,t,END,speed,temp,scene)
            if safe:candidates.append((finish,label,plan))
        # Nominal stop/wait rollout is compared under the SAME prediction and cost.
        stopped=execute('stop_wait',scene,soc,temp,.18,dt=DT,save=False,name='virtual_stop_wait')
        if stopped['collision_free_completion'] and stopped['min_ped_clearance_m']>=.25:
            candidates.append((stopped['finish_s'],'stop_wait',None))
        if candidates:
            _,chosen,plan=min(candidates,key=lambda x:x[0])
        else:
            # No admissible candidate: do not execute an unverified stop maneuver.
            # This is refusal at the initial staging area, not successful traversal.
            gap,si,ro=geometry(car,scene,0.)
            decision={'t_s':0.,'chosen':'no_plan','reason':'All forecast candidates rejected; no motion executed'}
            return {'case':name,'policy':policy,'chosen_motion':'no_plan','center_time_s':scene.center_time_s,
                    'ped_speed_m_s':scene.pedestrian_speed_m_s,'soc_initial':soc,'temperature_c':temp,'friction_tau_s':tau,
                    'completed':False,'ped_collision':gap<=0.,'static_collision':si,'road_exit':ro,
                    'collision_free_completion':False,'min_ped_clearance_m':gap,'finish_s':0.,'wait_s':0.,
                    'samples':0,'dt_s':dt,'decision_events':[decision]}
        decisions.append({'t_s':0.,'chosen':chosen,'safe_candidates':[c[1] for c in candidates],
                          'predicted_finishes_s':{c[1]:c[0] for c in candidates}})
    if chosen in ('nominal','proceed','slow','slow_only'):
        speed=1.5 if chosen in ('slow','slow_only') else 3.
        plan=make_plan(car,END,speed)
        t,check=segment(car,t,plan,p,temp,scene,dt,trace,chosen);checks.append(check)
        complete=check['complete']
    else:
        plan=make_plan(car,STOP,3.)
        t,check=segment(car,t,plan,p,temp,scene,dt,trace,'approach_stop');checks.append(check)
        complete=False
        if check['complete']:
            while wait<=25.:
                safe,resume,_=safe_trial(car,t,END,3.,temp,scene)
                decisions.append({'t_s':t,'chosen':'resume' if safe else 'hold','wait_s':wait})
                if safe:
                    t,last=segment(car,t,resume,p,temp,scene,dt,trace,'resume');checks.append(last)
                    complete=last['complete'];break
                # Observe and reconsider every 0.5s; actual actuator states keep evolving.
                for _ in range(round(.5/dt)):
                    outputs=advance(car,t,plan,plan[2],p,temp,dt,hold=True);t+=dt
                    gap,si,ro=geometry(car,scene,t);px,py=pedestrian(scene,t)
                    trace.append({'t_s':t,'s_m':car.s,'x_m':car.x,'y_m':car.y,'yaw_rad':car.yaw,'v_m_s':car.v,
                                  'ped_x_m':px,'ped_y_m':py,'clearance_m':gap,'ped_collision':gap<=0.,
                                  'static_collision':si,'road_exit':ro,'phase':'hold','soc':car.ev.soc_energy_fraction,**outputs})
                wait+=.5
    # No collision row is discarded; negative control continues for diagnostic replay.
    collided=any(r['ped_collision'] or r['static_collision'] or r['road_exit'] for r in trace)
    minimum=min((r['clearance_m'] for r in trace),default=math.inf)
    row={'case':name,'policy':policy,'chosen_motion':chosen,'center_time_s':scene.center_time_s,
         'ped_speed_m_s':scene.pedestrian_speed_m_s,'soc_initial':soc,'temperature_c':temp,'friction_tau_s':tau,
         'completed':complete,'ped_collision':any(r['ped_collision'] for r in trace),
         'static_collision':any(r['static_collision'] for r in trace),'road_exit':any(r['road_exit'] for r in trace),
         'collision_free_completion':complete and not collided,'min_ped_clearance_m':minimum,
         'finish_s':t,'wait_s':wait,'samples':len(trace),'dt_s':dt,'decision_events':decisions}
    if save:
        OUT.mkdir(parents=True,exist_ok=True)
        with (OUT/(name+'_trace.csv')).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)
        (OUT/(name+'_decisions.json')).write_text(json.dumps(decisions,indent=2),encoding='utf-8')
    return row

def main():
    OUT.mkdir(parents=True,exist_ok=True);rows=[]
    for center in (2.,14.,17.,25.,28.):
        for condition,soc,temp,tau in [('normal',.55,25.,.18),('cold',.55,-5.,.18),('cold_slow',.55,-5.,.35)]:
            for policy in ('nominal','slow_only','stop_wait','candidate'):
                name=f'cross{center:g}_{condition}_{policy}'
                rows.append(execute(policy,Scene(center),soc,temp,tau,save=True,name=name))
    (OUT/'episodes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    fields=[k for k in rows[0] if k!='decision_events']
    with (OUT/'episodes.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
    stats=[]
    for policy in ('nominal','slow_only','stop_wait','candidate'):
        rr=[r for r in rows if r['policy']==policy]
        stats.append({'policy':policy,'n':len(rr),'completed':sum(r['completed'] for r in rr),
                      'collision_free_completion':sum(r['collision_free_completion'] for r in rr),
                      'ped_collision':sum(r['ped_collision'] for r in rr),'static_collision':sum(r['static_collision'] for r in rr),
                      'road_exit':sum(r['road_exit'] for r in rr),'mean_finish_s':sum(r['finish_s'] for r in rr)/len(rr)})
    config={'dt_s':DT,'vehicle_parameters':asdict(Parameters()),'scene':asdict(Scene()),'static_stalls':STALLS,
            'road_y_bounds_m':[-3,3],'vehicle_footprint_rear_axle_m':{'rear':-1,'front':3.5,'half_width':.9},
            'predictor':'perfect present position and velocity, constant velocity; exact in these scripted cases',
            'prediction_extra_clearance_m':.25,'hold_recheck_s':.5,'path':'y=0.25*sin(pi*x/40)^2, arc-length parameterized',
            'reference_feasibility':'sampled derivatives; baseline, not continuous-time certificate',
            'control':'reuse stopping_v2 torque/brake interface and plant, bicycle steering; predictor plant tau=.18 vs actual .18/.35',
            'limits':['sampled collision checking','no occlusion or prediction noise','no moving obstacles besides one pedestrian',
                      'no continuous replanning during a segment; initial candidate selection and hold/resume checks only',
                      'synthetic parameters; no real vehicle calibration','no research novelty or state-of-art superiority claim'],
            'python':sys.version,'code_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('bev_probe.py','stopping_v2.py','crossing_2d.py')},
            'results':stats}
    (OUT/'config_summary.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
