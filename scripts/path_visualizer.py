import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_role_state_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def role_state_to_dataframe(role_state_data):
    records = []
    for chapter_id, role_states in role_state_data.items():
        for role, states in role_states.items():
            for state in states:
                records.append({
                    "Chapter": chapter_id,
                    "Role": role,
                    "State": state
                })
    return pd.DataFrame(records)

def plot_role_state_heatmap(df, output_path="state_heatmap.png"):
    heatmap_data = df.groupby(["Chapter", "State"]).size().unstack(fill_value=0)
    plt.figure(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="YlGnBu", annot=True, fmt="d")
    plt.title("State Frequency per Chapter")
    plt.ylabel("Chapter")
    plt.xlabel("State")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"✅ 热力图已保存：{output_path}")

def plot_state_trend_line(df, output_path="state_trend.png"):
    trend = df.groupby("Chapter").size().reset_index(name="Total States")
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=trend, x="Chapter", y="Total States", marker="o")
    plt.title("Total States per Chapter")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"✅ 趋势图已保存：{output_path}")

# 示例调用
if __name__ == "__main__":
    version_dir = "output/monte_灰姑娘_T07"  # 可修改为任意版本目录
    input_file = os.path.join(version_dir, "role_state.json")

    if os.path.exists(input_file):
        role_state = load_role_state_json(input_file)
        df = role_state_to_dataframe(role_state)
        plot_role_state_heatmap(df, os.path.join(version_dir, "state_heatmap.png"))
        plot_state_trend_line(df, os.path.join(version_dir, "state_trend.png"))
    else:
        print(f"❌ 未找到文件：{input_file}")
