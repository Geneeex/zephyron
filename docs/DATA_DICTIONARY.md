# Analytical CSV data dictionary

Every CSV in `research/analysis/` is a deterministic analytical scenario, selected parameter record, or calculation from a stated component specification. None contains acquired sensor or rover test measurements. Columns and row counts below are read from the committed files.

Files are UTF-8, comma-separated, with one header row and no index column. Decimal points use `.`. Units are explicit in column names or the `unit` column. Fractions and relative standard uncertainties are dimensionless; `pct` is percent. `cps` and `counts_s` mean counts per second. Booleans are written as `True`/`False`. Numeric calculations retain Python floating-point output rather than publication rounding.

**Blank values are meaningful:** `runtime_h` is blank for nonpositive modeled net depletion; `max_drive_duty_fraction` is blank when even stationary operation is infeasible. Neither blank means zero, infinity, or a missing physical observation. Read the corresponding state column.

Input grids and component choices are defined in `research/engineering_scenarios.json`; selected geometry, mass and operating assumptions are in `research/new_design_baseline.json`. [CALCULATIONS.md](CALCULATIONS.md) defines the equations and scope.

## `arm_torque_budget.csv`

7 data rows; 6 columns.

| Column | Meaning |
|---|---|
| `grasp_payload_scenario_kg` | Selected grasped mass; not an arm payload rating. |
| `shoulder_gravity_torque_Nm` | Shoulder gravity moment for a horizontal arm. |
| `elbow_gravity_torque_Nm` | Elbow gravity moment for a horizontal arm. |
| `shoulder_with_design_allowance_Nm` | Shoulder gravity moment multiplied by the selected factor of two. |
| `elbow_with_design_allowance_Nm` | Elbow gravity moment multiplied by the selected factor of two. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `arm_unconstrained_workspace.csv`

722 data rows; 5 columns.

| Column | Meaning |
|---|---|
| `boundary` | Inner or outer unconstrained two-link reach circle. |
| `angle_rad` | Angular coordinate of the workspace boundary. |
| `forward_m` | Forward coordinate relative to the starting pose or arm shoulder. |
| `vertical_m` | Vertical coordinate relative to the arm shoulder. |
| `status` | Explicit geometric/evidence state, not a validated reachability claim. |

## `baseline_parameters.csv`

21 data rows; 5 columns.

| Column | Meaning |
|---|---|
| `parameter` | Named design parameter. |
| `value` | Numerical selected or derived value. |
| `unit` | Units for this parameter row. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |
| `source` | Input registry file used for the parameter. |

## `energy_duty_sweep.csv`

404 data rows; 8 columns.

| Column | Meaning |
|---|---|
| `drive_duty_fraction` | Fraction of time assigned the incremental driving load (0 to 1). |
| `irradiance_W_m2` | Selected incident irradiance. |
| `load_W` | Constant auxiliary load plus duty-weighted incremental driving load. |
| `solar_W` | PV nameplate scaled by irradiance and combined mission derating. |
| `net_battery_power_W` | Battery depletion power: load minus available solar power. |
| `runtime_h` | Usable energy divided by positive depletion power; blank when net depletion is nonpositive. |
| `state` | Scenario feasibility/depletion state. It is part of the result, not an optional annotation. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `energy_mission_duty_limits.csv`

15 data rows; 8 columns.

| Column | Meaning |
|---|---|
| `mission_h` | Requested mission duration. |
| `irradiance_W_m2` | Selected incident irradiance. |
| `max_drive_duty_fraction` | Maximum feasible driving fraction capped at 1; blank if stationary demand already exceeds budget. |
| `stationary_feasible` | Boolean feasibility of zero incremental driving under this constant scenario. |
| `state` | Scenario feasibility/depletion state. It is part of the result, not an optional annotation. |
| `available_drive_power_W` | Usable energy per mission hour plus solar minus auxiliary demand; may be negative. |
| `equation` | Model expression and infeasibility rule retained with the result. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `gm_background_scenario.csv`

60 data rows; 7 columns.

| Column | Meaning |
|---|---|
| `signal_rate_cps` | Expected net signal count rate above background. |
| `background_rate_cps` | Expected independent background count rate. |
| `sample_duration_s` | Integration duration for signal plus background. |
| `background_duration_s` | Integration duration for the independent background measurement. |
| `net_standard_uncertainty_cps` | Poisson standard uncertainty of the background-subtracted expected rate. |
| `net_relative_standard_uncertainty` | Net-rate standard uncertainty divided by expected signal rate. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `gm_counting_time.csv`

40 data rows; 6 columns.

| Column | Meaning |
|---|---|
| `rate_counts_s` | Selected expected Poisson count rate. |
| `integration_s` | Selected counting duration. |
| `expected_counts` | Expected rate multiplied by integration time; these are not recorded counts. |
| `relative_poisson_standard_uncertainty` | One divided by square root of expected counts. |
| `rate_standard_uncertainty_counts_s` | Square root of expected counts divided by duration. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `grade_load.csv`

21 data rows; 12 columns.

| Column | Meaning |
|---|---|
| `grade_deg` | Selected uphill slope angle. |
| `total_mass_kg` | Gross mass budget used in the scenario. |
| `rolling_coefficient` | Assumed dimensionless rolling-resistance coefficient. |
| `tractive_force_N` | Total force needed for steady grade ascent under the simplified model. |
| `torque_each_Nm` | Wheel torque assuming equal load sharing among four wheels. |
| `approx_current_each_A` | Linear motor torque-current estimate at the selected voltage. |
| `full_nominal_voltage_no_load_curve_rpm` | Linear speed-torque curve estimate at full nominal voltage; not the commanded rover speed. |
| `minimum_friction_coefficient` | Ideal minimum traction coefficient: tan(grade) plus rolling coefficient. |
| `continuous_gearbox_torque_limit_Nm` | Selected component continuous gearbox torque guidance after unit conversion. |
| `continuous_current_guidance_A` | Selected continuous-current fraction multiplied by extrapolated stall current. |
| `mechanical_power_at_command_speed_W` | Tractive force multiplied by the selected command speed. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `odometry_mismatch_paths.csv`

404 data rows; 6 columns.

| Column | Meaning |
|---|---|
| `diameter_mismatch_fraction` | Fractional effective wheel-diameter/radius mismatch between sides. |
| `center_path_length_m` | Ideal traveled center path distance for equal wheel angular speeds. |
| `forward_m` | Forward coordinate relative to the starting pose or arm shoulder. |
| `lateral_error_m` | Cross-track displacement from ideal differential-drive curvature. |
| `heading_error_deg` | Heading change caused solely by the mismatch scenario. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `pv_irradiance_temperature.csv`

204 data rows; 5 columns.

| Column | Meaning |
|---|---|
| `irradiance_W_m2` | Selected incident irradiance. |
| `cell_temperature_C` | Assumed PV cell temperature, not ambient temperature. |
| `panel_dc_W` | Irradiance- and temperature-scaled panel DC power. |
| `after_controller_W` | Panel power times a separate assumed 0.9 controller efficiency; not combined again with mission derating. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `solar_recharge_lower_bound.csv`

5 data rows; 4 columns.

| Column | Meaning |
|---|---|
| `irradiance_W_m2` | Selected incident irradiance. |
| `available_solar_W` | Constant modeled mission solar power available with the load off. |
| `recharge_label_energy_h` | Label energy divided by available solar power; energy-only lower bound without constant-voltage tail. |
| `scope` | Explicit evidence/model limitation attached to the row. |

## `tds_fullscale_spec.csv`

9 data rows; 5 columns.

| Column | Meaning |
|---|---|
| `indicated_ppm` | Selected TDS indication. |
| `manufacturer_absolute_spec_limit_ppm` | Full scale times the stated full-scale fraction; not a standard uncertainty. |
| `equivalent_relative_limit_pct` | Absolute specification limit divided by indication, expressed as a percentage. |
| `not_a_standard_uncertainty` | Reminder that the manufacturer specification is a limit, not a probability distribution. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `tds_partial_uncertainty.csv`

4 data rows; 8 columns.

| Column | Meaning |
|---|---|
| `voltage_V` | Selected probe-output voltage before temperature compensation. |
| `temperature_C` | Selected sample temperature for the vendor conversion. |
| `tds_estimate_ppm` | Vendor polynomial evaluated at compensated voltage. |
| `ADC_quantization_standard_uncertainty_ppm` | Derivative-propagated uniform ADC quantization contribution. |
| `temperature_standard_uncertainty_C` | Assumed standard uncertainty of the separate temperature input. |
| `temperature_contribution_ppm` | Derivative-propagated temperature contribution to the converted result. |
| `combined_partial_uncertainty_ppm` | Root-sum-square of ADC and temperature terms; excludes other calibration and matrix effects. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `vision_latency_scenarios.csv`

48 data rows; 15 columns.

| Column | Meaning |
|---|---|
| `capture_fps` | Selected source capture rate; not delivered or processed rate. |
| `frame_size_bytes_assumed` | Assumed compressed payload size per frame. |
| `link_Mbps` | Ideal payload link throughput in decimal megabits per second. |
| `inference_ms` | Assumed external-host inference duration. |
| `acquisition_wait_mean_ms` | Half a capture period for a random event phase. |
| `transfer_ms` | Eight times payload bytes divided by ideal link throughput, converted to milliseconds. |
| `other_pipeline_ms` | Selected decode, postprocessing and display time. |
| `total_event_to_display_ms` | Mean acquisition wait plus transfer, inference and other pipeline time for an accepted frame with no prior queue. |
| `partial_capture_transfer_inference_upper_bound_fps` | Minimum of capture, payload transfer and inference rates; other stages and contention are excluded. |
| `offered_stream_Mbps` | Capture rate times frame payload bits per second. |
| `network_can_carry_all_captured_frames_ideal` | Boolean comparison of ideal offered payload traffic with link throughput. |
| `network_minimum_throttle_or_discard_fraction` | Minimum fraction to throttle/discard to fit ideal payload capacity. |
| `network_state` | Whether ideal payload capacity is sufficient or throttling/discard is required. |
| `travel_during_latency_m` | Command speed times modeled event-to-display latency. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `wheel_diameter_speed.csv`

41 data rows; 5 columns.

| Column | Meaning |
|---|---|
| `diameter_mm` | Wheel diameter sensitivity-grid value. |
| `no_load_rpm` | Selected motor no-load wheel speed. |
| `no_load_speed_m_s` | Circumference times no-load revolutions per second; not achievable loaded speed. |
| `at_commanded_speed_required_rpm` | Wheel revolutions per minute needed for the selected command speed. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## `zero_miss_confidence.csv`

200 data rows; 5 columns.

| Column | Meaning |
|---|---|
| `independent_positive_trials` | Hypothetical number of independent positive trials for confidence planning. |
| `observed_misses` | Zero-miss condition of this planning scenario; not an experimental observation. |
| `one_sided_confidence` | Selected one-sided confidence level (0.95). |
| `upper_miss_probability` | Binomial one-sided upper bound under the zero-miss condition. |
| `evidence` | Row-level evidence label identifying a model or calculation and its important exclusions. |

## JSON companions

`analytical_summary.json` records derived headline values in their named units: 72 Wh nominal label energy, 57.6 Wh assumed usable energy, no-load speed, selected finite-depletion runtimes, six-hour drive fractions, the energy-only recharge bound, and the planned number of zero-miss trials. These retain full numerical precision.

`analysis_provenance.json` stores the baseline and scenario snapshots, derived parameters, hashes of the serialized input snapshots, generator-source hashes, and SHA-256 hashes of all 16 CSVs. It describes the original analytical generation; the public verification report additionally hashes the current public source files.

`research/figures/engineering_figure_captions.json` and `.csv` connect nine analytical figure identifiers to titles, explanatory captions, source keys and input CSV filenames. JSON also records figure dimensions, format names and nominal output resolution. The figure files are scenarios rather than measured graphs.
