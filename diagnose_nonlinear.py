#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本：不修改主代码，只测试现有的 nonlinear 功能
找出具体问题所在
"""

import os
import json
import traceback
from src.generation.outline_generator import generate_outline
from src.generation.chapter_reorder import reorder_chapters
from src.utils.utils import save_json, load_json


def diagnose_step_by_step():
    """逐步诊断每个环节"""
    print("🔍 开始逐步诊断 nonlinear 流程...")
    
    # 步骤1: 测试 outline 生成
    print("\n" + "="*50)
    print("📝 步骤1: 测试 outline 生成")
    print("="*50)
    
    try:
        outline = generate_outline(topic="小红帽", style="科幻改写", custom_instruction="")
        print(f"✅ outline 生成成功，共 {len(outline)} 个章节")
        
        # 显示结构
        for i, ch in enumerate(outline):
            print(f"  {i+1}. {ch.get('chapter_id', 'NO_ID')}: {ch.get('title', 'NO_TITLE')}")
            
        # 检查必要字段
        missing_fields = []
        for ch in outline:
            if 'chapter_id' not in ch:
                missing_fields.append('chapter_id')
            if 'title' not in ch:
                missing_fields.append('title')
        
        if missing_fields:
            print(f"⚠️ outline 缺少字段: {set(missing_fields)}")
        else:
            print("✅ outline 字段完整")
            
    except Exception as e:
        print(f"❌ outline 生成失败: {e}")
        traceback.print_exc()
        return False
    
    # 步骤2: 测试 reorder_chapters 调用
    print("\n" + "="*50)
    print("🔄 步骤2: 测试 reorder_chapters 调用")
    print("="*50)
    
    try:
        print("测试 linear 模式...")
        linear_result = reorder_chapters(outline, mode="linear")
        print(f"✅ linear 模式成功，返回 {len(linear_result)} 个章节")
        
        print("\n测试 nonlinear 模式...")
        nonlinear_result = reorder_chapters(outline, mode="nonlinear")
        print(f"✅ nonlinear 模式成功，返回 {len(nonlinear_result)} 个章节")
        
        # 检查结果结构
        print("\n检查 nonlinear 结果结构:")
        for i, ch in enumerate(nonlinear_result):
            has_new_order = 'new_order' in ch
            new_order_val = ch.get('new_order', 'MISSING')
            print(f"  {i+1}. {ch.get('chapter_id', 'NO_ID')}: new_order={new_order_val} {'✅' if has_new_order else '❌'}")
        
        # 检查是否真的重排了
        linear_order = [ch['chapter_id'] for ch in linear_result]
        nonlinear_order = [ch['chapter_id'] for ch in sorted(nonlinear_result, key=lambda x: x.get('new_order', 999))]
        
        print(f"\nLinear 顺序:    {linear_order}")
        print(f"Nonlinear 顺序: {nonlinear_order}")
        
        if linear_order == nonlinear_order:
            print("⚠️ 顺序没有改变，可能 LLM 重排失败")
        else:
            print("✅ 顺序确实改变了")
            
    except Exception as e:
        print(f"❌ reorder_chapters 调用失败: {e}")
        traceback.print_exc()
        return False
    
    # 步骤3: 测试主流程的关键部分
    print("\n" + "="*50)
    print("🏭 步骤3: 测试主流程关键部分")
    print("="*50)
    
    try:
        # 模拟主流程中的处理
        print("模拟 main_pipeline 中的 nonlinear 处理...")
        
        # 检查是否有 new_order 字段
        has_new_order = any("new_order" in ch for ch in nonlinear_result)
        print(f"检测到 new_order 字段: {has_new_order}")
        
        if not has_new_order:
            print("⚠️ 这是问题所在：LLM 重排没有返回 new_order 字段")
            return False
        
        # 模拟统一结构处理
        reorder_outline = []
        for reordered_ch in nonlinear_result:
            match = next((x for x in outline if x["chapter_id"] == reordered_ch["chapter_id"]), None)
            if match:
                merged = {
                    "chapter_id": reordered_ch["chapter_id"],
                    "title": reordered_ch["title"],
                    "summary": match.get("summary", "")
                }
                if "new_order" in reordered_ch:
                    merged["new_order"] = reordered_ch["new_order"]
                reorder_outline.append(merged)
        
        print(f"✅ 结构统一处理成功，最终 {len(reorder_outline)} 个章节")
        
    except Exception as e:
        print(f"❌ 主流程模拟失败: {e}")
        traceback.print_exc()
        return False
    
    print("\n" + "="*50)
    print("📋 诊断总结")
    print("="*50)
    print("✅ 所有关键步骤都正常，nonlinear 功能应该可以工作")
    return True


def diagnose_with_your_pipeline():
    """使用你的实际 pipeline 进行单次测试"""
    print("\n🧪 使用你的实际 pipeline 进行单次测试...")
    
    try:
        from main_pipeline_glm import main as run_pipeline
        
        print("运行单个 nonlinear 测试...")
        run_pipeline(
            version="diagnose_test",
            reorder_mode="nonlinear", 
            use_cache=False,
            topic="小红帽",
            style="科幻改写",
            behavior_model="gpt-4.1",
            temperature=0.7,
            seed=1
        )
        
        print("✅ 实际 pipeline 运行成功")
        
        # 检查输出文件
        output_files = [
            "output/diagnose_test/test_outline.json",
            "output/diagnose_test/test_reorder_outline.json",
            "output/diagnose_test/story.json"
        ]
        
        for file_path in output_files:
            if os.path.exists(file_path):
                print(f"✅ 找到输出文件: {file_path}")
            else:
                print(f"❌ 缺少输出文件: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 实际 pipeline 运行失败: {e}")
        traceback.print_exc()
        return False


def main():
    """主诊断函数"""
    print("🚀 开始诊断 nonlinear 问题")
    
    # 第一步：逐步测试
    step1_ok = diagnose_step_by_step()
    
    if step1_ok:
        print("\n🎯 基础功能正常，测试完整流程...")
        step2_ok = diagnose_with_your_pipeline()
        
        if step2_ok:
            print("\n🎉 所有测试通过！nonlinear 功能应该正常工作。")
            print("你可以尝试运行你的实验循环了。")
        else:
            print("\n⚠️ 完整流程有问题，需要查看具体错误信息。")
    else:
        print("\n❌ 基础功能有问题，需要先解决这些问题。")


if __name__ == "__main__":
    main()