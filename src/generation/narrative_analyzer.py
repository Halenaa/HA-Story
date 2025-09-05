import json
import os
from src.utils.utils import generate_response, convert_json
from src.constant import output_dir

# def analyze_narrative_structure(reordered_chapters, original_chapters, topic="未知", style="未知"):
#     """
#     分析重排后章节的叙述结构，为每个章节添加叙述指导
    
#     Args:
#         reordered_chapters: chapter_reorder.py的输出结果
#         original_chapters: 原始线性章节
#         topic: 故事题材
#         style: 故事风格
    
#     Returns:
#         analyzed_chapters: 包含叙述分析的章节列表
#     """
    
#     # 构建分析用的章节对比
#     chapter_info = []
#     for new_pos, ch in enumerate(reordered_chapters):
#         original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
#                            if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
#         chapter_info.append({
#             "新位置": new_pos + 1,
#             "章节ID": ch["chapter_id"],
#             "标题": ch["title"],
#             "摘要": ch.get("summary", ""),
#             "原位置": original_pos + 1 if original_pos >= 0 else "?"
#         })
    
#     info_text = json.dumps(chapter_info, ensure_ascii=False, indent=2)
    
#     prompt = f"""
# 你是叙事结构专家。分析以下非线性章节安排，为每个章节设计叙述策略。

# 【故事信息】
# 题材：{topic}
# 风格：{style}

# 【章节重排对比】
# {info_text}

# 【分析要求】
# 根据每个章节在新顺序中的位置和与原时间线的关系，设计叙述方式。
# 要考虑：
# 1. 在新顺序中的戏剧功能（开场/转折/高潮/收尾）
# 2. 与原时间线的关系（前进/后退/跳跃）
# 3. 题材风格的特点
# 4. 读者的阅读体验

# 【输出格式】
# 返回JSON数组，每个章节对应一个对象：
# [
#   {{
#     "chapter_id": "Chapter X",
#     "narrative_role": "叙述角色（用3-6个字描述）",
#     "narrative_instruction": "具体的叙述指导和技巧说明",
#     "transition_hint": "与前后章节的过渡提示"
#   }},
#   ...
# ]

# 请发挥创意，不局限于传统技巧。根据{style}风格特点设计合适的叙述方式。
# 只返回JSON，不要其他解释。
# """

#     try:
#         response = generate_response([{"role": "user", "content": prompt}])
#         analysis_result = convert_json(response)
        
#         if not isinstance(analysis_result, list):
#             print("LLM分析格式错误，使用基础模式")
#             return add_basic_analysis(reordered_chapters, original_chapters)
        
#         # 验证结果完整性
#         chapter_ids = [ch["chapter_id"] for ch in reordered_chapters]
#         analysis_ids = [item.get("chapter_id") for item in analysis_result]
        
#         if set(chapter_ids) != set(analysis_ids):
#             print("LLM分析不完整，使用基础模式")
#             return add_basic_analysis(reordered_chapters, original_chapters)
        
#         print("LLM叙述分析成功")
#         return merge_analysis_with_chapters(reordered_chapters, analysis_result)
        
#     except Exception as e:
#         print(f"LLM分析失败: {e}，使用基础模式")
#         return add_basic_analysis(reordered_chapters, original_chapters)

def analyze_narrative_structure(reordered_chapters, original_chapters, topic="未知", style="未知", performance_analyzer=None):
    """
    改进版：分析重排后章节的叙述结构，为每个章节添加叙述指导
    
    Args:
        reordered_chapters: chapter_reorder.py的输出结果
        original_chapters: 原始线性章节
        topic: 故事题材
        style: 故事风格
    
    Returns:
        analyzed_chapters: 包含叙述分析的章节列表
    """
    
    chapter_analysis = []
    for new_pos, ch in enumerate(reordered_chapters):
        original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
                           if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
        # 计算位置变化
        position_change = new_pos - original_pos if original_pos >= 0 else 0
        
        # 时间关系分析
        if position_change > 0:
            time_relation = "时间前进"
            narrative_hint = "顺序发展，可直接承接"
        elif position_change < 0:
            time_relation = "时间倒退" 
            narrative_hint = "需要倒叙/插叙处理"
        else:
            time_relation = "位置不变"
            narrative_hint = "保持原有节奏"
        
        # 角色关系上下文分析
        if new_pos == 0:
            character_context = "读者首次接触，需要建立角色认知"
        elif original_pos == 0 and new_pos > 0:
            character_context = "原开头章节，现需要补充背景"
        elif abs(position_change) > 2:
            character_context = "大幅位置变动，需要仔细处理角色关系"
        else:
            character_context = "正常承接，维持角色关系连贯性"
            
        chapter_analysis.append({
            "章节ID": ch["chapter_id"],
            "标题": ch["title"], 
            "摘要": next((orig["summary"] for orig in original_chapters 
                         if orig["chapter_id"] == ch["chapter_id"]), ""),
            "新位置": new_pos + 1,
            "原位置": original_pos + 1 if original_pos >= 0 else "未知",
            "位置变化": position_change,
            "时间关系": time_relation,
            "叙述提示": narrative_hint,
            "角色关系上下文": character_context,
            "位置跨度": abs(position_change)
        })
    
    info_text = json.dumps(chapter_analysis, ensure_ascii=False, indent=2)
    
    prompt = f"""你是专业的叙事结构专家。请为以下非线性小说章节安排设计精确的叙述策略。

【故事背景】
题材：{topic}
风格：{style}

【详细章节时间线分析】
{info_text}

【关键要求】
1. 叙述视角统一：全文必须使用同一种叙述视角，不得随意切换
2. 时间线逻辑：对于"时间倒退"的章节，必须明确使用倒叙或插叙技巧
3. 角色关系一致性：确保角色间的熟悉程度符合故事内在时间线
4. 过渡自然性：章节间的转换要流畅，避免突兀

【特殊注意事项】
- 当"位置变化"为负数时，这是时间倒退，需要特殊处理
- 当"角色关系上下文"显示首次接触时，角色不能表现得已经熟悉
- 避免在不同章节使用不同的叙述人称（第一人称/第三人称混用）

【输出格式】
返回JSON数组，每个章节包含以下字段：
- chapter_id: 章节编号
- narrative_role: 叙述角色（3-6字）
- narrative_instruction: 详细指导（必须包含具体的视角类型、时态处理、角色关系处理方式）
- transition_hint: 具体过渡方法（如何从上一章自然过渡到本章）
- timeline_method: 时间线处理（顺叙/倒叙/插叙/并行叙述）
- pov_requirement: 视角要求（必须统一：第三人称全知/第三人称限知/第一人称）
- character_consistency_note: 角色关系注意事项

请确保所有章节的pov_requirement字段完全一致。只返回JSON数组，不要其他内容。"""
    
    try:
        response = generate_response([{"role": "user", "content": prompt}], performance_analyzer=performance_analyzer, stage_name="chapter_reorder")
        analysis_result = convert_json(response)
        
        if not isinstance(analysis_result, list):
            print("LLM分析格式错误，使用基础模式")
            return add_basic_analysis(reordered_chapters, original_chapters)
        
        # 验证结果完整性
        chapter_ids = [ch["chapter_id"] for ch in reordered_chapters]
        analysis_ids = [item.get("chapter_id") for item in analysis_result]
        
        if set(chapter_ids) != set(analysis_ids):
            print("LLM分析不完整，使用基础模式")
            return add_basic_analysis(reordered_chapters, original_chapters)
        
        print("LLM叙述分析成功")
        return merge_analysis_with_chapters(reordered_chapters, analysis_result)
        
    except Exception as e:
        print(f"LLM分析失败: {e}，使用基础模式")
        return add_basic_analysis(reordered_chapters, original_chapters)

# def add_basic_analysis(reordered_chapters, original_chapters):
#     """基础的叙述分析（兜底方案）"""
#     analyzed_chapters = []
    
#     for idx, ch in enumerate(reordered_chapters):
#         original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
#                            if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
#         # 简单逻辑判断
#         if idx == 0:  # 第一个位置
#             if original_pos > len(original_chapters) // 2:
#                 role = "开场悬念"
#                 instruction = "以后期情节开场，营造悬念，不解释前因后果"
#             else:
#                 role = "正常开场"
#                 instruction = "按原有逻辑开场，为后续发展做铺垫"
#         elif original_pos < idx:  # 时间线后退
#             role = "回忆讲述"
#             instruction = "使用回忆的形式讲述，添加'让我们回到...'等过渡语言"
#         else:  # 时间线前进
#             role = "顺序发展"
#             instruction = "承接前文，按时间顺序推进故事"
        
#         analyzed_ch = dict(ch)  # 复制原有信息
#         analyzed_ch.update({
#             "narrative_role": role,
#             "narrative_instruction": instruction,
#             "transition_hint": "标准过渡"
#         })
        
#         analyzed_chapters.append(analyzed_ch)
    
#     return analyzed_chapters

def add_basic_analysis(reordered_chapters, original_chapters):
    """改进版基础的叙述分析（兜底方案）"""
    analyzed_chapters = []
    
    for idx, ch in enumerate(reordered_chapters):
        original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
                           if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
        # 简单逻辑判断
        if idx == 0:
            if original_pos > len(original_chapters) // 2:
                role = "悬念开篇"
                instruction = "第三人称限知视角，以后期情节开场营造悬念，不解释前因后果"
                timeline_method = "跳跃开场"
            else:
                role = "正常开篇"
                instruction = "第三人称限知视角，按原有逻辑开场，为后续发展做铺垫"
                timeline_method = "顺叙"
        elif original_pos < idx:
            role = "回忆讲述"
            instruction = "第三人称限知视角，使用回忆形式讲述，添加'让我们回到...'等过渡语言"
            timeline_method = "倒叙"
        else:
            role = "顺序发展"
            instruction = "第三人称限知视角，承接前文，按时间顺序推进故事"
            timeline_method = "顺叙"
        
        analyzed_ch = dict(ch)  # 复制原有信息
        analyzed_ch.update({
            "narrative_role": role,
            "narrative_instruction": instruction,
            "transition_hint": "标准过渡",
            "timeline_method": timeline_method,
            "pov_requirement": "第三人称限知",  # 强制统一视角
            "character_consistency_note": "保持角色关系逻辑"
        })
        
        analyzed_chapters.append(analyzed_ch)
    
    return analyzed_chapters

def merge_analysis_with_chapters(reordered_chapters, analysis_result):
    """将LLM分析结果与章节信息合并"""
    analyzed_chapters = []
    
    for ch in reordered_chapters:
        # 找到对应的分析
        analysis = next((item for item in analysis_result 
                        if item["chapter_id"] == ch["chapter_id"]), {})
        
        analyzed_ch = dict(ch)  # 复制原有信息
        analyzed_ch.update({
            "narrative_role": analysis.get("narrative_role", "标准叙述"),
            "narrative_instruction": analysis.get("narrative_instruction", "按常规方式展开"),
            "transition_hint": analysis.get("transition_hint", "标准过渡")
        })
        
        analyzed_chapters.append(analyzed_ch)
    
    return analyzed_chapters

def enhance_summaries_with_narrative(analyzed_chapters):
    """
    基于叙述分析增强summary字段
    """
    enhanced_chapters = []
    
    for idx, ch in enumerate(analyzed_chapters):
        original_summary = ch.get("summary", "无摘要")
        narrative_role = ch.get("narrative_role", "标准叙述")
        narrative_instruction = ch.get("narrative_instruction", "")
        
        # 生成增强的summary
        enhanced_summary = f"【{narrative_role}】{original_summary}。{narrative_instruction}"
        
        enhanced_ch = dict(ch)
        enhanced_ch["narrative_summary"] = enhanced_summary
        
        enhanced_chapters.append(enhanced_ch)
    
    return enhanced_chapters

if __name__ == "__main__":
    # 独立测试模块
    print("🧪 测试叙述分析模块")
    
    # 模拟chapter_reorder.py的输出
    original_chapters = [
        {"chapter_id": "Chapter 1", "title": "红帽启程", "summary": "机器人小红帽接到任务"},
        {"chapter_id": "Chapter 2", "title": "数据森林", "summary": "进入虚拟森林环境"},
        {"chapter_id": "Chapter 3", "title": "AI狼出现", "summary": "遭遇恶意AI程序"},
        {"chapter_id": "Chapter 4", "title": "最终战斗", "summary": "与AI狼决战"}
    ]
    
    # 模拟重排结果
    reordered_chapters = [
        {"chapter_id": "Chapter 4", "title": "最终战斗", "new_order": 1},
        {"chapter_id": "Chapter 1", "title": "红帽启程", "new_order": 2},
        {"chapter_id": "Chapter 2", "title": "数据森林", "new_order": 3},
        {"chapter_id": "Chapter 3", "title": "AI狼出现", "new_order": 4}
    ]
    
    # 测试分析
    print("原始章节：", [ch["chapter_id"] for ch in original_chapters])
    print("重排顺序：", [ch["chapter_id"] for ch in reordered_chapters])
    print()
    
    # 执行分析（这里会调用基础模式，因为没有真实LLM）
    analyzed = analyze_narrative_structure(
        reordered_chapters, original_chapters, 
        topic="小红帽", style="科幻改写"
    )
    
    print("分析结果：")
    for ch in analyzed:
        print(f"  {ch['chapter_id']}: {ch['narrative_role']}")
        print(f"    指导: {ch['narrative_instruction']}")
    
    # 测试summary增强
    enhanced = enhance_summaries_with_narrative(analyzed)
    print("\n增强summary：")
    for ch in enhanced:
        print(f"  {ch['chapter_id']}: {ch['narrative_summary']}")