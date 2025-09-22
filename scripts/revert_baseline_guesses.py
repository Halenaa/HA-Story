#!/usr/bin/env python3
"""
回滚baseline中猜测的数据，只保留可以真正计算的数据
"""

import pandas as pd
import numpy as np

def revert_baseline_guesses():
    """回滚baseline中不合理的猜测数据"""
    
    # 读取现有数据
    df = pd.read_csv('/Users/haha/Story/metrics_master.csv')
    
    print("=== 回滚Baseline中的猜测数据 ===")
    
    # 1. 保留可以计算的数据
    print("1. 保留可以真正计算的数据:")
    print("   ✅ distinct_avg: 原始数据，保留")
    print("   ✅ distinct_score: 基于distinct_avg归一化，可以计算，保留")
    
    # 2. 回滚不能真正计算的数据
    print("\n2. 回滚无法真正计算的数据:")
    baseline_mask = df['is_baseline'] == 1
    
    # 将alpha相关字段设为NaN
    df.loc[baseline_mask, 'alpha_genre'] = np.nan
    df.loc[baseline_mask, 'alpha_value'] = np.nan
    
    print("   ❌ alpha_genre: 设为NaN (需要组内多样本计算)")
    print("   ❌ alpha_value: 设为NaN (需要组内多样本计算)")
    
    # 3. 确认其他字段保持NaN
    print("\n3. 确认其他字段正确为NaN:")
    nan_fields = ['diversity_group_score', 'self_bleu_group', 'one_minus_self_bleu', 
                  'wall_time_sec', 'peak_mem_mb', 'tokens_total', 'cost_usd']
    
    for field in nan_fields:
        baseline_values = df[baseline_mask][field]
        nan_count = baseline_values.isna().sum()
        print(f"   {field}: {nan_count}/2 为NaN ({'✅' if nan_count == 2 else '❌'})")
    
    # 4. 保存更正后的数据
    print(f"\n4. 保存更正...")
    output_file = '/Users/haha/Story/metrics_master.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"   已保存到: {output_file}")
    
    # 5. 显示最终的baseline数据状态
    print(f"\n=== 更正后的Baseline数据状态 ===")
    baseline_rows = df[df['is_baseline'] == 1]
    
    for idx, row in baseline_rows.iterrows():
        print(f"\n{row['original_config_name']}:")
        print(f"  📊 可计算的diversity数据:")
        print(f"     distinct_avg: {row['distinct_avg']:.3f} ✅")
        print(f"     distinct_score: {row['distinct_score']:.3f} ✅ (归一化计算)")
        
        print(f"  ⚪ 无法计算的字段(正确为NaN):")
        alpha_genre_val = 'NaN' if pd.isna(row['alpha_genre']) else f"{row['alpha_genre']:.3f} ❌"
        alpha_value_val = 'NaN' if pd.isna(row['alpha_value']) else f"{row['alpha_value']:.3f} ❌"
        div_group_val = 'NaN' if pd.isna(row['diversity_group_score']) else 'ERROR ❌'
        self_bleu_val = 'NaN' if pd.isna(row['self_bleu_group']) else 'ERROR ❌'
        one_minus_val = 'NaN' if pd.isna(row['one_minus_self_bleu']) else 'ERROR ❌'
        
        print(f"     alpha_genre: {alpha_genre_val}")
        print(f"     alpha_value: {alpha_value_val}")
        print(f"     diversity_group_score: {div_group_val}")
        print(f"     self_bleu_group: {self_bleu_val}")
        print(f"     one_minus_self_bleu: {one_minus_val}")
    
    # 6. 统计最终的缺失数据
    print(f"\n=== 最终缺失数据统计 ===")
    missing_stats = df.isnull().sum()
    missing_cols = missing_stats[missing_stats > 0].sort_values(ascending=False)
    
    print(f"缺失数据字段:")
    for col, count in missing_cols.items():
        pct = count / len(df) * 100
        if count == 2:  # baseline缺失
            reason = ""
            if col in ['alpha_genre', 'alpha_value']:
                reason = " - 需要组内多样本"
            elif col in ['diversity_group_score', 'self_bleu_group', 'one_minus_self_bleu']:
                reason = " - 需要组内多样本"
            elif col in ['wall_time_sec', 'peak_mem_mb', 'tokens_total', 'cost_usd']:
                reason = " - 生成时未记录"
            
            print(f"  {col}: {count}/{len(df)} ({pct:.1f}%){reason}")
        else:
            print(f"  {col}: {count}/{len(df)} ({pct:.1f}%)")
    
    print(f"\n✅ 回滚完成！现在只保留真正可以计算的数据:")
    print(f"   - distinct_avg: ✅ 原始数据")
    print(f"   - distinct_score: ✅ 归一化计算")
    print(f"   - 其他无法计算的字段: ⚪ 正确设为NaN")
    print(f"\n💡 严谨的数据分析原则: 算不出来就留空，不猜测不推断！")
    
    return df

if __name__ == "__main__":
    df = revert_baseline_guesses()
