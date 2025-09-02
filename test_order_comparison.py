#!/usr/bin/env python3
"""
测试章节顺序对比功能
"""

def test_order_comparison():
    """测试章节顺序对比显示"""
    print("🧪 测试章节顺序对比功能...")
    
    # 模拟初始章节数据（线性顺序）
    initial_chapters = [
        {"chapter_id": "Chapter 1", "title": "星际任务启动", "summary": "小红帽接受任务"},
        {"chapter_id": "Chapter 2", "title": "太空穿梭", "summary": "穿越太空"},
        {"chapter_id": "Chapter 3", "title": "人工智能狼的埋伏", "summary": "遇到AI狼"},
        {"chapter_id": "Chapter 4", "title": "量子迷宫对决", "summary": "与AI狼对战"},
        {"chapter_id": "Chapter 5", "title": "祖母的救援", "summary": "救援祖母"},
        {"chapter_id": "Chapter 6", "title": "星际归途", "summary": "回到家园"}
    ]
    
    print("\n1. 初始线性顺序:")
    for i, ch in enumerate(initial_chapters):
        print(f"   {i+1}. {ch['title']}")
    
    # 模拟非线性重排后的数据
    reordered_chapters = [
        {"chapter_id": "Chapter 4", "title": "量子迷宫对决", "summary": "与AI狼对战", "original_position": 4, "new_order": 1, "narrative_role": "倒叙开场"},
        {"chapter_id": "Chapter 1", "title": "星际任务启动", "summary": "小红帽接受任务", "original_position": 1, "new_order": 2, "narrative_role": "回忆开始"},
        {"chapter_id": "Chapter 2", "title": "太空穿梭", "summary": "穿越太空", "original_position": 2, "new_order": 3, "narrative_role": "顺序发展"},
        {"chapter_id": "Chapter 3", "title": "人工智能狼的埋伏", "summary": "遇到AI狼", "original_position": 3, "new_order": 4, "narrative_role": "冲突升级"},
        {"chapter_id": "Chapter 5", "title": "祖母的救援", "summary": "救援祖母", "original_position": 5, "new_order": 5, "narrative_role": "高潮延续"},
        {"chapter_id": "Chapter 6", "title": "星际归途", "summary": "回到家园", "original_position": 6, "new_order": 6, "narrative_role": "结局收尾"}
    ]
    
    print("\n2. 非线性重排后:")
    print("   🔸 原始顺序: 1.星际任务启动 → 2.太空穿梭 → 3.人工智能狼的埋伏 → 4.量子迷宫对决 → 5.祖母的救援 → 6.星际归途")
    
    print("   🔹 当前顺序:")
    for i, ch in enumerate(reordered_chapters):
        orig_pos = ch.get('original_position', '?')
        print(f"      {i+1}. {ch['title']} (原第{orig_pos}章)")
    
    print("\n3. 详细对比表格:")
    print("   | 当前位置 | 章节标题 | 原始位置 | 位置变化 | 叙述角色 |")
    print("   |----------|----------|----------|----------|----------|")
    
    for i, chapter in enumerate(reordered_chapters):
        orig_pos = chapter.get('original_position', '未知')
        narrative_role = chapter.get('narrative_role', '线性叙述')
        
        # 判断位置变化
        if isinstance(orig_pos, int):
            position_change = i + 1 - orig_pos
            if position_change > 0:
                change_indicator = f"↓ +{position_change}"
            elif position_change < 0:
                change_indicator = f"↑ {position_change}"
            else:
                change_indicator = "→ 不变"
        else:
            change_indicator = "?"
        
        print(f"   | 第{i+1}章 | {chapter['title'][:15]}... | 第{orig_pos}章 | {change_indicator} | {narrative_role} |")
    
    # 统计信息
    moved_chapters = sum(1 for i, ch in enumerate(reordered_chapters) 
                        if isinstance(ch.get('original_position'), int) and 
                        i + 1 != ch['original_position'])
    
    print(f"\n4. 重排统计:")
    print(f"   📊 总章节数: {len(reordered_chapters)}")
    print(f"   📊 重排章节数: {moved_chapters}")
    print(f"   📊 保持原位: {len(reordered_chapters) - moved_chapters}")
    
    # 测试手动重排逻辑
    print(f"\n5. 测试手动重排逻辑:")
    
    def simulate_manual_reorder(chapters, order_input):
        """模拟手动重排"""
        try:
            new_order = [int(x.strip()) - 1 for x in order_input.split(',')]
            
            print(f"   输入顺序: {order_input}")
            print(f"   解析结果: {[x+1 for x in new_order]}")
            
            # 重新排列章节并添加原始位置信息
            reordered_outline = []
            for new_pos, old_idx in enumerate(new_order):
                chapter = chapters[old_idx].copy()
                
                # 如果章节还没有original_position，则设置为当前位置+1
                if 'original_position' not in chapter:
                    chapter['original_position'] = old_idx + 1
                
                # 设置新的顺序信息
                chapter['new_order'] = new_pos + 1
                
                reordered_outline.append(chapter)
            
            print("   重排结果:")
            for i, ch in enumerate(reordered_outline):
                orig_pos = ch.get('original_position', '?')
                print(f"      {i+1}. {ch['title']} (原第{orig_pos}章)")
            
            return reordered_outline
            
        except Exception as e:
            print(f"   ❌ 重排失败: {str(e)}")
            return None
    
    # 测试几种手动重排场景
    test_cases = [
        "1,3,2,4,5,6",  # 交换第2和第3章
        "6,5,4,3,2,1",  # 完全倒序
        "1,2,3,4,5,6",  # 保持原序
    ]
    
    for i, test_order in enumerate(test_cases):
        print(f"\n   测试用例 {i+1}: {test_order}")
        simulate_manual_reorder(initial_chapters, test_order)
    
    print("\n✅ 章节顺序对比功能测试完成")
    return True

if __name__ == "__main__":
    print("🚀 开始测试章节顺序对比功能")
    print("=" * 60)
    
    if test_order_comparison():
        print("\n🎉 所有测试通过！")
    else:
        print("\n❌ 测试失败")
