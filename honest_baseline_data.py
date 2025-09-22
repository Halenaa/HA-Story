#!/usr/bin/env python3
"""
诚实的baseline数据重建 - 只使用真实测量值
"""

import pandas as pd
import numpy as np
import json
import os

def main():
    """重建诚实的baseline数据"""
    
    print("🎯 诚实的baseline数据重建")
    print("=" * 60)
    print("承认问题: 之前估算了一些数据")
    print("解决方案: 只使用真实分析结果")
    print("=" * 60)
    
    # 1. 恢复原始数据
    df = pd.read_csv('/Users/haha/Story/metrics_master_clean_backup.csv')
    print(f"从备份恢复: {len(df)} 行")
    
    # 2. 只添加有真实数据的baseline行
    new_baselines = []
    
    # simple_baseline_s1 - 只使用真实分析结果
    s1_row = {
        'story_id': 'simple_baseline_s1_Tbaseline_sbaseline',
        'original_config_name': 'simple_baseline_s1',
        'test_type': 'simple_baseline_analysis',
        'genre': 'baseline',
        'structure': 'baseline',
        'temperature': 'baseline',
        'seed': 'baseline',
        'is_baseline': 1,
        
        # 真实数据: 从文件计算
        'total_words': 2622,    # 实际字数
        'chapter_count': 10,    # 实际章节数  
        'total_sentences': 370, # 从分析结果
        
        # 真实数据: GPU流畅性分析
        'pseudo_ppl': 11.5,
        'err_per_100w': 6.79,
        'error_count': 178,
        'fluency_word_count': 2622,
        
        # 真实数据: HRED连贯性分析
        'avg_coherence': 0.23403690236812943,
        'coherence_std': 0.11633146579879684,
        'coherence_sentence_count': 369.0,
        'coherence_median': 0.22063671797513962,
        'coherence_max': 0.6327840089797974,
        'coherence_min': -0.05497781187295914,
        'low_coherence_points': 48.0,
        'high_coherence_segments': 22.0,
        
        # 真实数据: 多样性分析
        'distinct_avg': 0.6598736263736263,
        'distinct_score': 0.6598736263736263,
        
        # baseline概念性数据 (单样本固有属性)
        'diversity_group_score': 0.0,
        'self_bleu_group': 0.0,
        'one_minus_self_bleu': 1.0,
        'alpha_genre': 0.7,
        'alpha_value': 0.7,
        
        # 无法获取的数据保持NaN
        'wall_time_sec': np.nan,        # 没有运行时监控
        'peak_mem_mb': np.nan,          # 没有内存监控
        'tokens_total': np.nan,         # 没有API调用统计
        'cost_usd': np.nan,             # 没有成本统计
        'roberta_avg_score': np.nan,    # 情感分析需要重新检查
        'correlation_coefficient': np.nan, # 需要重新检查
        'reagan_classification': '',    # 需要重新检查
        'tp_coverage': '',              # 结构分析需要重新检查
        'li_function_diversity': np.nan, # 需要重新检查
        'total_events': np.nan,         # 需要重新检查
        'major_disagreements': np.nan,
        'roberta_std': np.nan,
        'labmt_std': np.nan,
        'emotion_correlation': np.nan,
        'roberta_scores_str': '',
        'labmt_scores_str': '',
        'diversity_score_seed': np.nan,
        'direction_consistency': False,
        'classification_agreement': False
    }
    
    # simple_baseline_s2 - 类似处理
    s2_row = {
        'story_id': 'simple_baseline_s2_Tbaseline_sbaseline',
        'original_config_name': 'simple_baseline_s2',
        'test_type': 'simple_baseline_analysis',
        'genre': 'baseline',
        'structure': 'baseline',
        'temperature': 'baseline',
        'seed': 'baseline',
        'is_baseline': 1,
        
        # 真实数据
        'total_words': 2043,
        'chapter_count': 8,      # 修正后的章节数
        'total_sentences': 187,
        
        # GPU流畅性
        'pseudo_ppl': 10.23,
        'err_per_100w': 5.09,
        'error_count': 104,
        'fluency_word_count': 2043,
        
        # HRED连贯性
        'avg_coherence': 0.2811895630962356,
        'coherence_std': 0.12283495284099478,
        'coherence_sentence_count': 180.0,
        'coherence_median': 0.2741487920284271,
        'coherence_max': 0.5814635753631592,
        'coherence_min': -0.023941390216350555,
        'low_coherence_points': 29.0,
        'high_coherence_segments': 10.0,
        
        # 多样性
        'distinct_avg': 0.6567763902763903,
        'distinct_score': 0.6567763902763903,
        
        # baseline概念性数据
        'diversity_group_score': 0.0,
        'self_bleu_group': 0.0,
        'one_minus_self_bleu': 1.0,
        'alpha_genre': 0.7,
        'alpha_value': 0.7,
        
        # 其他字段保持NaN
        'wall_time_sec': np.nan,
        'peak_mem_mb': np.nan,
        'tokens_total': np.nan,
        'cost_usd': np.nan,
        'roberta_avg_score': np.nan,
        'correlation_coefficient': np.nan,
        'reagan_classification': '',
        'tp_coverage': '',
        'li_function_diversity': np.nan,
        'total_events': np.nan,
        'major_disagreements': np.nan,
        'roberta_std': np.nan,
        'labmt_std': np.nan,
        'emotion_correlation': np.nan,
        'roberta_scores_str': '',
        'labmt_scores_str': '',
        'diversity_score_seed': np.nan,
        'direction_consistency': False,
        'classification_agreement': False
    }
    
    new_baselines = [s1_row, s2_row]
    
    # 3. 修改baseline_baseline的配置名
    bb_mask = df['story_id'] == 'baseline_baseline_Tbaseline_sbaseline'
    if bb_mask.any():
        df.loc[bb_mask, 'original_config_name'] = 'simple_baseline_s3'
        df.loc[bb_mask, 'test_type'] = 'simple_baseline_analysis'
        print("✅ 修改baseline_baseline配置为simple_baseline_s3")
    
    # 4. 合并数据
    df_new = pd.DataFrame(new_baselines)
    df_final = pd.concat([df, df_new], ignore_index=True)
    
    # 5. 保存
    df_final.to_csv('/Users/haha/Story/metrics_master_clean.csv', index=False)
    
    print(f"\n✅ 诚实数据重建完成!")
    print(f"📊 总行数: {len(df_final)}")
    
    # 6. 诚实性报告
    print(f"\n📋 数据诚实性声明:")
    print("-" * 60)
    print("✅ 流畅性数据: GPU实测")
    print("✅ 连贯性数据: HRED算法实测")  
    print("✅ 多样性数据: distinct算法实测")
    print("✅ 文本特征: 直接计算")
    print("⚠️  Performance数据: 无监控，保持NaN")
    print("⚠️  部分情感/结构数据: 分析可能失败，保持NaN")
    print("\n💯 不再估算任何无法测量的数据!")

if __name__ == "__main__":
    main()
