"""Check saved replay and geometry, then refine selected executions in time."""
import csv,json,math,unittest
from crossing_2d import OUT,Vehicle,Scene,execute,circle_clearance,geometry

class ReplayChecks(unittest.TestCase):
    def test_experiment_grid_and_outcome_classification(self):
        rows=json.loads((OUT/'episodes.json').read_text())
        self.assertEqual(len(rows),60)
        self.assertEqual(len({r['case'] for r in rows}),60)
        self.assertTrue(any(r['ped_collision'] for r in rows if r['policy']=='nominal'))
        self.assertTrue(any(r['ped_collision'] for r in rows if r['policy']=='slow_only'))
        for r in rows:
            self.assertEqual(r['collision_free_completion'],r['completed'] and not (r['ped_collision'] or r['static_collision'] or r['road_exit']))
            if r['policy'] in ('stop_wait','candidate'):
                self.assertTrue(r['collision_free_completion'],r['case'])
    def test_saved_replay_collision_and_steering(self):
        rows=json.loads((OUT/'episodes.json').read_text())
        for result in rows:
            if result['samples']==0:
                self.assertEqual(result['chosen_motion'],'no_plan')
                self.assertFalse(result['completed'])
                continue
            path=OUT/(result['case']+'_trace.csv')
            data=list(csv.DictReader(path.open()))
            self.assertEqual(len(data),result['samples'])
            scene=Scene(result['center_time_s'],result['ped_speed_m_s'])
            for r in data:
                car=Vehicle(x=float(r['x_m']),y=float(r['y_m']),yaw=float(r['yaw_rad']))
                gap,static,road=geometry(car,scene,float(r['t_s']))
                self.assertAlmostEqual(gap,float(r['clearance_m']),places=10)
                self.assertEqual(gap<=0,r['ped_collision']=='True')
                self.assertEqual(static,r['static_collision']=='True')
                self.assertEqual(road,r['road_exit']=='True')
                self.assertGreaterEqual(float(r['v_m_s']),0.)
                self.assertLessEqual(abs(float(r['steer_rad'])),.45+1e-10)
            for a,b in zip(data,data[1:]):
                self.assertGreater(float(b['t_s']),float(a['t_s']))
                self.assertLessEqual(abs(float(b['steer_rad'])-float(a['steer_rad']))/(float(b['t_s'])-float(a['t_s'])),.5+1e-8)
                ds=float(b['s_m'])-float(a['s_m'])
                displacement=math.hypot(float(b['x_m'])-float(a['x_m']),float(b['y_m'])-float(a['y_m']))
                self.assertAlmostEqual(ds,displacement,places=9)

def main():
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReplayChecks))
    if not tests.wasSuccessful():raise SystemExit(1)
    rows=json.loads((OUT/'episodes.json').read_text());refined=[]
    for policy,center,tau in [('nominal',14.,.18),('slow_only',28.,.18),('candidate',17.,.35),('candidate',14.,.35)]:
        coarse=next(r for r in rows if r['policy']==policy and r['center_time_s']==center and r['friction_tau_s']==tau and r['temperature_c']==(-5. if tau==.35 else 25.))
        fine=execute(policy,Scene(center),.55,coarse['temperature_c'],tau,dt=.01,save=False)
        assert coarse['ped_collision']==fine['ped_collision']
        assert coarse['collision_free_completion']==fine['collision_free_completion']
        refined.append({'policy':policy,'center_time_s':center,'collision_dt002':coarse['ped_collision'],
                        'collision_dt001':fine['ped_collision'],'clearance_difference_m':abs(coarse['min_ped_clearance_m']-fine['min_ped_clearance_m']),
                        'finish_time_difference_s':abs(coarse['finish_s']-fine['finish_s'])})
    missed_by_point=0
    for result in rows:
        if not result['ped_collision']:continue
        data=list(csv.DictReader((OUT/(result['case']+'_trace.csv')).open()))
        missed_by_point+=sum(r['ped_collision']=='True' and math.hypot(float(r['ped_x_m'])-float(r['x_m']),float(r['ped_y_m'])-float(r['y_m']))>.3 for r in data)
    report={'replay_tests_passed':tests.testsRun,'dt_refinement':refined,
            'body_contact_samples_missed_by_rear_axle_point_test':missed_by_point,
            'scope':'Specific deterministic replay/geometry tests, not a continuous-time collision guarantee or generalization test.'}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
