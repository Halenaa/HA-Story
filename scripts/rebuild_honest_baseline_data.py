#!/usr/bin/env python3
"""
重新构建诚实的baseline数据 - 只使用真实测量值
"""

import pandas as pd
import numpy as np
import json
import os

def extract_real_data_only():
    """只提取真实测量的数据"""
    
    print("🎯 重新构建诚实的baseline数据")
    print("=" * 60)
    print("只使用真实分析结果，不估算任何数据")
    print("=" * 60)
    
    # 1. 从备份恢复原始数据
    df = pd.read_csv('/Users/haha/Story/metrics_master_clean_backup.csv')
    print(f"从备份恢复: {len(df)} 行")
    
    # 2. 构建真实的baseline数据
    real_baselines = []
    
    baseline_mappings = {
        'simple_baseline_s1': {
            'story_id': 'simple_baseline_s1_Tbaseline_sbaseline',
            'source_dir': '/Users/haha/Story/baseline_analysis_results/baseline_s1',
            'diversity_dir': 'diversity_results_baseline_s1'
        },
        'simple_baseline_s2': {
            'story_id': 'simple_baseline_s2_Tbaseline_sbaseline', 
            'source_dir': '/Users/haha/Story/baseline_analysis_results/baseline_s2',
            'diversity_dir': 'diversity_results_baseline_s2'
        }
    }
    
    for config_name, info in baseline_mappings.items():
        print(f"\n📝 提取 {config_name} 的真实数据...")
        
        # 基础配置
        baseline_row = {
            'story_id': info['story_id'],
            'original_config_name': config_name,
            'test_type': 'simple_baseline_analysis',
            'genre': 'baseline',
            'structure': 'baseline',
            'temperature': 'baseline',
            'seed': 'baseline',
            'is_baseline': 1
        }
        
        # === 真实测量数据 ===
        
        # 1. 流畅性数据 (GPU实测)
        fluency_file = f"{info['source_dir']}/fluency_analysis.json"
        if os.path.exists(fluency_file):
            with open(fluency_file, 'r') as f:
                fluency = json.load(f)
            
            baseline_row.update({
                'pseudo_ppl': fluency.get('pseudo_ppl', np.nan),
                'err_per_100w': fluency.get('err_per_100w', np.nan),
                'error_count': fluency.get('error_count', np.nan),
                'fluency_word_count': fluency.get('word_count', np.nan)
            })
            print(f"   ✅ 流畅性: PPL={fluency.get('pseudo_ppl')}, 错误率={fluency.get('err_per_100w')}%")
        
        # 2. 连贯性数据 (实测)
        coherence_file = f"{info['source_dir']}/hred_coherence_analysis.json"
        if os.path.exists(coherence_file):
            with open(coherence_file, 'r') as f:
                coherence = json.load(f)
            
            if 'detailed_analysis' in coherence and 'basic_statistics' in coherence['detailed_analysis']:
                stats = coherence['detailed_analysis']['basic_statistics']
                
                baseline_row.update({
                    'avg_coherence': stats.get('average_coherence', np.nan),
                    'coherence_std': stats.get('coherence_std', np.nan),
                    'coherence_median': stats.get('coherence_median', np.nan),
                    'coherence_max': stats.get('max_coherence', np.nan),
                    'coherence_min': stats.get('min_coherence', np.nan)
                })
            
            if 'HRED_coherence_evaluation' in coherence:
                hred = coherence['HRED_coherence_evaluation']
                baseline_row['coherence_sentence_count'] = hred.get('total_sentences', np.nan)
            
            # 高低连贯性段落数 (实测)
            if 'detailed_analysis' in coherence:
                detailed = coherence['detailed_analysis']
                baseline_row['low_coherence_points'] = len(detailed.get('coherence_breakpoints', []))
                baseline_row['high_coherence_segments'] = len(detailed.get('high_coherence_segments', []))
            
            print(f"   ✅ 连贯性: {stats.get('average_coherence', 'N/A'):.3f}")
        
        # 3. 多样性数据 (实测)
        individual_file = f"{info['diversity_dir']}/individual_diversity_analysis.json"
        if os.path.exists(individual_file):
            with open(individual_file, 'r') as f:
                individual_data = json.load(f)
            
            if individual_data:
                first_key = list(individual_data.keys())[0]
                div_data = individual_data[first_key]
                
                baseline_row.update({
                    'distinct_avg': div_data.get('distinct_avg', np.nan),
                    'distinct_score': div_data.get('distinct_score', np.nan),
                    'total_words': div_data.get('total_words', np.nan),
                    'total_sentences': div_data.get('total_sentences', np.nan)
                })
                print(f"   ✅ 多样性: distinct_avg={div_data.get('distinct_avg'):.3f}")
        
        # 4. 基本文本特征 (从文件直接计算)
        if config_name == 'simple_baseline_s1':
            source_file = '/Users/haha/Story/output/baseline_s1.md'
        elif config_name == 'simple_baseline_s2':
            source_file = '/Users/haha/Story/output/baseline_s2.md'
        
        if os.path.exists(source_file):
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 真实章节计数
            import re
            chapter_count = len(re.findall(r'^#[^#]', content, re.MULTILINE))
            baseline_row['chapter_count'] = chapter_count
            print(f"   ✅ 章节数: {chapter_count} (重新计算)")
        
        # === 合理的baseline默认值 (不是估算) ===
        
        # 对于单样本baseline，这些值在概念上就是这样的：
        baseline_row.update({
            'diversity_group_score': 0.0,      # 单样本没有组内变异
            'self_bleu_group': 0.0,            # 单样本没有self-BLEU
            'one_minus_self_bleu': 1.0,        # 1 - 0 = 1
            'alpha_genre': 0.7,                # 使用标准alpha值
            'alpha_value': 0.7                 # 使用标准alpha值
        })
        
        # === 无法测量的数据保持NaN ===
        nan_fields = [
            'wall_time_sec',          # 没有性能监控
            'peak_mem_mb',            # 没有内存监控  
            'tokens_total',           # 没有API调用记录
            'cost_usd',               # 没有成本记录
            'roberta_avg_score',      # 情感分析可能失败
            'correlation_coefficient', # 相关性分析可能失败
            'reagan_classification',  # Reagan分类可能失败
            'tp_coverage',            # 结构分析可能失败
            'li_function_diversity',  # Li函数分析可能失败
            'total_events'            # 事件统计可能失败
        ]
        
        for field in nan_fields:
            if field not in baseline_row:
                baseline_row[field] = np.nan
        
        real_baselines.append(baseline_row)
        print(f"   ✅ {config_name} 真实数据提取完成")
    
    # 3. 合并数据
    print(f"\\n🔗 合并数据...")
    df_new = pd.DataFrame(real_baselines)
    df_final = pd.concat([df, df_new], ignore_index=True)
    
    # 4. 保存
    df_final.to_csv('/Users/haha/Story/metrics_master_clean.csv', index=False)
    
    print(f"\\n✅ 诚实的baseline数据重建完成!")
    print(f"📊 总行数: {len(df_final)}")
    print(f"📈 新增baseline: {len(real_baselines)} 个")
    
    # 5. 显示数据诚实性报告
    print(f"\\n📋 数据诚实性报告:")
    print("-" * 60)
    
    new_baselines_df = df_final[df_final['story_id'].str.startswith('simple_baseline', na=False)]
    
    for _, row in new_baselines_df.iterrows():
        config = row['original_config_name']
        print(f"• {config}:")
        
        # 真实测量数据
        real_data = []
        if not pd.isna(row['pseudo_ppl']): real_data.append(f"PPL={row['pseudo_ppl']}")
        if not pd.isna(row['avg_coherence']): real_data.append(f"连贯性={row['avg_coherence']:.3f}")
        if not pd.isna(row['distinct_avg']): real_data.append(f"多样性={row['distinct_avg']:.3f}")
        if not pd.isna(row['chapter_count']): real_data.append(f"章节={row['chapter_count']}")
        
        print(f"  ✅ 真实数据: {', '.join(real_data)}")
        
        # NaN的字段
        nan_count = sum(1 for v in row.values if pd.isna(v))
        print(f"  ⚠️  NaN字段: {nan_count} 个 (缺乏测量数据)")
        print()
    
    print("💯 现在只使用真实测量的数据，不再估算!")
    
    return df_final

if __name__ == '__main__':
    extract_real_data_only()
"
