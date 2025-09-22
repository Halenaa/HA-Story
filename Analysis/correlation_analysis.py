"""
Section 6.4 维度相关性 (改造版)
==============================
- 用等权聚合 OR PCA 权重生成维度分数
- 输出 6x6 Spearman 相关矩阵 + 热图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from pathlib import Path

INPUT_CSV = "clean.csv"
OUT_DIR = Path("section6_4_dims")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT_CSV)
df.columns = [c.lower().strip() for c in df.columns]

# 定义维度 → 指标
dim_defs = {
    "Fluency": ["pseudo_ppl", "err_per_100w"],
    "Diversity": ["distinct_avg", "diversity_group_score", "self_bleu_group"],
    "Coherence": ["avg_semantic_continuity", "semantic_continuity_std"],
    "Emotion": ["roberta_avg_score", "emotion_correlation"],
    "Structure": ["tp_coverage", "total_events", "li_function_diversity"],
    "Cost": ["cost_usd", "tokens_total", "wall_time_sec"]
}

# ----------- 方式 A：等权聚合 -----------
dim_scores_eq = {}
for dim, cols in dim_defs.items():
    cols = [c for c in cols if c in df.columns]
    if not cols: 
        continue
    X = df[cols].apply(pd.to_numeric, errors="coerce")
    X_z = X.apply(lambda col: (col - col.mean())/col.std(), axis=0)
    dim_scores_eq[dim] = X_z.mean(axis=1)

df_eq = pd.DataFrame(dim_scores_eq)

# ----------- 方式 B：PCA 聚合 -----------
dim_scores_pca = {}
for dim, cols in dim_defs.items():
    cols = [c for c in cols if c in df.columns]
    if len(cols) < 2: 
        continue
    X = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    pca = PCA(n_components=1)
    dim_scores_pca[dim] = pca.fit_transform(X_scaled).flatten()

df_pca = pd.DataFrame(dim_scores_pca)

# ----------- Spearman 相关矩阵 -----------
corr_eq = df_eq.corr(method="spearman")
corr_pca = df_pca.corr(method="spearman")

corr_eq.to_csv(OUT_DIR / "spearman_dims_eq.csv")
corr_pca.to_csv(OUT_DIR / "spearman_dims_pca.csv")

# ----------- 热图绘制 -----------
for name, corr in [("EqualWeights", corr_eq), ("PCAWeights", corr_pca)]:
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(corr.values, aspect='auto')
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)
    fig.colorbar(im, ax=ax)
    ax.set_title(f"Spearman Correlation ({name})")
    plt.tight_layout()
    fig.savefig(OUT_DIR / f"correlation_heatmap_{name}.png", dpi=200)
    plt.close(fig)

print("✅ 完成 6.4 维度相关性分析")
print("结果保存在:", OUT_DIR)
