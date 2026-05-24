#!/usr/bin/env python3
"""
Re-run a specific list of seeds for one condition.
Use this to fill in seeds that crashed during a parallel run.

Usage:
  python3 run_repopulate.py --condition four_peak_utilitarian \
      --seeds 687 651 876 72 634 128 619 991 984 829 719 518 \
      --output data --results four_peak_results -j 4
"""
import argparse
import json
import multiprocessing
import os
import subprocess
import time

from sim_runner import load_base_config, make_run_config, parse_sim_log, write_csv

CONDITION_MAP = {
    "four_peak_utilitarian": {
        "label": "four_peak_utilitarian",
        "model": ["bentham"],
        "sugar_peaks": [[15, 35, 4], [35, 15, 4]],
        "spice_peaks": [[15, 15, 4], [35, 35, 4]],
    },
    "four_peak_altruistic": {
        "label": "four_peak_altruistic",
        "model": ["altruist"],
        "sugar_peaks": [[15, 35, 4], [35, 15, 4]],
        "spice_peaks": [[15, 15, 4], [35, 35, 4]],
    },
    "four_peak_egoistic": {
        "label": "four_peak_egoistic",
        "model": ["egoist"],
        "sugar_peaks": [[15, 35, 4], [35, 15, 4]],
        "spice_peaks": [[15, 15, 4], [35, 35, 4]],
    },
    "d7_utilitarian": {
        "label": "d7_utilitarian",
        "model": ["bentham"],
        "sugar_peaks": [[20, 30, 4], [30, 20, 4]],
        "spice_peaks": [[20, 20, 4], [30, 30, 4]],
    },
    "d7_altruistic": {
        "label": "d7_altruistic",
        "model": ["altruist"],
        "sugar_peaks": [[20, 30, 4], [30, 20, 4]],
        "spice_peaks": [[20, 20, 4], [30, 30, 4]],
    },
    "d7_egoistic": {
        "label": "d7_egoistic",
        "model": ["egoist"],
        "sugar_peaks": [[20, 30, 4], [30, 20, 4]],
        "spice_peaks": [[20, 20, 4], [30, 30, 4]],
    },
    "one_peak_utilitarian": {
        "label": "one_peak_utilitarian",
        "model": ["bentham"],
        "sugar_peaks": [[25, 25, 4]],
        "spice_peaks": [[25, 25, 4]],
    },
    "one_peak_altruistic": {
        "label": "one_peak_altruistic",
        "model": ["altruist"],
        "sugar_peaks": [[25, 25, 4]],
        "spice_peaks": [[25, 25, 4]],
    },
    "one_peak_egoistic": {
        "label": "one_peak_egoistic",
        "model": ["egoist"],
        "sugar_peaks": [[25, 25, 4]],
        "spice_peaks": [[25, 25, 4]],
    },
}


def run_one(args):
    cfg_path, python_alias, label, seed = args
    t = time.time()
    result = subprocess.run(
        [python_alias, "sugarscape.py", "--conf", cfg_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    dur = time.time() - t
    if result.returncode != 0:
        print(f"\n  [error] seed={seed} exited {result.returncode}: {result.stderr.decode().strip()[-200:]}")
    else:
        print(f"  [done]  seed={seed}  ({dur:.1f}s)")
    return cfg_path, dur


def parse_args():
    p = argparse.ArgumentParser(
        description="Re-run specific failed seeds for one condition",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--condition", required=True, choices=list(CONDITION_MAP),
                   help="Condition label to re-run")
    p.add_argument("--seeds",    required=True, nargs="+", type=int,
                   help="Seed values to re-run")
    p.add_argument("-c", "--config",    default="config.json")
    p.add_argument("-o", "--output",    default="data")
    p.add_argument("-t", "--timesteps", type=int, default=5000)
    p.add_argument("-j", "--cores",     type=int, default=4)
    p.add_argument("--python",          default="python3")
    p.add_argument("--results",         default=None,
                   help="Results subdir name (default: <condition>_results)")
    return p.parse_args()


def main():
    args   = parse_args()
    cond   = CONDITION_MAP[args.condition]
    label  = cond["label"]
    seeds  = args.seeds
    root   = os.path.dirname(os.path.abspath(__file__))
    cdir   = os.path.join(root, args.output, label)
    rdir   = os.path.join(root, args.output, args.results or f"{label}_results")
    os.makedirs(cdir, exist_ok=True)
    os.makedirs(rdir, exist_ok=True)

    base = load_base_config(args.config)
    runs = []
    for seed in seeds:
        log_path = os.path.join(cdir, f"{label}_{seed}.json")
        cfg_path = os.path.join(cdir, f"{label}_{seed}.config")
        cfg = make_run_config(base, cond, seed, args.timesteps, log_path)
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)
        runs.append((cfg_path, args.python, label, seed))

    num_cores = max(1, min(args.cores, os.cpu_count() or 1))
    print(f"\n{'='*60}")
    print(f"  Repopulating {len(seeds)} seeds for {label}")
    print(f"  Cores: {num_cores}  Timesteps: {args.timesteps}")
    print(f"{'='*60}\n")

    t0 = time.time()
    with multiprocessing.Pool(processes=num_cores) as pool:
        results = pool.map(run_one, runs)
    print(f"\n  Finished in {time.time() - t0:.1f}s")

    # Parse new logs and append to existing CSVs
    new_pts, new_summaries = [], []
    durations = {path: dur for path, dur in results}
    for cfg_path, _, _, seed in runs:
        log_path = cfg_path.replace(".config", ".json")
        dur = durations.get(cfg_path, 0.0)
        pts, summary = parse_sim_log(log_path, label, seed, dur)
        if pts is None:
            print(f"  [warn] Still no data for seed={seed}")
            continue
        new_pts.extend(pts)
        new_summaries.append(summary)

    print(f"\n  Parsed {len(new_summaries)}/{len(seeds)} seeds successfully.")

    # Append to existing CSVs
    for fname, rows in [("per_timestep.csv", new_pts), ("per_seed_summary.csv", new_summaries)]:
        path = os.path.join(rdir, fname)
        if not rows:
            continue
        if os.path.exists(path):
            import csv
            with open(path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
                writer.writerows(rows)
            print(f"  Appended {len(rows)} rows → {path}")
        else:
            write_csv(rows, path)
            print(f"  Wrote {len(rows)} rows → {path}")


if __name__ == "__main__":
    main()
