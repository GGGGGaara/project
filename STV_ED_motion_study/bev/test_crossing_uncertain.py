import unittest
from crossing_uncertain import World,Sensor,observe,forecast

class CausalityChecks(unittest.TestCase):
    def test_speed_event_on_observation_boundary_is_not_delayed(self):
        world=World('late',17.,((12.,3.),))
        self.assertEqual(observe(world,Sensor(),12.).vy,3.)
        self.assertEqual(world.at(12.-1e-12)[2],3.)
        self.assertEqual(world.at(12.-1e-7)[2],1.)
    def test_future_changes_cannot_change_past_observation_or_prediction(self):
        a=World('a',17.)
        b=World('b',17.,((9.,2.),))
        sensor=Sensor('delayed',.4,.1,.12)
        oa,ob=observe(a,sensor,9.2),observe(b,sensor,9.2)
        self.assertEqual(oa,ob)  # both measured at 8.8, before the event
        self.assertEqual(forecast(oa),forecast(ob))
        self.assertNotEqual(a.at(10.)[1],b.at(10.)[1])
    def test_delay_compensation_does_not_peek_at_unseen_speed_change(self):
        world=World('change',17.,((9.,2.),))
        obs=observe(world,Sensor('delay',.4),9.2)
        predicted=forecast(obs).at(9.2)[1]
        self.assertAlmostEqual(obs.measured_t,8.8)
        self.assertNotAlmostEqual(predicted,world.at(9.2)[1])
    def test_exact_cv_without_bias_matches_constant_world(self):
        world=World('constant',17.)
        pred=forecast(observe(world,Sensor('delay',.4),10.))
        self.assertAlmostEqual(pred.at(14.)[1],world.at(14.)[1])
    def test_pause_integral_and_resume_are_continuous(self):
        world=World('pause',14.,((13.5,0.),(18.,1.)))
        self.assertAlmostEqual(world.at(13.5)[1],-.5)
        self.assertAlmostEqual(world.at(18.)[1],-.5)
        self.assertAlmostEqual(world.at(19.)[1],.5)
    def test_observation_bias_is_explicit(self):
        world=World()
        obs=observe(world,Sensor('bias',0.,.1,.12),5.)
        self.assertAlmostEqual(obs.y,world.at(5.)[1]+.1)
        self.assertAlmostEqual(obs.vy,1.12)

if __name__=='__main__':unittest.main()
