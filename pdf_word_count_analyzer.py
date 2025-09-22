#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计extracted_horror_pdfs文件夹中每个PDF文件的字数
使用类似Word的计数方法
"""

import os
import re
import json
import statistics
from pathlib import Path
from typing import List, Dict
import PyPDF2

def count_words_like_word(text: str) -> int:
    """
    使用类似Microsoft Word的计数方法计算英文字数
    Word的计数方法：
    1. 单词由空格、标点符号分隔
    2. 连字符连接的词算作一个词
    3. 数字序列算作一个词
    4. 标点符号不计入字数
    """
    if not text:
        return 0
    
    # 移除多余的空白行和空格
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # 分割成单词，使用正则表达式匹配单词边界
    # 包括字母、数字、连字符的组合
    words = re.findall(r'\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\b', text)
    
    return len(words)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """从PDF文件中提取文本"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
            
            return text
    except Exception as e:
        print(f"错误：无法读取PDF文件 {pdf_path}: {str(e)}")
        return ""

def analyze_pdf_file(pdf_path: Path) -> Dict:
    """分析单个PDF文件"""
    try:
        # 提取文本
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            return {
                'file_name': pdf_path.name,
                'word_count': 0,
                'char_count': 0,
                'status': 'error: 无法提取文本'
            }
        
        # 计算字数
        word_count = count_words_like_word(text)
        char_count = len(text)
        
        return {
            'file_name': pdf_path.name,
            'word_count': word_count,
            'char_count': char_count,
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'file_name': pdf_path.name,
            'word_count': 0,
            'char_count': 0,
            'status': f'error: {str(e)}'
        }

def get_statistics(word_counts: List[int]) -> Dict:
    """计算统计信息"""
    if not word_counts:
        return {}
    
    return {
        'count': len(word_counts),
        'mean': round(statistics.mean(word_counts), 2),
        'median': round(statistics.median(word_counts), 2),
        'mode': statistics.mode(word_counts) if len(set(word_counts)) < len(word_counts) else 'no mode',
        'std_dev': round(statistics.stdev(word_counts), 2) if len(word_counts) > 1 else 0,
        'min': min(word_counts),
        'max': max(word_counts),
        'range': max(word_counts) - min(word_counts),
        'sum': sum(word_counts)
    }

def parse_file_name(file_name: str) -> dict:
    """解析文件名，提取参数信息"""
    # 格式: linear_T0.3_s1.pdf
    name_without_ext = file_name.replace('.pdf', '')
    parts = name_without_ext.split('_')
    
    if len(parts) >= 3:
        return {
            'structure': parts[0],  # linear or nonlinear
            'temperature': parts[1],  # T0.3, T0.7, T0.9
            'seed': parts[2]  # s1, s2, s3
        }
    return {}

def group_by_parameter(results: list) -> dict:
    """按不同参数分组统计"""
    groups = {
        'by_structure': {},
        'by_temperature': {},
        'by_seed': {}
    }
    
    for result in results:
        if result['status'] != 'success':
            continue
            
        file_info = parse_file_name(result['file_name'])
        if not file_info:
            continue
            
        word_count = result['word_count']
        
        # 按结构分组
        structure = file_info['structure']
        if structure not in groups['by_structure']:
            groups['by_structure'][structure] = []
        groups['by_structure'][structure].append(word_count)
        
        # 按温度分组
        temp = file_info['temperature']
        if temp not in groups['by_temperature']:
            groups['by_temperature'][temp] = []
        groups['by_temperature'][temp].append(word_count)
        
        # 按种子分组
        seed = file_info['seed']
        if seed not in groups['by_seed']:
            groups['by_seed'][seed] = []
        groups['by_seed'][seed].append(word_count)
    
    return groups

def calculate_group_stats(group_data: dict) -> dict:
    """计算分组统计信息"""
    stats = {}
    for key, values in group_data.items():
        if values:
            stats[key] = {
                'count': len(values),
                'mean': round(statistics.mean(values), 2),
                'median': round(statistics.median(values), 2),
                'std_dev': round(statistics.stdev(values), 2) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values)
            }
    return stats

def analyze_folder(folder_path: str, folder_name: str):
    """分析指定文件夹中的PDF文件"""
    pdf_dir = Path(folder_path)
    
    if not pdf_dir.exists():
        print(f"错误：目录 {pdf_dir} 不存在")
        return
    
    print(f"开始分析{folder_name}文件夹中的PDF文件...")
    print("=" * 60)
    
    # 查找所有PDF文件
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("没有找到任何PDF文件")
        return
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    print()
    
    # 分析每个文件
    results = []
    word_counts = []
    
    for pdf_file in sorted(pdf_files):
        print(f"正在分析: {pdf_file.name}")
        result = analyze_pdf_file(pdf_file)
        results.append(result)
        
        if result['status'] == 'success':
            word_counts.append(result['word_count'])
            print(f"  字数: {result['word_count']:,}")
        else:
            print(f"  错误: {result['status']}")
    
    print()
    print("=" * 60)
    print("统计结果:")
    print("=" * 60)
    
    if word_counts:
        stats = get_statistics(word_counts)
        
        print(f"文件总数: {stats['count']}")
        print(f"总字数: {stats['sum']:,}")
        print(f"平均字数: {stats['mean']:,}")
        print(f"中位数: {stats['median']:,}")
        print(f"众数: {stats['mode']}")
        print(f"标准差: {stats['std_dev']:,}")
        print(f"最小字数: {stats['min']:,}")
        print(f"最大字数: {stats['max']:,}")
        print(f"字数范围: {stats['range']:,}")
        
        print()
        print("📈 按结构类型分组统计:")
        print("-" * 40)
        groups = group_by_parameter(results)
        structure_stats = calculate_group_stats(groups['by_structure'])
        for structure, stats in structure_stats.items():
            print(f"{structure.upper():<15} 文件数: {stats['count']:>2} | 平均: {stats['mean']:>7,} | 标准差: {stats['std_dev']:>7,} | 范围: {stats['min']:>5,}-{stats['max']:>5,}")
        
        print()
        print("🌡️ 按温度参数分组统计:")
        print("-" * 40)
        temp_stats = calculate_group_stats(groups['by_temperature'])
        for temp, stats in temp_stats.items():
            print(f"{temp:<15} 文件数: {stats['count']:>2} | 平均: {stats['mean']:>7,} | 标准差: {stats['std_dev']:>7,} | 范围: {stats['min']:>5,}-{stats['max']:>5,}")
        
        print()
        print("🎲 按随机种子分组统计:")
        print("-" * 40)
        seed_stats = calculate_group_stats(groups['by_seed'])
        for seed, stats in seed_stats.items():
            print(f"{seed:<15} 文件数: {stats['count']:>2} | 平均: {stats['mean']:>7,} | 标准差: {stats['std_dev']:>7,} | 范围: {stats['min']:>5,}-{stats['max']:>5,}")
        
        print()
        print("📋 各文件详细统计:")
        print("-" * 60)
        print(f"{'文件名':<30} {'字数':>8} {'字符数':>8}")
        print("-" * 60)
        
        for result in sorted(results, key=lambda x: x['word_count'], reverse=True):
            if result['status'] == 'success':
                print(f"{result['file_name']:<30} {result['word_count']:>8,} {result['char_count']:>8,}")
            else:
                print(f"{result['file_name']:<30} {'ERROR':>8} {'ERROR':>8}")
        
        # 保存结果到JSON文件
        output_data = {
            'summary': stats,
            'file_results': results,
            'group_stats': {
                'by_structure': structure_stats,
                'by_temperature': temp_stats,
                'by_seed': seed_stats
            },
            'analysis_timestamp': str(Path().cwd())
        }
        
        output_file = Path(f"/Users/haha/Story/{folder_name}_pdf_word_count_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"详细结果已保存到: {output_file}")
        
    else:
        print("没有成功分析任何文件")
    
    return results, word_counts

def main():
    """主函数"""
    folders_to_analyze = [
        ("/Users/haha/Story/extracted_romantic_pdfs", "romantic"),
        ("/Users/haha/Story/Sci-Fi_pdfs", "scifi")
    ]
    
    all_results = {}
    
    for folder_path, folder_name in folders_to_analyze:
        print(f"\n{'='*80}")
        print(f"分析 {folder_name.upper()} 文件夹")
        print(f"{'='*80}")
        
        results, word_counts = analyze_folder(folder_path, folder_name)
        all_results[folder_name] = {
            'results': results,
            'word_counts': word_counts
        }
    
    # 生成对比报告
    print(f"\n{'='*80}")
    print("对比分析报告")
    print(f"{'='*80}")
    
    for folder_name, data in all_results.items():
        if data['word_counts']:
            stats = get_statistics(data['word_counts'])
            print(f"\n{folder_name.upper()} 文件夹:")
            print(f"  平均字数: {stats['mean']:,}")
            print(f"  中位数: {stats['median']:,}")
            print(f"  文件数: {stats['count']}")
            print(f"  总字数: {stats['sum']:,}")
            print(f"  字数范围: {stats['min']:,} - {stats['max']:,}")

if __name__ == "__main__":
    main()
