"""
批量情感弧线分析脚本
遍历regression_test文件夹中的所有实验结果，运行emotional_arc_analyzer.py
将结果汇总到CSV表格中
"""

import os
import json
import pandas as pd
import re
from datetime import datetime
import sys

# 添加路径以便导入分析模块
sys.path.append('.')
from src.analysis.emotional_arc_analyzer import analyze_story_dual_method

def parse_folder_name(folder_name):
    """
    解析文件夹名称，提取实验参数
    例：thelittleredridinghood_sciencefictionrewrite_linear_T0.7_s2
    """
    parts = folder_name.split('_')
    
    # 查找模式标识
    mode_part = None
    temp_part = None
    seed_part = None
    
    for part in parts:
        if part in ['linear', 'nonlinear']:
            mode_part = part
        elif part.startswith('T') and '.' in part:
            temp_part = part
        elif part.startswith('s') and part[1:].isdigit():
            seed_part = part
    
    # 构建结果
    result = {
        'folder_name': folder_name,
        'topic': 'Little Red Riding Hood',  # 从文件夹名推断
        'style': 'Science Fiction Rewrite',  # 从文件夹名推断
        'mode': mode_part if mode_part else 'unknown',
        'temperature': float(temp_part[1:]) if temp_part else 0.0,
        'seed': int(seed_part[1:]) if seed_part else 0
    }
    
    return result

def run_batch_analysis(base_dir="/Users/haha/Story/data/output/regression_test"):
    """
    批量运行情感弧线分析
    """
    print("🚀 开始批量情感弧线分析...")
    print(f"扫描目录: {base_dir}")
    
    # 扫描所有文件夹
    if not os.path.exists(base_dir):
        print(f"❌ 目录不存在: {base_dir}")
        return None
    
    folders = [f for f in os.listdir(base_dir) 
              if os.path.isdir(os.path.join(base_dir, f)) and not f.startswith('.')]
    
    print(f"📁 发现 {len(folders)} 个实验文件夹")
    
    # 存储所有结果
    all_results = []
    success_count = 0
    failed_files = []
    
    # 遍历每个文件夹
    for i, folder in enumerate(folders, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(folders)}] 处理文件夹: {folder}")
        
        # 解析文件夹参数
        folder_params = parse_folder_name(folder)
        print(f"参数: {folder_params['mode']} | T{folder_params['temperature']} | s{folder_params['seed']}")
        
        # 构建MD文件路径
        md_file_path = os.path.join(base_dir, folder, "enhanced_story_dialogue_updated.md")
        
        if not os.path.exists(md_file_path):
            print(f"⚠️ MD文件不存在: {md_file_path}")
            failed_files.append({
                'folder': folder,
                'reason': 'MD文件不存在',
                'path': md_file_path
            })
            continue
        
        try:
            # 运行情感分析
            print("🔄 运行情感弧线分析...")
            result = analyze_story_dual_method(
                md_file_path,
                output_dir='output/batch_results/'
            )
            
            if 'error' in result:
                print(f"❌ 分析失败: {result['error']}")
                failed_files.append({
                    'folder': folder,
                    'reason': result['error'],
                    'path': md_file_path
                })
                continue
            
            # 提取关键指标
            primary_analysis = result['primary_analysis']
            validation_analysis = result['validation_analysis']
            correlation_analysis = result['correlation_analysis']
            
            # 构建结果记录
            result_record = {
                # 实验参数
                'folder_name': folder,
                'topic': folder_params['topic'],
                'style': folder_params['style'],
                'mode': folder_params['mode'],
                'temperature': folder_params['temperature'],
                'seed': folder_params['seed'],
                
                # 基本信息
                'total_chapters': result['metadata']['total_chapters'],
                'analysis_timestamp': result['metadata']['analysis_timestamp'],
                
                # RoBERTa分析结果
                'roberta_classification': primary_analysis['reagan_classification']['best_match'],
                'roberta_confidence': primary_analysis['reagan_classification']['confidence'],
                'roberta_category': primary_analysis['reagan_classification']['reagan_category'],
                
                # LabMT分析结果
                'labmt_classification': validation_analysis['reagan_classification']['best_match'],
                'labmt_confidence': validation_analysis['reagan_classification']['confidence'],
                'labmt_category': validation_analysis['reagan_classification']['reagan_category'],
                
                # 相关性分析
                'correlation_coefficient': correlation_analysis['pearson_correlation']['r'],
                'correlation_p_value': correlation_analysis['pearson_correlation']['p_value'],
                'correlation_significance': correlation_analysis['pearson_correlation']['significance'],
                'consistency_level': correlation_analysis['consistency_level'],
                'direction_consistency': correlation_analysis['direction_consistency'],
                
                # 分类一致性
                'classification_agreement': primary_analysis['reagan_classification']['best_match'] == validation_analysis['reagan_classification']['best_match'],
                
                # 章节得分（前7章，不够的用None填充）
                'chapter_scores_roberta': [ch['roberta_score'] for ch in result['chapter_analysis']],
                'chapter_scores_labmt': [ch['labmt_score'] for ch in result['chapter_analysis']],
                
                # 文件路径
                'source_file': md_file_path
            }
            
            # 扩展章节得分到单独列（便于统计分析）
            for j in range(max(7, len(result['chapter_analysis']))):  # 最多7章
                if j < len(result['chapter_analysis']):
                    result_record[f'ch{j+1}_roberta'] = result['chapter_analysis'][j]['roberta_score']
                    result_record[f'ch{j+1}_labmt'] = result['chapter_analysis'][j]['labmt_score']
                else:
                    result_record[f'ch{j+1}_roberta'] = None
                    result_record[f'ch{j+1}_labmt'] = None
            
            all_results.append(result_record)
            success_count += 1
            
            print(f"✅ 成功完成分析")
            print(f"   RoBERTa: {result_record['roberta_classification']} ({result_record['roberta_confidence']:.3f})")
            print(f"   LabMT: {result_record['labmt_classification']} ({result_record['labmt_confidence']:.3f})")
            print(f"   相关性: r={result_record['correlation_coefficient']:.3f} ({result_record['consistency_level']})")
            
        except Exception as e:
            print(f"❌ 分析异常: {str(e)}")
            failed_files.append({
                'folder': folder,
                'reason': f'异常: {str(e)}',
                'path': md_file_path
            })
    
    # 生成汇总报告
    print(f"\n{'='*60}")
    print("📊 批量分析完成汇总:")
    print(f"✅ 成功分析: {success_count}/{len(folders)} 个文件")
    print(f"❌ 失败文件: {len(failed_files)} 个")
    
    if failed_files:
        print("\n失败文件列表:")
        for failure in failed_files:
            print(f"  - {failure['folder']}: {failure['reason']}")
    
    if all_results:
        # 保存结果到CSV
        df = pd.DataFrame(all_results)
        
        # 确保输出目录存在
        os.makedirs('output/batch_results', exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'output/batch_results/batch_emotional_analysis_{timestamp}.csv'
        json_filename = f'output/batch_results/batch_emotional_analysis_{timestamp}.json'
        
        # 保存为CSV
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"📊 CSV结果已保存: {csv_filename}")
        
        # 保存为JSON（包含完整数据）
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'total_experiments': len(folders),
                    'successful_analyses': success_count,
                    'failed_analyses': len(failed_files),
                    'failed_files': failed_files
                },
                'results': all_results
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON结果已保存: {json_filename}")
        
        # 显示基本统计
        print(f"\n📈 快速统计:")
        print(f"温度分布: {df['temperature'].value_counts().to_dict()}")
        print(f"模式分布: {df['mode'].value_counts().to_dict()}")
        print(f"RoBERTa分类分布: {df['roberta_classification'].value_counts().to_dict()}")
        print(f"LabMT分类分布: {df['labmt_classification'].value_counts().to_dict()}")
        print(f"平均相关系数: {df['correlation_coefficient'].mean():.3f}")
        print(f"分类一致率: {df['classification_agreement'].mean():.1%}")
        
        return {
            'csv_file': csv_filename,
            'json_file': json_filename,
            'dataframe': df,
            'success_count': success_count,
            'failed_count': len(failed_files),
            'failed_files': failed_files
        }
    
    return None

if __name__ == "__main__":
    print("🎯 批量情感弧线分析工具")
    print("将分析所有regression_test实验结果")
    
    result_summary = run_batch_analysis()
    
    if result_summary:
        print(f"\n🎉 批量分析完成！")
        print(f"📊 CSV文件: {result_summary['csv_file']}")
        print(f"📄 JSON文件: {result_summary['json_file']}")
        print(f"✅ 成功: {result_summary['success_count']} 个")
        print(f"❌ 失败: {result_summary['failed_count']} 个")
    else:
        print(f"\n❌ 批量分析未产生结果")