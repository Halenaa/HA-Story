import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# 加载数据
df = pd.read_csv('metrics_master_clean.csv')

# === LAYER 1: 核心证明分析 ===
print("=== BASELINE vs 实验组对比分析 ===")

# 定义核心指标
core_metrics = [
    'avg_semantic_continuity',  # 语义连续性（之前的连贯性）
    'diversity_score_seed',     # 多样性  
    'roberta_avg_score',        # 情感质量
    'tp_completion_rate',       # 结构完整性
    'total_words',              # 内容丰富度
]

# 基础对比分析
comparison_results = {}
for metric in core_metrics:
    baseline_vals = df[df['is_baseline']==1][metric].dropna()
    exp_vals = df[df['is_baseline']==0][metric].dropna()
    
    if len(baseline_vals) > 0 and len(exp_vals) > 0:
        # 描述性统计
        baseline_mean = baseline_vals.mean()
        baseline_std = baseline_vals.std()
        exp_mean = exp_vals.mean()
        exp_std = exp_vals.std()
        
        # 效应量计算 (Cohen's d)
        pooled_std = np.sqrt((baseline_vals.var() + exp_vals.var()) / 2)
        cohens_d = (exp_mean - baseline_mean) / pooled_std if pooled_std > 0 else 0
        
        # 统计检验
        t_stat, p_val = stats.ttest_ind(exp_vals, baseline_vals)
        
        # 改进百分比
        improvement_pct = ((exp_mean - baseline_mean) / baseline_mean) * 100 if baseline_mean != 0 else 0
        
        comparison_results[metric] = {
            'baseline_mean': baseline_mean,
            'baseline_std': baseline_std,
            'exp_mean': exp_mean,
            'exp_std': exp_std,
            'cohens_d': cohens_d,
            'p_value': p_val,
            'improvement_pct': improvement_pct
        }
        
        print(f"\n{metric}:")
        print(f"  Baseline: {baseline_mean:.3f} ± {baseline_std:.3f}")
        print(f"  Experiment: {exp_mean:.3f} ± {exp_std:.3f}")
        print(f"  Improvement: {improvement_pct:+.1f}%")
        print(f"  Cohen's d: {cohens_d:.3f}")
        print(f"  p-value: {p_val:.4f}")

# === LAYER 2: 参数影响分析 ===
print("\n\n=== 参数影响分析 ===")

# Temperature影响分析
print("\n--- Temperature影响 ---")
exp_data = df[df['is_baseline']==0]
temp_analysis = {}

for metric in core_metrics:
    temp_groups = [exp_data[exp_data['temperature']==t][metric].dropna() 
                   for t in ['0.3', '0.7', '0.9']]
    
    if all(len(g) > 2 for g in temp_groups):
        f_stat, p_val = stats.f_oneway(*temp_groups)
        means = [g.mean() for g in temp_groups]
        
        temp_analysis[metric] = {
            'f_statistic': f_stat,
            'p_value': p_val,
            'means': means,
            'temp_labels': ['0.3', '0.7', '0.9']
        }
        
        print(f"{metric}: F={f_stat:.3f}, p={p_val:.4f}")
        print(f"  T0.3: {means[0]:.3f}, T0.7: {means[1]:.3f}, T0.9: {means[2]:.3f}")

# Structure影响分析
print("\n--- Structure影响 ---")
struct_analysis = {}

for metric in core_metrics:
    linear = exp_data[exp_data['structure']=='linear'][metric].dropna()
    nonlinear = exp_data[exp_data['structure']=='nonlinear'][metric].dropna()
    
    if len(linear) > 2 and len(nonlinear) > 2:
        t_stat, p_val = stats.ttest_ind(linear, nonlinear)
        
        struct_analysis[metric] = {
            't_statistic': t_stat,
            'p_value': p_val,
            'linear_mean': linear.mean(),
            'nonlinear_mean': nonlinear.mean()
        }
        
        print(f"{metric}: t={t_stat:.3f}, p={p_val:.4f}")
        print(f"  Linear: {linear.mean():.3f}, Nonlinear: {nonlinear.mean():.3f}")

# === LAYER 3: 综合评价体系 ===
print("\n\n=== 综合评价体系构建 ===")

# 标准化指标 (0-1 scale)
def normalize_metric(series, higher_better=True):
    if len(series) == 0:
        return series
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    
    normalized = (series - min_val) / (max_val - min_val)
    return normalized if higher_better else (1 - normalized)

# 对每个指标标准化
normalized_metrics = {}
for metric in core_metrics:
    exp_data_clean = exp_data[metric].dropna()
    if metric == 'err_per_100w':  # 错误率越低越好
        normalized_metrics[f'{metric}_norm'] = normalize_metric(exp_data_clean, higher_better=False)
    else:  # 其他指标越高越好
        normalized_metrics[f'{metric}_norm'] = normalize_metric(exp_data_clean, higher_better=True)

# 创建标准化数据框
norm_df = pd.DataFrame(normalized_metrics)

# 计算综合评分
weights = {
    'avg_semantic_continuity_norm': 0.25,      # 语义连续性（之前的连贯性）
    'diversity_score_seed_norm': 0.25, # 多样性
    'roberta_avg_score_norm': 0.2,   # 情感质量  
    'tp_completion_rate_norm': 0.2,  # 结构完整性
    'total_words_norm': 0.1          # 内容丰富度
}

# 计算综合分数
composite_scores = []
for idx, row in norm_df.iterrows():
    score = sum(row[metric] * weight for metric, weight in weights.items() if metric in row and pd.notna(row[metric]))
    composite_scores.append(score)

# 添加综合分数到原数据
exp_data_with_scores = exp_data.copy()
exp_data_with_scores['composite_score'] = composite_scores

# 分析最佳配置
print("\n--- 最佳参数配置 ---")
top_configs = exp_data_with_scores.nlargest(5, 'composite_score')
print("Top 5 配置:")
for idx, row in top_configs.iterrows():
    print(f"  {row['genre']}-{row['structure']}-T{row['temperature']}-s{row['seed']}: {row['composite_score']:.3f}")

# 最佳vs最差配置对比
worst_configs = exp_data_with_scores.nsmallest(5, 'composite_score')
best_mean = top_configs['composite_score'].mean()
worst_mean = worst_configs['composite_score'].mean()
improvement = (best_mean - worst_mean) / worst_mean * 100

print(f"\n最佳配置平均分: {best_mean:.3f}")
print(f"最差配置平均分: {worst_mean:.3f}")
print(f"配置优化改进: {improvement:.1f}%")

# === 关键结论总结 ===
print("\n\n=== 关键发现总结 ===")

# 1. 与baseline的比较
significant_improvements = sum(1 for result in comparison_results.values() if result['p_value'] < 0.05 and result['improvement_pct'] > 0)
total_metrics = len(comparison_results)

print(f"1. Baseline对比:")
print(f"   - {significant_improvements}/{total_metrics} 指标显示统计学改进")
print(f"   - 平均改进幅度: {np.mean([r['improvement_pct'] for r in comparison_results.values()]):.1f}%")

# 2. 参数显著性
temp_significant = sum(1 for result in temp_analysis.values() if result['p_value'] < 0.05)
struct_significant = sum(1 for result in struct_analysis.values() if result['p_value'] < 0.05)

print(f"2. 参数影响:")
print(f"   - Temperature在 {temp_significant}/{len(temp_analysis)} 指标上有显著影响")
print(f"   - Structure在 {struct_significant}/{len(struct_analysis)} 指标上有显著影响")

# 3. 系统可控性
print(f"3. 系统可控性:")
print(f"   - 参数优化可带来 {improvement:.1f}% 的性能提升")
print(f"   - 多维度评价体系成功构建")

print("\n=== 分析完成！===")