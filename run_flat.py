#!/usr/bin/env python3
"""
Flat resource distribution: every cell starts at maximum sugar (4) and maximum
spice (4) with no spatial gradient. This removes all concentration-driven
advantages and serves as a baseline comparable to Hawick (2014)'s uniform layout.

The flat grid is written to flat_environment.json once and reused for all runs.
"""
import argparse
import json
import os
from sim_runner import add_common_args, run_experiment

PROJECT_ROOT  = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, "flat_environment.json")

GRID_WIDTH  = 50
GRID_HEIGHT = 50
MAX_SUGAR   = 4
MAX_SPICE   = 4


def generate_flat_environment(path, width=GRID_WIDTH, height=GRID_HEIGHT,
                               max_sugar=MAX_SUGAR, max_spice=MAX_SPICE):
    grid = [
        [{"sugar": max_sugar, "spice": max_spice} for _ in range(height)]
        for _ in range(width)
    ]
    with open(path, "w") as f:
        json.dump(grid, f)
    print(f"  Flat environment written → {path}")


CONDITIONS = [
    {"label": "flat_utilitarian", "model": ["bentham"],  "environment_file": ENV_FILE_PATH},
    {"label": "flat_altruistic",  "model": ["altruist"], "environment_file": ENV_FILE_PATH},
    {"label": "flat_egoistic",    "model": ["egoist"],   "environment_file": ENV_FILE_PATH},
]


def parse_args():
    p = argparse.ArgumentParser(
        description="Flat resource distribution × utilitarian/altruistic/egoistic",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_common_args(p)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    generate_flat_environment(ENV_FILE_PATH)

    print(f"\n{'='*60}")
    print(f"  Flat Resource Distribution Conditions")
    print(f"  Grid: {GRID_WIDTH}x{GRID_HEIGHT}, sugar={MAX_SUGAR}, spice={MAX_SPICE} (uniform)")
    print(f"  Seeds: {args.seeds}  Timesteps: {args.timesteps}  Cores: {args.cores}")
    print(f"{'='*60}\n")

    run_experiment(CONDITIONS, args, results_subdir="flat_results")
