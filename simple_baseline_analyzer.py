#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的baseline文件多样性分析
"""

import re
import json
from pathlib import Path
import numpy as np

class SimpleBaselineAnalyzer:
    def __init__(self, window=1000, stride=500):
        self.window = window
        self.stride = stride
    
    def tokenize_text(self, text):
        """简单分词"""
        # 清理文本
        text = re.sub(r'#+\s*.*?\n', '', text)  # 移除标题
        text = re.sub(r'[*_`]', '', text)  # 移除markdown格式
        text = re.sub(r'\n+', ' ', text)  # 合并换行
        
        # 简单分词
        tokens = re.findall(r'\b\w+\b', text.lower())
        return [token for token in tokens if len(token) > 1]
    
    def calculate_distinct_with_window(self, tokens):
        """使用滑动窗口计算distinct分数"""
        if len(tokens) < 10:
            return 0.0, 0.0
        
        if len(tokens) <= self.window:
            # 如果文本短于窗口，直接计算
            uniq_1 = len(set(tokens))
            uniq_2 = len(set(zip(tokens[:-1], tokens[1:]))) if len(tokens) > 1 else 0
            
            d1 = uniq_1 / (len(tokens) + 1)
            d2 = uniq_2 / (max(len(tokens) - 1, 1) + 1)
            return d1, d2
        
        # 滑动窗口计算
        d1_scores = []
        d2_scores = []
        
        # 确保覆盖尾部
        last_start = max(0, len(tokens) - self.window)
        starts = list(range(0, len(tokens) - self.window + 1, self.stride))
        if not starts or starts[-1] != last_start:
            starts.append(last_start)
        
        for i in starts:
            window_tokens = tokens[i:i + self.window]
            
            uniq_1 = len(set(window_tokens))
            uniq_2 = len(set(zip(window_tokens[:-1], window_tokens[1:]))) if len(window_tokens) > 1 else 0
            
            d1 = uniq_1 / (len(window_tokens) + 1)
            d2 = uniq_2 / (max(len(window_tokens) - 1, 1) + 1)
            
            d1_scores.append(d1)
            d2_scores.append(d2)
        
        return np.mean(d1_scores), np.mean(d2_scores)
    
    def analyze_file(self, file_path):
        """分析单个文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分词
        tokens = self.tokenize_text(content)
        
        if len(tokens) < 10:
            return {
                'file_path': str(file_path),
                'total_words': len(tokens),
                'total_sentences': 0,
                'distinct_1': 0.0,
                'distinct_2': 0.0,
                'distinct_avg': 0.0,
                'error': 'Too few tokens'
            }
        
        # 计算distinct分数
        d1, d2 = self.calculate_distinct_with_window(tokens)
        distinct_avg = 0.5 * d1 + 0.5 * d2
        
        # 计算句子数（简单估算）
        sentences = len(re.split(r'[.!?]+', content))
        
        return {
            'file_path': str(file_path),
            'total_words': len(tokens),
            'total_sentences': sentences,
            'distinct_1': float(d1),
            'distinct_2': float(d2),
            'distinct_avg': float(distinct_avg)
        }

def analyze_baselines():
    """分析两个baseline文件"""
    print("=" * 80)
    print("Baseline文件多样性分析")
    print("=" * 80)
    
    analyzer = SimpleBaselineAnalyzer()
    
    # 分析两个文件
    sci_result = analyzer.analyze_file("/Users/haha/Story/data/sci_baseline.md")
    normal_result = analyzer.analyze_file("/Users/haha/Story/data/normal_baseline.md")
    
    print("\n📊 基本统计")
    print("-" * 40)
    print(f"科幻baseline: {sci_result['total_words']} 词, {sci_result['total_sentences']} 句")
    print(f"传统baseline: {normal_result['total_words']} 词, {normal_result['total_sentences']} 句")
    
    print("\n🎯 多样性指标对比")
    print("-" * 40)
    print(f"科幻baseline:")
    print(f"  distinct_1: {sci_result['distinct_1']:.4f}")
    print(f"  distinct_2: {sci_result['distinct_2']:.4f}")
    print(f"  distinct_avg: {sci_result['distinct_avg']:.4f}")
    
    print(f"传统baseline:")
    print(f"  distinct_1: {normal_result['distinct_1']:.4f}")
    print(f"  distinct_2: {normal_result['distinct_2']:.4f}")
    print(f"  distinct_avg: {normal_result['distinct_avg']:.4f}")
    
    print("\n📈 相对比较")
    print("-" * 40)
    
    # 计算相对差异
    if normal_result['distinct_1'] > 0:
        distinct_1_diff = (sci_result['distinct_1'] - normal_result['distinct_1']) / normal_result['distinct_1'] * 100
        distinct_2_diff = (sci_result['distinct_2'] - normal_result['distinct_2']) / normal_result['distinct_2'] * 100
        distinct_avg_diff = (sci_result['distinct_avg'] - normal_result['distinct_avg']) / normal_result['distinct_avg'] * 100
        
        print(f"科幻相对传统baseline:")
        print(f"  distinct_1: {distinct_1_diff:+.1f}%")
        print(f"  distinct_2: {distinct_2_diff:+.1f}%")
        print(f"  distinct_avg: {distinct_avg_diff:+.1f}%")
    
    # 词汇密度比较
    if sci_result['total_sentences'] > 0 and normal_result['total_sentences'] > 0:
        sci_density = sci_result['total_words'] / sci_result['total_sentences']
        normal_density = normal_result['total_words'] / normal_result['total_sentences']
        density_diff = (sci_density - normal_density) / normal_density * 100
        
        print(f"\n词汇密度:")
        print(f"  科幻: {sci_density:.1f} 词/句")
        print(f"  传统: {normal_density:.1f} 词/句")
        print(f"  差异: {density_diff:+.1f}%")
    
    print("\n💡 关键发现")
    print("-" * 40)
    
    if sci_result['distinct_avg'] > normal_result['distinct_avg']:
        print(f"• 科幻baseline词汇多样性更高 ({sci_result['distinct_avg']:.4f} vs {normal_result['distinct_avg']:.4f})")
    else:
        print(f"• 传统baseline词汇多样性更高 ({normal_result['distinct_avg']:.4f} vs {sci_result['distinct_avg']:.4f})")
    
    if sci_result['total_words'] > normal_result['total_words']:
        print(f"• 科幻baseline更长 ({sci_result['total_words']} vs {normal_result['total_words']} 词)")
    else:
        print(f"• 传统baseline更长 ({normal_result['total_words']} vs {sci_result['total_words']} 词)")
    
    # 风格分析
    print(f"\n🎨 风格特征分析")
    print("-" * 40)
    
    # 读取文件内容进行简单的风格分析
    with open("/Users/haha/Story/data/sci_baseline.md", 'r', encoding='utf-8') as f:
        sci_content = f.read().lower()
    
    with open("/Users/haha/Story/data/normal_baseline.md", 'r', encoding='utf-8') as f:
        normal_content = f.read().lower()
    
    # 科幻词汇
    sci_words = ['station', 'algorithm', 'data', 'network', 'drone', 'bio-signal', 'radiation', 'quantum', 'cyber', 'tech']
    sci_count = sum(sci_content.count(word) for word in sci_words)
    
    # 传统词汇
    traditional_words = ['forest', 'cottage', 'grandmother', 'wolf', 'path', 'village', 'woods', 'tree', 'flower', 'bird']
    trad_count_in_normal = sum(normal_content.count(word) for word in traditional_words)
    trad_count_in_sci = sum(sci_content.count(word) for word in traditional_words)
    
    print(f"科幻特征词在科幻baseline中: {sci_count} 次")
    print(f"传统特征词在传统baseline中: {trad_count_in_normal} 次")
    print(f"传统特征词在科幻baseline中: {trad_count_in_sci} 次")
    
    # 保存结果
    results = {
        'sci_baseline': sci_result,
        'normal_baseline': normal_result,
        'comparison': {
            'sci_higher_diversity': sci_result['distinct_avg'] > normal_result['distinct_avg'],
            'sci_longer': sci_result['total_words'] > normal_result['total_words'],
            'sci_feature_words': sci_count,
            'traditional_words_in_normal': trad_count_in_normal,
            'traditional_words_in_sci': trad_count_in_sci
        }
    }
    
    with open('baseline_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 结果已保存到: baseline_analysis_results.json")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    analyze_baselines()
