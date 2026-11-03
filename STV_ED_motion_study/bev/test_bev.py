"""Physical and brake-blending consistency tests for the assumed BEV model."""
import math
import unittest
from bev_probe import Parameters,State,limits,step

class TestBEV(unittest.TestCase):
    def setUp(self): self.p=Parameters()
    def test_torque_power_envelope(self):
        p=self.p
        low,_,_=limits(0.,.55,25.,p)
        self.assertEqual(low,p.motor_max_nm)
        for v in (2.,10.,30.,45.):
            drive,regen,omega=limits(v,.55,25.,p)
            self.assertLessEqual(drive,p.motor_max_nm+1e-9)
            self.assertLessEqual(drive*omega,p.motor_max_w+1e-7)
            self.assertLessEqual(drive*omega/p.drive_efficiency,p.discharge_max_w+1e-7)
            self.assertLessEqual(regen*omega*p.regen_efficiency,p.charge_max_w+1e-7)
    def test_regeneration_restrictions(self):
        self.assertEqual(limits(3.,1.,25.,self.p)[1],0.)
        self.assertEqual(limits(3.,.55,-5.,self.p)[1],0.)
        self.assertEqual(limits(.2,.55,25.,self.p)[1],0.)
        self.assertGreater(limits(3.,.55,25.,self.p)[1],0.)
    def test_friction_compensates_regeneration_unavailable(self):
        values=[]
        for soc,temp in ((.55,25.),(1.,25.),(.55,-5.)):
            state=State(soc_energy_fraction=soc)
            # Actuator bench held at 3m/s to test steady force allocation.
            for _ in range(1500): out=step(3.,-.8,temp,state,self.p,.002)
            self.assertAlmostEqual(out['a_m_s2'],-.8,places=4)
            self.assertGreaterEqual(out['friction_n'],0.)
            values.append(out)
        self.assertGreater(values[2]['friction_n'],values[0]['friction_n'])
    def test_driving_and_regeneration_power_are_lossy(self):
        for request in (1.,-.8):
            state=State()
            for _ in range(200): out=step(3.,request,25.,state,self.p,.01)
            electric=out['battery_w']-self.p.aux_w
            if request>0:
                self.assertGreaterEqual(electric,out['shaft_w'])
            else:
                self.assertLessEqual(-electric,-out['shaft_w']+1e-9)
                self.assertGreater(out['regen_electric_w'],0.)
            self.assertAlmostEqual(out['a_m_s2'],(out['wheel_force_n']-out['resistance_n'])/self.p.equivalent_mass_kg,places=12)

if __name__=='__main__': unittest.main()
