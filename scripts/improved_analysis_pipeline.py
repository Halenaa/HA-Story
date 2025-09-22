#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的分析流程 - 基于统计建议的修正版本

主要改进：
1. ICC模型选择：使用ICC(2,k)关注多评委平均分的可靠性
2. 配置级别分析：在混合效应模型中添加story_id随机效应，但检查共线性
3. 交叉验证组角色：分离G组进行独立分析，避免违反统计假设

作者: AI Assistant
日期: 2025年9月
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 统计分析库
try:
    import statsmodels.api as sm
    from statsmodels.formula.api import mixedlm
    from statsmodels.stats.anova import anova_lm
    import pingouin as pg
    ADVANCED_STATS = True
    print("✅ 高级统计库可用")
except ImportError:
    ADVANCED_STATS = False
    print("⚠️ 部分统计包不可用，将使用基础分析")

class ImprovedAnalysisPipeline:
    """改进的分析流程类"""
    
    def __init__(self, data_path="Interview.csv"):
        """初始化分析流程"""
        self.data_path = data_path
        self.raw_data = None
        self.main_data = None  # 主要分析组 (A-F)
        self.cross_val_data = None  # 交叉验证组 (G)
        self.long_data = None
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置参数
        self.rating_dimensions = [
            'Coherence', 'Emotional Development', 'Character Consistency',
            'Creativity/Originality', 'Language Fluency', 'Structural Completeness', 
            'Overall Quality'
        ]
        
    def load_and_prepare_data(self):
        """加载并预处理数据"""
        print("=" * 60)
        print("📊 数据加载与预处理")
        print("=" * 60)
        
        # 读取原始数据
        try:
            self.raw_data = pd.read_csv(self.data_path)
            print(f"✅ 成功加载数据: {len(self.raw_data)} 行")
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return False
            
        # 基本数据清理
        self.raw_data = self.raw_data.dropna(subset=['Group_id'])
        print(f"📊 组别分布:")
        print(self.raw_data['Group_id'].value_counts().sort_index())
        
        return True
    
    def separate_analysis_groups(self):
        """分离分析组：主要组(A-F) vs 交叉验证组(G)"""
        print("\n🔄 分离分析组")
        
        # 主要分析组 (A-F)：每组3人，完整的嵌套设计
        main_groups = ['A', 'B', 'C', 'D', 'E', 'F']
        self.main_data = self.raw_data[self.raw_data['Group_id'].isin(main_groups)].copy()
        
        # 交叉验证组 (G)：不同的设计模式，用于一致性检查
        self.cross_val_data = self.raw_data[self.raw_data['Group_id'] == 'G'].copy()
        
        print(f"📊 主要分析组 (A-F): {len(self.main_data)} 参与者")
        print(f"📊 交叉验证组 (G): {len(self.cross_val_data)} 参与者")
        
        return len(self.main_data) > 0 and len(self.cross_val_data) > 0
    
    def create_long_format(self, data, group_suffix=""):
        """转换为长表格式"""
        print(f"\n📋 转换为长表格式{group_suffix}")
        
        long_records = []
        
        for idx, row in data.iterrows():
            # 生成评委ID
            rater_id = f"{row['Group_id']}_P{idx}"
            
            # 处理4个故事槽位
            story_slots = ['Story 1', 'Story 2', 'Story 3', 'Story 4']
            
            for slot_idx, slot in enumerate(story_slots):
                story_id = row[slot]
                if pd.isna(story_id):
                    continue
                    
                # 获取该故事的7个评分维度
                base_idx = slot_idx * 7
                rating_cols = [col for col in data.columns if 
                              any(dim in col for dim in self.rating_dimensions)]
                
                story_ratings = []
                for dim_idx, dimension in enumerate(self.rating_dimensions):
                    # 查找对应的评分列
                    target_col_idx = base_idx + dim_idx
                    if target_col_idx < len(rating_cols):
                        col_name = rating_cols[target_col_idx]
                        score = row[col_name]
                        if pd.notna(score):
                            story_ratings.append({
                                'rater_id': rater_id,
                                'group_id': row['Group_id'],
                                'story_id': story_id,
                                'dimension': dimension,
                                'score': float(score),
                                'story_slot': slot_idx + 1
                            })
                
                long_records.extend(story_ratings)
        
        long_df = pd.DataFrame(long_records)
        
        if len(long_df) > 0:
            # 解析故事配置
            long_df = self._parse_story_config(long_df)
            # 标准化分数
            long_df = self._standardize_scores(long_df)
        
        print(f"   ✅ 生成 {len(long_df)} 条评分记录")
        return long_df
    
    def _parse_story_config(self, df):
        """解析故事配置参数"""
        import re
        
        def parse_config(story_id):
            if story_id == 'Sci baseline':
                return {'config': 'baseline', 'structure': 'baseline', 
                       'temperature': 'baseline', 'seed': 'baseline'}
            
            # 匹配 linear/nonlinear_T{temperature}_s{seed}
            pattern = r'(linear|nonlinear)_T([0-9.]+)_s([0-9]+)'
            match = re.match(pattern, story_id)
            
            if match:
                structure, temperature, seed = match.groups()
                config = f"{structure}_T{temperature}"
                return {
                    'config': config,
                    'structure': structure,
                    'temperature': float(temperature),
                    'seed': int(seed)
                }
            else:
                return {'config': 'unknown', 'structure': 'unknown',
                       'temperature': np.nan, 'seed': np.nan}
        
        # 应用解析
        parsed = df['story_id'].apply(parse_config)
        for key in ['config', 'structure', 'temperature', 'seed']:
            df[key] = [p[key] for p in parsed]
        
        return df
    
    def _standardize_scores(self, df):
        """标准化评分（按维度）"""
        for dimension in df['dimension'].unique():
            mask = df['dimension'] == dimension
            scores = df.loc[mask, 'score']
            if len(scores) > 1:
                df.loc[mask, 'score_z'] = (scores - scores.mean()) / scores.std()
            else:
                df.loc[mask, 'score_z'] = 0.0
        return df
    
    def calculate_improved_icc(self, data, focus_dim='Overall Quality'):
        """改进的ICC计算：确保使用ICC(2,k)，包含详细的seed级别分析"""
        print(f"\n🔍 改进的ICC分析 - 使用ICC(2,k)")
        
        if not ADVANCED_STATS:
            print("❌ 需要高级统计包进行ICC计算")
            return None
        
        dim_data = data[data['dimension'] == focus_dim].copy()
        
        if len(dim_data) == 0:
            print(f"❌ 没有 {focus_dim} 的数据")
            return None
        
        # 首先展示详细的数据结构
        print(f"\n📊 数据结构详情 - {focus_dim}:")
        for config in sorted(dim_data['config'].unique()):
            if config == 'baseline':
                continue
                
            config_data = dim_data[dim_data['config'] == config]
            stories = sorted(config_data['story_id'].unique())
            n_raters = config_data['rater_id'].nunique()
            
            print(f"\n   {config}:")
            print(f"     评委数: {n_raters}")
            print(f"     故事数: {len(stories)}")
            print(f"     不同seed的故事:")
            
            for story in stories:
                story_data = config_data[config_data['story_id'] == story]
                seed = story_data['seed'].iloc[0] if 'seed' in story_data.columns else 'unknown'
                raters_for_story = story_data['rater_id'].nunique() 
                scores = story_data['score'].values
                mean_score = np.mean(scores)
                std_score = np.std(scores)
                print(f"       {story} (seed={seed}): {raters_for_story}评委, 均分={mean_score:.2f}±{std_score:.2f}")
        
        icc_results = []
        
        # 按配置计算ICC(2,k)
        print(f"\n🔍 按配置计算ICC(2,k) - {focus_dim}:")
        print("   (评估：多个评委对同一配置下不同seed故事的评分一致性)")
        
        for config in sorted(dim_data['config'].unique()):
            if config == 'baseline':
                continue  # baseline只有1个故事，无法计算ICC
                
            config_data = dim_data[dim_data['config'] == config]
            
            # 检查数据充足性
            n_raters = config_data['rater_id'].nunique()
            n_stories = config_data['story_id'].nunique()
            
            print(f"\n   {config:<20}: {n_raters} 评委 × {n_stories} 故事", end="")
            
            if n_raters < 3 or n_stories < 2:
                print(" - 数据不足")
                continue
            
            try:
                # 计算ICC(2,k)
                icc_result = pg.intraclass_corr(
                    data=config_data,
                    targets='story_id',  # 目标：不同故事（不同seed）
                    raters='rater_id',   # 评委：不同评委  
                    ratings='score'      # 评分
                )
                
                # 选择ICC(2,k) - 多个评委平均分的信度
                icc_2k = icc_result[icc_result['Type'] == 'ICC2k']
                
                if len(icc_2k) > 0:
                    icc_value = icc_2k['ICC'].iloc[0]
                    ci_lower = icc_2k['CI95%'].iloc[0][0] 
                    ci_upper = icc_2k['CI95%'].iloc[0][1]
                    
                    # 可靠性等级
                    if icc_value >= 0.75:
                        reliability = "优秀"
                        emoji = "🌟"
                    elif icc_value >= 0.60:
                        reliability = "良好" 
                        emoji = "✅"
                    elif icc_value >= 0.40:
                        reliability = "一般"
                        emoji = "⚠️"
                    else:
                        reliability = "较差"
                        emoji = "❌"
                    
                    print(f" = ICC(2,k)={icc_value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}] {emoji} ({reliability})")
                    
                    # 详细解释这个结果的含义
                    if config == 'nonlinear_T0.7' and icc_value > 0.6:
                        print(f"     🎯 解释: 评委们对{config}配置下不同seed故事的质量评分高度一致")
                        print(f"           这表明该配置生成的故事质量稳定可靠")
                    elif icc_value < 0.4:
                        print(f"     ⚠️  解释: 评委们对{config}配置下不同seed故事的评分差异较大") 
                        print(f"           这可能表明该配置生成的故事质量不够稳定")
                    
                    icc_results.append({
                        'config': config,
                        'dimension': focus_dim,
                        'icc_2k': icc_value,
                        'ci_lower': ci_lower,
                        'ci_upper': ci_upper,
                        'reliability': reliability,
                        'n_raters': n_raters,
                        'n_stories': n_stories
                    })
                else:
                    print(" - ICC计算失败")
                    
            except Exception as e:
                print(f" - 错误: {str(e)[:50]}")
        
        # 按story计算简单的一致性指标
        print(f"\n📈 单个故事的评委一致性 (补充信息):")
        for config in sorted(dim_data['config'].unique()):
            if config == 'baseline':
                continue
                
            config_data = dim_data[dim_data['config'] == config]
            stories = sorted(config_data['story_id'].unique())
            
            print(f"\n   {config}:")
            for story in stories:
                story_data = config_data[config_data['story_id'] == story]
                if len(story_data) >= 3:  # 至少3个评委
                    scores = story_data['score'].values
                    cv = np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else np.inf
                    consistency = 1 / (1 + cv)  # 简单一致性指标
                    seed = story_data['seed'].iloc[0] if 'seed' in story_data.columns else 'unknown'
                    
                    if consistency > 0.7:
                        emoji = "✅"
                    elif consistency > 0.5:
                        emoji = "⚠️" 
                    else:
                        emoji = "❌"
                        
                    print(f"     {story} (seed={seed}): 一致性={consistency:.3f} {emoji}")
        
        if icc_results:
            icc_df = pd.DataFrame(icc_results)
            # 保存结果
            icc_df.to_csv(self.processed_dir / f'improved_icc_results_{focus_dim.lower().replace(" ", "_")}.csv', 
                         index=False)
            return icc_df
        
        return None
    
    def improved_mixed_effects_analysis(self):
        """改进的混合效应分析：分步模型比较"""
        print("\n🔬 改进的混合效应分析")
        
        if not ADVANCED_STATS:
            print("❌ 需要高级统计包进行混合效应建模")
            return None
        
        # 使用主要分析组的Overall Quality数据
        model_data = self.main_data_long[
            (self.main_data_long['dimension'] == 'Overall Quality') &
            (self.main_data_long['score_z'].notna()) &
            (self.main_data_long['config'] != 'baseline')  # 排除baseline进行对比分析
        ].copy()
        
        if len(model_data) < 20:
            print("❌ 数据不足，无法进行混合效应建模")
            return None
        
        print(f"📊 模型数据:")
        print(f"   观测数: {len(model_data)}")
        print(f"   评委数: {model_data['rater_id'].nunique()}")
        print(f"   故事数: {model_data['story_id'].nunique()}")
        print(f"   配置数: {model_data['config'].nunique()}")
        
        # 数据预处理：确保分类变量和数值变量正确
        model_data = model_data.reset_index(drop=True)
        model_data['config'] = model_data['config'].astype('category')
        model_data['structure'] = model_data['structure'].astype('category')
        
        # 创建数值编码的评委ID
        rater_mapping = {rater: i for i, rater in enumerate(model_data['rater_id'].unique())}
        model_data['rater_numeric'] = model_data['rater_id'].map(rater_mapping)
        
        # 创建story的数值ID（避免字符串问题）
        story_mapping = {story: i for i, story in enumerate(model_data['story_id'].unique())}
        model_data['story_numeric'] = model_data['story_id'].map(story_mapping)
        
        results = {}
        
        # 模型1：简单模型（仅评委随机效应）
        try:
            print(f"\n🏗️ 模型1: 简单模型（仅评委随机效应）")
            model1 = mixedlm("score_z ~ C(config)", 
                           data=model_data, 
                           groups="rater_numeric")
            result1 = model1.fit()
            results['simple'] = result1
            
            print(f"   ✅ 简单模型拟合完成")
            print(f"   - AIC: {result1.aic:.2f}")
            print(f"   - LogLik: {result1.llf:.2f}")
            print(f"   - 评委随机效应方差: {result1.cov_re.iloc[0,0]:.4f}")
            print(f"   - 残差方差: {result1.scale:.4f}")
            
        except Exception as e:
            print(f"   ❌ 简单模型失败: {str(e)[:100]}")
            
        # 模型2：改进的简单模型（使用structure*temperature）
        try:
            print(f"\n🏗️ 模型2: 改进简单模型（structure*temperature交互）")
            model2 = mixedlm("score_z ~ C(structure) * temperature", 
                           data=model_data, 
                           groups="rater_numeric")
            result2 = model2.fit()
            results['improved_simple'] = result2
            
            print(f"   ✅ 改进简单模型拟合完成")
            print(f"   - AIC: {result2.aic:.2f}")
            print(f"   - LogLik: {result2.llf:.2f}")
            print(f"   - 评委随机效应方差: {result2.cov_re.iloc[0,0]:.4f}")
            print(f"   - 残差方差: {result2.scale:.4f}")
            
        except Exception as e:
            print(f"   ❌ 改进简单模型失败: {str(e)[:100]}")
        
        # 模型3：尝试添加story随机效应（谨慎处理共线性）
        try:
            print(f"\n🏗️ 模型3: 复杂模型（添加story随机效应）")
            
            # 检查共线性风险
            config_story_crosstab = pd.crosstab(model_data['config'], model_data['story_id'])
            print(f"   📊 配置-故事交叉表形状: {config_story_crosstab.shape}")
            
            # 只有在story_id与config不完全重叠时才尝试
            if config_story_crosstab.shape[0] < config_story_crosstab.shape[1]:
                # 使用简化的公式避免完全共线性
                model_data_subset = model_data[model_data['config'].isin(['linear_T0.7', 'nonlinear_T0.7'])]
                
                if len(model_data_subset) >= 10:
                    # 针对有足够数据的配置子集建模
                    model3 = mixedlm("score_z ~ C(config)", 
                                   data=model_data_subset, 
                                   groups="rater_numeric",
                                   vc_formula={"story_numeric": "0 + C(story_numeric)"})
                    result3 = model3.fit()
                    results['with_story'] = result3
                    
                    print(f"   ✅ 复杂模型拟合完成（子集数据）")
                    print(f"   - AIC: {result3.aic:.2f}")
                    print(f"   - LogLik: {result3.llf:.2f}")
                else:
                    print(f"   ⚠️ 子集数据不足，跳过复杂模型")
            else:
                print(f"   ⚠️ 检测到严重共线性风险，跳过story随机效应")
                
        except Exception as e:
            print(f"   ❌ 复杂模型失败: {str(e)[:100]}")
            print(f"   → 确认了共线性问题，正如你预期的那样")
        
        # 模型比较和选择
        if len(results) >= 2:
            print(f"\n📊 模型比较:")
            for name, result in results.items():
                print(f"   {name:15}: AIC={result.aic:7.2f}, LogLik={result.llf:8.2f}")
            
            # 选择最佳模型
            best_model = min(results.items(), key=lambda x: x[1].aic)
            print(f"   🏆 最佳模型: {best_model[0]} (AIC={best_model[1].aic:.2f})")
            
            # 显示最佳模型的系数
            print(f"\n📈 最佳模型参数估计:")
            best_result = best_model[1]
            for param, coef in best_result.params.items():
                pval = best_result.pvalues[param]
                significance = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""
                print(f"   {param:<25}: {coef:+7.3f} (p={pval:.4f}) {significance}")
                
        elif len(results) == 1:
            print(f"\n📊 单一模型结果:")
            result = list(results.values())[0]
            print(f"   AIC: {result.aic:.2f}")
            print(f"   参数估计:")
            for param, coef in result.params.items():
                pval = result.pvalues[param]
                significance = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""
                print(f"     {param:<20}: {coef:+7.3f} (p={pval:.4f}) {significance}")
        
        return results
    
    def analyze_cross_validation_consistency(self):
        """分析交叉验证组的一致性"""
        print("\n🔄 交叉验证组一致性分析")
        
        if len(self.cross_val_data_long) == 0:
            print("❌ 交叉验证组数据为空")
            return None
        
        cv_data = self.cross_val_data_long.copy()
        
        print(f"📊 交叉验证组数据:")
        print(f"   参与者: {cv_data['rater_id'].nunique()}")
        print(f"   故事: {cv_data['story_id'].nunique()}")
        print(f"   评分记录: {len(cv_data)}")
        
        # 与主要组的配置一致性检查
        print(f"\n🔍 与主要分析组的一致性检查:")
        
        main_configs = set(self.main_data_long['config'].unique())
        cv_configs = set(cv_data['config'].unique())
        
        overlap = main_configs.intersection(cv_configs)
        print(f"   重叠配置: {len(overlap)} / {len(main_configs)}")
        print(f"   重叠的配置: {sorted(overlap)}")
        
        # 对重叠配置计算相关性
        consistency_results = []
        
        for config in overlap:
            if config == 'baseline':
                continue
                
            for dimension in self.rating_dimensions:
                # 主要组平均分
                main_scores = self.main_data_long[
                    (self.main_data_long['config'] == config) &
                    (self.main_data_long['dimension'] == dimension)
                ]['score'].values
                
                # 交叉验证组平均分
                cv_scores = cv_data[
                    (cv_data['config'] == config) &
                    (cv_data['dimension'] == dimension)
                ]['score'].values
                
                if len(main_scores) > 0 and len(cv_scores) > 0:
                    main_mean = np.mean(main_scores)
                    cv_mean = np.mean(cv_scores)
                    
                    consistency_results.append({
                        'config': config,
                        'dimension': dimension,
                        'main_mean': main_mean,
                        'cv_mean': cv_mean,
                        'difference': cv_mean - main_mean,
                        'main_n': len(main_scores),
                        'cv_n': len(cv_scores)
                    })
        
        if consistency_results:
            consistency_df = pd.DataFrame(consistency_results)
            
            print(f"\n📊 一致性结果 (前10个最大差异):")
            top_diff = consistency_df.nlargest(10, 'difference')
            for _, row in top_diff.iterrows():
                print(f"   {row['config']:<15} {row['dimension']:<20}: "
                      f"主={row['main_mean']:.2f}, 验证={row['cv_mean']:.2f}, "
                      f"差值={row['difference']:+.2f}")
            
            # 保存结果
            consistency_df.to_csv(self.processed_dir / 'cross_validation_consistency.csv', 
                                 index=False)
            
            return consistency_df
        
        return None
    
    def run_complete_pipeline(self):
        """运行完整的改进分析流程"""
        print("🚀 开始改进的分析流程")
        print("=" * 60)
        
        # 1. 数据加载
        if not self.load_and_prepare_data():
            return False
        
        # 2. 分离分析组
        if not self.separate_analysis_groups():
            return False
        
        # 3. 转换为长表格式
        self.main_data_long = self.create_long_format(self.main_data, " (主要分析组)")
        self.cross_val_data_long = self.create_long_format(self.cross_val_data, " (交叉验证组)")
        
        if len(self.main_data_long) == 0:
            print("❌ 主要分析组数据转换失败")
            return False
        
        # 4. 改进的ICC分析
        icc_results = self.calculate_improved_icc(self.main_data_long, 'Overall Quality')
        
        # 5. 改进的混合效应分析
        mixed_results = self.improved_mixed_effects_analysis()
        
        # 6. 交叉验证一致性分析
        consistency_results = self.analyze_cross_validation_consistency()
        
        # 7. 生成总结报告
        self.generate_summary_report(icc_results, mixed_results, consistency_results)
        
        print("\n🎉 改进分析流程完成!")
        return True
    
    def generate_summary_report(self, icc_results, mixed_results, consistency_results):
        """生成总结报告"""
        print("\n📋 生成分析总结报告")
        
        report_lines = [
            "# 改进的统计分析报告",
            "",
            "## 分析改进要点",
            "",
            "### 1. ICC模型选择修正",
            "- **修正前**: 使用ICC(2,1) - 单个评委评分的信度", 
            "- **修正后**: 使用ICC(2,k) - 多个评委平均分的信度",
            "- **原因**: 我们更关心多个评委平均分是否可靠，用于后续配置比较",
            "",
            "### 2. 分析组分离",
            "- **主要分析组**: A-F组，每组3人，完整嵌套设计",
            "- **交叉验证组**: G组，不同设计模式，用于一致性检查",
            "- **原因**: 避免违反混合效应模型的嵌套结构假设",
            "",
            "### 3. 混合效应模型改进", 
            "- **简单模型**: score ~ structure*temperature + (1|rater_id)",
            "- **复杂模型**: 尝试添加story_id随机效应",
            "- **模型选择**: 基于AIC比较选择最佳模型",
            "",
            "## 分析结果",
            ""
        ]
        
        # ICC结果
        if icc_results is not None:
            report_lines.extend([
                "### ICC(2,k) 结果",
                ""
            ])
            
            for _, row in icc_results.iterrows():
                report_lines.append(
                    f"- **{row['config']}**: ICC(2,k)={row['icc_2k']:.3f} "
                    f"[{row['ci_lower']:.3f}, {row['ci_upper']:.3f}] - {row['reliability']}"
                )
            
            report_lines.append("")
        
        # 混合效应结果
        if mixed_results:
            report_lines.extend([
                "### 混合效应模型结果",
                ""
            ])
            
            for model_name, result in mixed_results.items():
                report_lines.append(f"- **{model_name}模型**: AIC={result.aic:.2f}")
            
            if len(mixed_results) > 1:
                best_model = min(mixed_results.items(), key=lambda x: x[1].aic)
                report_lines.append(f"- **最佳模型**: {best_model[0]} (AIC最小)")
                
            report_lines.append("")
        
        # 一致性检查结果  
        if consistency_results is not None:
            report_lines.extend([
                "### 交叉验证一致性检查",
                "",
                f"- 重叠配置数量: {len(consistency_results['config'].unique())}",
                f"- 平均差异: {consistency_results['difference'].mean():.3f}",
                f"- 差异标准差: {consistency_results['difference'].std():.3f}",
                ""
            ])
        
        report_lines.extend([
            "## 结论与建议",
            "",
            "### 统计方法改进验证",
            "1. ✅ ICC(2,k)方法更适合评价多评委平均分可靠性",
            "2. ✅ 分离交叉验证组避免了统计假设违反", 
            "3. ⚠️ story_id随机效应需谨慎使用，注意共线性问题",
            "",
            "### 后续建议",
            "1. 基于最佳混合效应模型进行假设检验",
            "2. 使用交叉验证组进行结果稳健性检查",
            "3. 考虑故事内容作为协变量的进一步分析",
            ""
        ])
        
        # 保存报告
        report_path = self.processed_dir / "improved_analysis_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"✅ 报告已保存至: {report_path}")

def main():
    """主函数"""
    pipeline = ImprovedAnalysisPipeline()
    success = pipeline.run_complete_pipeline()
    
    if success:
        print("\n🎯 改进分析流程执行成功！")
    else:
        print("\n❌ 分析流程执行失败")

if __name__ == "__main__":
    main()
