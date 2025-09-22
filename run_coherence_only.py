#!/usr/bin/env python3
"""
单独运行baseline文件的语义连续性分析
处理baseline_s1.md, baseline_s2.md, baseline_s3.md三个文件
输出结果到analysis_test目录
"""

import os
import sys
import json
from pathlib import Path

def run_semantic_continuity_analysis():
    """运行语义连续性分析"""
    try:
        print("开始所有baseline文件的语义连续性分析...")
        
        # 导入语义连续性分析器
        sys.path.append('/Users/haha/Story/src/analysis')
        from hred_coherence_evaluator import HREDSemanticContinuityEvaluator
        
        # 定义baseline文件
        baseline_files = {
            'baseline_s1': '/Users/haha/Story/baseline_s1.md',
            'baseline_s2': '/Users/haha/Story/baseline_s2.md', 
            'baseline_s3': '/Users/haha/Story/baseline_s3.md'
        }
        
        results = {}
        
        for baseline_name, story_file in baseline_files.items():
            print(f"\n{'='*60}")
            print(f"🔍 分析 {baseline_name}: {story_file}")
            print(f"{'='*60}")
            
            if not os.path.exists(story_file):
                print(f"❌ 文件不存在: {story_file}")
                continue
                
            # 读取故事文件
            with open(story_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析markdown为章节
            chapters = []
            current_chapter = None
            lines = content.split('\n')
            
            for line in lines:
                if line.startswith('# Chapter '):
                    if current_chapter:
                        chapters.append(current_chapter)
                    current_chapter = {
                        'title': line[2:].strip(),
                        'plot': ''
                    }
                elif current_chapter and line.strip():
                    current_chapter['plot'] += line.strip() + ' '
            
            if current_chapter:
                chapters.append(current_chapter)
            
            # 清理plot字段
            for chapter in chapters:
                chapter['plot'] = chapter['plot'].strip()
            
            print(f"解析出 {len(chapters)} 个章节")
            
            # 创建语义连续性分析器（每次重新创建以确保清洁状态）
            print("创建语义连续性分析器...")
            evaluator = HREDSemanticContinuityEvaluator()
            
            # 分析
            print("开始分析...")
            result = evaluator.evaluate_story_semantic_continuity(chapters)
            
            # 创建输出目录
            output_dir = f"/Users/haha/Story/data/analysis_test/{baseline_name}_analysis"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 保存结果
            output_file = os.path.join(output_dir, 'hred_semantic_continuity_analysis.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            results[baseline_name] = result
            
            print(f"✅ {baseline_name} 分析完成！")
            print(f"📁 结果保存至: {output_file}")
            
            # 打印关键指标
            continuity_eval = result.get('HRED_semantic_continuity_evaluation', {})
            if 'average_semantic_continuity' in continuity_eval:
                print(f"📊 平均语义连续性: {continuity_eval['average_semantic_continuity']:.4f}")
            if 'total_sentences' in continuity_eval:
                print(f"📝 分析句子数: {continuity_eval['total_sentences']}")
            
            print("⚠️  注意: 此指标仅测量相邻句子语义相似度，不代表完整故事连贯性")
        
        print(f"\n{'='*60}")
        print("🎉 所有baseline文件分析完成！")
        print(f"{'='*60}")
        print("📊 结果汇总:")
        for name, result in results.items():
            continuity_eval = result.get('HRED_semantic_continuity_evaluation', {})
            avg_continuity = continuity_eval.get('average_semantic_continuity', 'N/A')
            sentence_count = continuity_eval.get('total_sentences', 'N/A')
            
            if isinstance(avg_continuity, (int, float)):
                avg_str = f"{avg_continuity:.4f}"
            else:
                avg_str = str(avg_continuity)
            
            print(f"  {name}: 语义连续性={avg_str}, 句子数={sentence_count}")
        
        return results
        
    except Exception as e:
        print(f"语义连续性分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*60)
    print("单独运行baseline语义连续性分析")
    print("="*60)
    
    results = run_semantic_continuity_analysis()
    
    if results:
        print("\n✅ 语义连续性分析成功完成！")
        return True
    else:
        print("\n❌ 语义连续性分析失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)