#!/usr/bin/env python3
"""
更新metrics_master_clean.csv，整合所有baseline分析结果
"""

import pandas as pd
import numpy as np
import json
import os
import re
from pathlib import Path

class BaselineMetricsUpdater:
    def __init__(self):
        """初始化数据更新器"""
        self.baseline_analysis_dir = '/Users/haha/Story/baseline_analysis_results'
        self.metrics_csv_path = '/Users/haha/Story/metrics_master_clean.csv'
        self.backup_csv_path = '/Users/haha/Story/metrics_master_clean_backup.csv'
        
        # baseline映射 - 修正命名避免与原有baseline混淆
        self.baseline_mapping = {
            'baseline_s1': {
                'story_id': 'simple_baseline_s1_Tbaseline_sbaseline',
                'original_config_name': 'simple_baseline_s1',
                'test_type': 'simple_baseline_analysis',
                'genre': 'baseline',
                'structure': 'baseline', 
                'temperature': 'baseline',
                'seed': 'baseline',
                'is_baseline': 1
            },
            'baseline_s2': {
                'story_id': 'simple_baseline_s2_Tbaseline_sbaseline', 
                'original_config_name': 'simple_baseline_s2',
                'test_type': 'simple_baseline_analysis',
                'genre': 'baseline',
                'structure': 'baseline',
                'temperature': 'baseline',
                'seed': 'baseline',
                'is_baseline': 1
            },
            'baseline_s3': {
                'story_id': 'simple_baseline_s3_Tbaseline_sbaseline',
                'original_config_name': 'simple_baseline_s3', 
                'test_type': 'simple_baseline_analysis',
                'genre': 'baseline',
                'structure': 'baseline',
                'temperature': 'baseline',
                'seed': 'baseline',
                'is_baseline': 1
            }
        }
    
    def backup_original_csv(self):
        """备份原始CSV文件"""
        if os.path.exists(self.metrics_csv_path):
            import shutil
            shutil.copy2(self.metrics_csv_path, self.backup_csv_path)
            print(f"✅ 已备份原始CSV到: {self.backup_csv_path}")
    
    def load_baseline_analysis_results(self, baseline_name):
        """加载单个baseline的分析结果"""
        baseline_dir = f"{self.baseline_analysis_dir}/{baseline_name}"
        
        if not os.path.exists(baseline_dir):
            print(f"❌ 未找到baseline分析结果: {baseline_dir}")
            return None
        
        results = {}
        
        # 1. 加载综合分析结果
        comprehensive_file = f"{baseline_dir}/comprehensive_analysis.json"
        if os.path.exists(comprehensive_file):
            with open(comprehensive_file, 'r', encoding='utf-8') as f:
                results['comprehensive'] = json.load(f)
        
        # 2. 加载多样性结果
        diversity_dir = f"diversity_results_baseline_{baseline_name}"
        if os.path.exists(diversity_dir):
            # 查找结果文件
            individual_file = f"{diversity_dir}/individual_results.json"
            group_file = f"{diversity_dir}/group_results.json"
            
            if os.path.exists(individual_file):
                with open(individual_file, 'r', encoding='utf-8') as f:
                    results['diversity_individual'] = json.load(f)
            
            if os.path.exists(group_file):
                with open(group_file, 'r', encoding='utf-8') as f:
                    results['diversity_group'] = json.load(f)
        
        return results
    
    def extract_metrics_from_analysis(self, baseline_name, analysis_results):
        """从分析结果中提取指标"""
        config = self.baseline_mapping[baseline_name]
        metrics = config.copy()  # 基础配置
        
        if not analysis_results:
            return metrics
        
        try:
            # 1. 基础文本特征
            if 'comprehensive' in analysis_results and 'text_features' in analysis_results['comprehensive']:
                text_features = analysis_results['comprehensive']['text_features']
                metrics.update({
                    'total_words': text_features.get('total_words', 0),
                    'total_sentences': text_features.get('total_sentences', 0),
                    'chapter_count': text_features.get('chapter_count', 0)
                })
            
            # 2. 多样性指标
            if 'comprehensive' in analysis_results and 'diversity' in analysis_results['comprehensive']:
                diversity_data = analysis_results['comprehensive']['diversity']
                
                # 个体多样性数据
                if 'individual' in diversity_data and diversity_data['individual']:
                    first_key = list(diversity_data['individual'].keys())[0]
                    div_result = diversity_data['individual'][first_key]
                    
                    metrics.update({
                        'distinct_avg': div_result.get('distinct_avg', np.nan),
                        'distinct_score': div_result.get('distinct_score', np.nan)
                    })
                
                # 组多样性数据
                if 'group' in diversity_data and diversity_data['group']:
                    first_key = list(diversity_data['group'].keys())[0]
                    group_result = diversity_data['group'][first_key]
                    
                    metrics.update({
                        'diversity_group_score': group_result.get('diversity_score', np.nan),
                        'self_bleu_group': group_result.get('self_bleu_group', np.nan),
                        'one_minus_self_bleu': 1 - group_result.get('self_bleu_group', 0) if group_result.get('self_bleu_group') is not None else np.nan,
                        'alpha_value': group_result.get('alpha', np.nan),
                        'alpha_genre': group_result.get('alpha', np.nan)  # 通常相同
                    })
            
            # 3. 流畅性指标
            if 'comprehensive' in analysis_results and 'fluency' in analysis_results['comprehensive']:
                fluency = analysis_results['comprehensive']['fluency']
                metrics.update({
                    'pseudo_ppl': fluency.get('pseudo_ppl', np.nan),
                    'err_per_100w': fluency.get('err_per_100w', np.nan),
                    'error_count': fluency.get('error_count', 0),
                    'fluency_word_count': fluency.get('word_count', 0)
                })
            
            # 4. 连贯性指标
            if 'comprehensive' in analysis_results and 'coherence' in analysis_results['comprehensive']:
                coherence = analysis_results['comprehensive']['coherence']
                
                # 尝试从detailed_analysis中提取
                if 'detailed_analysis' in coherence and 'basic_statistics' in coherence['detailed_analysis']:
                    stats = coherence['detailed_analysis']['basic_statistics']
                    
                    metrics.update({
                        'avg_coherence': stats.get('average_coherence', np.nan),
                        'coherence_std': stats.get('coherence_std', np.nan),
                        'coherence_median': stats.get('coherence_median', np.nan),
                        'coherence_max': stats.get('max_coherence', np.nan),
                        'coherence_min': stats.get('min_coherence', np.nan)
                    })
                
                # 从HRED_coherence_evaluation中提取句子数
                if 'HRED_coherence_evaluation' in coherence:
                    hred = coherence['HRED_coherence_evaluation']
                    metrics.update({
                        'coherence_sentence_count': hred.get('total_sentences', 0)
                    })
                
                # 计算高低连贯性段落数
                if 'detailed_analysis' in coherence:
                    detailed = coherence['detailed_analysis']
                    
                    # 低连贯性断点数
                    low_coherence_count = len(detailed.get('coherence_breakpoints', []))
                    metrics['low_coherence_points'] = low_coherence_count
                    
                    # 高连贯性段落数
                    high_coherence_count = len(detailed.get('high_coherence_segments', []))
                    metrics['high_coherence_segments'] = high_coherence_count
            
            # 5. 情感分析指标
            if 'comprehensive' in analysis_results and 'emotion' in analysis_results['comprehensive']:
                emotion = analysis_results['comprehensive']['emotion']
                
                # RoBERTa指标 (从primary_analysis)
                if 'primary_analysis' in emotion:
                    roberta = emotion['primary_analysis']
                    
                    # 计算平均分数
                    if 'scores' in roberta and roberta['scores']:
                        roberta_scores = roberta['scores']
                        roberta_avg = sum(roberta_scores) / len(roberta_scores)
                        roberta_std = np.std(roberta_scores)
                        
                        metrics.update({
                            'roberta_avg_score': roberta_avg,
                            'roberta_std': roberta_std
                        })
                        
                        # 章节分数字符串
                        scores_str = ','.join([str(round(s, 4)) for s in roberta_scores])
                        metrics['roberta_scores_str'] = scores_str
                    
                    # Reagan分类
                    if 'reagan_classification' in roberta:
                        reagan = roberta['reagan_classification']
                        metrics['reagan_classification'] = reagan.get('best_match', '')
                
                # LabMT指标 (从validation_analysis)
                if 'validation_analysis' in emotion:
                    labmt = emotion['validation_analysis']
                    
                    if 'scores' in labmt and labmt['scores']:
                        labmt_scores = labmt['scores']
                        labmt_std = np.std(labmt_scores)
                        metrics['labmt_std'] = labmt_std
                        
                        # 章节分数字符串
                        scores_str = ','.join([str(round(s, 4)) for s in labmt_scores])
                        metrics['labmt_scores_str'] = scores_str
                
                # 相关性和一致性指标
                if 'correlation_analysis' in emotion:
                    corr = emotion['correlation_analysis']
                    
                    # Pearson相关性
                    if 'pearson_correlation' in corr:
                        pearson = corr['pearson_correlation']
                        if isinstance(pearson, dict) and 'r' in pearson:
                            metrics['correlation_coefficient'] = pearson['r']
                        else:
                            metrics['correlation_coefficient'] = pearson
                    
                    # 方向一致性
                    metrics['direction_consistency'] = corr.get('direction_consistency', False)
                    
                    # 分类一致性（通过比较primary和validation的分类）
                    primary_class = ''
                    validation_class = ''
                    if 'primary_analysis' in emotion and 'reagan_classification' in emotion['primary_analysis']:
                        primary_class = emotion['primary_analysis']['reagan_classification'].get('best_match', '')
                    if 'validation_analysis' in emotion and 'reagan_classification' in emotion['validation_analysis']:
                        validation_class = emotion['validation_analysis']['reagan_classification'].get('best_match', '')
                    
                    metrics['classification_agreement'] = (primary_class == validation_class) if primary_class and validation_class else False
                
                # 主要分歧数（暂时设为0，可能需要进一步计算）
                metrics['major_disagreements'] = 0
            
            # 6. 结构分析指标
            if 'comprehensive' in analysis_results and 'structure' in analysis_results['comprehensive']:
                structure = analysis_results['comprehensive']['structure']
                
                # TP覆盖率 (从Papalampidi_detailed_results)
                if 'Papalampidi_detailed_results' in structure:
                    papa = structure['Papalampidi_detailed_results']
                    if 'turning_points' in papa:
                        tp_count = len(papa['turning_points'])
                        metrics.update({
                            'tp_coverage': f'{tp_count}/5',
                            'tp_m': tp_count,
                            'tp_n': 5,
                            'tp_completion_rate': tp_count / 5
                        })
                
                # Li函数多样性 (从Li_detailed_results)
                if 'Li_detailed_results' in structure:
                    li_data = structure['Li_detailed_results']
                    if li_data:
                        unique_functions = len(set(li_data.values()))
                        metrics['li_function_diversity'] = unique_functions
                
                # 事件统计 (从event_list)
                if 'event_list' in structure:
                    metrics['total_events'] = len(structure['event_list'])
            
            # 7. 设置默认值（如果没有实际数据）
            default_values = {
                'diversity_score_seed': np.nan,
                'wall_time_sec': np.nan,
                'peak_mem_mb': np.nan,
                'tokens_total': np.nan,
                'cost_usd': np.nan,
                'emotion_correlation': np.nan
            }
            
            for key, default_val in default_values.items():
                if key not in metrics:
                    metrics[key] = default_val
            
            return metrics
            
        except Exception as e:
            print(f"❌ 提取{baseline_name}指标时出错: {e}")
            import traceback
            traceback.print_exc()
            return config  # 返回基础配置
    
    def update_metrics_csv(self):
        """更新metrics CSV文件"""
        print("🔄 开始更新metrics_master_clean.csv...")
        
        # 1. 备份原文件
        self.backup_original_csv()
        
        # 2. 加载现有数据
        if os.path.exists(self.metrics_csv_path):
            df_existing = pd.read_csv(self.metrics_csv_path)
            print(f"📊 加载现有数据: {len(df_existing)} 行")
            
            # 保留原有数据，只检查是否有重复的story_id
            baseline_story_ids = [config['story_id'] for config in self.baseline_mapping.values()]
            existing_baseline_count = len(df_existing[df_existing['story_id'].isin(baseline_story_ids)])
            if existing_baseline_count > 0:
                print(f"⚠️  发现 {existing_baseline_count} 个已存在的baseline记录，将追加新数据")
            else:
                print("✅ 没有发现重复的baseline记录")
        else:
            df_existing = pd.DataFrame()
            print("📊 创建新的DataFrame")
        
        # 3. 处理每个baseline
        new_rows = []
        
        for baseline_name in self.baseline_mapping.keys():
            print(f"\n📝 处理 {baseline_name}...")
            
            # 加载分析结果
            analysis_results = self.load_baseline_analysis_results(baseline_name)
            
            # 提取指标
            metrics = self.extract_metrics_from_analysis(baseline_name, analysis_results)
            new_rows.append(metrics)
            
            print(f"   ✅ 指标提取完成: {len([k for k, v in metrics.items() if v is not None and v != ''])} 个有效指标")
        
        # 4. 创建新的DataFrame
        df_new = pd.DataFrame(new_rows)
        
        # 5. 合并数据
        if len(df_existing) > 0:
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_final = df_new
        
        # 6. 重新排序列（保持与原CSV相同的列顺序）
        if os.path.exists(self.metrics_csv_path):
            original_df = pd.read_csv(self.metrics_csv_path)
            original_columns = original_df.columns.tolist()
            
            # 确保所有新列都包含在内
            all_columns = original_columns + [col for col in df_final.columns if col not in original_columns]
            df_final = df_final.reindex(columns=all_columns)
        
        # 7. 保存更新后的CSV
        df_final.to_csv(self.metrics_csv_path, index=False)
        
        print(f"\n🎉 metrics_master_clean.csv 更新完成!")
        print(f"📊 最终数据: {len(df_final)} 行 x {len(df_final.columns)} 列")
        print(f"📈 新增baseline: {len(new_rows)} 个")
        print(f"💾 文件保存到: {self.metrics_csv_path}")
        print(f"🗂️  备份文件: {self.backup_csv_path}")
        
        return df_final

def main():
    """主函数"""
    updater = BaselineMetricsUpdater()
    df = updater.update_metrics_csv()
    
    # 显示新增的baseline数据概览
    print("\n📋 新增baseline数据概览:")
    print("-" * 60)
    baseline_story_ids = [config['story_id'] for config in updater.baseline_mapping.values()]
    baseline_data = df[df['story_id'].isin(baseline_story_ids)]
    
    for _, row in baseline_data.iterrows():
        print(f"• {row['story_id']}")
        print(f"  - 总词数: {row.get('total_words', 'N/A')}")
        print(f"  - 章节数: {row.get('chapter_count', 'N/A')}")
        print(f"  - 流畅性PPL: {row.get('pseudo_ppl', 'N/A')}")
        print(f"  - 平均连贯性: {row.get('avg_coherence', 'N/A')}")
        print()
    
    return df

if __name__ == "__main__":
    main()
