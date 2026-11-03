from pathlib import Path
import csv,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle,Rectangle
from matplotlib.animation import FuncAnimation,PillowWriter
from crossing_2d import OUT,Vehicle,corners,STALLS,XGRID,YGRID

rows=json.loads((OUT/'episodes.json').read_text())
selected=['cross14_cold_slow_nominal','cross14_cold_slow_stop_wait','cross14_cold_slow_candidate']
fig,axs=plt.subplots(3,1,figsize=(10,8))
ax=axs[0]
for x0,x1,y0,y1 in STALLS: ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color='.6'))
ax.plot(XGRID,YGRID,'k--',lw=1,label='Reference path')
example=list(csv.DictReader((OUT/'cross14_cold_slow_candidate_trace.csv').open()))
ax.plot([float(r['x_m']) for r in example],[float(r['y_m']) for r in example],label='Executed BEV path')
for target in (8,11,14,18):
    r=min(example,key=lambda z:abs(float(z['t_s'])-target))
    car=Vehicle(x=float(r['x_m']),y=float(r['y_m']),yaw=float(r['yaw_rad']))
    ax.add_patch(Polygon(corners(car),fill=False,edgecolor='tab:blue',alpha=.7))
ax.plot([20,20],[-3,3],color='tab:red',label='Pedestrian crossing line')
ax.set(xlim=(-3,45),ylim=(-3.3,3.3),xlabel='x (m)',ylabel='y (m)',title='Full vehicle footprint in a narrowed road')
ax.set_aspect('equal',adjustable='box');ax.legend(fontsize=7,loc='upper left',ncol=2)
for name in selected:
    data=list(csv.DictReader((OUT/(name+'_trace.csv')).open()))
    tt=[float(r['t_s']) for r in data]
    label=name.replace('cross14_cold_slow_','')
    axs[1].plot(tt,[float(r['v_m_s']) for r in data],label=label)
    axs[2].plot(tt,[float(r['clearance_m']) for r in data],label=label)
axs[1].set(xlabel='Time (s)',ylabel='Speed (m/s)');axs[1].legend(fontsize=8)
axs[2].axhline(0,color='red',ls='--',label='Contact threshold')
axs[2].set(xlabel='Time (s)',ylabel='Pedestrian clearance (m)',ylim=(-.5,4))
for ax in axs:ax.grid(alpha=.2)
fig.suptitle('Scripted crossing validation: contact, stop, and resume')
fig.tight_layout();fig.savefig(OUT/'crossing_overview.png',dpi=160);plt.close(fig)

# A local replay uses actual CSV state samples, not re-simulated animation poses.
fig,ax=plt.subplots(figsize=(8,3.5))
for x0,x1,y0,y1 in STALLS:ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color='.65'))
ax.plot(XGRID,YGRID,'k--',lw=1)
ax.set(xlim=(8,30),ylim=(-3.5,3.5),xlabel='x (m)',ylabel='y (m)')
ax.set_aspect('equal',adjustable='box')
body=Polygon(corners(Vehicle()),color='tab:blue',alpha=.7);ax.add_patch(body)
person=Circle((20,0),.3,color='tab:red');ax.add_patch(person)
title=ax.set_title('')
frames=[r for r in example[::10] if 8<=float(r['t_s'])<=22]
def update(i):
    r=frames[i];car=Vehicle(x=float(r['x_m']),y=float(r['y_m']),yaw=float(r['yaw_rad']))
    body.set_xy(corners(car));person.center=(float(r['ped_x_m']),float(r['ped_y_m']))
    title.set_text(f"t={float(r['t_s']):.1f}s | {r['phase']} | v={float(r['v_m_s']):.2f} m/s")
    return body,person,title
animation=FuncAnimation(fig,update,frames=len(frames),interval=100,blit=False)
fig.tight_layout();animation.save(OUT/'crossing_local_replay.gif',writer=PillowWriter(fps=10));plt.close(fig)

root=Path(__file__).resolve().parent
manifest={'case_count':len(rows),'center_time_values_s':sorted({r['center_time_s'] for r in rows}),
          'conditions':sorted({(r['soc_initial'],r['temperature_c'],r['friction_tau_s']) for r in rows}),
          'policies':sorted({r['policy'] for r in rows}),'numpy_version':np.__version__,
          'code_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in ('crossing_2d.py','test_crossing_2d.py','verify_crossing_2d.py','plot_crossing_2d.py','stopping_v2.py','bev_probe.py')},
          'replay':'CSV frame subsampling in simulated time; local view 8-22s; playback speed is not wall-clock vehicle speed'}
(OUT/'experiment_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(OUT/'crossing_overview.png');print(OUT/'crossing_local_replay.gif')
