"""
Section 6.3 参数效应分析（维度级聚合版）
===================================
- 将多个指标聚合成六大维度
- 分析 structure × temperature 对各维度的影响
- 输出均值表、bootstrap CI、折线图与箱线图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import zscore

# 配置
INPUT_CSV = "clean.csv"
OUT_DIR = Path("section6_3_dims")
N_BOOT = 1000
np.random.seed(42)

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== Step 1: 读取数据 ==========
df = pd.read_csv(INPUT_CSV)
df.columns = [c.lower().strip() for c in df.columns]

# ========== Step 2: 定义维度聚合规则 ==========
dim_defs = {
    "Fluency": [
        ("pseudo_ppl", -1),       # 越低越好 → 取负号
        ("err_per_100w", -1)
    ],
    "Diversity": [
        ("distinct_avg", +1),
        ("diversity_group_score", +1),
        ("self_bleu_group", -1)   # 越低越好
    ],
    "Coherence": [
        ("avg_semantic_continuity", +1),
        ("semantic_continuity_std", -1)
    ],
    "Emotion": [
        ("roberta_avg_score", +1),
        ("emotion_correlation", +1)
    ],
    "Structure": [
        ("tp_coverage", +1),
        ("total_events", +1),
        ("li_function_diversity", +1)
    ],
    "Cost": [
        ("cost_usd", -1),         # 成本越低越好
        ("tokens_total", -1),
        ("wall_time_sec", -1)
    ]
}

# ========== Step 3: 构造维度分数 ==========
dim_scores = {}

for dim, items in dim_defs.items():
    vals = []
    for col, sign in items:
        if col in df.columns:
            v = pd.to_numeric(df[col], errors="coerce") * sign
            vals.append(zscore(v, nan_policy="omit"))
    if vals:
        dim_scores[dim] = np.nanmean(np.column_stack(vals), axis=1)

dim_df = pd.DataFrame(dim_scores)
dim_df["structure"] = df["structure"]
dim_df["temperature"] = df["temperature"]

# ========== Step 4: Bootstrap CI ==========
records = []
for (s, t), sub in dim_df.groupby(["structure", "temperature"]):
    for dim in dim_scores.keys():
        values = sub[dim].dropna().values
        if len(values) == 0:
            continue
        boot_means = []
        for _ in range(N_BOOT):
            resample = np.random.choice(values, size=len(values), replace=True)
            boot_means.append(resample.mean())
        mean = np.mean(boot_means)
        ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])
        records.append({
            "structure": s,
            "temperature": t,
            "dimension": dim,
            "mean": mean,
            "ci95_low": ci_low,
            "ci95_high": ci_high,
            "n": len(values)
        })

df_summary = pd.DataFrame(records)
df_summary.to_csv(OUT_DIR / "param_effects_summary_dims.csv", index=False)

# ========== Step 5: 可视化 ==========
for dim in dim_scores.keys():
    plt.figure(figsize=(8, 5))
    for s in dim_df["structure"].unique():
        subset = df_summary[(df_summary["structure"] == s) & (df_summary["dimension"] == dim)]
        plt.errorbar(
            subset["temperature"], subset["mean"],
            yerr=[subset["mean"] - subset["ci95_low"], subset["ci95_high"] - subset["mean"]],
            label=s, capsize=4, marker="o", linestyle="-"
        )
    plt.title(f"Temperature Effect on {dim}")
    plt.xlabel("Temperature")
    plt.ylabel(f"{dim} (z-normalized score)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"{dim}_temp_effect.png", dpi=200)
    plt.close()

    # 箱线图：结构 vs score
    plt.figure(figsize=(6, 5))
    dim_df.boxplot(column=dim, by="structure")
    plt.title(f"{dim}: Structure Effect")
    plt.suptitle("")
    plt.xlabel("Structure")
    plt.ylabel(f"{dim} (z-normalized score)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"{dim}_structure_effect.png", dpi=200)
    plt.close()

print("✅ 完成：维度级参数效应分析")
print("结果保存在:", OUT_DIR)
