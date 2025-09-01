import os
import json
import pandas as pd

def load_role_state_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def role_state_to_matrix(role_state_data):
    """
    将 role_state.json 转换为行为状态矩阵：行是章节，列是角色状态组合
    """
    records = []
    for chapter_id, role_states in role_state_data.items():
        for role, states in role_states.items():
            for state in states:
                records.append({
                    "Chapter": chapter_id,
                    "Role": role,
                    "State": state
                })

    df = pd.DataFrame(records)
    pivot = df.groupby(["Chapter", "Role", "State"]).size().reset_index(name="Count")
    matrix = pivot.pivot_table(index=["Chapter"], columns=["Role", "State"], values="Count", fill_value=0)
    return matrix

def save_matrix(matrix_df, output_dir="output", basename="role_path_matrix"):
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{basename}.csv")
    md_path = os.path.join(output_dir, f"{basename}.md")

    matrix_df.to_csv(csv_path)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(matrix_df.to_markdown())

    print(f"✅ 矩阵 CSV 保存至：{csv_path}")
    print(f"✅ Markdown 表格保存至：{md_path}")
    return matrix_df

# ✅ 示例用法（可作为主程序调用）
if __name__ == "__main__":
    version_dir = "data/output/exp_小红帽_科幻改写"  # 可以替换为其他版本
    input_file = os.path.join(version_dir, "role_state.json")
    
    if os.path.exists(input_file):
        role_state_data = load_role_state_json(input_file)
        matrix = role_state_to_matrix(role_state_data)
        save_matrix(matrix, output_dir=version_dir)
    else:
        print(f"❌ 未找到 role_state.json：{input_file}")
