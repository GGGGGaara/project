# Temporal Admission and Execution Limits in Dynamic Narrow-Road Passage

## Abstract
Temporary openings in a narrow passage do not necessarily leave enough time or space for a vehicle to finish crossing or stop. This study examines that distinction through two complementary synthetic evaluations: a resource-window admission model and a separate vehicle-execution diagnostic. The admission model jointly schedules two conflict regions and a temporarily available refuge, with fixed temporal inflation of predicted occupation. At a timing-error standard deviation of 1.0 s, joint inflated scheduling reduces realized resource-window exposure from 22.6% to 6.1% over 1,000 paired scenarios, while mean planned exit time increases from 13.51 to 15.27 s. A subsequent planar battery-electric-vehicle simulation separates scripted obstacle motion, delayed and biased observations, constant-velocity prediction, and actuator execution. Across 24 matched constructed conditions, frozen prediction, prediction refresh restricted to initial/holding decisions, and updates during forward motion complete 8, 10, and 22 cases without sampled contact, respectively. The two retained failures expose a gap between nominal path prediction and the executable braking response. These evaluations establish reproducible mechanisms and counterexamples, rather than an integrated safety-certified planner. Safe-interval planning, kinodynamic interval search, and fail-safe trajectory research already address central ingredients; independent algorithmic novelty and superiority to published planners remain unestablished.

Keywords: narrow roads; temporal admission; safe intervals; actuator response; delayed observation; reproducible simulation

## 1. Introduction
A vehicle facing a temporarily occupied narrow road must decide whether to wait, enter, or stop after entering. A clear entrance alone does not establish that downstream passage or intermediate waiting will remain possible. For a vehicle with nonzero speed, a later command to stop must also account for the distance traveled while the controller changes its acceleration request and the actuators establish braking force. Motion planning and feedback execution therefore need compatible assumptions [1].

Township markets motivate the study through temporary roadside occupation and changing crossing activity. The experiments are synthetic abstractions: they contain neither measured market traffic nor demographic participant models. The question addressed is whether temporal resource checks and prediction updates resolve specific failure mechanisms, and which execution failures remain after those checks.

The study has three empirical objectives. First, isolate the effect of temporal inflation and refuge availability in a small admission problem. Second, document a vehicle simulation in which the world, observations, predictions, and executed trajectory are explicitly separated. Third, retain and diagnose cases in which updating a nominal prediction still fails. The two evaluations use different scenes and outcome definitions; the admission scheduler is not connected to the planar controller. Their results must therefore be interpreted separately.

The contribution is a reproducible diagnostic study with explicit modeling limits, internal ablations, and traceable failure evidence. It does not establish a new viability algorithm, a collision-avoidance guarantee, or superiority over published safe planning methods.

## 2. Related work and research positioning
Safe Interval Path Planning (SIPP) represents configurations together with intervals during which they are free of dynamic obstacles [2]. Waiting and searching for early arrival are established parts of this formulation. The present two-stage resource scheduler has closely related temporal structure, although it is a small direct enumeration rather than a SIPP graph-search implementation. Temporal occupancy checks and waiting-resource constraints alone are insufficient evidence of a new planning principle.

Ali and Yakovlev explicitly address the inability to stop instantaneously through Safe Interval Path Planning with Kinodynamic Constraints [3]. Consequently, adding acceleration or stopping duration to an interval model does not by itself establish originality. Magdici and Althoff maintain an emergency maneuver under enclosing occupancy predictions [4]. This provides a more demanding reference point than merely issuing a braking command after a nominal conflict is predicted.

The distinction between simplified planning dynamics and execution dynamics is also central to FaSTrack, which constructs a controller and tracking-error bound under its model assumptions [5]. The fixed position/heading offset used in the present predictor is not such a bound. Narrow-road scene modeling by Zhang et al. identifies candidate meeting gaps and optimizes trajectories [6]; the retrieved source is an arXiv preprint and is cited as such. Fujinami and Raksincharoensak jointly consider risk-predictive speed and lateral distance near occlusions [7]. Their work further limits novelty claims based on anticipatory slowing in narrow roads.

These sources motivate the evaluation and identify missing capabilities. None is implemented as a performance baseline here. In particular, the experiments do not test geometric meeting-gap selection, SIPP-IP search, reachable occupancy enclosure, or a certified backup controller.

## 3. Temporal admission model
### 3.1 Resources, assumptions, and timing
The abstract corridor contains an entrance B0, an optional intermediate refuge B1, and an exit B2. Conflict resources G1 and G2 lie on successive stages. Each stage takes T = 6 s, corresponding to an assumed 18 m traveled at 3 m/s. A stage departing at t uses its conflict resource over C(t) = [t + 2.2, t + 3.8). Refuge residence in a staged plan uses H(t0,t1) = [t0 + T - 0.2, t1 + 0.2), where t0 is entry and t1 is second-stage departure.

All resource intervals in this section are half-open. Two intervals [a,b) and [c,d) overlap precisely when a < d and b > c. Endpoint equality is therefore permitted in this scheduling abstraction, consistent with the strict inequalities in the supplied implementation. It does not represent permissible physical contact. A direct traversal has t1 = t0 + T and does not occupy B1; a staged traversal requires t1 > t0 + T.

### 3.2 Forecast inflation and admission
For each resource r, the planner receives event intervals [a_hat,b_hat). Inflation by delta produces their union O_hat_r(delta). The main experiment uses delta = 1.25 s. The optimization is:

EQ: minimize t1 + T over permitted grid times t0 and t1. (1)

EQ: C(t0) ∩ O_hat_G1(delta) = ∅; C(t1) ∩ O_hat_G2(delta) = ∅. (2)

EQ: Staged plan: H(t0,t1) ∩ O_hat_B1(delta) = ∅. (3)

The symbol ∩ denotes set intersection. Entry times range from 0 to 50 s on a 0.5 s grid; intermediate holding is limited to 30 s, with the implementation's absolute second-departure bound of 84 s. The joint strategies enumerate entry times and select the earliest feasible exit. No continuous trajectory, braking process, or geometric access to the refuge is computed.

Conditional non-overlap follows immediately: if every used resource's realized occupation is contained in its inflated forecast, disjointness from the inflated forecast implies disjointness from realized occupation. This is a conditional set argument, not a safety theorem for a vehicle. Gaussian timing error is unbounded, and the test assumes correct event existence and duration. Delta is an experimental parameter, not a calibrated confidence level.

### 3.3 Scene generation and internal comparisons
Two independent potential events are generated per resource. G1 starts are uniform on (1,13) and (17,33) s; G2 starts on (5,22) and (24,42) s. Each is present with probability 0.82 and has uniform duration 2 to 5.5 s. Refuge starts are uniform on (4,23) and (25,38) s; event probability is 0.65 and duration is uniform from 2 to 7 s. These distributions are design choices. For each existing event, one Gaussian shift with standard deviation sigma is added to both endpoints, preserving duration and event identity.

The main script generates 1,000 scenes for each sigma in {0.4, 1.0, 1.6} s using NumPy seed 20261102. Methods within a noise level share the scene and forecast. The random generator continues between noise levels, so actual scenes differ across sigma; cross-sigma changes are not a purely controlled noise intervention.

| Code policy | Exact comparison rule |
| --- | --- |
| reactive | Weak heuristic inspecting actual G1 occupation over the next 0.5 s; all original scenes yield immediate entry |
| local_prediction | First feasible entry after checking both gate forecasts, without checking refuge occupation |
| joint_nominal | Earliest exit with both gate checks and refuge occupation checks; delta = 0 |
| robust_no_refuge | Earliest exit with inflated gate windows; may use B1 but ignores its occupation |
| joint_robust | Earliest exit with inflated gate and refuge windows; delta = 1.25 s |

The code name robust_no_refuge means “without refuge-occupation checking,” not “without a refuge.” The reactive heuristic is not an operational reactive vehicle planner, and local_prediction is not restricted to G1. Primary interpretation rests on the joint and refuge-check ablations.

## 4. Vehicle execution and observation model
### 4.1 Geometry and execution state
The separate execution study uses a 40 m planar path y(x) = 0.25 sin²(pi x / 40), sampled for arc-length lookup. The road boundary is y = ±3 m. Rectangular stalls occupy x from 13 to 24 m and y from 1.6 to 3 m or -3 to -1.6 m. The ego body extends from -1 to 3.5 m longitudinally and ±0.9 m laterally relative to its reference point. A circular crossing object of radius 0.3 m moves at x = 20 m. Collision evaluation uses the oriented rectangular body and the object's circle, with static-obstacle and road-boundary checks.

The state includes path progress, position, heading, speed, steering angle, previous acceleration request, motor torque, friction-brake capacity, and an energy-based state-of-charge variable. The generic parameters include mass 1900 kg, equivalent longitudinal mass 1976 kg, wheel radius 0.31 m, gear ratio 9, wheelbase 2.7 m, motor response constant 0.04 s, and motor slew limit 2000 N m/s. The maps are stipulated research assumptions, without vehicle calibration.

The delivered friction force is brake capacity multiplied by tanh(v/0.03). With motor torque Tm, brake capacity Fb, ratio i, wheel radius rw, equivalent mass me, and resistance R(v), the force law and brake update are:

EQ: me a = clip(i Tm/rw - Fb tanh(v/0.03), -mu m g, mu m g) - R(v). (4)

EQ: Fb(k+1) = Fb(k) + (1 - exp(-h/tau_b)) [clip(ub,0,7m) - Fb(k)]. (5)

Here ub is brake-capacity command, h is execution step, mu = 0.85, and the bound 7m corresponds to a stipulated 7 m/s² force capacity. Velocity is constrained to be nonnegative, with within-step stopping integration when a frozen-force step would cross zero. Motor torque is limited by synthetic torque, power, temperature, state-of-charge, and low-speed regeneration maps. Friction braking can compensate for limited regeneration; regeneration loss alone does not imply inability to stop.

Reference trajectories are seventh-order position polynomials. The search imposes speed, acceleration, and jerk bounds on 301 sampled reference points; for the stopping baseline, acceleration and jerk magnitudes are limited to 1.1 m/s² and 1.5 m/s³. A failed search establishes failure of the specified reference family and duration search, not physical infeasibility. Position/speed feedback and nominal actuator inversion produce motor/brake commands. The acceleration request changes by at most 2 m/s³. Steering follows a look-ahead rule, with angle magnitude limited to 0.45 rad and rate magnitude to 0.5 rad/s. Execution uses a midpoint heading update and 0.02 s steps.

### 4.2 Causal observations and nominal risk prediction
Every 0.5 s, an observation received at t measures the world at max(0,t-d). Position and speed biases are added at that measurement time. Constant-velocity extrapolation first compensates for observation age, then predicts forward. Only received snapshots enter the predictor; future scripted speed changes are unavailable. Ego pose is assumed known exactly.

The risk check samples the nominal reference every 0.2 s with a 0.25 m clearance threshold. It adds the current progress, lateral, and heading offsets to future reference poses; it does not propagate actuator state, future tracking deviations, or obstacle uncertainty sets. Thus the execution model is more detailed than the risk model. Discrete collision checks and fixed margins provide no continuous-time guarantee.

### 4.3 Policies and constructed conditions
All three policies receive the same world/sensor/vehicle condition. Frozen prediction retains the initial forecast. Refresh-at-hold uses updated predictions for initial admission and decisions while holding, but not while progressing. Rolling also rechecks in forward motion every 0.5 s, attempts to stop near x = 15.4 m when necessary, waits, and checks whether to resume. It does not reoptimize during stopping or emergency braking. If ordinary stop-reference generation fails while moving, it requests braking through the existing controller under the label emergency_unverified.

There are four scripted motions: constant 1 m/s; acceleration from 1 to 2 m/s at 9 s; acceleration from 1 to 3 m/s at 12 s; and a pause from 13.5 to 18 s at y = -0.5 m. Instantaneous speed changes are stress-test inputs rather than physiological pedestrian models. Three sensors use (delay, position bias, speed bias) of (0,0,0), (0.4 s,+0.1 m,+0.12 m/s), and (0.4 s,-0.1 m,-0.12 m/s). Two vehicle conditions use (25 °C,0.18 s brake constant) or (-5 °C,0.35 s). Initial state of charge is 0.55. The factorial design contains 24 matched conditions per policy, or 72 executions.

## 5. Results
### 5.1 Resource-window exposure
Table 1 reports the fraction of scheduled resource uses overlapping realized resource occupation. This is not a vehicle-collision metric.

| sigma (s) | reactive | local_prediction | joint_nominal | robust_no_refuge | joint_robust |
| --- | --- | --- | --- | --- | --- |
| 0.4 | 39.2% | 18.2% | 14.4% | 9.6% | 0.0% |
| 1.0 | 36.4% | 24.8% | 22.6% | 13.3% | 6.1% |
| 1.6 | 36.5% | 32.1% | 30.3% | 23.5% | 16.8% |

At sigma = 1.0 s, joint inflation changes exposure by -16.5 percentage points relative to joint_nominal; the stored 5,000-resample episode-paired bootstrap interval is [-19.0,-14.1] points. Mean planned exit increases by 1.759 s, from 13.5135 to 15.2725 s. Wilson intervals for the two exposure proportions are 20.1–25.3% and 4.8–7.8%. These quantify variation under the stipulated generator. Planned exit is not measured travel time or multi-vehicle throughput.

FIGURE: ../STV_ED_reproducible_pilot_bundle/rural_narrow_road_research/results/pilot_exposure.png | Figure 1. Original resource-exposure comparison across noise levels. Bars summarize synthetic schedules, not physical collisions; each method has 1,000 cases at each noise level.

In the separate padding sensitivity set, exposure changes from 23.3% at delta = 0 to 6.4% at 1.25 s and 1.3% at 2 s; mean planned exit changes from 13.47 to 15.19 and 16.74 s. The 6.4% sensitivity result and 6.1% main result come from different samples and must not be interchanged.

The supplied evaluator classifies no_plan as exposure. No such records occur in the original 15,000 policy evaluations, so this defect does not alter Table 1. Future extensions must distinguish refusal to enter, timeout, algorithm failure, and realized overlap. Furthermore, all generated occupations eventually end; a direct entry at 39.5 s avoids every realized gate window under the generator's support. This analytical late-wait comparator finishes at 51.5 s and illustrates that the abstract problem trades earlier entry against exposure, rather than demonstrating that eventual passage is difficult.

### 5.2 Execution results and matched comparisons
The stopping baseline finds references and completes two stops in 36 of 48 stipulated inputs; maximum absolute stop-position error among completed cases is 0.0072913 m. Twelve inputs starting at 4 m/s with a first target 10 m away fail the reference search. These are synthetic controller results, without empirical millimeter-accuracy validation. The separate ideal-prediction planar stage contains 60 runs; stop_wait and candidate each complete all 15 conditions without sampled collision. This stage is distinct from the delayed-observation experiment.

| Policy | Completed without sampled contact | Collision termination | Timeout/no progress | Cases invoking emergency_unverified |
| --- | --- | --- | --- | --- |
| frozen | 8/24 | 16/24 | 0/24 | 0/24 |
| refresh_hold | 10/24 | 14/24 | 0/24 | 0/24 |
| rolling | 22/24 | 2/24 | 0/24 | 10/24 |

Completion requires reaching the endpoint and stopping within the implemented terminal tolerances, with no sampled body/object contact, stall collision, or road departure. Collisions terminate execution, and failed cases have null finish times. These counts characterize a constructed test suite, not a sample of real traffic; no population collision probability or random-traffic significance claim is inferred.

FIGURE: manuscript_assets/execution_comparison.png | Figure 2. Outcomes in the 24 matched constructed conditions per policy. Collision counts include sampled contact checks; zero timeouts does not establish liveness outside this suite.

Means over each policy's own successful cases are 30.71, 30.83, and 33.33 s, but the successful subsets differ. Those means cannot rank efficiency across the common task set. On the eight conditions completed by all three policies, paired reanalysis gives 30.7100, 30.1475, and 30.1475 s, respectively. This subset primarily tests conditions already handled by the weakest policy and does not establish efficiency on the remaining conditions. A 90 s timeout-budget score, assigning every failed case the common execution horizon, gives 70.24, 65.35, and 38.06 s. It is a penalty-based diagnostic, not actual completion time; the 90 s choice affects its magnitude. The machine-readable supplement supplies exact values and case membership.

### 5.3 Retained failure and execution mismatch
Both rolling failures combine the late speed increase with the delayed negative-bias sensor; one uses each vehicle condition. At 12.50 s, the first emergency attempt occurs at speed 2.8175 m/s, positive acceleration 0.1703 m/s², motor torque 19.40 N m, and almost zero established friction-brake capacity. The front-to-crossing-strip longitudinal gap is 2.3314 m. Ordinary stop-reference search returns reference_not_found, and sampled contact occurs at 13.42 s in both cases.

FIGURE: bev/results_crossing_uncertain/retained_failure.png | Figure 3. Retained late-acceleration collision from the supplied execution traces. Speed, acceleration, and delayed-observation estimates are shown; torque and brake-state values are reported in the text. This is not a proof of unavoidable collision.

The constant-deceleration expression v²/(2 × 2.5) gives 1.5876 m, but omits request slew, force buildup, the positive torque state, and crossing geometry. Comparing it with 2.3314 m cannot establish either preventability or inevitability. Equal failures under both vehicle conditions also do not identify cold temperature or regeneration as their cause. What is demonstrated is that this particular nominal predictor plus reactive, unverified fallback fails in these conditions.

## 6. Verification and reproducibility
The original resource experiment stores 15,000 policy records, 15 aggregate rows, nine paired-bootstrap rows, and six padding-sensitivity rows. The original review also includes independently enumerated small scheduling checks. Supplied scripts, seeds, forecasts, outputs, and previous review reports remain available; historical review text describes its own earlier execution, not a fresh guarantee.

The vehicle suite stores each episode's trajectory, received observations, decision events, parameters, and source hashes. Causality tests check that future world changes cannot change past observations, delayed snapshots do not reveal unseen changes, constant-velocity delay compensation is consistent, pause integration is continuous, bias is explicit, and an event on an observation boundary is not delayed by floating-point accumulation. The verifier reconstructs world positions, observation bias, forecast selection, and sampled collision labels for all 72 traces. Four selected cases were checked at 0.01 s instead of 0.02 s: statuses agree, end-time differences do not exceed 0.02 s, and minimum-clearance changes do not exceed approximately 0.029 m. This is a local refinement check, not convergence of every trajectory or continuous collision verification.

The supplementary audit uses only named top-level datasets, excluding obsolete diagnostic subdirectories. It checks hashes before trusting stored outputs, reaggregates reported counts, and records matched-condition membership. Reproduction commands are in the repository's manuscript supplement.

## 7. Discussion and limitations
The admission experiment shows a reduction in overlap under known-event Gaussian timing shifts. The execution experiment shows that prediction refresh during progression can handle more scripted changes than frozen prediction, while still failing twice. These are complementary observations, not evidence that the admission scheduler has been validated in closed loop: its refuge resource is not connected to the planar stopping location, and no integrated transfer is evaluated.

External validity is limited by synthetic schedules, a single crossing object, fixed lateral path, exact ego localization, deterministic sensor biases, and absent interaction responses. There are no missed detections, multiple intent hypotheses, road gradients, tire slip, ABS dynamics, vehicle calibration, measured traffic frequencies, or empirical battery/brake maps. Temperature and response constant change together in the constructed condition, so their individual effects are confounded. Reference feasibility is checked by finite sampling and bounded search, and reference transitions do not establish continuous acceleration or jerk compatibility with actual actuator state.

The next falsifiable hypothesis is that admission or speed restriction based on the current speed, torque, brake buildup, and observation age can retain a feasible stopping action more consistently than fixed speed or fixed distance/time margins. Testing it requires a defined backup policy, explicit uncertainty assumptions, matching all baselines to the same execution model, and held-out conditions. SIPP-IP [3], fail-safe planning [4], FaSTrack [5], and risk-predictive narrow-road planning [7] must inform the comparison; a state-dependent stopping margin alone is not a verified novelty claim.

Future evaluation should report contact, progress failure, matched completion cost, stopping position, and braking demand together. It should include initially occupied and continuously replenished scenes, multiple objects, extended observation delays, and continuous or conservatively bounded collision checking. A proof of recursive safety additionally needs a safe terminal condition and evidence that a valid backup survives each action and update; such a proof is absent here.

## 8. Conclusion
Joint temporal inflation and refuge-occupation checks reduce resource-window exposure in the stipulated admission generator at the cost of later planned exit. Separately, updates during forward vehicle motion improve constructed-suite completion from 8/24 to 22/24 relative to frozen prediction, but retain two actuator-execution failures. The supported result is a reproducible separation of scheduling feasibility, nominal prediction, and executed stopping behavior. Establishing a new safe planner requires connecting these layers and validating the resulting method against appropriate published alternatives.

## References
[1] B. Paden, M. Cap, S. Z. Yong, D. Yershov, and E. Frazzoli. A Survey of Motion Planning and Control Techniques for Self-Driving Urban Vehicles. IEEE Transactions on Intelligent Vehicles, 1(1):33–55, 2016. doi:10.1109/TIV.2016.2578706. Author preprint: https://arxiv.org/abs/1604.07446.

[2] M. Phillips and M. Likhachev. SIPP: Safe Interval Path Planning for Dynamic Environments. IEEE International Conference on Robotics and Automation, pp. 5628–5635, 2011. doi:10.1109/ICRA.2011.5980306. Author full text: https://www.cs.cmu.edu/~maxim/files/sipp_icra11.pdf.

[3] Z. A. Ali and K. Yakovlev. Safe Interval Path Planning with Kinodynamic Constraints. Proceedings of the AAAI Conference on Artificial Intelligence, 37(10):12330–12337, 2023. doi:10.1609/aaai.v37i10.26453. Author preprint: https://arxiv.org/abs/2302.00776.

[4] S. Magdici and M. Althoff. Fail-safe motion planning of autonomous vehicles. IEEE 19th International Conference on Intelligent Transportation Systems, pp. 452–458, 2016. doi:10.1109/ITSC.2016.7795594. Institutional full text: https://mediatum.ub.tum.de/doc/1379704/document.pdf.

[5] S. L. Herbert, M. Chen, S. Han, S. Bansal, J. F. Fisac, and C. J. Tomlin. FaSTrack: a Modular Framework for Fast and Guaranteed Safe Motion Planning. IEEE Conference on Decision and Control, 2017. doi:10.1109/CDC.2017.8263867. Author preprint: https://arxiv.org/abs/1703.07373.

[6] Q. Zhang, J. Guang, Z. Cao, and J. Liu. Scene Modeling of Autonomous Vehicles Avoiding Stationary and Moving Vehicles on Narrow Roads. arXiv:2412.13305, 2024. Preprint; formal publication status not established here. https://arxiv.org/abs/2412.13305.

[7] Y. Fujinami and P. Raksincharoensak. Risk-predictive trajectory and speed planning method for safe autonomous driving on urban narrow roads. Mechanical Engineering Journal, 13(2):25-00380, 2026. doi:10.1299/mej.25-00380. Publisher: https://www.jstage.jst.go.jp/article/mej/13/2/13_25-00380/_article/-char/en.
