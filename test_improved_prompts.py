#!/usr/bin/env python3
"""
测试改进后的Prompt效果
对比修改前后的故事生成质量
"""

import json
import os
from src.generation.outline_generator import generate_outline
from src.generation.generate_characters import generate_characters_v1
from src.generation.expand_story import expand_story_v1
from analyze_story_concreteness import analyze_story_concreteness, print_concreteness_analysis

def test_new_prompts():
    """测试新的Prompt效果"""
    
    print("🧪 测试改进后的故事生成Prompt")
    print("=" * 50)
    
    # 测试参数
    test_topic = "The Little Match Girl"
    test_style = "Modern urban thriller"
    
    try:
        # Step 1: 生成大纲
        print("📝 生成故事大纲...")
        outline = generate_outline(
            topic=test_topic,
            style=test_style,
            generation_mode="traditional"
        )
        print(f"✅ 成功生成 {len(outline)} 个章节的大纲")
        
        # 显示大纲内容
        print("\n📋 生成的大纲:")
        for i, chapter in enumerate(outline[:3], 1):  # 只显示前3章
            print(f"{i}. {chapter['title']}")
            print(f"   {chapter['summary']}")
            print()
        
        # Step 2: 生成角色
        print("👥 生成角色设定...")
        characters = generate_characters_v1(outline)
        print(f"✅ 成功生成 {len(characters)} 个角色")
        
        # Step 3: 扩展故事（只测试前2章，避免API消耗过多）
        print("📖 扩展故事内容（测试前2章）...")
        test_chapters = outline[:2]
        story = expand_story_v1(test_chapters, characters)
        print(f"✅ 成功扩展 {len(story)} 个章节")
        
        # Step 4: 分析具体性
        print("\n📊 分析故事具体性...")
        results = analyze_story_concreteness(story)
        print_concreteness_analysis(results)
        
        # 保存测试结果
        test_output_dir = "test_outputs"
        os.makedirs(test_output_dir, exist_ok=True)
        
        # 保存生成的内容
        with open(f"{test_output_dir}/test_outline.json", "w", encoding="utf-8") as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)
        
        with open(f"{test_output_dir}/test_characters.json", "w", encoding="utf-8") as f:
            json.dump(characters, f, ensure_ascii=False, indent=2)
            
        with open(f"{test_output_dir}/test_story.json", "w", encoding="utf-8") as f:
            json.dump(story, f, ensure_ascii=False, indent=2)
        
        with open(f"{test_output_dir}/test_concreteness_analysis.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存到 {test_output_dir}/ 文件夹")
        
        # 总结改进效果
        print("\n🎯 改进效果总结:")
        stats = results['overall_stats']
        abstract_ratio = stats['abstract_ratio']
        concrete_ratio = stats['concrete_ratio']
        
        if abstract_ratio < 0.4:
            print("✅ 情感/抽象比例良好 (<40%)")
        elif abstract_ratio < 0.6:
            print("🟡 情感/抽象比例尚可 (40-60%)")
        else:
            print("🔴 情感/抽象比例仍然过高 (>60%)")
        
        if concrete_ratio > 0.2:
            print("✅ 具体行动比例良好 (>20%)")
        elif concrete_ratio > 0.1:
            print("🟡 具体行动比例尚可 (10-20%)")
        else:
            print("🔴 具体行动比例仍然过低 (<10%)")
        
        print(f"\n📈 关键指标:")
        print(f"   情感描述比例: {abstract_ratio:.1%}")
        print(f"   具体行动比例: {concrete_ratio:.1%}")
        print(f"   行动/情感比例: 1:{abstract_ratio/concrete_ratio:.1f}" if concrete_ratio > 0 else "   行动/情感比例: 无法计算")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def compare_with_old_version():
    """与旧版本对比（如果有旧版本数据的话）"""
    old_file = "data/output/theuglyduckling_abo_nonlinear_T0.7_s2/story_concreteness_analysis.json"
    
    if os.path.exists(old_file):
        print("\n📊 与旧版本对比:")
        print("-" * 30)
        
        with open(old_file, 'r', encoding='utf-8') as f:
            old_results = json.load(f)
        
        old_abstract = old_results['overall_stats']['abstract_ratio']
        old_concrete = old_results['overall_stats']['concrete_ratio']
        
        print(f"旧版本:")
        print(f"   情感描述比例: {old_abstract:.1%}")
        print(f"   具体行动比例: {old_concrete:.1%}")
        
        print(f"\n如果新版本改进成功，应该看到:")
        print(f"   情感描述比例 < {old_abstract:.1%}")
        print(f"   具体行动比例 > {old_concrete:.1%}")

if __name__ == "__main__":
    print("开始测试改进后的故事生成...")
    
    # 先显示对比目标
    compare_with_old_version()
    
    # 运行测试
    success = test_new_prompts()
    
    if success:
        print("\n🎉 测试完成！请查看上方的分析结果来评估改进效果。")
    else:
        print("\n❌ 测试遇到问题，请检查错误信息。")
