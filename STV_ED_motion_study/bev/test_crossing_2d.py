import math
import unittest
from unittest.mock import patch
from crossing_2d import Vehicle,Scene,execute,corners,circle_clearance,rectangle_hit

class GeometryChecks(unittest.TestCase):
    def test_rejects_all_candidates_without_executing_motion(self):
        with patch('crossing_2d.safe_trial',return_value=(False,None,math.inf)),patch('crossing_2d.execute',return_value={'collision_free_completion':False}):
            r=execute('candidate',Scene())
        self.assertFalse(r['completed']);self.assertFalse(r['ped_collision'])
        self.assertEqual(r['chosen_motion'],'no_plan');self.assertEqual(r['finish_s'],0.)
    def test_front_contact_when_reference_point_is_far_away(self):
        car=Vehicle()
        self.assertLess(circle_clearance(car,3.6,0.,.3),0.)
        self.assertGreater(math.hypot(3.6,0.)-.3,0.)
    def test_rear_side_corner_and_tangency(self):
        car=Vehicle()
        self.assertLess(circle_clearance(car,-1.1,0.,.3),0.)
        self.assertAlmostEqual(circle_clearance(car,0.,1.2,.3),0.,places=12)
        self.assertGreater(circle_clearance(car,3.8,1.2,.3),0.)
    def test_rotation_changes_collision_and_static_sat(self):
        car=Vehicle(yaw=math.pi/2)
        self.assertLess(circle_clearance(car,0.,3.6,.3),0.)
        self.assertGreater(circle_clearance(car,3.6,0.,.3),0.)
        self.assertTrue(rectangle_hit(corners(car),(-.2,.2,3.,4.)))
        self.assertFalse(rectangle_hit(corners(car),(2.,3.,2.,3.)))

if __name__=='__main__':unittest.main()
