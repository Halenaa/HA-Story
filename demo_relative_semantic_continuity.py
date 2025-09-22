#!/usr/bin/env python3
"""
演示语义连续性相对比较系统的使用
展示如何将绝对分数转换为"高于X%样本"的相对评价
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加路径
sys.path.append('/Users/haha/Story/src/utils')
sys.path.append('/Users/haha/Story/src/analysis')

from semantic_continuity_relative_comparison import SemanticContinuityRelativeComparison
from hred_coherence_evaluator import HREDSemanticContinuityEvaluator

def load_reference_data():
    """加载参考数据集"""
    print("📊 加载参考数据集...")
    
    # 从CSV加载所有样本的语义连续性分数
    df = pd.read_csv('/Users/haha/Story/metrics_master_clean.csv')
    scores = df['avg_semantic_continuity'].dropna().tolist()
    
    print(f"✅ 成功加载 {len(scores)} 个样本作为参考基准")
    print(f"   分数范围: {min(scores):.4f} - {max(scores):.4f}")
    print(f"   平均值: {np.mean(scores):.4f}")
    print(f"   标准差: {np.std(scores):.4f}")
    
    return scores

def analyze_story_with_relative_comparison(story_file, story_name):
    """分析单个故事并提供相对比较"""
    print(f"\n{'='*60}")
    print(f"🔍 分析故事: {story_name}")
    print(f"{'='*60}")
    
    # 读取故事文件
    with open(story_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析章节
    chapters = []
    current_chapter = None
    for line in content.split('\n'):
        if line.startswith('# Chapter '):
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = {'title': line[2:].strip(), 'plot': ''}
        elif current_chapter and line.strip():
            current_chapter['plot'] += line.strip() + ' '
    
    if current_chapter:
        chapters.append(current_chapter)
    
    # 清理plot字段
    for chapter in chapters:
        chapter['plot'] = chapter['plot'].strip()
    
    print(f"📝 解析出 {len(chapters)} 个章节")
    
    # 进行语义连续性分析
    print("🔬 进行语义连续性分析...")
    evaluator = HREDSemanticContinuityEvaluator()
    result = evaluator.evaluate_story_semantic_continuity(chapters)
    
    # 提取分析结果
    continuity_eval = result.get('HRED_semantic_continuity_evaluation', {})
    avg_continuity = continuity_eval.get('average_semantic_continuity')
    sentence_count = continuity_eval.get('total_sentences')
    
    print(f"📊 绝对分数结果:")
    print(f"   平均语义连续性: {avg_continuity:.4f}")
    print(f"   分析句子数: {sentence_count}")
    
    return avg_continuity

def demonstrate_relative_comparison():
    """演示相对比较系统"""
    print("🎯 语义连续性相对比较系统演示")
    print("=" * 80)
    
    # 1. 加载参考数据
    reference_scores = load_reference_data()
    
    # 2. 创建比较系统
    comparator = SemanticContinuityRelativeComparison()
    comparator.add_baseline_data(reference_scores, 'research_corpus')
    
    # 3. 分析几个baseline故事
    baseline_files = {
        'baseline_s1': '/Users/haha/Story/baseline_s1.md',
        'baseline_s2': '/Users/haha/Story/baseline_s2.md',
        'baseline_s3': '/Users/haha/Story/baseline_s3.md'
    }
    
    results = {}
    
    for story_name, story_file in baseline_files.items():
        if Path(story_file).exists():
            score = analyze_story_with_relative_comparison(story_file, story_name)
            if score is not None:
                results[story_name] = score
    
    # 4. 进行相对比较分析
    print(f"\n{'='*60}")
    print("📈 相对比较分析结果")
    print(f"{'='*60}")
    
    for story_name, score in results.items():
        comparison = comparator.compare_to_baseline(score, 'research_corpus')
        
        print(f"\n🎪 {story_name}:")
        print(f"   📊 绝对分数: {score:.4f}")
        print(f"   📈 相对位置: {comparison['comparison_description']}")
        print(f"   🎯 百分位排名: 第{comparison['percentile_rank']}百分位")
        print(f"   📝 评价等级: {comparison['position_description']}")
        print(f"   ⚠️  说明: {comparison['measurement_note']}")
    
    # 5. 生成分布总结
    print(f"\n{'='*60}")
    print("📊 参考数据集分布总结")
    print(f"{'='*60}")
    
    distribution = comparator.generate_distribution_summary('research_corpus')
    dist_summary = distribution['distribution_summary']
    
    print(f"📈 基准数据集统计 ({distribution['sample_count']} 个样本):")
    print(f"   平均值: {dist_summary['mean']:.4f}")
    print(f"   标准差: {dist_summary['std']:.4f}")
    print(f"   分数范围: {dist_summary['min']:.4f} - {dist_summary['max']:.4f}")
    
    percentiles = distribution['percentile_benchmarks']
    print(f"\n🎯 百分位基准:")
    for desc, pct, value in [
        ("低水平分界线", "25th", percentiles['p25']),
        ("中位数", "50th", percentiles['p50']),
        ("较高水平分界线", "75th", percentiles['p75']),
        ("高水平分界线", "90th", percentiles['p90']),
        ("极高水平分界线", "95th", percentiles['p95'])
    ]:
        print(f"   {desc} ({pct}): {value:.4f}")
    
    # 6. 改进建议
    print(f"\n{'='*60}")
    print("💡 相对比较系统的优势")
    print(f"{'='*60}")
    
    improvements = [
        "✅ 避免主观阈值：不再使用'0.7=优秀'等武断标准",
        "✅ 基于数据驱动：基于实际样本分布进行比较",
        "✅ 提供相对位置：'高于73.2%的样本'更有意义",
        "✅ 诚实表述局限：明确说明仅测量语义相似度",
        "✅ 科学严谨性：基于百分位排名的客观评价",
        "✅ 可解释性强：用户更容易理解相对位置"
    ]
    
    for improvement in improvements:
        print(f"   {improvement}")
    
    print(f"\n🎉 相对比较系统演示完成！")
    print("这个系统现在提供更加诚实、准确和科学的语义连续性评估。")

if __name__ == "__main__":
    demonstrate_relative_comparison()
