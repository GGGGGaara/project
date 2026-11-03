from pathlib import Path
import csv,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from crossing_uncertain import OUT,forecast,Snapshot

names=[('pause_in_road_ideal_normal_frozen','Frozen'),('pause_in_road_ideal_normal_refresh_hold','Refresh while stopped'),
       ('pause_in_road_ideal_normal_rolling','Moving updates')]
fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
for name,label in names:
    rows=list(csv.DictReader((OUT/(name+'_trace.csv')).open()))
    tt=[float(r['t_s']) for r in rows]
    axs[0].plot(tt,[float(r['v_m_s']) for r in rows],label=label)
    axs[1].plot(tt,[float(r['clearance_m']) for r in rows],label=label)
    if label=='Moving updates':axs[2].plot(tt,[float(r['actual_ped_y_m']) for r in rows],color='k',label='Actual pedestrian y')
axs[1].axhline(0,color='red',ls='--')
axs[1].set_ylim(-.4,4)
for ax in axs:ax.grid(alpha=.2)
axs[0].set_ylabel('Vehicle speed (m/s)');axs[0].legend(fontsize=8)
axs[1].set_ylabel('Vehicle-body clearance (m)')
axs[2].set_ylabel('Pedestrian y (m)');axs[2].set_xlabel('Time (s)');axs[2].legend(fontsize=8)
fig.suptitle('Unexpected pedestrian pause: observation updates and retained failures')
fig.tight_layout();fig.savefig(OUT/'pause_comparison.png',dpi=160);plt.close(fig)

name='speedup_late_delay_negative_bias_normal_rolling'
rows=list(csv.DictReader((OUT/(name+'_trace.csv')).open()))
events=json.loads((OUT/(name+'_events.json')).read_text())
fig,axs=plt.subplots(3,1,figsize=(10,8),sharex=True)
tt=[float(r['t_s']) for r in rows]
axs[0].plot(tt,[float(r['v_m_s']) for r in rows],label='Speed')
axs[1].plot(tt,[float(r['a_actual_m_s2']) for r in rows],label='Actual acceleration')
axs[2].plot(tt,[float(r['actual_ped_y_m']) for r in rows],label='Actual pedestrian y')
obs_t=[e['t_s'] for e in events]
pred_y=[e['forecast_used']['y']+e['forecast_used']['vy']*(e['t_s']-e['forecast_used']['epoch']) for e in events]
axs[2].plot(obs_t,pred_y,'o--',label='CV current estimate from delayed observation',markersize=3)
for ax in axs:
    ax.axvline(12.,color='.5',ls=':',label='Actual speed change')
    ax.axvline(12.5,color='red',ls='--',label='Brake trigger')
    ax.grid(alpha=.2)
axs[0].set_ylabel('Speed (m/s)');axs[1].set_ylabel('Acceleration (m/s2)')
axs[2].set_ylabel('Pedestrian y (m)');axs[2].set_xlabel('Time (s)')
axs[0].legend(fontsize=7);axs[2].legend(fontsize=7)
fig.suptitle('Retained collision: delayed observation and insufficient validated fallback')
fig.tight_layout();fig.savefig(OUT/'retained_failure.png',dpi=160);plt.close(fig)

root=Path(__file__).resolve().parent
(OUT/'source_manifest.json').write_text(json.dumps({n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
    'crossing_uncertain.py','test_crossing_uncertain.py','verify_crossing_uncertain.py','plot_crossing_uncertain.py',
    'crossing_2d.py','stopping_v2.py','bev_probe.py')},indent=2),encoding='utf-8')
print(OUT/'pause_comparison.png');print(OUT/'retained_failure.png')
