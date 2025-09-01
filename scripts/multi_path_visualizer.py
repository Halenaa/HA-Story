import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def load_role_state_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_trend_from_role_state(role_state_data, label=""):
    """
    统计每章的总状态数，并添加来源标签
    """
    records = []
    for chapter_id, role_states in role_state_data.items():
        total = sum(len(states) for states in role_states.values())
        records.append({
            "Chapter": chapter_id,
            "Total States": total,
            "Version": label
        })
    return pd.DataFrame(records)

def multi_version_trend_plot(version_dirs, labels, output_path="output/multi_state_trend.png"):
    all_trends = []

    for version_dir, label in zip(version_dirs, labels):
        role_state_path = os.path.join(version_dir, "role_state.json")
        if os.path.exists(role_state_path):
            role_state_data = load_role_state_json(role_state_path)
            trend_df = extract_trend_from_role_state(role_state_data, label)
            all_trends.append(trend_df)
        else:
            print(f"❌ 未找到文件：{role_state_path}")

    if not all_trends:
        print("❌ 没有可用的数据用于绘图。")
        return

    full_df = pd.concat(all_trends, ignore_index=True)

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=full_df, x="Chapter", y="Total States", hue="Version", marker="o")
    plt.title("State Count Trend Across Versions")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"✅ 多版本状态趋势图已保存：{output_path}")

# 示例调用
if __name__ == "__main__":
    version_dirs = [
        "output/monte_灰姑娘_T03",
        "output/monte_灰姑娘_T07",
        "output/monte_灰姑娘_T10"
    ]
    labels = ["T=0.3", "T=0.7", "T=1.0"]
    multi_version_trend_plot(version_dirs, labels)
