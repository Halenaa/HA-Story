"""
批量流畅度分析脚本
遍历regression_test文件夹中的enhanced_story_dialogue_updated.md文件，计算fluency指标
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime

# 添加src路径到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from analysis.fluency_analyzer import FluencyAnalyzer

def find_story_files(base_dir: str) -> List[Dict]:
    """
    查找所有需要分析的故事文件
    
    Args:
        base_dir: regression_test文件夹路径
        
    Returns:
        文件信息列表
    """
    story_files = []
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"错误：目录不存在 {base_dir}")
        return story_files
    
    # 遍历所有子目录
    for subdir in base_path.iterdir():
        if subdir.is_dir():
            # 查找enhanced_story_dialogue_updated.md文件
            story_file = subdir / "enhanced_story_dialogue_updated.md"
            if story_file.exists():
                story_files.append({
                    'subdir_name': subdir.name,
                    'story_file_path': str(story_file),
                    'output_dir': str(subdir)
                })
    
    print(f"找到 {len(story_files)} 个故事文件")
    return story_files

def read_story_content(file_path: str) -> str:
    """
    读取故事文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return ""

def save_fluency_analysis(result: Dict, base_output_dir: str, subdir_name: str):
    """
    保存流畅度分析结果
    
    Args:
        result: 分析结果
        base_output_dir: 基础输出目录
        subdir_name: 子目录名称
    """
    try:
        # 创建对应参数配置的输出目录
        output_path = Path(base_output_dir) / subdir_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON结果
        json_file = output_path / "fluency_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"流畅度分析结果已保存: {json_file}")
        
    except Exception as e:
        print(f"保存结果失败 {subdir_name}: {e}")

def batch_analyze_fluency(input_dir: str, output_dir: str, model_name: str = "roberta-large"):
    """
    批量分析流畅度
    
    Args:
        input_dir: regression_test文件夹路径
        output_dir: regression_test_analysis文件夹路径
        model_name: 使用的模型名称
    """
    print(f"开始批量流畅度分析")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"使用模型: {model_name}")
    
    # 初始化分析器
    print("初始化流畅度分析器...")
    analyzer = FluencyAnalyzer(model_name=model_name)
    
    # 查找所有故事文件
    story_files = find_story_files(input_dir)
    
    if not story_files:
        print("没有找到需要分析的故事文件")
        return
    
    # 分析结果列表
    all_results = []
    
    # 逐个分析
    for i, file_info in enumerate(story_files, 1):
        subdir_name = file_info['subdir_name']
        story_file_path = file_info['story_file_path']
        
        print(f"\n[{i}/{len(story_files)}] 分析: {subdir_name}")
        
        # 读取故事内容
        story_content = read_story_content(story_file_path)
        if not story_content:
            print(f"跳过空文件: {subdir_name}")
            continue
        
        # 分析流畅度
        try:
            result = analyzer.analyze_fluency(story_content)
            
            # 添加文件信息
            result.update({
                'subdir_name': subdir_name,
                'story_file_path': story_file_path,
                'word_count': len(story_content.split()),
                'char_count': len(story_content)
            })
            
            # 保存单个结果
            save_fluency_analysis(result, output_dir, subdir_name)
            
            # 添加到总结果列表
            all_results.append(result)
            
        except Exception as e:
            print(f"分析失败 {subdir_name}: {e}")
            continue
    
    # 归一化分数
    if all_results:
        print(f"\n归一化分数...")
        all_results = analyzer.normalize_scores(all_results)
        
        # 保存汇总结果
        save_summary_results(all_results, output_dir)
        
        # 生成CSV报告
        generate_csv_report(all_results, output_dir)
    
    print(f"\n批量流畅度分析完成！共处理 {len(all_results)} 个文件")

def save_summary_results(results: List[Dict], output_dir: str):
    """
    保存汇总结果
    
    Args:
        results: 所有分析结果
        output_dir: 输出目录
    """
    try:
        summary_file = Path(output_dir) / "fluency_analysis_summary.json"
        
        summary_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_files': len(results),
            'results': results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        print(f"汇总结果已保存: {summary_file}")
        
    except Exception as e:
        print(f"保存汇总结果失败: {e}")

def generate_csv_report(results: List[Dict], output_dir: str):
    """
    生成CSV报告
    
    Args:
        results: 所有分析结果
        output_dir: 输出目录
    """
    try:
        # 提取关键指标
        csv_data = []
        for result in results:
            csv_data.append({
                'subdir_name': result['subdir_name'],
                'pseudo_ppl': result['pseudo_ppl'],
                'err_per_100w': result['err_per_100w'],
                'pseudo_ppl_score': result.get('pseudo_ppl_score', 0),
                'grammar_score': result.get('grammar_score', 0),
                'fluency_score': result.get('fluency_score', 0),
                'word_count': result.get('word_count', 0),
                'char_count': result.get('char_count', 0),
                'error_count': result.get('error_count', 0)
            })
        
        # 创建DataFrame
        df = pd.DataFrame(csv_data)
        
        # 保存CSV
        csv_file = Path(output_dir) / "fluency_analysis_report.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"CSV报告已保存: {csv_file}")
        
        # 打印统计信息
        print(f"\n流畅度分析统计:")
        print(f"平均Pseudo-PPL: {df['pseudo_ppl'].mean():.2f}")
        print(f"平均语法错误率: {df['err_per_100w'].mean():.2f}")
        print(f"平均流畅度分数: {df['fluency_score'].mean():.2f}")
        
    except Exception as e:
        print(f"生成CSV报告失败: {e}")

def main():
    """主函数"""
    # 设置路径
    base_dir = "/Users/haha/Story/data/output/regression_test"
    output_dir = "/Users/haha/Story/data/analysis_test/regression_test_analysis"
    
    # 检查输入目录
    if not os.path.exists(base_dir):
        print(f"错误：输入目录不存在 {base_dir}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 开始批量分析
    batch_analyze_fluency(base_dir, output_dir)

if __name__ == "__main__":
    main()