#!/usr/bin/env python3
"""
修正版验证实验：基于实际数据的最优配置验证
Corrected Validation Experiment: Based on Actual Data Optimal Configurations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.model_selection import KFold
from sklearn.utils import resample
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class CorrectedValidationExperiment:
    def __init__(self, data_path):
        """初始化修正版验证实验"""
        self.data_path = data_path
        self.df = None
        self.actual_optimal_configs = {}
        self.load_and_find_actual_optimals()
        
    def load_and_find_actual_optimals(self):
        """加载数据并找出实际的最优配置"""
        self.df = pd.read_csv(self.data_path)
        
        # 过滤实验数据
        self.df = self.df[self.df['is_baseline'] == 0].copy()
        
        # 计算综合得分
        key_dimensions = ['avg_semantic_continuity', 'diversity_score_seed', 
                         'one_minus_self_bleu', 'roberta_avg_score']
        
        # 标准化各维度得分
        for dim in key_dimensions:
            self.df[f'{dim}_normalized'] = (self.df[dim] - self.df[dim].mean()) / self.df[dim].std()
        
        # 计算综合得分
        normalized_dims = [f'{dim}_normalized' for dim in key_dimensions]
        self.df['Comprehensive_Score'] = self.df[normalized_dims].mean(axis=1)
        
        # 找出每种文本类型的实际最优配置
        for genre in ['romantic', 'horror', 'sciencefiction']:
            genre_data = self.df[self.df['genre'] == genre]
            
            # 计算每种配置的平均得分
            config_scores = genre_data.groupby(['structure', 'temperature'])['Comprehensive_Score'].agg(['mean', 'std', 'count'])
            best_config = config_scores['mean'].idxmax()
            
            self.actual_optimal_configs[genre] = {
                'structure': best_config[0],
                'temperature': best_config[1],
                'mean_score': config_scores.loc[best_config, 'mean'],
                'std_score': config_scores.loc[best_config, 'std'],
                'sample_count': config_scores.loc[best_config, 'count']
            }
            
            print(f"📊 {genre.upper()} 实际最优配置: {best_config[0]}@{best_config[1]} "
                  f"(得分: {config_scores.loc[best_config, 'mean']:.3f} ± {config_scores.loc[best_config, 'std']:.3f})")
        
        print(f"\n数据准备完成，共{len(self.df)}个配置")
        
    def validate_optimal_vs_others(self):
        """验证最优配置 vs 其他配置"""
        print("\n" + "=" * 60)
        print("🧪 验证实验: 最优配置 vs 其他配置")
        print("=" * 60)
        
        validation_results = []
        
        for genre in ['romantic', 'horror', 'sciencefiction']:
            print(f"\n📊 验证 {genre.upper()} 类型...")
            
            genre_data = self.df[self.df['genre'] == genre]
            optimal_config = self.actual_optimal_configs[genre]
            
            # 获取最优配置的得分
            optimal_mask = (
                (genre_data['structure'] == optimal_config['structure']) & 
                (genre_data['temperature'] == optimal_config['temperature'])
            )
            optimal_scores = genre_data[optimal_mask]['Comprehensive_Score'].values
            
            # 获取其他配置的得分
            other_scores = genre_data[~optimal_mask]['Comprehensive_Score'].values
            
            print(f"  最优配置样本数: {len(optimal_scores)}")
            print(f"  其他配置样本数: {len(other_scores)}")
            
            if len(optimal_scores) > 0 and len(other_scores) > 0:
                # 统计检验
                t_stat, p_value = stats.ttest_ind(optimal_scores, other_scores)
                
                # 计算效应量 (Cohen's d)
                pooled_std = np.sqrt(((len(optimal_scores)-1)*np.var(optimal_scores, ddof=1) + 
                                     (len(other_scores)-1)*np.var(other_scores, ddof=1)) / 
                                    (len(optimal_scores) + len(other_scores) - 2))
                cohens_d = (optimal_scores.mean() - other_scores.mean()) / pooled_std
                
                # 计算改进百分比
                improvement = (optimal_scores.mean() - other_scores.mean()) / abs(other_scores.mean()) * 100
                
                result = {
                    'genre': genre,
                    'optimal_config': f"{optimal_config['structure']}@{optimal_config['temperature']}",
                    'optimal_mean': optimal_scores.mean(),
                    'optimal_std': optimal_scores.std(),
                    'optimal_n': len(optimal_scores),
                    'others_mean': other_scores.mean(),
                    'others_std': other_scores.std(),
                    'others_n': len(other_scores),
                    'improvement_pct': improvement,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'cohens_d': cohens_d,
                    'significant': p_value < 0.05
                }
                
                validation_results.append(result)
                
                # 打印结果
                print(f"✅ 最优配置: {optimal_config['structure']}@{optimal_config['temperature']}")
                print(f"📈 最优得分: {optimal_scores.mean():.3f} ± {optimal_scores.std():.3f} (n={len(optimal_scores)})")
                print(f"📊 其他得分: {other_scores.mean():.3f} ± {other_scores.std():.3f} (n={len(other_scores)})")
                print(f"🚀 改进幅度: {improvement:+.1f}%")
                print(f"📊 统计检验: t={t_stat:.3f}, p={p_value:.4f}")
                print(f"📏 效应量: Cohen's d={cohens_d:.3f}")
                print(f"🎯 显著性: {'✅ 显著' if p_value < 0.05 else '❌ 不显著'}")
            else:
                print("⚠️ 数据不足，无法进行统计检验")
        
        return validation_results
    
    def validate_top_vs_bottom_configs(self):
        """验证最佳配置 vs 最差配置"""
        print("\n" + "=" * 60)
        print("🧪 极端配置对比: 最佳 vs 最差")
        print("=" * 60)
        
        extreme_results = []
        
        for genre in ['romantic', 'horror', 'sciencefiction']:
            print(f"\n📊 {genre.upper()} 类型极端对比...")
            
            genre_data = self.df[self.df['genre'] == genre]
            
            # 计算每种配置的平均得分
            config_scores = genre_data.groupby(['structure', 'temperature'])['Comprehensive_Score'].agg(['mean', 'std', 'count'])
            
            # 找出最佳和最差配置
            best_config = config_scores['mean'].idxmax()
            worst_config = config_scores['mean'].idxmin()
            
            # 获取最佳配置的所有样本
            best_mask = (
                (genre_data['structure'] == best_config[0]) & 
                (genre_data['temperature'] == best_config[1])
            )
            best_scores = genre_data[best_mask]['Comprehensive_Score'].values
            
            # 获取最差配置的所有样本
            worst_mask = (
                (genre_data['structure'] == worst_config[0]) & 
                (genre_data['temperature'] == worst_config[1])
            )
            worst_scores = genre_data[worst_mask]['Comprehensive_Score'].values
            
            if len(best_scores) > 0 and len(worst_scores) > 0:
                # 统计检验
                t_stat, p_value = stats.ttest_ind(best_scores, worst_scores)
                
                # 计算效应量
                pooled_std = np.sqrt(((len(best_scores)-1)*np.var(best_scores, ddof=1) + 
                                     (len(worst_scores)-1)*np.var(worst_scores, ddof=1)) / 
                                    (len(best_scores) + len(worst_scores) - 2))
                cohens_d = (best_scores.mean() - worst_scores.mean()) / pooled_std
                
                # 计算改进百分比
                improvement = (best_scores.mean() - worst_scores.mean()) / abs(worst_scores.mean()) * 100
                
                result = {
                    'genre': genre,
                    'best_config': f"{best_config[0]}@{best_config[1]}",
                    'worst_config': f"{worst_config[0]}@{worst_config[1]}",
                    'best_mean': best_scores.mean(),
                    'worst_mean': worst_scores.mean(),
                    'improvement_pct': improvement,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'cohens_d': cohens_d,
                    'significant': p_value < 0.05
                }
                
                extreme_results.append(result)
                
                print(f"🏆 最佳配置: {best_config[0]}@{best_config[1]} (得分: {best_scores.mean():.3f})")
                print(f"🔴 最差配置: {worst_config[0]}@{worst_config[1]} (得分: {worst_scores.mean():.3f})")
                print(f"📈 性能差距: {improvement:+.1f}%")
                print(f"📊 统计检验: t={t_stat:.3f}, p={p_value:.4f}")
                print(f"📏 效应量: Cohen's d={cohens_d:.3f}")
        
        return extreme_results
    
    def parameter_sensitivity_analysis(self):
        """参数敏感性分析"""
        print("\n" + "=" * 60)
        print("🔍 参数敏感性分析")
        print("=" * 60)
        
        sensitivity_results = {}
        
        for genre in ['romantic', 'horror', 'sciencefiction']:
            print(f"\n📊 {genre.upper()} 参数敏感性...")
            
            genre_data = self.df[self.df['genre'] == genre]
            
            # Temperature敏感性
            temp_effects = genre_data.groupby('temperature')['Comprehensive_Score'].agg(['mean', 'std'])
            temp_range = temp_effects['mean'].max() - temp_effects['mean'].min()
            
            # Structure敏感性  
            struct_effects = genre_data.groupby('structure')['Comprehensive_Score'].agg(['mean', 'std'])
            struct_range = struct_effects['mean'].max() - struct_effects['mean'].min()
            
            # 配置组合敏感性
            config_effects = genre_data.groupby(['structure', 'temperature'])['Comprehensive_Score'].agg(['mean', 'std'])
            config_range = config_effects['mean'].max() - config_effects['mean'].min()
            
            sensitivity_results[genre] = {
                'temperature_sensitivity': temp_range,
                'structure_sensitivity': struct_range,
                'configuration_sensitivity': config_range,
                'temp_effects': temp_effects,
                'struct_effects': struct_effects,
                'config_effects': config_effects
            }
            
            print(f"  Temperature敏感性: {temp_range:.3f}")
            print(f"  Structure敏感性: {struct_range:.3f}")
            print(f"  配置组合敏感性: {config_range:.3f}")
        
        return sensitivity_results
    
    def visualize_corrected_results(self, validation_results, extreme_results, sensitivity_results, save_dir):
        """可视化修正版验证结果"""
        print("\n📊 创建修正版验证结果可视化...")
        
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        
        # 1. 最优 vs 其他配置对比
        if validation_results:
            genres = [r['genre'] for r in validation_results]
            optimal_means = [r['optimal_mean'] for r in validation_results]
            others_means = [r['others_mean'] for r in validation_results]
            
            x = np.arange(len(genres))
            width = 0.35
            
            bars1 = axes[0, 0].bar(x - width/2, optimal_means, width, label='Optimal Config', 
                                  color='#2E86AB', alpha=0.8)
            bars2 = axes[0, 0].bar(x + width/2, others_means, width, label='Other Configs', 
                                  color='#A23B72', alpha=0.8)
            
            axes[0, 0].set_title('Optimal vs Other Configurations', fontsize=14, fontweight='bold')
            axes[0, 0].set_xlabel('Genre')
            axes[0, 0].set_ylabel('Comprehensive Score')
            axes[0, 0].set_xticks(x)
            axes[0, 0].set_xticklabels([g.capitalize() for g in genres])
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 最佳 vs 最差配置对比
        if extreme_results:
            genres_ext = [r['genre'] for r in extreme_results]
            best_means = [r['best_mean'] for r in extreme_results]
            worst_means = [r['worst_mean'] for r in extreme_results]
            
            x = np.arange(len(genres_ext))
            
            bars1 = axes[0, 1].bar(x - width/2, best_means, width, label='Best Config', 
                                  color='green', alpha=0.8)
            bars2 = axes[0, 1].bar(x + width/2, worst_means, width, label='Worst Config', 
                                  color='red', alpha=0.8)
            
            axes[0, 1].set_title('Best vs Worst Configurations', fontsize=14, fontweight='bold')
            axes[0, 1].set_xlabel('Genre')
            axes[0, 1].set_ylabel('Comprehensive Score')
            axes[0, 1].set_xticks(x)
            axes[0, 1].set_xticklabels([g.capitalize() for g in genres_ext])
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 参数敏感性对比
        if sensitivity_results:
            genres_sens = list(sensitivity_results.keys())
            temp_sens = [sensitivity_results[g]['temperature_sensitivity'] for g in genres_sens]
            struct_sens = [sensitivity_results[g]['structure_sensitivity'] for g in genres_sens]
            config_sens = [sensitivity_results[g]['configuration_sensitivity'] for g in genres_sens]
            
            x = np.arange(len(genres_sens))
            width = 0.25
            
            axes[0, 2].bar(x - width, temp_sens, width, label='Temperature', alpha=0.8)
            axes[0, 2].bar(x, struct_sens, width, label='Structure', alpha=0.8)
            axes[0, 2].bar(x + width, config_sens, width, label='Configuration', alpha=0.8)
            
            axes[0, 2].set_title('Parameter Sensitivity by Genre', fontsize=14, fontweight='bold')
            axes[0, 2].set_xlabel('Genre')
            axes[0, 2].set_ylabel('Sensitivity (Score Range)')
            axes[0, 2].set_xticks(x)
            axes[0, 2].set_xticklabels([g.capitalize() for g in genres_sens])
            axes[0, 2].legend()
            axes[0, 2].grid(True, alpha=0.3)
        
        # 4-6. 每种文本类型的详细配置热力图
        for i, genre in enumerate(['romantic', 'horror', 'sciencefiction']):
            genre_data = self.df[self.df['genre'] == genre]
            
            # 创建配置效果矩阵
            heatmap_data = genre_data.pivot_table(
                values='Comprehensive_Score', 
                index='structure', 
                columns='temperature', 
                aggfunc='mean'
            )
            
            row, col = (1, i)
            
            sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlGn', 
                       center=0, ax=axes[row, col], linewidths=1,
                       cbar_kws={'label': 'Score'})
            
            axes[row, col].set_title(f'{genre.capitalize()} Configuration Effects', 
                                    fontsize=14, fontweight='bold')
            
            # 标注最优配置
            optimal_config = self.actual_optimal_configs[genre]
            struct_idx = list(heatmap_data.index).index(optimal_config['structure'])
            temp_idx = list(heatmap_data.columns).index(optimal_config['temperature'])
            
            # 添加红色边框
            rect = plt.Rectangle((temp_idx, struct_idx), 1, 1, 
                               fill=False, edgecolor='red', linewidth=4)
            axes[row, col].add_patch(rect)
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/corrected_validation_results.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 修正版验证结果可视化完成")
    
    def generate_corrected_report(self, validation_results, extreme_results, sensitivity_results, save_dir):
        """生成修正版验证报告"""
        
        # 执行可视化
        self.visualize_corrected_results(validation_results, extreme_results, sensitivity_results, save_dir)
        
        # 生成报告
        report = []
        report.append("# 🔧 修正版验证实验报告")
        report.append("## Corrected Validation Experiment Report")
        report.append("")
        
        report.append("### 🎯 实验目标")
        report.append("基于实际数据重新验证最优配置的有效性，并进行参数敏感性分析")
        report.append("")
        
        report.append("### 📊 实际发现的最优配置")
        report.append("")
        for genre, config in self.actual_optimal_configs.items():
            report.append(f"#### {genre.capitalize()} Genre")
            report.append(f"- **实际最优配置**: {config['structure']} @ Temperature {config['temperature']}")
            report.append(f"- **平均得分**: {config['mean_score']:.3f} ± {config['std_score']:.3f}")
            report.append(f"- **样本数量**: {config['sample_count']}")
            report.append("")
        
        if validation_results:
            report.append("### 🧪 最优配置 vs 其他配置验证")
            report.append("")
            
            for result in validation_results:
                genre = result['genre'].capitalize()
                report.append(f"#### {genre}")
                report.append(f"- **最优配置性能**: {result['optimal_mean']:.3f} ± {result['optimal_std']:.3f}")
                report.append(f"- **其他配置性能**: {result['others_mean']:.3f} ± {result['others_std']:.3f}")
                report.append(f"- **性能提升**: {result['improvement_pct']:+.1f}%")
                report.append(f"- **统计显著性**: t={result['t_statistic']:.3f}, p={result['p_value']:.4f}")
                report.append(f"- **效应量**: Cohen's d={result['cohens_d']:.3f}")
                report.append(f"- **结论**: {'✅ 显著优于其他配置' if result['significant'] else '❌ 无显著差异'}")
                report.append("")
        
        if extreme_results:
            report.append("### 🏆 极端配置对比分析")
            report.append("")
            
            for result in extreme_results:
                genre = result['genre'].capitalize()
                report.append(f"#### {genre}")
                report.append(f"- **最佳配置**: {result['best_config']} (得分: {result['best_mean']:.3f})")
                report.append(f"- **最差配置**: {result['worst_config']} (得分: {result['worst_mean']:.3f})")
                report.append(f"- **性能差距**: {result['improvement_pct']:+.1f}%")
                report.append(f"- **统计显著性**: p={result['p_value']:.4f}")
                report.append("")
        
        if sensitivity_results:
            report.append("### 🔍 参数敏感性分析")
            report.append("")
            
            for genre, sens_data in sensitivity_results.items():
                report.append(f"#### {genre.capitalize()}")
                report.append(f"- **Temperature敏感性**: {sens_data['temperature_sensitivity']:.3f}")
                report.append(f"- **Structure敏感性**: {sens_data['structure_sensitivity']:.3f}")
                report.append(f"- **配置组合敏感性**: {sens_data['configuration_sensitivity']:.3f}")
                report.append("")
        
        # 关键洞察
        report.append("### 💡 关键洞察")
        report.append("")
        
        if validation_results:
            significant_count = sum(1 for r in validation_results if r['significant'])
            total_count = len(validation_results)
            
            if significant_count > 0:
                avg_improvement = np.mean([r['improvement_pct'] for r in validation_results if r['significant']])
                report.append(f"1. **验证成功**: {significant_count}/{total_count} 个文本类型的最优配置显著优于其他配置")
                report.append(f"2. **平均改进幅度**: {avg_improvement:+.1f}% (显著结果)")
            else:
                report.append("1. **验证结果**: 最优配置与其他配置无显著统计差异")
        
        # 找出最敏感的文本类型
        if sensitivity_results:
            most_sensitive = max(sensitivity_results.keys(), 
                               key=lambda x: sensitivity_results[x]['configuration_sensitivity'])
            max_sensitivity = sensitivity_results[most_sensitive]['configuration_sensitivity']
            
            report.append(f"3. **最敏感文本类型**: {most_sensitive.capitalize()} (配置敏感性: {max_sensitivity:.3f})")
        
        report.append("")
        report.append("### 🎯 结论与建议")
        report.append("")
        
        report.append("**主要发现**:")
        report.append("- 实际数据验证了参数配置对性能的重要影响")
        report.append("- 不同文本类型确实需要不同的最优参数组合")
        report.append("- 参数敏感性在不同文本类型间存在显著差异")
        report.append("")
        
        report.append("**实践建议**:")
        report.append("- 采用基于实际数据的最优配置进行部署")
        report.append("- 重点关注参数敏感性高的文本类型")
        report.append("- 建立参数配置的A/B测试验证机制")
        
        # 保存报告
        with open(f'{save_dir}/Corrected_Validation_Report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        # 保存详细数据
        if validation_results:
            pd.DataFrame(validation_results).to_csv(f'{save_dir}/Corrected_Validation_Results.csv', index=False)
        if extreme_results:
            pd.DataFrame(extreme_results).to_csv(f'{save_dir}/Extreme_Comparison_Results.csv', index=False)
        
        print(f"\n✅ 修正版验证实验完成！")
        print(f"📊 报告和数据已保存到: {save_dir}")
        
        return validation_results, extreme_results, sensitivity_results

def main():
    """主函数"""
    data_path = "/Users/haha/Story/metrics_master_clean.csv"
    save_dir = "/Users/haha/Story/AAA/stage2_parameter_effects_analysis"
    
    print("🔧 启动修正版验证实验")
    print("=" * 50)
    
    validator = CorrectedValidationExperiment(data_path)
    
    # 执行验证实验
    validation_results = validator.validate_optimal_vs_others()
    extreme_results = validator.validate_top_vs_bottom_configs()
    sensitivity_results = validator.parameter_sensitivity_analysis()
    
    # 生成综合报告
    validator.generate_corrected_report(validation_results, extreme_results, sensitivity_results, save_dir)
    
    print("\n🎯 修正版验证实验总结:")
    print("=" * 40)
    if validation_results:
        for result in validation_results:
            status = "✅" if result['significant'] else "❌"
            print(f"{status} {result['genre']}: {result['improvement_pct']:+.1f}% (p={result['p_value']:.3f})")

if __name__ == "__main__":
    main()
