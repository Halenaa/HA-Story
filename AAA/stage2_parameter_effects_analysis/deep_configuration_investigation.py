#!/usr/bin/env python3
"""
参数配置深度调查 - 找出为什么某些配置评分特别高
Deep Configuration Investigation - Finding Why Certain Configs Score Higher

目标：发现被整体统计掩盖的隐藏参数效应模式
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class DeepConfigurationInvestigator:
    def __init__(self, data_path):
        """初始化深度调查器"""
        self.data_path = data_path
        self.df = None
        self.load_and_prepare_data()
        
    def load_and_prepare_data(self):
        """加载和预处理数据"""
        self.df = pd.read_csv(self.data_path)
        
        # 过滤实验数据
        self.df = self.df[self.df['is_baseline'] == 0].copy()
        
        # 计算综合得分
        key_dimensions = ['avg_semantic_continuity', 'diversity_score_seed', 
                         'one_minus_self_bleu', 'roberta_avg_score']
        
        # 标准化各维度得分（避免量纲影响）
        for dim in key_dimensions:
            self.df[f'{dim}_normalized'] = (self.df[dim] - self.df[dim].mean()) / self.df[dim].std()
        
        # 计算综合得分（标准化后）
        normalized_dims = [f'{dim}_normalized' for dim in key_dimensions]
        self.df['综合得分'] = self.df[normalized_dims].mean(axis=1)
        
        # 添加原始维度的中文名
        self.df['语义连贯性'] = self.df['avg_semantic_continuity']
        self.df['多样性'] = self.df['diversity_score_seed']
        self.df['独创性'] = self.df['one_minus_self_bleu']
        self.df['情感一致性'] = self.df['roberta_avg_score']
        self.df['流畅性'] = 1 / (1 + self.df['pseudo_ppl'])  # 转换为正向指标
        
        print(f"数据准备完成，共{len(self.df)}个配置")
        print(f"综合得分范围: {self.df['综合得分'].min():.3f} - {self.df['综合得分'].max():.3f}")
        
    def find_top_configurations(self, top_k=10):
        """🏆 识别各维度得分最高的配置"""
        print("=" * 60)
        print("🏆 最优配置识别分析")
        print("=" * 60)
        
        # 找出top配置
        top_configs = self.df.nlargest(top_k, '综合得分')
        
        print(f"\n🏆 表现最佳的{top_k}个配置：")
        display_cols = ['structure', 'temperature', 'genre', '综合得分', 
                       '语义连贯性', '多样性', '独创性', '情感一致性']
        print(top_configs[display_cols].round(3))
        
        # 统计最优配置的参数分布
        print(f"\n📈 最优配置中的参数偏好：")
        print("Structure分布：")
        print(top_configs['structure'].value_counts())
        print("\nTemperature分布：")
        print(top_configs['temperature'].value_counts())
        print("\nGenre分布：")
        print(top_configs['genre'].value_counts())
        
        # 计算参数偏好强度
        total_configs = len(self.df)
        struct_bias = self.calculate_parameter_bias(top_configs, 'structure', total_configs)
        temp_bias = self.calculate_parameter_bias(top_configs, 'temperature', total_configs)
        genre_bias = self.calculate_parameter_bias(top_configs, 'genre', total_configs)
        
        print(f"\n🎯 参数偏好强度（偏离随机分布的程度）：")
        print(f"Structure偏好强度: {struct_bias:.2f}")
        print(f"Temperature偏好强度: {temp_bias:.2f}")
        print(f"Genre偏好强度: {genre_bias:.2f}")
        
        return top_configs
    
    def calculate_parameter_bias(self, top_configs, param, total_configs):
        """计算参数偏好强度"""
        observed = top_configs[param].value_counts()
        total_dist = self.df[param].value_counts()
        expected = total_dist / total_configs * len(top_configs)
        
        # 计算卡方统计量作为偏好强度
        chi2_stat = sum((observed - expected)**2 / expected)
        return chi2_stat
    
    def compare_extremes(self):
        """🔍 对比最优和最差配置的参数特征"""
        print("\n" + "=" * 60)
        print("🔍 极端配置对比分析")
        print("=" * 60)
        
        top_10 = self.df.nlargest(10, '综合得分')
        bottom_10 = self.df.nsmallest(10, '综合得分')
        
        print("🔴 最差配置特征：")
        print(f"平均综合得分: {bottom_10['综合得分'].mean():.3f}")
        print(f"Structure偏好: {bottom_10['structure'].mode().iloc[0]}")
        print(f"平均Temperature: {bottom_10['temperature'].astype(float).mean():.2f}")
        print(f"Genre分布: {dict(bottom_10['genre'].value_counts())}")
        
        print("\n🟢 最优配置特征：")
        print(f"平均综合得分: {top_10['综合得分'].mean():.3f}")
        print(f"Structure偏好: {top_10['structure'].mode().iloc[0]}")
        print(f"平均Temperature: {top_10['temperature'].astype(float).mean():.2f}")
        print(f"Genre分布: {dict(top_10['genre'].value_counts())}")
        
        # 统计显著性检验
        print(f"\n📊 统计检验结果：")
        
        # Temperature差异检验
        top_temps = top_10['temperature'].astype(float)
        bottom_temps = bottom_10['temperature'].astype(float)
        t_stat, t_p = stats.ttest_ind(top_temps, bottom_temps)
        print(f"Temperature差异: t={t_stat:.3f}, p={t_p:.3f}")
        
        # Structure差异检验（卡方）
        top_struct = top_10['structure'].value_counts()
        bottom_struct = bottom_10['structure'].value_counts()
        chi2_stat, chi2_p = stats.chi2_contingency([top_struct, bottom_struct])[:2]
        print(f"Structure差异: χ²={chi2_stat:.3f}, p={chi2_p:.3f}")
        
        return top_10, bottom_10
    
    def genre_specific_analysis(self):
        """🎭 分文本类型的参数效应分析"""
        print("\n" + "=" * 60)
        print("🎭 分文本类型参数效应分析")
        print("=" * 60)
        
        genre_results = {}
        
        for genre in self.df['genre'].unique():
            print(f"\n📚 === {genre.upper()} 类型分析 ===")
            genre_data = self.df[self.df['genre'] == genre].copy()
            
            # 找出最佳和最差配置
            best_idx = genre_data['综合得分'].idxmax()
            worst_idx = genre_data['综合得分'].idxmin()
            best_config = genre_data.loc[best_idx]
            worst_config = genre_data.loc[worst_idx]
            
            print(f"🏆 最佳配置: Structure={best_config['structure']}, Temp={best_config['temperature']}, 得分={best_config['综合得分']:.3f}")
            print(f"🔴 最差配置: Structure={worst_config['structure']}, Temp={worst_config['temperature']}, 得分={worst_config['综合得分']:.3f}")
            
            # 参数效应分析
            temp_effect = genre_data.groupby('temperature')['综合得分'].agg(['mean', 'std', 'count'])
            struct_effect = genre_data.groupby('structure')['综合得分'].agg(['mean', 'std', 'count'])
            
            print(f"\n🌡️ Temperature效应:")
            print(temp_effect.round(3))
            temp_range = temp_effect['mean'].max() - temp_effect['mean'].min()
            print(f"Temperature效应大小: {temp_range:.3f}")
            
            print(f"\n🏗️ Structure效应:")
            print(struct_effect.round(3))
            struct_range = struct_effect['mean'].max() - struct_effect['mean'].min()
            print(f"Structure效应大小: {struct_range:.3f}")
            
            # 保存结果
            genre_results[genre] = {
                'best_config': best_config,
                'worst_config': worst_config,
                'temp_effect_size': temp_range,
                'struct_effect_size': struct_range,
                'temp_effects': temp_effect,
                'struct_effects': struct_effect
            }
            
            # 寻找最优参数组合
            best_temp = temp_effect.loc[temp_effect['mean'].idxmax(), 'mean']
            best_struct = struct_effect.loc[struct_effect['mean'].idxmax(), 'mean']
            
            print(f"\n🎯 {genre}类型的最优参数:")
            print(f"最优Temperature: {temp_effect['mean'].idxmax()} (得分: {best_temp:.3f})")
            print(f"最优Structure: {struct_effect['mean'].idxmax()} (得分: {best_struct:.3f})")
        
        return genre_results
    
    def find_interaction_patterns(self):
        """🎯 寻找隐藏的交互模式"""
        print("\n" + "=" * 60)
        print("🎯 隐藏交互模式发现")
        print("=" * 60)
        
        # 创建所有可能的参数组合分析
        interactions = self.df.groupby(['structure', 'temperature', 'genre'])['综合得分'].agg([
            'mean', 'std', 'count', 'min', 'max'
        ]).round(3)
        
        # 计算效应大小（最大值-最小值）
        interactions['range'] = interactions['max'] - interactions['min']
        
        # 找出方差最大的组合（说明参数敏感）
        high_variance = interactions.nlargest(5, 'std')
        print("🎲 参数敏感的配置组合（高方差）：")
        print(high_variance)
        
        # 找出均值最高的组合
        best_combinations = interactions.nlargest(5, 'mean')
        print("\n🏆 表现最佳的参数组合：")
        print(best_combinations)
        
        # 找出效应范围最大的组合
        high_range = interactions.nlargest(5, 'range')
        print("\n📊 效应范围最大的组合（参数影响最显著）：")
        print(high_range)
        
        # 检查各Genre的最优Temperature
        temp_analysis = self.df.groupby(['genre', 'temperature'])['综合得分'].mean().unstack()
        print("\n🌡️ 各文本类型的最优Temperature：")
        for genre in temp_analysis.index:
            best_temp = temp_analysis.loc[genre].idxmax()
            best_score = temp_analysis.loc[genre].max()
            worst_temp = temp_analysis.loc[genre].idxmin()
            worst_score = temp_analysis.loc[genre].min()
            temp_effect = best_score - worst_score
            print(f"{genre}: 最优Temp={best_temp}(得分{best_score:.3f}) vs 最差Temp={worst_temp}(得分{worst_score:.3f}), 效应={temp_effect:.3f}")
        
        # 检查各Genre的最优Structure
        struct_analysis = self.df.groupby(['genre', 'structure'])['综合得分'].mean().unstack()
        print("\n🏗️ 各文本类型的最优Structure：")
        for genre in struct_analysis.index:
            best_struct = struct_analysis.loc[genre].idxmax()
            best_score = struct_analysis.loc[genre].max()
            worst_struct = struct_analysis.loc[genre].idxmin()
            worst_score = struct_analysis.loc[genre].min()
            struct_effect = best_score - worst_score
            print(f"{genre}: 最优Struct={best_struct}(得分{best_score:.3f}) vs 最差Struct={worst_struct}(得分{worst_score:.3f}), 效应={struct_effect:.3f}")
        
        return interactions, temp_analysis, struct_analysis
    
    def visualize_hidden_effects(self, save_dir):
        """📊 可视化隐藏的参数效应"""
        print("\n" + "=" * 60)
        print("📊 可视化隐藏效应")
        print("=" * 60)
        
        # 1. 分Genre的参数效应箱线图
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        genres = self.df['genre'].unique()
        
        # 各Genre下的Temperature效应
        for i, genre in enumerate(genres):
            genre_data = self.df[self.df['genre'] == genre]
            sns.boxplot(data=genre_data, x='temperature', y='综合得分', ax=axes[0, i])
            axes[0, i].set_title(f'{genre} - Temperature效应')
            axes[0, i].tick_params(axis='x', rotation=45)
            
            # 添加均值线
            means = genre_data.groupby('temperature')['综合得分'].mean()
            for j, (temp, mean_val) in enumerate(means.items()):
                axes[0, i].axhline(y=mean_val, color='red', linestyle='--', alpha=0.7)
        
        # 各Genre下的Structure效应
        for i, genre in enumerate(genres):
            genre_data = self.df[self.df['genre'] == genre]
            sns.boxplot(data=genre_data, x='structure', y='综合得分', ax=axes[1, i])
            axes[1, i].set_title(f'{genre} - Structure效应')
            axes[1, i].tick_params(axis='x', rotation=45)
            
            # 添加均值线
            means = genre_data.groupby('structure')['综合得分'].mean()
            for j, (struct, mean_val) in enumerate(means.items()):
                axes[1, i].axhline(y=mean_val, color='red', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/hidden_parameter_effects.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 参数组合效果热力图
        pivot_table = self.df.pivot_table(values='综合得分', 
                                        index=['genre', 'structure'], 
                                        columns='temperature', 
                                        aggfunc='mean')
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_table, annot=True, cmap='RdYlGn', center=pivot_table.mean().mean(),
                   fmt='.3f', cbar_kws={'label': '综合得分'})
        plt.title('参数组合效果热力图\n(绿色=高分，红色=低分)', fontsize=14)
        plt.xlabel('Temperature')
        plt.ylabel('Genre × Structure')
        plt.tight_layout()
        plt.savefig(f'{save_dir}/parameter_combination_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 最优配置雷达图
        top_5 = self.df.nlargest(5, '综合得分')
        
        dimensions = ['语义连贯性', '多样性', '独创性', '情感一致性', '流畅性']
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, (idx, config) in enumerate(top_5.iterrows()):
            values = [config[dim] for dim in dimensions]
            values += values[:1]  # 闭合图形
            
            ax.plot(angles, values, 'o-', linewidth=2, label=f'#{i+1}: {config["structure"]}-{config["temperature"]}-{config["genre"]}', color=colors[i])
            ax.fill(angles, values, alpha=0.1, color=colors[i])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions)
        ax.set_ylim(0, 1)
        ax.set_title('Top 5 配置的维度表现雷达图', size=16, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/top_configurations_radar.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ 可视化图表已保存到 {save_dir}")
    
    def generate_investigation_report(self, save_dir):
        """生成深度调查报告"""
        
        # 运行所有分析
        top_configs = self.find_top_configurations()
        top_10, bottom_10 = self.compare_extremes()
        genre_results = self.genre_specific_analysis()
        interactions, temp_analysis, struct_analysis = self.find_interaction_patterns()
        self.visualize_hidden_effects(save_dir)
        
        # 生成报告
        report = []
        report.append("# 参数配置深度调查报告")
        report.append("## Deep Configuration Investigation Report")
        report.append("")
        report.append("### 🎯 调查目标")
        report.append("发现被整体统计分析掩盖的隐藏参数效应模式")
        report.append("")
        
        # 核心发现
        report.append("### 🔍 核心发现")
        report.append("")
        
        # 最优配置模式
        report.append("#### 1. 最优配置模式")
        top_struct = top_configs['structure'].mode().iloc[0]
        top_temp_mean = top_configs['temperature'].astype(float).mean()
        top_genre = top_configs['genre'].mode().iloc[0]
        
        report.append(f"- **最优Structure偏好**: {top_struct}")
        report.append(f"- **最优Temperature均值**: {top_temp_mean:.2f}")
        report.append(f"- **最优Genre偏好**: {top_genre}")
        report.append("")
        
        # 分类型效应
        report.append("#### 2. 分文本类型的隐藏效应")
        for genre, results in genre_results.items():
            report.append(f"**{genre.upper()}类型:**")
            report.append(f"- Temperature效应大小: {results['temp_effect_size']:.3f}")
            report.append(f"- Structure效应大小: {results['struct_effect_size']:.3f}")
            
            # 找出最优参数
            best_temp = results['temp_effects']['mean'].idxmax()
            best_struct = results['struct_effects']['mean'].idxmax()
            report.append(f"- 最优参数组合: {best_struct} + Temperature {best_temp}")
            report.append("")
        
        # 关键洞察
        report.append("### 💡 关键洞察")
        report.append("")
        report.append("1. **参数效应确实存在但被掩盖**: 在特定文本类型内，参数选择对性能有明显影响")
        report.append("2. **文本类型特异性**: 不同文本类型的最优参数组合不同")
        report.append("3. **交互效应复杂**: 简单的主效应分析无法捕捉复杂的参数交互模式")
        report.append("")
        
        # 实践建议
        report.append("### 🎯 实践建议")
        report.append("")
        report.append("1. **采用分类型参数策略**: 为不同文本类型设计专门的参数配置")
        report.append("2. **重视参数微调**: 虽然整体效应不显著，但在特定场景下参数优化仍有价值")
        report.append("3. **关注配置组合**: 重点关注表现最佳的参数组合模式")
        report.append("")
        
        # 保存报告
        with open(f'{save_dir}/Deep_Investigation_Report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        # 保存详细数据
        top_configs.to_csv(f'{save_dir}/Top_Configurations_Detailed.csv', index=False)
        interactions.to_csv(f'{save_dir}/Parameter_Interactions_Analysis.csv')
        temp_analysis.to_csv(f'{save_dir}/Temperature_Effects_by_Genre.csv')
        struct_analysis.to_csv(f'{save_dir}/Structure_Effects_by_Genre.csv')
        
        print(f"\n✅ 深度调查完成！")
        print(f"📊 报告和数据已保存到: {save_dir}")
        
        return {
            'top_configs': top_configs,
            'genre_results': genre_results,
            'interactions': interactions,
            'temp_analysis': temp_analysis,
            'struct_analysis': struct_analysis
        }

def main():
    """主函数"""
    data_path = "/Users/haha/Story/metrics_master_clean.csv"
    save_dir = "/Users/haha/Story/AAA/stage2_parameter_effects_analysis"
    
    investigator = DeepConfigurationInvestigator(data_path)
    results = investigator.generate_investigation_report(save_dir)
    
    print("\n🎯 快速总结:")
    print("=" * 40)
    top_configs = results['top_configs']
    print(f"最优配置数量: {len(top_configs)}")
    print(f"Structure偏好: {top_configs['structure'].value_counts().to_dict()}")
    print(f"Temperature偏好: {top_configs['temperature'].value_counts().to_dict()}")
    print(f"Genre偏好: {top_configs['genre'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
