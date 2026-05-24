#!/usr/bin/env python3
"""
Two-peak resource configurations.

Co-located: sugar and spice peaks share the same two corners.
  Each zone is rich in both resources — two full-wealth clusters.

Separated: sugar and spice peaks are at opposite corners.
  One corner is sugar-rich, the other is spice-rich.
  No location on the grid has both resources abundant.
"""
import argparse
from sim_runner import add_common_args, run_experiment

# Co-located: both resources at the same two anti-diagonal corners
COLOCATED_SUGAR = [[15, 35, 4], [35, 15, 4]]
COLOCATED_SPICE = [[15, 35, 4], [35, 15, 4]]

# Separated: sugar and spice at opposite corners (no co-location)
SEPARATED_SUGAR = [[15, 35, 4]]
SEPARATED_SPICE = [[35, 15, 4]]

CONDITIONS = [
    {"label": "two_peak_colocated_utilitarian", "model": ["bentham"],  "sugar_peaks": COLOCATED_SUGAR, "spice_peaks": COLOCATED_SPICE},
    {"label": "two_peak_colocated_altruistic",  "model": ["altruist"], "sugar_peaks": COLOCATED_SUGAR, "spice_peaks": COLOCATED_SPICE},
    {"label": "two_peak_colocated_egoistic",    "model": ["egoist"],   "sugar_peaks": COLOCATED_SUGAR, "spice_peaks": COLOCATED_SPICE},
    {"label": "two_peak_separated_utilitarian", "model": ["bentham"],  "sugar_peaks": SEPARATED_SUGAR, "spice_peaks": SEPARATED_SPICE},
    {"label": "two_peak_separated_altruistic",  "model": ["altruist"], "sugar_peaks": SEPARATED_SUGAR, "spice_peaks": SEPARATED_SPICE},
    {"label": "two_peak_separated_egoistic",    "model": ["egoist"],   "sugar_peaks": SEPARATED_SUGAR, "spice_peaks": SEPARATED_SPICE},
]

def parse_args():
    p = argparse.ArgumentParser(
        description="Two-peak conditions: co-located and separated x utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Two-Peak Conditions (co-located + separated)")
    print(f"  Co-located:  sugar={COLOCATED_SUGAR}  spice={COLOCATED_SPICE}")
    print(f"  Separated:   sugar={SEPARATED_SUGAR}  spice={SEPARATED_SPICE}")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")
    run_experiment(CONDITIONS, args, results_subdir="two_peak_results")
