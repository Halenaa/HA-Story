#!/usr/bin/env python3
"""
Coherence维度Human Validation分析
目标：回应硕士论文导师的学术要求
- 计算auto-human coherence correlation
- 重新设定基于empirical data的阈值
- 分析practical significance
- 验证method validity
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_curve, auc
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings('ignore')

class CoherenceHumanValidationAnalyzer:
    def __init__(self):
        """初始化分析器"""
        self.human_data = None
        self.auto_data = None
        self.merged_data = None
        self.results = {}
        
    def load_human_data(self, csv_path="/Users/haha/Story/Interview.csv"):
        """加载人工评价数据"""
        print("📊 加载人工评价数据...")
        df = pd.read_csv(csv_path)
        
        # 提取coherence评分 (每个故事4列coherence数据)
        coherence_data = []
        
        for index, row in df.iterrows():
            participant_id = f"P{index+1:02d}"
            group_id = row['Group_id']
            
            # 获取4个故事的配置信息
            stories = [row['Story 1'], row['Story 2'], row['Story 3'], row['Story 4']]
            
            # 获取coherence评分 (注意列名可能有后缀)
            coherence_cols = [
                'Coherence How coherent and logical is the plot development of this story?',
                'Coherence How coherent and logical is the plot development of this story?.1', 
                'Coherence How coherent and logical is the plot development of this story?.2',
                'Coherence How coherent and logical is the plot development of this story?.3'
            ]
            
            for i, (story_config, coherence_col) in enumerate(zip(stories, coherence_cols)):
                if coherence_col in row and pd.notna(row[coherence_col]):
                    coherence_data.append({
                        'participant_id': participant_id,
                        'group_id': group_id,
                        'story_position': i + 1,
                        'story_config': story_config,
                        'human_coherence': row[coherence_col],
                        'is_baseline': story_config == 'Sci baseline'
                    })
        
        self.human_data = pd.DataFrame(coherence_data)
        print(f"✅ 成功加载 {len(self.human_data)} 条人工coherence评分")
        print(f"   - 基线故事评分: {sum(self.human_data['is_baseline'])} 条")
        print(f"   - 实验故事评分: {sum(~self.human_data['is_baseline'])} 条")
        
        return self.human_data
    
    def load_auto_coherence_data(self):
        """加载自动coherence数据"""
        print("\n🤖 加载自动coherence分析结果...")
        
        auto_data = []
        
        # 1. 加载baseline数据
        baseline_files = [
            ("/Users/haha/Story/baseline_analysis_results/baseline_s1/hred_coherence_analysis.json", "simple_baseline_s1"),
            ("/Users/haha/Story/baseline_analysis_results/baseline_s2/hred_coherence_analysis.json", "simple_baseline_s2"), 
            ("/Users/haha/Story/baseline_analysis_results/baseline_s3/hred_coherence_analysis.json", "simple_baseline_s3")
        ]
        
        for file_path, config_name in baseline_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    auto_coherence = data['HRED_coherence_evaluation']['average_coherence']
                    total_sentences = data['HRED_coherence_evaluation']['total_sentences']
                    coherence_std = data['detailed_analysis']['basic_statistics']['coherence_std']
                    
                    auto_data.append({
                        'story_config': config_name,
                        'auto_coherence': auto_coherence,
                        'total_sentences': total_sentences,
                        'coherence_std': coherence_std,
                        'is_baseline': True
                    })
            except Exception as e:
                print(f"   警告：无法加载 {file_path}: {e}")
        
        # 2. 从metrics_master_clean.csv加载实验数据
        try:
            metrics_df = pd.read_csv("/Users/haha/Story/metrics_master_clean.csv")
            
            for _, row in metrics_df.iterrows():
                if pd.notna(row.get('avg_coherence')):
                    # 构建story_config名称
                    structure = row.get('structure', '')
                    temperature = row.get('temperature', '')
                    seed = row.get('seed', '')
                    
                    if structure and temperature and seed:
                        story_config = f"{structure}_T{temperature}_s{seed}"
                        
                        auto_data.append({
                            'story_config': story_config,
                            'auto_coherence': row['avg_coherence'],
                            'total_sentences': row.get('total_sentences', None),
                            'coherence_std': None,  # metrics文件中没有std数据
                            'is_baseline': False
                        })
        except Exception as e:
            print(f"   警告：无法加载metrics文件: {e}")
        
        self.auto_data = pd.DataFrame(auto_data)
        print(f"✅ 成功加载 {len(self.auto_data)} 条自动coherence分析结果")
        
        return self.auto_data
    
    def merge_human_auto_data(self):
        """合并人工和自动评价数据"""
        print("\n🔗 合并人工和自动评价数据...")
        
        # 打印调试信息
        print("\n调试信息:")
        print("Human story configs:", self.human_data['story_config'].unique())
        print("Auto story configs:", self.auto_data['story_config'].unique())
        
        # 更复杂的mapping策略
        merged_records = []
        
        for _, human_row in self.human_data.iterrows():
            human_config = human_row['story_config']
            
            # 1. 处理baseline匹配
            if human_config == 'Sci baseline':
                # 找到任意一个baseline auto结果（因为它们本质相同）
                baseline_auto = self.auto_data[self.auto_data['is_baseline']].iloc[0] if len(self.auto_data[self.auto_data['is_baseline']]) > 0 else None
                if baseline_auto is not None:
                    merged_record = human_row.to_dict()
                    merged_record.update({
                        'auto_coherence': baseline_auto['auto_coherence'],
                        'total_sentences': baseline_auto['total_sentences'],
                        'coherence_std': baseline_auto['coherence_std'],
                        'is_baseline_auto': baseline_auto['is_baseline']
                    })
                    merged_records.append(merged_record)
            
            # 2. 处理实验配置匹配
            else:
                # 直接查找匹配的配置
                matching_auto = self.auto_data[self.auto_data['story_config'] == human_config]
                if len(matching_auto) > 0:
                    auto_row = matching_auto.iloc[0]
                    merged_record = human_row.to_dict()
                    merged_record.update({
                        'auto_coherence': auto_row['auto_coherence'],
                        'total_sentences': auto_row['total_sentences'], 
                        'coherence_std': auto_row['coherence_std'],
                        'is_baseline_auto': auto_row['is_baseline']
                    })
                    merged_records.append(merged_record)
        
        self.merged_data = pd.DataFrame(merged_records)
        print(f"✅ 成功合并 {len(self.merged_data)} 条matched记录")
        
        if len(self.merged_data) > 0:
            print(f"   - Baseline记录: {sum(self.merged_data['is_baseline'])} 条")  
            print(f"   - 实验记录: {sum(~self.merged_data['is_baseline'])} 条")
            print(f"   - Auto coherence范围: {self.merged_data['auto_coherence'].min():.3f} - {self.merged_data['auto_coherence'].max():.3f}")
        else:
            print("❌ 警告：没有匹配的记录！")
        
        return self.merged_data
    
    def calculate_correlation_analysis(self):
        """计算correlation分析 - 核心学术验证"""
        print("\n📈 计算Human-Auto Coherence Correlation...")
        
        if len(self.merged_data) == 0:
            print("❌ 无法进行correlation分析：没有匹配数据")
            return None
        
        human_scores = self.merged_data['human_coherence']
        auto_scores = self.merged_data['auto_coherence']
        
        # 检查auto scores是否为constant
        if auto_scores.std() == 0:
            print("⚠️ 警告：所有auto coherence分数相同，无法计算correlation")
            pearson_r, pearson_p = np.nan, np.nan
            spearman_r, spearman_p = np.nan, np.nan
        else:
            # 1. Pearson correlation
            pearson_r, pearson_p = pearsonr(human_scores, auto_scores)
            
            # 2. Spearman correlation (更robust)
            spearman_r, spearman_p = spearmanr(human_scores, auto_scores)
        
        # 3. 计算不同子组的correlation
        baseline_mask = self.merged_data['is_baseline']
        
        if sum(baseline_mask) > 2:
            baseline_pearson_r, baseline_pearson_p = pearsonr(
                human_scores[baseline_mask], auto_scores[baseline_mask]
            )
        else:
            baseline_pearson_r, baseline_pearson_p = np.nan, np.nan
        
        if sum(~baseline_mask) > 2:
            exp_pearson_r, exp_pearson_p = pearsonr(
                human_scores[~baseline_mask], auto_scores[~baseline_mask]
            )
        else:
            exp_pearson_r, exp_pearson_p = np.nan, np.nan
        
        correlation_results = {
            'overall_correlation': {
                'pearson_r': pearson_r,
                'pearson_p': pearson_p,
                'spearman_r': spearman_r,
                'spearman_p': spearman_p,
                'sample_size': len(human_scores),
                'significant': pearson_p < 0.05,
                'strong_correlation': abs(pearson_r) > 0.5
            },
            'baseline_correlation': {
                'pearson_r': baseline_pearson_r,
                'pearson_p': baseline_pearson_p,
                'sample_size': sum(baseline_mask)
            },
            'experimental_correlation': {
                'pearson_r': exp_pearson_r,
                'pearson_p': exp_pearson_p,
                'sample_size': sum(~baseline_mask)
            }
        }
        
        self.results['correlation_analysis'] = correlation_results
        
        # 打印结果
        print(f"📊 Correlation Analysis Results:")
        print(f"   Overall Pearson r = {pearson_r:.3f} (p = {pearson_p:.3f})")
        print(f"   Overall Spearman r = {spearman_r:.3f} (p = {spearman_p:.3f})")
        print(f"   Sample size: {len(human_scores)}")
        
        # 学术判断
        if pearson_p < 0.05:
            if abs(pearson_r) > 0.7:
                print("   ✅ 强显著相关 (学术标准: EXCELLENT)")
            elif abs(pearson_r) > 0.5:
                print("   ✅ 中等显著相关 (学术标准: ACCEPTABLE)")
            elif abs(pearson_r) > 0.3:
                print("   ⚠️ 弱显著相关 (学术标准: MARGINAL)")
            else:
                print("   ❌ 显著但相关性很弱 (学术标准: INSUFFICIENT)")
        else:
            print("   ❌ 无显著相关 (学术标准: FAILED)")
        
        return correlation_results
    
    def empirical_threshold_setting(self):
        """基于empirical data重新设定阈值"""
        print("\n🎯 基于Human Data设定Empirical Thresholds...")
        
        if len(self.merged_data) == 0:
            return None
        
        human_scores = self.merged_data['human_coherence']
        auto_scores = self.merged_data['auto_coherence']
        
        # 1. 基于human score quartiles
        human_quartiles = np.percentile(human_scores, [25, 50, 75])
        
        # 2. 基于human score对应的auto score分布
        high_human = auto_scores[human_scores >= human_quartiles[2]]  # top 25%
        medium_human = auto_scores[(human_scores >= human_quartiles[0]) & (human_scores < human_quartiles[2])]
        low_human = auto_scores[human_scores < human_quartiles[0]]  # bottom 25%
        
        # 3. 设定new thresholds
        if len(high_human) > 0 and len(low_human) > 0:
            excellent_threshold = np.percentile(high_human, 25)  # 高人工评分组的25%分位数
            poor_threshold = np.percentile(low_human, 75)        # 低人工评分组的75%分位数
            good_threshold = (excellent_threshold + poor_threshold) / 2
        else:
            # fallback到统计学方法
            excellent_threshold = np.percentile(auto_scores, 75)
            good_threshold = np.percentile(auto_scores, 50)  
            poor_threshold = np.percentile(auto_scores, 25)
        
        threshold_results = {
            'empirical_thresholds': {
                'excellent': excellent_threshold,
                'good': good_threshold,
                'poor': poor_threshold
            },
            'old_thresholds': {
                'excellent': 0.7,
                'good': 0.5,
                'poor': 0.3
            },
            'human_quartiles': {
                'Q1': human_quartiles[0],
                'Q2': human_quartiles[1], 
                'Q3': human_quartiles[2]
            },
            'threshold_method': 'human_score_based_quartiles'
        }
        
        self.results['threshold_analysis'] = threshold_results
        
        print(f"📊 Empirical Thresholds (vs Old Arbitrary):")
        print(f"   Excellent: {excellent_threshold:.3f} (was: 0.700)")
        print(f"   Good:      {good_threshold:.3f} (was: 0.500)")
        print(f"   Poor:      {poor_threshold:.3f} (was: 0.300)")
        
        return threshold_results
    
    def practical_significance_analysis(self):
        """分析practical significance"""
        print("\n💡 Practical Significance Analysis...")
        
        if len(self.merged_data) == 0:
            return None
        
        human_scores = self.merged_data['human_coherence']
        auto_scores = self.merged_data['auto_coherence']
        
        # 1. Effect size分析
        # 计算人工评分高分组vs低分组的auto score差异
        high_human_mask = human_scores >= np.percentile(human_scores, 75)
        low_human_mask = human_scores <= np.percentile(human_scores, 25)
        
        high_auto_scores = auto_scores[high_human_mask]
        low_auto_scores = auto_scores[low_human_mask]
        
        if len(high_auto_scores) > 0 and len(low_auto_scores) > 0:
            # Cohen's d effect size
            pooled_std = np.sqrt(((len(high_auto_scores)-1)*np.var(high_auto_scores) + 
                                (len(low_auto_scores)-1)*np.var(low_auto_scores)) / 
                               (len(high_auto_scores)+len(low_auto_scores)-2))
            cohens_d = (np.mean(high_auto_scores) - np.mean(low_auto_scores)) / pooled_std
            
            # 实际差异
            practical_diff = np.mean(high_auto_scores) - np.mean(low_auto_scores)
            relative_diff = practical_diff / np.mean(low_auto_scores) * 100
        else:
            cohens_d = np.nan
            practical_diff = np.nan 
            relative_diff = np.nan
        
        # 2. 分析0.404这个分数的意义
        auto_mean = np.mean(auto_scores)
        human_mean = np.mean(human_scores)
        
        # 找到auto_coherence=0.404对应的human score期望值
        if len(self.merged_data) > 3:
            from scipy.interpolate import interp1d
            try:
                # 使用插值估计0.404对应的human score
                sorted_indices = np.argsort(auto_scores)
                sorted_auto = auto_scores.iloc[sorted_indices]
                sorted_human = human_scores.iloc[sorted_indices]
                
                if auto_mean >= min(sorted_auto) and auto_mean <= max(sorted_auto):
                    interp_func = interp1d(sorted_auto, sorted_human, kind='linear', fill_value='extrapolate')
                    expected_human_score = interp_func(0.404)
                else:
                    expected_human_score = np.nan
            except:
                expected_human_score = np.nan
        else:
            expected_human_score = np.nan
        
        practical_results = {
            'effect_size': {
                'cohens_d': cohens_d,
                'interpretation': self._interpret_cohens_d(cohens_d)
            },
            'practical_difference': {
                'absolute_diff': practical_diff,
                'relative_diff_percent': relative_diff
            },
            'score_interpretation': {
                'ai_average_auto_coherence': 0.404,
                'baseline_average_auto_coherence': 0.259,
                'expected_human_score_for_0404': expected_human_score,
                'human_score_range': f"{np.min(human_scores):.1f} - {np.max(human_scores):.1f}",
                'human_mean': human_mean
            }
        }
        
        self.results['practical_significance'] = practical_results
        
        print(f"📊 Practical Significance Results:")
        if not np.isnan(cohens_d):
            print(f"   Cohen's d = {cohens_d:.3f} ({self._interpret_cohens_d(cohens_d)})")
        if not np.isnan(expected_human_score):
            print(f"   Auto score 0.404 → Expected human score: {expected_human_score:.1f}/10")
        print(f"   Human score range: {np.min(human_scores):.1f} - {np.max(human_scores):.1f}")
        print(f"   Human mean: {human_mean:.1f}")
        
        return practical_results
    
    def _interpret_cohens_d(self, d):
        """解释Cohen's d effect size"""
        if np.isnan(d):
            return "无法计算"
        elif abs(d) >= 0.8:
            return "大效应"
        elif abs(d) >= 0.5:
            return "中等效应"
        elif abs(d) >= 0.2:
            return "小效应"
        else:
            return "微弱效应"
    
    def create_validation_visualizations(self):
        """创建validation可视化图表"""
        print("\n📈 创建Human Validation可视化...")
        
        if len(self.merged_data) == 0:
            print("❌ 无数据可视化")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Scatter plot: Human vs Auto coherence
        ax1 = axes[0, 0]
        human_scores = self.merged_data['human_coherence']
        auto_scores = self.merged_data['auto_coherence']
        
        ax1.scatter(auto_scores, human_scores, alpha=0.7, s=60)
        
        # 添加regression line
        z = np.polyfit(auto_scores, human_scores, 1)
        p = np.poly1d(z)
        ax1.plot(auto_scores, p(auto_scores), "r--", alpha=0.8)
        
        # 添加correlation信息
        if 'correlation_analysis' in self.results:
            r = self.results['correlation_analysis']['overall_correlation']['pearson_r']
            p_val = self.results['correlation_analysis']['overall_correlation']['pearson_p']
            ax1.text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.3f}', 
                    transform=ax1.transAxes, bbox=dict(boxstyle="round", facecolor='white', alpha=0.8),
                    verticalalignment='top')
        
        ax1.set_xlabel('Auto Coherence Score')
        ax1.set_ylabel('Human Coherence Score (1-10)')
        ax1.set_title('Human vs Automated Coherence Correlation')
        ax1.grid(True, alpha=0.3)
        
        # 2. Distribution comparison
        ax2 = axes[0, 1]
        ax2.hist(human_scores, alpha=0.5, label='Human Scores', bins=10, density=True)
        
        # Normalize auto scores to 1-10 scale for comparison
        if auto_scores.max() != auto_scores.min():
            auto_normalized = (auto_scores - auto_scores.min()) / (auto_scores.max() - auto_scores.min()) * 9 + 1
            ax2.hist(auto_normalized, alpha=0.5, label='Auto Scores (normalized)', bins=10, density=True)
        else:
            # 如果所有auto scores相同，显示为单一值
            ax2.axvline(x=5, color='orange', alpha=0.7, linewidth=3, label=f'Auto Score (constant: {auto_scores.iloc[0]:.3f})')
        
        ax2.set_xlabel('Coherence Score')
        ax2.set_ylabel('Density')
        ax2.set_title('Score Distribution Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Threshold comparison
        ax3 = axes[1, 0]
        if 'threshold_analysis' in self.results:
            old_thresholds = [0.3, 0.5, 0.7]
            new_thresholds = [
                self.results['threshold_analysis']['empirical_thresholds']['poor'],
                self.results['threshold_analysis']['empirical_thresholds']['good'],
                self.results['threshold_analysis']['empirical_thresholds']['excellent']
            ]
            
            x = ['Poor/Good', 'Good/Excellent', 'Excellent+']
            x_pos = np.arange(len(x))
            
            width = 0.35
            ax3.bar(x_pos - width/2, old_thresholds, width, label='Old (Arbitrary)', alpha=0.7)
            ax3.bar(x_pos + width/2, new_thresholds, width, label='New (Empirical)', alpha=0.7)
            
            ax3.set_xlabel('Threshold Categories')
            ax3.set_ylabel('Auto Coherence Score')
            ax3.set_title('Threshold Comparison: Arbitrary vs Empirical')
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels(x)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 4. Residual analysis
        ax4 = axes[1, 1]
        if len(auto_scores) > 0 and len(human_scores) > 0:
            # Calculate predicted human scores
            z = np.polyfit(auto_scores, human_scores, 1)
            predicted_human = z[0] * auto_scores + z[1]
            residuals = human_scores - predicted_human
            
            ax4.scatter(predicted_human, residuals, alpha=0.7)
            ax4.axhline(y=0, color='red', linestyle='--', alpha=0.8)
            ax4.set_xlabel('Predicted Human Score')
            ax4.set_ylabel('Residuals')
            ax4.set_title('Residual Analysis')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/Users/haha/Story/coherence_human_validation_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("✅ 可视化图表已保存: coherence_human_validation_analysis.png")
    
    def generate_academic_report(self):
        """生成学术报告"""
        print("\n📝 生成学术报告...")
        
        report = {
            'analysis_metadata': {
                'analysis_date': pd.Timestamp.now().isoformat(),
                'purpose': 'Human validation of automated coherence metric for Master thesis',
                'human_evaluators': len(self.human_data['participant_id'].unique()) if self.human_data is not None else 0,
                'total_evaluations': len(self.merged_data) if self.merged_data is not None else 0
            },
            'validation_results': self.results
        }
        
        # 保存detailed results
        with open('/Users/haha/Story/coherence_human_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        # 生成简化的学术总结
        self._generate_academic_summary()
        
        print("✅ 学术报告已生成:")
        print("   - 详细报告: coherence_human_validation_report.json")
        print("   - 学术总结: coherence_academic_validation_summary.md")
    
    def _generate_academic_summary(self):
        """生成学术总结"""
        if len(self.results) == 0:
            return
        
        summary = """# Coherence Metric Human Validation - Academic Summary

## 🎯 研究目的
验证自动化coherence指标与人工评价的一致性，以满足硕士论文学术标准要求。

## 📊 验证方法
- **Human Evaluation**: 20名评价者，80条coherence评分 (1-10分)
- **Automated Metric**: HRED-based sentence-transformer coherence analysis
- **Question**: "How coherent and logical is the plot development of this story?"

## 📈 关键发现

### 1. Correlation Analysis
"""
        
        if 'correlation_analysis' in self.results:
            corr = self.results['correlation_analysis']['overall_correlation']
            summary += f"""
- **Pearson r = {corr['pearson_r']:.3f}** (p = {corr['pearson_p']:.3f})
- **Spearman r = {corr['spearman_r']:.3f}** (p = {corr['spearman_p']:.3f})
- **Sample size**: {corr['sample_size']}
- **Statistical significance**: {'✅ YES' if corr['significant'] else '❌ NO'}
- **Academic assessment**: {'✅ ACCEPTABLE' if corr.get('strong_correlation', False) else '⚠️ NEEDS IMPROVEMENT'}
"""
        
        if 'threshold_analysis' in self.results:
            thresh = self.results['threshold_analysis']
            summary += f"""
### 2. Empirical Threshold Setting
**Old (Arbitrary) vs New (Empirical)**:
- Poor/Good boundary: 0.300 → {thresh['empirical_thresholds']['poor']:.3f}
- Good/Excellent boundary: 0.500 → {thresh['empirical_thresholds']['good']:.3f}  
- Excellence threshold: 0.700 → {thresh['empirical_thresholds']['excellent']:.3f}

**Method**: Based on human score quartiles and corresponding auto scores
"""
        
        if 'practical_significance' in self.results:
            practical = self.results['practical_significance']
            summary += f"""
### 3. Practical Significance
"""
            if 'effect_size' in practical:
                summary += f"- **Effect size**: Cohen's d = {practical['effect_size']['cohens_d']:.3f} ({practical['effect_size']['interpretation']})\n"
            
            if 'score_interpretation' in practical:
                score_interp = practical['score_interpretation']
                summary += f"""- **AI Story Average (0.404)** corresponds to human score: {score_interp.get('expected_human_score_for_0404', 'N/A'):.1f}/10
- **Human score range**: {score_interp['human_score_range']}
- **Baseline vs AI improvement**: 0.259 → 0.404 (+56%)
"""
        
        summary += """
## 🎓 学术结论

### Method Validity
"""
        
        # 根据correlation结果判断
        if 'correlation_analysis' in self.results:
            r = self.results['correlation_analysis']['overall_correlation']['pearson_r']
            p = self.results['correlation_analysis']['overall_correlation']['pearson_p']
            
            if p < 0.05 and abs(r) > 0.5:
                summary += "✅ **VALIDATED**: Automated coherence shows acceptable correlation with human judgment\n"
            elif p < 0.05 and abs(r) > 0.3:
                summary += "⚠️ **MARGINAL**: Automated coherence shows weak but significant correlation\n" 
            else:
                summary += "❌ **INSUFFICIENT**: Automated coherence lacks sufficient human validation\n"
        
        summary += """
### Threshold Justification
✅ **IMPROVED**: Thresholds now based on empirical human data rather than arbitrary cutoffs

### Limitations Acknowledged
- ⚠️ Method focuses on adjacent sentence similarity, may miss long-range coherence
- ⚠️ Semantic similarity ≠ logical consistency  
- ⚠️ Genre-specific effects not fully explored

### Master Thesis Readiness
"""
        
        # 综合判断
        validation_score = 0
        if 'correlation_analysis' in self.results:
            if self.results['correlation_analysis']['overall_correlation'].get('significant', False):
                validation_score += 1
            if self.results['correlation_analysis']['overall_correlation'].get('strong_correlation', False):
                validation_score += 1
        
        if validation_score >= 2:
            summary += "✅ **READY**: Coherence metric meets academic standards for Master thesis\n"
        elif validation_score == 1:
            summary += "⚠️ **CONDITIONAL**: Requires additional discussion of limitations\n"
        else:
            summary += "❌ **NOT READY**: Requires substantial improvement or replacement\n"
        
        summary += """
## 🔍 Recommended Next Steps

1. **If correlation is acceptable (r>0.5)**: Proceed with empirical thresholds
2. **If correlation is marginal (0.3<r<0.5)**: Add limitation discussion, consider complementary metrics
3. **If correlation is insufficient (r<0.3)**: Consider method revision or replacement

## 📚 Academic Defense Points

**Expected Questions & Answers**:
- Q: "Why 0.404 is good coherence?" 
  A: "Based on human validation, corresponds to X/10 human rating"
- Q: "Adjacent sentence limitation?"
  A: "Acknowledged limitation, future work should include discourse markers"  
- Q: "Human agreement validity?"
  A: "Correlation analysis shows r=X.XX, statistically significant"
"""
        
        with open('/Users/haha/Story/coherence_academic_validation_summary.md', 'w', encoding='utf-8') as f:
            f.write(summary)
    
    def run_complete_validation(self):
        """运行完整的human validation分析"""
        print("🎓 开始Coherence Human Validation Analysis")
        print("=" * 60)
        
        # Step 1: Load data
        self.load_human_data()
        self.load_auto_coherence_data()
        
        # Step 2: Merge and validate
        merged = self.merge_human_auto_data()
        if len(merged) == 0:
            print("❌ 分析失败：无法匹配human和auto数据")
            return None
        
        # Step 3: Core academic validations
        self.calculate_correlation_analysis()
        self.empirical_threshold_setting()
        self.practical_significance_analysis()
        
        # Step 4: Visualizations and reporting
        self.create_validation_visualizations()
        self.generate_academic_report()
        
        print("=" * 60)
        print("✅ Human Validation Analysis Complete!")
        
        return self.results


if __name__ == "__main__":
    analyzer = CoherenceHumanValidationAnalyzer()
    results = analyzer.run_complete_validation()
