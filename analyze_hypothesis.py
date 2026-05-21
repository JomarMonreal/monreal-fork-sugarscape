#!/usr/bin/env python3
"""
Hypothesis test: do agent types differ in societal outcomes across resource configurations?

H1 (four-peak, distributed):    utilitarian / altruistic / egoistic produce
                                 significantly different outcomes.
H2 (one-peak, concentrated):    no significant difference between agent types
                                 (all models collapse equally under peak pressure).

Tests used:
  - Kruskal-Wallis H  : non-parametric one-way comparison of 3 independent groups
  - Post-hoc Dunn     : pairwise follow-up (Bonferroni-corrected) when KW is significant
  - Effect size eta^2 : (H - k + 1) / (n - k)  [Tomczak & Tomczak, 2014]
  - Chi-square        : for binary extinction rate

Run with the project venv:
  .venv/bin/python3 analyze_hypothesis.py
"""

import csv
import math
import os

import numpy as np
import pandas as pd
import scikit_posthocs as sp
from scipy.stats import chi2_contingency, kruskal

ALPHA = 0.05

CONFIGS = {
    "four_peak (d=14)": {
        "csv":    "data/four_peak_results/per_seed_summary.csv",
        "prefix": "four_peak",
    },
    "d=7 (intermediate)": {
        "csv":    "data/d_sweep_results/per_seed_summary.csv",
        "prefix": "d07",
    },
    "one_peak (d=0)": {
        "csv":    "data/one_peak_results/per_seed_summary.csv",
        "prefix": "one_peak",
    },
}

AGENT_TYPES = ["utilitarian", "altruistic", "egoistic"]

METRICS = [
    ("finalPopulation",     "Final Population"),
    ("finalSocietalWealth", "Societal Wealth"),
    ("finalGini",           "Gini Coefficient"),
    ("finalMeanTimeToLive", "Mean Time to Live"),
]


def sig_label(p):
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < ALPHA:
        return "*"
    return "ns"


def effect_label(eta2):
    if math.isnan(eta2):
        return "n/a"
    if eta2 < 0.01:
        return "negligible"
    if eta2 < 0.06:
        return "small"
    if eta2 < 0.14:
        return "medium"
    return "large"


def eta_squared_h(H, k, n):
    if n <= k:
        return float("nan")
    return max(0.0, (H - k + 1) / (n - k))


def iqr_string(arr):
    q1  = np.percentile(arr, 25)
    med = np.percentile(arr, 50)
    q3  = np.percentile(arr, 75)
    return med, f"[{q1:.2f}, {q3:.2f}]"


def analyze(config_name, config, project_root):
    csv_path = os.path.join(project_root, config["csv"])
    if not os.path.exists(csv_path):
        print(f"\n[SKIP] {config_name}: data not found at {csv_path}")
        return []

    df   = pd.read_csv(csv_path)
    pfx  = config["prefix"]
    lbls = [f"{pfx}_{a}" for a in AGENT_TYPES]

    present = [l for l in lbls if l in df["condition"].values]
    if len(present) < 2:
        print(f"\n[SKIP] {config_name}: fewer than 2 agent-type groups in data")
        return []

    k = len(present)
    print(f"\n{'='*72}")
    print(f"  {config_name.upper().replace('_', ' ')}  "
          f"({' / '.join(l.split('_')[-1].capitalize() for l in present)})")
    ns = {l: len(df[df["condition"] == l]) for l in present}
    n_summary = ", ".join(f"{l.split('_')[-1]}={ns[l]}" for l in present)
    print(f"  n per group: {n_summary}")
    print(f"{'='*72}")

    rows = []

    for col, label in METRICS:
        if col not in df.columns:
            continue
        samples = [df[df["condition"] == l][col].dropna().to_numpy()
                   for l in present]
        if any(len(s) < 3 for s in samples):
            continue

        n    = sum(len(s) for s in samples)
        H, p = kruskal(*samples)
        eta2 = eta_squared_h(H, k, n)

        print(f"\n  {label}")
        print(f"  {'Group':<18} {'Median':>9}  {'IQR':>20}")
        print(f"  {'-'*52}")
        for lbl, s in zip(present, samples):
            short     = lbl.split("_")[-1].capitalize()
            med, iqrs = iqr_string(s)
            print(f"  {short:<18} {med:>9.2f}  {iqrs:>20}")
        print(f"\n  Kruskal-Wallis: H={H:.3f},  p={p:.4f} {sig_label(p)},  "
              f"η²={eta2:.3f} ({effect_label(eta2)})")

        if p < ALPHA:
            group_labels = [l.split("_")[-1] for l in present]
            melted = pd.DataFrame({
                "val":   np.concatenate(samples),
                "group": np.repeat(group_labels, [len(s) for s in samples]),
            })
            dunn = sp.posthoc_dunn(
                melted, val_col="val", group_col="group", p_adjust="bonferroni"
            )
            print(f"  Post-hoc Dunn (Bonferroni):")
            idx = dunn.index.tolist()
            for i in range(len(idx)):
                for j in range(i + 1, len(idx)):
                    pv = dunn.loc[idx[i], idx[j]]
                    print(f"    {idx[i].capitalize()} vs {idx[j].capitalize()}: "
                          f"p={pv:.4f} {sig_label(pv)}")

        rows.append({
            "config":  config_name,
            "metric":  col,
            "H":       round(H, 3),
            "p":       round(p, 4),
            "sig":     sig_label(p),
            "eta2":    round(eta2, 3),
            "effect":  effect_label(eta2),
        })

    if "extinct" in df.columns:
        table = [
            [int((df[(df["condition"] == l) & (df["extinct"] == True)]).shape[0]),
             int((df[(df["condition"] == l) & (df["extinct"] == False)]).shape[0])]
            for l in present
        ]
        chi2, p_chi, dof, _ = chi2_contingency(table)
        print(f"\n  Extinction Rate (chi-square, df={dof})")
        print(f"  {'Group':<18} {'Extinct/Total':>14}  {'Rate':>8}")
        print(f"  {'-'*44}")
        for lbl, row in zip(present, table):
            short = lbl.split("_")[-1].capitalize()
            total = row[0] + row[1]
            rate  = row[0] / total * 100 if total > 0 else float("nan")
            print(f"  {short:<18} {row[0]:>5}/{total:<8}  {rate:>7.1f}%")
        print(f"\n  χ²={chi2:.3f},  p={p_chi:.4f} {sig_label(p_chi)}")
        rows.append({
            "config":  config_name,
            "metric":  "extinctionRate",
            "H":       round(chi2, 3),
            "p":       round(p_chi, 4),
            "sig":     sig_label(p_chi),
            "eta2":    float("nan"),
            "effect":  "n/a",
        })

    return rows


def main():
    root     = os.path.dirname(os.path.abspath(__file__))
    all_rows = []

    for name, cfg in CONFIGS.items():
        r = analyze(name, cfg, root)
        all_rows.extend(r)

    if all_rows:
        out = os.path.join(root, "data", "hypothesis_test_results.csv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n{'='*72}")
        print(f"  Full results saved to  {out}")

    print("\nSig. codes: *** p<0.001  ** p<0.01  * p<0.05  ns = not significant")
    print("Effect size η² (Kruskal-Wallis): <0.01 negligible / 0.01 small / "
          "0.06 medium / 0.14 large\n")


if __name__ == "__main__":
    main()
