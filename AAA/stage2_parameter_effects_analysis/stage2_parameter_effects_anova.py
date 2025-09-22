#!/usr/bin/env python3
"""
阶段2：参数效应分析 - ANOVA分析
目标：回答"参数组合（Structure, Temp, Genre）如何影响维度表现"

分析方法：
- 三因素ANOVA (Structure × Temperature × Genre)
- 主效应和交互效应分析
- 效应量计算 (η²)
- Bonferroni多重比较校正
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import f_oneway
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

class ParameterEffectsAnalyzer:
    def __init__(self, data_path):
        """初始化分析器"""
        self.data_path = data_path
        self.df = None
        self.results = {}
        self.load_data()
        
    def load_data(self):
        """加载和预处理数据"""
        self.df = pd.read_csv(self.data_path)
        
        # 过滤掉baseline数据，只保留实验数据
        self.df = self.df[self.df['is_baseline'] == 0].copy()
        
        # 确保分类变量正确编码
        self.df['structure'] = self.df['structure'].astype('category')
        self.df['temperature'] = self.df['temperature'].astype('category') 
        self.df['genre'] = self.df['genre'].astype('category')
        
        print(f"数据加载完成，共{len(self.df)}个观测")
        print(f"Structure水平: {self.df['structure'].cat.categories.tolist()}")
        print(f"Temperature水平: {self.df['temperature'].cat.categories.tolist()}")
        print(f"Genre水平: {self.df['genre'].cat.categories.tolist()}")
        
    def calculate_effect_size(self, ss_factor, ss_total):
        """计算效应量 η² (Eta squared)"""
        return ss_factor / ss_total if ss_total > 0 else 0
    
    def perform_anova_analysis(self, dependent_vars):
        """对指定的因变量进行三因素ANOVA分析"""
        anova_results = {}
        
        for var in dependent_vars:
            if var not in self.df.columns:
                print(f"警告: 变量 {var} 不在数据中")
                continue
                
            # 检查数据完整性
            clean_data = self.df[[var, 'structure', 'temperature', 'genre']].dropna()
            if len(clean_data) < 10:
                print(f"警告: {var} 的有效数据量太少 ({len(clean_data)})")
                continue
                
            try:
                # 构建ANOVA模型
                formula = f'{var} ~ C(structure) * C(temperature) * C(genre)'
                model = ols(formula, data=clean_data).fit()
                anova_table = anova_lm(model, typ=2)
                
                # 计算效应量
                ss_total = anova_table['sum_sq'].sum()
                effect_sizes = {}
                for effect in anova_table.index:
                    if effect != 'Residual':
                        effect_sizes[effect] = self.calculate_effect_size(
                            anova_table.loc[effect, 'sum_sq'], ss_total
                        )
                
                anova_results[var] = {
                    'anova_table': anova_table,
                    'effect_sizes': effect_sizes,
                    'model': model,
                    'n_obs': len(clean_data)
                }
                
                print(f"✓ {var}: ANOVA完成 (n={len(clean_data)})")
                
            except Exception as e:
                print(f"✗ {var}: ANOVA分析失败 - {str(e)}")
                continue
                
        return anova_results
    
    def format_anova_table(self, results):
        """格式化ANOVA结果表"""
        all_effects = []
        
        for var, result in results.items():
            anova_table = result['anova_table']
            effect_sizes = result['effect_sizes']
            
            for effect in anova_table.index:
                if effect != 'Residual':
                    all_effects.append({
                        'Dependent_Variable': var,
                        'Effect': effect,
                        'F': anova_table.loc[effect, 'F'],
                        'p_value': anova_table.loc[effect, 'PR(>F)'],
                        'eta_squared': effect_sizes.get(effect, 0),
                        'df': f"{int(anova_table.loc[effect, 'df'])}, {int(anova_table.loc['Residual', 'df'])}",
                        'n_obs': result['n_obs']
                    })
        
        return pd.DataFrame(all_effects)
    
    def interpret_effect_size(self, eta_squared):
        """解释效应量大小"""
        if eta_squared < 0.01:
            return "极小"
        elif eta_squared < 0.06:
            return "小"
        elif eta_squared < 0.14:
            return "中等"
        else:
            return "大"
    
    def create_effects_summary(self, formatted_table):
        """创建效应摘要"""
        # 应用Bonferroni校正
        n_tests = len(formatted_table)
        formatted_table['p_adjusted'] = formatted_table['p_value'] * n_tests
        formatted_table['p_adjusted'] = formatted_table['p_adjusted'].clip(upper=1.0)
        
        # 添加显著性标记
        def sig_marker(p):
            if p < 0.001: return "***"
            elif p < 0.01: return "**"
            elif p < 0.05: return "*"
            elif p < 0.10: return "†"
            else: return "ns"
        
        formatted_table['Significance'] = formatted_table['p_adjusted'].apply(sig_marker)
        formatted_table['Effect_Size_Interpretation'] = formatted_table['eta_squared'].apply(self.interpret_effect_size)
        
        return formatted_table
    
    def visualize_main_effects(self, results, save_dir):
        """可视化主效应"""
        for var in results.keys():
            if var not in self.df.columns:
                continue
                
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            # Structure效应
            sns.boxplot(data=self.df, x='structure', y=var, ax=axes[0])
            axes[0].set_title(f'{var} by Structure')
            axes[0].tick_params(axis='x', rotation=45)
            
            # Temperature效应
            sns.boxplot(data=self.df, x='temperature', y=var, ax=axes[1])
            axes[1].set_title(f'{var} by Temperature')
            
            # Genre效应  
            sns.boxplot(data=self.df, x='genre', y=var, ax=axes[2])
            axes[2].set_title(f'{var} by Genre')
            axes[2].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/{var}_main_effects.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def visualize_interaction_effects(self, results, save_dir):
        """可视化交互效应"""
        for var in results.keys():
            if var not in self.df.columns:
                continue
                
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # Structure × Temperature
            sns.pointplot(data=self.df, x='temperature', y=var, hue='structure', ax=axes[0,0])
            axes[0,0].set_title(f'{var}: Structure × Temperature')
            
            # Structure × Genre
            sns.pointplot(data=self.df, x='genre', y=var, hue='structure', ax=axes[0,1])
            axes[0,1].set_title(f'{var}: Structure × Genre')
            axes[0,1].tick_params(axis='x', rotation=45)
            
            # Temperature × Genre
            sns.pointplot(data=self.df, x='genre', y=var, hue='temperature', ax=axes[1,0])
            axes[1,0].set_title(f'{var}: Temperature × Genre')
            axes[1,0].tick_params(axis='x', rotation=45)
            
            # 三因素交互（使用热图近似）
            interaction_data = self.df.groupby(['structure', 'temperature', 'genre'])[var].mean().unstack()
            sns.heatmap(interaction_data, annot=True, fmt='.3f', ax=axes[1,1], cmap='viridis')
            axes[1,1].set_title(f'{var}: Three-way Interaction')
            
            plt.tight_layout()
            plt.savefig(f'{save_dir}/{var}_interaction_effects.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def run_comprehensive_analysis(self):
        """运行完整的参数效应分析"""
        print("=" * 60)
        print("阶段2：参数效应分析开始")
        print("=" * 60)
        
        # 定义关键维度
        key_dimensions = [
            'avg_semantic_continuity',    # 语义连贯性
            'diversity_score_seed',       # 多样性  
            'pseudo_ppl',                # 流畅性
            'one_minus_self_bleu',       # 独创性
            'roberta_avg_score',         # 情感一致性
            'err_per_100w'              # 错误率
        ]
        
        print(f"分析维度: {key_dimensions}")
        print()
        
        # 执行ANOVA分析
        print("步骤1: 执行三因素ANOVA分析...")
        results = self.perform_anova_analysis(key_dimensions)
        
        if not results:
            print("错误：没有成功分析任何维度")
            return None
        
        # 格式化结果
        print("\n步骤2: 格式化ANOVA结果...")
        formatted_table = self.format_anova_table(results)
        summary_table = self.create_effects_summary(formatted_table)
        
        # 保存结果
        save_dir = "/Users/haha/Story/AAA/stage2_parameter_effects_analysis"
        
        print(f"\n步骤3: 保存结果到 {save_dir}...")
        summary_table.to_csv(f'{save_dir}/table2_parameter_effects.csv', index=False)
        
        # 创建可视化
        print("\n步骤4: 创建可视化...")
        self.visualize_main_effects(results, save_dir)
        self.visualize_interaction_effects(results, save_dir)
        
        # 生成详细报告
        self.generate_detailed_report(summary_table, results, save_dir)
        
        print("\n" + "=" * 60)
        print("阶段2分析完成！")
        print(f"结果保存在: {save_dir}")
        print("=" * 60)
        
        return {
            'summary_table': summary_table,
            'detailed_results': results,
            'save_dir': save_dir
        }
    
    def generate_detailed_report(self, summary_table, results, save_dir):
        """生成详细的分析报告"""
        
        report = []
        report.append("# 阶段2：参数效应分析报告")
        report.append("## Parameter Effects Analysis Report")
        report.append("")
        report.append("### 分析目标")
        report.append("检验参数组合（Structure, Temperature, Genre）如何影响各维度表现")
        report.append("")
        report.append("### 分析方法")
        report.append("- 三因素方差分析 (Three-way ANOVA)")
        report.append("- Structure (2水平) × Temperature (3水平) × Genre (3水平)")
        report.append("- Bonferroni多重比较校正")
        report.append("- 效应量计算 (η²)")
        report.append("")
        
        # 添加显著效应总结
        report.append("### 主要发现")
        significant_effects = summary_table[summary_table['p_adjusted'] < 0.05]
        
        if len(significant_effects) > 0:
            report.append("#### 显著效应 (p < 0.05):")
            for _, row in significant_effects.iterrows():
                report.append(f"- **{row['Dependent_Variable']}**: {row['Effect']} "
                           f"(F={row['F']:.2f}, p={row['p_adjusted']:.4f}, η²={row['eta_squared']:.3f}, {row['Effect_Size_Interpretation']}效应)")
        else:
            report.append("- 未发现显著的参数效应")
        
        report.append("")
        
        # 按效应类型分组总结
        effect_types = ['C(structure)', 'C(temperature)', 'C(genre)', 
                       'C(structure):C(temperature)', 'C(structure):C(genre)', 
                       'C(temperature):C(genre)', 'C(structure):C(temperature):C(genre)']
        
        for effect_type in effect_types:
            effect_data = summary_table[summary_table['Effect'] == effect_type]
            if len(effect_data) > 0:
                report.append(f"#### {effect_type}")
                significant = effect_data[effect_data['p_adjusted'] < 0.05]
                if len(significant) > 0:
                    report.append("显著影响的维度:")
                    for _, row in significant.iterrows():
                        report.append(f"- {row['Dependent_Variable']}: η²={row['eta_squared']:.3f} ({row['Effect_Size_Interpretation']})")
                else:
                    report.append("无显著影响")
                report.append("")
        
        # 保存报告
        with open(f'{save_dir}/stage2_parameter_effects_report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

def main():
    """主函数"""
    data_path = "/Users/haha/Story/metrics_master_clean.csv"
    analyzer = ParameterEffectsAnalyzer(data_path)
    results = analyzer.run_comprehensive_analysis()
    
    if results:
        print("\n表2预览:")
        display_cols = ['Dependent_Variable', 'Effect', 'F', 'p_adjusted', 'eta_squared', 'Significance']
        print(results['summary_table'][display_cols].head(20))

if __name__ == "__main__":
    main()
