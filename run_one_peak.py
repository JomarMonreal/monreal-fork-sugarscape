#!/usr/bin/env python3
import argparse
from sim_runner import add_common_args, run_experiment

ONE_PEAK_SUGAR = [[25, 25, 4]]
ONE_PEAK_SPICE = [[25, 25, 4]]

CONDITIONS = [
    {"label": "one_peak_utilitarian", "model": ["bentham"],  "sugar_peaks": ONE_PEAK_SUGAR, "spice_peaks": ONE_PEAK_SPICE},
    {"label": "one_peak_altruistic",  "model": ["altruist"], "sugar_peaks": ONE_PEAK_SUGAR, "spice_peaks": ONE_PEAK_SPICE},
    {"label": "one_peak_egoistic",    "model": ["egoist"],   "sugar_peaks": ONE_PEAK_SUGAR, "spice_peaks": ONE_PEAK_SPICE},
]

def parse_args():
    p = argparse.ArgumentParser(
        description="Conditions 7-9: single-peak x utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Single-Peak Conditions (7-9)")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(CONDITIONS, args, results_subdir="one_peak_results")
