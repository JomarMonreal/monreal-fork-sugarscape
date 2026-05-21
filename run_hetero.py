#!/usr/bin/env python3
import argparse
from sim_runner import add_common_args, run_experiment, make_models_list

FOUR_PEAK_SUGAR = [[15, 35, 4], [35, 15, 4]]
FOUR_PEAK_SPICE = [[15, 15, 4], [35, 35, 4]]
ONE_PEAK_SUGAR  = [[25, 25, 4]]
ONE_PEAK_SPICE  = [[25, 25, 4]]

def build_hetero_conditions(step=10):
    conditions = []
    for pct in range(step, 100, step):
        models = make_models_list(pct)
        conditions.append({
            "label":       f"four_peak_hetero_p{pct:03d}",
            "model":       models,
            "sugar_peaks": FOUR_PEAK_SUGAR,
            "spice_peaks": FOUR_PEAK_SPICE,
        })
    for pct in range(step, 100, step):
        models = make_models_list(pct)
        conditions.append({
            "label":       f"one_peak_hetero_p{pct:03d}",
            "model":       models,
            "sugar_peaks": ONE_PEAK_SUGAR,
            "spice_peaks": ONE_PEAK_SPICE,
        })
    return conditions

def parse_args():
    p = argparse.ArgumentParser(
        description="Phase 2: heterogeneous Egoist-Bentham sweep under four-peak and single-peak",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    p.add_argument("--step", type=int, default=20,
                   help="Percentage-point increment for Bentham proportion sweep")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    conditions = build_hetero_conditions(step=args.step)
    n_per_config = len(conditions) // 2
    print(f"\n{'='*60}")
    print(f"  Phase 2: Heterogeneous Egoist-Bentham Sweep")
    print(f"  Step: {args.step}%  ({n_per_config} levels x 2 configs = {len(conditions)} conditions)")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(conditions, args, results_subdir="hetero_results")
