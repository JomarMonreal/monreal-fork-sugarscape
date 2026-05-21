#!/usr/bin/env python3
import argparse
from sim_runner import add_common_args, run_experiment, make_models_list

D0_SUGAR = [[25, 25, 4], [25, 25, 4]]
D0_SPICE = [[25, 25, 4], [25, 25, 4]]

def build_conditions(step=20):
    conditions = []
    for pct in range(step, 100, step):
        conditions.append({
            "label":       f"d0_hetero_p{pct:03d}",
            "model":       make_models_list(pct),
            "sugar_peaks": D0_SUGAR,
            "spice_peaks": D0_SPICE,
        })
    return conditions

def parse_args():
    p = argparse.ArgumentParser(
        description="Phase 2: Egoist-Bentham sweep at d=0 (concentrated)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    p.add_argument("--step", type=int, default=20,
                   help="Percentage-point increment for Bentham proportion sweep")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    conditions = build_conditions(step=args.step)
    print(f"\n{'='*60}")
    print(f"  Phase 2: Heterogeneous Sweep — d=0 (Concentrated)")
    print(f"  Step: {args.step}%  ({len(conditions)} proportion levels)")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(conditions, args, results_subdir="hetero_d0_results")
