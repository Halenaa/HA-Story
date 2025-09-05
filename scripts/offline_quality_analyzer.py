#!/usr/bin/env python3
"""
离线质量-效率分析工具

专门用于分析已生成的性能报告JSON文件，进行详细的质量-效率权衡分析。
支持单个文件分析和批量对比分析。

使用方式:
1. 单个文件分析: python offline_quality_analyzer.py single report.json
2. 批量对比分析: python offline_quality_analyzer.py batch data/output/
3. 参数对比分析: python offline_quality_analyzer.py compare data/output/ --metric temperature
"""

import json
import os
import argparse
import glob
from typing import Dict, List, Any, Tuple
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class OfflineQualityAnalyzer:
    """离线质量-效率分析器"""
    
    def __init__(self):
        self.reports = []
        self.analysis_results = {}
    
    def load_single_report(self, report_path: str) -> Dict:
        """加载单个性能报告"""
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            print(f"✅ 成功加载报告: {report_path}")
            return report
        except Exception as e:
            print(f"❌ 加载报告失败 {report_path}: {e}")
            return None
    
    def load_batch_reports(self, directory: str) -> List[Dict]:
        """批量加载目录下的所有性能报告"""
        reports = []
        pattern = os.path.join(directory, "**/performance_analysis_*.json")
        
        for report_path in glob.glob(pattern, recursive=True):
            report = self.load_single_report(report_path)
            if report:
                # 添加文件路径信息
                report['_file_path'] = report_path
                report['_file_name'] = os.path.basename(report_path)
                reports.append(report)
        
        print(f"📊 共加载了 {len(reports)} 个报告文件")
        return reports
    
    def analyze_single_report_quality(self, report: Dict) -> Dict:
        """分析单个报告的质量指标"""
        text_features = report.get('text_features', {})
        memory_data = report.get('memory_complexity_data', {})
        api_data = report.get('api_cost_breakdown', {})
        metadata = report.get('metadata', {})
        
        # 基础指标
        total_words = text_features.get('total_word_count', 0)
        total_chars = text_features.get('total_char_count', 0)
        total_time = metadata.get('total_execution_time', 0)
        total_cost = metadata.get('total_api_cost', 0)
        peak_memory = metadata.get('peak_memory_usage_mb', 0)
        total_tokens = metadata.get('total_tokens', 0)
        
        # 质量指标计算
        quality_metrics = self._calculate_quality_metrics(text_features, memory_data)
        
        # 效率指标计算
        efficiency_metrics = self._calculate_efficiency_metrics(
            total_words, total_time, total_cost, peak_memory, total_tokens
        )
        
        # 综合分析
        overall_score = (quality_metrics['overall_score'] + efficiency_metrics['overall_score']) / 2
        
        return {
            'quality_metrics': quality_metrics,
            'efficiency_metrics': efficiency_metrics,
            'overall_score': overall_score,
            'basic_stats': {
                'words': total_words,
                'time_seconds': total_time,
                'cost_usd': total_cost,
                'memory_mb': peak_memory,
                'tokens': total_tokens
            }
        }
    
    def _calculate_quality_metrics(self, text_features: Dict, memory_data: Dict) -> Dict:
        """计算质量指标 - 基于实际数据的更准确版本"""
        
        total_words = text_features.get('total_word_count', 0)
        total_chars = text_features.get('total_char_count', 0)
        sentence_count = text_features.get('sentence_count', 0)
        chapter_count = text_features.get('chapter_count', 0)
        
        scores = {}
        
        # 1. 文本丰富度 (0-25分)
        if total_words > 0 and sentence_count > 0:
            avg_sentence_length = total_words / sentence_count
            # 中文理想句子长度 8-20字
            richness_score = 25
            if avg_sentence_length < 5:
                richness_score = avg_sentence_length / 5 * 15
            elif avg_sentence_length > 25:
                richness_score = max(15, 25 - (avg_sentence_length - 25) * 0.5)
                
            # 字符密度评分
            char_density = total_chars / total_words if total_words > 0 else 0
            density_score = min(char_density / 2.5 * 10, 10)  # 中文平均2.5字/词
            
            scores['text_richness'] = min(richness_score + density_score, 25)
        else:
            scores['text_richness'] = 0
        
        # 2. 故事结构完整性 (0-25分)
        if chapter_count > 0 and total_words > 0:
            avg_chapter_length = total_words / chapter_count
            
            # 理想章节长度 300-800字
            if 300 <= avg_chapter_length <= 800:
                length_score = 15
            elif avg_chapter_length < 300:
                length_score = avg_chapter_length / 300 * 15
            else:
                length_score = max(10, 15 - (avg_chapter_length - 800) / 200)
            
            # 章节数量合理性 (3-15章比较合理)
            if 3 <= chapter_count <= 15:
                count_score = 10
            elif chapter_count < 3:
                count_score = chapter_count / 3 * 10
            else:
                count_score = max(5, 10 - (chapter_count - 15) * 0.3)
            
            scores['story_structure'] = min(length_score + count_score, 25)
        else:
            scores['story_structure'] = 0
        
        # 3. 内容一致性 (0-25分) - 基于角色和剧情复杂度
        character_features = memory_data.get('story_features', {})
        char_count = character_features.get('character_count', 0)
        char_complexity = character_features.get('character_complexity_score', 0)
        
        if char_count > 0:
            # 角色数量合理性
            if 2 <= char_count <= 8:
                char_balance_score = 15
            elif char_count == 1:
                char_balance_score = 10
            else:
                char_balance_score = max(8, 15 - abs(char_count - 5))
            
            # 角色复杂度
            complexity_score = min(char_complexity / 50, 10)  # 标准化
            
            scores['content_consistency'] = min(char_balance_score + complexity_score, 25)
        else:
            scores['content_consistency'] = 0
        
        # 4. 文本连贯性 (0-25分) - 基于句子和段落结构
        if sentence_count > 0 and chapter_count > 0:
            sentences_per_chapter = sentence_count / chapter_count
            
            # 理想范围：每章10-40句
            if 10 <= sentences_per_chapter <= 40:
                coherence_score = 25
            elif sentences_per_chapter < 10:
                coherence_score = sentences_per_chapter / 10 * 25
            else:
                coherence_score = max(15, 25 - (sentences_per_chapter - 40) * 0.2)
            
            scores['text_coherence'] = coherence_score
        else:
            scores['text_coherence'] = 0
        
        total_score = sum(scores.values())
        
        return {
            'overall_score': total_score,
            'breakdown': scores,
            'max_possible': 100,
            'percentage': total_score
        }
    
    def _calculate_efficiency_metrics(self, total_words: int, total_time: float, 
                                    total_cost: float, peak_memory: float, total_tokens: int) -> Dict:
        """计算效率指标"""
        
        scores = {}
        
        # 1. 时间效率 (0-25分)
        if total_time > 0 and total_words > 0:
            words_per_second = total_words / total_time
            # 评分标准：中文3字/秒为满分，1字/秒为及格
            if words_per_second >= 3:
                scores['time_efficiency'] = 25
            elif words_per_second >= 1:
                scores['time_efficiency'] = 15 + (words_per_second - 1) / 2 * 10
            else:
                scores['time_efficiency'] = words_per_second / 1 * 15
        else:
            scores['time_efficiency'] = 0
        
        # 2. 成本效率 (0-25分)
        if total_cost > 0 and total_words > 0:
            cost_per_word = total_cost / total_words
            # 评分标准：每字$0.0005为满分，$0.002为及格
            if cost_per_word <= 0.0005:
                scores['cost_efficiency'] = 25
            elif cost_per_word <= 0.002:
                scores['cost_efficiency'] = 15 + (0.002 - cost_per_word) / 0.0015 * 10
            else:
                scores['cost_efficiency'] = max(5, 15 - (cost_per_word - 0.002) * 5000)
        else:
            scores['cost_efficiency'] = 25  # 无成本给满分
        
        # 3. 内存效率 (0-25分)
        if peak_memory > 0 and total_words > 0:
            memory_per_word = peak_memory / total_words
            # 评分标准：每字0.005MB为满分，0.02MB为及格
            if memory_per_word <= 0.005:
                scores['memory_efficiency'] = 25
            elif memory_per_word <= 0.02:
                scores['memory_efficiency'] = 15 + (0.02 - memory_per_word) / 0.015 * 10
            else:
                scores['memory_efficiency'] = max(5, 15 - (memory_per_word - 0.02) * 500)
        else:
            scores['memory_efficiency'] = 25  # 无数据给满分
        
        # 4. Token效率 (0-25分)
        if total_tokens > 0 and total_words > 0:
            tokens_per_word = total_tokens / total_words
            # 评分标准：中文每字1.5token为满分，3token为及格
            if tokens_per_word <= 1.5:
                scores['token_efficiency'] = 25
            elif tokens_per_word <= 3:
                scores['token_efficiency'] = 15 + (3 - tokens_per_word) / 1.5 * 10
            else:
                scores['token_efficiency'] = max(5, 15 - (tokens_per_word - 3) * 5)
        else:
            scores['token_efficiency'] = 25  # 无数据给满分
        
        total_score = sum(scores.values())
        
        return {
            'overall_score': total_score,
            'breakdown': scores,
            'max_possible': 100,
            'percentage': total_score
        }
    
    def generate_single_report_analysis(self, report_path: str, output_dir: str = None):
        """生成单个报告的详细分析"""
        report = self.load_single_report(report_path)
        if not report:
            return
        
        analysis = self.analyze_single_report_quality(report)
        
        # 生成分析报告
        if output_dir is None:
            output_dir = os.path.dirname(report_path)
        
        base_name = os.path.splitext(os.path.basename(report_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_quality_analysis.json")
        
        detailed_analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'source_report': report_path,
            'analysis_results': analysis,
            'recommendations': self._generate_recommendations(analysis)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\n📋 质量分析报告:")
        print(f"   综合得分: {analysis['overall_score']:.1f}/100")
        print(f"   质量得分: {analysis['quality_metrics']['percentage']:.1f}%")
        print(f"   效率得分: {analysis['efficiency_metrics']['percentage']:.1f}%")
        print(f"   详细报告: {output_path}")
        
        return analysis
    
    def generate_batch_comparison(self, directory: str, output_dir: str = None):
        """生成批量对比分析"""
        reports = self.load_batch_reports(directory)
        if not reports:
            print("❌ 没有找到可分析的报告文件")
            return
        
        analyses = []
        for report in reports:
            analysis = self.analyze_single_report_quality(report)
            analysis['task_name'] = report.get('metadata', {}).get('task_name', 'unknown')
            analysis['file_name'] = report['_file_name']
            analyses.append(analysis)
        
        # 创建对比表格
        comparison_data = []
        for analysis in analyses:
            comparison_data.append({
                'Task': analysis['task_name'],
                'File': analysis['file_name'],
                'Overall Score': analysis['overall_score'],
                'Quality Score': analysis['quality_metrics']['percentage'],
                'Efficiency Score': analysis['efficiency_metrics']['percentage'],
                'Words': analysis['basic_stats']['words'],
                'Time (s)': analysis['basic_stats']['time_seconds'],
                'Cost ($)': analysis['basic_stats']['cost_usd'],
                'Memory (MB)': analysis['basic_stats']['memory_mb']
            })
        
        df = pd.DataFrame(comparison_data)
        
        if output_dir is None:
            output_dir = directory
        
        # 保存对比表格
        csv_path = os.path.join(output_dir, f"quality_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 生成可视化图表
        self._create_comparison_charts(df, output_dir)
        
        print(f"\n📊 批量对比分析完成:")
        print(f"   分析了 {len(analyses)} 个报告")
        print(f"   对比表格: {csv_path}")
        print(f"   可视化图表已保存到: {output_dir}")
        
        return analyses
    
    def _create_comparison_charts(self, df: pd.DataFrame, output_dir: str):
        """创建对比分析图表"""
        
        # 1. 综合得分对比
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.bar(range(len(df)), df['Overall Score'])
        plt.title('综合得分对比')
        plt.xlabel('实验')
        plt.ylabel('得分')
        plt.xticks(range(len(df)), df['Task'], rotation=45, ha='right')
        
        # 2. 质量vs效率散点图
        plt.subplot(1, 2, 2)
        plt.scatter(df['Quality Score'], df['Efficiency Score'], s=100, alpha=0.7)
        plt.xlabel('质量得分')
        plt.ylabel('效率得分')
        plt.title('质量-效率权衡分析')
        
        for i, row in df.iterrows():
            plt.annotate(row['Task'][:10], (row['Quality Score'], row['Efficiency Score']), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'quality_efficiency_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 成本-效果分析
        plt.figure(figsize=(10, 6))
        plt.scatter(df['Cost ($)'], df['Words'], s=df['Overall Score']*2, alpha=0.6)
        plt.xlabel('成本 ($)')
        plt.ylabel('生成字数')
        plt.title('成本-效果分析 (气泡大小代表综合得分)')
        
        for i, row in df.iterrows():
            plt.annotate(row['Task'][:8], (row['Cost ($)'], row['Words']), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.savefig(os.path.join(output_dir, 'cost_effectiveness_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """基于分析结果生成优化建议"""
        recommendations = []
        
        quality_score = analysis['quality_metrics']['percentage']
        efficiency_score = analysis['efficiency_metrics']['percentage']
        quality_breakdown = analysis['quality_metrics']['breakdown']
        efficiency_breakdown = analysis['efficiency_metrics']['breakdown']
        
        # 质量建议
        if quality_score < 60:
            if quality_breakdown.get('text_richness', 0) < 15:
                recommendations.append("🎨 文本丰富度偏低，建议调整prompt让模型生成更多样化的表达")
            
            if quality_breakdown.get('story_structure', 0) < 15:
                recommendations.append("📚 故事结构需要优化，考虑调整章节分布或每章目标长度")
            
            if quality_breakdown.get('content_consistency', 0) < 15:
                recommendations.append("👥 角色设定可能过于简单或复杂，建议调整角色数量和背景深度")
        
        # 效率建议
        if efficiency_score < 60:
            if efficiency_breakdown.get('time_efficiency', 0) < 15:
                recommendations.append("⚡ 生成速度较慢，考虑使用更快的模型或优化并发调用")
            
            if efficiency_breakdown.get('cost_efficiency', 0) < 15:
                recommendations.append("💰 成本偏高，建议尝试更经济的模型或优化prompt长度")
            
            if efficiency_breakdown.get('memory_efficiency', 0) < 15:
                recommendations.append("💾 内存使用过多，考虑分批处理或优化数据结构")
        
        # 权衡建议
        if quality_score > 80 and efficiency_score < 40:
            recommendations.append("⚖️ 质量很高但效率偏低，可以适当简化以提高效率")
        elif efficiency_score > 80 and quality_score < 40:
            recommendations.append("⚖️ 效率很高但质量偏低，建议增加一些质量控制措施")
        elif quality_score > 70 and efficiency_score > 70:
            recommendations.append("🎉 质量和效率都很好，系统运行良好！")
        
        if not recommendations:
            recommendations.append("✨ 系统表现均衡，建议根据具体需求微调参数")
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description="离线质量-效率分析工具")
    parser.add_argument("mode", choices=["single", "batch"], 
                       help="分析模式：single=单个文件分析，batch=批量对比分析")
    parser.add_argument("path", help="报告文件路径或目录路径")
    parser.add_argument("--output", "-o", help="输出目录")
    
    args = parser.parse_args()
    
    analyzer = OfflineQualityAnalyzer()
    
    if args.mode == "single":
        if not os.path.isfile(args.path):
            print(f"❌ 文件不存在: {args.path}")
            return
        
        analyzer.generate_single_report_analysis(args.path, args.output)
    
    elif args.mode == "batch":
        if not os.path.isdir(args.path):
            print(f"❌ 目录不存在: {args.path}")
            return
        
        analyzer.generate_batch_comparison(args.path, args.output or args.path)

if __name__ == "__main__":
    main()
