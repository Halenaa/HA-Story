#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行简化版内容多样性分析
"""

import os
import sys
from pathlib import Path
from simple_diversity_analyzer import SimpleDiversityAnalyzer

def main():
    """主函数"""
    print("=" * 60)
    print("简化版内容多样性分析系统")
    print("=" * 60)
    
    # 设置路径
    data_dir = "/Users/haha/Story/data/output/regression_test"
    output_dir = "/Users/haha/Story/diversity_results"
    
    # 检查数据目录是否存在
    if not Path(data_dir).exists():
        print(f"错误: 数据目录不存在: {data_dir}")
        return
    
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"数据目录: {data_dir}")
    print(f"输出目录: {output_dir}")
    print()
    
    # 初始化分析器
    analyzer = SimpleDiversityAnalyzer(data_dir)
    
    # 运行分析
    try:
        individual_results, group_results = analyzer.run_analysis()
        
        # 保存结果
        analyzer.save_results(output_dir)
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("分析摘要")
        print("=" * 60)
        print(f"逐篇分析: {len(individual_results)} 篇故事")
        print(f"组内分析: {len(group_results)} 个条件组")
        
        if individual_results:
            print("\n逐篇多样性统计:")
            distinct_avg_values = [r['distinct_avg'] for r in individual_results.values()]
            distinct_score_values = [r['distinct_score'] for r in individual_results.values()]
            print(f"  distinct_avg: {min(distinct_avg_values):.4f} - {max(distinct_avg_values):.4f}")
            print(f"  distinct_score: {min(distinct_score_values):.4f} - {max(distinct_score_values):.4f}")
        
        if group_results:
            print("\n组内多样性统计:")
            diversity_scores = [r['diversity_score'] for r in group_results.values()]
            alpha_values = [r['alpha'] for r in group_results.values()]
            print(f"  diversity_score: {min(diversity_scores):.4f} - {max(diversity_scores):.4f}")
            print(f"  alpha权重: {min(alpha_values):.4f} - {max(alpha_values):.4f}")
            
            # 按条件显示结果
            print("\n各条件组结果:")
            for key, result in group_results.items():
                print(f"  {key}: diversity_score={result['diversity_score']:.4f}, alpha={result['alpha']:.4f}")
        
        print(f"\n结果文件已保存到: {output_dir}")
        print("  - individual_diversity_analysis.csv: 逐篇分析结果")
        print("  - group_diversity_analysis.csv: 组内分析结果")
        print("  - individual_diversity_analysis.json: 逐篇分析结果(JSON)")
        print("  - group_diversity_analysis.json: 组内分析结果(JSON)")
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
