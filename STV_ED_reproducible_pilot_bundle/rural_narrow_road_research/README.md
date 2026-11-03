# STV-ED preliminary research project (2026-11-02)

This repository contains a **reproducible synthetic decision-level pilot**, not a validated autonomous-driving decision/planning method. The objective is to test whether jointly anticipating downstream conflict-window occupation and the temporary availability of a holding/refuge region can change *entrance* choices at a narrow road bottleneck.

## Deliverables

- `STV_ED_english_pilot_manuscript.docx`: complete **preliminary research manuscript** (not ready for submission); includes methods, observed experimental outcomes, failure modes, limitations, and 13 references.
- `STV_ED_chinese_literature_guide.docx`: annotated Chinese literature guide, novelty boundary, pilot results, and outstanding requirements.
- `pilot_simulation.py`: actually executed Python simulation code, no fabricated experimental outcomes.
- `test_pilot.py`: minimal unit tests for feasibility logic.
- `analysis_extra.py`: paired-bootstrap risk contrasts, padding sensitivity.
- `references.bib`: BibTeX entries with publisher DOI/links when available (the SM-NR item is an arXiv preprint; do not cite as a published journal article unless verified).
- `results/`: original generated CSV, config, JSON, and figures.

## Reproduce

Python 3.10+ with `numpy`, `pandas`, and `matplotlib`:

```bash
python -m pip install numpy pandas matplotlib
python -m unittest test_pilot.py
python pilot_simulation.py --episodes 1000 --seed 20261102 --padding 1.25 --output results
python analysis_extra.py
```

Run from the project folder. The extra analysis saves to `results/` relative to `analysis_extra.py`. Graphs appear in `results/pilot_exposure.png` and `results/padding_sensitivity.png`. If you want to keep the delivered outcome unchanged, copy the directory before rerunning.

## The model that was *actually executed*

- There are two conflict resources (gates G1 and G2) and one intermediate waiting/refuge resource B1.
- Each stage is 18 m and is traversed at an idealized fixed speed of 3 m/s, hence 6 s/stage. The crossing exposure interval relative to stage departure is `[2.2, 3.8]` seconds.
- For every simulated scene, each resource can have up to two synthetic occupation events, with event existence sampled independently with probabilities 0.82 (gates) and 0.65 (refuge); the occupation time distributions are **hand-chosen and not calibrated to township field data**. See `actual_events()` for exact distributions.
- Every future real occupation is assumed correctly *known to exist*, with duration known, but shifted in its **forecast** by an independent Gaussian temporal error `N(0, sigma^2)`, sigma in `[0.4, 1.0, 1.6]` seconds.
- Policies search candidate entry times at 0.5-s increments; choose earliest scheduled exit subject to their respective forecast constraints. They cannot replan once underway.
- The main joint-robust method inflates the predicted event intervals by delta=1.25 s, checks both gate crossings, and verifies the full time of refuge usage when an intermediate stop is needed.
- `reactive` observes only current *real* G1 occupancy, not a future forecast. Other internal baselines share the same noisy forecast to allow paired episode analysis.

## What the numbers mean

- `exposure`: a **binary resource schedule conflict**. It means the prescribed crossing or residence time overlaps a realized occupation interval. It is **NOT** a physical vehicle collision, TTC threshold, or proof of road safety.
- `completion`: the schedule has no conflict in this abstraction. It is **NOT** guaranteed vehicle maneuver feasibility.
- `planned_finish`: planned scheduled exit time; may be calculated even for a schedule later found to conflict. Consequently it is **NOT** the empirically observed successful vehicle travel time. Interpret it as a schedule-efficiency proxy only.

In 1,000 paired synthetic episodes at sigma=1.0 s:

| Internal method | Schedule conflict exposure | Mean planned finish (s) |
| --- | ---: | ---: |
| `joint_nominal` (no padding, checks refuge) | 22.6% | 13.5135 |
| `robust_no_refuge` (padding, ignores refuge occupancy) | 13.3% | 15.1250 |
| `joint_robust` / proposed STV-ED (padding + refuge check) | 6.1% | 15.2725 |

The paired difference `joint_robust - joint_nominal` is -16.5 percentage points, paired 5,000-resample bootstrap 95% CI (-19.0, -14.1) percentage points. **These intervals measure sampling variability under the fixed synthetic scenario generator, not real-world validity.** Results are easily affected by selected timing error, padding, occupancy distributions, and rules favorable to the tested method.

## A mathematically limited observation

Suppose every true resource occupation interval for resources used by a candidate schedule is contained in the corresponding padded predicted interval (i.e., a valid bounded forecast-error envelope), and every scheduled vehicle resource usage interval is disjoint from the padded predicted occupation. In this simplified schedule model, the schedule does not overlap true resource occupation (by set inclusion). This is a conditional *set-theoretic* observation only. **Gaussian errors are unbounded; a fixed delta=1.25s does not establish deterministic coverage. The observation makes no claim about actual vehicle collision avoidance.**

## Unresolved issues before a credible EI conference submission

1. Use a vehicle kinematic or dynamic model, vehicle footprint, steering and braking limits, and realistic stopping/turning geometry instead of fixed stage transit times.
2. Model pedestrian/cyclist motion and previously unseen or falsely detected actors; calibrate forecasts using authentic or public trajectory data.
3. Implement rolling/closed-loop replanning with safe-to-stop or safe-to-retreat terminal states, including a blocked or inaccessible refuge.
4. Compare under genuinely equivalent inputs and computational budgets with strong published baselines or faithful reproductions (e.g. SM-NR, published reachable-set approaches), not merely internal ablations.
5. Add full scenario coverage, collision/near-collision metrics, progress, control effort/comfort, planning runtime, confidence intervals and statistical tests.
6. Justify novelty against prior fail-safe planning, dynamic narrow-road meeting-gap search, OA-MPC terminal stop, and 2026 uncertainty-aware reachability approaches.
7. Obtain instructor/coauthor checks, preserve raw output, and check exact author-paper metadata as well as any target conference deadlines and indexing policy.

## Research integrity

No real vehicles, human drivers, human participants, or real township road traffic data were used. No CARLA/CommonRoad runs were performed here. None of the empirical outcomes is suitable for describing a *collision rate*, *generalizable safety improvement*, or *proven superior state-of-the-art performance*. All displayed numerical results were produced by the included code. References are genuine papers, but only metadata, accessible pages, and accessible passages were checked; this is **not** a claim that every full paper has been read comprehensively.
