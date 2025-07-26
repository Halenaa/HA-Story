from typing import List, Dict, Tuple
from src.sync.plot_dependency_tracker import detect_affected_chapters
from src.sync.regenerate_dialogue_from_plot import regenerate_dialogue_from_plot
from src.generation.expand_story import expand_story_v1

def auto_propagate_plot_update(
    story: List[Dict],
    dialogue_result: List[Dict],
    characters: List[Dict],
    changed_idx: int,
    model: str = "claude-sonnet-4-20250514",
    behavior_hint: str = ""
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    如果某章节 plot 被改，自动检测其对后续章节的影响并更新对应 plot + dialogue。
    返回更新后的 story、dialogue_result 和传播日志。
    """
    propagation_log = []

    # 检测受影响章节
    affected_idxs, reasons = detect_affected_chapters(story, changed_idx, characters)

    for idx in affected_idxs:
        old_plot = story[idx].get("plot", "")
        outline_info = {
            "chapter_id": story[idx].get("chapter_id", f"Chapter {idx+1}"),
            "title": story[idx].get("title", f"第{idx+1}章")
        }

        custom_instruction = reasons[idx]
        if behavior_hint:
            custom_instruction += f"\n前文行为提示：{behavior_hint}"

        # 重新生成 plot
        print(f"\n🔁 正在自动传播：第 {idx+1} 章 plot 更新中...")
        new_chapter = expand_story_v1([outline_info], characters, custom_instruction=custom_instruction)[0]
        story[idx]["plot"] = new_chapter["plot"]
        story[idx]["plot_updated"] = True
        story[idx]["plot_change_note"] = reasons[idx]

        # 联动生成新 dialogue
        print(f"💬 正在生成第 {idx+1} 章新对话...")
        new_dialogue = regenerate_dialogue_from_plot(
            chapter_id=story[idx]["chapter_id"],
            plot=new_chapter["plot"],
            character_info=characters,
            model=model
        )
        dialogue_result[idx]["dialogue"] = new_dialogue
        dialogue_result[idx]["regenerated"] = True

        # 记录传播日志
        propagation_log.append({
            "chapter_id": story[idx]["chapter_id"],
            "title": story[idx]["title"],
            "reason": reasons[idx],
            "plot_updated": True,
            "dialogue_updated": True
        })

    return story, dialogue_result, propagation_log
