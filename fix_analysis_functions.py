#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正问卷分析函数 - 处理深度评价vs浅度评价的不平衡问题
Fix Questionnaire Analysis Functions - Handle Deep vs Shallow Evaluation Imbalance

主要修正：
1. Config级别分析 - 区分Group A-F(深度9次) vs Group G(浅度1次)
2. Story级别分析 - 处理3人vs4人评价的不等权重
3. 种子稳定性分析 - 考虑组间差异
4. 混合效应模型 - 添加组别效应
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def identify_group_membership(long_table_df):
    """
    根据每个rater评价的story pattern识别其所属组别
    
    Returns:
        dict: {rater_id: {'group_type': 'deep'/'shallow', 'pattern': '...'}}
    """
    rater_groups = {}
    
    for rater_id in long_table_df['rater_id'].unique():
        rater_data = long_table_df[long_table_df['rater_id'] == rater_id]
        
        # 获取该rater评价的非baseline故事
        exp_stories = rater_data[rater_data['config'] != 'baseline']['story_id'].unique()
        exp_configs = rater_data[rater_data['config'] != 'baseline']['config'].unique()
        
        # 判断评价模式
        if len(exp_configs) == 1 and len(exp_stories) == 3:
            # 单一config的3个seeds - 深度评价组 (Group A-F)
            rater_groups[rater_id] = {
                'group_type': 'deep',
                'pattern': f"single_config_{exp_configs[0]}",
                'n_configs': 1,
                'n_stories': 3
            }
        elif len(exp_configs) > 1:
            # 多个configs的单一seeds - 浅度评价组 (Group G)
            rater_groups[rater_id] = {
                'group_type': 'shallow', 
                'pattern': f"multi_config_{len(exp_configs)}",
                'n_configs': len(exp_configs),
                'n_stories': len(exp_stories)
            }
        else:
            # 其他异常情况
            rater_groups[rater_id] = {
                'group_type': 'unknown',
                'pattern': f"unknown_{len(exp_configs)}c_{len(exp_stories)}s",
                'n_configs': len(exp_configs),
                'n_stories': len(exp_stories)
            }
    
    return rater_groups

def create_corrected_config_aggregation(long_table_df):
    """
    修正版Config级别聚合 - 考虑深度vs浅度评价的质量差异
    
    Args:
        long_table_df: 长格式数据表
        
    Returns:
        pd.DataFrame: 修正后的config聚合数据
    """
    # 1. 识别组别
    rater_groups = identify_group_membership(long_table_df)
    
    # 2. 为数据添加组别标识
    working_df = long_table_df.copy()
    working_df['group_type'] = working_df['rater_id'].map(
        lambda x: rater_groups.get(x, {}).get('group_type', 'unknown')
    )
    
    # 3. 分层聚合
    results = []
    
    for config in working_df['config'].unique():
        if config == 'baseline':
            # Baseline使用标准聚合
            config_data = working_df[working_df['config'] == config]
            for dimension in config_data['dimension'].unique():
                dim_data = config_data[config_data['dimension'] == dimension]
                
                results.append({
                    'config': config,
                    'structure': None,
                    'temperature': None,
                    'dimension': dimension,
                    'mean_score': dim_data['score'].mean(),
                    'corrected_mean': dim_data['score'].mean(),  # baseline无需修正
                    'std_score': dim_data['score'].std(),
                    'n_ratings': len(dim_data),
                    'n_deep_eval': len(dim_data),  # baseline全为深度评价
                    'n_shallow_eval': 0,
                    'eval_balance': 1.0,
                    'quality_score': 1.0  # baseline质量分数为1.0
                })
        else:
            # 实验配置使用修正聚合
            config_data = working_df[working_df['config'] == config]
            
            for dimension in config_data['dimension'].unique():
                dim_data = config_data[config_data['dimension'] == dimension]
                
                # 分离深度和浅度评价
                deep_data = dim_data[dim_data['group_type'] == 'deep']
                shallow_data = dim_data[dim_data['group_type'] == 'shallow']
                
                # 计算统计量
                n_deep = len(deep_data)
                n_shallow = len(shallow_data)
                total_n = n_deep + n_shallow
                
                if total_n == 0:
                    continue
                
                # 质量加权聚合（深度评价权重更高）
                deep_weight = 0.8  # 深度评价权重80%
                shallow_weight = 0.2  # 浅度评价权重20%
                
                # 归一化权重
                actual_deep_prop = n_deep / total_n
                actual_shallow_prop = n_shallow / total_n
                
                if n_deep > 0 and n_shallow > 0:
                    # 质量加权均值
                    corrected_mean = (
                        deep_data['score'].mean() * deep_weight + 
                        shallow_data['score'].mean() * shallow_weight
                    )
                elif n_deep > 0:
                    corrected_mean = deep_data['score'].mean()
                else:
                    corrected_mean = shallow_data['score'].mean()
                
                # 原始等权重均值
                raw_mean = dim_data['score'].mean()
                
                # 数据质量分数（深度评价比例越高质量分数越高）
                quality_score = actual_deep_prop * 0.9 + 0.1  # 最低0.1，最高1.0
                
                results.append({
                    'config': config,
                    'structure': dim_data['structure'].iloc[0] if 'structure' in dim_data.columns else None,
                    'temperature': dim_data['temperature'].iloc[0] if 'temperature' in dim_data.columns else None,
                    'dimension': dimension,
                    'mean_score': raw_mean,  # 原始均值
                    'corrected_mean': corrected_mean,  # 质量修正均值  
                    'std_score': dim_data['score'].std(),
                    'n_ratings': total_n,
                    'n_deep_eval': n_deep,
                    'n_shallow_eval': n_shallow,
                    'eval_balance': actual_deep_prop,
                    'quality_score': quality_score
                })
    
    return pd.DataFrame(results).round(3)

def create_corrected_story_aggregation(long_table_df):
    """
    修正版Story级别聚合 - 处理评价者数量不等的权重问题
    """
    rater_groups = identify_group_membership(long_table_df)
    working_df = long_table_df.copy()
    working_df['group_type'] = working_df['rater_id'].map(
        lambda x: rater_groups.get(x, {}).get('group_type', 'unknown')
    )
    
    results = []
    
    for story_id in working_df['story_id'].unique():
        story_data = working_df[working_df['story_id'] == story_id]
        
        for dimension in story_data['dimension'].unique():
            dim_data = story_data[story_data['dimension'] == dimension]
            
            # 计算评价者构成
            deep_raters = dim_data[dim_data['group_type'] == 'deep']['rater_id'].nunique()
            shallow_raters = dim_data[dim_data['group_type'] == 'shallow']['rater_id'].nunique()
            total_raters = dim_data['rater_id'].nunique()
            
            # 标准误修正（考虑评价者数量差异）
            if total_raters > 1:
                # 使用Bessel修正
                corrected_std = dim_data['score'].std(ddof=1) * np.sqrt((total_raters - 1) / total_raters)
                std_error = corrected_std / np.sqrt(total_raters)
            else:
                corrected_std = 0
                std_error = np.inf
            
            results.append({
                'story_id': story_id,
                'config': dim_data['config'].iloc[0] if 'config' in dim_data.columns else None,
                'seed': dim_data['seed'].iloc[0] if 'seed' in dim_data.columns else None,
                'structure': dim_data['structure'].iloc[0] if 'structure' in dim_data.columns else None,
                'temperature': dim_data['temperature'].iloc[0] if 'temperature' in dim_data.columns else None,
                'dimension': dimension,
                'mean_score': dim_data['score'].mean(),
                'std_score': corrected_std,
                'std_error': std_error,
                'n_ratings': len(dim_data),
                'n_raters': total_raters,
                'n_deep_raters': deep_raters,
                'n_shallow_raters': shallow_raters,
                'rater_balance': deep_raters / total_raters if total_raters > 0 else 0,
                'reliability_weight': min(1.0, total_raters / 4.0)  # 权重：4人为满分
            })
    
    return pd.DataFrame(results).round(3)

def corrected_seed_stability_analysis(long_table_df, focus_dim='Overall Quality'):
    """
    修正版种子稳定性分析 - 考虑组间效应
    """
    from scipy.stats import levene, kruskal
    
    rater_groups = identify_group_membership(long_table_df)
    working_df = long_table_df.copy()
    working_df['group_type'] = working_df['rater_id'].map(
        lambda x: rater_groups.get(x, {}).get('group_type', 'unknown')
    )
    
    # 筛选目标维度
    focus_data = working_df[
        (working_df['dimension'] == focus_dim) & 
        (working_df['config'] != 'baseline')
    ].copy()
    
    results = []
    
    for config in focus_data['config'].unique():
        config_data = focus_data[focus_data['config'] == config]
        
        # 按seed聚合（考虑组别权重）
        seed_stats = []
        seed_groups = []  # 用于方差齐性检验
        
        for seed in config_data['seed'].unique():
            if pd.isna(seed):
                continue
                
            seed_data = config_data[config_data['seed'] == seed]
            
            # 分组统计
            deep_scores = seed_data[seed_data['group_type'] == 'deep']['score']
            shallow_scores = seed_data[seed_data['group_type'] == 'shallow']['score']
            
            # 质量加权均值
            if len(deep_scores) > 0 and len(shallow_scores) > 0:
                weighted_mean = deep_scores.mean() * 0.8 + shallow_scores.mean() * 0.2
            elif len(deep_scores) > 0:
                weighted_mean = deep_scores.mean()
            elif len(shallow_scores) > 0:
                weighted_mean = shallow_scores.mean()
            else:
                continue
                
            seed_stats.append({
                'seed': seed,
                'weighted_mean': weighted_mean,
                'raw_mean': seed_data['score'].mean(),
                'n_deep': len(deep_scores),
                'n_shallow': len(shallow_scores),
                'n_total': len(seed_data)
            })
            
            # 收集用于方差检验的数据
            seed_groups.append(seed_data['score'].values)
        
        if len(seed_stats) < 2:
            continue
            
        seed_df = pd.DataFrame(seed_stats)
        
        # 种子间稳定性统计
        weighted_means = seed_df['weighted_mean'].values
        raw_means = seed_df['raw_mean'].values
        
        # 变异系数
        cv_weighted = np.std(weighted_means, ddof=1) / np.mean(weighted_means) if np.mean(weighted_means) != 0 else np.nan
        cv_raw = np.std(raw_means, ddof=1) / np.mean(raw_means) if np.mean(raw_means) != 0 else np.nan
        
        # Levene检验（方差齐性）
        try:
            if len(seed_groups) >= 2 and all(len(g) > 1 for g in seed_groups):
                levene_stat, levene_p = levene(*seed_groups, center='median')
            else:
                levene_stat, levene_p = np.nan, np.nan
        except:
            levene_stat, levene_p = np.nan, np.nan
        
        # Kruskal-Wallis检验（分布差异）
        try:
            if len(seed_groups) >= 2 and all(len(g) > 0 for g in seed_groups):
                kruskal_stat, kruskal_p = kruskal(*seed_groups)
            else:
                kruskal_stat, kruskal_p = np.nan, np.nan
        except:
            kruskal_stat, kruskal_p = np.nan, np.nan
        
        results.append({
            'config': config,
            'n_seeds': len(seed_stats),
            'mean_weighted': np.mean(weighted_means),
            'mean_raw': np.mean(raw_means),
            'std_weighted': np.std(weighted_means, ddof=1),
            'std_raw': np.std(raw_means, ddof=1),
            'cv_weighted': cv_weighted,
            'cv_raw': cv_raw,
            'levene_stat': levene_stat,
            'levene_p': levene_p,
            'kruskal_stat': kruskal_stat,
            'kruskal_p': kruskal_p,
            'stability_quality': 'High' if cv_weighted < 0.15 else 'Medium' if cv_weighted < 0.30 else 'Low'
        })
    
    return pd.DataFrame(results).round(4)

def corrected_bradley_terry_analysis(pairwise_df, story_agg_df):
    """
    修正版Bradley-Terry分析 - 添加评价次数权重
    """
    # 合并story聚合信息（包含reliability_weight）
    enhanced_pairwise = pairwise_df.merge(
        story_agg_df[['story_id', 'reliability_weight']].drop_duplicates(),
        left_on='winner_story_id', right_on='story_id', how='left'
    ).rename(columns={'reliability_weight': 'winner_weight'})
    
    enhanced_pairwise = enhanced_pairwise.merge(
        story_agg_df[['story_id', 'reliability_weight']].drop_duplicates(), 
        left_on='loser_story_id', right_on='story_id', how='left'
    ).rename(columns={'reliability_weight': 'loser_weight'})
    
    # 计算比较权重（取两者平均）
    enhanced_pairwise['comparison_weight'] = (
        enhanced_pairwise['winner_weight'].fillna(1.0) + 
        enhanced_pairwise['loser_weight'].fillna(1.0)
    ) / 2
    
    # 加权Bradley-Terry评分
    story_scores = {}
    story_comparisons = {}
    
    for _, row in enhanced_pairwise.iterrows():
        winner = row['winner_story_id']
        loser = row['loser_story_id'] 
        weight = row['comparison_weight']
        
        if winner not in story_scores:
            story_scores[winner] = 0
            story_comparisons[winner] = {'wins': 0, 'losses': 0, 'total_weight': 0}
        if loser not in story_scores:
            story_scores[loser] = 0
            story_comparisons[loser] = {'wins': 0, 'losses': 0, 'total_weight': 0}
        
        # 加权得分更新
        story_scores[winner] += weight
        story_scores[loser] -= weight * 0.5  # 失败惩罚权重减半
        
        # 统计信息更新
        story_comparisons[winner]['wins'] += weight
        story_comparisons[winner]['total_weight'] += weight
        story_comparisons[loser]['losses'] += weight  
        story_comparisons[loser]['total_weight'] += weight
    
    # 生成排名表
    results = []
    for story_id, score in story_scores.items():
        comp_info = story_comparisons[story_id]
        win_rate = comp_info['wins'] / comp_info['total_weight'] if comp_info['total_weight'] > 0 else 0
        
        results.append({
            'story_id': story_id,
            'bt_score': score,
            'weighted_wins': comp_info['wins'],
            'weighted_losses': comp_info['losses'],
            'total_weight': comp_info['total_weight'],
            'weighted_win_rate': win_rate,
            'confidence': min(1.0, comp_info['total_weight'] / 10.0)  # 基于权重总数的信心分数
        })
    
    result_df = pd.DataFrame(results).sort_values('bt_score', ascending=False).reset_index(drop=True)
    result_df['rank'] = range(1, len(result_df) + 1)
    
    return result_df

if __name__ == "__main__":
    print("🔧 问卷分析修正函数已加载")
    print("主要修正内容：")
    print("1. ✅ Config级别分析 - 区分深度(9次)vs浅度(1次)评价") 
    print("2. ✅ Story级别分析 - 处理3人vs4人评价权重")
    print("3. ✅ 种子稳定性分析 - 考虑组间效应") 
    print("4. ✅ Bradley-Terry分析 - 添加评价次数权重")
    print()
    print("使用方法：")
    print(">>> import fix_analysis_functions as fix")
    print(">>> corrected_config = fix.create_corrected_config_aggregation(long_table)")
    print(">>> corrected_story = fix.create_corrected_story_aggregation(long_table)")
