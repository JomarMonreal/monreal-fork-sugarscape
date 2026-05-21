#!/usr/bin/env python3
import argparse
from sim_runner import add_common_args, run_experiment

TWO_PEAK_SUGAR = [[15, 35, 4]]
TWO_PEAK_SPICE = [[35, 15, 4]]

CONDITIONS = [
    {"label": "two_peak_utilitarian", "model": ["bentham"],  "sugar_peaks": TWO_PEAK_SUGAR, "spice_peaks": TWO_PEAK_SPICE},
    {"label": "two_peak_altruistic",  "model": ["altruist"], "sugar_peaks": TWO_PEAK_SUGAR, "spice_peaks": TWO_PEAK_SPICE},
    {"label": "two_peak_egoistic",    "model": ["egoist"],   "sugar_peaks": TWO_PEAK_SUGAR, "spice_peaks": TWO_PEAK_SPICE},
]

def parse_args():
    p = argparse.ArgumentParser(
        description="Conditions 4-6: two-peak x utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Two-Peak Conditions (4-6)")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(CONDITIONS, args, results_subdir="two_peak_results")
