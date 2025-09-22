#!/usr/bin/env python3
"""
更新comprehensive_analysis.json文件，将结构分析结果合并进去
"""

import os
import json

def update_comprehensive_analysis():
    """更新所有comprehensive_analysis.json文件"""
    
    # 缺失结构分析的配置
    missing_configs = [
        ('thelittleredridinghood_sciencefictionrewrite_linear_T0.3_s2', 'regression'),
        ('thelittleredridinghood_horror-suspenserewrite_nonlinear_T0.9_s3', 'horror'),
        ('thelittleredridinghood_horror-suspenserewrite_linear_T0.7_s1', 'horror'),
        ('thelittleredridinghood_horror-suspenserewrite_nonlinear_T0.7_s3', 'horror'),
        ('thelittleredridinghood_romanticrewrite_nonlinear_T0.3_s3', 'romantic'),
        ('thelittleredridinghood_romanticrewrite_linear_T0.7_s1', 'romantic')
    ]
    
    success_count = 0
    total_count = len(missing_configs)
    
    print("=" * 80)
    print("更新comprehensive_analysis.json文件")
    print("=" * 80)
    
    for config_name, test_type in missing_configs:
        print(f"\n处理配置: {config_name}")
        
        # 构建文件路径
        comprehensive_file = f'/Users/haha/Story/data/analysis_test/{test_type}_test_analysis/{config_name}/comprehensive_analysis.json'
        structure_file = f'/Users/haha/Story/data/analysis_test/{test_type}_test_analysis/{config_name}/story_structure_analysis.json'
        
        # 检查文件是否存在
        if not os.path.exists(comprehensive_file):
            print(f"❌ comprehensive_analysis.json不存在: {comprehensive_file}")
            continue
            
        if not os.path.exists(structure_file):
            print(f"❌ story_structure_analysis.json不存在: {structure_file}")
            continue
        
        try:
            # 读取comprehensive_analysis.json
            with open(comprehensive_file, 'r', encoding='utf-8') as f:
                comprehensive_data = json.load(f)
            
            # 读取结构分析结果
            with open(structure_file, 'r', encoding='utf-8') as f:
                structure_data = json.load(f)
            
            # 更新comprehensive_analysis.json
            comprehensive_data['story_structure_analysis'] = structure_data
            
            # 保存更新后的文件
            with open(comprehensive_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已更新comprehensive_analysis.json")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"comprehensive_analysis.json更新完成: {success_count}/{total_count} 成功")
    print("=" * 80)
    
    return success_count, total_count

if __name__ == "__main__":
    update_comprehensive_analysis()
