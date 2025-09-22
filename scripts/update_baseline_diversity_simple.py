#!/usr/bin/env python3
"""
为baseline补充diversity数据 - 简化版
"""

import pandas as pd
import numpy as np

def update_baseline_diversity():
    """为baseline补充可以计算的diversity数据"""
    
    # 读取现有数据
    df = pd.read_csv('/Users/haha/Story/metrics_master.csv')
    
    print("=== 更新Baseline的Diversity数据 ===")
    
    # 1. 补充 distinct_score (归一化分数)
    print("1. 补充 distinct_score...")
    
    # 获取所有distinct_avg的范围
    all_distinct_avg = df['distinct_avg'].dropna()
    min_val, max_val = all_distinct_avg.min(), all_distinct_avg.max()
    print(f"   distinct_avg范围: [{min_val:.3f}, {max_val:.3f}]")
    
    # 为baseline计算distinct_score
    baseline_mask = df['is_baseline'] == 1
    baseline_rows = df[baseline_mask]
    
    for idx in baseline_rows.index:
        distinct_avg = df.loc[idx, 'distinct_avg']
        if pd.notna(distinct_avg):
            # 使用Min-Max归一化
            normalized_score = (distinct_avg - min_val) / (max_val - min_val)
            df.loc[idx, 'distinct_score'] = normalized_score
            print(f"   {df.loc[idx, 'original_config_name']}: {distinct_avg:.3f} -> {normalized_score:.3f}")
    
    # 2. 补充 alpha 相关字段
    print("\n2. 补充 alpha 相关字段...")
    
    # 获取各genre的alpha值
    genre_alpha = df.groupby('genre')['alpha_value'].first().dropna()
    
    # 为sci_baseline设置sciencefiction的alpha值
    sci_baseline_idx = df[df['original_config_name'] == 'sci_baseline'].index
    if len(sci_baseline_idx) > 0:
        sci_alpha = genre_alpha.get('sciencefiction', np.nan)
        if pd.notna(sci_alpha):
            df.loc[sci_baseline_idx[0], 'alpha_genre'] = sci_alpha
            df.loc[sci_baseline_idx[0], 'alpha_value'] = sci_alpha
            print(f"   sci_baseline: alpha设为{sci_alpha:.3f} (来自sciencefiction)")
    
    # 为normal_baseline设置所有genre的平均alpha值
    normal_baseline_idx = df[df['original_config_name'] == 'normal_baseline'].index
    if len(normal_baseline_idx) > 0:
        avg_alpha = genre_alpha.mean()
        df.loc[normal_baseline_idx[0], 'alpha_genre'] = avg_alpha
        df.loc[normal_baseline_idx[0], 'alpha_value'] = avg_alpha
        print(f"   normal_baseline: alpha设为{avg_alpha:.3f} (所有genre平均值)")
    
    # 3. 保持组级diversity指标为NaN (表示不适用)
    print("\n3. 组级diversity指标...")
    print("   保持 diversity_group_score, self_bleu_group, one_minus_self_bleu 为NaN")
    print("   (这些指标需要组内多个故事，不适用于baseline)")
    
    # 4. 保存更新后的数据
    print(f"\n4. 保存更新...")
    output_file = '/Users/haha/Story/metrics_master.csv'
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"   已保存到: {output_file}")
    
    # 5. 显示更新结果
    print(f"\n=== 更新结果 ===")
    updated_baseline = df[df['is_baseline'] == 1]
    
    for idx, row in updated_baseline.iterrows():
        print(f"\n{row['original_config_name']}:")
        print(f"  distinct_avg: {row['distinct_avg']:.3f} ✓")
        print(f"  distinct_score: {row['distinct_score']:.3f} ✓")
        print(f"  alpha_genre: {row['alpha_genre']:.3f} ✓")
        print(f"  alpha_value: {row['alpha_value']:.3f} ✓")
        print(f"  diversity_group_score: NaN (不适用)")
        print(f"  self_bleu_group: NaN (不适用)")
        print(f"  one_minus_self_bleu: NaN (不适用)")
    
    # 6. 统计缺失数据变化
    print(f"\n=== 更新统计 ===")
    missing_stats = df.isnull().sum()
    missing_cols = missing_stats[missing_stats > 0].sort_values(ascending=False)
    
    print(f"剩余缺失数据:")
    for col, count in missing_cols.items():
        pct = count / len(df) * 100
        if count == 2:  # baseline的缺失
            print(f"  {col}: {count}/{len(df)} ({pct:.1f}% 缺失) - 仅baseline缺失（正常）")
        else:
            print(f"  {col}: {count}/{len(df)} ({pct:.1f}% 缺失)")
    
    print(f"\n✅ Baseline diversity数据更新完成！")
    print(f"   - 补充了 distinct_score (归一化分数)")
    print(f"   - 补充了 alpha_genre/alpha_value")
    print(f"   - 保持组级指标为NaN（符合逻辑）")
    
    return df

if __name__ == "__main__":
    df = update_baseline_diversity()
