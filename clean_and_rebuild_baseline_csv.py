#!/usr/bin/env python3
"""
清理和重建CSV文件 - 添加正确命名的simple_baseline数据
"""

import pandas as pd
import numpy as np
import json
import os

def load_baseline_metrics():
    """从分析结果中加载baseline指标"""
    
    # baseline文件和分析结果映射
    baselines_info = {
        'simple_baseline_s1': {
            'story_id': 'simple_baseline_s1_Tbaseline_sbaseline',
            'original_config_name': 'simple_baseline_s1',
            'source': '/Users/haha/Story/baseline_analysis_results/baseline_s1',
            'words': 2622,
            'chapters': 10,
            'sentences': 370
        },
        'simple_baseline_s2': {
            'story_id': 'simple_baseline_s2_Tbaseline_sbaseline', 
            'original_config_name': 'simple_baseline_s2',
            'source': '/Users/haha/Story/baseline_analysis_results/baseline_s2',
            'words': 2043,
            'chapters': 8,
            'sentences': 187
        },
        'simple_baseline_s3': {
            'story_id': 'simple_baseline_s3_Tbaseline_sbaseline',
            'original_config_name': 'simple_baseline_s3',
            'source': '/Users/haha/Story/baseline_analysis_results/baseline_s3',
            'words': 3136,
            'chapters': 24,
            'sentences': 385
        }
    }
    
    new_rows = []
    
    for baseline_name, info in baselines_info.items():
        print(f"📝 加载 {baseline_name} 数据...")
        
        # 基础行
        row = {
            'story_id': info['story_id'],
            'original_config_name': info['original_config_name'],
            'test_type': 'simple_baseline_analysis',
            'genre': 'baseline',
            'structure': 'baseline',
            'temperature': 'baseline',
            'seed': 'baseline',
            'is_baseline': 1,
            'total_words': info['words'],
            'total_sentences': info['sentences'], 
            'chapter_count': info['chapters']
        }
        
        # 加载多样性数据
        diversity_dir = f"diversity_results_baseline_{baseline_name.split('_')[-1]}"
        individual_file = f"{diversity_dir}/individual_diversity_analysis.json"
        group_file = f"{diversity_dir}/group_diversity_analysis.json"
        
        if os.path.exists(individual_file):
            with open(individual_file, 'r') as f:
                individual_data = json.load(f)
                if individual_data:
                    first_key = list(individual_data.keys())[0]
                    div_result = individual_data[first_key]
                    row.update({
                        'distinct_avg': div_result.get('distinct_avg', np.nan),
                        'distinct_score': div_result.get('distinct_score', np.nan)
                    })
        
        if os.path.exists(group_file):
            with open(group_file, 'r') as f:
                group_data = json.load(f)
                if group_data:
                    first_key = list(group_data.keys())[0]
                    group_result = group_data[first_key]
                    row.update({
                        'diversity_group_score': group_result.get('diversity_score', np.nan),
                        'self_bleu_group': group_result.get('self_bleu_group', np.nan),
                        'one_minus_self_bleu': 1 - group_result.get('self_bleu_group', 0) if group_result.get('self_bleu_group') is not None else 1.0,
                        'alpha_value': group_result.get('alpha', 0.7),
                        'alpha_genre': group_result.get('alpha', 0.7)
                    })
        
        # 加载流畅性数据
        fluency_file = f"{info['source']}/fluency_analysis.json"
        if os.path.exists(fluency_file):
            with open(fluency_file, 'r') as f:
                fluency_data = json.load(f)
                row.update({
                    'pseudo_ppl': fluency_data.get('pseudo_ppl', np.nan),
                    'err_per_100w': fluency_data.get('err_per_100w', np.nan),
                    'error_count': fluency_data.get('error_count', 0),
                    'fluency_word_count': fluency_data.get('word_count', 0)
                })
        
        # 加载连贯性数据
        coherence_file = f"{info['source']}/hred_coherence_analysis.json"
        if os.path.exists(coherence_file):
            with open(coherence_file, 'r') as f:
                coherence_data = json.load(f)
                
                if 'detailed_analysis' in coherence_data and 'basic_statistics' in coherence_data['detailed_analysis']:
                    stats = coherence_data['detailed_analysis']['basic_statistics']
                    row.update({
                        'avg_coherence': stats.get('average_coherence', np.nan),
                        'coherence_std': stats.get('coherence_std', np.nan),
                        'coherence_median': stats.get('coherence_median', np.nan),
                        'coherence_max': stats.get('max_coherence', np.nan),
                        'coherence_min': stats.get('min_coherence', np.nan)
                    })
                
                if 'HRED_coherence_evaluation' in coherence_data:
                    hred = coherence_data['HRED_coherence_evaluation']
                    row['coherence_sentence_count'] = hred.get('total_sentences', 0)
                
                # 高低连贯性段落数
                if 'detailed_analysis' in coherence_data:
                    detailed = coherence_data['detailed_analysis']
                    row['low_coherence_points'] = len(detailed.get('coherence_breakpoints', []))
                    row['high_coherence_segments'] = len(detailed.get('high_coherence_segments', []))
        
        # 加载结构数据
        structure_file = f"{info['source']}/story_structure_analysis.json"
        if os.path.exists(structure_file):
            with open(structure_file, 'r') as f:
                structure_data = json.load(f)
                
                # TP覆盖率
                if 'papalampidi' in structure_data and 'turning_points' in structure_data['papalampidi']:
                    tp_count = len(structure_data['papalampidi']['turning_points'])
                    row.update({
                        'tp_coverage': f'{tp_count}/5',
                        'tp_m': tp_count,
                        'tp_n': 5,
                        'tp_completion_rate': tp_count / 5
                    })
                
                # Li函数多样性
                if 'li_function' in structure_data:
                    li_functions = structure_data['li_function']
                    unique_functions = len(set(li_functions.values())) if li_functions else 0
                    row['li_function_diversity'] = unique_functions
                
                # 事件数
                if 'events' in structure_data:
                    row['total_events'] = len(structure_data['events'])
        
        # 设置默认值
        defaults = {
            'correlation_coefficient': np.nan,
            'direction_consistency': False,
            'classification_agreement': False,
            'roberta_avg_score': np.nan,
            'reagan_classification': '',
            'major_disagreements': 0,
            'roberta_std': np.nan,
            'labmt_std': np.nan,
            'emotion_correlation': np.nan,
            'roberta_scores_str': '',
            'labmt_scores_str': '',
            'diversity_score_seed': np.nan,
            'wall_time_sec': np.nan,
            'peak_mem_mb': np.nan,
            'tokens_total': np.nan,
            'cost_usd': np.nan
        }
        
        for key, default_val in defaults.items():
            if key not in row:
                row[key] = default_val
        
        new_rows.append(row)
        print(f"   ✅ {baseline_name}: {len([k for k, v in row.items() if v is not None and v != '' and not pd.isna(v)])} 个有效指标")
    
    return new_rows

def main():
    """主函数"""
    print("🔧 清理和重建CSV - 修正baseline命名混乱")
    print("=" * 60)
    
    # 1. 加载原始数据
    original_file = '/Users/haha/Story/metrics_master_clean.csv'
    df_original = pd.read_csv(original_file)
    print(f"📊 原始数据: {len(df_original)} 行")
    
    # 显示原有baseline
    original_baselines = df_original[df_original['is_baseline'] == 1]
    print(f"🎯 原有baseline: {len(original_baselines)} 个")
    for _, row in original_baselines.iterrows():
        print(f"   • {row['story_id']}")
    
    # 2. 加载新baseline数据
    print(f"\n📝 加载新baseline数据...")
    new_baseline_rows = load_baseline_metrics()
    
    # 3. 合并数据
    df_new = pd.DataFrame(new_baseline_rows)
    df_final = pd.concat([df_original, df_new], ignore_index=True)
    
    # 4. 保存
    df_final.to_csv(original_file, index=False)
    
    print(f"\n🎉 CSV重建完成!")
    print(f"📊 最终数据: {len(df_final)} 行")
    
    # 显示最终baseline概览
    final_baselines = df_final[df_final['is_baseline'] == 1]
    print(f"📈 最终baseline: {len(final_baselines)} 个")
    
    print(f"\n📋 所有baseline数据概览:")
    for _, row in final_baselines.iterrows():
        story_id = row['story_id']
        config_name = row['original_config_name']
        words = row.get('total_words', 'N/A')
        chapters = row.get('chapter_count', 'N/A')
        ppl = row.get('pseudo_ppl', 'N/A')
        coherence = row.get('avg_coherence', 'N/A')
        
        print(f"   • {story_id}")
        print(f"     config: {config_name}")
        print(f"     特征: {words}词, {chapters}章")
        print(f"     指标: PPL={ppl}, 连贯性={coherence}")
        print()

if __name__ == "__main__":
    main()