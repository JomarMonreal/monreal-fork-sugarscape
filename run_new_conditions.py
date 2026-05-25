#!/usr/bin/env python3
"""
run_new_conditions.py
Unified runner for two new experiment types across d=0, d=7, and d=14.

Homogeneous rawSugarscape (--mode raw):
  Standard greedy Sugarscape agents (no ethical decision model) at each
  resource configuration.  Three conditions total:
    raw_d0   concentrated       (d=0)
    raw_d7   moderately conc.   (d=7)
    raw_d14  distributed        (d=14)

Heterogeneous Bentham-Egoist sweep (--mode hetero):
  Mixed populations where the proportion of Bentham (utilitarian) agents
  varies from --step to (100-step) percent in increments of --step,
  with the remainder being Egoist agents.  Each d level is swept
  independently:
    hetero_d0_pXXX   / hetero_d7_pXXX   / hetero_d14_pXXX

Usage examples:
  python3 run_new_conditions.py                        # both modes, defaults
  python3 run_new_conditions.py --mode raw             # rawSugarscape only
  python3 run_new_conditions.py --mode hetero          # heterogeneous only
  python3 run_new_conditions.py --mode hetero --step 10
  python3 run_new_conditions.py -j 9 -s 100 -t 5000
"""

import argparse
from sim_runner import add_common_args, run_experiment, make_models_list

# ── Resource peak coordinates ────────────────────────────────────────────────
D14_SUGAR = [[15, 35, 4], [35, 15, 4]]
D14_SPICE = [[15, 15, 4], [35, 35, 4]]

D7_SUGAR  = [[20, 30, 4], [30, 20, 4]]
D7_SPICE  = [[20, 20, 4], [30, 30, 4]]

D0_SUGAR  = [[25, 25, 4], [25, 25, 4]]
D0_SPICE  = [[25, 25, 4], [25, 25, 4]]

# ── Condition builders ───────────────────────────────────────────────────────

RAW_CONDITIONS = [
    {
        "label":       "raw_d0",
        "model":       ["none"],
        "sugar_peaks": D0_SUGAR,
        "spice_peaks": D0_SPICE,
    },
    {
        "label":       "raw_d7",
        "model":       ["none"],
        "sugar_peaks": D7_SUGAR,
        "spice_peaks": D7_SPICE,
    },
    {
        "label":       "raw_d14",
        "model":       ["none"],
        "sugar_peaks": D14_SUGAR,
        "spice_peaks": D14_SPICE,
    },
]


def build_hetero_conditions(step=20):
    conditions = []
    for d_label, sugar, spice in [
        ("d0",  D0_SUGAR,  D0_SPICE),
        ("d7",  D7_SUGAR,  D7_SPICE),
        ("d14", D14_SUGAR, D14_SPICE),
    ]:
        for pct in range(step, 100, step):
            conditions.append({
                "label":            f"hetero_{d_label}_p{pct:03d}",
                "model":            make_models_list(pct),
                "sugar_peaks":      sugar,
                "spice_peaks":      spice,
                "experimentalGroup": "bentham",
            })
    return conditions


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Homogeneous rawSugarscape and heterogeneous Bentham-Egoist "
                    "sweep across d=0, d=7, and d=14.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    p.add_argument(
        "--mode",
        choices=["raw", "hetero", "all"],
        default="all",
        help="Which experiment type to run: raw, hetero, or all (default: all)",
    )
    p.add_argument(
        "--step",
        type=int,
        default=20,
        help="Bentham percentage-point increment for the heterogeneous sweep "
             "(e.g. 20 → 20%%, 40%%, 60%%, 80%% Bentham)",
    )
    return p.parse_args()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"  run_new_conditions.py")
    print(f"  Mode:      {args.mode}")
    print(f"  Seeds:     {args.seeds}   Timesteps: {args.timesteps}")
    print(f"  Cores:     {args.cores}   Output:    {args.output}")
    if args.mode in ("hetero", "all"):
        print(f"  Hetero step: {args.step}%")
    print(f"{'='*60}\n")

    if args.mode in ("raw", "all"):
        print("── Homogeneous rawSugarscape ────────────────────────────────")
        run_experiment(RAW_CONDITIONS, args, results_subdir="raw_results")

    if args.mode in ("hetero", "all"):
        hetero = build_hetero_conditions(step=args.step)
        n_levels = len(hetero) // 3
        print("── Heterogeneous Bentham-Egoist sweep ───────────────────────")
        print(f"   {n_levels} proportion levels × 3 d-values = {len(hetero)} conditions")
        run_experiment(hetero, args, results_subdir="hetero_results")


if __name__ == "__main__":
    main()
