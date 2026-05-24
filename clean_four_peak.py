#!/usr/bin/env python3
"""
Remove four_peak_altruistic and four_peak_egoistic entries from
data/four_peak_results/ CSVs and subdirectories.

Usage:
  python3 clean_four_peak.py           # dry run (preview only)
  python3 clean_four_peak.py --apply   # actually delete/rewrite
"""
import argparse
import csv
import os
import shutil

ROOT        = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(ROOT, "data", "four_peak_results")
REMOVE_CONDS = {"four_peak_altruistic", "four_peak_egoistic"}

CSV_FILES = [
    "per_seed_summary.csv",
    "per_timestep.csv",
    "condition_aggregates.csv",
]


def filter_csv(path, apply):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    kept    = [r for r in rows if r.get("condition") not in REMOVE_CONDS]
    removed = len(rows) - len(kept)

    print(f"  {os.path.relpath(path, ROOT)}: {len(rows)} rows → {len(kept)} kept, {removed} removed")
    if apply and removed > 0:
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept)


def remove_subdir(path, apply):
    if os.path.isdir(path):
        print(f"  rmdir: {os.path.relpath(path, ROOT)}/")
        if apply:
            shutil.rmtree(path)
    else:
        print(f"  (not found, skip): {os.path.relpath(path, ROOT)}/")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true",
                   help="Actually apply deletions (default: dry run)")
    args = p.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\n{'='*60}")
    print(f"  clean_four_peak.py  [{mode}]")
    print(f"  Removing conditions: {', '.join(sorted(REMOVE_CONDS))}")
    print(f"{'='*60}\n")

    print("CSV files:")
    for fname in CSV_FILES:
        path = os.path.join(RESULTS_DIR, fname)
        if os.path.exists(path):
            filter_csv(path, args.apply)
        else:
            print(f"  (not found, skip): {fname}")

    print("\nSubdirectories:")
    for cond in sorted(REMOVE_CONDS):
        remove_subdir(os.path.join(RESULTS_DIR, cond), args.apply)

    print()
    if not args.apply:
        print("  --> Dry run complete. Run with --apply to make changes.\n")
    else:
        print("  --> Done.\n")


if __name__ == "__main__":
    main()
