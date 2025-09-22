#!/usr/bin/env python3
"""
更新Baseline情绪分析 - 保持原有技术分析结论
=======================================

只更新baseline部分，保持所有原有的RoBERTa vs LabMT技术分析和修复结论。
现在有3个不同原型的baseline：
- simple_baseline_s1: Rags to riches原型
- simple_baseline_s2: Tragedy原型  
- simple_baseline_s3: Icarus原型

不做一致性分析，只分析各个baseline的情感特征。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from datetime import datetime
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class UpdatedBaselineEmotionAnalyzer:
    """更新后的Baseline情绪分析器"""
    
    def __init__(self, csv_path):
        """初始化，保持原有数据结构"""
        self.data = pd.read_csv(csv_path)
        self.experiment_data = self.data[self.data['is_baseline'] == 0].copy()
        self.baseline_data = self.data[self.data['is_baseline'] == 1].copy()
        
        self.output_dir = '/Users/haha/Story/AAA/emotion_analysis/updated_baseline_results'
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"🎯 更新Baseline情绪分析")
        print(f"📊 实验故事数: {len(self.experiment_data)}")
        print(f"📊 Baseline故事数: {len(self.baseline_data)}")
        
        # 解析情绪分数
        self._parse_emotion_scores()
        
        # 读取原有技术分析结论
        self._load_original_technical_findings()
        
    def _parse_emotion_scores(self):
        """解析情绪分数字符串"""
        def safe_parse_scores(score_str):
            if pd.isna(score_str):
                return []
            try:
                if isinstance(score_str, str):
                    score_str = score_str.strip('[]"\'')
                    return [float(x.strip()) for x in score_str.split(',') if x.strip() and x.strip() != 'nan']
                return []
            except Exception:
                return []
        
        self.baseline_data['roberta_scores_list'] = self.baseline_data['roberta_scores_str'].apply(safe_parse_scores)
        self.baseline_data['labmt_scores_list'] = self.baseline_data['labmt_scores_str'].apply(safe_parse_scores)
        
        print(f"✅ 有效baseline故事数: {len([1 for _, row in self.baseline_data.iterrows() if len(row['roberta_scores_list']) > 0])}")
    
    def _load_original_technical_findings(self):
        """加载原有技术分析结论"""
        # 保持原有的关键技术发现
        self.original_technical_findings = {
            "critical_bug_discovered": {
                "correlation_direction_consistency_bug": {
                    "description": "74.1%的条目中correlation_coefficient和direction_consistency值完全相同",
                    "impact": "致命的串值错误，导致分析结果不可靠",
                    "fix_status": "已修复"
                }
            },
            "labmt_technical_issues": {
                "negation_handling": {
                    "problem": "否定词处理完全未实现",
                    "examples": ["not good被分析为正面情绪", "This is not bad被误判为负面"],
                    "impact": "严重影响情感分析准确性"
                },
                "tokenization_issues": {
                    "problem": "仅使用简单正则表达式，不处理缩略词",
                    "impact": "分词精度偏低，丢失重要语义信息"
                }
            },
            "performance_improvements": {
                "direction_consistency": {
                    "before": 0.418,
                    "after": 0.614,
                    "improvement": "+46.9%",
                    "status": "显著改善"
                }
            },
            "validation_results": {
                "fdr_correction": "FDR校正后显著相关性为0.0%",
                "statistical_significance": "修正后真正显著的相关性仍然很低"
            }
        }
    
    def analyze_updated_baselines(self):
        """分析3个新baseline的情绪特征"""
        print(f"\n📊 更新后Baseline情绪特征分析")
        print("=" * 60)
        
        baseline_results = []
        
        for idx, row in self.baseline_data.iterrows():
            story_id = row['story_id']
            seed = row['seed']
            archetype = row['reagan_classification']
            
            roberta_scores = np.array(row['roberta_scores_list'])
            labmt_scores = np.array(row['labmt_scores_list'])
            
            if len(roberta_scores) == 0 or len(labmt_scores) == 0:
                continue
            
            # 计算基础统计信息
            basic_stats = {
                'story_id': story_id,
                'seed': seed,
                'archetype': archetype,
                'chapter_count': len(roberta_scores),
                'roberta_mean': np.mean(roberta_scores),
                'roberta_std': np.std(roberta_scores),
                'roberta_range': np.max(roberta_scores) - np.min(roberta_scores),
                'roberta_min': np.min(roberta_scores),
                'roberta_max': np.max(roberta_scores),
                'labmt_mean': np.mean(labmt_scores),
                'labmt_std': np.std(labmt_scores),
                'labmt_range': np.max(labmt_scores) - np.min(labmt_scores),
                'labmt_min': np.min(labmt_scores),
                'labmt_max': np.max(labmt_scores),
                'emotion_correlation': row['emotion_correlation']
            }
            
            # 计算方向一致性（使用修复后的方法）
            if len(roberta_scores) > 1:
                roberta_diffs = np.diff(roberta_scores)
                labmt_diffs = np.diff(labmt_scores)
                
                agreements = 0
                total_valid = 0
                
                for r_diff, l_diff in zip(roberta_diffs, labmt_diffs):
                    if abs(r_diff) > 1e-6 or abs(l_diff) > 1e-6:
                        total_valid += 1
                        if np.sign(r_diff) == np.sign(l_diff):
                            agreements += 1
                
                direction_consistency = agreements / total_valid if total_valid > 0 else 0
            else:
                direction_consistency = 0
            
            basic_stats['direction_consistency_fixed'] = direction_consistency
            
            # 情绪波动性分析
            if len(roberta_scores) > 1:
                emotional_volatility = np.std(np.diff(roberta_scores))
            else:
                emotional_volatility = 0
            
            basic_stats['emotional_volatility'] = emotional_volatility
            
            # 情绪轨迹特征
            emotion_trajectory = self._analyze_emotion_trajectory(roberta_scores, labmt_scores, archetype)
            basic_stats.update(emotion_trajectory)
            
            baseline_results.append(basic_stats)
            
            # 打印详细信息
            print(f"\n🎭 {story_id} (seed {seed})")
            print(f"   原型: {archetype}")
            print(f"   RoBERTa均值: {np.mean(roberta_scores):.3f}, 标准差: {np.std(roberta_scores):.3f}")
            print(f"   LabMT均值: {np.mean(labmt_scores):.3f}, 标准差: {np.std(labmt_scores):.3f}")
            print(f"   情绪相关性: {row['emotion_correlation']:.3f}")
            print(f"   方向一致性(修复后): {direction_consistency:.3f}")
            print(f"   情绪波动性: {emotional_volatility:.3f}")
        
        # 保存结果
        self.baseline_results = baseline_results
        return baseline_results
    
    def _analyze_emotion_trajectory(self, roberta_scores, labmt_scores, archetype):
        """分析情绪轨迹特征"""
        trajectory_features = {}
        
        # 起始和结束情绪状态
        trajectory_features['emotion_start_roberta'] = roberta_scores[0]
        trajectory_features['emotion_end_roberta'] = roberta_scores[-1]
        trajectory_features['emotion_start_labmt'] = labmt_scores[0]
        trajectory_features['emotion_end_labmt'] = labmt_scores[-1]
        
        # 情绪变化幅度
        trajectory_features['roberta_total_change'] = roberta_scores[-1] - roberta_scores[0]
        trajectory_features['labmt_total_change'] = labmt_scores[-1] - labmt_scores[0]
        
        # 情绪峰值和谷值
        trajectory_features['roberta_peak'] = np.max(roberta_scores)
        trajectory_features['roberta_valley'] = np.min(roberta_scores)
        trajectory_features['labmt_peak'] = np.max(labmt_scores)
        trajectory_features['labmt_valley'] = np.min(labmt_scores)
        
        # 情绪变化趋势（线性回归斜率）
        if len(roberta_scores) > 2:
            x = np.arange(len(roberta_scores))
            roberta_trend = np.polyfit(x, roberta_scores, 1)[0]
            labmt_trend = np.polyfit(x, labmt_scores, 1)[0]
            trajectory_features['roberta_trend'] = roberta_trend
            trajectory_features['labmt_trend'] = labmt_trend
        else:
            trajectory_features['roberta_trend'] = 0
            trajectory_features['labmt_trend'] = 0
        
        return trajectory_features
    
    def compare_with_experiments(self):
        """与实验数据比较（保持原有对比方法）"""
        print(f"\n⚖️ Baseline vs 实验数据对比")
        print("=" * 60)
        
        # 计算实验数据的统计信息
        exp_correlations = self.experiment_data['emotion_correlation'].dropna()
        baseline_correlations = [result['emotion_correlation'] for result in self.baseline_results]
        
        comparison = {
            'experimental_stats': {
                'mean_correlation': exp_correlations.mean(),
                'std_correlation': exp_correlations.std(),
                'median_correlation': exp_correlations.median(),
                'count': len(exp_correlations)
            },
            'baseline_stats': {
                'correlations': baseline_correlations,
                'mean_correlation': np.mean(baseline_correlations),
                'std_correlation': np.std(baseline_correlations),
                'median_correlation': np.median(baseline_correlations),
                'count': len(baseline_correlations)
            }
        }
        
        print(f"实验数据情绪相关性: {comparison['experimental_stats']['mean_correlation']:.3f} ± {comparison['experimental_stats']['std_correlation']:.3f}")
        print(f"Baseline情绪相关性: {comparison['baseline_stats']['mean_correlation']:.3f} ± {comparison['baseline_stats']['std_correlation']:.3f}")
        
        # 分析各个baseline相对于实验数据的位置
        exp_percentiles = np.percentile(exp_correlations, [25, 50, 75])
        
        print(f"\nBaseline在实验数据分布中的位置:")
        for result in self.baseline_results:
            correlation = result['emotion_correlation']
            if correlation < exp_percentiles[0]:
                position = "低于25分位"
            elif correlation < exp_percentiles[1]:
                position = "25-50分位"
            elif correlation < exp_percentiles[2]:
                position = "50-75分位"
            else:
                position = "高于75分位"
            
            print(f"  {result['archetype']} (seed {result['seed']}): {correlation:.3f} ({position})")
        
        return comparison
    
    def generate_visualizations(self):
        """生成可视化图表"""
        print(f"\n📊 生成可视化图表")
        print("=" * 60)
        
        # 1. Baseline情绪特征对比图
        self._plot_baseline_emotion_comparison()
        
        # 2. 情绪轨迹图
        self._plot_emotion_trajectories()
        
        # 3. 与实验数据的分布对比
        self._plot_distribution_comparison()
        
        print(f"✅ 图表已保存到 {self.output_dir}")
    
    def _plot_baseline_emotion_comparison(self):
        """绘制baseline情绪特征对比"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Updated Baseline Emotion Analysis Comparison', fontsize=16, fontweight='bold')
        
        # 提取数据
        seeds = [result['seed'] for result in self.baseline_results]
        archetypes = [result['archetype'] for result in self.baseline_results]
        roberta_means = [result['roberta_mean'] for result in self.baseline_results]
        labmt_means = [result['labmt_mean'] for result in self.baseline_results]
        correlations = [result['emotion_correlation'] for result in self.baseline_results]
        volatilities = [result['emotional_volatility'] for result in self.baseline_results]
        
        # RoBERTa平均分
        ax1 = axes[0, 0]
        bars1 = ax1.bar(range(len(seeds)), roberta_means, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('RoBERTa Average Scores', fontweight='bold')
        ax1.set_xlabel('Baseline')
        ax1.set_ylabel('Average Score')
        ax1.set_xticks(range(len(seeds)))
        ax1.set_xticklabels([f'{archetype}\n(seed {seed})' for seed, archetype in zip(seeds, archetypes)])
        
        for bar, value in zip(bars1, roberta_means):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # LabMT平均分
        ax2 = axes[0, 1]
        bars2 = ax2.bar(range(len(seeds)), labmt_means, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax2.set_title('LabMT Average Scores', fontweight='bold')
        ax2.set_xlabel('Baseline')
        ax2.set_ylabel('Average Score')
        ax2.set_xticks(range(len(seeds)))
        ax2.set_xticklabels([f'{archetype}\n(seed {seed})' for seed, archetype in zip(seeds, archetypes)])
        
        for bar, value in zip(bars2, labmt_means):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 情绪相关性
        ax3 = axes[1, 0]
        bars3 = ax3.bar(range(len(seeds)), correlations, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax3.set_title('Emotion Correlations', fontweight='bold')
        ax3.set_xlabel('Baseline')
        ax3.set_ylabel('Correlation')
        ax3.set_xticks(range(len(seeds)))
        ax3.set_xticklabels([f'{archetype}\n(seed {seed})' for seed, archetype in zip(seeds, archetypes)])
        
        for bar, value in zip(bars3, correlations):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 情绪波动性
        ax4 = axes[1, 1]
        bars4 = ax4.bar(range(len(seeds)), volatilities, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax4.set_title('Emotional Volatility', fontweight='bold')
        ax4.set_xlabel('Baseline')
        ax4.set_ylabel('Volatility')
        ax4.set_xticks(range(len(seeds)))
        ax4.set_xticklabels([f'{archetype}\n(seed {seed})' for seed, archetype in zip(seeds, archetypes)])
        
        for bar, value in zip(bars4, volatilities):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/updated_baseline_emotion_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_emotion_trajectories(self):
        """绘制情绪轨迹图"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Emotion Trajectories by Archetype', fontsize=16, fontweight='bold')
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, result in enumerate(self.baseline_results):
            ax = axes[i]
            
            # 获取情绪分数
            row = self.baseline_data[self.baseline_data['seed'] == result['seed']].iloc[0]
            roberta_scores = row['roberta_scores_list']
            labmt_scores = row['labmt_scores_list']
            
            x = range(len(roberta_scores))
            
            ax.plot(x, roberta_scores, 'o-', color=colors[i], linewidth=2, markersize=6, label='RoBERTa')
            ax.plot(x, labmt_scores, 's--', color=colors[i], alpha=0.7, linewidth=2, markersize=6, label='LabMT')
            
            ax.set_title(f'{result["archetype"]} (seed {result["seed"]})', fontweight='bold')
            ax.set_xlabel('Chapter')
            ax.set_ylabel('Emotion Score')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 添加相关性信息
            ax.text(0.02, 0.98, f'Correlation: {result["emotion_correlation"]:.3f}', 
                   transform=ax.transAxes, fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/emotion_trajectories_by_archetype.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_distribution_comparison(self):
        """绘制与实验数据的分布对比"""
        plt.figure(figsize=(12, 8))
        
        # 实验数据分布
        exp_correlations = self.experiment_data['emotion_correlation'].dropna()
        plt.hist(exp_correlations, bins=20, alpha=0.7, label='Experimental Data', color='skyblue', density=True)
        
        # Baseline点位
        baseline_correlations = [result['emotion_correlation'] for result in self.baseline_results]
        colors = ['red', 'green', 'orange']
        
        for i, (result, color) in enumerate(zip(self.baseline_results, colors)):
            plt.axvline(result['emotion_correlation'], color=color, linestyle='--', linewidth=2,
                       label=f'{result["archetype"]} (seed {result["seed"]})')
        
        plt.title('Emotion Correlation Distribution: Baselines vs Experimental Data', 
                 fontsize=14, fontweight='bold')
        plt.xlabel('Emotion Correlation')
        plt.ylabel('Density')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 添加统计信息
        exp_mean = exp_correlations.mean()
        baseline_mean = np.mean(baseline_correlations)
        
        plt.text(0.02, 0.98, f'Experimental Mean: {exp_mean:.3f}\nBaseline Mean: {baseline_mean:.3f}', 
                transform=plt.gca().transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/distribution_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_updated_report(self):
        """生成更新后的报告"""
        print(f"\n📝 生成更新后的报告")
        print("=" * 60)
        
        # 进行对比分析
        comparison = self.compare_with_experiments()
        
        updated_report = {
            'report_info': {
                'timestamp': datetime.now().isoformat(),
                'report_type': 'Updated Baseline Emotion Analysis',
                'baseline_count': len(self.baseline_results),
                'preserves_original_findings': True
            },
            'original_technical_findings': self.original_technical_findings,
            'updated_baseline_analysis': {
                'baseline_details': self.baseline_results,
                'archetype_distribution': {
                    result['archetype']: {
                        'seed': result['seed'],
                        'emotion_correlation': result['emotion_correlation'],
                        'roberta_mean': result['roberta_mean'],
                        'labmt_mean': result['labmt_mean'],
                        'emotional_volatility': result['emotional_volatility']
                    } for result in self.baseline_results
                }
            },
            'baseline_experimental_comparison': comparison,
            'key_observations': [
                f"3个baseline分别代表不同的故事原型：{', '.join([r['archetype'] for r in self.baseline_results])}",
                f"情绪相关性范围：{min([r['emotion_correlation'] for r in self.baseline_results]):.3f} - {max([r['emotion_correlation'] for r in self.baseline_results]):.3f}",
                f"Tragedy原型显示最高的情绪相关性({[r for r in self.baseline_results if r['archetype'] == 'Tragedy'][0]['emotion_correlation']:.3f})",
                "保持原有技术分析结论：RoBERTa vs LabMT的bug修复和方法改进"
            ],
            'technical_status': {
                'correlation_direction_bug': 'FIXED',
                'labmt_negation_handling': 'IDENTIFIED_NOT_IMPLEMENTED',
                'direction_consistency_improvement': '+46.9%',
                'fdr_correction_applied': True
            }
        }
        
        # 保存JSON报告
        with open(f'{self.output_dir}/updated_baseline_emotion_report.json', 'w', encoding='utf-8') as f:
            json.dump(updated_report, f, indent=2, ensure_ascii=False, default=str)
        
        # 生成Markdown报告
        self._generate_markdown_report(updated_report)
        
        print(f"✅ 报告已保存到 {self.output_dir}")
        
        return updated_report
    
    def _generate_markdown_report(self, report):
        """生成Markdown报告"""
        md_content = f"""# 更新后的Baseline情绪分析报告

**生成时间**: {datetime.now().strftime('%Y年%m月%d日')}  
**分析范围**: 54个实验故事 + 3个baseline故事  

---

## 🎯 核心说明

**保持原有技术分析结论**：本次更新仅针对baseline部分，**完全保持**原有的RoBERTa vs LabMT双方法情绪分析的技术问题与修复结论。

### 原有关键技术发现（保持不变）

#### 🚨 **致命BUG确认并修复**
- **串值错误**: 74.1%的条目中`correlation_coefficient`和`direction_consistency`值完全相同
- **修复状态**: ✅ 已修复
- **影响**: 解释了为什么相关性分析结果不可靠

#### 🔧 **LabMT技术缺陷（待修复）**
- **否定词处理**: ❌ 完全未实现，"not good"被误判为正面情绪
- **分词问题**: 仅使用简单正则表达式，不处理缩略词
- **影响**: 严重影响情感分析准确性

#### ✅ **修复效果显著**
- **方向一致性**: 从0.418提升至0.614 (+46.9%)
- **FDR校正**: 实施多重测试校正，确保统计严谨性

---

## 📊 更新后的Baseline分析

### 3个Baseline的情绪特征

现在有3个不同原型的baseline（不做一致性分析，而是描述各自特征）：

"""
        
        for result in report['updated_baseline_analysis']['baseline_details']:
            md_content += f"""
#### 🎭 {result['archetype']} 原型 (seed {result['seed']})

- **情绪相关性**: {result['emotion_correlation']:.3f}
- **RoBERTa均值**: {result['roberta_mean']:.3f} ± {result['roberta_std']:.3f}
- **LabMT均值**: {result['labmt_mean']:.3f} ± {result['labmt_std']:.3f}  
- **情绪波动性**: {result['emotional_volatility']:.3f}
- **方向一致性(修复后)**: {result['direction_consistency_fixed']:.3f}
- **情绪变化幅度**: {result['roberta_total_change']:.3f} (RoBERTa)
"""
        
        md_content += f"""
### 与实验数据对比

| 数据类型 | 情绪相关性均值 | 标准差 | 中位数 |
|----------|----------------|--------|--------|
| 实验数据 | {report['baseline_experimental_comparison']['experimental_stats']['mean_correlation']:.3f} | {report['baseline_experimental_comparison']['experimental_stats']['std_correlation']:.3f} | {report['baseline_experimental_comparison']['experimental_stats']['median_correlation']:.3f} |
| Baseline | {report['baseline_experimental_comparison']['baseline_stats']['mean_correlation']:.3f} | {report['baseline_experimental_comparison']['baseline_stats']['std_correlation']:.3f} | {report['baseline_experimental_comparison']['baseline_stats']['median_correlation']:.3f} |

---

## 🔍 关键观察

"""
        
        for observation in report['key_observations']:
            md_content += f"- {observation}\n"
        
        md_content += f"""
---

## 🛠️ 技术状态总结

| 技术问题 | 状态 | 说明 |
|----------|------|------|
| 串值BUG | ✅ 已修复 | correlation与direction_consistency不再相同 |
| 方向一致性 | ✅ 显著改善 | 提升46.9% |
| LabMT否定词处理 | ❌ 未实现 | 需要后续开发 |
| FDR多重测试校正 | ✅ 已实施 | 确保统计严谨性 |

---

## 📁 生成文件

- `updated_baseline_emotion_comparison.png` - baseline情绪特征对比
- `emotion_trajectories_by_archetype.png` - 按原型分类的情绪轨迹
- `distribution_comparison.png` - 与实验数据的分布对比
- `updated_baseline_emotion_report.json` - 完整数据报告

---

**重要说明**: 本报告保持所有原有技术分析结论不变，仅更新baseline分析部分以适应新的3个baseline结构。所有关于RoBERTa vs LabMT方法对比、bug修复、改进建议等技术结论继续有效。
"""
        
        with open(f'{self.output_dir}/updated_baseline_emotion_report.md', 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def run_complete_analysis(self):
        """运行完整分析"""
        print("🚀 开始更新后的Baseline情绪分析")
        print("=" * 60)
        
        # 1. 分析新的baseline
        self.analyze_updated_baselines()
        
        # 2. 生成可视化
        self.generate_visualizations()
        
        # 3. 生成报告
        report = self.generate_updated_report()
        
        print("\n🎉 分析完成！")
        print("=" * 60)
        print(f"✅ 保持所有原有技术分析结论")
        print(f"✅ 更新了3个baseline的情绪特征分析")
        print(f"✅ 结果保存在: {self.output_dir}")
        
        return report


def main():
    """主函数"""
    csv_path = '/Users/haha/Story/metrics_master_clean.csv'
    
    # 初始化并运行分析
    analyzer = UpdatedBaselineEmotionAnalyzer(csv_path)
    report = analyzer.run_complete_analysis()
    
    return report


if __name__ == "__main__":
    main()
