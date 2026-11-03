from pathlib import Path
import numpy as np
import pandas as pd
from pilot_simulation import actual_events, perceived_events, plan_for_policy, evaluate
OUT=Path(__file__).parent / 'results'
x=pd.read_csv(OUT/'episode_results.csv')
rng=np.random.default_rng(8462)
paired=[]
for sig in [0.4,1.0,1.6]:
    group=x[x['sigma_s']==sig]
    pivot=group.pivot(index='episode', columns='policy', values='exposure').astype(int)
    for b in ['joint_nominal','robust_no_refuge','local_prediction']:
        diff=(pivot['joint_robust']-pivot[b]).to_numpy()
        inds=rng.integers(0,len(diff),size=(5000,len(diff)))
        boot=diff[inds].mean(axis=1)
        paired.append({'sigma_s':sig,'comparison':f'joint_robust minus {b}',
                       'risk_difference_pp':100*float(diff.mean()),
                       'bootstrap_low_pp':100*float(np.quantile(boot,.025)),
                       'bootstrap_high_pp':100*float(np.quantile(boot,.975))})
print(pd.DataFrame(paired).to_string(index=False))
pd.DataFrame(paired).to_csv(OUT/'paired_bootstrap.csv',index=False)

# Sensitivity: same synthetic scenario across padding choices for paired design.
pads=[0.0,0.5,1.0,1.25,2.0,3.0]
N=1000
rng=np.random.default_rng(20270117)
examples=[]
for i in range(N):
    actual=actual_events(rng)
    forecast=perceived_events(actual,rng,1.0)
    for pad in pads:
        p=plan_for_policy('joint_robust',forecast,pad)
        r=evaluate(p,actual)
        examples.append({'episode':i,'padding_s':pad,'exposure':int(r['exposure']),
                         'planned_finish_s':p.finish if p else np.nan})
sens=pd.DataFrame(examples)
output=sens.groupby('padding_s').agg(exposure_pct=('exposure',lambda a:100*a.mean()),
                                    planned_finish_s=('planned_finish_s','mean')).reset_index()
print('\nSensitivity\n'+output.to_string(index=False))
output.to_csv(OUT/'padding_sensitivity.csv',index=False)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(7.0,4.1))
ax.plot(output.padding_s, output.exposure_pct, marker='o',label='Exposure rate (%)')
ax.set_xlabel('Forecast interval padding (s)')
ax.set_ylabel('Conflict exposure (%)')
ax2=ax.twinx()
ax2.plot(output.padding_s, output.planned_finish_s,marker='s',ls='--',label='Planned finish time (s)')
ax2.set_ylabel('Planned finish time (s)')
ax.set_title('Pilot sensitivity at timing error sigma = 1.0 s')
fig.tight_layout();fig.savefig(OUT/'padding_sensitivity.png',dpi=170);plt.close(fig)
