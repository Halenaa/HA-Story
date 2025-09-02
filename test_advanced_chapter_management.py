#!/usr/bin/env python3
"""
测试高级章节管理功能：指定位置插入和冲突检测
"""

def test_conflict_detection():
    """测试内容冲突检测功能"""
    print("🧪 测试内容冲突检测...")
    
    # 模拟现有章节
    existing_chapters = [
        {"title": "奶奶是好人", "summary": "小红帽的奶奶是一个善良的老人，帮助村民解决问题"},
        {"title": "狼是坏蛋", "summary": "大灰狼是故事中的反派角色，想要伤害小红帽"},
        {"title": "白天的森林", "summary": "小红帽在明亮的白天穿越森林"},
        {"title": "小红帽胜利", "summary": "最终小红帽成功战胜了大灰狼"}
    ]
    
    def detect_content_conflicts(new_title, new_summary, existing_chapters):
        """检测新章节与现有章节的内容冲突"""
        conflicts = []
        
        # 提取关键信息进行冲突检测
        new_content = f"{new_title} {new_summary}".lower()
        
        # 定义一些常见的冲突关键词对
        conflict_patterns = [
            # 角色状态冲突
            (["死", "死亡", "牺牲", "去世"], ["活", "生存", "救", "复活"]),
            (["好人", "善良", "正义"], ["坏人", "邪恶", "反派", "敌人"]),
            (["朋友", "盟友", "帮助"], ["敌人", "背叛", "对抗"]),
            
            # 地点冲突
            (["地球", "家乡", "故乡"], ["外星", "异世界", "太空"]),
            (["城市", "都市"], ["乡村", "农村", "森林"]),
            
            # 时间冲突
            (["过去", "回忆", "历史"], ["未来", "预言", "明天"]),
            (["白天", "早晨", "中午"], ["夜晚", "深夜", "黄昏"]),
            
            # 情节状态冲突
            (["成功", "胜利", "完成"], ["失败", "失败", "放弃"]),
            (["开始", "启程", "出发"], ["结束", "完成", "到达"]),
        ]
        
        # 检查与现有章节的冲突
        for i, chapter in enumerate(existing_chapters):
            existing_content = f"{chapter['title']} {chapter.get('summary', '')}".lower()
            
            # 检查标题相似性
            if similar_titles(new_title, chapter['title']):
                conflicts.append(f"与第{i+1}章标题过于相似: '{chapter['title']}'")
            
            # 检查内容冲突模式
            for positive_words, negative_words in conflict_patterns:
                has_positive_new = any(word in new_content for word in positive_words)
                has_negative_new = any(word in new_content for word in negative_words)
                has_positive_existing = any(word in existing_content for word in positive_words)
                has_negative_existing = any(word in existing_content for word in negative_words)
                
                # 检测矛盾
                if (has_positive_new and has_negative_existing) or (has_negative_new and has_positive_existing):
                    conflicts.append(f"与第{i+1}章 '{chapter['title']}' 存在逻辑矛盾")
                    break
        
        return conflicts

    def similar_titles(title1, title2):
        """检查两个标题是否过于相似"""
        # 简单的相似性检测
        title1_words = set(title1.replace(" ", "").lower())
        title2_words = set(title2.replace(" ", "").lower())
        
        if len(title1_words) == 0 or len(title2_words) == 0:
            return False
        
        # 计算相似度
        intersection = len(title1_words & title2_words)
        union = len(title1_words | title2_words)
        similarity = intersection / union if union > 0 else 0
        
        return similarity > 0.6  # 60%以上相似度认为是相似标题
    
    # 测试用例
    test_cases = [
        {
            "title": "奶奶的真面目",
            "summary": "小红帽发现奶奶其实是一个邪恶的巫师，一直在欺骗村民",
            "expected_conflicts": True,
            "description": "与'奶奶是好人'冲突"
        },
        {
            "title": "夜晚的恐惧",
            "summary": "在深夜的森林中，小红帽遇到了更多的危险",
            "expected_conflicts": True,
            "description": "与'白天的森林'冲突"
        },
        {
            "title": "小红帽失败",
            "summary": "小红帽在与大灰狼的战斗中败北，不得不逃跑",
            "expected_conflicts": True,
            "description": "与'小红帽胜利'冲突"
        },
        {
            "title": "森林中的花朵",
            "summary": "小红帽在路上看到了美丽的花朵，停下来欣赏",
            "expected_conflicts": False,
            "description": "无冲突的章节"
        },
        {
            "title": "奶奶是好人吗",
            "summary": "小红帽对奶奶的身份产生了疑问",
            "expected_conflicts": True,
            "description": "标题相似性冲突"
        }
    ]
    
    print("\n测试冲突检测:")
    for i, test_case in enumerate(test_cases):
        print(f"\n  测试用例 {i+1}: {test_case['description']}")
        print(f"    标题: {test_case['title']}")
        print(f"    摘要: {test_case['summary'][:50]}...")
        
        conflicts = detect_content_conflicts(
            test_case['title'], 
            test_case['summary'], 
            existing_chapters
        )
        
        has_conflicts = len(conflicts) > 0
        expected = test_case['expected_conflicts']
        
        if has_conflicts == expected:
            print(f"    ✅ 检测结果正确: {'有冲突' if has_conflicts else '无冲突'}")
        else:
            print(f"    ❌ 检测结果错误: 预期{'有' if expected else '无'}冲突，实际{'有' if has_conflicts else '无'}冲突")
        
        if conflicts:
            for conflict in conflicts:
                print(f"      - {conflict}")

def test_insert_positions():
    """测试章节插入位置功能"""
    print("\n🧪 测试章节插入位置...")
    
    # 模拟初始章节列表
    initial_chapters = [
        {"chapter_id": "Chapter 1", "title": "开始", "summary": "故事开始"},
        {"chapter_id": "Chapter 2", "title": "中间", "summary": "故事发展"},
        {"chapter_id": "Chapter 3", "title": "结束", "summary": "故事结束"}
    ]
    
    def simulate_insert(chapters, new_chapter, insert_idx):
        """模拟章节插入"""
        result = chapters.copy()
        result.insert(insert_idx, new_chapter)
        
        # 更新chapter_id
        for i in range(len(result)):
            result[i]['chapter_id'] = f"Chapter {i + 1}"
        
        return result
    
    new_chapter = {"chapter_id": "Chapter X", "title": "新章节", "summary": "新添加的章节"}
    
    test_positions = [
        (0, "插入到开头"),
        (1, "插入到第1章后"),
        (2, "插入到第2章后"),
        (3, "插入到末尾")
    ]
    
    for insert_idx, description in test_positions:
        print(f"\n  {description} (位置 {insert_idx}):")
        result = simulate_insert(initial_chapters, new_chapter, insert_idx)
        
        for i, ch in enumerate(result):
            marker = "🆕" if i == insert_idx else "📄"
            print(f"    {marker} {ch['chapter_id']}: {ch['title']}")

def test_chapter_id_update():
    """测试章节ID更新逻辑"""
    print("\n🧪 测试章节ID更新...")
    
    chapters = [
        {"chapter_id": "Chapter 1", "title": "第一章"},
        {"chapter_id": "Chapter 2", "title": "第二章"},
        {"chapter_id": "Chapter 3", "title": "第三章"},
        {"chapter_id": "Chapter 4", "title": "第四章"}
    ]
    
    def update_chapter_ids_after_insert(chapters, insert_idx):
        """插入章节后更新后续章节的ID"""
        for i in range(insert_idx + 1, len(chapters)):
            chapters[i]['chapter_id'] = f"Chapter {i + 1}"
    
    print("  原始章节:")
    for ch in chapters:
        print(f"    {ch['chapter_id']}: {ch['title']}")
    
    # 在位置1插入新章节
    new_chapter = {"chapter_id": "Chapter 2", "title": "新插入章节"}
    chapters.insert(1, new_chapter)
    update_chapter_ids_after_insert(chapters, 1)
    
    print("\n  插入新章节后:")
    for ch in chapters:
        print(f"    {ch['chapter_id']}: {ch['title']}")

if __name__ == "__main__":
    print("🚀 开始测试高级章节管理功能")
    print("=" * 60)
    
    test_conflict_detection()
    test_insert_positions()
    test_chapter_id_update()
    
    print("\n🎉 所有测试完成！")
