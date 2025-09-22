#!/usr/bin/env python3
"""
重新运行缺失的结构分析，并手动保存结果到正确位置
"""

import sys
import os
import json
sys.path.append('/Users/haha/Story/src')

from analysis.story_evaluator import run_story_evaluation
import src.constant as constant

def run_missing_structure_analysis():
    """重新运行缺失的结构分析"""
    
    # 设置输出目录
    constant.output_dir = '/Users/haha/Story/output'
    
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
    print("重新运行缺失的结构分析")
    print("=" * 80)
    
    for config_name, test_type in missing_configs:
        print(f"\n处理配置: {config_name}")
        
        # 构建文件路径
        story_json_path = f'/Users/haha/Story/data/output/{test_type}_test/{config_name}/story_updated.json'
        analysis_dir = f'/Users/haha/Story/data/analysis_test/{test_type}_test_analysis/{config_name}'
        
        # 检查story_updated.json是否存在
        if not os.path.exists(story_json_path):
            print(f"❌ story_updated.json不存在: {story_json_path}")
            continue
        
        try:
            # 运行结构分析
            print(f"  调用run_story_evaluation({config_name})")
            result = run_story_evaluation(config_name)
            
            if result is None:
                print(f"❌ 结构分析返回None")
                continue
            
            print(f"✅ 结构分析成功")
            
            # 手动保存结构分析结果到正确位置
            structure_file = os.path.join(analysis_dir, 'story_structure_analysis.json')
            with open(structure_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 已保存结构分析结果到: {structure_file}")
            
            # 更新comprehensive_analysis.json
            comprehensive_file = os.path.join(analysis_dir, 'comprehensive_analysis.json')
            if os.path.exists(comprehensive_file):
                with open(comprehensive_file, 'r', encoding='utf-8') as f:
                    comprehensive_data = json.load(f)
                
                # 更新comprehensive_analysis.json
                comprehensive_data['story_structure_analysis'] = result
                
                with open(comprehensive_file, 'w', encoding='utf-8') as f:
                    json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 已更新comprehensive_analysis.json")
            else:
                print(f"⚠️ comprehensive_analysis.json不存在")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ 结构分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"结构分析修复完成: {success_count}/{total_count} 成功")
    print("=" * 80)
    
    return success_count, total_count

if __name__ == "__main__":
    run_missing_structure_analysis()
