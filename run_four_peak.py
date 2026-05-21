#!/usr/bin/env python3
import argparse
from sim_runner import add_common_args, run_experiment

FOUR_PEAK_SUGAR = [[15, 35, 4], [35, 15, 4]]
FOUR_PEAK_SPICE = [[15, 15, 4], [35, 35, 4]]

CONDITIONS = [
    {"label": "four_peak_utilitarian", "model": ["bentham"],  "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE},
    {"label": "four_peak_altruistic",  "model": ["altruist"], "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE},
    {"label": "four_peak_egoistic",    "model": ["egoist"],   "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE},
]

def parse_args():
    p = argparse.ArgumentParser(
        description="Conditions 1-3: four-peak x utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Four-Peak Conditions (1-3)")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(CONDITIONS, args, results_subdir="four_peak_results")
