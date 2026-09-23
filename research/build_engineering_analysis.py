"""Deterministic selected-design analysis; all outputs are scenarios, not observations."""
from pathlib import Path
import argparse, csv, hashlib, json, math
from engineering_models import mission_duty_limit, vision_timing

BASE = Path(__file__).resolve().parent


def inclusive_grid(spec):
    start, stop, step = spec
    if step <= 0 or stop < start:
        raise ValueError('Invalid increasing grid')
    n = int(round((stop - start) / step))
    return [round(start + i * step, 12) for i in range(n + 1)]


def parameters(b, s):
    geo, op, masses = b['geometry_mm'], b['operating_assumptions'], b['mass_budget_kg']
    motors, battery, panel = (s['component_specs'][k] for k in ('motor', 'battery', 'pv'))
    if not math.isclose(geo['overall_wheel_footprint_length'], geo['wheelbase'] + geo['wheel_diameter']):
        raise ValueError('Longitudinal tire footprint disagrees with wheelbase + diameter')
    if not math.isclose(geo['overall_wheel_footprint_width'], geo['track_center_to_center'] + geo['wheel_tread']):
        raise ValueError('Transverse tire footprint disagrees with track + tread')
    if not math.isclose(masses['gross_model_mass'], masses['dry_target'] + masses['payload_target']):
        raise ValueError('Gross mass budget differs from dry + payload allocation')
    if not 0 < op['usable_battery_fraction'] <= 1 or not 0 < op['pv_combined_derating'] <= 1:
        raise ValueError('Energy fractions must lie in (0, 1]')
    energy = battery['label_voltage_V'] * battery['capacity_Ah']
    return dict(energy_Wh=energy, usable_Wh=energy * op['usable_battery_fraction'],
                auxiliary_W=op['auxiliary_battery_power_W'], drive_W=op['drive_battery_power_nominal_W'],
                pv_W=panel['nameplate_W'], pv_derating=op['pv_combined_derating'],
                radius_m=geo['wheel_diameter'] / 2000, track_m=geo['track_center_to_center'] / 1000,
                mass_kg=masses['gross_model_mass'], gravity=s['constants']['gravity_m_s2'],
                rolling=op['rolling_resistance_coefficient'], speed_m_s=op['command_speed_m_s'],
                stall_Nm=motors['extrapolated_stall_torque_kgf_cm'] * s['constants']['kgf_cm_to_Nm'],
                gearbox_Nm=motors['continuous_gearbox_torque_kgf_cm'] * s['constants']['kgf_cm_to_Nm'],
                current_guidance_A=motors['extrapolated_stall_current_A'] * motors['continuous_current_fraction_of_stall'])


def generate(b, s, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    p = parameters(b, s)
    component = s['component_specs']
    motor, panel = component['motor'], component['pv']
    reference_G = panel['reference_irradiance_W_m2']
    files = []

    def write(name, rows):
        rows = list(rows)
        with (out / name).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        files.append(name)

    def solar(G):
        return p['pv_W'] * p['pv_derating'] * G / reference_G

    rows = []
    for percent in inclusive_grid(s['energy']['drive_duty_percent']):
        d = percent / 100
        for G in s['energy']['irradiance_W_m2']:
            load = p['auxiliary_W'] + d * p['drive_W']
            net = load - solar(G)
            rows.append(dict(drive_duty_fraction=d, irradiance_W_m2=G, load_W=load, solar_W=solar(G),
                             net_battery_power_W=net, runtime_h=p['usable_Wh'] / net if net > 0 else '',
                             state='finite_depletion' if net > 0 else 'conditional_energy_non_depleting',
                             evidence='MODELLED_constant_conditions_not_endurance_test'))
    write('energy_duty_sweep.csv', rows)
    write('energy_mission_duty_limits.csv',
          [dict(mission_h=h, irradiance_W_m2=G,
                **mission_duty_limit(p['usable_Wh'], h, p['auxiliary_W'], p['drive_W'], solar(G)),
                equation='B=E_usable/t+P_solar-P_aux; infeasible if B<0; otherwise d_max=min(1,B/P_drive)', evidence='MODELLED')
           for h in s['energy']['mission_hours'] for G in s['energy']['mission_irradiance_W_m2']])

    rows = []
    for T in s['pv']['cell_temperature_C']:
        for G in inclusive_grid(s['pv']['irradiance_grid_W_m2']):
            power = max(0, p['pv_W'] * G / reference_G * (1 + panel['power_temperature_coefficient_per_K'] * (T - panel['reference_cell_temperature_C'])))
            rows.append(dict(irradiance_W_m2=G, cell_temperature_C=T, panel_dc_W=power,
                             after_controller_W=s['pv']['standalone_controller_efficiency_assumed'] * power,
                             evidence='MODELLED_selected_panel_coefficient_separate_controller_efficiency_scenario'))
    write('pv_irradiance_temperature.csv', rows)
    write('solar_recharge_lower_bound.csv',
          [dict(irradiance_W_m2=G, available_solar_W=solar(G), recharge_label_energy_h=p['energy_Wh'] / solar(G),
                scope='MODELLED_energy_only_empty_to_full_load_off_no_CV_tail') for G in s['pv']['recharge_irradiance_W_m2']])
    rows = []
    for deg in inclusive_grid(s['mobility']['grade_grid_deg']):
        a = math.radians(deg)
        force = p['mass_kg'] * p['gravity'] * (math.sin(a) + p['rolling'] * math.cos(a))
        tau = force * p['radius_m'] / motor['count']
        current = motor['free_current_A'] + (motor['extrapolated_stall_current_A'] - motor['free_current_A']) * tau / p['stall_Nm']
        rows.append(dict(grade_deg=deg, total_mass_kg=p['mass_kg'], rolling_coefficient=p['rolling'], tractive_force_N=force,
                         torque_each_Nm=tau, approx_current_each_A=current,
                         full_nominal_voltage_no_load_curve_rpm=motor['free_speed_rpm'] * (1 - tau / p['stall_Nm']),
                         minimum_friction_coefficient=math.tan(a) + p['rolling'], continuous_gearbox_torque_limit_Nm=p['gearbox_Nm'],
                         continuous_current_guidance_A=p['current_guidance_A'], mechanical_power_at_command_speed_W=force * p['speed_m_s'],
                         evidence='MODELLED_equal_wheel_loading_no_turn_or_sinkage'))
    write('grade_load.csv', rows)
    write('wheel_diameter_speed.csv',
          [dict(diameter_mm=D, no_load_rpm=motor['free_speed_rpm'], no_load_speed_m_s=math.pi * D / 1000 * motor['free_speed_rpm'] / 60,
                at_commanded_speed_required_rpm=p['speed_m_s'] / (math.pi * D / 1000) * 60, evidence='MODELLED_diameter_sensitivity_only')
           for D in inclusive_grid(s['mobility']['wheel_diameter_grid_mm'])])
    rows = []
    for eps in s['mobility']['radius_mismatch_fraction']:
        k = eps / (p['track_m'] * (1 + eps / 2))
        for distance in inclusive_grid(s['mobility']['center_path_grid_m']):
            theta = k * distance
            rows.append(dict(diameter_mismatch_fraction=eps, center_path_length_m=distance,
                             forward_m=math.sin(theta) / k if k else distance, lateral_error_m=(1 - math.cos(theta)) / k if k else 0,
                             heading_error_deg=math.degrees(theta), evidence='MODELLED_ideal_differential_drive_equal_wheel_angular_speed'))
    write('odometry_mismatch_paths.csv', rows)
    rad = s['radiation']
    write('gm_counting_time.csv',
          [dict(rate_counts_s=r, integration_s=t, expected_counts=r*t, relative_poisson_standard_uncertainty=1/math.sqrt(r*t),
                rate_standard_uncertainty_counts_s=math.sqrt(r*t)/t, evidence='MODELLED_expected_Poisson_counts_no_background_no_deadtime')
           for r in rad['rate_counts_s'] for t in rad['integration_s']])
    write('gm_background_scenario.csv',
          [dict(signal_rate_cps=r, background_rate_cps=bg, sample_duration_s=t, background_duration_s=tb,
                net_standard_uncertainty_cps=math.sqrt((r+bg)/t+bg/tb), net_relative_standard_uncertainty=math.sqrt((r+bg)/t+bg/tb)/r,
                evidence='MODELLED_independent_Poisson_expected_counts')
           for r in rad['background_signal_rate_cps'] for bg in rad['background_rate_cps'] for t in rad['sample_duration_s'] for tb in rad['background_duration_s']])
    tds, ts = component['tds'], s['tds']
    abs_spec = tds['full_scale_ppm'] * tds['full_scale_spec_fraction']
    write('tds_fullscale_spec.csv', [dict(indicated_ppm=c, manufacturer_absolute_spec_limit_ppm=abs_spec, equivalent_relative_limit_pct=100*abs_spec/c,
          not_a_standard_uncertainty='Manufacturer_limit_not_probabilistic_uncertainty', evidence='CALCULATED_selected_SEN0244_fullscale_specification') for c in ts['indicated_ppm']])
    rows = []
    for voltage in ts['voltage_V']:
        temp = ts['temperature_C']; alpha = tds['temperature_coefficient_per_C']
        compensation = 1 + alpha * (temp - tds['reference_temperature_C'])
        if compensation <= 0:
            raise ValueError('TDS temperature compensation outside model domain')
        v = voltage / compensation
        a, c2, c1, c0 = tds['conversion_coefficients_descending']; mult = tds['conversion_multiplier']
        concentration = mult * (a*v**3+c2*v**2+c1*v+c0)
        derivative = mult * (3*a*v**2+2*c2*v+c1)
        uADC = abs(derivative / compensation) * (ts['ADC_reference_V_assumed'] / 2**ts['ADC_bits_assumed']) / math.sqrt(12)
        uTemp = abs(derivative * (-alpha * voltage / compensation**2)) * ts['temperature_standard_uncertainty_C_assumed']
        rows.append(dict(voltage_V=voltage, temperature_C=temp, tds_estimate_ppm=concentration,
                         ADC_quantization_standard_uncertainty_ppm=uADC, temperature_standard_uncertainty_C=ts['temperature_standard_uncertainty_C_assumed'],
                         temperature_contribution_ppm=uTemp, combined_partial_uncertainty_ppm=math.hypot(uADC,uTemp),
                         evidence='MODELLED_partial_budget_excludes_probe_calibration_matrix_drift_voltage_reference'))
    write('tds_partial_uncertainty.csv', rows)
    vision = s['vision']; other_ms = sum(vision[k] for k in ('decode_ms_assumed','postprocessing_ms_assumed','display_ms_assumed'))
    write('vision_latency_scenarios.csv',
          [dict(capture_fps=fps, frame_size_bytes_assumed=vision['frame_size_bytes_assumed'], link_Mbps=link, inference_ms=ms,
                **vision_timing(fps,vision['frame_size_bytes_assumed'],link,ms,other_ms,p['speed_m_s']),
                evidence='MODELLED_per_accepted_frame_no_queue_jitter_retransmission_or_humanreaction')
           for fps in vision['capture_fps'] for link in vision['link_Mbps'] for ms in vision['inference_ms']])
    confidence=s['confidence']; alpha=1-confidence['one_sided_confidence']
    write('zero_miss_confidence.csv', [dict(independent_positive_trials=n,observed_misses=0,one_sided_confidence=confidence['one_sided_confidence'],
          upper_miss_probability=1-alpha**(1/n),evidence='MODELLED_binomial_zero_miss_design_not_observed_data') for n in inclusive_grid(confidence['trial_grid'])])
    arm=b['arm']; L1,L2=arm['upper_link_m'],arm['forearm_m']; M1,M2,Mh=arm['upper_link_mass_kg_assumed'],arm['forearm_mass_kg_assumed'],arm['hand_mass_kg_assumed']
    rows=[]
    for payload in s['arm']['grasp_payload_kg']:
        shoulder=p['gravity']*(M1*L1/2+M2*(L1+L2/2)+(Mh+payload)*(L1+L2))
        elbow=p['gravity']*(M2*L2/2+(Mh+payload)*L2)
        rows.append(dict(grasp_payload_scenario_kg=payload,shoulder_gravity_torque_Nm=shoulder,elbow_gravity_torque_Nm=elbow,
                         shoulder_with_design_allowance_Nm=arm['dynamic_design_factor_assumed']*shoulder,
                         elbow_with_design_allowance_Nm=arm['dynamic_design_factor_assumed']*elbow,
                         evidence='MODELLED_horizontal_arm_assumed_linkmasses_not_payload_rating'))
    write('arm_torque_budget.csv',rows)
    write('arm_unconstrained_workspace.csv',
          [dict(boundary=boundary,angle_rad=math.radians(deg),forward_m=radius*math.cos(math.radians(deg)),vertical_m=radius*math.sin(math.radians(deg)),status='UNCONSTRAINED_geometric_scenario')
           for boundary,radius in [('outer',L1+L2),('inner',abs(L2-L1))] for deg in inclusive_grid(s['arm']['workspace_angle_grid_deg'])])
    params=[dict(parameter=k,value=v,unit='mm',evidence='SELECTED_nominal_central_chassis_clearance_target' if k=='ground_clearance' else 'SELECTED_design_geometry',source='new_design_baseline.json') for k,v in b['geometry_mm'].items()]
    for k,v,unit in [('dry_mass_target',b['mass_budget_kg']['dry_target'],'kg'),('gross_mass_target',p['mass_kg'],'kg'),('chassis_payload_target',b['mass_budget_kg']['payload_target'],'kg'),('nominal_label_energy',p['energy_Wh'],'Wh'),('usable_energy_assumption',p['usable_Wh'],'Wh'),('drive_power_assumption',p['drive_W'],'W'),('aux_power_assumption',p['auxiliary_W'],'W'),('PV_nameplate',p['pv_W'],'W'),('PV_derating_assumption',p['pv_derating'],'fraction'),('speed_cap',p['speed_m_s'],'m/s')]:
        params.append(dict(parameter=k,value=v,unit=unit,evidence='SELECTED_or_CALCULATED_not_measured',source='new_design_baseline.json_and_engineering_scenarios.json'))
    write('baseline_parameters.csv',params)
    d=s['energy']['summary_duty_fraction']; G=s['energy']['summary_irradiance_W_m2']; h=s['energy']['summary_mission_h']
    def depletion(duty,pv):
        net=p['auxiliary_W']+duty*p['drive_W']-pv
        return p['usable_Wh']/net if net>0 else None
    summary=dict(nominal_energy_Wh=p['energy_Wh'],usable_energy_Wh=p['usable_Wh'],
                 no_load_speed_m_s=math.pi*(2*p['radius_m'])*motor['free_speed_rpm']/60,
                 full_time_nominal_motion_dark_h=depletion(1,0),quarter_duty_dark_h=depletion(d,0),quarter_duty_500Wm2_h=depletion(d,solar(G)),
                 sixhour_dark_duty=mission_duty_limit(p['usable_Wh'],h,p['auxiliary_W'],p['drive_W'],0)['max_drive_duty_fraction'],
                 sixhour_500Wm2_duty=mission_duty_limit(p['usable_Wh'],h,p['auxiliary_W'],p['drive_W'],solar(G))['max_drive_duty_fraction'],
                 recharge_full_sun_energy_lower_bound_h=p['energy_Wh']/solar(reference_G),
                 zero_miss_trials_for_upper5pct=math.ceil(math.log(alpha)/math.log(1-confidence['upper_miss_probability_target'])))
    (out/'analytical_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    provenance=dict(evidence_status='Analytical scenarios; no experimental observations',baseline_snapshot=b,scenario_registry_snapshot=s,
                    derived_parameters=p,input_snapshot_hashes={k:hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest() for k,v in [('baseline',b),('scenarios',s)]},
                    source_hashes={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in ['build_engineering_analysis.py','engineering_models.py']},
                    datasets={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in files})
    (out/'analysis_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,default=BASE/'new_design_baseline.json')
    parser.add_argument('--scenarios',type=Path,default=BASE/'engineering_scenarios.json')
    parser.add_argument('--output',type=Path,default=BASE/'analysis')
    args=parser.parse_args()
    baseline=json.loads(args.baseline.read_text(encoding='utf-8-sig'))
    scenarios=json.loads(args.scenarios.read_text(encoding='utf-8-sig'))
    print(json.dumps(generate(baseline,scenarios,args.output),indent=2))
    print('Regenerated all 16 CSVs and input/output provenance.')
