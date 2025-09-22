#!/usr/bin/env python3
"""
实验4A：离散参数敏感性分析
Experiment 4A: Discrete Parameter Sensitivity Analysis

基于54组实验的3×2×3参数组合分析
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class DiscreteParameterAnalyzer:
    """离散参数敏感性分析器（适合54组实验）"""
    
    def __init__(self, df):
        self.df = df
        self.prepare_data()
    
    def prepare_data(self):
        """准备分析数据"""
        # 过滤实验数据
        self.df = self.df[self.df['is_baseline'] == 0].copy()
        
        # 重命名列以便使用
        self.df['Genre'] = self.df['genre']
        self.df['Structure'] = self.df['structure']
        self.df['Temperature'] = pd.to_numeric(self.df['temperature'])
        self.df['Semantic_Continuity'] = self.df['avg_semantic_continuity']
        self.df['Diversity'] = self.df['diversity_score_seed']
        self.df['Novelty'] = self.df['one_minus_self_bleu']
        self.df['Emotional_Consistency'] = self.df['roberta_avg_score']
        self.df['Fluency'] = 1 / (1 + self.df['pseudo_ppl'])  # 转换为正向指标
        
        # 计算综合得分
        score_columns = ['Semantic_Continuity', 'Diversity', 'Novelty', 'Emotional_Consistency']
        
        # 标准化各维度得分
        for col in score_columns:
            self.df[f'{col}_normalized'] = (self.df[col] - self.df[col].mean()) / self.df[col].std()
        
        normalized_cols = [f'{col}_normalized' for col in score_columns]
        self.df['综合得分'] = self.df[normalized_cols].mean(axis=1)
        
        print(f"📊 数据概览: {len(self.df)} 条记录")
        print(f"🎭 文本类型: {self.df['Genre'].unique()}")
        print(f"🌡️ Temperature设置: {sorted(self.df['Temperature'].unique())}")
        print(f"🏗️ Structure类型: {self.df['Structure'].unique()}")
        
        # 检查每个组合的样本数
        combination_counts = self.df.groupby(['Genre', 'Structure', 'Temperature']).size()
        print(f"\n📈 参数组合分布:")
        print(combination_counts)
    
    def calculate_discrete_sensitivity(self):
        """计算离散参数的敏感性（适合3个Temperature点）"""
        
        sensitivity_results = {}
        
        for genre in self.df['Genre'].unique():
            sensitivity_results[genre] = {}
            
            for structure in self.df['Structure'].unique():
                # 筛选当前组合的数据
                mask = (self.df['Genre'] == genre) & (self.df['Structure'] == structure)
                subset = self.df[mask].copy()
                
                if len(subset) == 0:
                    continue
                
                # 计算每个Temperature的统计量
                temp_stats = subset.groupby('Temperature')['综合得分'].agg([
                    'mean', 'std', 'count', 'min', 'max'
                ]).round(4)
                
                # 计算Temperature效应大小
                temp_means = temp_stats['mean']
                if len(temp_means) >= 2:
                    temp_effect_size = (temp_means.max() - temp_means.min())
                    optimal_temp = temp_means.idxmax()
                    worst_temp = temp_means.idxmin()
                    
                    # 计算相对改进
                    if abs(temp_means.min()) > 0.001:  # 避免除零
                        relative_improvement = ((temp_means.max() - temp_means.min()) / 
                                              abs(temp_means.min())) * 100
                    else:
                        relative_improvement = 0
                    
                    # 方差分析（如果有足够数据）
                    if len(subset) >= 6 and len(temp_means) >= 3:
                        groups = [subset[subset['Temperature']==t]['综合得分'].values 
                                 for t in sorted(subset['Temperature'].unique())]
                        # 过滤空组
                        groups = [g for g in groups if len(g) > 0]
                        if len(groups) >= 2:
                            try:
                                f_stat, p_value = stats.f_oneway(*groups)
                            except:
                                f_stat, p_value = None, None
                        else:
                            f_stat, p_value = None, None
                    else:
                        f_stat, p_value = None, None
                    
                    sensitivity_results[genre][structure] = {
                        'temperature_stats': temp_stats,
                        'effect_size': temp_effect_size,
                        'relative_improvement': relative_improvement,
                        'optimal_temp': optimal_temp,
                        'worst_temp': worst_temp,
                        'f_statistic': f_stat,
                        'p_value': p_value,
                        'sample_size': len(subset)
                    }
        
        return sensitivity_results
    
    def run_4a_discrete_analysis(self):
        """执行适合离散参数的4A分析"""
        
        print("🚀 开始4A实验：离散参数敏感性分析...\n")
        
        # 计算敏感性
        results = self.calculate_discrete_sensitivity()
        
        # 分析并输出结果
        print("📊 == 参数敏感性分析结果 ==\n")
        
        for genre, genre_data in results.items():
            print(f"🎭 **{genre.upper()}类型分析**")
            
            for structure, data in genre_data.items():
                print(f"\n🏗️ {structure}结构:")
                print(f"  📈 Temperature效应大小: {data['effect_size']:.4f}")
                print(f"  🎯 最优Temperature: {data['optimal_temp']} (得分: {data['temperature_stats'].loc[data['optimal_temp'], 'mean']:.3f})")
                print(f"  🔴 最差Temperature: {data['worst_temp']} (得分: {data['temperature_stats'].loc[data['worst_temp'], 'mean']:.3f})")
                print(f"  📊 相对改进: {data['relative_improvement']:.1f}%")
                print(f"  📝 样本数: {data['sample_size']}")
                
                if data['p_value'] is not None:
                    significance = "显著" if data['p_value'] < 0.05 else "不显著"
                    print(f"  🧪 统计检验: F={data['f_statistic']:.2f}, p={data['p_value']:.4f} ({significance})")
                
                # 详细的Temperature表现
                print(f"  📋 详细表现:")
                for temp in sorted(data['temperature_stats'].index):
                    stats_row = data['temperature_stats'].loc[temp]
                    print(f"    - Temperature {temp}: {stats_row['mean']:.3f} ± {stats_row['std']:.3f} (n={int(stats_row['count'])})")
            
            print("\n" + "="*50 + "\n")
        
        return results
    
    def create_discrete_interaction_plot(self, save_dir):
        """创建适合离散参数的交互效应图"""
        
        print("📊 创建离散参数交互效应图...")
        
        fig, axes = plt.subplots(2, len(self.df['Genre'].unique()), figsize=(18, 10))
        
        available_dims = ['Semantic_Continuity', 'Diversity']
        dim_names = ['Semantic Continuity', 'Diversity']
        
        if len(self.df['Genre'].unique()) == 1:
            axes = axes.reshape(-1, 1)
        
        for col, genre in enumerate(self.df['Genre'].unique()):
            genre_data = self.df[self.df['Genre'] == genre]
            
            for row, (dim, dim_name) in enumerate(zip(available_dims, dim_names)):
                ax = axes[row, col]
                
                # 为每种结构绘制折线图
                for structure in ['linear', 'nonlinear']:
                    struct_data = genre_data[genre_data['Structure'] == structure]
                    
                    if len(struct_data) == 0:
                        continue
                    
                    # 计算每个Temperature的统计量
                    temp_stats = struct_data.groupby('Temperature')[dim].agg(['mean', 'std', 'count'])
                    temp_stats['se'] = temp_stats['std'] / np.sqrt(temp_stats['count'])
                    
                    # 颜色设置
                    color = '#FF6B6B' if structure == 'linear' else '#4ECDC4'
                    
                    # 绘制主线条（连接离散点）
                    temperatures = sorted(temp_stats.index)
                    means = [temp_stats.loc[t, 'mean'] for t in temperatures]
                    
                    ax.plot(temperatures, means, 'o-', color=color, 
                           linewidth=3, markersize=10, label=f'{structure.capitalize()} Structure')
                    
                    # 误差棒
                    errors = [temp_stats.loc[t, 'se'] if not pd.isna(temp_stats.loc[t, 'se']) else 0 
                             for t in temperatures]
                    ax.errorbar(temperatures, means, yerr=errors, 
                               color=color, alpha=0.6, capsize=5, capthick=2)
                
                # 找出并标注最优点
                if len(genre_data) > 0:
                    best_idx = genre_data[dim].idxmax()
                    best_config = genre_data.loc[best_idx]
                    
                    ax.scatter(best_config['Temperature'], best_config[dim],
                              s=400, color='gold', marker='*', 
                              edgecolor='red', linewidth=3, zorder=10)
                    
                    # 添加最优点标注
                    ax.annotate(f'Optimal\n{best_config["Structure"]}@{best_config["Temperature"]}', 
                               xy=(best_config['Temperature'], best_config[dim]),
                               xytext=(0.02, 0.95), textcoords='axes fraction',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8),
                               arrowprops=dict(arrowstyle='->', color='red', lw=2),
                               fontsize=10, fontweight='bold')
                
                # 美化图表
                ax.set_title(f'{genre.capitalize()} - {dim_name}', fontsize=14, fontweight='bold')
                ax.set_xlabel('Temperature Setting')
                ax.set_ylabel(f'{dim_name} Score')
                ax.legend(loc='best')
                ax.grid(True, alpha=0.3)
                
                # 设置x轴刻度为实际的Temperature值
                ax.set_xticks(sorted(self.df['Temperature'].unique()))
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/discrete_interaction_effects.png', dpi=300, bbox_inches='tight')
        plt.close()
        return fig
    
    def create_discrete_heatmaps(self, save_dir):
        """创建离散参数热力图"""
        
        print("🔥 创建离散参数热力图...")
        
        genres = self.df['Genre'].unique()
        fig, axes = plt.subplots(2, len(genres), figsize=(6*len(genres), 10))
        
        if len(genres) == 1:
            axes = axes.reshape(-1, 1)
        
        for col, genre in enumerate(genres):
            genre_data = self.df[self.df['Genre'] == genre]
            
            # 上排：综合得分热力图
            ax1 = axes[0, col]
            heatmap_data = genre_data.pivot_table(values='综合得分', 
                                                 index='Structure', 
                                                 columns='Temperature', 
                                                 aggfunc='mean')
            
            if not heatmap_data.empty:
                sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlGn',
                           center=heatmap_data.values.mean(), ax=ax1, cbar_kws={'shrink': 0.8})
                
                # 标注最优点（红框）
                max_pos = np.unravel_index(heatmap_data.values.argmax(), heatmap_data.shape)
                from matplotlib.patches import Rectangle
                rect = Rectangle((max_pos[1], max_pos[0]), 1, 1, 
                               fill=False, edgecolor='red', linewidth=4)
                ax1.add_patch(rect)
                
                # 添加数值标注
                max_temp = heatmap_data.columns[max_pos[1]]
                max_struct = heatmap_data.index[max_pos[0]]
                max_score = heatmap_data.iloc[max_pos]
                ax1.text(max_pos[1]+0.5, max_pos[0]-0.15, 
                        f'Optimal\n{max_struct}@{max_temp}\n{max_score:.3f}',
                        ha='center', va='center',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", 
                                edgecolor="red", linewidth=2),
                        fontsize=10, fontweight='bold')
            
            ax1.set_title(f'{genre.capitalize()} - Comprehensive Score Distribution')
            
            # 下排：样本数量分布
            ax2 = axes[1, col]
            
            # 创建样本数量热力图
            stats_data = genre_data.groupby(['Structure', 'Temperature'])['综合得分'].agg(['count', 'std']).round(3)
            count_pivot = stats_data['count'].unstack(fill_value=0)
            
            if not count_pivot.empty:
                sns.heatmap(count_pivot, annot=True, fmt='d', cmap='Blues', 
                           ax=ax2, cbar_kws={'shrink': 0.8})
            
            ax2.set_title(f'{genre.capitalize()} - Sample Size Distribution')
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/discrete_parameter_heatmaps.png', dpi=300, bbox_inches='tight')
        plt.close()
        return fig
    
    def generate_discrete_4a_report(self, results, save_dir):
        """生成离散参数4A报告"""
        
        report = []
        report.append("# 🧪 实验4A：离散参数敏感性分析报告")
        report.append("## Experiment 4A: Discrete Parameter Sensitivity Analysis")
        report.append("### （基于54组实验的3×2×3参数组合分析）\n")
        
        # 总体发现
        report.append("## 🎯 核心发现汇总\n")
        
        overall_findings = []
        for genre, genre_data in results.items():
            best_improvement = 0
            best_config = ""
            best_effect_size = 0
            
            for structure, data in genre_data.items():
                if data['relative_improvement'] > best_improvement:
                    best_improvement = data['relative_improvement']
                    best_effect_size = data['effect_size']
                    best_config = f"{structure}@{data['optimal_temp']}"
            
            overall_findings.append({
                'genre': genre,
                'improvement': best_improvement,
                'effect_size': best_effect_size,
                'config': best_config
            })
        
        # 按改进程度排序
        overall_findings.sort(key=lambda x: x['improvement'], reverse=True)
        
        for i, finding in enumerate(overall_findings, 1):
            report.append(f"{i}. **{finding['genre'].capitalize()}**: 最大改进 **{finding['improvement']:.1f}%** "
                         f"(效应大小: {finding['effect_size']:.3f}, 最优: {finding['config']})")
        
        report.append("")
        
        # 详细分析
        for genre, genre_data in results.items():
            report.append(f"## 📚 {genre.capitalize()} Genre 详细分析\n")
            
            for structure, data in genre_data.items():
                report.append(f"### 🏗️ {structure.capitalize()} Structure\n")
                
                # 核心指标
                report.append(f"- **Temperature Effect Size**: {data['effect_size']:.4f}")
                report.append(f"- **Optimal Configuration**: Temperature = {data['optimal_temp']} (Score: {data['temperature_stats'].loc[data['optimal_temp'], 'mean']:.3f})")
                report.append(f"- **Performance Improvement**: {data['relative_improvement']:.1f}%")
                report.append(f"- **Sample Size**: {data['sample_size']}")
                
                if data['p_value'] is not None:
                    significance = "Statistically Significant" if data['p_value'] < 0.05 else "Not Significant"
                    report.append(f"- **Statistical Test**: {significance} (F={data['f_statistic']:.2f}, p={data['p_value']:.4f})")
                
                # 各Temperature表现
                report.append(f"\n**Temperature Settings Performance**:")
                for temp in sorted(data['temperature_stats'].index):
                    stats_row = data['temperature_stats'].loc[temp]
                    rank = "🥇" if temp == data['optimal_temp'] else "🥉" if temp == data['worst_temp'] else "🥈"
                    report.append(f"- {rank} Temperature {temp}: {stats_row['mean']:.3f} ± {stats_row['std']:.3f} (n={int(stats_row['count'])})")
                
                report.append("")
        
        # 跨类型比较
        report.append("## 🔍 Cross-Genre Comparison\n")
        
        # 找出最敏感的类型
        max_sensitivity = 0
        most_sensitive_genre = ""
        for genre, genre_data in results.items():
            for structure, data in genre_data.items():
                if data['effect_size'] > max_sensitivity:
                    max_sensitivity = data['effect_size']
                    most_sensitive_genre = f"{genre}-{structure}"
        
        report.append(f"- **Most Parameter-Sensitive Configuration**: {most_sensitive_genre} (Effect Size: {max_sensitivity:.4f})")
        
        # 统计显著性汇总
        significant_count = 0
        total_count = 0
        for genre, genre_data in results.items():
            for structure, data in genre_data.items():
                total_count += 1
                if data['p_value'] is not None and data['p_value'] < 0.05:
                    significant_count += 1
        
        report.append(f"- **Statistical Significance Rate**: {significant_count}/{total_count} configurations show significant temperature effects")
        
        # 方法论说明
        report.append("\n## 📊 Methodology")
        report.append("This analysis is based on 54 experiments with discrete parameter settings:")
        report.append(f"- **Temperature**: {sorted(self.df['Temperature'].unique())}")
        report.append(f"- **Structure**: {list(self.df['Structure'].unique())}")
        report.append(f"- **Genre**: {list(self.df['Genre'].unique())}")
        report.append("- **Analysis Method**: ANOVA and effect size calculation for parameter sensitivity quantification")
        report.append("- **Comprehensive Score**: Normalized average of Semantic Continuity, Diversity, Novelty, and Emotional Consistency")
        
        # 实践建议
        report.append("\n## 🎯 Practical Recommendations\n")
        
        for finding in overall_findings:
            if finding['improvement'] > 50:  # 只推荐改进幅度大的
                report.append(f"### {finding['genre'].capitalize()} Genre")
                report.append(f"- **Recommended Configuration**: {finding['config']}")
                report.append(f"- **Expected Improvement**: {finding['improvement']:.1f}%")
                report.append(f"- **Implementation Priority**: {'High' if finding['improvement'] > 200 else 'Medium'}")
                report.append("")
        
        # 保存报告
        with open(f'{save_dir}/Experiment4A_Discrete_Analysis_Report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        return '\n'.join(report)

def run_experiment4a_discrete_analysis(data_path, save_dir):
    """运行实验4A：离散参数敏感性分析"""
    
    print("🎯 开始实验4A：离散参数敏感性分析（54组实验）...\n")
    
    # 加载数据
    df = pd.read_csv(data_path)
    
    # 创建分析器
    analyzer = DiscreteParameterAnalyzer(df)
    
    # 执行分析
    results = analyzer.run_4a_discrete_analysis()
    
    # 创建可视化
    print("\n📊 创建可视化图表...")
    fig1 = analyzer.create_discrete_interaction_plot(save_dir)
    fig2 = analyzer.create_discrete_heatmaps(save_dir)
    
    # 生成报告
    report = analyzer.generate_discrete_4a_report(results, save_dir)
    
    print("\n✅ 实验4A离散参数分析完成！生成的文件:")
    print(f"  📊 {save_dir}/discrete_interaction_effects.png - 离散参数交互图") 
    print(f"  🔥 {save_dir}/discrete_parameter_heatmaps.png - 离散参数热力图")
    print(f"  📋 {save_dir}/Experiment4A_Discrete_Analysis_Report.md - 详细分析报告")
    
    print("\n🎯 这个分析完美适配您的实验设置：3个Temperature × 2个Structure × 3个Genre")
    
    return results, report

def main():
    """主函数"""
    data_path = "/Users/haha/Story/metrics_master_clean.csv"
    save_dir = "/Users/haha/Story/AAA/stage2_parameter_effects_analysis"
    
    results, report = run_experiment4a_discrete_analysis(data_path, save_dir)
    
    print("\n🎯 实验4A快速总结:")
    print("=" * 50)
    
    # 显示最重要的发现
    max_improvement = 0
    best_genre = ""
    for genre, genre_data in results.items():
        for structure, data in genre_data.items():
            if data['relative_improvement'] > max_improvement:
                max_improvement = data['relative_improvement']
                best_genre = f"{genre}-{structure}@{data['optimal_temp']}"
    
    print(f"🏆 最大参数效应: {best_genre} (+{max_improvement:.1f}%)")

if __name__ == "__main__":
    main()
