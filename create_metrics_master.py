#!/usr/bin/env python3
"""
创建统一的metrics_master.csv主表
合并所有分析文件的数据到一张主表中
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
import os
import glob

def create_story_id(config_name, genre=None, structure=None, temperature=None, seed=None):
    """
    从config_name或其他字段构造统一的story_id
    格式: {genre}_{structure}_T{temperature}_s{seed}
    """
    # 如果直接传入了参数，使用参数构造
    if all([genre, structure, temperature, seed]):
        temp_str = str(temperature) if temperature != 'baseline' else 'baseline'
        seed_str = str(seed) if seed != 'baseline' else 'baseline'
        return f"{genre}_{structure}_T{temp_str}_s{seed_str}"
    
    # 从config_name解析
    if 'baseline' in config_name.lower():
        if 'sci_baseline' in config_name:
            return "sciencefiction_baseline_Tbaseline_sbaseline"
        elif 'normal_baseline' in config_name:
            return "baseline_baseline_Tbaseline_sbaseline"
        else:
            return f"{config_name}_baseline_Tbaseline_sbaseline"
    
    # 解析AI生成的配置名
    # 格式: thelittleredridinghood_{genre}_structure_T{temp}_s{seed}
    try:
        # 提取类型
        if 'sciencefictionrewrite' in config_name:
            genre = 'sciencefiction'
        elif 'horror-suspenserewrite' in config_name:
            genre = 'horror'  
        elif 'romanticrewrite' in config_name:
            genre = 'romantic'
        else:
            genre = 'unknown'
        
        # 提取结构
        if '_linear_' in config_name:
            structure = 'linear'
        elif '_nonlinear_' in config_name:
            structure = 'nonlinear'
        else:
            structure = 'unknown'
        
        # 提取温度
        temp_match = re.search(r'_T(0\.[379])_', config_name)
        temperature = temp_match.group(1) if temp_match else 'unknown'
        
        # 提取种子
        seed_match = re.search(r'_s([123])$', config_name)
        seed = seed_match.group(1) if seed_match else 'unknown'
        
        return f"{genre}_{structure}_T{temperature}_s{seed}"
        
    except Exception as e:
        print(f"Warning: 无法解析config_name: {config_name}, error: {e}")
        return config_name

def load_core_metrics():
    """加载核心指标数据作为主表"""
    df = pd.read_csv('/Users/haha/Story/data/core_metrics_analysis.csv')
    
    # 构造story_id - 特殊处理baseline
    def create_baseline_story_id(row):
        config_name = row['config_name']
        if config_name == 'sci_baseline':
            return 'sciencefiction_baseline_Tbaseline_sbaseline'
        elif config_name == 'normal_baseline':
            return 'baseline_baseline_Tbaseline_sbaseline'
        else:
            # 普通实验数据
            return create_story_id(
                config_name, row['genre'], row['structure'], 
                row['temperature'], row['seed']
            )
    
    df['story_id'] = df.apply(create_baseline_story_id, axis=1)
    
    # 添加is_baseline标志
    df['is_baseline'] = (df['genre'] == 'baseline').astype(int)
    
    # 重命名列以符合标准
    column_mapping = {
        'config_name': 'original_config_name',
        'roberta_avg_score': 'roberta_avg_score',
        'reagan_classification': 'reagan_classification', 
        'correlation_coefficient': 'correlation_coefficient',
        'hred_avg_coherence': 'avg_semantic_continuity',
        'total_sentences': 'semantic_continuity_sentence_count',
        'tp_coverage': 'tp_coverage',
        'li_function_diversity': 'li_function_diversity',
        'total_events': 'total_events',
        'total_words': 'total_words',
        'sentence_count': 'total_sentences'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 选择需要的列
    core_cols = [
        'story_id', 'original_config_name', 'test_type', 'genre', 'structure', 
        'temperature', 'seed', 'is_baseline',
        # 情感轨迹相关
        'roberta_avg_score', 'reagan_classification', 'correlation_coefficient', 'chapter_count',
        # 语义连续性相关
        'avg_semantic_continuity', 'semantic_continuity_sentence_count',
        # 结构相关
        'tp_coverage', 'li_function_diversity', 'total_events', 'total_words', 'total_sentences'
    ]
    
    return df[core_cols]

def load_diversity_individual():
    """加载逐篇多样性数据（合并所有类型）"""
    all_diversity_data = []
    
    # 加载三个类型的多样性数据
    diversity_dirs = [
        '/Users/haha/Story/diversity_results',
        '/Users/haha/Story/diversity_results_horror', 
        '/Users/haha/Story/diversity_results_romantic'
    ]
    
    for div_dir in diversity_dirs:
        try:
            df = pd.read_csv(f'{div_dir}/individual_diversity_analysis.csv')
            
            # 构造story_id匹配主表
            df['story_id'] = df.apply(lambda row: create_story_id(
                row['folder_name'], row['genre'], row['structure'], 
                row['temperature'], row['seed']
            ), axis=1)
            
            all_diversity_data.append(df)
            print(f"   加载 {div_dir}: {len(df)} 个故事")
            
        except FileNotFoundError:
            print(f"Warning: {div_dir}/individual_diversity_analysis.csv not found")
            continue
    
    # 加载baseline多样性数据
    try:
        with open('/Users/haha/Story/baseline_analysis_results.json', 'r') as f:
            baseline_data = json.load(f)
        
        # sci_baseline多样性
        sci_baseline_div = {
            'story_id': 'sciencefiction_baseline_Tbaseline_sbaseline',
            'distinct_avg': baseline_data['sci_baseline']['distinct_avg'],
            'distinct_1': baseline_data['sci_baseline']['distinct_1'],
            'distinct_2': baseline_data['sci_baseline']['distinct_2'],
            'distinct_score': np.nan  # 需要归一化，暂时设为nan
        }
        
        # normal_baseline多样性  
        normal_baseline_div = {
            'story_id': 'baseline_baseline_Tbaseline_sbaseline',
            'distinct_avg': baseline_data['normal_baseline']['distinct_avg'],
            'distinct_1': baseline_data['normal_baseline']['distinct_1'],
            'distinct_2': baseline_data['normal_baseline']['distinct_2'],
            'distinct_score': np.nan  # 需要归一化，暂时设为nan
        }
        
        baseline_df = pd.DataFrame([sci_baseline_div, normal_baseline_div])
        all_diversity_data.append(baseline_df)
        print(f"   加载baseline多样性数据: 2 个故事")
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: baseline多样性数据加载失败: {e}")
    
    if not all_diversity_data:
        print("Warning: 没有找到任何多样性数据")
        return None
    
    # 合并所有数据
    combined_df = pd.concat(all_diversity_data, ignore_index=True)
    
    # 重命名列
    diversity_cols = {
        'distinct_avg': 'distinct_avg',
        'distinct_score': 'distinct_score'  # 这个是归一化后的分数
    }
    combined_df = combined_df.rename(columns=diversity_cols)
    
    return combined_df[['story_id', 'distinct_avg', 'distinct_score']]

def load_diversity_group():
    """加载组级多样性数据（合并所有类型）"""
    all_group_data = []
    
    # 加载三个类型的组级多样性数据
    diversity_dirs = [
        '/Users/haha/Story/diversity_results',
        '/Users/haha/Story/diversity_results_horror', 
        '/Users/haha/Story/diversity_results_romantic'
    ]
    
    for div_dir in diversity_dirs:
        try:
            df = pd.read_csv(f'{div_dir}/group_diversity_analysis.csv')
            
            # 构造匹配键 (genre_structure_temperature)
            df['group_key'] = df['genre'] + '_' + df['structure'] + '_T' + df['temperature'].astype(str)
            
            all_group_data.append(df)
            print(f"   加载 {div_dir}: {len(df)} 个组")
            
        except FileNotFoundError:
            print(f"Warning: {div_dir}/group_diversity_analysis.csv not found")
            continue
    
    if not all_group_data:
        print("Warning: 没有找到任何组级多样性数据")
        return None
    
    # 合并所有数据
    combined_df = pd.concat(all_group_data, ignore_index=True)
    
    # 选择需要的列
    group_cols = {
        'diversity_score': 'diversity_group_score',
        'alpha': 'alpha_value',
        'self_bleu_group': 'self_bleu_group',
        'one_minus_self_bleu': 'one_minus_self_bleu'
    }
    combined_df = combined_df.rename(columns=group_cols)
    
    return combined_df[['group_key', 'diversity_group_score', 'alpha_value', 'self_bleu_group', 'one_minus_self_bleu']]

def load_fluency_data():
    """加载流畅性数据（从多个来源合并）"""
    all_fluency_data = []
    
    # 1. 加载各个测试类型的流畅性报告
    fluency_reports = [
        '/Users/haha/Story/fluency_analysis_results/regression_test_results/fluency_analysis_report.csv',
        '/Users/haha/Story/fluency_analysis_results/horror_test_results/fluency_analysis_report.csv', 
        '/Users/haha/Story/fluency_analysis_results/romantic_test_results/fluency_analysis_report.csv'
    ]
    
    for report_file in fluency_reports:
        try:
            df = pd.read_csv(report_file)
            # 从subdir_name构造story_id
            df['story_id'] = df['subdir_name'].apply(create_story_id)
            all_fluency_data.append(df)
            print(f"   加载流畅性报告: {len(df)} 个故事")
        except FileNotFoundError:
            print(f"Warning: {report_file} not found")
            continue
    
    # 2. 加载baseline流畅性数据
    try:
        # sci_baseline
        with open('/Users/haha/Story/fluency_analysis_results/sci_baseline_results/sci_baseline_fluency_analysis.json', 'r') as f:
            sci_baseline_data = json.load(f)
        
        sci_baseline_row = {
            'story_id': 'sciencefiction_baseline_Tbaseline_sbaseline',
            'subdir_name': 'sci_baseline',
            'pseudo_ppl': sci_baseline_data.get('pseudo_ppl', np.nan),
            'err_per_100w': sci_baseline_data.get('err_per_100w', np.nan),
            'error_count': sci_baseline_data.get('error_count', 0),
            'word_count': sci_baseline_data.get('word_count', 0)
        }
        
        baseline_df = pd.DataFrame([sci_baseline_row])
        all_fluency_data.append(baseline_df)
        print(f"   加载sci_baseline流畅性数据")
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: sci_baseline fluency data not found: {e}")
    
    try:
        # normal_baseline 
        with open('/Users/haha/Story/fluency_analysis_results/normal_baseline_results/normal_baseline_fluency_analysis.json', 'r') as f:
            normal_baseline_data = json.load(f)
        
        normal_baseline_row = {
            'story_id': 'baseline_baseline_Tbaseline_sbaseline',
            'subdir_name': 'normal_baseline',
            'pseudo_ppl': normal_baseline_data.get('pseudo_ppl', np.nan),
            'err_per_100w': normal_baseline_data.get('err_per_100w', np.nan),
            'error_count': normal_baseline_data.get('error_count', 0),
            'word_count': normal_baseline_data.get('word_count', 0)
        }
        
        normal_baseline_df = pd.DataFrame([normal_baseline_row])
        all_fluency_data.append(normal_baseline_df)
        print(f"   加载normal_baseline流畅性数据")
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: normal_baseline fluency data not found: {e}")
    
    if not all_fluency_data:
        print("Warning: 没有找到任何流畅性数据")
        return None
        
    # 合并所有流畅性数据
    combined_df = pd.concat(all_fluency_data, ignore_index=True)
    
    # 重命名流畅性相关列
    fluency_cols = {
        'pseudo_ppl': 'pseudo_ppl',
        'error_count': 'error_count',
        'word_count': 'fluency_word_count'
    }
    combined_df = combined_df.rename(columns=fluency_cols)
    
    # 确保错误率列存在
    if 'err_per_100w' not in combined_df.columns:
        combined_df['err_per_100w'] = (combined_df.get('error_count', 0) / combined_df.get('fluency_word_count', 1)) * 100000
    
    return combined_df[['story_id', 'pseudo_ppl', 'err_per_100w', 'error_count', 'fluency_word_count']]

def load_semantic_continuity_supplement():
    """加载语义连续性补充数据（std, low_continuity_points, high_continuity_segments）"""
    semantic_continuity_supplement = []
    
    # 遍历所有analysis_test目录中的连贯性分析文件
    test_dirs = [
        '/Users/haha/Story/data/analysis_test/regression_test_analysis',
        '/Users/haha/Story/data/analysis_test/horror_test_analysis', 
        '/Users/haha/Story/data/analysis_test/romantic_test_analysis'
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            # 查找每个故事目录中的hred_coherence_analysis文件
            for story_dir in os.listdir(test_dir):
                story_path = os.path.join(test_dir, story_dir)
                if os.path.isdir(story_path):
                    # 查找连贯性分析文件
                    coherence_file = os.path.join(story_path, 'hred_coherence_analysis.json')
                    if os.path.exists(coherence_file):
                        try:
                            with open(coherence_file, 'r') as f:
                                coherence_data = json.load(f)
                            
                            story_id = create_story_id(story_dir)
                            
                            # 提取详细分析数据
                            detailed = coherence_data.get('detailed_analysis', {})
                            basic_stats = detailed.get('basic_statistics', {})
                            
                            # 计算断点和高连贯性段落数量
                            breakpoints = detailed.get('coherence_breakpoints', [])
                            high_segments = detailed.get('high_coherence_segments', [])
                            
                            semantic_continuity_supplement.append({
                                'story_id': story_id,
                                'semantic_continuity_std': basic_stats.get('coherence_std', np.nan),
                                'low_continuity_points': len(breakpoints),
                                'high_continuity_segments': len(high_segments),
                                'semantic_continuity_median': basic_stats.get('coherence_median', np.nan),
                                'semantic_continuity_max': basic_stats.get('max_coherence', np.nan),
                                'semantic_continuity_min': basic_stats.get('min_coherence', np.nan)
                            })
                            
                        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                            print(f"Warning: 无法加载 {coherence_file}: {e}")
                            continue
    
    # 处理baseline的连贯性数据
    baseline_dirs = [
        '/Users/haha/Story/data/analysis_test/sci_baseline_analysis',
        '/Users/haha/Story/data/analysis_test/normal_baseline_analysis'
    ]
    
    for baseline_dir in baseline_dirs:
        if os.path.exists(baseline_dir):
            coherence_file = os.path.join(baseline_dir, 'hred_coherence_analysis.json')
            if os.path.exists(coherence_file):
                try:
                    with open(coherence_file, 'r') as f:
                        coherence_data = json.load(f)
                    
                    # 确定baseline的story_id
                    if 'sci_baseline' in baseline_dir:
                        story_id = 'sciencefiction_baseline_Tbaseline_sbaseline'
                    else:
                        story_id = 'baseline_baseline_Tbaseline_sbaseline'
                    
                    detailed = coherence_data.get('detailed_analysis', {})
                    basic_stats = detailed.get('basic_statistics', {})
                    
                    breakpoints = detailed.get('coherence_breakpoints', [])
                    high_segments = detailed.get('high_coherence_segments', [])
                    
                    semantic_continuity_supplement.append({
                        'story_id': story_id,
                        'semantic_continuity_std': basic_stats.get('coherence_std', np.nan),
                        'low_continuity_points': len(breakpoints),
                        'high_continuity_segments': len(high_segments),
                        'semantic_continuity_median': basic_stats.get('coherence_median', np.nan),
                        'semantic_continuity_max': basic_stats.get('max_coherence', np.nan),
                        'semantic_continuity_min': basic_stats.get('min_coherence', np.nan)
                    })
                    
                except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                    print(f"Warning: 无法加载baseline连贯性数据 {coherence_file}: {e}")
    
    if semantic_continuity_supplement:
        print(f"   加载语义连续性补充数据: {len(semantic_continuity_supplement)} 个故事")
        return pd.DataFrame(semantic_continuity_supplement)
    else:
        print("Warning: 没有找到语义连续性补充数据")
        return None

def load_emotion_supplement():
    """加载情感分析补充数据（classification_agreement, 章节级scores）"""
    emotion_supplement = []
    
    # 遍历所有analysis_test目录中的情感分析文件
    test_dirs = [
        '/Users/haha/Story/data/analysis_test/regression_test_analysis',
        '/Users/haha/Story/data/analysis_test/horror_test_analysis', 
        '/Users/haha/Story/data/analysis_test/romantic_test_analysis'
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            # 查找每个故事目录中的roberta_labmt_analysis文件
            for story_dir in os.listdir(test_dir):
                story_path = os.path.join(test_dir, story_dir)
                if os.path.isdir(story_path):
                    # 查找情感分析文件
                    emotion_files = glob.glob(os.path.join(story_path, 'roberta_labmt_analysis_*.json'))
                    if emotion_files:
                        try:
                            with open(emotion_files[0], 'r') as f:
                                emotion_data = json.load(f)
                            
                            story_id = create_story_id(story_dir)
                            
                            # 提取一致性信息 - 支持新旧两种格式
                            consistency = emotion_data.get('consistency_assessment', {})
                            
                            # 如果是新格式，从comparison_analysis中提取
                            if not consistency and 'comparison_analysis' in emotion_data:
                                comparison = emotion_data['comparison_analysis']
                                consistency = comparison.get('consistency_assessment', {})
                            
                            chapter_analysis = emotion_data.get('chapter_analysis', [])
                            
                            # 计算章节级统计
                            roberta_scores = [ch.get('roberta_score', 0) for ch in chapter_analysis]
                            labmt_scores = [ch.get('labmt_score', 0) for ch in chapter_analysis]
                            
                            emotion_supplement.append({
                                'story_id': story_id,
                                'classification_agreement': consistency.get('classification_agreement', np.nan),
                                'major_disagreements': consistency.get('major_disagreements', np.nan),
                                'roberta_scores_str': ','.join(map(str, roberta_scores[:10])),  # 只存前10个章节，避免字段过长
                                'labmt_scores_str': ','.join(map(str, labmt_scores[:10])),
                                'roberta_std': np.std(roberta_scores) if roberta_scores else np.nan,
                                'labmt_std': np.std(labmt_scores) if labmt_scores else np.nan,
                                'emotion_correlation': np.corrcoef(roberta_scores, labmt_scores)[0,1] if len(roberta_scores) > 1 and len(labmt_scores) > 1 else np.nan
                            })
                            
                        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                            print(f"Warning: 无法加载 {emotion_files[0]}: {e}")
                            continue
    
    # 处理baseline的情感数据
    baseline_dirs = [
        '/Users/haha/Story/data/analysis_test/sci_baseline_analysis',
        '/Users/haha/Story/data/analysis_test/normal_baseline_analysis'
    ]
    
    for baseline_dir in baseline_dirs:
        if os.path.exists(baseline_dir):
            emotion_files = glob.glob(os.path.join(baseline_dir, 'roberta_labmt_analysis_*.json'))
            if emotion_files:
                try:
                    with open(emotion_files[0], 'r') as f:
                        emotion_data = json.load(f)
                    
                    # 确定baseline的story_id
                    if 'sci_baseline' in baseline_dir:
                        story_id = 'sciencefiction_baseline_Tbaseline_sbaseline'
                    else:
                        story_id = 'baseline_baseline_Tbaseline_sbaseline'
                    
                    # 提取一致性信息 - 支持新旧两种格式
                    consistency = emotion_data.get('consistency_assessment', {})
                    
                    # 如果是新格式，从comparison_analysis中提取
                    if not consistency and 'comparison_analysis' in emotion_data:
                        comparison = emotion_data['comparison_analysis']
                        consistency = comparison.get('consistency_assessment', {})
                    
                    chapter_analysis = emotion_data.get('chapter_analysis', [])
                    
                    roberta_scores = [ch.get('roberta_score', 0) for ch in chapter_analysis]
                    labmt_scores = [ch.get('labmt_score', 0) for ch in chapter_analysis]
                    
                    emotion_supplement.append({
                        'story_id': story_id,
                        'classification_agreement': consistency.get('classification_agreement', np.nan),
                        'major_disagreements': consistency.get('major_disagreements', np.nan),
                        'roberta_scores_str': ','.join(map(str, roberta_scores[:10])),
                        'labmt_scores_str': ','.join(map(str, labmt_scores[:10])),
                        'roberta_std': np.std(roberta_scores) if roberta_scores else np.nan,
                        'labmt_std': np.std(labmt_scores) if labmt_scores else np.nan,
                        'emotion_correlation': np.corrcoef(roberta_scores, labmt_scores)[0,1] if len(roberta_scores) > 1 and len(labmt_scores) > 1 else np.nan
                    })
                    
                except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                    print(f"Warning: 无法加载baseline情感数据 {emotion_files[0]}: {e}")
    
    if emotion_supplement:
        print(f"   加载情感分析补充数据: {len(emotion_supplement)} 个故事")
        return pd.DataFrame(emotion_supplement)
    else:
        print("Warning: 没有找到情感分析补充数据")
        return None

def load_performance_data():
    """加载性能数据（wall_time_sec, peak_mem_mb, tokens_total, cost_usd）"""
    performance_supplement = []
    
    # 遍历所有可能包含性能数据的目录
    test_dirs = [
        '/Users/haha/Story/data/output/regression_test',
        '/Users/haha/Story/data/output/horror_test', 
        '/Users/haha/Story/data/output/romantic_test'
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            # 查找每个故事目录中的性能分析文件
            for story_dir in os.listdir(test_dir):
                story_path = os.path.join(test_dir, story_dir)
                if os.path.isdir(story_path):
                    # 查找性能分析文件
                    perf_files = glob.glob(os.path.join(story_path, 'performance_analysis_*.json'))
                    if perf_files:
                        try:
                            with open(perf_files[0], 'r') as f:
                                perf_data = json.load(f)
                            
                            story_id = create_story_id(story_dir)
                            
                            # 提取性能指标
                            metadata = perf_data.get('metadata', {})
                            
                            performance_supplement.append({
                                'story_id': story_id,
                                'wall_time_sec': metadata.get('total_execution_time', np.nan),
                                'peak_mem_mb': metadata.get('peak_memory_usage_mb', np.nan),
                                'tokens_total': metadata.get('total_tokens', np.nan),
                                'cost_usd': metadata.get('total_api_cost', np.nan),
                                'task_name': metadata.get('task_name', '')
                            })
                            
                        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                            print(f"Warning: 无法加载 {perf_files[0]}: {e}")
                            continue
    
    # 检查baseline是否有性能数据（通常baseline没有性能数据，因为它们是人工写的）
    # 但如果有的话也加载进来
    baseline_dirs = [
        '/Users/haha/Story/data/output/sci_baseline',
        '/Users/haha/Story/data/output/normal_baseline'
    ]
    
    for baseline_dir in baseline_dirs:
        if os.path.exists(baseline_dir):
            perf_files = glob.glob(os.path.join(baseline_dir, 'performance_analysis_*.json'))
            if perf_files:
                try:
                    with open(perf_files[0], 'r') as f:
                        perf_data = json.load(f)
                    
                    # 确定baseline的story_id
                    if 'sci_baseline' in baseline_dir:
                        story_id = 'sciencefiction_baseline_Tbaseline_sbaseline'
                    else:
                        story_id = 'baseline_baseline_Tbaseline_sbaseline'
                    
                    metadata = perf_data.get('metadata', {})
                    
                    performance_supplement.append({
                        'story_id': story_id,
                        'wall_time_sec': metadata.get('total_execution_time', np.nan),
                        'peak_mem_mb': metadata.get('peak_memory_usage_mb', np.nan), 
                        'tokens_total': metadata.get('total_tokens', np.nan),
                        'cost_usd': metadata.get('total_api_cost', np.nan),
                        'task_name': metadata.get('task_name', '')
                    })
                    
                except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
                    print(f"Warning: 无法加载baseline性能数据 {perf_files[0]}: {e}")
    
    if performance_supplement:
        print(f"   加载性能数据: {len(performance_supplement)} 个故事")
        return pd.DataFrame(performance_supplement)
    else:
        print("Warning: 没有找到任何性能数据")
        return None

def create_master_table():
    """创建主表"""
    print("="*80)
    print("开始创建metrics_master.csv主表")
    print("="*80)
    
    # 1. 加载核心数据作为基础
    print("1. 加载核心指标数据...")
    master_df = load_core_metrics()
    print(f"   核心数据: {len(master_df)} 行")
    
    # 2. 合并逐篇多样性数据
    print("2. 合并逐篇多样性数据...")
    diversity_individual = load_diversity_individual()
    if diversity_individual is not None:
        master_df = master_df.merge(diversity_individual, on='story_id', how='left')
        print(f"   合并后: {len(master_df)} 行, 新增 {len(diversity_individual.columns)-1} 列")
    else:
        # 如果没有数据，添加空列
        master_df['distinct_avg'] = np.nan
        master_df['distinct_score'] = np.nan
        print("   添加空的多样性列")
    
    # 3. 合并流畅性数据
    print("3. 合并流畅性数据...")
    fluency_data = load_fluency_data()
    if fluency_data is not None:
        master_df = master_df.merge(fluency_data, on='story_id', how='left')
        print(f"   合并后: {len(master_df)} 行, 新增 {len(fluency_data.columns)-1} 列")
    else:
        # 添加空的流畅性列
        master_df['pseudo_ppl'] = np.nan
        master_df['error_count'] = np.nan
        master_df['fluency_word_count'] = np.nan
        master_df['err_per_100w'] = np.nan
        print("   添加空的流畅性列")
    
    # 4. 合并组级多样性数据
    print("4. 合并组级多样性数据...")
    diversity_group = load_diversity_group()
    if diversity_group is not None:
        # 构造匹配键
        master_df['group_key'] = master_df['genre'] + '_' + master_df['structure'] + '_T' + master_df['temperature'].astype(str)
        master_df = master_df.merge(diversity_group, on='group_key', how='left')
        master_df = master_df.drop('group_key', axis=1)  # 删除临时键
        print(f"   合并后: {len(master_df)} 行, 新增 {len(diversity_group.columns)-1} 列")
    else:
        # 添加空的组级多样性列
        master_df['diversity_group_score'] = np.nan
        master_df['alpha_value'] = np.nan
        master_df['self_bleu_group'] = np.nan
        master_df['one_minus_self_bleu'] = np.nan
        print("   添加空的组级多样性列")
    
    # 5. 合并语义连续性补充数据...
    print("5. 合并语义连续性补充数据...")
    semantic_continuity_supp = load_semantic_continuity_supplement()
    if semantic_continuity_supp is not None:
        master_df = master_df.merge(semantic_continuity_supp, on='story_id', how='left')
        print(f"   合并后: {len(master_df)} 行, 新增 {len(semantic_continuity_supp.columns)-1} 列")
    
    # 6. 合并情感分析补充数据...
    print("6. 合并情感分析补充数据...")
    emotion_supp = load_emotion_supplement()
    if emotion_supp is not None:
        master_df = master_df.merge(emotion_supp, on='story_id', how='left')
        print(f"   合并后: {len(master_df)} 行, 新增 {len(emotion_supp.columns)-1} 列")
    
    # 7. 合并性能数据...
    print("7. 合并性能数据...")
    performance_supp = load_performance_data()
    if performance_supp is not None:
        master_df = master_df.merge(performance_supp, on='story_id', how='left')
        print(f"   合并后: {len(master_df)} 行, 新增 {len(performance_supp.columns)-1} 列")
    
    # 8. 计算派生字段...
    print("8. 计算派生字段...")
    
    # 拆分tp_coverage为数值
    def split_tp_coverage(tp_str):
        if pd.isna(tp_str) or tp_str == '':
            return np.nan, np.nan
        try:
            if '/' in str(tp_str):
                parts = str(tp_str).split('/')
                return int(parts[0]), int(parts[1])
            else:
                return np.nan, np.nan
        except:
            return np.nan, np.nan
    
    master_df[['tp_m', 'tp_n']] = master_df['tp_coverage'].apply(
        lambda x: pd.Series(split_tp_coverage(x))
    )
    
    # 计算tp完成率
    master_df['tp_completion_rate'] = master_df['tp_m'] / master_df['tp_n']
    
    # 方向一致性 (基于correlation_coefficient)
    master_df['direction_consistency'] = master_df['correlation_coefficient'].apply(
        lambda x: abs(x) if pd.notna(x) else np.nan
    )
    
    # 添加meta信息 - alpha按题材
    genre_alpha_map = {}
    if diversity_group is not None:
        # 从组级数据中提取每个题材的alpha值
        for _, row in diversity_group.iterrows():
            genre = row['group_key'].split('_')[0]
            if genre not in genre_alpha_map:
                genre_alpha_map[genre] = row['alpha_value']
    
    master_df['alpha_genre'] = master_df['genre'].map(genre_alpha_map)
    
    # 8. 去重（特别是baseline可能重复）
    print("8. 去除重复数据...")
    before_dedup = len(master_df)
    master_df = master_df.drop_duplicates(subset=['story_id'], keep='first')
    after_dedup = len(master_df)
    if before_dedup != after_dedup:
        print(f"   去除了 {before_dedup - after_dedup} 行重复数据")
    
    # 7. 重排列顺序
    column_order = [
        # 基础标识
        'story_id', 'original_config_name', 'test_type', 'genre', 'structure', 
        'temperature', 'seed', 'is_baseline',
        
        # 多样性 (Diversity)
        'distinct_avg', 'diversity_group_score', 'alpha_genre', 'alpha_value',
        'distinct_score', 'self_bleu_group', 'one_minus_self_bleu',
        
        # 语义连续性 (Semantic Continuity) - 扩展
        'avg_semantic_continuity', 'semantic_continuity_sentence_count', 'semantic_continuity_std', 'low_continuity_points', 
        'high_continuity_segments', 'semantic_continuity_median', 'semantic_continuity_max', 'semantic_continuity_min',
        
        # 流畅性 (Fluency)
        'pseudo_ppl', 'err_per_100w', 'error_count', 'fluency_word_count',
        
        # 情感轨迹 (Emotion Arc) - 扩展
        'correlation_coefficient', 'direction_consistency', 'classification_agreement',
        'roberta_avg_score', 'reagan_classification', 'chapter_count',
        'major_disagreements', 'roberta_std', 'labmt_std', 'emotion_correlation',
        'roberta_scores_str', 'labmt_scores_str',
        
        # 结构完整性 (Structure) - 扩展
        'tp_coverage', 'tp_m', 'tp_n', 'tp_completion_rate',
        'li_function_diversity', 'total_events', 'total_words', 'total_sentences',
        
        # 性能 (Performance)
        'wall_time_sec', 'peak_mem_mb', 'tokens_total', 'cost_usd'
    ]
    
    # 只选择存在的列
    available_cols = [col for col in column_order if col in master_df.columns]
    master_df = master_df[available_cols]
    
    return master_df

def main():
    """主函数"""
    # 创建主表
    master_df = create_master_table()
    
    # 保存结果
    output_file = '/Users/haha/Story/metrics_master.csv'
    master_df.to_csv(output_file, index=False, encoding='utf-8')
    
    # 打印统计信息
    print("\n" + "="*80)
    print("metrics_master.csv 创建完成！")
    print("="*80)
    print(f"保存路径: {output_file}")
    print(f"总行数: {len(master_df)}")
    print(f"总列数: {len(master_df.columns)}")
    
    # 按类型统计
    print(f"\n按类型统计:")
    type_counts = master_df['genre'].value_counts()
    for genre, count in type_counts.items():
        print(f"  {genre}: {count} 个故事")
    
    # 数据完整性检查
    print(f"\n数据完整性:")
    key_cols = ['distinct_avg', 'diversity_group_score', 'avg_semantic_continuity', 
                'pseudo_ppl', 'correlation_coefficient']
    
    for col in key_cols:
        if col in master_df.columns:
            complete_count = master_df[col].notna().sum()
            print(f"  {col}: {complete_count}/{len(master_df)} ({complete_count/len(master_df)*100:.1f}%)")
    
    # 显示前几行作为示例
    print(f"\n数据示例:")
    print(master_df.head(3).to_string())
    
    return master_df

if __name__ == "__main__":
    df = main()
