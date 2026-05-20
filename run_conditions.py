#!/usr/bin/env python3
import argparse
import csv
import json
import math
import multiprocessing
import os
import random
import subprocess
import sys
import time

FOUR_PEAK_SUGAR = [[15, 35, 4], [35, 15, 4]]
FOUR_PEAK_SPICE = [[15, 15, 4], [35, 35, 4]]
ONE_PEAK_SUGAR  = [[25, 25, 4]]
ONE_PEAK_SPICE  = [[25, 25, 4]]

CONDITIONS = [
    {"id": 1, "label": "four_peak_utilitarian", "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE, "model": ["bentham"]},
    {"id": 2, "label": "four_peak_altruistic",  "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE, "model": ["altruist"]},
    {"id": 3, "label": "four_peak_egoistic",    "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE, "model": ["egoist"]},
    {"id": 4, "label": "one_peak_utilitarian",  "sugar_peaks": ONE_PEAK_SUGAR,  "spice_peaks": ONE_PEAK_SPICE,  "model": ["bentham"]},
    {"id": 5, "label": "one_peak_altruistic",   "sugar_peaks": ONE_PEAK_SUGAR,  "spice_peaks": ONE_PEAK_SPICE,  "model": ["altruist"]},
    {"id": 6, "label": "one_peak_egoistic",     "sugar_peaks": ONE_PEAK_SUGAR,  "spice_peaks": ONE_PEAK_SPICE,  "model": ["egoist"]},
]


def generate_seeds(n, master_seed=42):
    random.seed(master_seed)
    seeds = []
    while len(seeds) < n:
        s = random.randint(0, sys.maxsize)
        if s not in seeds:
            seeds.append(s)
    return seeds


def load_base_config(path):
    with open(path) as f:
        full = json.load(f)
    return full.get("sugarscapeOptions", full)


def make_run_config(base, condition, seed, timesteps, log_path):
    cfg = dict(base)
    cfg["seed"]                    = seed
    cfg["agentDecisionModels"]     = condition["model"]
    cfg["environmentSugarPeaks"]   = condition["sugar_peaks"]
    cfg["environmentSpicePeaks"]   = condition["spice_peaks"]
    cfg["timesteps"]               = timesteps
    cfg["headlessMode"]            = True
    cfg["debugMode"]               = ["none"]
    cfg["keepAlivePostExtinction"] = False
    cfg["keepAliveAtEnd"]          = False
    cfg["screenshots"]             = False
    cfg["profileMode"]             = False
    cfg["logfile"]                 = log_path
    cfg["agentLogfile"]            = None
    cfg["logfileFormat"]           = "json"
    return cfg


def safe_json_load(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def is_complete(log_path, timesteps):
    d = safe_json_load(log_path)
    if not d:
        return False
    last_ts  = int(d[-1].get("timestep", 0))
    last_pop = int(d[-1].get("population", -1))
    return last_ts >= timesteps or last_pop == 0


def run_one_simulation(args):
    config_path, python_alias, counter, lock, total = args
    t = time.time()
    subprocess.run(
        [python_alias, "sugarscape.py", "--conf", config_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    dur = time.time() - t
    with lock:
        counter.value += 1
        pct = counter.value / total * 100
        print(f"\r  [{counter.value:>4}/{total}]  {pct:5.1f}%  "
              f"last={os.path.basename(config_path):<55}", end="", flush=True)
    return config_path, dur


def parse_sim_log(log_path, label, seed, duration=0.0):
    sim_log = safe_json_load(log_path)
    if not sim_log:
        return None, None

    per_timestep = []
    total_deaths = 0
    total_born   = 0
    final_pop    = 0

    for entry in sim_log:
        pop = int(entry.get("population", 0))
        d   = int(entry.get("agentDeaths", 0))
        b   = int(entry.get("agentsBorn", 0))
        total_deaths += d
        total_born   += b
        per_timestep.append({
            "condition":             label,
            "seed":                  seed,
            "timestep":              int(entry.get("timestep", 0)),
            "population":            pop,
            "meanWealth":            float(entry.get("meanWealth", 0)),
            "societalWealth":        float(entry.get("agentWealthTotal", 0)),
            "giniCoefficient":       float(entry.get("giniCoefficient", 0)),
            "agentDeaths":           d,
            "agentStarvationDeaths": int(entry.get("agentStarvationDeaths", 0)),
            "agentAgingDeaths":      int(entry.get("agentAgingDeaths", 0)),
            "agentsBorn":            b,
            "meanTimeToLive":        float(entry.get("agentMeanTimeToLive", 0)),
            "meanAge":               float(entry.get("meanAge", 0)),
            "tradeVolume":           float(entry.get("tradeVolume", 0)),
            "meanHappiness":         float(entry.get("meanHappiness", 0)),
        })
        final_pop = pop

    last = per_timestep[-1] if per_timestep else {}
    summary = {
        "condition":           label,
        "seed":                seed,
        "executionTime":       round(duration, 2),
        "extinct":             (final_pop == 0),
        "finalPopulation":     final_pop,
        "totalDeaths":         total_deaths,
        "totalBorn":           total_born,
        "finalTimestep":       last.get("timestep", 0),
        "finalMeanWealth":     last.get("meanWealth", 0),
        "finalSocietalWealth": last.get("societalWealth", 0),
        "finalGini":           last.get("giniCoefficient", 0),
        "finalMeanTimeToLive": last.get("meanTimeToLive", 0),
    }
    return per_timestep, summary


def write_csv(rows, path):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    keys = list(rows[0].keys())
    seen = set(keys)
    for r in rows[1:]:
        for k in r:
            if k not in seen:
                keys.append(k)
                seen.add(k)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, restval="")
        writer.writeheader()
        writer.writerows(rows)


def aggregate_seeds(summaries):
    if not summaries:
        return {}
    num_keys = [k for k, v in summaries[0].items()
                if isinstance(v, (int, float)) and k != "seed"]
    agg = {
        "condition":      summaries[0]["condition"],
        "numSeeds":       len(summaries),
        "extinctionRate": sum(1 for s in summaries if s["extinct"]) / len(summaries),
    }
    for k in num_keys:
        vals = [s[k] for s in summaries]
        mu   = sum(vals) / len(vals)
        std  = math.sqrt(sum((v - mu) ** 2 for v in vals) / len(vals))
        agg[f"mean_{k}"] = round(mu, 4)
        agg[f"std_{k}"]  = round(std, 4)
    return agg


def parse_args():
    p = argparse.ArgumentParser(
        description="Run 6 experimental conditions (2 resource configs × 3 ethical models)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("conditions", nargs="*", type=int,
                   help="Condition IDs to run (1–6). Omit to run all.")
    p.add_argument("-c", "--config",    default="config.json")
    p.add_argument("-o", "--output",    default="data")
    p.add_argument("-s", "--seeds",     type=int, default=30)
    p.add_argument("-t", "--timesteps", type=int, default=5000)
    p.add_argument("-j", "--cores",     type=int, default=1)
    p.add_argument("--python",          default="python3")
    p.add_argument("--force",       action="store_true",
                   help="Re-run even if log already exists")
    p.add_argument("--delete-logs", action="store_true",
                   help="Delete raw JSON logs after parsing (saves disk space)")
    return p.parse_args()


def main():
    args = parse_args()

    selected_ids = args.conditions if args.conditions else list(range(1, 7))
    valid = [i for i in selected_ids if 1 <= i <= 6]
    if not valid:
        print("Valid condition IDs are 1 through 6.")
        sys.exit(1)

    selected  = [c for c in CONDITIONS if c["id"] in valid]
    num_cores = max(1, min(args.cores, os.cpu_count() or 1))
    base_cfg  = load_base_config(args.config)
    seeds     = generate_seeds(args.seeds)

    project_root = os.path.dirname(os.path.abspath(__file__))
    results_dir  = os.path.join(project_root, args.output, "results")
    os.makedirs(results_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Sugarscape Ethical Model Experiment Runner")
    print(f"{'='*60}")
    print(f"  Conditions: {[c['id'] for c in selected]}")
    print(f"  Seeds:      {args.seeds}   Timesteps: {args.timesteps}")
    print(f"  Cores:      {num_cores}   Output:    {args.output}")
    print(f"{'='*60}\n")

    # Build run specs and write config files
    all_runs = []
    for cond in selected:
        cdir = os.path.join(project_root, args.output, cond["label"])
        os.makedirs(cdir, exist_ok=True)
        for seed in seeds:
            log_path = os.path.join(cdir, f"{cond['label']}_{seed}.json")
            cfg_path = os.path.join(cdir, f"{cond['label']}_{seed}.config")
            cfg = make_run_config(base_cfg, cond, seed, args.timesteps, log_path)
            with open(cfg_path, "w") as f:
                json.dump(cfg, f)
            all_runs.append((cond["label"], seed, cfg_path, log_path))

    pending = [
        run for run in all_runs
        if args.force or not is_complete(run[3], args.timesteps)
    ]

    total = len(all_runs)
    print(f"  Total: {total}  |  Queued: {len(pending)}  |  Skipped: {total - len(pending)}\n")

    session_durations = {}
    if pending:
        t_start = time.time()
        manager = multiprocessing.Manager()
        counter = manager.Value("i", 0)
        lock    = manager.Lock()
        worker_args = [
            (cfg_path, args.python, counter, lock, len(pending))
            for (_, _, cfg_path, _) in pending
        ]
        print(f"  Running {len(pending)} simulations on {num_cores} core(s) ...")
        with multiprocessing.Pool(processes=num_cores) as pool:
            results = pool.map(run_one_simulation, worker_args)
        session_durations = {path: dur for path, dur in results}
        print(f"\n\n  Completed in {time.time() - t_start:.1f}s\n")

    # Parse logs and collect results
    print("  Parsing logs ...")
    all_pts        = []
    all_summaries  = []
    cond_summaries = {c["label"]: [] for c in selected}

    for (label, seed, cfg_path, log_path) in all_runs:
        dur = session_durations.get(cfg_path, 0.0)
        pts, summary = parse_sim_log(log_path, label, seed, dur)
        if pts is None:
            print(f"  [warn] No data for {label} seed={seed}")
            continue
        all_pts.extend(pts)
        all_summaries.append(summary)
        cond_summaries[label].append(summary)

    # Write combined CSVs
    write_csv(all_pts,      os.path.join(results_dir, "per_timestep.csv"))
    write_csv(all_summaries, os.path.join(results_dir, "per_seed_summary.csv"))

    agg_rows = [aggregate_seeds(s) for s in cond_summaries.values() if s]
    write_csv(agg_rows, os.path.join(results_dir, "condition_aggregates.csv"))

    # Write per-condition subdirs
    for cond in selected:
        label = cond["label"]
        cd = os.path.join(results_dir, label)
        os.makedirs(cd, exist_ok=True)
        write_csv([r for r in all_pts      if r["condition"] == label], os.path.join(cd, "per_timestep.csv"))
        write_csv([r for r in all_summaries if r["condition"] == label], os.path.join(cd, "per_seed_summary.csv"))
        write_csv([r for r in agg_rows     if r.get("condition") == label], os.path.join(cd, "condition_aggregates.csv"))

    if args.delete_logs:
        for (_, _, cfg_path, log_path) in all_runs:
            for p in (log_path, cfg_path):
                if p and os.path.exists(p):
                    os.remove(p)

    # Print summary table
    print(f"\n{'='*72}")
    print(f"  {'Condition':<28} {'Seeds':>6} {'Extinct%':>9} {'FinalPop':>10} {'Gini':>7} {'TTL':>8}")
    print(f"  {'-'*70}")
    for row in agg_rows:
        print(f"  {row.get('condition','?'):<28} "
              f"{row.get('numSeeds', 0):>6} "
              f"{row.get('extinctionRate', 0) * 100:>8.1f}% "
              f"{row.get('mean_finalPopulation', 0):>10.1f} "
              f"{row.get('mean_finalGini', 0):>7.3f} "
              f"{row.get('mean_finalMeanTimeToLive', 0):>8.2f}")
    print(f"{'='*72}\n")
    print(f"  Results written to {results_dir}/\n")


if __name__ == "__main__":
    main()
