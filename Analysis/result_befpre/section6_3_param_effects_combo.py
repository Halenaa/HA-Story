
"""
Section 6.3 参数效应分析（合并子图 + 基线虚线覆盖）
====================================================
改动点：
1) 将同一指标的两类图放到一个 Figure 里（左：温度趋势；右：结构箱线），便于横向对照。
2) 在两类图上叠加 baseline 的数值：
   - 温度趋势图：对 baseline 计算每个 temperature 的均值，绘制 3 条红色虚线（"r--"）。
   - 结构箱线图：对 baseline 计算整体均值，绘制一条红色虚线（"r--"）。
3) 仍只使用 matplotlib；默认会指定 baseline 线为红色虚线，其余曲线沿用默认配色。

注意：
- 你需要告诉脚本如何识别 "baseline"。本脚本提供 `baseline_filter(df)` 函数，
  默认规则（任选其一即可匹配）：
  - 存在列 "is_baseline" 且其值为 1/true
  - 或存在列 "model"/"source"/"system" 且文本中包含 "baseline" 或 "direct"
- 如果你的 clean.csv 有其他标记方式，请在 baseline_filter 中替换为你的条件。

运行：
$ python section6_3_param_effects_combo.py
输出：
- 合并图：/mnt/data/section6_3_figs_combo/
- 统计表：/mnt/data/section6_3_tables/（与原脚本相同文件名以便对齐）
"""

import re
import math
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ========== 配置 ==========
INPUT_CSV = "clean.csv"
OUT_DIR_FIG = Path("section6_3_figs_combo")  # 新的合并图输出目录
OUT_DIR_TAB = Path("section6_3_tables")      # 复用原目录（如果已存在会覆盖同名表）

# 你可以在这里限制要绘制的指标（为空则自动与文件列求交集）
USER_SELECTED_METRICS: List[str] = []

# ========== 工具函数 ==========
def safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def to_float_safe(x):
    try:
        return float(x)
    except Exception:
        return np.nan

def find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for name in df.columns:
        if name in candidates:
            return name
    return None

def safe_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s)

def _coerce_numeric(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.astype(float)
    return pd.to_numeric(series, errors="coerce").astype(float)

def group_stats(d: pd.DataFrame, value_col: str, group_cols: List[str]) -> pd.DataFrame:
    g = d.groupby(group_cols, dropna=True)[value_col].agg(['mean', 'std', 'count']).reset_index()
    ci95 = []
    for _, row in g.iterrows():
        n = row['count']
        if n and n > 1 and not math.isnan(row['std']):
            ci = 1.96 * (row['std'] / math.sqrt(n))
        else:
            ci = np.nan
        ci95.append(ci)
    g['ci95'] = ci95
    return g

# ========== 如何识别 baseline ==========
def baseline_filter(df: pd.DataFrame) -> pd.Series:
    """
    返回一个布尔 Series，标记哪些行是 baseline。
    你可以按需修改逻辑：
    1) is_baseline 列存在且为真
    2) model/source/system 列包含 'baseline' 或 'direct' 等关键词（不区分大小写）
    """
    candidates_flag = ["is_baseline", "baseline"]
    for c in candidates_flag:
        if c in df.columns:
            v = df[c]
            if v.dtype == bool:
                return v
            try:
                return v.astype(int) == 1
            except Exception:
                pass

    text_cols = ["model", "source", "system", "pipeline", "tag"]
    for c in text_cols:
        if c in df.columns:
            txt = df[c].astype(str).str.lower()
            return txt.str.contains("baseline") | txt.str.contains("direct")

    # 如果都没有，默认全 False（即没有 baseline）
    return pd.Series([False]*len(df), index=df.index)

# ========== 主流程 ==========
def main():
    safe_mkdir(OUT_DIR_FIG)
    safe_mkdir(OUT_DIR_TAB)

    # 读取并统一列名
    df = pd.read_csv(INPUT_CSV)
    df.columns = [c.lower().strip() for c in df.columns]

    # 关键列
    structure_col = find_col(df, ["structure", "story_structure", "layout", "narrative_structure"])
    temperature_col = find_col(df, ["temperature", "temp", "t"])
    genre_col = find_col(df, ["genre", "category", "domain"])

    missing = []
    if structure_col is None: missing.append("structure")
    if temperature_col is None: missing.append("temperature")
    if missing:
        raise RuntimeError(f"缺少关键参数列：{', '.join(missing)}。请在 clean.csv 中包含这些列。当前列为：{list(df.columns)}")

    # 规范化
    df[structure_col] = df[structure_col].astype(str).str.lower().str.strip().replace({
        "non-linear": "nonlinear",
        "non linear": "nonlinear",
        "non_line": "nonlinear",
        "linear_": "linear",
    })
    df[temperature_col] = df[temperature_col].apply(to_float_safe)

    # 指标集合
    expected_metrics = [
        "pseudo_ppl", "err_per_100w",
        "distinct_avg", "diversity_group_score", "self_bleu_group",
        "avg_semantic_continuity", "semantic_continuity_std",
        "roberta_avg_score", "emotion_correlation", "classification_agreement",
        "tp_coverage", "li_function_diversity", "total_events", "chapter_count",
        "tokens_total", "cost_usd", "wall_time_sec",
    ]
    metrics = [m for m in (USER_SELECTED_METRICS or expected_metrics) if m in df.columns]
    if not metrics:
        raise RuntimeError(f"未在 clean.csv 中找到待绘制的指标列。可选包括：{expected_metrics}")

    # baseline vs system 划分
    base_mask = baseline_filter(df)
    has_baseline = base_mask.any()
    df_sys = df[~base_mask].copy()
    df_base = df[base_mask].copy() if has_baseline else pd.DataFrame(columns=df.columns)

    # 统计表（与原脚本一致）
    all_stats = []
    for m in metrics:
        df[m] = _coerce_numeric(df[m])
        stat = group_stats(df.dropna(subset=[m]), m, [structure_col, temperature_col])
        stat.insert(0, "metric", m)
        all_stats.append(stat)

    summary = pd.concat(all_stats, ignore_index=True)
    summary = summary[["metric", structure_col, temperature_col, "mean", "std", "count", "ci95"]]
    summary_csv = OUT_DIR_TAB / "section6_3_param_effects_summary.csv"
    summary.to_csv(summary_csv, index=False)

    pivot = summary.pivot_table(index=["metric", structure_col], columns=temperature_col, values="mean").reset_index()
    pivot_csv = OUT_DIR_TAB / "section6_3_means_pivot_metric_structure_by_temperature.csv"
    pivot.to_csv(pivot_csv, index=False)

    # ========== 绘图（合并子图） ==========
    for m in metrics:
        # 数据准备
        df_sys[m] = _coerce_numeric(df_sys[m])
        if has_baseline:
            df_base[m] = _coerce_numeric(df_base[m])

        # Figure：两列子图
        fig = plt.figure(figsize=(12, 5))
        fig.suptitle(f"{m} — Parameter Effects (structure × temperature)", fontsize=12)

        # --- 左：温度趋势（按 structure 均值），叠加 baseline@T 的红色虚线 ---
        ax1 = fig.add_subplot(1, 2, 1)
        stat_sys = df_sys.groupby([structure_col, temperature_col], dropna=True)[m].mean().reset_index()
        if not stat_sys.empty:
            for s_val, sub in stat_sys.groupby(structure_col):
                xs = sub[temperature_col].values
                ys = sub[m].values
                ax1.plot(xs, ys, marker='o', label=str(s_val))
        ax1.set_xlabel("temperature")
        ax1.set_ylabel(m)
        ax1.set_title("Trend by structure")

        if has_baseline:
            base_by_t = df_base.groupby(temperature_col, dropna=True)[m].mean().reset_index()
            # 三条红色虚线：每个温度一个水平线
            for _, row in base_by_t.iterrows():
                t = row[temperature_col]
                y = row[m]
                # 在当前 x 轴范围画水平线
                ax1.axhline(y, linestyle="--", color="r", linewidth=1)
                ax1.text(0.99, y, f"baseline@T={t:g}", color="r", va="bottom", ha="right", fontsize=8,
                         transform=ax1.get_yaxis_transform())

        ax1.legend(loc="best")

        # --- 右：结构箱线图（系统数据），叠加 baseline 整体均值红色虚线 ---
        ax2 = fig.add_subplot(1, 2, 2)
        data, labels = [], []
        for s_val, sub in df_sys.groupby(structure_col):
            vals = sub[m].dropna().values
            if len(vals) > 0:
                data.append(vals)
                labels.append(str(s_val))
        if len(data) > 0:
            ax2.boxplot(data, labels=labels, showmeans=True)
        ax2.set_xlabel(structure_col)
        ax2.set_ylabel(m)
        ax2.set_title("Distribution by structure")

        if has_baseline and not df_base[m].dropna().empty:
            base_mean = df_base[m].mean()
            ax2.axhline(base_mean, linestyle="--", color="r", linewidth=1)
            ax2.text(0.98, base_mean, "baseline mean", color="r", va="bottom", ha="right", fontsize=8,
                     transform=ax2.get_yaxis_transform())

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        out_path = OUT_DIR_FIG / f"{safe_name(m)}__combo.png"
        fig.savefig(out_path, dpi=200)
        plt.close(fig)

    print("=== 6.3 合并子图版：生成完毕 ===")
    print("合并图目录：", OUT_DIR_FIG)
    print("表格目录：", OUT_DIR_TAB)
    print("关键表：", str(summary_csv))
    print("均值透视表：", str(pivot_csv))

if __name__ == "__main__":
    main()
