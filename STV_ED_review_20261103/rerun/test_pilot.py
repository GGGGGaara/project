import unittest
import numpy as np
from pilot_simulation import actual_events, perceived_events, plan_for_policy, evaluate, intersects

class TestPlanningLogic(unittest.TestCase):
    def test_overlap(self):
        self.assertTrue(intersects([(2,3)], 2.5, 4))
        self.assertFalse(intersects([(2,3)], 3.1, 4))
    def test_perfect_forecast_joint_policy_no_conflict(self):
        rng=np.random.default_rng(999)
        for i in range(300):
            actual=actual_events(rng)
            forecast=perceived_events(actual,rng,0.0)
            for policy in ('joint_nominal','joint_robust'):
                plan=plan_for_policy(policy,forecast,1.25)
                res=evaluate(plan,actual)
                self.assertTrue(res['completion'],msg=(policy,i,actual,plan,res))
    def test_joint_policy_never_uses_forecast_occupied_refuge(self):
        forecast={'gate_1': [], 'gate_2': [(8,100)], 'refuge': [(0,100)]}
        self.assertIsNone(plan_for_policy('joint_robust',forecast,1.25))

if __name__=='__main__': unittest.main()
