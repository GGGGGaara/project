"""Independent integration checks and held-out step-size/preview-distance probes."""
from pathlib import Path
import csv
import json
import math
import unittest
import stopping_v2 as model
from stopping_v2 import Parameters,State,plant,simulate,OUT

class ModelChecks(unittest.TestCase):
    def test_work_energy_and_battery_energy_consistency(self):
        for torque in (-80.,80.):
            p=Parameters();state=State();soc0=state.soc_energy_fraction;v0=3.;dt=.02
            nv,dx,a,free_a,power=plant(v0,state,torque,300.,25.,p,dt)
            self.assertAlmostEqual(.5*p.equivalent_mass_kg*(nv*nv-v0*v0),p.equivalent_mass_kg*free_a*dx,places=8)
            self.assertAlmostEqual((soc0-state.soc_energy_fraction)*p.battery_j,power*dt,places=6)
    def test_flat_standstill_has_no_creep_or_spurious_regeneration(self):
        state=State(friction_n=300.)
        for _ in range(100):
            v,dx,a,_,power=plant(0.,state,0.,300.,25.,Parameters(),.02)
            self.assertEqual(v,0.);self.assertEqual(dx,0.);self.assertEqual(a,0.)
            self.assertEqual(power,Parameters().aux_w)
    def test_saved_positions_are_integrated_not_snapped_to_target(self):
        traces=list(OUT.glob('*_trace.csv'))
        self.assertTrue(traces)
        for path in traces:
            rows=list(csv.DictReader(path.open()))
            for a,b in zip(rows,rows[1:]):
                dt=float(b['t_s'])-float(a['t_s']);v=float(a['v_m_s']);acc=float(a['a_free_m_s2'])
                predicted_dx=(v*v/(-2*acc) if acc<0 and v+acc*dt<0 else .5*(v+max(0.,v+acc*dt))*dt)
                self.assertAlmostEqual(float(b['x_m'])-float(a['x_m']),predicted_dx,places=9)
    def test_terminal_error_and_failures_reported_separately(self):
        rows=json.loads((OUT/'sweep.json').read_text())
        self.assertEqual(len(rows),48)
        for r in rows:
            if r['reference_available']:
                self.assertTrue(r['completed'],r['case'])
                self.assertLessEqual(max(abs(r['first_stop_error_m']),abs(r['final_stop_error_m'])),.1)
                self.assertLess(r['hold_drift_m'],.001)
            else:
                self.assertFalse(r['completed']);self.assertEqual(r['initial_v_m_s'],4.)

def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ModelChecks))
    if not result.wasSuccessful(): raise SystemExit(1)
    rows=json.loads((OUT/'sweep.json').read_text())
    checks=[]
    for v0,temp,tau in ((0.,25.,.18),(0.,-5.,.35),(3.,-5.,.35)):
        coarse=next(r for r in rows if r['initial_v_m_s']==v0 and r['temperature_c']==temp and r['actual_friction_tau_s']==tau and r['initial_soc']==.55)
        fine=simulate(f'fine_v{v0:g}_t{temp:g}_tau{tau:g}',v0,.55,temp,tau,dt=.01,save=False)
        assert fine['completed']
        error_diff=max(abs(fine[k]-coarse[k]) for k in ('first_stop_error_m','final_stop_error_m'))
        assert error_diff<.01
        checks.append({'initial_v':v0,'temp':temp,'tau':tau,'max_stop_error_difference_m':error_diff,
                       'jerk_dt002':coarse['max_raw_jerk_m_s3'],'jerk_dt001':fine['max_raw_jerk_m_s3'],
                       'max_zero_crossing_pre_speed_m_s':max((e['v_before_m_s'] for e in fine['stop_events']),default=0.)})
    preview=simulate('v4_preview15m',4.,.55,-5.,.35,save=True,first_target=15.,final_target=45.)
    assert preview['completed'] and max(abs(preview['first_stop_error_m']),abs(preview['final_stop_error_m']))<.1
    sensitivity=[]
    for scale in (.02,.03,.05):
        model.BRAKE_REGULARIZATION_M_S=scale
        run=simulate(f'friction_scale_{scale:g}',0.,.55,-5.,.35)
        assert run['completed'] and max(abs(run['first_stop_error_m']),abs(run['final_stop_error_m']))<.1
        sensitivity.append({'regularization_m_s':scale,'first_stop_error_m':run['first_stop_error_m'],
                            'final_stop_error_m':run['final_stop_error_m'],'max_raw_jerk_m_s3':run['max_raw_jerk_m_s3']})
    model.BRAKE_REGULARIZATION_M_S=.03
    output={'unit_tests_passed':result.testsRun,'dt_refinement':checks,'extended_preview_example':preview,
            'regularization_sensitivity':sensitivity,
            'interpretation':'15m example changes available stopping distance; not a matched 10m comparison or proof of safe emergency fallback.'}
    (OUT/'verification.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
