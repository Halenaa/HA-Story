#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳健组别效应分析 - 使用Cluster-Robust标准误
Robust Group Effects Analysis - Using Cluster-Robust Standard Errors

由于混合效应模型收敛问题，改用OLS + cluster-robust标准误进行分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 导入修正函数
import fix_analysis_functions as fix

def robust_group_effects_ols(long_table_df):
    """
    使用OLS + cluster-robust标准误分析组别效应
    """
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
    except ImportError:
        print("❌ statsmodels未安装")
        return None
    
    print("🔧 稳健组别效应分析 (OLS + Cluster-Robust SE)")
    print("-" * 60)
    
    # 1. 数据准备
    rater_groups = fix.identify_group_membership(long_table_df)
    
    model_data = long_table_df[long_table_df['dimension'] == 'Overall Quality'].copy()
    model_data['group_type'] = model_data['rater_id'].map(
        lambda x: rater_groups.get(x, {}).get('group_type', 'unknown')
    )
    
    # 标准化评分 (within-rater)
    model_data['score_z'] = model_data.groupby('rater_id')['score'].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() > 0 else x - x.mean()
    )
    
    # 过滤实验配置
    exp_data = model_data[model_data['config'] != 'baseline'].copy()
    
    print(f"📊 数据概况:")
    print(f"   观察数: {len(exp_data)}")
    print(f"   参与者: {exp_data['rater_id'].nunique()}")
    print(f"   深度评价: {len(exp_data[exp_data['group_type']=='deep'])}")
    print(f"   浅度评价: {len(exp_data[exp_data['group_type']=='shallow'])}")
    
    results = {}
    
    # 2. 模型1: 仅config效应
    print(f"\n🔧 模型1: Config效应模型")
    try:
        model1 = ols('score_z ~ C(config)', data=exp_data).fit(cov_type='cluster', 
                                                               cov_kwds={'groups': exp_data['rater_id']})
        
        print(f"   R²: {model1.rsquared:.4f}")
        print(f"   F统计量: {model1.fvalue:.3f} (p={model1.f_pvalue:.4f})")
        
        results['model1'] = model1
        
    except Exception as e:
        print(f"   ❌ 模型1拟合失败: {e}")
        results['model1'] = None
    
    # 3. 模型2: Config + 组别效应
    print(f"\n🔧 模型2: Config + 组别效应模型")
    try:
        model2 = ols('score_z ~ C(config) + C(group_type)', data=exp_data).fit(cov_type='cluster',
                                                                               cov_kwds={'groups': exp_data['rater_id']})
        
        print(f"   R²: {model2.rsquared:.4f}")
        print(f"   F统计量: {model2.fvalue:.3f} (p={model2.f_pvalue:.4f})")
        
        # 检验组别效应是否显著
        group_coef = model2.params.get('C(group_type)[T.shallow]', None)
        if group_coef is not None:
            group_p = model2.pvalues.get('C(group_type)[T.shallow]', 1.0)
            print(f"   组别效应: {group_coef:+.4f} (p={group_p:.4f})")
        
        results['model2'] = model2
        
    except Exception as e:
        print(f"   ❌ 模型2拟合失败: {e}")
        results['model2'] = None
    
    # 4. 模型3: Config × 组别交互
    print(f"\n🔧 模型3: Config × 组别交互模型")
    try:
        model3 = ols('score_z ~ C(config) * C(group_type)', data=exp_data).fit(cov_type='cluster',
                                                                               cov_kwds={'groups': exp_data['rater_id']})
        
        print(f"   R²: {model3.rsquared:.4f}")
        print(f"   F统计量: {model3.fvalue:.3f} (p={model3.f_pvalue:.4f})")
        
        results['model3'] = model3
        
    except Exception as e:
        print(f"   ❌ 模型3拟合失败: {e}")
        results['model3'] = None
    
    # 5. 模型比较
    valid_models = {name: model for name, model in results.items() if model is not None}
    
    if len(valid_models) > 1:
        print(f"\n📊 模型比较:")
        print("模型\\t\\t\\tR²\\t\\tAIC\\t\\tF统计量\\tp值")
        print("-" * 60)
        
        best_r2 = 0
        best_model_name = None
        
        for name, model in valid_models.items():
            print(f"{name:<15}\\t{model.rsquared:.4f}\\t\\t{model.aic:.1f}\\t\\t{model.fvalue:.3f}\\t\\t{model.f_pvalue:.4f}")
            
            if model.rsquared > best_r2:
                best_r2 = model.rsquared
                best_model_name = name
        
        print(f"\n🏆 最佳模型: {best_model_name} (R² = {best_r2:.4f})")
        best_model = valid_models[best_model_name]
        
    else:
        best_model = list(valid_models.values())[0] if valid_models else None
        best_model_name = list(valid_models.keys())[0] if valid_models else "无"
    
    # 6. 详细分析最佳模型
    if best_model is not None:
        print(f"\n📋 {best_model_name} 详细结果 (Cluster-Robust SE):")
        print("-" * 60)
        
        print("系数\\t\\t\\t\\t\\t估计值\\t\\t标准误\\t\\tt值\\t\\tP值\\t\\t显著性")
        print("-" * 90)
        
        for param, coef in best_model.params.items():
            se = best_model.bse[param]
            t_val = best_model.tvalues[param]
            p_val = best_model.pvalues[param]
            
            # 显著性标记
            if p_val < 0.001:
                sig = "***"
            elif p_val < 0.01:
                sig = "**"
            elif p_val < 0.05:
                sig = "*"
            elif p_val < 0.1:
                sig = "."
            else:
                sig = ""
            
            print(f"{param:<25}\\t\\t{coef:8.4f}\\t{se:8.4f}\\t{t_val:8.3f}\\t{p_val:8.4f}\\t\\t{sig}")
    
    return results, exp_data

def detailed_group_comparison(long_table_df):
    """
    详细的组别比较分析
    """
    print(f"\n🔍 详细组别比较分析")
    print("-" * 60)
    
    rater_groups = fix.identify_group_membership(long_table_df)
    
    overall_data = long_table_df[long_table_df['dimension'] == 'Overall Quality'].copy()
    overall_data['group_type'] = overall_data['rater_id'].map(
        lambda x: rater_groups.get(x, {}).get('group_type', 'unknown')
    )
    
    # 1. 描述性统计
    print("📊 各组别评分描述统计:")
    group_desc = overall_data.groupby('group_type')['score'].agg(['count', 'mean', 'std', 'min', 'max']).round(3)
    print(group_desc)
    
    # 2. 配置级别的组别差异
    print(f"\n📊 各配置的组别差异:")
    print("Config\\t\\t\\t深度组\\t\\t浅度组\\t\\t差值\\t\\tCohen's d")
    print("-" * 70)
    
    comparison_results = []
    
    for config in overall_data['config'].unique():
        config_data = overall_data[overall_data['config'] == config]
        
        deep_scores = config_data[config_data['group_type'] == 'deep']['score']
        shallow_scores = config_data[config_data['group_type'] == 'shallow']['score']
        
        if len(deep_scores) > 0 and len(shallow_scores) > 0:
            deep_mean = deep_scores.mean()
            shallow_mean = shallow_scores.mean()
            diff = shallow_mean - deep_mean
            
            # Cohen's d
            pooled_std = np.sqrt(((len(deep_scores)-1)*deep_scores.var() + 
                                 (len(shallow_scores)-1)*shallow_scores.var()) / 
                                (len(deep_scores)+len(shallow_scores)-2))
            cohens_d = (shallow_mean - deep_mean) / pooled_std if pooled_std > 0 else 0
            
            print(f"{config:<15}\\t\\t{deep_mean:.2f}±{deep_scores.std():.2f}\\t{shallow_mean:.2f}±{shallow_scores.std():.2f}\\t{diff:+.2f}\\t\\t{cohens_d:+.3f}")
            
            comparison_results.append({
                'config': config,
                'deep_mean': deep_mean,
                'deep_std': deep_scores.std(),
                'deep_n': len(deep_scores),
                'shallow_mean': shallow_mean,
                'shallow_std': shallow_scores.std(),
                'shallow_n': len(shallow_scores),
                'difference': diff,
                'cohens_d': cohens_d
            })
        elif len(deep_scores) > 0:
            print(f"{config:<15}\\t\\t{deep_scores.mean():.2f}±{deep_scores.std():.2f}\\t   N/A\\t\\t   N/A\\t\\t   N/A")
    
    # 3. 总体组别效应的假设检验
    print(f"\n🧪 总体组别效应检验:")
    
    exp_data = overall_data[overall_data['config'] != 'baseline']
    deep_all = exp_data[exp_data['group_type'] == 'deep']['score']
    shallow_all = exp_data[exp_data['group_type'] == 'shallow']['score']
    
    if len(deep_all) > 0 and len(shallow_all) > 0:
        from scipy.stats import mannwhitneyu, ttest_ind, levene
        
        # Levene方差齐性检验
        levene_stat, levene_p = levene(deep_all, shallow_all)
        print(f"   Levene方差齐性检验: F={levene_stat:.3f}, p={levene_p:.4f}")
        
        # 选择合适的t检验
        equal_var = levene_p > 0.05
        t_stat, t_p = ttest_ind(deep_all, shallow_all, equal_var=equal_var)
        test_type = "等方差" if equal_var else "不等方差"
        print(f"   独立样本t检验({test_type}): t={t_stat:.3f}, p={t_p:.4f}")
        
        # 非参数检验
        u_stat, u_p = mannwhitneyu(deep_all, shallow_all, alternative='two-sided')
        print(f"   Mann-Whitney U检验: U={u_stat:.2f}, p={u_p:.4f}")
        
        # 效应量
        pooled_std = np.sqrt(((len(deep_all)-1)*deep_all.var() + 
                             (len(shallow_all)-1)*shallow_all.var()) / 
                            (len(deep_all)+len(shallow_all)-2))
        overall_cohens_d = (shallow_all.mean() - deep_all.mean()) / pooled_std
        
        # 置信区间 (基于t分布)
        se_diff = pooled_std * np.sqrt(1/len(deep_all) + 1/len(shallow_all))
        df = len(deep_all) + len(shallow_all) - 2
        from scipy.stats import t
        t_critical = t.ppf(0.975, df)
        ci_lower = (shallow_all.mean() - deep_all.mean()) - t_critical * se_diff
        ci_upper = (shallow_all.mean() - deep_all.mean()) + t_critical * se_diff
        
        print(f"   整体效应量(Cohen's d): {overall_cohens_d:+.3f}")
        print(f"   均值差异95%CI: [{ci_lower:+.3f}, {ci_upper:+.3f}]")
        
        # 解释效应
        if abs(overall_cohens_d) < 0.2:
            effect_interpretation = "微小效应"
        elif abs(overall_cohens_d) < 0.5:
            effect_interpretation = "小效应"
        elif abs(overall_cohens_d) < 0.8:
            effect_interpretation = "中等效应"
        else:
            effect_interpretation = "大效应"
        
        direction = "浅度组评分更高" if overall_cohens_d > 0 else "深度组评分更高"
        print(f"   → {direction}，{effect_interpretation}")
    
    return pd.DataFrame(comparison_results)

def create_group_effects_visualization(group_comparison, exp_data):
    """
    创建组别效应可视化
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    print(f"\n📊 创建组别效应可视化")
    
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 组别差异箱线图
    sns.boxplot(data=exp_data, x='config', y='score', hue='group_type', ax=axes[0,0])
    axes[0,0].set_title('各配置的组别评分差异')
    axes[0,0].set_xlabel('配置')
    axes[0,0].set_ylabel('评分')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].legend(title='组别类型')
    
    # 2. 效应量热图
    if len(group_comparison) > 0:
        pivot_data = group_comparison.pivot_table(index=['config'], values=['cohens_d'], aggfunc='first')
        pivot_data = pivot_data.fillna(0)
        
        sns.heatmap(pivot_data, annot=True, cmap='RdBu_r', center=0, ax=axes[0,1],
                    cbar_kws={'label': "Cohen's d"})
        axes[0,1].set_title('组别效应量热图')
        axes[0,1].set_xlabel('')
    
    # 3. 均值差异散点图
    if len(group_comparison) > 0:
        axes[1,0].scatter(group_comparison['deep_mean'], group_comparison['shallow_mean'], 
                         s=100, alpha=0.7)
        
        # 添加配置标签
        for _, row in group_comparison.iterrows():
            axes[1,0].annotate(row['config'], 
                              (row['deep_mean'], row['shallow_mean']),
                              xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # 添加对角线
        min_val = min(group_comparison['deep_mean'].min(), group_comparison['shallow_mean'].min())
        max_val = max(group_comparison['deep_mean'].max(), group_comparison['shallow_mean'].max())
        axes[1,0].plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='相等线')
        
        axes[1,0].set_xlabel('深度组均值')
        axes[1,0].set_ylabel('浅度组均值')
        axes[1,0].set_title('深度vs浅度组均值比较')
        axes[1,0].legend()
    
    # 4. 组别分布直方图
    deep_scores = exp_data[exp_data['group_type'] == 'deep']['score']
    shallow_scores = exp_data[exp_data['group_type'] == 'shallow']['score']
    
    axes[1,1].hist(deep_scores, alpha=0.6, label=f'深度组 (n={len(deep_scores)})', bins=15, color='blue')
    axes[1,1].hist(shallow_scores, alpha=0.6, label=f'浅度组 (n={len(shallow_scores)})', bins=8, color='red')
    
    axes[1,1].axvline(deep_scores.mean(), color='blue', linestyle='--', alpha=0.8, 
                     label=f'深度组均值: {deep_scores.mean():.2f}')
    axes[1,1].axvline(shallow_scores.mean(), color='red', linestyle='--', alpha=0.8,
                     label=f'浅度组均值: {shallow_scores.mean():.2f}')
    
    axes[1,1].set_xlabel('评分')
    axes[1,1].set_ylabel('频次')
    axes[1,1].set_title('组别评分分布')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig('group_effects_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 组别效应图表已保存: group_effects_analysis.png")
    plt.show()

def export_group_analysis_results(model_results, group_comparison):
    """导出组别分析结果"""
    output_dir = Path('data/processed_corrected')
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 导出组别比较结果
        if group_comparison is not None and len(group_comparison) > 0:
            group_comparison.to_csv(output_dir / 'group_effects_detailed.csv', index=False)
        
        # 导出模型结果摘要
        model_summaries = []
        for name, model in model_results.items():
            if model is not None:
                summary = {
                    'model_name': name,
                    'r_squared': model.rsquared,
                    'adj_r_squared': model.rsquared_adj,
                    'aic': model.aic,
                    'f_statistic': model.fvalue,
                    'f_pvalue': model.f_pvalue,
                    'n_obs': model.nobs
                }
                model_summaries.append(summary)
        
        if model_summaries:
            pd.DataFrame(model_summaries).to_csv(output_dir / 'robust_models_summary.csv', index=False)
        
        print(f"✅ 组别分析结果已导出到 {output_dir}/")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")

def main():
    """主分析流程"""
    print("🔧 稳健组别效应分析")
    print("="*60)
    
    # 加载数据
    try:
        long_table = pd.read_csv('data/processed/human_ratings_long.csv')
        print(f"✅ 数据加载成功: {long_table.shape}")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return
    
    # 1. 稳健组别效应OLS分析
    model_results, exp_data = robust_group_effects_ols(long_table)
    
    # 2. 详细组别比较
    group_comparison = detailed_group_comparison(long_table)
    
    # 3. 可视化
    if model_results and exp_data is not None:
        create_group_effects_visualization(group_comparison, exp_data)
    
    # 4. 导出结果
    export_group_analysis_results(model_results, group_comparison)
    
    print(f"\n" + "="*60)
    print("🎉 稳健组别效应分析完成！")
    print("="*60)
    
    print(f"\n🔑 核心发现:")
    if len(group_comparison) > 0:
        avg_effect = group_comparison['cohens_d'].mean()
        print(f"   平均效应量(Cohen's d): {avg_effect:+.3f}")
        
        significant_configs = group_comparison[np.abs(group_comparison['cohens_d']) > 0.2]
        if len(significant_configs) > 0:
            print(f"   有明显组别差异的配置: {significant_configs['config'].tolist()}")
        else:
            print(f"   所有配置的组别差异都很小 (|d| < 0.2)")
    
    return model_results, group_comparison, exp_data

if __name__ == "__main__":
    model_results, group_comparison, exp_data = main()
