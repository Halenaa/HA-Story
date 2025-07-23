import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==== 用户修改区：指定任务文件夹路径 ====
VERSION_DIRS = [
    "data/output/exp_小红帽_科幻改写",
    "data/output/exp_灰姑娘_现代改写",
    "data/output/exp_白雪公主_军事改写",
    "data/output/exp_青蛙王子_ABO改写"
]

OUTPUT_ROOT = "analysis_output"
os.makedirs(OUTPUT_ROOT, exist_ok=True)

def plot_state_trend(csv_path, version_name):
    df = pd.read_csv(csv_path, index_col=0)

    # 若为多层列，则合并为角色|状态形式
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["|".join(col).strip() for col in df.columns.values]

    df_reset = df.stack().reset_index()
    df_reset.columns = ["Chapter", "RoleState", "Count"]

    # 尝试分割为两列
    if df_reset["RoleState"].str.contains("|", regex=False).all():
        df_reset[["Role", "State"]] = df_reset["RoleState"].str.split("|", expand=True)
    else:
        # 如果没有分隔符，就把整列当作角色名，状态未知
        df_reset["Role"] = df_reset["RoleState"]
        df_reset["State"] = "Unknown"

    
    df_reset["Chapter_Num"] = (
        df_reset["Chapter"].str.extract("(\d+)")[0].astype("Int64")
    )
    df_reset = df_reset.dropna(subset=["Chapter_Num"])

    trend_data = (
        df_reset.groupby(["Chapter_Num", "Role"])
        .agg({"Count": "sum"})
        .reset_index()
    )

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=trend_data, x="Chapter_Num", y="Count", hue="Role", marker="o")
    plt.title(f"State Trend per Role – {version_name}")
    plt.xlabel("Chapter")
    plt.ylabel("Total States")
    plt.legend(title="Role", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    outpath = os.path.join(OUTPUT_ROOT, f"trend_{version_name}.png")
    plt.savefig(outpath)
    plt.close()

def plot_heatmap(csv_path, version_name):
    df = pd.read_csv(csv_path, index_col=0)

    # 按角色合并状态列（适配行为密度热力图）
    heatmap_data = df.groupby(level=0, axis=1).sum()

    # 转换为 float，避免非数字报错
    heatmap_data = heatmap_data.apply(pd.to_numeric, errors="coerce")

    plt.figure(figsize=(10, 6))
    sns.heatmap(heatmap_data, cmap="YlGnBu", annot=True, fmt=".0f", cbar=True)
    plt.title(f"Role-State Heatmap – {version_name}")
    plt.xlabel("Role")
    plt.ylabel("Chapter")
    plt.tight_layout()
    outpath = os.path.join(OUTPUT_ROOT, f"heatmap_{version_name}.png")
    plt.savefig(outpath)
    plt.close()

# 主程序
if __name__ == "__main__":
    for version_dir in VERSION_DIRS:
        name = os.path.basename(version_dir)
        csv_file = os.path.join(version_dir, "role_path_matrix.csv")
        if os.path.exists(csv_file):
            print(f"✅ 分析中：{name}")
            plot_state_trend(csv_file, name)
            plot_heatmap(csv_file, name)
        else:
            print(f"⚠️ 未找到文件：{csv_file}")
