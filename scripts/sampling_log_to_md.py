import os
import json
import pandas as pd

def sampling_log_to_md_csv(
    log_path="output/sampling_log.json",
    output_dir="output",
    md_name="sampling_summary.md",
    csv_name="sampling_summary.csv"
):
    """
    将 sampling_log.json 转换为 markdown 和 csv 格式，方便论文图表展示
    """
    if not os.path.exists(log_path):
        print(f"❌ 找不到日志文件：{log_path}")
        return

    # 加载 JSON 数据
    with open(log_path, "r", encoding="utf-8") as f:
        log_data = pd.read_json(f)

    # 重命名列，便于论文展示
    display_df = log_data.rename(columns={
        "version": "Version",
        "temperature": "Temp",
        "topic": "Topic",
        "style": "Style",
        "anchor_count": "Anchor Count",
        "avg_states_per_role": "Avg States/Role"
    })

    # 输出 CSV 文件
    csv_path = os.path.join(output_dir, csv_name)
    display_df.to_csv(csv_path, index=False)

    # 输出 Markdown 文件
    md_path = os.path.join(output_dir, md_name)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(display_df.to_markdown(index=False))

    print(f"✅ Markdown 表格已保存：{md_path}")
    print(f"✅ CSV 表格已保存：{csv_path}")
    return display_df


# ✅ 脚本直接运行时默认执行转换
if __name__ == "__main__":
    sampling_log_to_md_csv()
