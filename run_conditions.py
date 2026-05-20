import json
import os
import subprocess
import sys

BASE_CONFIG = "config.json"
PYTHON = "python"

FOUR_PEAK_SUGAR = [[15, 35, 4], [35, 15, 4]]
FOUR_PEAK_SPICE = [[15, 15, 4], [35, 35, 4]]
ONE_PEAK_SUGAR  = [[25, 25, 4]]
ONE_PEAK_SPICE  = [[25, 25, 4]]

CONDITIONS = [
    {"id": 1, "label": "four_peak_utilitarian", "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE, "model": "bentham"},
    {"id": 2, "label": "four_peak_altruistic",  "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE, "model": "altruist"},
    {"id": 3, "label": "four_peak_egoistic",    "sugar_peaks": FOUR_PEAK_SUGAR, "spice_peaks": FOUR_PEAK_SPICE, "model": "egoist"},
    {"id": 4, "label": "one_peak_utilitarian",  "sugar_peaks": ONE_PEAK_SUGAR,  "spice_peaks": ONE_PEAK_SPICE,  "model": "bentham"},
    {"id": 5, "label": "one_peak_altruistic",   "sugar_peaks": ONE_PEAK_SUGAR,  "spice_peaks": ONE_PEAK_SPICE,  "model": "altruist"},
    {"id": 6, "label": "one_peak_egoistic",     "sugar_peaks": ONE_PEAK_SUGAR,  "spice_peaks": ONE_PEAK_SPICE,  "model": "egoist"},
]

def load_base_config():
    with open(BASE_CONFIG) as f:
        return json.load(f)

def build_condition_config(base, condition):
    config = json.loads(json.dumps(base))
    config["sugarscapeOptions"]["environmentSugarPeaks"] = condition["sugar_peaks"]
    config["sugarscapeOptions"]["environmentSpicePeaks"] = condition["spice_peaks"]
    config["dataCollectionOptions"]["decisionModels"] = [[condition["model"]]]
    return config

def run_condition(condition, base_config):
    cid = condition["id"]
    label = condition["label"]
    output_dir = os.path.join("data", label)
    config_path = f"condition{cid}.json"

    os.makedirs(output_dir, exist_ok=True)

    config = build_condition_config(base_config, condition)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    print(f"\n--- Condition {cid}: {label} ---")
    result = subprocess.run(
        [PYTHON, "data/run.py", "--conf", config_path, "--path", output_dir + "/", "--mode", "csv"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    if result.returncode != 0:
        print(f"Condition {cid} failed with return code {result.returncode}.")
    else:
        print(f"Condition {cid} complete. Data saved to {output_dir}/")

    os.remove(config_path)

def parse_args():
    args = sys.argv[1:]
    if not args:
        return list(range(1, 7))
    try:
        ids = [int(a) for a in args]
        valid = [i for i in ids if 1 <= i <= 6]
        if not valid:
            print("Valid condition IDs are 1 through 6.")
            sys.exit(1)
        return valid
    except ValueError:
        print("Usage: python run_conditions.py [condition_ids...]")
        print("Example: python run_conditions.py 1 2 3")
        sys.exit(1)

if __name__ == "__main__":
    selected = parse_args()
    base = load_base_config()

    print(f"Running conditions: {selected}")
    print(f"Conditions 1-3 = four-peak baseline")
    print(f"Conditions 4-6 = single-peak treatment\n")

    for condition in CONDITIONS:
        if condition["id"] in selected:
            run_condition(condition, base)

    print("\nAll selected conditions complete.")
