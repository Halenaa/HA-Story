#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新功能演示脚本
展示自定义描述模式的实际使用效果
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.generation.outline_generator import generate_outline

def demo_original_story():
    """演示1：原创故事"""
    print("🎬 演示1：原创科幻故事")
    print("=" * 50)
    
    user_description = """
    我想创作一个关于记忆交易的科幻故事。故事背景设定在2080年，
    人类发明了记忆提取和植入技术。主人公是一名记忆商人，
    专门买卖珍贵的记忆。但当他接触到一个神秘客户的记忆时，
    发现了一个关于人类起源的惊天秘密。
    故事应该探讨记忆与身份、真实与虚假的哲学问题。
    """
    
    print("📖 用户描述:")
    print(user_description)
    print("\n🔄 正在生成大纲...")
    
    try:
        outline = generate_outline(
            generation_mode="description_based",
            user_description=user_description
        )
        
        print(f"\n✅ 生成完成！共 {len(outline)} 个章节:")
        for i, chapter in enumerate(outline, 1):
            print(f"{i:2d}. {chapter.get('title', '无标题')}")
            print(f"    📝 {chapter.get('summary', '无摘要')}")
        
        return outline
    
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        return None

def demo_story_continuation():
    """演示2：故事续写"""
    print("\n🎬 演示2：故事续写")
    print("=" * 50)
    
    user_description = """
    请基于提供的故事开头，继续创作后续章节。
    保持原有的悬疑氛围和角色设定，
    逐步揭露真相，设计精彩的情节转折。
    """
    
    original_story = """
    《消失的记录员》
    
    第一章：神秘失踪
    档案管理员林小雨在整理旧文件时，发现了一份奇怪的档案。
    这份档案记录的事件日期竟然是未来的，而且详细描述了她自己的失踪。
    更诡异的是，档案上的签名正是她的笔迹。
    
    第二章：时间的痕迹
    林小雨开始调查这份档案的来源，却发现类似的档案还有很多。
    每一份都预言着不同人的未来，而且都在逐一应验。
    她意识到，有人在操控着时间，而她可能是下一个目标。
    """
    
    print("📖 原故事内容:")
    print(original_story)
    print("\n📝 续写要求:")
    print(user_description)
    print("\n🔄 正在生成续写大纲...")
    
    try:
        outline = generate_outline(
            generation_mode="description_based",
            user_description=user_description,
            file_content=original_story
        )
        
        print(f"\n✅ 续写大纲生成完成！共 {len(outline)} 个章节:")
        for i, chapter in enumerate(outline, 1):
            print(f"{i:2d}. {chapter.get('title', '无标题')}")
            print(f"    📝 {chapter.get('summary', '无摘要')}")
        
        return outline
    
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        return None

def demo_story_adaptation():
    """演示3：故事改编"""
    print("\n🎬 演示3：经典改编")
    print("=" * 50)
    
    user_description = """
    将经典童话《灰姑娘》改编成现代职场励志故事。
    背景设定在现代大城市，主人公是一名普通的职场新人，
    遭受职场霸凌但凭借才华和努力获得成功。
    保留原故事的核心主题，但更新为现代职场设定。
    """
    
    original_cinderella = """
    灰姑娘原故事梗概：
    
    从前有个善良的女孩，父亲去世后被继母和两个姐姐欺负，
    整天做家务被称为"灰姑娘"。某天王子举办舞会选妃，
    仙女教母帮助灰姑娘参加舞会。王子对她一见钟情，
    但午夜钟声响起时她必须离开，只留下一只玻璃鞋。
    王子凭借玻璃鞋找到了灰姑娘，两人从此幸福生活。
    """
    
    print("📖 原故事梗概:")
    print(original_cinderella)
    print("\n🔄 改编要求:")
    print(user_description)
    print("\n🔄 正在生成改编大纲...")
    
    try:
        outline = generate_outline(
            generation_mode="description_based",
            user_description=user_description,
            file_content=original_cinderella
        )
        
        print(f"\n✅ 改编大纲生成完成！共 {len(outline)} 个章节:")
        for i, chapter in enumerate(outline, 1):
            print(f"{i:2d}. {chapter.get('title', '无标题')}")
            print(f"    📝 {chapter.get('summary', '无摘要')}")
        
        return outline
    
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        return None

def save_demo_results(demo1, demo2, demo3):
    """保存演示结果"""
    results = {
        "original_story_demo": demo1,
        "continuation_demo": demo2, 
        "adaptation_demo": demo3,
        "timestamp": "2024-01-01 12:00:00"  # 实际会是当前时间
    }
    
    with open("demo_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 演示结果已保存到 demo_results.json")

def main():
    print("🌟 故事生成系统 - 自定义描述模式演示")
    print("=" * 60)
    print("这个演示将展示新功能的三种主要使用场景：")
    print("1. 原创故事创作")
    print("2. 现有故事续写")
    print("3. 经典故事改编")
    print("=" * 60)
    
    # 运行三个演示
    demo1 = demo_original_story()
    demo2 = demo_story_continuation() 
    demo3 = demo_story_adaptation()
    
    # 保存结果
    if any([demo1, demo2, demo3]):
        save_demo_results(demo1, demo2, demo3)
    
    # 总结
    print("\n" + "=" * 60)
    print("🎊 演示完成！")
    print("=" * 60)
    
    successful_demos = sum(1 for demo in [demo1, demo2, demo3] if demo is not None)
    print(f"✅ 成功演示：{successful_demos}/3 个场景")
    
    if successful_demos == 3:
        print("🎉 所有演示都成功了！新功能运行良好。")
        print("\n💡 接下来您可以：")
        print("1. 启动前端界面体验完整功能")
        print("   streamlit run outline_generator_app.py")
        print("2. 运行完整的故事生成流程")  
        print("   python main_pipeline_glm.py --generation-mode description_based ...")
        print("3. 查看详细使用指南")
        print("   cat README_新功能使用指南.md")
    else:
        print("⚠️ 部分演示失败，请检查系统配置和网络连接")

if __name__ == "__main__":
    main()
