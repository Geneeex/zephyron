# Analytical models and selected design assumptions

All numbers below are selected design inputs or calculated scenarios. The prototype photographs establish component arrangement; they do not establish measured dimensions, mass, motor performance, calibration, or runtime. Component specification values are traceable through the source keys in `engineering_scenarios.json` and the repository's reference records.

## Inputs and evidence boundaries

| Quantity | Selected value | Interpretation |
|---|---:|---|
| Wheel diameter / tread | 165 / 75 mm | Design geometry |
| Wheelbase / track | 570 / 538 mm | Wheel-center spacing |
| Tire footprint | 735 × 613 mm | Derived geometry; not a measured envelope |
| Chassis length / width | 600 / 390 mm | Selected structural allocation |
| Central chassis clearance | 130 mm | Nominal central target, not uniform clearance or obstacle rating |
| Upper solar hinge height | 720 mm | Reference height, not maximum external height |
| Dry / chassis payload / gross mass | 10 / 2 / 12 kg | Mass budget; payload allocation is not a tested carrying rating |
| Battery label energy | 12 V × 6 Ah = 72 Wh | Conservative label convention, not measured delivered energy |
| Usable battery fraction | 0.80 | Assumption, giving 57.6 Wh |
| Auxiliary / incremental drive demand | 5 / 35 W | Battery-side constant scenario loads |
| PV nameplate / mission derating | 20 W / 0.75 | Selected component and combined assumed derating |
| Speed cap / rolling coefficient | 0.35 m/s / 0.04 | Control scenario and ground-contact assumption |
| Arm link lengths | 0.146 / 0.264 m | Selected kinematic geometry |
| Arm link / hand masses | 0.12 / 0.16 / 0.13 kg | Assumed masses; no weighing performed |

## Energy and mission duty

Let $d$ be the moving fraction, $G$ the irradiance in W/m², $E_u$ the usable battery energy in Wh, and $P_a,P_d$ the auxiliary and incremental driving loads in W:

$$P_{PV}=20(0.75)G/1000,\quad P_L=P_a+dP_d,\quad t=E_u/(P_L-P_{PV}).$$

The last expression only applies when net depletion power is positive. Otherwise the output is marked `conditional_energy_non_depleting` and runtime is blank. This is a constant-condition energy balance, not a claim of perpetual operation or unlimited battery capacity.

For a requested duration $t_m$, the drive budget is $B=E_u/t_m+P_{PV}-P_a$. If $B<0$, even stationary operation is infeasible and the maximum drive fraction is blank. Otherwise $d_{max}=\min(1,B/P_d)$. With the stated assumptions, continuous driving in darkness gives 1.44 h; 25% drive duty gives approximately 4.189 h without solar and 9.216 h at constant 500 W/m². A six-hour dark mission permits approximately 0.1314 drive duty. These values exclude time-varying weather and actual pack/load measurements.

`energy_trajectory` additionally audits piecewise-constant accepted battery-side charge and load. It enforces capacity saturation at every interval, records curtailed and unserved energy, and remembers any reserve breach even if later charging raises final energy. Accepted charging power must already satisfy the chosen pack and charger constraints; the function does not model or certify those devices.

The separate PV temperature model is

$$P_{DC}=\max\{0,P_{STC}(G/1000)[1+\gamma(T_c-25)]\},\quad \gamma=-0.0038\ {\rm K}^{-1}.$$

Its `after_controller_W` column uses a separate assumed 0.9 controller efficiency. That factor is not multiplied into the mission model's combined 0.75 derating. Energy-only recharge times assume the load is off and omit the constant-voltage tail and real charging constraints; 72/15 = 4.8 h is consequently a lower-bound scenario.

## Mobility, motor loading and odometry

For mass $m$, grade $\theta$, rolling coefficient $C_{rr}$, wheel radius $r$ and four equally loaded wheels:

$$F=mg(\sin\theta+C_{rr}\cos\theta),\quad \tau_{wheel}=Fr/4,\quad \mu_{min}=\tan\theta+C_{rr}.$$

At 12 kg, 165 mm diameter, $C_{rr}=0.04$, and 10°, the model gives approximately 0.51726 N·m per wheel. Mechanical power at the commanded speed is $Fv$. A linear DC-motor approximation uses $I=I_0+(I_s-I_0)\tau/\tau_s$ and $n=n_0(1-\tau/\tau_s)$. Stall torque is converted from kgf·cm using 0.0980665 N·m per kgf·cm. The motor is the selected Pololu 4755 scenario, not a confirmed installed part.

These relations omit starting transients, terrain sinkage, turning scrub, motor/driver thermal behavior and unequal load sharing. A torque curve or gearbox limit alone does not establish feasible climbing. The full-voltage speed column must not be interpreted as actual controlled rover speed.

Wheel speed follows $v=\pi Dn/60$. For ideal differential travel with fractional effective radius mismatch $\epsilon$ and track $b$, $\kappa=\epsilon/[b(1+\epsilon/2)]$, heading $\psi=\kappa s$, forward distance $x=\sin(\kappa s)/\kappa$, and lateral error $y=[1-\cos(\kappa s)]/\kappa$. At zero mismatch the straight-line limits are used. This comparison holds equal wheel angular velocity and ignores slip.

## Manipulator geometry and gravity loading

The two-link unconstrained reach lies between $|L_2-L_1|$ and $L_1+L_2$ (0.118 and 0.410 m). Circular boundaries are geometric only; joint limits, self-collision, rover contact and gripper geometry reduce attainable workspace.

For a horizontal arm with uniform link masses $m_1,m_2$, hand mass $m_h$ and grasped mass $m_p$:

$$\tau_s=g[m_1L_1/2+m_2(L_1+L_2/2)+(m_h+m_p)(L_1+L_2)],$$
$$\tau_e=g[m_2L_2/2+(m_h+m_p)L_2].$$

The design allowance multiplies these gravity torques by 2. It is a selected margin, not a dynamic simulation, actuator verification, or payload rating. The chassis 2 kg payload budget and the arm grasp scenarios are distinct quantities.

## Sensor uncertainty scenarios

For expected Poisson count rate $r$ and integration time $t$, expected count is $rt$, rate standard uncertainty is $\sqrt{rt}/t$, and relative uncertainty is $1/\sqrt{rt}$. With independently counted background rate $b$ over duration $t_b$, the net-rate standard uncertainty is $\sqrt{(r+b)/t+b/t_b}$. These tables exclude detector dead time, response calibration, spectral response and non-Poisson effects; counts cannot be converted to dose without appropriate calibration.

For the selected SEN0244 TDS specification, 10% of a 1000 ppm full scale gives an absolute specification limit of 100 ppm. Its equivalent reading-relative percentage is $100(100/c)$ for indication $c$ in ppm. This manufacturer limit is not a probabilistic standard uncertainty.

The vendor conversion scenario uses compensated voltage $V_c=V/[1+\alpha(T-25)]$ with $\alpha=0.02/°C$ and $c=0.5(133.42V_c^3-255.86V_c^2+857.39V_c)$. The partial uncertainty combines the voltage-quantization derivative contribution and temperature derivative contribution by root-sum-square. ADC voltage step is $V_{ref}/2^N$ and its uniform-quantization standard uncertainty is that step divided by $\sqrt{12}$. Selected inputs are 5 V, 10 bits and 0.5°C temperature standard uncertainty. Probe calibration, water matrix, drift and voltage-reference error are excluded; the result is not a complete uncertainty budget or a water-quality certification.

## Distributed vision and evidence planning

For capture rate $f$, frame size $S$ bytes, ideal payload link rate $B$ Mbit/s, inference time $t_i$ and other processing $t_o$:

$$t_{event}=1/(2f)+8S/(10^6B)+t_i+t_o.$$

The selected frame size is 40,000 bytes and other processing totals 50 ms. The 5 fps, 2 Mbit/s, 50 ms inference scenario gives 360 ms event-to-display delay and 0.126 m travel at 0.35 m/s. This is for an accepted frame with no prior queue, jitter, retransmission or human reaction. The partial throughput bound is $\min(f,10^6B/(8S),1/t_i)$. Offered traffic is $8Sf/10^6$ Mbit/s; overload requires throttling or discarding. Capture rate is not delivered frame rate.

For zero observed misses in $n$ independent positive trials, the one-sided binomial upper miss-probability bound is $1-\alpha^{1/n}$, with $\alpha=0.05$ for 95% confidence. Fifty-nine trials are needed for the bound to fall below 5%. The table is a sample-size planning calculation; no such trials are claimed to have been performed.

The executable ML primitives implement IoU, threshold matching, precision/recall/direct-count $F_1=2TP/(2TP+FP+FN)$, bounded frame-age admission, and reproducible dependency-group partitioning. Empty denominators remain undefined; a missed object can produce $F_1=0$. They do not train or run the proposed MobileNetV3/SSDLite or YOLO comparators. See the manuscript method text and ML README for the planned experimental protocol.
