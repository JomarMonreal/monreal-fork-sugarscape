#!/usr/bin/env python3
"""
Two-peak separated (d=7): sugar and spice at opposite corners, pulled toward center.
Sugar peak at (20,30), spice peak at (30,20).
Same separation logic as d=14 but zones are closer — lower travel cost between them.
"""
import argparse
from sim_runner import add_common_args, run_experiment

SUGAR = [[20, 30, 4]]
SPICE = [[30, 20, 4]]

CONDITIONS = [
    {"label": "two_peak_d7_utilitarian", "model": ["bentham"],  "sugar_peaks": SUGAR, "spice_peaks": SPICE},
    {"label": "two_peak_d7_altruistic",  "model": ["altruist"], "sugar_peaks": SUGAR, "spice_peaks": SPICE},
    {"label": "two_peak_d7_egoistic",    "model": ["egoist"],   "sugar_peaks": SUGAR, "spice_peaks": SPICE},
]

def parse_args():
    p = argparse.ArgumentParser(
        description="Two-peak separated d=7 x utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Two-Peak Separated d=7")
    print(f"  Sugar: {SUGAR}  Spice: {SPICE}")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(CONDITIONS, args, results_subdir="two_peak_d7_results")
