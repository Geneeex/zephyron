"""Regression checks of analytical constraints and input-to-output propagation.

Run with: python -X utf8 test_engineering_reproduction.py
No laboratory observations are generated or asserted by these tests.
"""
from pathlib import Path
import copy,csv,json,math,tempfile,unittest
from build_engineering_analysis import generate,parameters
from engineering_models import mission_duty_limit,energy_trajectory,vision_timing

BASE=Path(__file__).resolve().parent


def read_rows(directory,name):
    with (Path(directory)/name).open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


class MissionConstraints(unittest.TestCase):
    def test_stationary_infeasibility_is_not_zero_duty(self):
        result=mission_duty_limit(57.6,20,5,35,0)
        self.assertFalse(result['stationary_feasible'])
        self.assertIsNone(result['max_drive_duty_fraction'])
        self.assertEqual(result['state'],'infeasible_even_stationary')
        boundary=mission_duty_limit(50,10,5,35,0)
        self.assertTrue(boundary['stationary_feasible'])
        self.assertEqual(boundary['max_drive_duty_fraction'],0)

    def test_published_six_hour_duties(self):
        for solar,expected in [(0,.13142857142857142),(7.5,.34571428571428575),(15,.56)]:
            self.assertAlmostEqual(mission_duty_limit(57.6,6,5,35,solar)['max_drive_duty_fraction'],expected)

    def test_recharging_cannot_erase_an_intermediate_reserve_breach(self):
        result=energy_trajectory(15,57.6,8,[dict(duration_s=3600,load_W=13.75,accepted_charge_W=0),dict(duration_s=3600,load_W=5,accepted_charge_W=15)])
        self.assertAlmostEqual(result['final_Wh'],11.25)
        self.assertAlmostEqual(result['minimum_Wh'],1.25)
        self.assertFalse(result['reserve_feasible'])

    def test_intermediate_capacity_saturation_conserves_curtailed_energy(self):
        result=energy_trajectory(50,57.6,8,[dict(duration_s=3600,load_W=0,accepted_charge_W=15),dict(duration_s=3600,load_W=15,accepted_charge_W=0)])
        self.assertAlmostEqual(result['final_Wh'],42.6)
        self.assertAlmostEqual(result['curtailed_Wh'],7.4)
        self.assertAlmostEqual(result['final_Wh']+result['curtailed_Wh'],50)
        self.assertTrue(result['reserve_feasible'])

    def test_loss_of_energy_is_recorded_as_infeasible(self):
        result=energy_trajectory(1,57.6,0,[dict(duration_s=3600,load_W=5,accepted_charge_W=0),dict(duration_s=3600,load_W=0,accepted_charge_W=5)])
        self.assertEqual(result['unserved_Wh'],4)
        self.assertFalse(result['reserve_feasible'])

    def test_overloaded_capture_stream_requires_throttling(self):
        result=vision_timing(20,40000,2,50,50,.35)
        self.assertAlmostEqual(result['offered_stream_Mbps'],6.4)
        self.assertAlmostEqual(result['network_minimum_throttle_or_discard_fraction'],.6875)
        self.assertAlmostEqual(result['partial_capture_transfer_inference_upper_bound_fps'],6.25)
        self.assertFalse(result['network_can_carry_all_captured_frames_ideal'])
        self.assertEqual(result['network_state'],'requires_throttling_or_discard')


class Reproduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=json.loads((BASE/'new_design_baseline.json').read_text(encoding='utf-8-sig'))
        cls.scenarios=json.loads((BASE/'engineering_scenarios.json').read_text(encoding='utf-8-sig'))
        cls.temporary=tempfile.TemporaryDirectory(prefix='zephyron-regression-')
        cls.root=Path(cls.temporary.name)
        cls.reference=cls.root/'reference'
        cls.summary=generate(cls.baseline,cls.scenarios,cls.reference)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def variant(self,name,baseline=None,scenarios=None):
        out=self.root/name
        summary=generate(baseline or self.baseline,scenarios or self.scenarios,out)
        return out,summary

    def test_complete_clean_regeneration_is_deterministic(self):
        repeat,_=self.variant('repeat')
        expected={'energy_duty_sweep.csv','energy_mission_duty_limits.csv','pv_irradiance_temperature.csv','solar_recharge_lower_bound.csv','grade_load.csv','wheel_diameter_speed.csv','odometry_mismatch_paths.csv','gm_counting_time.csv','gm_background_scenario.csv','tds_fullscale_spec.csv','tds_partial_uncertainty.csv','vision_latency_scenarios.csv','zero_miss_confidence.csv','arm_torque_budget.csv','arm_unconstrained_workspace.csv','baseline_parameters.csv'}
        self.assertEqual({x.name for x in repeat.glob('*.csv')},expected)
        for name in expected|{'analytical_summary.json','analysis_provenance.json'}:
            self.assertEqual((repeat/name).read_bytes(),(self.reference/name).read_bytes(),name)
        self.assertEqual(len(read_rows(repeat,'arm_unconstrained_workspace.csv')),722)
        confidence=read_rows(repeat,'zero_miss_confidence.csv')
        self.assertEqual([int(x['independent_positive_trials']) for x in confidence],list(range(1,201)))
        dark20=next(x for x in read_rows(repeat,'energy_mission_duty_limits.csv') if x['mission_h']=='20' and x['irradiance_W_m2']=='0')
        self.assertEqual(dark20['state'],'infeasible_even_stationary')
        self.assertEqual(dark20['max_drive_duty_fraction'],'')

    def test_component_energy_changes_propagate(self):
        scenario=copy.deepcopy(self.scenarios)
        scenario['component_specs']['battery']['capacity_Ah']=7
        out,result=self.variant('battery7',scenarios=scenario)
        self.assertEqual(result['nominal_energy_Wh'],84)
        self.assertAlmostEqual(result['full_time_nominal_motion_dark_h']/self.summary['full_time_nominal_motion_dark_h'],7/6)
        self.assertAlmostEqual(float(read_rows(out,'solar_recharge_lower_bound.csv')[-1]['recharge_label_energy_h']),5.6)

    def test_baseline_auxiliary_and_pv_changes_propagate(self):
        baseline=copy.deepcopy(self.baseline);baseline['operating_assumptions']['auxiliary_battery_power_W']+=2
        out,_=self.variant('auxiliary',baseline=baseline)
        new=read_rows(out,'energy_duty_sweep.csv');old=read_rows(self.reference,'energy_duty_sweep.csv')
        for a,b in zip(new,old):self.assertAlmostEqual(float(a['load_W'])-float(b['load_W']),2)
        scenario=copy.deepcopy(self.scenarios);scenario['component_specs']['pv']['nameplate_W']/=2
        out,_=self.variant('pvhalf',scenarios=scenario)
        for a,b in zip(read_rows(out,'pv_irradiance_temperature.csv'),read_rows(self.reference,'pv_irradiance_temperature.csv')):
            self.assertAlmostEqual(float(a['panel_dc_W']),float(b['panel_dc_W'])/2)

    def test_mass_diameter_motor_and_arm_changes_propagate(self):
        baseline=copy.deepcopy(self.baseline);baseline['mass_budget_kg']['payload_target']+=2;baseline['mass_budget_kg']['gross_model_mass']+=2
        out,_=self.variant('mass14',baseline=baseline)
        for a,b in zip(read_rows(out,'grade_load.csv'),read_rows(self.reference,'grade_load.csv')):
            self.assertAlmostEqual(float(a['torque_each_Nm'])/float(b['torque_each_Nm']),14/12)
        baseline=copy.deepcopy(self.baseline);baseline['geometry_mm']['wheel_diameter']+=20;baseline['geometry_mm']['overall_wheel_footprint_length']+=20
        out,result=self.variant('wheel185',baseline=baseline)
        self.assertAlmostEqual(result['no_load_speed_m_s']/self.summary['no_load_speed_m_s'],185/165)
        self.assertAlmostEqual(float(read_rows(out,'grade_load.csv')[10]['torque_each_Nm'])/float(read_rows(self.reference,'grade_load.csv')[10]['torque_each_Nm']),185/165)
        scenario=copy.deepcopy(self.scenarios);scenario['component_specs']['motor']['free_speed_rpm']*=1.1
        out,_=self.variant('motor110',scenarios=scenario)
        for a,b in zip(read_rows(out,'wheel_diameter_speed.csv'),read_rows(self.reference,'wheel_diameter_speed.csv')):
            self.assertAlmostEqual(float(a['no_load_speed_m_s'])/float(b['no_load_speed_m_s']),1.1)
        baseline=copy.deepcopy(self.baseline);baseline['arm']['upper_link_m']+=.02
        out,_=self.variant('arm_longer',baseline=baseline)
        self.assertAlmostEqual(float(read_rows(out,'arm_unconstrained_workspace.csv')[0]['forward_m']),.430)
        self.assertGreater(float(read_rows(out,'arm_torque_budget.csv')[-1]['shoulder_gravity_torque_Nm']),float(read_rows(self.reference,'arm_torque_budget.csv')[-1]['shoulder_gravity_torque_Nm']))

    def test_inconsistent_derived_geometry_fails_loudly(self):
        baseline=copy.deepcopy(self.baseline);baseline['geometry_mm']['wheel_diameter']+=20
        with self.assertRaisesRegex(ValueError,'footprint'):
            parameters(baseline,self.scenarios)

    def test_declared_headlines_remain_original_scenarios(self):
        self.assertAlmostEqual(self.summary['full_time_nominal_motion_dark_h'],1.44)
        self.assertAlmostEqual(self.summary['quarter_duty_dark_h'],4.189090909090909)
        self.assertAlmostEqual(self.summary['quarter_duty_500Wm2_h'],9.216)
        self.assertEqual(self.summary['zero_miss_trials_for_upper5pct'],59)
        grade=read_rows(self.reference,'grade_load.csv')[10]
        self.assertAlmostEqual(float(grade['torque_each_Nm']),.5172569783356579)
        latency=next(x for x in read_rows(self.reference,'vision_latency_scenarios.csv') if x['capture_fps']=='5' and x['link_Mbps']=='2' and x['inference_ms']=='50')
        self.assertAlmostEqual(float(latency['total_event_to_display_ms']),360)
        self.assertAlmostEqual(float(latency['travel_during_latency_m']),.126)


if __name__=='__main__':
    unittest.main(verbosity=2)
