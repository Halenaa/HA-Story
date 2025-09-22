import os
import json
import pandas as pd
from typing import List
from glob import glob
from collections import defaultdict
import ace_tools as tools

def extract_anchor_path(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        anchors = json.load(f)
    path = defaultdict(list)
    for anchor in anchors:
        chapter = anchor.get("chapter_id", "Unknown")
        anchor_type = anchor.get("type", "Unknown")
        path[chapter].append(anchor_type)
    return path

def build_prompt_tree_matrix(input_dir):
    pattern = os.path.join(input_dir, "*_functional.json")
    files = sorted(glob(pattern))
    all_data = {}

    for file in files:
        version = os.path.basename(file).replace("_functional.json", "")
        anchor_path = extract_anchor_path(file)
        flat_dict = {}
        for ch, types in anchor_path.items():
            flat_dict[ch] = " / ".join(types)
        all_data[version] = flat_dict

    df = pd.DataFrame(all_data).fillna("")
    return df

# Example call (please replace with your output path)
output_dir = "output"
tree_df = build_prompt_tree_matrix(output_dir)
tools.display_dataframe_to_user(name="Prompt Tree Anchor Matrix", dataframe=tree_df)
