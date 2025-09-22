import os
import json
import argparse
import pandas as pd
output_dir = "data/output"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_anchor_count(anchor_path):
    data = load_json(anchor_path)
    return len(data)

def compute_avg_states_per_role(role_state_path):
    data = load_json(role_state_path)
    role_count = {}
    total_states = {}

    for chapter in data.values():
        for role, states in chapter.items():
            role_count[role] = role_count.get(role, 0) + 1
            total_states[role] = total_states.get(role, 0) + len(states)

    avg_per_role = []
    for role in role_count:
        avg = total_states[role] / role_count[role]
        avg_per_role.append(avg)

    return round(sum(avg_per_role) / len(avg_per_role), 3) if avg_per_role else 0.0

def process_version(version):
    base_dir = os.path.join(output_dir, version)
    anchor_file = os.path.join(base_dir, "generated_anchors_dual_functional.json")
    role_state_file = os.path.join(base_dir, "role_state.json")

    if not os.path.exists(anchor_file) or not os.path.exists(role_state_file):
        print(f"WARNING: Missing file, skipping version: {version}")
        return None

    return {
        "version": version,
        "anchor_count": compute_anchor_count(anchor_file),
        "avg_states_per_role": compute_avg_states_per_role(role_state_file)
    }

def main(version_list, output_csv):
    records = []
    for version in version_list:
        result = process_version(version)
        if result:
            records.append(result)

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f" Metrics calculation completed, results saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--versions", type=str, required=True,
                        help="Comma-separated list of version names, e.g. demo1,demo2")
    parser.add_argument("--output", type=str, default="plot_metrics.csv",
                        help="Output CSV file path")

    args = parser.parse_args()
    version_list = [v.strip() for v in args.versions.split(",")]
    main(version_list, args.output)
