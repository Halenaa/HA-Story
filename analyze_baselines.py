#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析baseline文件的多样性
"""

import os
import sys
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from advanced_diversity_analyzer import AdvancedDiversityAnalyzer

def analyze_single_baseline(file_path, output_name, tokenizer='simple'):
    """分析单个baseline文件"""
    print(f"\n分析 {file_path}...")
    
    # 创建临时目录结构
    temp_dir = Path(f"temp_baseline_{output_name}")
    temp_dir.mkdir(exist_ok=True)
    
    # 创建子目录（模拟参数配置）
    # 使用标准的命名格式，让分析器能正确解析
    sub_dir = temp_dir / f"baseline_{output_name}rewrite_linear_T1.0_s1"
    sub_dir.mkdir(exist_ok=True)
    
    # 复制文件到临时目录
    import shutil
    target_file = sub_dir / "enhanced_story_dialogue_updated.md"
    shutil.copy2(file_path, target_file)
    
    # 创建输出目录
    output_dir = f"diversity_results_baseline_{output_name}"
    
    try:
        # 初始化分析器
        analyzer = AdvancedDiversityAnalyzer(
            data_dir=str(temp_dir),
            output_dir=output_dir,
            window=1000,
            stride=500,
            bleu_sample_every=1,
            tokenizer=tokenizer,
            p_low=5,
            p_high=95,
            alpha_min=0.4,
            alpha_max=0.8
        )
        
        # 运行分析
        individual_results, group_results = analyzer.run_analysis()
        analyzer.save_results()
        
        print(f"✓ {output_name} 分析完成，结果保存到: {output_dir}")
        
        # 返回结果
        return individual_results, group_results, output_dir
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

def compare_baselines():
    """比较两个baseline的结果"""
    print("=" * 80)
    print("Baseline文件多样性分析")
    print("=" * 80)
    
    # 分析两个baseline文件
    sci_results, sci_group, sci_dir = analyze_single_baseline(
        "/Users/haha/Story/data/sci_baseline.md", 
        "sci"
    )
    
    normal_results, normal_group, normal_dir = analyze_single_baseline(
        "/Users/haha/Story/data/normal_baseline.md", 
        "normal"
    )
    
    # 提取结果数据
    sci_key = list(sci_results.keys())[0]
    normal_key = list(normal_results.keys())[0]
    
    sci_data = sci_results[sci_key]
    normal_data = normal_results[normal_key]
    
    print("\n" + "=" * 80)
    print("Baseline对比分析结果")
    print("=" * 80)
    
    print("\n📊 基本统计")
    print("-" * 40)
    print(f"科幻baseline: {sci_data['total_words']} 词, {sci_data['total_sentences']} 句")
    print(f"传统baseline: {normal_data['total_words']} 词, {normal_data['total_sentences']} 句")
    
    print("\n🎯 多样性指标对比")
    print("-" * 40)
    print(f"科幻baseline:")
    print(f"  distinct_1: {sci_data['distinct_1']:.4f}")
    print(f"  distinct_2: {sci_data['distinct_2']:.4f}")
    print(f"  distinct_avg: {sci_data['distinct_avg']:.4f}")
    
    print(f"传统baseline:")
    print(f"  distinct_1: {normal_data['distinct_1']:.4f}")
    print(f"  distinct_2: {normal_data['distinct_2']:.4f}")
    print(f"  distinct_avg: {normal_data['distinct_avg']:.4f}")
    
    print("\n📈 相对比较")
    print("-" * 40)
    
    # 计算相对差异
    distinct_1_diff = (sci_data['distinct_1'] - normal_data['distinct_1']) / normal_data['distinct_1'] * 100
    distinct_2_diff = (sci_data['distinct_2'] - normal_data['distinct_2']) / normal_data['distinct_2'] * 100
    distinct_avg_diff = (sci_data['distinct_avg'] - normal_data['distinct_avg']) / normal_data['distinct_avg'] * 100
    
    print(f"科幻相对传统baseline:")
    print(f"  distinct_1: {distinct_1_diff:+.1f}%")
    print(f"  distinct_2: {distinct_2_diff:+.1f}%")
    print(f"  distinct_avg: {distinct_avg_diff:+.1f}%")
    
    # 词汇密度比较
    sci_density = sci_data['total_words'] / sci_data['total_sentences']
    normal_density = normal_data['total_words'] / normal_data['total_sentences']
    density_diff = (sci_density - normal_density) / normal_density * 100
    
    print(f"\n词汇密度:")
    print(f"  科幻: {sci_density:.1f} 词/句")
    print(f"  传统: {normal_density:.1f} 词/句")
    print(f"  差异: {density_diff:+.1f}%")
    
    print("\n💡 关键发现")
    print("-" * 40)
    
    if sci_data['distinct_avg'] > normal_data['distinct_avg']:
        print(f"• 科幻baseline词汇多样性更高 ({sci_data['distinct_avg']:.4f} vs {normal_data['distinct_avg']:.4f})")
    else:
        print(f"• 传统baseline词汇多样性更高 ({normal_data['distinct_avg']:.4f} vs {sci_data['distinct_avg']:.4f})")
    
    if sci_data['total_words'] > normal_data['total_words']:
        print(f"• 科幻baseline更长 ({sci_data['total_words']} vs {normal_data['total_words']} 词)")
    else:
        print(f"• 传统baseline更长 ({normal_data['total_words']} vs {sci_data['total_words']} 词)")
    
    # 风格分析
    print(f"\n🎨 风格特征")
    print("-" * 40)
    
    # 读取文件内容进行简单的风格分析
    with open("/Users/haha/Story/data/sci_baseline.md", 'r', encoding='utf-8') as f:
        sci_content = f.read().lower()
    
    with open("/Users/haha/Story/data/normal_baseline.md", 'r', encoding='utf-8') as f:
        normal_content = f.read().lower()
    
    # 科幻词汇
    sci_words = ['station', 'algorithm', 'data', 'network', 'drone', 'bio-signal', 'radiation']
    sci_count = sum(sci_content.count(word) for word in sci_words)
    
    # 传统词汇
    traditional_words = ['forest', 'cottage', 'grandmother', 'wolf', 'path', 'village', 'woods']
    trad_count = sum(normal_content.count(word) for word in traditional_words)
    
    print(f"科幻特征词频: {sci_count}")
    print(f"传统特征词频: {trad_count}")
    
    print("\n📁 结果文件")
    print("-" * 40)
    print(f"科幻baseline结果: {sci_dir}/")
    print(f"传统baseline结果: {normal_dir}/")
    
    print("\n" + "=" * 80)
    
    return sci_data, normal_data

def create_baseline_summary():
    """创建baseline分析摘要"""
    print("创建baseline分析摘要...")
    
    # 运行分析
    sci_data, normal_data = compare_baselines()
    
    # 创建摘要数据
    summary = {
        'sci_baseline': {
            'file': 'data/sci_baseline.md',
            'total_words': sci_data['total_words'],
            'total_sentences': sci_data['total_sentences'],
            'distinct_1': sci_data['distinct_1'],
            'distinct_2': sci_data['distinct_2'],
            'distinct_avg': sci_data['distinct_avg'],
            'word_per_sentence': sci_data['total_words'] / sci_data['total_sentences']
        },
        'normal_baseline': {
            'file': 'data/normal_baseline.md',
            'total_words': normal_data['total_words'],
            'total_sentences': normal_data['total_sentences'],
            'distinct_1': normal_data['distinct_1'],
            'distinct_2': normal_data['distinct_2'],
            'distinct_avg': normal_data['distinct_avg'],
            'word_per_sentence': normal_data['total_words'] / normal_data['total_sentences']
        }
    }
    
    # 保存摘要
    with open('baseline_analysis_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("摘要已保存到: baseline_analysis_summary.json")

if __name__ == "__main__":
    create_baseline_summary()
