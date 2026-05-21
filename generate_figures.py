#!/usr/bin/env python3
"""
generate_figures.py  —  thesis visualization and statistical summary

Outputs (all saved under figures/ and data/)
--------------------------------------------
figures/01_population_timeseries.png
figures/02_societalWealth_timeseries.png
figures/03_giniCoefficient_timeseries.png
figures/04_meanTimeToLive_timeseries.png
figures/05_meanWealth_timeseries.png
figures/06_final_values_boxplot.png
figures/07_extinction_rate.png
figures/08_effect_size_gradient.png
figures/09_execution_time.png
data/descriptive_summary.csv
data/hypothesis_test_results.csv   (also printed to console)

Run:  .venv/bin/python3 generate_figures.py
"""

import csv
import math
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scikit_posthocs as sp
from scipy.stats import chi2_contingency, kruskal

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Configuration ──────────────────────────────────────────────────────────────

ROOT    = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(ROOT, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

CONFIGS = [
    {"label": "d=14  (distributed)",   "d": 14, "dir": "data/four_peak_results", "prefix": "four_peak"},
    {"label": "d=7   (intermediate)",  "d":  7, "dir": "data/d_sweep_results",   "prefix": "d07"},
    {"label": "d=0   (concentrated)",  "d":  0, "dir": "data/one_peak_results",  "prefix": "one_peak"},
]

AGENT_TYPES = ["utilitarian", "altruistic", "egoistic"]

COLORS = {
    "utilitarian": "#2166ac",
    "altruistic":  "#4dac26",
    "egoistic":    "#d7191c",
}

LINESTYLES = {
    "utilitarian": "-",
    "altruistic":  "--",
    "egoistic":    ":",
}

TS_METRICS = [
    ("population",      "Population"),
    ("societalWealth",  "Societal Wealth"),
    ("giniCoefficient", "Gini Coefficient"),
    ("meanTimeToLive",  "Mean Time to Live (timesteps)"),
    ("meanWealth",      "Mean Agent Wealth"),
]

FINAL_METRICS = [
    ("finalPopulation",     "Final Population"),
    ("finalSocietalWealth", "Final Societal Wealth"),
    ("finalGini",           "Final Gini Coefficient"),
    ("finalMeanTimeToLive", "Final Mean Time to Live"),
    ("finalMeanWealth",     "Final Mean Agent Wealth"),
]

ALPHA = 0.05


# ── Helpers ────────────────────────────────────────────────────────────────────

def cond(prefix, agent):
    return f"{prefix}_{agent}"


def sig_label(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < ALPHA: return "*"
    return "ns"


def effect_label(eta2):
    if math.isnan(eta2): return "n/a"
    if eta2 < 0.01:  return "negligible"
    if eta2 < 0.06:  return "small"
    if eta2 < 0.14:  return "medium"
    return "large"


def eta_squared_h(H, k, n):
    if n <= k:
        return float("nan")
    return max(0.0, (H - k + 1) / (n - k))


def set_style():
    plt.rcParams.update({
        "figure.dpi":        150,
        "savefig.dpi":       300,
        "font.size":         9,
        "axes.titlesize":    9,
        "axes.labelsize":    8,
        "legend.fontsize":   8,
        "xtick.labelsize":   7,
        "ytick.labelsize":   7,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.grid":         True,
        "grid.alpha":        0.3,
    })


# ── Data Loading ───────────────────────────────────────────────────────────────

def load_csv(name):
    """Load one CSV type from all three result directories, tag with d value."""
    frames = []
    for cfg in CONFIGS:
        path = os.path.join(ROOT, cfg["dir"], name)
        if not os.path.exists(path):
            print(f"  [skip] {path}")
            continue
        df = pd.read_csv(path)
        df["d"] = cfg["d"]
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ── Figure 1–4: Timestep Trajectories ─────────────────────────────────────────

def plot_timeseries(ts_df):
    if ts_df.empty:
        print("[SKIP] No per-timestep data.")
        return

    legend_handles = [
        mpatches.Patch(color=COLORS[a], label=a.capitalize())
        for a in AGENT_TYPES
    ]

    for fig_num, (col, ylabel) in enumerate(TS_METRICS, start=1):
        if col not in ts_df.columns:
            continue

        fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), sharey=False)
        fig.suptitle(f"{ylabel} Over Time  (mean ± 1 SD across seeds)",
                     fontsize=10, fontweight="bold")

        for ax, cfg in zip(axes, CONFIGS):
            sub = ts_df[ts_df["d"] == cfg["d"]]
            for agent in AGENT_TYPES:
                grp = sub[sub["condition"] == cond(cfg["prefix"], agent)]
                if grp.empty:
                    continue
                agg = (grp.groupby("timestep")[col]
                         .agg(["mean", "std"])
                         .reset_index())
                agg["std"] = agg["std"].fillna(0)
                ax.plot(
                    agg["timestep"], agg["mean"],
                    color=COLORS[agent], ls=LINESTYLES[agent],
                    linewidth=1.4, label=agent.capitalize(),
                )
                ax.fill_between(
                    agg["timestep"],
                    (agg["mean"] - agg["std"]).clip(lower=0),
                    agg["mean"] + agg["std"],
                    color=COLORS[agent], alpha=0.15,
                )
            ax.set_title(cfg["label"])
            ax.set_xlabel("Timestep")
            if ax is axes[0]:
                ax.set_ylabel(ylabel)

        axes[-1].legend(handles=legend_handles, loc="upper right")
        fig.tight_layout()
        out = os.path.join(FIG_DIR, f"0{fig_num}_{col}_timeseries.png")
        fig.savefig(out, bbox_inches="tight")
        plt.close(fig)
        print(f"  Saved: {out}")


# ── Figure 5: Final Value Box Plots ───────────────────────────────────────────

def plot_final_boxplots(seed_df):
    if seed_df.empty:
        print("[SKIP] No per-seed data for box plots.")
        return

    d_vals   = [14, 7, 0]
    x_pos    = np.arange(len(d_vals))
    width    = 0.22
    x_labels = ["d=14\n(distributed)", "d=7\n(intermediate)", "d=0\n(concentrated)"]

    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    axes = axes.flatten()
    fig.suptitle("Final Outcome Distributions by Condition",
                 fontsize=11, fontweight="bold")

    for ax, (col, title) in zip(axes, FINAL_METRICS):
        if col not in seed_df.columns:
            continue
        bp_data, bp_pos, bp_colors = [], [], []

        for i, d in enumerate(d_vals):
            cfg = next(c for c in CONFIGS if c["d"] == d)
            for j, agent in enumerate(AGENT_TYPES):
                vals = seed_df[seed_df["condition"] == cond(cfg["prefix"], agent)][col].dropna().values
                if len(vals) == 0:
                    continue
                bp_data.append(vals)
                bp_pos.append(x_pos[i] + (j - 1) * width)
                bp_colors.append(COLORS[agent])

        if not bp_data:
            continue

        bp = ax.boxplot(
            bp_data, positions=bp_pos, widths=width * 0.85,
            patch_artist=True,
            medianprops={"color": "black", "linewidth": 1.5},
            whiskerprops={"linewidth": 0.8},
            capprops={"linewidth": 0.8},
            flierprops={"markersize": 2, "alpha": 0.5},
        )
        for patch, color in zip(bp["boxes"], bp_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels)
        ax.set_title(title)
        ax.set_xlabel("Resource Configuration")

    legend_handles = [
        mpatches.Patch(facecolor=COLORS[a], alpha=0.7, label=a.capitalize())
        for a in AGENT_TYPES
    ]
    axes[-1].legend(handles=legend_handles, loc="best")
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "06_final_values_boxplot.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ── Figure 6: Extinction Rate ──────────────────────────────────────────────────

def plot_extinction_rate(seed_df):
    if seed_df.empty or "extinct" not in seed_df.columns:
        print("[SKIP] No extinction data.")
        return

    d_vals   = [14, 7, 0]
    x_labels = ["d=14\n(distributed)", "d=7\n(intermediate)", "d=0\n(concentrated)"]
    x_pos    = np.arange(len(d_vals))
    width    = 0.22

    fig, ax = plt.subplots(figsize=(7, 4))
    for j, agent in enumerate(AGENT_TYPES):
        rates = []
        for d in d_vals:
            cfg = next(c for c in CONFIGS if c["d"] == d)
            sub = seed_df[seed_df["condition"] == cond(cfg["prefix"], agent)]
            rates.append(sub["extinct"].sum() / len(sub) * 100 if len(sub) > 0 else 0)
        ax.bar(
            x_pos + (j - 1) * width, rates,
            width=width, label=agent.capitalize(),
            color=COLORS[agent], alpha=0.8, edgecolor="white",
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("Extinction Rate (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Extinction Rate by Condition and Agent Type", fontweight="bold")
    ax.legend()
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "07_extinction_rate.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ── Figure 7: Effect Size Gradient (H2 visualization) ─────────────────────────

def plot_effect_size_gradient(seed_df):
    if seed_df.empty:
        print("[SKIP] No data for effect size gradient plot.")
        return

    d_vals = [0, 7, 14]
    fig, axes = plt.subplots(1, 5, figsize=(16, 4))
    fig.suptitle(r"Effect Size ($\eta^2_H$) vs. Peak Distance $d$  (RQ4)",
                 fontsize=10, fontweight="bold")

    threshold_lines = [
        (0.01, "#aaaaaa", "small (0.01)"),
        (0.06, "#777777", "medium (0.06)"),
        (0.14, "#444444", "large (0.14)"),
    ]

    for ax, (col, label) in zip(axes, FINAL_METRICS):
        eta2_vals, p_vals = [], []
        for d in d_vals:
            cfg    = next(c for c in CONFIGS if c["d"] == d)
            groups = [
                seed_df[seed_df["condition"] == cond(cfg["prefix"], a)][col].dropna().values
                for a in AGENT_TYPES
            ]
            valid = [g for g in groups if len(g) >= 3]
            if len(valid) < 2:
                eta2_vals.append(float("nan"))
                p_vals.append(float("nan"))
                continue
            try:
                H, p = kruskal(*valid)
                n    = sum(len(g) for g in valid)
                eta2_vals.append(eta_squared_h(H, len(valid), n))
                p_vals.append(p)
            except Exception:
                eta2_vals.append(float("nan"))
                p_vals.append(float("nan"))

        ax.plot(d_vals, eta2_vals, "o-", color="#1a1a1a", linewidth=1.8,
                markersize=6, zorder=5)

        # Annotate significance on each point
        for d, eta2, p in zip(d_vals, eta2_vals, p_vals):
            if not math.isnan(p):
                ax.annotate(sig_label(p), xy=(d, eta2),
                            xytext=(0, 6), textcoords="offset points",
                            ha="center", fontsize=7, color="#333333")

        for thresh, color, lbl in threshold_lines:
            ax.axhline(thresh, color=color, ls="--", linewidth=0.8, label=lbl)

        ax.set_xticks(d_vals)
        ax.set_xticklabels(["d=0", "d=7", "d=14"])
        ax.set_xlabel("Peak Distance (d)")
        ax.set_title(label, fontsize=8)
        ax.set_ylim(bottom=0)
        if ax is axes[0]:
            ax.set_ylabel(r"$\eta^2_H$")
            ax.legend(fontsize=6, loc="upper left")

    fig.tight_layout()
    out = os.path.join(FIG_DIR, "08_effect_size_gradient.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ── Figure 8: Execution Time ───────────────────────────────────────────────────

def plot_execution_time(seed_df):
    if seed_df.empty or "executionTime" not in seed_df.columns:
        print("[SKIP] No execution time data.")
        return

    bp_data, bp_labels, bp_colors = [], [], []
    for cfg in CONFIGS:
        for agent in AGENT_TYPES:
            vals = seed_df[seed_df["condition"] == cond(cfg["prefix"], agent)]["executionTime"].dropna().values
            if len(vals) == 0:
                continue
            bp_data.append(vals)
            bp_labels.append(f"d={cfg['d']}\n{agent[:3].capitalize()}")
            bp_colors.append(COLORS[agent])

    if not bp_data:
        return

    fig, ax = plt.subplots(figsize=(10, 4))
    bp = ax.boxplot(
        bp_data, patch_artist=True,
        medianprops={"color": "black", "linewidth": 1.5},
        flierprops={"markersize": 2, "alpha": 0.4},
    )
    for patch, color in zip(bp["boxes"], bp_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticks(range(1, len(bp_labels) + 1))
    ax.set_xticklabels(bp_labels, fontsize=7)
    ax.set_ylabel("Wall-clock time (s)")
    ax.set_title("Execution Time per Simulation Run", fontweight="bold")
    legend_handles = [
        mpatches.Patch(facecolor=COLORS[a], alpha=0.7, label=a.capitalize())
        for a in AGENT_TYPES
    ]
    ax.legend(handles=legend_handles)
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "09_execution_time.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")


# ── Runtime Summary CSV ────────────────────────────────────────────────────────

def save_runtime_table(seed_df):
    """Save mean/SD/median/IQR of executionTime per condition to data/runtime_summary.csv."""
    if seed_df.empty or "executionTime" not in seed_df.columns:
        print("[SKIP] No executionTime data for runtime table.")
        return

    rows = []
    for cfg in CONFIGS:
        for agent in AGENT_TYPES:
            vals = seed_df[seed_df["condition"] == cond(cfg["prefix"], agent)]["executionTime"].dropna()
            if vals.empty:
                continue
            rows.append({
                "config":     cfg["label"].strip(),
                "model":      agent.capitalize(),
                "mean_s":     round(vals.mean(),                              3),
                "sd_s":       round(vals.std(),                               3),
                "median_s":   round(vals.median(),                            3),
                "iqr_s":      round(vals.quantile(0.75) - vals.quantile(0.25), 3),
            })

    if not rows:
        return
    out = os.path.join(ROOT, "data", "runtime_summary.csv")
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {out}")


# ── Descriptive Summary CSV ────────────────────────────────────────────────────

def save_descriptive_table(seed_df):
    if seed_df.empty:
        return
    rows = []
    for cfg in CONFIGS:
        for agent in AGENT_TYPES:
            sub = seed_df[seed_df["condition"] == cond(cfg["prefix"], agent)]
            if sub.empty:
                continue
            row = {
                "d":         cfg["d"],
                "config":    cfg["label"].strip(),
                "agent":     agent,
                "n":         len(sub),
            }
            if "extinct" in sub.columns:
                row["extinction_rate_%"] = round(sub["extinct"].sum() / len(sub) * 100, 1)
            for col, _ in FINAL_METRICS:
                if col not in sub.columns:
                    continue
                v = sub[col].dropna()
                row[col + "_mean"]   = round(v.mean(),          3)
                row[col + "_sd"]     = round(v.std(),           3)
                row[col + "_median"] = round(v.median(),        3)
                row[col + "_iqr"]    = round(v.quantile(0.75) - v.quantile(0.25), 3)
            rows.append(row)

    if not rows:
        return
    out = os.path.join(ROOT, "data", "descriptive_summary.csv")
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved: {out}")


# ── Statistical Tests ──────────────────────────────────────────────────────────

def run_statistics(seed_df):
    if seed_df.empty:
        print("[SKIP] No data for statistical tests.")
        return

    all_rows = []

    for cfg in CONFIGS:
        present = [cond(cfg["prefix"], a) for a in AGENT_TYPES
                   if cond(cfg["prefix"], a) in seed_df["condition"].values]
        if len(present) < 2:
            continue

        k  = len(present)
        ns = {l: len(seed_df[seed_df["condition"] == l]) for l in present}
        n_str = ", ".join(f"{l.split('_')[-1]}={ns[l]}" for l in present)

        print(f"\n{'='*70}")
        print(f"  {cfg['label'].strip().upper()}")
        print(f"  n per group: {n_str}")
        print(f"{'='*70}")

        for col, metric_label in FINAL_METRICS:
            if col not in seed_df.columns:
                continue
            samples = [seed_df[seed_df["condition"] == l][col].dropna().to_numpy()
                       for l in present]
            if any(len(s) < 3 for s in samples):
                continue

            n    = sum(len(s) for s in samples)
            H, p = kruskal(*samples)
            eta2 = eta_squared_h(H, k, n)

            print(f"\n  {metric_label}")
            print(f"  {'Group':<16} {'Median':>9}  {'IQR':>18}")
            print(f"  {'-'*46}")
            for lbl, s in zip(present, samples):
                short = lbl.split("_")[-1].capitalize()
                med   = np.median(s)
                q1, q3 = np.percentile(s, [25, 75])
                print(f"  {short:<16} {med:>9.2f}  [{q1:.2f}, {q3:.2f}]")

            print(f"\n  KW: H={H:.3f},  p={p:.4f} {sig_label(p)},  "
                  f"eta2_H={eta2:.3f} ({effect_label(eta2)})")

            if p < ALPHA:
                group_labels = [l.split("_")[-1] for l in present]
                melted = pd.DataFrame({
                    "val":   np.concatenate(samples),
                    "group": np.repeat(group_labels, [len(s) for s in samples]),
                })
                dunn = sp.posthoc_dunn(
                    melted, val_col="val", group_col="group", p_adjust="bonferroni"
                )
                idx = dunn.index.tolist()
                print("  Post-hoc Dunn (Bonferroni):")
                for i in range(len(idx)):
                    for j in range(i + 1, len(idx)):
                        pv = dunn.loc[idx[i], idx[j]]
                        print(f"    {idx[i].capitalize()} vs {idx[j].capitalize()}: "
                              f"p={pv:.4f} {sig_label(pv)}")

            all_rows.append({
                "d":      cfg["d"],
                "config": cfg["label"].strip(),
                "metric": col,
                "H":      round(H, 3),
                "p":      round(p, 4),
                "sig":    sig_label(p),
                "eta2_H": round(eta2, 3),
                "effect": effect_label(eta2),
            })

        # Extinction rate — chi-square
        if "extinct" in seed_df.columns:
            table = [
                [int((seed_df[(seed_df["condition"] == l) & seed_df["extinct"]]).shape[0]),
                 int((seed_df[(seed_df["condition"] == l) & ~seed_df["extinct"]]).shape[0])]
                for l in present
            ]
            try:
                chi2, p_chi, dof, expected = chi2_contingency(table)
                min_expected = expected.min()
                print(f"\n  Extinction Rate  (chi-square, df={dof}, "
                      f"min expected cell={min_expected:.1f})")
                print(f"  {'Group':<16} {'Extinct/Total':>14}  {'Rate':>8}")
                print(f"  {'-'*42}")
                for lbl, row in zip(present, table):
                    short = lbl.split("_")[-1].capitalize()
                    total = row[0] + row[1]
                    rate  = row[0] / total * 100 if total > 0 else float("nan")
                    print(f"  {short:<16} {row[0]:>5}/{total:<8}  {rate:>7.1f}%")
                print(f"\n  chi2={chi2:.3f},  p={p_chi:.4f} {sig_label(p_chi)}")
                all_rows.append({
                    "d":      cfg["d"],
                    "config": cfg["label"].strip(),
                    "metric": "extinctionRate",
                    "H":      round(chi2, 3),
                    "p":      round(p_chi, 4),
                    "sig":    sig_label(p_chi),
                    "eta2_H": float("nan"),
                    "effect": "n/a",
                })
            except Exception as exc:
                print(f"  [warn] chi-square failed: {exc}")

    if all_rows:
        out = os.path.join(ROOT, "data", "hypothesis_test_results.csv")
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n  Statistical results saved to {out}")

    print("\nSig. codes:  *** p<0.001   ** p<0.01   * p<0.05   ns = not significant")
    print("eta2_H:  <0.01 negligible  /  0.01 small  /  0.06 medium  /  0.14 large\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    set_style()

    print("Loading data ...")
    ts_df   = load_csv("per_timestep.csv")
    seed_df = load_csv("per_seed_summary.csv")

    if ts_df.empty and seed_df.empty:
        print("No data found. Run simulations first:\n"
              "  python run_four_peak.py\n"
              "  python run_d_sweep.py --distances 7\n"
              "  python run_one_peak.py")
        return

    print(f"  per_timestep rows : {len(ts_df):,}")
    print(f"  per_seed rows     : {len(seed_df):,}")

    print(f"\nGenerating figures → {FIG_DIR}/")
    plot_timeseries(ts_df)
    plot_final_boxplots(seed_df)
    plot_extinction_rate(seed_df)
    plot_effect_size_gradient(seed_df)
    plot_execution_time(seed_df)

    print("\nSaving descriptive summary ...")
    save_descriptive_table(seed_df)
    save_runtime_table(seed_df)

    print("\nRunning statistical tests ...")
    run_statistics(seed_df)

    print("Done.")
    print(f"  figures/                         — 9 PNGs (300 dpi)")
    print(f"  data/descriptive_summary.csv     — mean, SD, median, IQR per condition")
    print(f"  data/runtime_summary.csv         — execution time stats per condition (Table 7)")
    print(f"  data/hypothesis_test_results.csv — KW + Dunn + eta2_H + chi-square")


if __name__ == "__main__":
    main()
