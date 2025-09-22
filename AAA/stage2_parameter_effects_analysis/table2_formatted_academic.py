#!/usr/bin/env python3
"""
创建学术标准的表2：参数效应ANOVA结果
按照学术惯例格式化表格
"""

import pandas as pd
import numpy as np

def create_academic_table2():
    """创建学术格式的表2"""
    
    # 读取原始结果
    results = pd.read_csv('/Users/haha/Story/AAA/stage2_parameter_effects_analysis/table2_parameter_effects.csv')
    
    # 定义维度的中文名称映射
    dimension_names = {
        'avg_semantic_continuity': '语义连贯性 (Semantic Continuity)',
        'diversity_score_seed': '多样性 (Diversity)',
        'pseudo_ppl': '流畅性 (Fluency)',
        'one_minus_self_bleu': '独创性 (Novelty)',
        'roberta_avg_score': '情感一致性 (Emotional Consistency)',
        'err_per_100w': '错误率 (Error Rate)'
    }
    
    # 定义效应的中文名称映射
    effect_names = {
        'C(structure)': 'Structure (S)',
        'C(temperature)': 'Temperature (T)',
        'C(genre)': 'Genre (G)',
        'C(structure):C(temperature)': 'S × T',
        'C(structure):C(genre)': 'S × G',
        'C(temperature):C(genre)': 'T × G',
        'C(structure):C(temperature):C(genre)': 'S × T × G'
    }
    
    # 重组数据为学术表格格式
    academic_table = []
    
    for dim in dimension_names.keys():
        dim_data = results[results['Dependent_Variable'] == dim]
        
        row = {
            'Dimension': dimension_names[dim],
            'Structure_F': '',
            'Structure_p': '',
            'Structure_eta2': '',
            'Temperature_F': '',
            'Temperature_p': '',
            'Temperature_eta2': '',
            'Genre_F': '',
            'Genre_p': '',
            'Genre_eta2': '',
            'SxT_F': '',
            'SxT_p': '',
            'SxT_eta2': '',
            'SxG_F': '',
            'SxG_p': '',
            'SxG_eta2': '',
            'TxG_F': '',
            'TxG_p': '',
            'TxG_eta2': '',
            'SxTxG_F': '',
            'SxTxG_p': '',
            'SxTxG_eta2': ''
        }
        
        for _, effect_row in dim_data.iterrows():
            effect = effect_row['Effect']
            f_val = f"{effect_row['F']:.2f}"
            p_val = format_p_value(effect_row['p_adjusted'])
            eta2_val = f"{effect_row['eta_squared']:.3f}"
            sig_marker = effect_row['Significance']
            
            if effect == 'C(structure)':
                row['Structure_F'] = f_val
                row['Structure_p'] = f"{p_val}{sig_marker}"
                row['Structure_eta2'] = eta2_val
            elif effect == 'C(temperature)':
                row['Temperature_F'] = f_val
                row['Temperature_p'] = f"{p_val}{sig_marker}"
                row['Temperature_eta2'] = eta2_val
            elif effect == 'C(genre)':
                row['Genre_F'] = f_val
                row['Genre_p'] = f"{p_val}{sig_marker}"
                row['Genre_eta2'] = eta2_val
            elif effect == 'C(structure):C(temperature)':
                row['SxT_F'] = f_val
                row['SxT_p'] = f"{p_val}{sig_marker}"
                row['SxT_eta2'] = eta2_val
            elif effect == 'C(structure):C(genre)':
                row['SxG_F'] = f_val
                row['SxG_p'] = f"{p_val}{sig_marker}"
                row['SxG_eta2'] = eta2_val
            elif effect == 'C(temperature):C(genre)':
                row['TxG_F'] = f_val
                row['TxG_p'] = f"{p_val}{sig_marker}"
                row['TxG_eta2'] = eta2_val
            elif effect == 'C(structure):C(temperature):C(genre)':
                row['SxTxG_F'] = f_val
                row['SxTxG_p'] = f"{p_val}{sig_marker}"
                row['SxTxG_eta2'] = eta2_val
        
        academic_table.append(row)
    
    df_academic = pd.DataFrame(academic_table)
    
    # 保存学术格式表格
    df_academic.to_csv('/Users/haha/Story/AAA/stage2_parameter_effects_analysis/Table2_Academic_Format.csv', index=False)
    
    # 创建简化版表格（只显示显著效应）
    create_significant_effects_table(results)
    
    # 创建效应量汇总表
    create_effect_size_summary(results)
    
    print("✓ 学术格式表2创建完成")
    print("✓ 显著效应汇总表创建完成") 
    print("✓ 效应量汇总表创建完成")

def format_p_value(p):
    """格式化p值"""
    if p < 0.001:
        return "< .001"
    elif p < 0.01:
        return f"{p:.3f}"
    elif p < 0.05:
        return f"{p:.3f}"
    else:
        return f"{p:.3f}"

def create_significant_effects_table(results):
    """创建显著效应汇总表"""
    
    # 筛选显著效应
    significant = results[results['p_adjusted'] < 0.05].copy()
    
    if len(significant) > 0:
        # 重新排序和格式化
        significant_clean = significant[['Dependent_Variable', 'Effect', 'F', 'p_adjusted', 'eta_squared']].copy()
        significant_clean.columns = ['维度', '效应', 'F值', 'p值 (校正后)', 'η²']
        
        # 维度名称映射
        dimension_names = {
            'avg_semantic_continuity': '语义连贯性',
            'diversity_score_seed': '多样性',
            'pseudo_ppl': '流畅性',
            'one_minus_self_bleu': '独创性', 
            'roberta_avg_score': '情感一致性',
            'err_per_100w': '错误率'
        }
        
        significant_clean['维度'] = significant_clean['维度'].map(dimension_names)
        
        # 效应名称映射
        effect_names = {
            'C(structure)': '结构',
            'C(temperature)': '温度',
            'C(genre)': '文本类型',
            'C(structure):C(temperature)': '结构×温度',
            'C(structure):C(genre)': '结构×文本类型',
            'C(temperature):C(genre)': '温度×文本类型',
            'C(structure):C(temperature):C(genre)': '结构×温度×文本类型'
        }
        
        significant_clean['效应'] = significant_clean['效应'].map(effect_names)
        
        # 格式化数值
        significant_clean['F值'] = significant_clean['F值'].round(2)
        significant_clean['p值 (校正后)'] = significant_clean['p值 (校正后)'].apply(lambda x: f"{x:.2e}" if x < 0.001 else f"{x:.3f}")
        significant_clean['η²'] = significant_clean['η²'].round(3)
        
        significant_clean.to_csv('/Users/haha/Story/AAA/stage2_parameter_effects_analysis/Significant_Effects_Summary.csv', index=False)
    else:
        print("未发现显著效应")

def create_effect_size_summary(results):
    """创建效应量汇总表"""
    
    # 按效应类型汇总
    effect_summary = []
    
    effects = ['C(structure)', 'C(temperature)', 'C(genre)', 
              'C(structure):C(temperature)', 'C(structure):C(genre)', 
              'C(temperature):C(genre)', 'C(structure):C(temperature):C(genre)']
    
    effect_names_cn = {
        'C(structure)': '结构主效应',
        'C(temperature)': '温度主效应',
        'C(genre)': '文本类型主效应',
        'C(structure):C(temperature)': '结构×温度交互',
        'C(structure):C(genre)': '结构×文本类型交互',
        'C(temperature):C(genre)': '温度×文本类型交互',
        'C(structure):C(temperature):C(genre)': '三因素交互'
    }
    
    for effect in effects:
        effect_data = results[results['Effect'] == effect]
        
        # 计算统计量
        mean_eta2 = effect_data['eta_squared'].mean()
        max_eta2 = effect_data['eta_squared'].max()
        min_eta2 = effect_data['eta_squared'].min()
        n_significant = len(effect_data[effect_data['p_adjusted'] < 0.05])
        n_total = len(effect_data)
        
        # 分类效应大小
        large_effects = len(effect_data[effect_data['eta_squared'] >= 0.14])
        medium_effects = len(effect_data[(effect_data['eta_squared'] >= 0.06) & (effect_data['eta_squared'] < 0.14)])
        small_effects = len(effect_data[(effect_data['eta_squared'] >= 0.01) & (effect_data['eta_squared'] < 0.06)])
        
        effect_summary.append({
            '效应类型': effect_names_cn[effect],
            '平均η²': f"{mean_eta2:.3f}",
            '最大η²': f"{max_eta2:.3f}",
            '最小η²': f"{min_eta2:.3f}",
            '显著效应数': f"{n_significant}/{n_total}",
            '大效应数': large_effects,
            '中效应数': medium_effects,
            '小效应数': small_effects
        })
    
    effect_summary_df = pd.DataFrame(effect_summary)
    effect_summary_df.to_csv('/Users/haha/Story/AAA/stage2_parameter_effects_analysis/Effect_Size_Summary.csv', index=False)

if __name__ == "__main__":
    create_academic_table2()
