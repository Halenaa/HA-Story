#!/usr/bin/env python3
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import re

def extract_text_features(md_file_path):
    """提取文本特征"""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 计算章节数
        chapters = re.findall(r'# Chapter \d+', content)
        chapter_count = len(chapters)
        
        # 计算句子数
        sentences = re.split(r'[。！？.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # 计算英文字数
        words = re.findall(r'\b[a-zA-Z]+\b', content)
        word_count = len(words)
        
        return {
            'total_words': word_count,
            'chapter_count': chapter_count,
            'sentence_count': sentence_count
        }
    except Exception as e:
        print(f"Error extracting text features from {md_file_path}: {e}")
        return {
            'total_words': 0,
            'chapter_count': 0,
            'sentence_count': 0
        }

def extract_emotional_metrics(emotional_data):
    """提取情感弧线指标"""
    try:
        if 'error' in emotional_data:
            return {
                'roberta_avg_score': None,
                'reagan_classification': None,
                'correlation_coefficient': None
            }
        
        # RoBERTa平均分数
        roberta_scores = emotional_data.get('primary_analysis', {}).get('scores', [])
        roberta_avg_score = np.mean(roberta_scores) if roberta_scores else None
        
        # Reagan分类
        reagan_classification = emotional_data.get('primary_analysis', {}).get('reagan_classification', {}).get('best_match', None)
        
        # 相关性系数
        correlation_coefficient = emotional_data.get('correlation_analysis', {}).get('pearson_correlation', {}).get('r', None)
        
        return {
            'roberta_avg_score': roberta_avg_score,
            'reagan_classification': reagan_classification,
            'correlation_coefficient': correlation_coefficient
        }
    except Exception as e:
        print(f"Error extracting emotional metrics: {e}")
        return {
            'roberta_avg_score': None,
            'reagan_classification': None,
            'correlation_coefficient': None
        }

def extract_coherence_metrics(hred_data):
    """提取连贯性指标"""
    try:
        if 'error' in hred_data:
            return {
                'hred_avg_coherence': None,
                'total_sentences': None
            }
        
        # HRED平均连贯性分数
        hred_avg_coherence = hred_data.get('HRED_coherence_evaluation', {}).get('average_coherence', None)
        
        # 总句子数
        total_sentences = hred_data.get('HRED_coherence_evaluation', {}).get('total_sentences', None)
        
        return {
            'hred_avg_coherence': hred_avg_coherence,
            'total_sentences': total_sentences
        }
    except Exception as e:
        print(f"Error extracting coherence metrics: {e}")
        return {
            'hred_avg_coherence': None,
            'total_sentences': None
        }

def extract_structure_metrics(structure_data):
    """提取结构分析指标"""
    try:
        if 'error' in structure_data:
            return {
                'tp_coverage': None,
                'li_function_diversity': None,
                'total_events': None
            }
        
        # TP覆盖率
        tp_coverage = structure_data.get('structure_analysis', {}).get('Papalampidi_structure_analysis', {}).get('turning_point_integrity', {}).get('TP_coverage', None)
        
        # Li功能多样性
        li_function_diversity = structure_data.get('structure_analysis', {}).get('Li_function_analysis', {}).get('function_diversity', None)
        
        # 总事件数
        total_events = structure_data.get('structure_analysis', {}).get('basic_info', {}).get('total_events', None)
        
        return {
            'tp_coverage': tp_coverage,
            'li_function_diversity': li_function_diversity,
            'total_events': total_events
        }
    except Exception as e:
        print(f"Error extracting structure metrics: {e}")
        return {
            'tp_coverage': None,
            'li_function_diversity': None,
            'total_events': None
        }

def parse_config_name(folder_name):
    """解析配置名称"""
    try:
        # 处理baseline配置
        if folder_name == 'sci_baseline':
            return {
                'genre': 'sciencefiction',
                'structure': 'baseline',
                'temperature': 'baseline',
                'seed': 'baseline'
            }
        
        # 解析格式: thelittleredridinghood_[genre]_[structure]_T[temperature]_s[seed]
        # 例如: thelittleredridinghood_sciencefictionrewrite_linear_T0.3_s1
        
        # 使用正则表达式提取信息
        import re
        
        # 匹配结构类型 (linear 或 nonlinear)
        structure_match = re.search(r'_(linear|nonlinear)_', folder_name)
        structure = structure_match.group(1) if structure_match else 'unknown'
        
        # 匹配温度 (T0.3, T0.7, T0.9)
        temp_match = re.search(r'_T(0\.[379])_', folder_name)
        temperature = temp_match.group(1) if temp_match else 'unknown'
        
        # 匹配种子 (s1, s2, s3)
        seed_match = re.search(r'_s([123])$', folder_name)
        seed = seed_match.group(1) if seed_match else 'unknown'
        
        # 匹配类型 (sciencefictionrewrite, horror-suspenserewrite, romanticrewrite)
        if 'sciencefictionrewrite' in folder_name:
            genre = 'sciencefiction'
        elif 'horror-suspenserewrite' in folder_name:
            genre = 'horror'
        elif 'romanticrewrite' in folder_name:
            genre = 'romantic'
        else:
            genre = 'unknown'
        
        return {
            'genre': genre,
            'structure': structure,
            'temperature': temperature,
            'seed': seed
        }
    except Exception as e:
        print(f"Error parsing config name {folder_name}: {e}")
        return {
            'genre': 'unknown',
            'structure': 'unknown',
            'temperature': 'unknown',
            'seed': 'unknown'
        }

def main():
    """主函数"""
    print("开始提取核心指标...")
    
    # 设置路径
    analysis_base_dir = "/Users/haha/Story/data/analysis_test"
    output_dir = "/Users/haha/Story/data"
    
    # 收集所有分析结果
    all_metrics = []
    
    # 遍历四个测试文件夹（包括baseline）
    test_folders = ['regression_test_analysis', 'horror_test_analysis', 'romantic_test_analysis', 'sci_baseline_analysis']
    """提取文本特征"""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 计算章节数
        chapters = re.findall(r'# Chapter \d+', content)
        chapter_count = len(chapters)
        
        # 计算句子数
        sentences = re.split(r'[。！？.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # 计算英文字数
        words = re.findall(r'\b[a-zA-Z]+\b', content)
        word_count = len(words)
        
        return {
            'total_words': word_count,
            'chapter_count': chapter_count,
            'sentence_count': sentence_count
        }
    except Exception as e:
        print(f"Error extracting text features from {md_file_path}: {e}")
        return {
            'total_words': 0,
            'chapter_count': 0,
            'sentence_count': 0
        }

def extract_emotional_metrics(emotional_data):
    """提取情感弧线指标"""
    try:
        if 'error' in emotional_data:
            return {
                'roberta_avg_score': None,
                'reagan_classification': None,
                'correlation_coefficient': None
            }
        
        # RoBERTa平均分数
        roberta_scores = emotional_data.get('primary_analysis', {}).get('scores', [])
        roberta_avg_score = np.mean(roberta_scores) if roberta_scores else None
        
        # Reagan分类
        reagan_classification = emotional_data.get('primary_analysis', {}).get('reagan_classification', {}).get('best_match', None)
        
        # 相关性系数
        correlation_coefficient = emotional_data.get('correlation_analysis', {}).get('pearson_correlation', {}).get('r', None)
        
        return {
            'roberta_avg_score': roberta_avg_score,
            'reagan_classification': reagan_classification,
            'correlation_coefficient': correlation_coefficient
        }
    except Exception as e:
        print(f"Error extracting emotional metrics: {e}")
        return {
            'roberta_avg_score': None,
            'reagan_classification': None,
            'correlation_coefficient': None
        }

def extract_coherence_metrics(hred_data):
    """提取连贯性指标"""
    try:
        if 'error' in hred_data:
            return {
                'hred_avg_coherence': None,
                'total_sentences': None
            }
        
        # HRED平均连贯性分数
        hred_avg_coherence = hred_data.get('HRED_coherence_evaluation', {}).get('average_coherence', None)
        
        # 总句子数
        total_sentences = hred_data.get('HRED_coherence_evaluation', {}).get('total_sentences', None)
        
        return {
            'hred_avg_coherence': hred_avg_coherence,
            'total_sentences': total_sentences
        }
    except Exception as e:
        print(f"Error extracting coherence metrics: {e}")
        return {
            'hred_avg_coherence': None,
            'total_sentences': None
        }

def extract_structure_metrics(structure_data):
    """提取结构分析指标"""
    try:
        if 'error' in structure_data:
            return {
                'tp_coverage': None,
                'li_function_diversity': None,
                'total_events': None
            }
        
        # TP覆盖率
        tp_coverage = structure_data.get('structure_analysis', {}).get('Papalampidi_structure_analysis', {}).get('turning_point_integrity', {}).get('TP_coverage', None)
        
        # Li功能多样性
        li_function_diversity = structure_data.get('structure_analysis', {}).get('Li_function_analysis', {}).get('function_diversity', None)
        
        # 总事件数
        total_events = structure_data.get('structure_analysis', {}).get('basic_info', {}).get('total_events', None)
        
        return {
            'tp_coverage': tp_coverage,
            'li_function_diversity': li_function_diversity,
            'total_events': total_events
        }
    except Exception as e:
        print(f"Error extracting structure metrics: {e}")
        return {
            'tp_coverage': None,
            'li_function_diversity': None,
            'total_events': None
        }

def parse_config_name(folder_name):
    """解析配置名称"""
    try:
        # 解析格式: thelittleredridinghood_[genre]_[structure]_T[temperature]_s[seed]
        # 例如: thelittleredridinghood_sciencefictionrewrite_linear_T0.3_s1
        
        # 使用正则表达式提取信息
        import re
        
        # 匹配结构类型 (linear 或 nonlinear)
        structure_match = re.search(r'_(linear|nonlinear)_', folder_name)
        structure = structure_match.group(1) if structure_match else 'unknown'
        
        # 匹配温度 (T0.3, T0.7, T0.9)
        temp_match = re.search(r'_T(0\.[379])_', folder_name)
        temperature = temp_match.group(1) if temp_match else 'unknown'
        
        # 匹配种子 (s1, s2, s3)
        seed_match = re.search(r'_s([123])$', folder_name)
        seed = seed_match.group(1) if seed_match else 'unknown'
        
        # 匹配类型 (sciencefictionrewrite, horror-suspenserewrite, romanticrewrite)
        if 'sciencefictionrewrite' in folder_name:
            genre = 'sciencefiction'
        elif 'horror-suspenserewrite' in folder_name:
            genre = 'horror'
        elif 'romanticrewrite' in folder_name:
            genre = 'romantic'
        else:
            genre = 'unknown'
        
        return {
            'genre': genre,
            'structure': structure,
            'temperature': temperature,
            'seed': seed
        }
    except Exception as e:
        print(f"Error parsing config name {folder_name}: {e}")
        return {
            'genre': 'unknown',
            'structure': 'unknown',
            'temperature': 'unknown',
            'seed': 'unknown'
        }

def main():
    """主函数"""
    print("开始提取核心指标...")
    
    # 设置路径
    analysis_base_dir = "/Users/haha/Story/data/analysis_test"
    output_dir = "/Users/haha/Story/data"
    
    # 收集所有分析结果
    all_metrics = []
    
    # 遍历四个测试文件夹（包括baseline）
    test_folders = ['regression_test_analysis', 'horror_test_analysis', 'romantic_test_analysis', 'sci_baseline_analysis']
    
    for test_folder in test_folders:
        test_dir = os.path.join(analysis_base_dir, test_folder)
        
        if not os.path.exists(test_dir):
            print(f"警告: {test_dir} 不存在")
            continue
        
        print(f"\n处理 {test_folder}...")
        
        # 遍历每个配置文件夹
        for config_folder in os.listdir(test_dir):
            config_path = os.path.join(test_dir, config_folder)
            
            if not os.path.isdir(config_path):
                continue
            
            print(f"  处理配置: {config_folder}")
            
            # 读取综合分析结果
            comprehensive_file = os.path.join(config_path, 'comprehensive_analysis.json')
            
            if not os.path.exists(comprehensive_file):
                print(f"    警告: {comprehensive_file} 不存在")
                continue
            
            try:
                with open(comprehensive_file, 'r', encoding='utf-8') as f:
                    comprehensive_data = json.load(f)
                
                # 解析配置名称
                config_info = parse_config_name(config_folder)
                
                # 提取情感弧线指标 (尝试两种键名格式)
                emotional_data = comprehensive_data.get('emotional_arc_analysis', comprehensive_data.get('emotional_arc', {}))
                emotional_metrics = extract_emotional_metrics(emotional_data)
                
                # 提取连贯性指标 (尝试两种键名格式)
                coherence_data = comprehensive_data.get('hred_coherence_analysis', comprehensive_data.get('hred_coherence', {}))
                coherence_metrics = extract_coherence_metrics(coherence_data)
                
                # 提取结构分析指标 (尝试两种键名格式)
                structure_data = comprehensive_data.get('story_structure_analysis', comprehensive_data.get('story_structure', {}))
                structure_metrics = extract_structure_metrics(structure_data)
                
                # 提取文本特征
                # 需要找到对应的markdown文件
                md_file_path = None
                if test_folder == 'regression_test_analysis':
                    md_file_path = f"/Users/haha/Story/data/output/regression_test/{config_folder}/enhanced_story_dialogue_updated.md"
                elif test_folder == 'horror_test_analysis':
                    md_file_path = f"/Users/haha/Story/data/output/horror_test/{config_folder}/enhanced_story_dialogue_updated.md"
                elif test_folder == 'romantic_test_analysis':
                    md_file_path = f"/Users/haha/Story/data/output/romantic_test/{config_folder}/enhanced_story_dialogue_updated.md"
                elif test_folder == 'sci_baseline_analysis':
                    md_file_path = "/Users/haha/Story/data/sci_baseline.md"
                
                text_features = extract_text_features(md_file_path) if md_file_path and os.path.exists(md_file_path) else {
                    'total_words': 0,
                    'chapter_count': 0,
                    'sentence_count': 0
                }
                
                # 合并所有指标
                config_metrics = {
                    'config_name': config_folder,
                    'test_type': test_folder.replace('_test_analysis', ''),
                    **config_info,
                    **emotional_metrics,
                    **coherence_metrics,
                    **structure_metrics,
                    **text_features
                }
                
                all_metrics.append(config_metrics)
                
            except Exception as e:
                print(f"    错误处理 {config_folder}: {e}")
                continue
    
    # 转换为DataFrame
    df = pd.DataFrame(all_metrics)
    
    # 保存结果
    output_file = os.path.join(output_dir, 'core_metrics_analysis.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # 保存JSON格式
    output_json = os.path.join(output_dir, 'core_metrics_analysis.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    print(f"\n{'='*80}")
    print("核心指标提取完成！")
    print(f"{'='*80}")
    print(f"总配置数: {len(all_metrics)}")
    print(f"CSV文件: {output_file}")
    print(f"JSON文件: {output_json}")
    
    # 按测试类型统计
    test_counts = df['test_type'].value_counts()
    print(f"\n按测试类型统计:")
    for test_type, count in test_counts.items():
        print(f"  {test_type}: {count}个配置")
    
    # 按结构类型统计
    structure_counts = df['structure'].value_counts()
    print(f"\n按结构类型统计:")
    for structure, count in structure_counts.items():
        print(f"  {structure}: {count}个配置")
    
    # 按温度统计
    temp_counts = df['temperature'].value_counts()
    print(f"\n按温度统计:")
    for temp, count in temp_counts.items():
        print(f"  T{temp}: {count}个配置")
    
    # 检查数据完整性
    print(f"\n数据完整性检查:")
    print(f"  情感分析完整: {df['roberta_avg_score'].notna().sum()}/{len(df)}")
    print(f"  连贯性分析完整: {df['hred_avg_coherence'].notna().sum()}/{len(df)}")
    print(f"  结构分析完整: {df['tp_coverage'].notna().sum()}/{len(df)}")
    print(f"  文本特征完整: {df['total_words'].notna().sum()}/{len(df)}")
    
    return df

if __name__ == "__main__":
    df = main()

def main():
    """主函数"""
    print("开始提取核心指标...")
    
    # 设置路径
    analysis_base_dir = "/Users/haha/Story/data/analysis_test"
    output_dir = "/Users/haha/Story/data"
    
    # 收集所有分析结果
    all_metrics = []
    
    # 遍历四个测试文件夹（包括baseline）
    test_folders = ['regression_test_analysis', 'horror_test_analysis', 'romantic_test_analysis', 'sci_baseline_analysis']
    
    for test_folder in test_folders:
        test_dir = os.path.join(analysis_base_dir, test_folder)
        
        if not os.path.exists(test_dir):
            print(f"警告: {test_dir} 不存在")
            continue
        
        print(f"\n处理 {test_folder}...")
        
        # 处理baseline配置（特殊处理）
        if test_folder == 'sci_baseline_analysis':
            print(f"  处理配置: sci_baseline")
            try:
                # 读取单独的分析文件（在sci_baseline_analysis目录的根目录下）
                emotional_file = os.path.join(test_dir, 'emotional_arc_analysis.json')
                coherence_file = os.path.join(test_dir, 'hred_coherence_analysis.json')
                structure_file = os.path.join(test_dir, 'story_structure_analysis.json')
                
                # 读取情感分析
                emotional_data = {}
                if os.path.exists(emotional_file):
                    with open(emotional_file, 'r', encoding='utf-8') as f:
                        emotional_data = json.load(f)
                
                # 读取连贯性分析
                coherence_data = {}
                if os.path.exists(coherence_file):
                    with open(coherence_file, 'r', encoding='utf-8') as f:
                        coherence_data = json.load(f)
                
                # 读取结构分析
                structure_data = {}
                if os.path.exists(structure_file):
                    with open(structure_file, 'r', encoding='utf-8') as f:
                        structure_data = json.load(f)
                
                # 提取指标
                emotional_metrics = extract_emotional_metrics(emotional_data)
                coherence_metrics = extract_coherence_metrics(coherence_data)
                structure_metrics = extract_structure_metrics(structure_data)
                
                # 为baseline设置固定的配置信息
                config_info = {
                    'genre': 'baseline',
                    'structure': 'baseline',
                    'temperature': 'baseline',
                    'seed': 'baseline'
                }
                config_folder = 'sci_baseline'  # 使用固定的配置名称
                
                # 提取文本特征
                md_file_path = "/Users/haha/Story/data/sci_baseline.md"
                text_features = extract_text_features(md_file_path) if md_file_path and os.path.exists(md_file_path) else {
                    'total_words': 0,
                    'chapter_count': 0,
                    'sentence_count': 0
                }
                
                # 合并所有指标
                config_metrics = {
                    'config_name': config_folder,
                    'test_type': test_folder.replace('_test_analysis', ''),
                    **config_info,
                    **emotional_metrics,
                    **coherence_metrics,
                    **structure_metrics,
                    **text_features
                }
                
                all_metrics.append(config_metrics)
                
            except Exception as e:
                print(f"    错误: 处理baseline配置失败: {e}")
                continue
        else:
            # 遍历每个配置文件夹
            for config_folder in os.listdir(test_dir):
                config_path = os.path.join(test_dir, config_folder)
                
                if not os.path.isdir(config_path):
                    continue
                
                print(f"  处理配置: {config_folder}")
                
                try:
                    # 解析配置名称
                    config_info = parse_config_name(config_folder)
                    
                    # 处理其他配置（有comprehensive_analysis.json）
                    comprehensive_file = os.path.join(config_path, 'comprehensive_analysis.json')
                    
                    if not os.path.exists(comprehensive_file):
                        print(f"    警告: {comprehensive_file} 不存在")
                        continue
                    
                    try:
                        with open(comprehensive_file, 'r', encoding='utf-8') as f:
                            comprehensive_data = json.load(f)
                        
                        # 提取情感弧线指标 (尝试两种键名格式)
                        emotional_data = comprehensive_data.get('emotional_arc_analysis', comprehensive_data.get('emotional_arc', {}))
                        emotional_metrics = extract_emotional_metrics(emotional_data)
                        
                        # 提取连贯性指标 (尝试两种键名格式)
                        coherence_data = comprehensive_data.get('hred_coherence_analysis', comprehensive_data.get('hred_coherence', {}))
                        coherence_metrics = extract_coherence_metrics(coherence_data)
                        
                        # 提取结构分析指标 (尝试两种键名格式)
                        structure_data = comprehensive_data.get('story_structure_analysis', comprehensive_data.get('story_structure', {}))
                        structure_metrics = extract_structure_metrics(structure_data)
                        
                    except Exception as e:
                        print(f"    错误读取综合分析文件 {comprehensive_file}: {e}")
                        emotional_metrics = {}
                        coherence_metrics = {}
                        structure_metrics = {}
                    
                    # 提取文本特征
                    # 需要找到对应的markdown文件
                    md_file_path = None
                    if test_folder == 'regression_test_analysis':
                        md_file_path = f"/Users/haha/Story/data/output/regression_test/{config_folder}/enhanced_story_dialogue_updated.md"
                    elif test_folder == 'horror_test_analysis':
                        md_file_path = f"/Users/haha/Story/data/output/horror_test/{config_folder}/enhanced_story_dialogue_updated.md"
                    elif test_folder == 'romantic_test_analysis':
                        md_file_path = f"/Users/haha/Story/data/output/romantic_test/{config_folder}/enhanced_story_dialogue_updated.md"
                    elif test_folder == 'sci_baseline_analysis':
                        md_file_path = "/Users/haha/Story/data/sci_baseline.md"
                    
                    text_features = extract_text_features(md_file_path) if md_file_path and os.path.exists(md_file_path) else {
                        'total_words': 0,
                        'chapter_count': 0,
                        'sentence_count': 0
                    }
                    
                    # 合并所有指标
                    config_metrics = {
                        'config_name': config_folder,
                        'test_type': test_folder.replace('_test_analysis', ''),
                        **config_info,
                        **emotional_metrics,
                        **coherence_metrics,
                        **structure_metrics,
                        **text_features
                    }
                    
                    all_metrics.append(config_metrics)
                    
                except Exception as e:
                    print(f"    错误处理 {config_folder}: {e}")
                    continue
    
    # 转换为DataFrame
    df = pd.DataFrame(all_metrics)
    
    # 保存结果
    output_file = os.path.join(output_dir, 'core_metrics_analysis.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # 保存JSON格式
    output_json = os.path.join(output_dir, 'core_metrics_analysis.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    print(f"\n{'='*80}")
    print("核心指标提取完成！")
    print(f"{'='*80}")
    print(f"总配置数: {len(all_metrics)}")
    print(f"CSV文件: {output_file}")
    print(f"JSON文件: {output_json}")
    
    # 按测试类型统计
    test_counts = df['test_type'].value_counts()
    print(f"\n按测试类型统计:")
    for test_type, count in test_counts.items():
        print(f"  {test_type}: {count}个配置")
    
    # 按结构类型统计
    structure_counts = df['structure'].value_counts()
    print(f"\n按结构类型统计:")
    for structure, count in structure_counts.items():
        print(f"  {structure}: {count}个配置")
    
    # 按温度统计
    temp_counts = df['temperature'].value_counts()
    print(f"\n按温度统计:")
    for temp, count in temp_counts.items():
        print(f"  T{temp}: {count}个配置")
    
    # 检查数据完整性
    print(f"\n数据完整性检查:")
    print(f"  情感分析完整: {df['roberta_avg_score'].notna().sum()}/{len(df)}")
    print(f"  连贯性分析完整: {df['hred_avg_coherence'].notna().sum()}/{len(df)}")
    print(f"  结构分析完整: {df['tp_coverage'].notna().sum()}/{len(df)}")
    print(f"  文本特征完整: {df['total_words'].notna().sum()}/{len(df)}")
    
    return df

if __name__ == "__main__":
    df = main()