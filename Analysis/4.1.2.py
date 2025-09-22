import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import pearsonr, spearmanr
from sklearn.utils import resample
import seaborn as sns
import matplotlib.pyplot as plt

# 4.1.2 聚合方法验证 - 快速实现
def aggregation_method_validation(df):
    """
    4.1.2 聚合方法验证完整分析
    """
    print("=== 4.1.2 聚合方法验证分析 ===\n")
    
    # 排除基线样本
    work_data = df[df['is_baseline'] != 1].copy()
    
    # 1. 定义核心评估指标
    core_metrics = [
        'distinct_avg', 'distinct_score',           # 多样性
        'avg_semantic_continuity',                  # 连贯性
        'pseudo_ppl', 'err_per_100w',              # 流畅性
        'roberta_avg_score', 'emotion_correlation', # 情感
        'tp_completion_rate', 'li_function_diversity', # 结构
        'wall_time_sec', 'cost_usd'                 # 效率
    ]
    
    # 过滤存在的指标
    available_metrics = [m for m in core_metrics if m in work_data.columns and work_data[m].notna().sum() > 10]
    print(f"选用的核心指标 ({len(available_metrics)}个): {available_metrics}\n")
    
    # 2. 数据标准化分析
    print("数据标准化需求分析:")
    
    normalized_data = work_data[available_metrics + ['story_id', 'genre', 'structure', 'temperature']].copy()
    scaler = MinMaxScaler()
    
    # 检查并标准化需要处理的指标
    for metric in available_metrics:
        values = work_data[metric].dropna()
        min_val, max_val = values.min(), values.max()
        range_span = max_val - min_val
        
        # 判断是否需要标准化
        needs_norm = range_span > 2 or max_val > 2 or min_val < -2
        
        if needs_norm:
            normalized_data[metric] = scaler.fit_transform(work_data[[metric]])
            print(f"  {metric}: [{min_val:.3f}, {max_val:.3f}] -> [0, 1] ✅")
        else:
            print(f"  {metric}: [{min_val:.3f}, {max_val:.3f}] -> 无需处理")
    
    # 3. 等权聚合方法
    print(f"\n=== 等权聚合 vs PCA聚合对比 ===\n")
    
    # 处理反向指标（越小越好的指标需要反转）
    reverse_metrics = ['pseudo_ppl', 'err_per_100w', 'wall_time_sec', 'cost_usd']
    aggregation_data = normalized_data[available_metrics].copy()
    
    for metric in reverse_metrics:
        if metric in aggregation_data.columns:
            aggregation_data[metric] = 1 - aggregation_data[metric]
    
    # 等权聚合
    equal_weight_score = aggregation_data.mean(axis=1)
    print(f"1. 等权聚合结果:")
    print(f"   均值: {equal_weight_score.mean():.3f}")
    print(f"   标准差: {equal_weight_score.std():.3f}")
    print(f"   范围: [{equal_weight_score.min():.3f}, {equal_weight_score.max():.3f}]")
    
    # 4. PCA聚合方法
    pca = PCA()
    pca.fit(aggregation_data.fillna(0))
    
    # 选择主成分数量（解释85%方差）
    cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
    n_components = np.argmax(cumsum_variance >= 0.85) + 1
    
    print(f"\n2. PCA聚合结果:")
    print(f"   选择主成分数: {n_components} (解释方差: {cumsum_variance[n_components-1]:.3f})")
    
    # 重新拟合PCA
    pca = PCA(n_components=n_components)
    pca_scores = pca.fit_transform(aggregation_data.fillna(0))
    pca_aggregated = np.average(pca_scores, axis=1, weights=pca.explained_variance_ratio_)
    
    print(f"   PCA聚合均值: {pca_aggregated.mean():.3f}")
    print(f"   PCA聚合标准差: {pca_aggregated.std():.3f}")
    
    # 主成分权重分析
    print(f"\n   主成分权重分析 (|权重|>0.3):")
    for i, component in enumerate(pca.components_):
        print(f"   PC{i+1} (解释方差: {pca.explained_variance_ratio_[i]:.3f}):")
        for j, weight in enumerate(component):
            if abs(weight) > 0.3:
                print(f"     {available_metrics[j]}: {weight:.3f}")
    
    # 5. 聚合结果对比分析
    correlation = pearsonr(equal_weight_score, pca_aggregated)[0]
    spearman_corr = spearmanr(equal_weight_score, pca_aggregated)[0]
    
    print(f"\n=== 聚合结果一致性检验 ===")
    print(f"Pearson相关系数: {correlation:.3f}")
    print(f"Spearman相关系数: {spearman_corr:.3f}")
    
    # 排名一致性
    from scipy import stats
    equal_rank = stats.rankdata(-equal_weight_score)
    pca_rank = stats.rankdata(-pca_aggregated)
    rank_correlation = spearmanr(equal_rank, pca_rank)[0]
    print(f"排名相关性: {rank_correlation:.3f}")
    
    # 分歧分析
    rank_diff = np.abs(equal_rank - pca_rank)
    large_disagreements = np.sum(rank_diff > 5)
    print(f"平均排名差异: {np.mean(rank_diff):.1f}")
    print(f"重大分歧数量 (差异>5): {large_disagreements}")
    
    # 6. Bootstrap置信区间分析
    print(f"\n=== Bootstrap置信区间分析 ===")
    
    n_bootstrap = 200  # 减少计算时间
    bootstrap_equal = []
    bootstrap_pca = []
    bootstrap_corr = []
    
    for i in range(n_bootstrap):
        # 重采样
        sample_indices = resample(range(len(aggregation_data)), random_state=i)
        sample_data = aggregation_data.iloc[sample_indices]
        
        # 等权聚合
        eq_sample = sample_data.mean(axis=1)
        bootstrap_equal.append(eq_sample.mean())
        
        # PCA聚合
        pca_temp = PCA(n_components=n_components)
        pca_scores_temp = pca_temp.fit_transform(sample_data.fillna(0))
        pca_sample = np.average(pca_scores_temp, axis=1, weights=pca_temp.explained_variance_ratio_)
        bootstrap_pca.append(pca_sample.mean())
        
        # 相关性
        bootstrap_corr.append(pearsonr(eq_sample, pca_sample)[0])
    
    # 计算95%置信区间
    eq_ci = np.percentile(bootstrap_equal, [2.5, 97.5])
    pca_ci = np.percentile(bootstrap_pca, [2.5, 97.5])
    corr_ci = np.percentile(bootstrap_corr, [2.5, 97.5])
    
    print(f"等权聚合95%置信区间: [{eq_ci[0]:.3f}, {eq_ci[1]:.3f}]")
    print(f"PCA聚合95%置信区间: [{pca_ci[0]:.3f}, {pca_ci[1]:.3f}]")
    print(f"相关性95%置信区间: [{corr_ci[0]:.3f}, {corr_ci[1]:.3f}]")
    
    # 稳定性分析
    eq_stability = np.std(bootstrap_equal)
    pca_stability = np.std(bootstrap_pca)
    print(f"等权聚合稳定性: {eq_stability:.4f}")
    print(f"PCA聚合稳定性: {pca_stability:.4f}")
    
    # 7. 综合结论
    print(f"\n=== 聚合方法验证结论 ===")
    
    if correlation > 0.8:
        consistency_level = "高度一致"
    elif correlation > 0.6:
        consistency_level = "基本一致"
    else:
        consistency_level = "存在显著分歧"
    
    stable_method = "等权聚合" if eq_stability < pca_stability else "PCA聚合"
    
    print(f"1. 方法一致性: {consistency_level} (r={correlation:.3f})")
    print(f"2. 排名稳定性: 平均差异{np.mean(rank_diff):.1f}位")
    print(f"3. 推荐方法: {stable_method} (基于稳定性)")
    print(f"4. 置信度: 两种方法相关性置信区间{corr_ci}")
    
    # 返回结果用于后续分析
    results = {
        'equal_weight_scores': equal_weight_score,
        'pca_scores': pca_aggregated,
        'correlation': correlation,
        'rank_correlation': rank_correlation,
        'bootstrap_ci': {
            'equal_weight': eq_ci,
            'pca': pca_ci,
            'correlation': corr_ci
        },
        'stability': {
            'equal_weight': eq_stability,
            'pca': pca_stability
        },
        'pca_components': n_components,
        'explained_variance': pca.explained_variance_ratio_
    }
    
    return results, normalized_data

# 快速数据检查函数
def quick_metrics_check(df):
    """
    快速检查指标分布，确定标准化需求
    """
    print("=== 指标分布快速检查 ===\n")
    
    metrics_to_check = [
        'distinct_avg', 'pseudo_ppl', 'err_per_100w', 
        'avg_semantic_continuity', 'roberta_avg_score',
        'wall_time_sec', 'cost_usd', 'tp_completion_rate'
    ]
    
    work_data = df[df['is_baseline'] != 1]
    
    for metric in metrics_to_check:
        if metric in df.columns:
            values = work_data[metric].dropna()
            if len(values) > 0:
                min_val, max_val = values.min(), values.max()
                mean_val, std_val = values.mean(), values.std()
                
                # 判断标准化需求
                needs_norm = (max_val - min_val) > 2 or max_val > 2 or min_val < -2
                status = "需要归一化" if needs_norm else "可直接使用"
                
                print(f"{metric}:")
                print(f"  范围: [{min_val:.3f}, {max_val:.3f}]")
                print(f"  均值±标准差: {mean_val:.3f}±{std_val:.3f}")
                print(f"  处理建议: {status}\n")

# 使用示例
if __name__ == "__main__":
    # 使用方法:
    # df = pd.read_csv('clean.csv')
    # quick_metrics_check(df)  # 先快速检查
    # results, normalized_data = aggregation_method_validation(df)  # 完整分析
    print("聚合方法验证工具准备就绪!")