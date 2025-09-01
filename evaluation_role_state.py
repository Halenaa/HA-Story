# 代码需要调整，把csv,md还有热力图放一起了
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def convert_role_state_to_csv_and_md(base_dir):
    role_state_path = os.path.join(base_dir, "role_state.json")
    if not os.path.exists(role_state_path):
        print("未找到 role_state.json 文件")
        return

    with open(role_state_path, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    # === 1. 生成 CSV ===
    csv_rows = []
    for chapter, roles in state_data.items():
        chapter_num = chapter.replace("Chapter ", "")
        for role, states in roles.items():
            for state in states:
                csv_rows.append({
                    "Chapter": chapter_num,
                    "Role": role,
                    "State": state
                })
    df = pd.DataFrame(csv_rows)
    csv_path = os.path.join(base_dir, "role_state.csv")
    df.to_csv(csv_path, index=False)

    # === 2. 生成 Markdown 表格 ===
    all_roles = sorted({r for chap in state_data.values() for r in chap})
    md_lines = ["| Chapter | " + " | ".join(all_roles) + " |",
                "|---------|" + "|".join(["--------" for _ in all_roles]) + "|"]

    for chapter, roles in state_data.items():
        row = [chapter]
        for role in all_roles:
            row.append(", ".join(roles.get(role, [])))
        md_lines.append("| " + " | ".join(row) + " |")

    md_path = os.path.join(base_dir, "role_state.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"✅ 已生成：\n{csv_path}\n{md_path}")
    return csv_path, md_path

# 用法示例
# 替换成你的输出路径（如 output/test）
convert_role_state_to_csv_and_md("output/test")


# 示例调用结构
# result = update_plot_from_dialogue("Chapter 4", original_plot, dialogue_list, characters)
# print(result)


import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_character_state_heatmap(base_dir, save_fig=True):
    """
    将 role_state.json 转为热力图：角色 × 章节 × 状态数量
    """
    role_state_path = os.path.join(base_dir, "role_state.json")
    if not os.path.exists(role_state_path):
        print("❌ role_state.json 文件不存在")
        return

    with open(role_state_path, "r", encoding="utf-8") as f:
        state_data = json.load(f)

    # 组织成 DataFrame（每个单元格是状态数量）
    rows = []
    for chapter, roles in state_data.items():
        chapter_num = int(chapter.replace("Chapter ", ""))
        for role, states in roles.items():
            rows.append({
                "Chapter": chapter_num,
                "Role": role,
                "StateCount": len(states)
            })

    df = pd.DataFrame(rows)

    # 透视表
    pivot_df = df.pivot(index="Role", columns="Chapter", values="StateCount").fillna(0)

    # 绘图
    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot_df, annot=True, fmt=".0f", cmap="YlGnBu", cbar=True)
    plt.title("角色状态变化热力图")
    plt.xlabel("章节")
    plt.ylabel("角色")
    plt.tight_layout()

    if save_fig:
        fig_path = os.path.join(base_dir, "role_state_heatmap.png")
        plt.savefig(fig_path)
        print(f"热力图已保存为：{fig_path}")
    else:
        plt.show()

# 示例调用
plot_character_state_heatmap("output/test")

# ✅ 后续你可以：
# 用 seaborn 的 cmap 自定义风格（比如灰度、红蓝）

# 将热力图截图贴入论文

# 对多个模型或风格版本跑出多个热力图并比较

# 是否我也给你做个角色状态折线图（随章节演化趋势）？📈 可以看到角色在不同章节是否逐渐活跃/冷静/崩溃等趋势 ✅ 