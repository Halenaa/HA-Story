#!/usr/bin/env python3
"""
分析最新实验theuglyduckling_abo_nonlinear_T0.9_s3的故事具体性
"""

import json
from analyze_story_concreteness import analyze_story_concreteness, print_concreteness_analysis

def analyze_latest_experiment():
    """分析最新实验结果"""
    
    new_version = "theuglyduckling_abo_nonlinear_T0.9_s3"
    story_file = f"data/output/{new_version}/story_updated.json"
    
    print("📊 分析最新实验结果：改进后的Prompt效果")
    print("=" * 60)
    print(f"实验版本: {new_version}")
    print("使用改进后的Prompt生成")
    print()
    
    try:
        # 加载新实验的故事数据
        with open(story_file, 'r', encoding='utf-8') as f:
            new_story_data = json.load(f)
        
        print(f"✅ 成功加载 {len(new_story_data)} 个章节")
        
        # 分析新实验的具体性
        new_results = analyze_story_concreteness(new_story_data)
        print_concreteness_analysis(new_results)
        
        # 保存分析结果
        output_file = f"data/output/{new_version}/story_concreteness_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析结果已保存: {output_file}")
        
        # 与旧版本对比
        old_version = "theuglyduckling_abo_nonlinear_T0.7_s2"
        old_file = f"data/output/{old_version}/story_concreteness_analysis.json"
        
        try:
            with open(old_file, 'r', encoding='utf-8') as f:
                old_results = json.load(f)
            
            print("\n📈 改进效果对比:")
            print("-" * 40)
            
            old_stats = old_results['overall_stats']
            new_stats = new_results['overall_stats']
            
            print(f"📊 情感描述句比例:")
            print(f"   旧版本: {old_stats['abstract_ratio']:.1%}")
            print(f"   新版本: {new_stats['abstract_ratio']:.1%}")
            
            improvement = old_stats['abstract_ratio'] - new_stats['abstract_ratio']
            if improvement > 0:
                print(f"   ✅ 改进: 减少了 {improvement:.1%}")
            elif improvement < 0:
                print(f"   🔴 退步: 增加了 {-improvement:.1%}")
            else:
                print(f"   🟡 无变化")
            
            print(f"\n📊 具体行动句比例:")
            print(f"   旧版本: {old_stats['concrete_ratio']:.1%}")
            print(f"   新版本: {new_stats['concrete_ratio']:.1%}")
            
            improvement2 = new_stats['concrete_ratio'] - old_stats['concrete_ratio']
            if improvement2 > 0:
                print(f"   ✅ 改进: 增加了 {improvement2:.1%}")
            elif improvement2 < 0:
                print(f"   🔴 退步: 减少了 {-improvement2:.1%}")
            else:
                print(f"   🟡 无变化")
            
            # 总体评估
            print(f"\n🎯 改进总评:")
            if improvement > 0 and improvement2 > 0:
                print("   🎉 显著改进：情感描述减少，具体行动增加")
            elif improvement > 0 or improvement2 > 0:
                print("   ✅ 有所改进：部分指标提升")
            elif improvement == 0 and improvement2 == 0:
                print("   🟡 无明显变化：可能需要进一步调整")
            else:
                print("   🔴 效果不佳：可能需要重新检查Prompt")
                
        except FileNotFoundError:
            print("\n⚠️  无法找到旧版本数据进行对比")
        
        return new_results
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

if __name__ == "__main__":
    analyze_latest_experiment()
