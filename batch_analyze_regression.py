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
            # 读取markdown文件并解析
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析为章节格式
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
            version = f"{folder_name}_temp"
            version_dir = os.path.join(result_dir, version)
            os.makedirs(version_dir, exist_ok=True)
            
            # 将解析的章节保存为JSON文件
            story_data = []
            for chapter in chapters:
                story_data.append({
                    'chapter_id': chapter['chapter_id'],
                    'plot': chapter['plot']
                })
            
            with open(os.path.join(version_dir, 'story_updated.json'), 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            # 修改常量中的output_dir
            constant.output_dir = result_dir
            
            # 运行分析
            story_result = run_story_evaluation(version, mode='default', story_file='story_updated.json')
            
            if story_result:
                results['story_structure'] = story_result
                # 复制结果到主目录
                with open(os.path.join(result_dir, 'story_structure_analysis.json'), 'w', encoding='utf-8') as f:
                    json.dump(story_result, f, ensure_ascii=False, indent=2)
                print("✅ 故事结构分析完成")
            else:
                print("❌ 故事结构分析失败")
                results['story_structure'] = {"error": "Analysis failed"}
                
        except Exception as e:
            print(f"❌ 故事结构分析失败: {e}")
            results['story_structure'] = {"error": str(e)}
        
        # 4. 保存综合分析结果
        comprehensive_result = {
            "folder_name": folder_name,
            "file_path": md_file_path,
            "analysis_timestamp": None,
            "emotional_arc_analysis": results.get('emotional_arc', {}),
            "hred_coherence_analysis": results.get('hred_coherence', {}),
            "story_structure_analysis": results.get('story_structure', {})
        }
        
        with open(os.path.join(result_dir, 'comprehensive_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(comprehensive_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ {folder_name} 分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ {folder_name} 分析过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    # 设置路径
    regression_test_dir = "/Users/haha/Story/data/output/regression_test"
    output_dir = "/Users/haha/Story/data/regression_test_analysis"
    
    print("开始批量分析regression_test文件夹...")
    print(f"源目录: {regression_test_dir}")
    print(f"输出目录: {output_dir}")
    
    # 遍历regression_test文件夹
    success_count = 0
    total_count = 0
    
    for item in os.listdir(regression_test_dir):
        item_path = os.path.join(regression_test_dir, item)
        
        # 跳过非目录项
        if not os.path.isdir(item_path):
            continue
        
        # 查找enhanced_story_dialogue_updated.md文件
        md_file = os.path.join(item_path, "enhanced_story_dialogue_updated.md")
        
        if os.path.exists(md_file):
            total_count += 1
            print(f"\n找到文件: {item}")
            
            # 分析该文件
            if analyze_single_file(md_file, output_dir, item):
                success_count += 1
        else:
            print(f"⚠️  {item} 中未找到enhanced_story_dialogue_updated.md文件")
    
    # 打印总结
    print(f"\n{'='*80}")
    print("批量分析完成！")
    print(f"总文件数: {total_count}")
    print(f"成功分析: {success_count}")
    print(f"失败数量: {total_count - success_count}")
    print(f"结果保存在: {output_dir}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
