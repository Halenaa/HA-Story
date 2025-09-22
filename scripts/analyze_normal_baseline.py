#!/usr/bin/env python3
"""
对normal_baseline.md进行完整分析
"""

import os
import sys
import json
from pathlib import Path

def ensure_directory(directory_path):
    """确保目录存在"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    return directory_path

def run_emotional_analysis(story_file, output_dir):
    """运行情感分析"""
    print("开始情感分析...")
    
    try:
        # 导入情感分析器
        sys.path.append('/Users/haha/Story/src/analysis')
        from emotional_arc_analyzer import analyze_story_dual_method
        
        # 运行分析
        result = analyze_story_dual_method(story_file, output_dir)
        
        # 保存结果
        output_file = os.path.join(output_dir, 'emotional_arc_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"情感分析完成: {output_file}")
        return True
        
    except Exception as e:
        print(f"情感分析失败: {e}")
        return False

def run_coherence_analysis(story_file, output_dir):
    """运行连贯性分析"""
    print("开始连贯性分析...")
    
    try:
        # 导入连贯性分析器
        sys.path.append('/Users/haha/Story/src/analysis')
        from hred_coherence_evaluator import evaluate_story_coherence_from_file
        
        # 由于函数需要version参数，我们需要先转换markdown为json格式
        # 创建临时的story数据
        with open(story_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单的markdown解析 - 提取章节
        chapters = []
        current_chapter = None
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('# Chapter '):
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    'title': line[2:],
                    'plot': ''
                }
            elif current_chapter and line.strip():
                current_chapter['plot'] += line + ' '
        
        if current_chapter:
            chapters.append(current_chapter)
        
        # 创建临时story数据
        story_data = {
            'chapters': chapters,
            'story_title': 'Normal Baseline Story'
        }
        
        # 保存临时文件
        temp_story_file = os.path.join(output_dir, 'temp_story.json')
        with open(temp_story_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        # 运行连贯性分析器中的类
        from hred_coherence_evaluator import HREDCoherenceEvaluator
        evaluator = HREDCoherenceEvaluator()
        result = evaluator.evaluate_story_coherence(story_data)
        
        # 清理临时文件
        if os.path.exists(temp_story_file):
            os.remove(temp_story_file)
        
        # 保存结果
        output_file = os.path.join(output_dir, 'hred_coherence_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"连贯性分析完成: {output_file}")
        return True
        
    except Exception as e:
        print(f"连贯性分析失败: {e}")
        return False

def run_structure_analysis(story_file, output_dir):
    """运行结构分析"""
    print("开始结构分析...")
    
    try:
        # 导入结构分析器
        sys.path.append('/Users/haha/Story/src/analysis')
        from story_evaluator import run_story_evaluation, parse_markdown_story
        
        # 解析markdown故事
        with open(story_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用story_evaluator中的解析函数
        story_data = parse_markdown_story(content)
        
        # 创建临时故事文件
        temp_story_file = os.path.join(output_dir, 'temp_story_structure.json')
        with open(temp_story_file, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        
        # 运行结构分析 (使用 "normal_baseline" 作为version)
        result = run_story_evaluation("normal_baseline", mode="default", runs=1, 
                                    story_file=temp_story_file, model="gpt-4.1")
        
        # 清理临时文件
        if os.path.exists(temp_story_file):
            os.remove(temp_story_file)
        
        # 保存结果
        output_file = os.path.join(output_dir, 'story_structure_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"结构分析完成: {output_file}")
        return True
        
    except Exception as e:
        print(f"结构分析失败: {e}")
        return False

def main():
    """主函数"""
    print("="*60)
    print("开始对normal_baseline.md进行完整分析")
    print("="*60)
    
    # 设置路径
    story_file = "/Users/haha/Story/data/normal_baseline.md"
    output_dir = "/Users/haha/Story/data/analysis_test/normal_baseline_analysis"
    
    # 检查故事文件是否存在
    if not os.path.exists(story_file):
        print(f"错误: 故事文件不存在: {story_file}")
        return False
    
    # 确保输出目录存在
    ensure_directory(output_dir)
    
    print(f"故事文件: {story_file}")
    print(f"输出目录: {output_dir}")
    print()
    
    # 运行各项分析
    results = {}
    
    # 1. 情感分析
    results['emotional'] = run_emotional_analysis(story_file, output_dir)
    
    # 2. 连贯性分析
    results['coherence'] = run_coherence_analysis(story_file, output_dir)
    
    # 3. 结构分析
    results['structure'] = run_structure_analysis(story_file, output_dir)
    
    # 总结结果
    print("\n" + "="*60)
    print("分析结果总结:")
    print("="*60)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for analysis_type, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {analysis_type:12} {status}")
    
    print(f"\n总计: {success_count}/{total_count} 项分析完成")
    
    if success_count == total_count:
        print("\n🎉 所有分析完成！现在可以运行 extract_core_metrics_final.py")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 项分析失败，请检查错误信息")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
