"""Reaggregate only the named datasets; never rewrite historical experiment files."""
from pathlib import Path
import csv,hashlib,json,statistics,sys
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent/'manuscript_assets'

def main():
    OUT.mkdir(exist_ok=True)
    pilot=ROOT/'STV_ED_reproducible_pilot_bundle/rural_narrow_road_research/results'
    bev=ROOT/'STV_ED_motion_study/bev'
    rows=list(csv.DictReader((pilot/'episode_results.csv').open(encoding='utf-8-sig',newline='')))
    assert len(rows)==15000
    summary=list(csv.DictReader((pilot/'summary.csv').open(encoding='utf-8-sig',newline='')))
    for s in summary:
        rr=[r for r in rows if r['sigma_s']==s['sigma_s'] and r['policy']==s['policy']]
        assert len(rr)==int(s['n'])
        assert sum(r['exposure'] in ('True','1') for r in rr)==int(s['exposure_n'])
        assert sum(r['cause']=='no_plan' for r in rr)==int(s['cause_no_plan_n'])==0
    execution=bev/'results_crossing_uncertain'
    episodes=json.loads((execution/'episodes.json').read_text())
    config=json.loads((execution/'config_summary.json').read_text())
    for name,expected in config['source_sha256'].items():
        assert hashlib.sha256((bev/name).read_bytes()).hexdigest()==expected,name
    assert len(episodes)==72
    policies=('frozen','refresh_hold','rolling')
    key=lambda r:(r['world'],r['sensor'],r['temperature_c'],r['tau_s'])
    groups={p:{key(r):r for r in episodes if r['policy']==p} for p in policies}
    assert all(len(g)==24 for g in groups.values())
    assert all(set(groups[p])==set(groups['frozen']) for p in policies)
    common=set.intersection(*[{k for k,r in g.items() if r['status']=='completed'} for g in groups.values()])
    stats={p:{'counts':dict(Counter(r['status'] for r in g.values())),
              'own_success_mean_s':statistics.mean(r['finish_s'] for r in g.values() if r['status']=='completed'),
              'common_success_mean_s':statistics.mean(g[k]['finish_s'] for k in common),
              'horizon_penalty_mean_s':statistics.mean(r['finish_s'] if r['status']=='completed' else 90. for r in g.values())}
           for p,g in groups.items()}
    assert [stats[p]['counts']['completed'] for p in policies]==[8,10,22]
    report={'python':sys.version,'base_commit':'8e5f0d7810e136ec5abaa6956c233b3342e90c21',
            'pilot_records':len(rows),'execution_records':len(episodes),
            'common_success_n':len(common),'common_success_condition_keys':sorted(common),
            'statistics':stats,'score_definition':'Finish time for completed cases; 90 s for each failure. Not actual travel time.',
            'source_hashes_verified':config['source_sha256'],
            'data_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (pilot/'episode_results.csv',pilot/'summary.csv',execution/'episodes.json')}}
    (OUT/'evidence_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,3))
    for i,p in enumerate(policies):
        completed=stats[p]['counts']['completed']
        ax.barh(i,completed,color='#4477AA',label='Completed' if i==0 else '')
        ax.barh(i,24-completed,left=completed,color='#CC6677',hatch='///',label='Collision' if i==0 else '')
        ax.text(completed/2,i,f'{completed}',ha='center',va='center',color='white',weight='bold')
        ax.text(completed+(24-completed)/2,i,f'{24-completed}',ha='center',va='center',color='white',weight='bold')
    ax.set_yticks(range(3),['Frozen prediction','Refresh at hold','Rolling update'])
    ax.set_xlim(0,24);ax.set_xlabel('Constructed conditions (24 per policy)');ax.invert_yaxis()
    ax.legend(ncol=2,loc='upper center',bbox_to_anchor=(.5,1.25),frameon=False)
    fig.tight_layout();fig.savefig(OUT/'execution_comparison.png',dpi=220);plt.close(fig)

if __name__=='__main__':main()
