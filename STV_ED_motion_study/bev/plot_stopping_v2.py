from dataclasses import asdict
from pathlib import Path
import csv
import hashlib
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from stopping_v2 import OUT,Parameters,BRAKE_REGULARIZATION_M_S

fig,axs=plt.subplots(4,1,figsize=(10,9),sharex=True)
for name,label in [('v0_soc0.55_temp25_tau0.18','Normal'),('v0_soc0.55_temp-5_tau0.35','Cold + slower friction response')]:
    data=list(csv.DictReader((OUT/(name+'_trace.csv')).open()))
    t=[float(r['t_s']) for r in data]
    axs[0].plot(t,[float(r['v_m_s']) for r in data],label=label)
    axs[1].plot(t,[float(r['x_m'])-float(r['x_ref_m']) for r in data])
    aa=[float(r['a_actual_m_s2']) for r in data]
    axs[2].plot(t,aa)
    axs[3].plot(t[1:],[(b-a)/(tt-t0) for a,b,t0,tt in zip(aa,aa[1:],t,t[1:])])
for ax in axs:ax.grid(alpha=.2)
axs[0].legend(fontsize=8);axs[0].set_ylabel('Speed (m/s)')
axs[1].set_ylabel('Position error (m)');axs[2].set_ylabel('Acceleration (m/s2)')
axs[3].set_ylabel('Raw jerk (m/s3)');axs[3].set_xlabel('Time (s)')
fig.suptitle('Synthetic BEV stopping v2: position tracking and near-zero regularization')
fig.tight_layout();fig.savefig(OUT/'stopping_tracking.png',dpi=160);plt.close(fig)

root=Path(__file__).resolve().parent
metadata={'python':sys.version,'parameters':asdict(Parameters()),'brake_regularization_m_s':BRAKE_REGULARIZATION_M_S,
          'reference':{'first_target_m':10.,'final_target_m':40.,'max_abs_acceleration_m_s2':1.1,'max_abs_jerk_m_s3':1.5,'check_samples':301},
          'hold_entry':{'speed_m_s':.002,'position_error_m':.05,'actual_acceleration_m_s2':.05},
          'code_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('bev_probe.py','stopping_v2.py','verify_stopping_v2.py','plot_stopping_v2.py')},
          'claim_boundary':'Assumed model and baseline controller, not vehicle-calibrated or a new research contribution.'}
(OUT/'run_metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(OUT/'stopping_tracking.png')
