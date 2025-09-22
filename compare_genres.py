#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较不同题材的多样性分析结果
"""

import pandas as pd
import json
from pathlib import Path

def load_results(results_dir):
    """加载分析结果"""
    results_path = Path(results_dir)
    
    # 加载CSV数据
    individual_df = pd.read_csv(results_path / 'individual_diversity_analysis.csv')
    group_df = pd.read_csv(results_path / 'group_diversity_analysis.csv')
    
    # 加载meta数据
    with open(results_path / 'meta.json', 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    return individual_df, group_df, meta

def compare_genres():
    """比较不同题材的结果"""
    print("=" * 80)
    print("三题材多样性对比分析")
    print("=" * 80)
    
    # 加载三个题材的结果
    sci_individual, sci_group, sci_meta = load_results('diversity_results')
    horror_individual, horror_group, horror_meta = load_results('diversity_results_horror')
    romantic_individual, romantic_group, romantic_meta = load_results('diversity_results_romantic')
    
    print("\n📊 基本统计")
    print("-" * 40)
    print(f"科幻题材: {len(sci_individual)} 个样本, {len(sci_group)} 个条件组")
    print(f"恐怖题材: {len(horror_individual)} 个样本, {len(horror_group)} 个条件组")
    print(f"浪漫题材: {len(romantic_individual)} 个样本, {len(romantic_group)} 个条件组")
    
    print(f"\n科幻α权重: {sci_meta['learn_alpha']['alpha']:.4f}")
    print(f"恐怖α权重: {horror_meta['learn_alpha']['alpha']:.4f}")
    print(f"浪漫α权重: {romantic_meta['learn_alpha']['alpha']:.4f}")
    
    print("\n🎯 逐篇多样性对比")
    print("-" * 40)
    
    # 逐篇多样性统计
    sci_distinct_avg = sci_individual['distinct_avg']
    horror_distinct_avg = horror_individual['distinct_avg']
    romantic_distinct_avg = romantic_individual['distinct_avg']
    
    print(f"科幻 distinct_avg: {sci_distinct_avg.mean():.4f} ± {sci_distinct_avg.std():.4f} (范围: {sci_distinct_avg.min():.4f} - {sci_distinct_avg.max():.4f})")
    print(f"恐怖 distinct_avg: {horror_distinct_avg.mean():.4f} ± {horror_distinct_avg.std():.4f} (范围: {horror_distinct_avg.min():.4f} - {horror_distinct_avg.max():.4f})")
    print(f"浪漫 distinct_avg: {romantic_distinct_avg.mean():.4f} ± {romantic_distinct_avg.std():.4f} (范围: {romantic_distinct_avg.min():.4f} - {romantic_distinct_avg.max():.4f})")
    
    print("\n🏆 组内多样性对比")
    print("-" * 40)
    
    # 组内多样性统计
    sci_diversity = sci_group['diversity_score']
    horror_diversity = horror_group['diversity_score']
    romantic_diversity = romantic_group['diversity_score']
    
    print(f"科幻 diversity_score: {sci_diversity.mean():.4f} ± {sci_diversity.std():.4f} (范围: {sci_diversity.min():.4f} - {sci_diversity.max():.4f})")
    print(f"恐怖 diversity_score: {horror_diversity.mean():.4f} ± {horror_diversity.std():.4f} (范围: {horror_diversity.min():.4f} - {horror_diversity.max():.4f})")
    print(f"浪漫 diversity_score: {romantic_diversity.mean():.4f} ± {romantic_diversity.std():.4f} (范围: {romantic_diversity.min():.4f} - {romantic_diversity.max():.4f})")
    
    print("\n📈 温度效应分析")
    print("-" * 40)
    
    # 按温度分组分析
    for temp in [0.3, 0.7, 0.9]:
        sci_temp = sci_group[sci_group['temperature'] == temp]['diversity_score']
        horror_temp = horror_group[horror_group['temperature'] == temp]['diversity_score']
        romantic_temp = romantic_group[romantic_group['temperature'] == temp]['diversity_score']
        
        print(f"T={temp}:")
        print(f"  科幻: {sci_temp.mean():.4f} (n={len(sci_temp)})")
        print(f"  恐怖: {horror_temp.mean():.4f} (n={len(horror_temp)})")
        print(f"  浪漫: {romantic_temp.mean():.4f} (n={len(romantic_temp)})")
    
    print("\n🏗️ 结构效应分析")
    print("-" * 40)
    
    # 按结构分组分析
    for structure in ['linear', 'nonlinear']:
        sci_struct = sci_group[sci_group['structure'] == structure]['diversity_score']
        horror_struct = horror_group[horror_group['structure'] == structure]['diversity_score']
        romantic_struct = romantic_group[romantic_group['structure'] == structure]['diversity_score']
        
        print(f"{structure}:")
        print(f"  科幻: {sci_struct.mean():.4f} (n={len(sci_struct)})")
        print(f"  恐怖: {horror_struct.mean():.4f} (n={len(horror_struct)})")
        print(f"  浪漫: {romantic_struct.mean():.4f} (n={len(romantic_struct)})")
    
    print("\n🥇 最佳条件组排名")
    print("-" * 40)
    
    # 合并三个题材的结果
    all_groups = []
    
    for _, row in sci_group.iterrows():
        all_groups.append({
            'genre': 'sciencefiction',
            'condition': f"{row['structure']}_T{row['temperature']}",
            'diversity_score': row['diversity_score']
        })
    
    for _, row in horror_group.iterrows():
        all_groups.append({
            'genre': 'horror',
            'condition': f"{row['structure']}_T{row['temperature']}",
            'diversity_score': row['diversity_score']
        })
    
    for _, row in romantic_group.iterrows():
        all_groups.append({
            'genre': 'romantic',
            'condition': f"{row['structure']}_T{row['temperature']}",
            'diversity_score': row['diversity_score']
        })
    
    # 按多样性分数排序
    all_groups.sort(key=lambda x: x['diversity_score'], reverse=True)
    
    print("Top 10 最高多样性条件:")
    for i, group in enumerate(all_groups[:10], 1):
        print(f"{i:2d}. {group['genre']:<15} {group['condition']:<15} {group['diversity_score']:.4f}")
    
    print("\n📊 Self-BLEU vs Distinct权重对比")
    print("-" * 40)
    
    sci_alpha = sci_meta['learn_alpha']['alpha']
    horror_alpha = horror_meta['learn_alpha']['alpha']
    romantic_alpha = romantic_meta['learn_alpha']['alpha']
    
    print(f"科幻题材:")
    print(f"  Self-BLEU权重: {sci_alpha:.1%}")
    print(f"  Distinct权重:  {1-sci_alpha:.1%}")
    
    print(f"恐怖题材:")
    print(f"  Self-BLEU权重: {horror_alpha:.1%}")
    print(f"  Distinct权重:  {1-horror_alpha:.1%}")
    
    print(f"浪漫题材:")
    print(f"  Self-BLEU权重: {romantic_alpha:.1%}")
    print(f"  Distinct权重:  {1-romantic_alpha:.1%}")
    
    print("\n💡 关键发现")
    print("-" * 40)
    
    # 分析关键发现
    if horror_diversity.mean() > sci_diversity.mean():
        print(f"• 恐怖题材整体多样性更高 ({horror_diversity.mean():.4f} vs {sci_diversity.mean():.4f})")
    else:
        print(f"• 科幻题材整体多样性更高 ({sci_diversity.mean():.4f} vs {horror_diversity.mean():.4f})")
    
    if horror_alpha > sci_alpha:
        print(f"• 恐怖题材更依赖Self-BLEU指标 (α={horror_alpha:.3f} vs {sci_alpha:.3f})")
    else:
        print(f"• 科幻题材更依赖Self-BLEU指标 (α={sci_alpha:.3f} vs {horror_alpha:.3f})")
    
    # 找出最佳温度
    best_temp_sci = sci_group.loc[sci_group['diversity_score'].idxmax(), 'temperature']
    best_temp_horror = horror_group.loc[horror_group['diversity_score'].idxmax(), 'temperature']
    
    print(f"• 科幻题材最佳温度: T={best_temp_sci}")
    print(f"• 恐怖题材最佳温度: T={best_temp_horror}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    compare_genres()
