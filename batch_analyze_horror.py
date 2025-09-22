#!/usr/bin/env python3
import os
import sys
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.append('/Users/haha/Story/src/analysis')

from emotional_arc_analyzer import analyze_story_dual_method
from hred_coherence_evaluator import HREDCoherenceEvaluator
from story_evaluator import parse_markdown_story, run_story_evaluation
import src.constant as constant

def analyze_single_file(md_file_path, output_dir, folder_name):
    """分析单个markdown文件"""
    print(f"\n{'='*80}")
    print(f"分析文件: {folder_name}")
    print(f"路径: {md_file_path}")
    print(f"{'='*80}")
    
    # 创建该文件夹的结果目录
    result_dir = os.path.join(output_dir, folder_name)
    os.makedirs(result_dir, exist_ok=True)
    
    results = {}
    
    try:
        # 1. 情感弧分析
        print("\n1. 开始情感弧分析...")
        try:
            emotional_result = analyze_story_dual_method(md_file_path, result_dir)
            results['emotional_arc'] = emotional_result
            print("✅ 情感弧分析完成")
        except Exception as e:
            print(f"❌ 情感弧分析失败: {e}")
            results['emotional_arc'] = {"error": str(e)}
        
        # 2. HRED连贯性分析
        print("\n2. 开始HRED连贯性分析...")
        try:
            # 读取并解析markdown文件
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            chapters = parse_markdown_story(content)
            
            # 创建分析器
            evaluator = HREDCoherenceEvaluator(model_name='all-mpnet-base-v2')
            
            # 运行分析
            hred_result = evaluator.evaluate_story_coherence(chapters, include_details=True)
            results['hred_coherence'] = hred_result
            
            # 保存结果
            with open(os.path.join(result_dir, 'hred_coherence_analysis.json'), 'w', encoding='utf-8') as f:
                json.dump(hred_result, f, ensure_ascii=False, indent=2)
            
            print("✅ HRED连贯性分析完成")
        except Exception as e:
            print(f"❌ HRED连贯性分析失败: {e}")
            results['hred_coherence'] = {"error": str(e)}
        
        # 3. 故事结构分析
        print("\n3. 开始故事结构分析...")
        try:
            # 创建临时版本目录
            temp_version = f"{folder_name}_temp"
            temp_dir = os.path.join(output_dir, temp_version)
            os.makedirs(temp_dir, exist_ok=True)
            
            # 保存JSON格式的故事数据
            story_json_path = os.path.join(temp_dir, 'story_updated.json')
            with open(story_json_path, 'w', encoding='utf-8') as f:
                json.dump(chapters, f, ensure_ascii=False, indent=2)
            
            # 修改常量中的output_dir
            constant.output_dir = output_dir
            
            # 运行分析
            structure_result = run_story_evaluation(temp_version, mode='default', story_file='story_updated.json')
            
            if structure_result:
                results['story_structure'] = structure_result
                
                # 保存结果
                with open(os.path.join(result_dir, 'story_structure_analysis.json'), 'w', encoding='utf-8') as f:
                    json.dump(structure_result, f, ensure_ascii=False, indent=2)
                
                print("✅ 故事结构分析完成")
            else:
                print("❌ 故事结构分析失败")
                results['story_structure'] = {"error": "Analysis failed"}
            
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            print(f"❌ 故事结构分析失败: {e}")
            results['story_structure'] = {"error": str(e)}
        
        # 保存综合结果
        with open(os.path.join(result_dir, 'comprehensive_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ {folder_name} 分析完成，结果保存到: {result_dir}")
        return True
        
    except Exception as e:
        print(f"❌ {folder_name} 分析过程中出现错误: {e}")
        results['error'] = str(e)
        
        # 保存错误结果
        with open(os.path.join(result_dir, 'error_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return False

def main():
    """主函数"""
    horror_test_dir = "/Users/haha/Story/data/output/horror_test"
    output_dir = "/Users/haha/Story/data/horror_test_analysis"
    
    print("开始批量分析horror_test文件夹...")
    print(f"源目录: {horror_test_dir}")
    print(f"结果目录: {output_dir}")
    
    # 查找所有包含enhanced_story_dialogue_updated.md的文件夹
    md_files = []
    for root, dirs, files in os.walk(horror_test_dir):
        if 'enhanced_story_dialogue_updated.md' in files:
            md_path = os.path.join(root, 'enhanced_story_dialogue_updated.md')
            folder_name = os.path.basename(root)
            md_files.append((md_path, folder_name))
    
    print(f"\n找到 {len(md_files)} 个enhanced_story_dialogue_updated.md文件")
    
    # 分析每个文件
    success_count = 0
    failed_count = 0
    
    for i, (md_path, folder_name) in enumerate(md_files, 1):
        print(f"\n进度: {i}/{len(md_files)}")
        
        if analyze_single_file(md_path, output_dir, folder_name):
            success_count += 1
        else:
            failed_count += 1
    
    # 生成总结报告
    summary = {
        "total_files": len(md_files),
        "successful_analyses": success_count,
        "failed_analyses": failed_count,
        "success_rate": success_count / len(md_files) if md_files else 0,
        "analyzed_folders": [folder for _, folder in md_files]
    }
    
    with open(os.path.join(output_dir, 'analysis_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("批量分析完成!")
    print(f"总文件数: {len(md_files)}")
    print(f"成功分析: {success_count}")
    print(f"失败分析: {failed_count}")
    print(f"成功率: {summary['success_rate']:.1%}")
    print(f"结果保存在: {output_dir}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
