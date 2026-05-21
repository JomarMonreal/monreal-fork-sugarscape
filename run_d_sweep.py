#!/usr/bin/env python3
"""
Phase 1 distance sweep: vary radial distance of four peaks from center.

At distance d, peaks are placed at:
  Sugar: (25 - d/√2, 25 + d/√2)  and  (25 + d/√2, 25 - d/√2)
  Spice: (25 - d/√2, 25 - d/√2)  and  (25 + d/√2, 25 + d/√2)

d=0  → all peaks at center (25,25) — identical to one-peak, maximum concentration
d=14 → peaks at corners (15,35)/(35,15) — identical to original four-peak, maximum spread

Note: d=0 and d=14 match existing run_one_peak.py and run_four_peak.py data exactly.
      Only intermediate d values need new runs.
"""
import math
import argparse
from sim_runner import add_common_args, run_experiment

CENTER = 25

def peaks_for_distance(d):
    offset = round(d / math.sqrt(2))
    sugar_peaks = [
        [CENTER - offset, CENTER + offset, 4],
        [CENTER + offset, CENTER - offset, 4],
    ]
    spice_peaks = [
        [CENTER - offset, CENTER - offset, 4],
        [CENTER + offset, CENTER + offset, 4],
    ]
    return sugar_peaks, spice_peaks

def build_conditions(distances):
    conditions = []
    for d in distances:
        sugar_peaks, spice_peaks = peaks_for_distance(d)
        for model, label in [("bentham", "utilitarian"), ("altruist", "altruistic"), ("egoist", "egoistic")]:
            conditions.append({
                "label":       f"d{d:02d}_{label}",
                "model":       [model],
                "sugar_peaks": sugar_peaks,
                "spice_peaks": spice_peaks,
            })
    return conditions

def parse_args():
    p = argparse.ArgumentParser(
        description="Distance sweep: vary radial peak distance from center",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    p.add_argument(
        "--distances", type=int, nargs="+", default=[7],
        help="Radial distances from center to run (d=0 and d=14 reuse existing data)",
    )
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    conditions = build_conditions(args.distances)

    print(f"\n{'='*60}")
    print(f"  Distance Sweep")
    for d in args.distances:
        sugar, spice = peaks_for_distance(d)
        print(f"  d={d:2d}  sugar={sugar}  spice={spice}")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")

    run_experiment(conditions, args, results_subdir="d_sweep_results")
