#!/usr/bin/env python3
"""
综合baseline分析器 - 为3个baseline文件生成完整的metrics数据
包括多样性、流畅性、连贯性、情感、结构等所有维度分析
"""

import os
import sys
import json
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# 导入各种分析器
sys.path.append('/Users/haha/Story')
sys.path.append('/Users/haha/Story/src')

from advanced_diversity_analyzer import AdvancedDiversityAnalyzer
from src.analysis.emotional_arc_analyzer import analyze_story_dual_method
from src.analysis.hred_coherence_evaluator import HREDSemanticContinuityEvaluator
from src.analysis.story_evaluator import parse_markdown_story, run_story_evaluation
from src.analysis.fluency_analyzer import FluencyAnalyzer

class ComprehensiveBaselineAnalyzer:
    def __init__(self):
        """初始化综合分析器"""
        self.baseline_files = {
            'baseline_s1': '/Users/haha/Story/output/baseline_s1.md',  # 科幻版
            'baseline_s2': '/Users/haha/Story/output/baseline_s2.md',  # 传统版
            'baseline_s3': '/Users/haha/Story/data/normal_baseline.md'  # 原normal_baseline
        }
        
        self.output_base_dir = '/Users/haha/Story/baseline_analysis_results'
        self.ensure_output_directories()
        
        # 初始化分析器
        self.fluency_analyzer = None
        self.hred_evaluator = None
        
    def ensure_output_directories(self):
        """确保输出目录存在"""
        os.makedirs(self.output_base_dir, exist_ok=True)
        for baseline_name in self.baseline_files.keys():
            os.makedirs(f"{self.output_base_dir}/{baseline_name}", exist_ok=True)
    
    def run_diversity_analysis(self, baseline_name, file_path):
        """运行多样性分析"""
        print(f"🔍 [{baseline_name}] 运行多样性分析...")
        
        # 创建临时目录结构
        temp_dir = Path(f"temp_baseline_{baseline_name}")
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 创建子目录（模拟参数配置）
            # 使用标准命名格式：thelittleredridinghood_baselinerewrite_linear_T1.0_s1
            sub_dir = temp_dir / f"thelittleredridinghood_baselinerewrite_linear_T1.0_s1"
            sub_dir.mkdir(exist_ok=True)
            
            # 复制文件到临时目录
            target_file = sub_dir / "enhanced_story_dialogue_updated.md"
            shutil.copy2(file_path, target_file)
            
            # 创建输出目录
            diversity_output_dir = f"diversity_results_baseline_{baseline_name}"
            
            # 初始化分析器
            analyzer = AdvancedDiversityAnalyzer(
                data_dir=str(temp_dir),
                output_dir=diversity_output_dir,
                window=1000,
                stride=500,
                bleu_sample_every=1,
                tokenizer='simple',
                p_low=5,
                p_high=95,
                alpha_min=0.4,
                alpha_max=0.8
            )
            
            # 运行分析
            individual_results, group_results = analyzer.run_analysis()
            analyzer.save_results()
            
            print(f"   ✅ 多样性分析完成，结果保存到: {diversity_output_dir}")
            return individual_results, group_results
            
        finally:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def run_fluency_analysis(self, baseline_name, file_path):
        """跳过流畅性分析（用户将使用GPU运行）"""
        print(f"⏭️  [{baseline_name}] 跳过流畅性分析（用户将使用GPU单独运行）...")
        return None
    
    def run_semantic_continuity_analysis(self, baseline_name, file_path):
        """运行语义连续性分析"""
        print(f"🔍 [{baseline_name}] 运行HRED语义连续性分析...")
        
        if self.hred_evaluator is None:
            self.hred_evaluator = HREDSemanticContinuityEvaluator(model_name='all-mpnet-base-v2')
        
        # 读取并解析文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析为章节格式
        chapters = parse_markdown_story(content)
        
        # 运行分析
        result = self.hred_evaluator.evaluate_story_semantic_continuity(chapters, include_details=True)
        
        # 保存结果
        output_file = f"{self.output_base_dir}/{baseline_name}/hred_semantic_continuity_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 提取平均语义连续性值
        avg_continuity = None
        try:
            avg_continuity = result['detailed_analysis']['basic_statistics']['average_semantic_continuity']
            print(f"   ✅ 语义连续性分析完成 - 平均语义连续性: {avg_continuity:.3f}")
        except KeyError:
            print(f"   ✅ 语义连续性分析完成 - 结构: {result.get('HRED_semantic_continuity_evaluation', {}).get('average_semantic_continuity', 'N/A')}")
        
        return result
    
    def run_emotional_analysis(self, baseline_name, file_path):
        """运行情感弧分析"""
        print(f"🔍 [{baseline_name}] 运行情感弧分析...")
        
        # 创建输出目录
        result_dir = f"{self.output_base_dir}/{baseline_name}"
        
        # 运行情感分析
        result = analyze_story_dual_method(file_path, result_dir)
        
        print(f"   ✅ 情感分析完成")
        return result
    
    def run_structure_analysis(self, baseline_name, file_path):
        """运行结构分析"""
        print(f"🔍 [{baseline_name}] 运行结构分析...")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析markdown故事
            story_data = parse_markdown_story(content)
            
            # 创建临时故事文件
            temp_story_file = f"{self.output_base_dir}/{baseline_name}/temp_story_structure.json"
            with open(temp_story_file, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)
            
            # 创建临时版本目录
            version = f"{baseline_name}_temp"
            version_dir = f"/Users/haha/Story/data/output/{version}"
            os.makedirs(version_dir, exist_ok=True)
            
            # 复制故事文件到版本目录
            shutil.copy2(temp_story_file, f"{version_dir}/story_updated.json")
            
            # 运行结构分析
            result = run_story_evaluation(version, mode="default", runs=1, 
                                        story_file="story_updated.json", model="gpt-4.1")
            
            # 清理临时文件
            if os.path.exists(temp_story_file):
                os.remove(temp_story_file)
            if os.path.exists(version_dir):
                shutil.rmtree(version_dir)
            
            # 保存结果
            output_file = f"{self.output_base_dir}/{baseline_name}/story_structure_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ 结构分析完成")
            return result
            
        except Exception as e:
            print(f"   ❌ 结构分析失败: {e}")
            return None
    
    def extract_text_features(self, file_path):
        """提取基本文本特征"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本统计
        words = content.split()
        sentences = [s.strip() for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        
        # 计算章节数
        chapter_count = len([line for line in content.split('\n') if line.strip().startswith('#')])
        
        return {
            'total_words': len(words),
            'total_sentences': len(sentences),
            'chapter_count': chapter_count,
            'char_count': len(content)
        }
    
    def analyze_single_baseline(self, baseline_name):
        """分析单个baseline文件"""
        file_path = self.baseline_files[baseline_name]
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        print(f"\n{'='*60}")
        print(f"🚀 开始分析 {baseline_name}: {file_path}")
        print(f"{'='*60}")
        
        results = {'baseline_name': baseline_name, 'source_file': file_path}
        
        try:
            # 1. 提取基本文本特征
            print("📝 提取基本文本特征...")
            text_features = self.extract_text_features(file_path)
            results['text_features'] = text_features
            print(f"   ✅ 文本特征: {text_features['total_words']} 词, {text_features['chapter_count']} 章")
            
            # 2. 多样性分析
            diversity_individual, diversity_group = self.run_diversity_analysis(baseline_name, file_path)
            results['diversity'] = {
                'individual': diversity_individual,
                'group': diversity_group
            }
            
            # 3. 流畅性分析（跳过，用户将使用GPU）
            fluency_result = self.run_fluency_analysis(baseline_name, file_path)
            if fluency_result:
                results['fluency'] = fluency_result
            
            # 4. 语义连续性分析
            continuity_result = self.run_semantic_continuity_analysis(baseline_name, file_path)
            results['semantic_continuity'] = continuity_result
            
            # 5. 情感分析
            emotional_result = self.run_emotional_analysis(baseline_name, file_path)
            results['emotion'] = emotional_result
            
            # 6. 结构分析
            structure_result = self.run_structure_analysis(baseline_name, file_path)
            results['structure'] = structure_result
            
            # 保存综合结果（转换tuple键为字符串）
            def convert_keys(obj):
                if isinstance(obj, dict):
                    return {str(k): convert_keys(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_keys(item) for item in obj]
                else:
                    return obj
            
            results_serializable = convert_keys(results)
            output_file = f"{self.output_base_dir}/{baseline_name}/comprehensive_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_serializable, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n✅ {baseline_name} 分析完成！结果保存到: {self.output_base_dir}/{baseline_name}/")
            return results
            
        except Exception as e:
            print(f"❌ {baseline_name} 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_all_analysis(self):
        """运行所有baseline的分析"""
        print("🎯 开始综合baseline分析...")
        print(f"分析文件: {list(self.baseline_files.keys())}")
        print(f"输出目录: {self.output_base_dir}")
        
        all_results = {}
        
        for baseline_name in self.baseline_files.keys():
            result = self.analyze_single_baseline(baseline_name)
            if result:
                all_results[baseline_name] = result
        
        # 保存总结果（处理tuple键）
        def convert_keys(obj):
            if isinstance(obj, dict):
                return {str(k): convert_keys(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_keys(item) for item in obj]
            else:
                return obj
        
        all_results_serializable = convert_keys(all_results)
        summary_file = f"{self.output_base_dir}/all_baselines_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_results_serializable, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n🎉 所有baseline分析完成!")
        print(f"📊 成功分析: {len(all_results)}/{len(self.baseline_files)} 个文件")
        print(f"📁 结果保存到: {self.output_base_dir}/")
        
        return all_results

def main():
    """主函数"""
    analyzer = ComprehensiveBaselineAnalyzer()
    results = analyzer.run_all_analysis()
    return results

if __name__ == "__main__":
    main()
