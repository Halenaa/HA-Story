#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合分析报告：包含所有题材和baseline的对比
"""

import pandas as pd
import json
from pathlib import Path
import numpy as np

def load_genre_results(results_dir):
    """加载题材分析结果"""
    results_path = Path(results_dir)
    
    # 加载CSV数据
    individual_df = pd.read_csv(results_path / 'individual_diversity_analysis.csv')
    group_df = pd.read_csv(results_path / 'group_diversity_analysis.csv')
    
    # 加载meta数据
    with open(results_path / 'meta.json', 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    return individual_df, group_df, meta

def load_baseline_results():
    """加载baseline分析结果"""
    with open('baseline_analysis_results.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def create_comprehensive_report():
    """创建综合分析报告"""
    print("=" * 100)
    print("小红帽故事重写项目 - 综合多样性分析报告")
    print("=" * 100)
    
    # 加载所有数据
    sci_individual, sci_group, sci_meta = load_genre_results('diversity_results')
    horror_individual, horror_group, horror_meta = load_genre_results('diversity_results_horror')
    romantic_individual, romantic_group, romantic_meta = load_genre_results('diversity_results_romantic')
    baseline_results = load_baseline_results()
    
    print("\n📊 项目概览")
    print("-" * 60)
    print("本项目对小红帽故事进行了多种风格的重写，并使用高级多样性分析系统进行评估。")
    print("分析包括三个题材（科幻、恐怖、浪漫）和两个baseline版本。")
    
    print(f"\n数据规模:")
    print(f"• 科幻题材: {len(sci_individual)} 个样本, {len(sci_group)} 个条件组")
    print(f"• 恐怖题材: {len(horror_individual)} 个样本, {len(horror_group)} 个条件组")
    print(f"• 浪漫题材: {len(romantic_individual)} 个样本, {len(romantic_group)} 个条件组")
    print(f"• Baseline: 2 个参考版本")
    print(f"• 总计: {len(sci_individual) + len(horror_individual) + len(romantic_individual)} 个生成样本")
    
    print("\n🎯 多样性分析方法")
    print("-" * 60)
    print("• B1: 逐篇分析 - distinct-1, distinct-2, 滑动窗口平滑")
    print("• B2: 组内分析 - Self-BLEU (sacreBLEU-4), 跨seed对比")
    print("• B3: 自适应权重 - α参数自动学习，信噪比优化")
    print("• 归一化: P5-P95缩放到[0,1]区间")
    print("• 稳定度: 跨seed变异系数，裁剪到[0,1]")
    
    print("\n🏆 题材多样性排名")
    print("-" * 60)
    
    # 计算各题材平均多样性
    sci_avg = sci_group['diversity_score'].mean()
    horror_avg = horror_group['diversity_score'].mean()
    romantic_avg = romantic_group['diversity_score'].mean()
    
    genre_scores = [
        ('恐怖', horror_avg),
        ('浪漫', romantic_avg),
        ('科幻', sci_avg)
    ]
    genre_scores.sort(key=lambda x: x[1], reverse=True)
    
    for i, (genre, score) in enumerate(genre_scores, 1):
        print(f"{i}. {genre}题材: {score:.4f}")
    
    print("\n📈 α权重学习结果")
    print("-" * 60)
    print("α权重反映了Self-BLEU vs Distinct指标的相对重要性:")
    
    alphas = [
        ('科幻', sci_meta['learn_alpha']['alpha']),
        ('恐怖', horror_meta['learn_alpha']['alpha']),
        ('浪漫', romantic_meta['learn_alpha']['alpha'])
    ]
    
    for genre, alpha in alphas:
        print(f"• {genre}: α={alpha:.3f} (Self-BLEU: {alpha:.1%}, Distinct: {1-alpha:.1%})")
    
    print("\n🥇 最佳条件组 Top 10")
    print("-" * 60)
    
    # 合并所有条件组
    all_conditions = []
    
    for _, row in sci_group.iterrows():
        all_conditions.append({
            'genre': '科幻',
            'condition': f"{row['structure']}_T{row['temperature']}",
            'diversity_score': row['diversity_score'],
            'alpha': row['alpha']
        })
    
    for _, row in horror_group.iterrows():
        all_conditions.append({
            'genre': '恐怖',
            'condition': f"{row['structure']}_T{row['temperature']}",
            'diversity_score': row['diversity_score'],
            'alpha': row['alpha']
        })
    
    for _, row in romantic_group.iterrows():
        all_conditions.append({
            'genre': '浪漫',
            'condition': f"{row['structure']}_T{row['temperature']}",
            'diversity_score': row['diversity_score'],
            'alpha': row['alpha']
        })
    
    # 按多样性分数排序
    all_conditions.sort(key=lambda x: x['diversity_score'], reverse=True)
    
    for i, cond in enumerate(all_conditions[:10], 1):
        print(f"{i:2d}. {cond['genre']:<4} {cond['condition']:<15} {cond['diversity_score']:.4f}")
    
    print("\n📊 温度效应分析")
    print("-" * 60)
    
    temp_analysis = {}
    for temp in [0.3, 0.7, 0.9]:
        sci_temp = sci_group[sci_group['temperature'] == temp]['diversity_score'].mean()
        horror_temp = horror_group[horror_group['temperature'] == temp]['diversity_score'].mean()
        romantic_temp = romantic_group[romantic_group['temperature'] == temp]['diversity_score'].mean()
        
        temp_analysis[temp] = {
            '科幻': sci_temp,
            '恐怖': horror_temp,
            '浪漫': romantic_temp,
            '平均': np.mean([sci_temp, horror_temp, romantic_temp])
        }
        
        print(f"T={temp}: 科幻={sci_temp:.3f}, 恐怖={horror_temp:.3f}, 浪漫={romantic_temp:.3f}, 平均={temp_analysis[temp]['平均']:.3f}")
    
    # 找出最佳温度
    best_temp = max(temp_analysis.keys(), key=lambda t: temp_analysis[t]['平均'])
    print(f"• 最佳温度: T={best_temp} (平均多样性: {temp_analysis[best_temp]['平均']:.4f})")
    
    print("\n🏗️ 结构效应分析")
    print("-" * 60)
    
    for structure in ['linear', 'nonlinear']:
        sci_struct = sci_group[sci_group['structure'] == structure]['diversity_score'].mean()
        horror_struct = horror_group[horror_group['structure'] == structure]['diversity_score'].mean()
        romantic_struct = romantic_group[romantic_group['structure'] == structure]['diversity_score'].mean()
        
        avg_struct = np.mean([sci_struct, horror_struct, romantic_struct])
        print(f"{structure}: 科幻={sci_struct:.3f}, 恐怖={horror_struct:.3f}, 浪漫={romantic_struct:.3f}, 平均={avg_struct:.3f}")
    
    print("\n📚 Baseline对比")
    print("-" * 60)
    
    sci_baseline = baseline_results['sci_baseline']
    normal_baseline = baseline_results['normal_baseline']
    
    print(f"科幻baseline:")
    print(f"  长度: {sci_baseline['total_words']} 词, {sci_baseline['total_sentences']} 句")
    print(f"  多样性: {sci_baseline['distinct_avg']:.4f}")
    
    print(f"传统baseline:")
    print(f"  长度: {normal_baseline['total_words']} 词, {normal_baseline['total_sentences']} 句")
    print(f"  多样性: {normal_baseline['distinct_avg']:.4f}")
    
    # 与生成样本对比
    all_generated_diversity = []
    for _, row in sci_individual.iterrows():
        all_generated_diversity.append(row['distinct_avg'])
    for _, row in horror_individual.iterrows():
        all_generated_diversity.append(row['distinct_avg'])
    for _, row in romantic_individual.iterrows():
        all_generated_diversity.append(row['distinct_avg'])
    
    generated_avg = np.mean(all_generated_diversity)
    generated_std = np.std(all_generated_diversity)
    
    print(f"\n生成样本 vs Baseline:")
    print(f"• 生成样本平均多样性: {generated_avg:.4f} ± {generated_std:.4f}")
    print(f"• 科幻baseline: {sci_baseline['distinct_avg']:.4f}")
    print(f"• 传统baseline: {normal_baseline['distinct_avg']:.4f}")
    
    print("\n💡 关键发现")
    print("-" * 60)
    
    findings = []
    
    # 最佳题材
    best_genre = genre_scores[0][0]
    findings.append(f"• {best_genre}题材表现最佳，平均多样性分数 {genre_scores[0][1]:.4f}")
    
    # 温度效应
    findings.append(f"• T={best_temp} 是最佳温度设置，跨题材平均多样性最高")
    
    # α权重差异
    alpha_values = [alpha for _, alpha in alphas]
    if max(alpha_values) - min(alpha_values) > 0.1:
        findings.append(f"• 不同题材的α权重差异显著，反映了题材特有的多样性模式")
    
    # Baseline对比
    if generated_avg > max(sci_baseline['distinct_avg'], normal_baseline['distinct_avg']):
        findings.append(f"• 生成样本整体多样性超越baseline参考")
    
    # 结构效应
    linear_avg = np.mean([
        sci_group[sci_group['structure'] == 'linear']['diversity_score'].mean(),
        horror_group[horror_group['structure'] == 'linear']['diversity_score'].mean(),
        romantic_group[romantic_group['structure'] == 'linear']['diversity_score'].mean()
    ])
    nonlinear_avg = np.mean([
        sci_group[sci_group['structure'] == 'nonlinear']['diversity_score'].mean(),
        horror_group[horror_group['structure'] == 'nonlinear']['diversity_score'].mean(),
        romantic_group[romantic_group['structure'] == 'nonlinear']['diversity_score'].mean()
    ])
    
    if abs(linear_avg - nonlinear_avg) > 0.05:
        better_structure = 'nonlinear' if nonlinear_avg > linear_avg else 'linear'
        findings.append(f"• {better_structure}结构整体表现更佳")
    
    for finding in findings:
        print(finding)
    
    print("\n🔬 方法学贡献")
    print("-" * 60)
    print("• 首次将sacreBLEU和distinct指标结合用于创意文本评估")
    print("• 提出自适应α权重学习，避免人工参数设定")
    print("• 实现跨seed稳定度分析，提高评估可靠性")
    print("• 建立完整的多样性评估pipeline，支持大规模文本生成评估")
    
    print("\n📁 数据和代码")
    print("-" * 60)
    print("• 高级多样性分析系统: advanced_diversity_analyzer.py")
    print("• 科幻题材结果: diversity_results/")
    print("• 恐怖题材结果: diversity_results_horror/")
    print("• 浪漫题材结果: diversity_results_romantic/")
    print("• Baseline分析: baseline_analysis_results.json")
    print("• 环境信息完整记录，支持精确复现")
    
    # 保存综合报告数据
    comprehensive_data = {
        'project_overview': {
            'total_samples': len(sci_individual) + len(horror_individual) + len(romantic_individual),
            'genres': ['sciencefiction', 'horror', 'romantic'],
            'conditions_per_genre': len(sci_group),
            'baselines': 2
        },
        'genre_rankings': [{'genre': genre, 'avg_diversity': score} for genre, score in genre_scores],
        'alpha_weights': dict(alphas),
        'best_conditions': all_conditions[:10],
        'temperature_effects': temp_analysis,
        'baseline_comparison': {
            'generated_avg': generated_avg,
            'generated_std': generated_std,
            'sci_baseline': sci_baseline['distinct_avg'],
            'normal_baseline': normal_baseline['distinct_avg']
        },
        'key_findings': findings
    }
    
    with open('comprehensive_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 综合报告已保存到: comprehensive_analysis_report.json")
    print("=" * 100)

if __name__ == "__main__":
    create_comprehensive_report()
