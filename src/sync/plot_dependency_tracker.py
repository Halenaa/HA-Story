def detect_affected_chapters(story, changed_idx, character_info):
    """
    根据某一章节 plot 被改动，检测是否影响后续章节。

    参数:
        story: List[Dict]，含 plot 字段的 story.json 内容
        changed_idx: 被修改的章节索引（从0开始）
        character_info: List[Dict]，含角色姓名与设定

    返回:
        affected_chapters: List[int]
        reasons: Dict[int, str]
    """
    # 提取所有角色名字（如 ["卡尔", "莉亚", ...]）
    character_names = [char["name"] for char in character_info]

    # 当前被改动的章节内容
    changed_plot = story[changed_idx]["plot"]

    # 从该章节中找出被提及的角色
    involved_roles = [name for name in character_names if name in changed_plot]

    # 初始化输出
    affected_chapters = []
    reasons = {}

    # 检查后续章节是否继续使用这些角色
    for idx in range(changed_idx + 1, len(story)):
        plot_text = story[idx]["plot"]
        for name in involved_roles:
            if name in plot_text:
                affected_chapters.append(idx)
                if idx not in reasons:
                    reasons[idx] = f"角色“{name}”在第 {changed_idx+1} 章发生变动，但在第 {idx+1} 章仍被使用。"
                break  # 一章中有一个匹配即可标记

    return affected_chapters, reasons

# 是否你下一步想我帮你：

# ✅ 生成 affected_log.md 或 .json 报告输出（可用于论文实验）

# ✅ 编写结构影响图生成器（可视化章节间传播链）

# ✅ 将这个检测模块嵌入 main_pipeline（作为 Step 6.8）