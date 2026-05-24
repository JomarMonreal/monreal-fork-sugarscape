#!/usr/bin/env python3
"""
Two-peak separated (d=14): sugar and spice at opposite corners, spread out.
Sugar peak at (15,35), spice peak at (35,15).
No location on the grid has both resources abundant.
"""
import argparse
from sim_runner import add_common_args, run_experiment

SUGAR = [[15, 35, 4]]
SPICE = [[35, 15, 4]]

CONDITIONS = [
    {"label": "two_peak_d14_utilitarian", "model": ["bentham"],  "sugar_peaks": SUGAR, "spice_peaks": SPICE},
    {"label": "two_peak_d14_altruistic",  "model": ["altruist"], "sugar_peaks": SUGAR, "spice_peaks": SPICE},
    {"label": "two_peak_d14_egoistic",    "model": ["egoist"],   "sugar_peaks": SUGAR, "spice_peaks": SPICE},
]

def parse_args():
    p = argparse.ArgumentParser(
        description="Two-peak separated d=14 x utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Two-Peak Separated d=14")
    print(f"  Sugar: {SUGAR}  Spice: {SPICE}")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(CONDITIONS, args, results_subdir="two_peak_d14_results")
