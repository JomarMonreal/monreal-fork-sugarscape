#!/usr/bin/env python3
"""
Generate GUI test configs for all 7 resource setups x 3 agent types = 21 files.
Uses test_gui_twopeak.json as the base template.

Run:  python3 generate_test_gui_configs.py
"""
import json
import math
import os

BASE_TEMPLATE = "test_gui_twopeak.json"
PROJECT_ROOT  = os.path.dirname(os.path.abspath(__file__))
FLAT_ENV_FILE = os.path.join(PROJECT_ROOT, "flat_environment.json")

AGENTS = [
    ("utilitarian", ["bentham"]),
    ("altruistic",  ["altruist"]),
    ("egoistic",    ["egoist"]),
]

def d_peaks(d):
    center = 25
    offset = round(d / math.sqrt(2))
    sugar = [
        [center - offset, center + offset, 4],
        [center + offset, center - offset, 4],
    ]
    spice = [
        [center - offset, center - offset, 4],
        [center + offset, center + offset, 4],
    ]
    return sugar, spice

SETUPS = [
    {
        "key":   "d14",
        "label": "Four-peak distributed (d=14)",
        "sugar": [[15, 35, 4], [35, 15, 4]],
        "spice": [[15, 15, 4], [35, 35, 4]],
        "env_file": None,
    },
    {
        "key":   "d7",
        "label": "Four-peak moderate (d=7)",
        "sugar": d_peaks(7)[0],
        "spice": d_peaks(7)[1],
        "env_file": None,
    },
    {
        "key":   "d0",
        "label": "One-peak concentrated (d=0)",
        "sugar": [[25, 25, 4]],
        "spice": [[25, 25, 4]],
        "env_file": None,
    },
    {
        "key":   "twopeak_colocated",
        "label": "Two-peak co-located (sugar and spice share same corners)",
        "sugar": [[15, 35, 4], [35, 15, 4]],
        "spice": [[15, 35, 4], [35, 15, 4]],
        "env_file": None,
    },
    {
        "key":   "twopeak_separated",
        "label": "Two-peak separated (sugar and spice at opposite corners, d=14)",
        "sugar": [[15, 35, 4]],
        "spice": [[35, 15, 4]],
        "env_file": None,
    },
    {
        "key":   "twopeak_separated_d7",
        "label": "Two-peak separated moderate (sugar and spice at opposite corners, d=7)",
        "sugar": [[20, 30, 4]],
        "spice": [[30, 20, 4]],
        "env_file": None,
    },
    {
        "key":   "flat",
        "label": "Flat (uniform, no peaks — requires flat_environment.json)",
        "sugar": [],
        "spice": [],
        "env_file": FLAT_ENV_FILE,
    },
]

def load_template():
    path = os.path.join(PROJECT_ROOT, BASE_TEMPLATE)
    with open(path) as f:
        return json.load(f)

def make_config(template, setup, agent_label, agent_models):
    cfg = dict(template)
    cfg["__README__"] = (
        f"{setup['label']} | {agent_label} agents. "
        f"Run with: python sugarscape.py --conf <this_file>"
    )
    cfg["agentDecisionModels"]   = agent_models
    cfg["environmentSugarPeaks"] = setup["sugar"]
    cfg["environmentSpicePeaks"] = setup["spice"]
    cfg["environmentFile"]       = setup["env_file"]
    cfg["headlessMode"]          = False
    return cfg

def main():
    template = load_template()
    created  = []

    for setup in SETUPS:
        for agent_label, agent_models in AGENTS:
            filename = f"test_gui_{setup['key']}_{agent_label}.json"
            path     = os.path.join(PROJECT_ROOT, filename)
            cfg      = make_config(template, setup, agent_label, agent_models)
            with open(path, "w") as f:
                json.dump(cfg, f, indent=2)
            created.append(filename)
            print(f"  wrote {filename}")

    print(f"\n  {len(created)} configs created.")
    if any(s["env_file"] for s in SETUPS):
        print(f"\n  NOTE: flat configs need flat_environment.json.")
        print(f"  Generate it first:  python3 run_flat.py --seeds 1 --timesteps 1")

if __name__ == "__main__":
    main()
