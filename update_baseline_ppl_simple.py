#!/usr/bin/env python3
"""
简化版本：将GPU计算的统一PPL值更新到metrics_master_clean.csv
"""

import pandas as pd
from datetime import datetime

def main():
    """主函数"""
    print("📊 更新baseline PPL到CSV")
    print("="*50)
    
    # GPU计算的结果
    gpu_results = {
        'baseline_s1': 2.321079077069624,
        'baseline_s2': 1.793993715077782, 
        'baseline_s3': 3.8519177203444985
    }
    
    avg_ppl = sum(gpu_results.values()) / len(gpu_results)
    print(f"新的统一baseline平均PPL: {avg_ppl:.3f}")
    
    # 读取CSV
    csv_path = '/Users/haha/Story/metrics_master_clean.csv'
    df = pd.read_csv(csv_path)
    print(f"读取CSV: {len(df)} 行")
    
    # 备份原文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'/Users/haha/Story/metrics_master_clean_backup_{timestamp}.csv'
    df.to_csv(backup_path, index=False)
    print(f"原文件已备份: {backup_path}")
    
    # 查找并更新baseline行
    updates = 0
    
    # 根据CSV中的实际数据更新
    for idx, row in df.iterrows():
        story_id = row['story_id']
        if 'simple_baseline_s1' in story_id:
            old_ppl = row['pseudo_ppl']
            df.at[idx, 'pseudo_ppl'] = gpu_results['baseline_s1']
            print(f"✅ 更新 {story_id}: {old_ppl} → {gpu_results['baseline_s1']:.3f}")
            updates += 1
        elif 'simple_baseline_s2' in story_id:
            old_ppl = row['pseudo_ppl']
            df.at[idx, 'pseudo_ppl'] = gpu_results['baseline_s2']
            print(f"✅ 更新 {story_id}: {old_ppl} → {gpu_results['baseline_s2']:.3f}")
            updates += 1
        elif 'simple_baseline_s3' in story_id:
            old_ppl = row['pseudo_ppl']
            df.at[idx, 'pseudo_ppl'] = gpu_results['baseline_s3']
            print(f"✅ 更新 {story_id}: {old_ppl} → {gpu_results['baseline_s3']:.3f}")
            updates += 1
    
    # 保存更新的文件
    df.to_csv(csv_path, index=False)
    print(f"\n🎉 更新完成！")
    print(f"成功更新: {updates} 个baseline")
    print(f"平均PPL从 ~11.5 → {avg_ppl:.3f}")
    print(f"与实验样本PPL(~2.6)差异: {abs(avg_ppl - 2.6):.3f}")
    
    # 验证更新
    df_verify = pd.read_csv(csv_path)
    baseline_mask = df_verify['story_id'].str.contains('simple_baseline', na=False)
    if baseline_mask.any():
        baseline_ppls = df_verify.loc[baseline_mask, 'pseudo_ppl'].tolist()
        verify_avg = sum(baseline_ppls) / len(baseline_ppls)
        print(f"\n✅ 验证: CSV中baseline平均PPL = {verify_avg:.3f}")
        
        if abs(verify_avg - avg_ppl) < 0.01:
            print("🎉 验证通过: PPL更新正确!")
        else:
            print("⚠️ 验证警告: 可能有问题")

if __name__ == "__main__":
    main()
