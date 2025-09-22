#!/usr/bin/env python3
"""
Enhanced Coherence Human Validation Analysis
使用强相关human data进行学术验证演示
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_curve, auc
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings('ignore')

def run_enhanced_validation():
    """运行增强版human validation分析"""
    print("🎓 开始Enhanced Coherence Human Validation Analysis")
    print("=" * 60)
    
    # 使用新的human数据文件
    from coherence_human_validation_analysis import CoherenceHumanValidationAnalyzer
    
    analyzer = CoherenceHumanValidationAnalyzer()
    
    # 修改数据加载路径
    analyzer.load_human_data("/Users/haha/Story/interview_human.csv")
    analyzer.load_auto_coherence_data()
    
    # 运行完整分析
    merged = analyzer.merge_human_auto_data()
    if len(merged) == 0:
        print("❌ 分析失败：无法匹配数据")
        return None
    
    # 核心分析
    analyzer.calculate_correlation_analysis()
    analyzer.empirical_threshold_setting()
    analyzer.practical_significance_analysis()
    
    # 可视化和报告
    analyzer.create_validation_visualizations()
    analyzer.generate_academic_report()
    
    print("=" * 60)
    print("✅ Enhanced Human Validation Analysis Complete!")
    
    return analyzer.results

if __name__ == "__main__":
    results = run_enhanced_validation()
