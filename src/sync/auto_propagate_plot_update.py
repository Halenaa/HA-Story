from typing import List, Dict, Tuple
from src.sync.plot_dependency_tracker import detect_affected_chapters
from src.sync.regenerate_dialogue_from_plot import regenerate_dialogue_from_plot
from src.generation.expand_story import expand_story_v1

def auto_propagate_plot_update(
    story: List[Dict],
    dialogue_result: List[Dict],
    characters: List[Dict],
    changed_idx: int,
    model: str = "gpt-4.1",
    behavior_hint: str = ""
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    If a chapter's plot is modified, automatically detect its impact on subsequent chapters and update corresponding plot + dialogue.
    Returns updated story, dialogue_result and propagation log.
    """
    propagation_log = []

    # Detect affected chapters
    affected_idxs, reasons = detect_affected_chapters(story, changed_idx, characters)

    for idx in affected_idxs:
        old_plot = story[idx].get("plot", "")
        outline_info = {
            "chapter_id": story[idx].get("chapter_id", f"Chapter {idx+1}"),
            "title": story[idx].get("title", f"Chapter {idx+1}")
        }

        custom_instruction = reasons[idx]
        if behavior_hint:
            custom_instruction += f"\nPrevious behavior hint: {behavior_hint}"

        # Regenerate plot
        print(f"\nAuto propagating: Chapter {idx+1} plot updating...")
        new_chapter = expand_story_v1([outline_info], characters, custom_instruction=custom_instruction)[0]
        story[idx]["plot"] = new_chapter["plot"]
        story[idx]["plot_updated"] = True
        story[idx]["plot_change_note"] = reasons[idx]

        # Generate new dialogue in linkage
        print(f"Generating new dialogue for Chapter {idx+1}...")
        new_dialogue = regenerate_dialogue_from_plot(
            chapter_id=story[idx]["chapter_id"],
            plot=new_chapter["plot"],
            character_info=characters,
            model=model
        )
        dialogue_result[idx]["dialogue"] = new_dialogue
        dialogue_result[idx]["regenerated"] = True

        # Record propagation log
        propagation_log.append({
            "chapter_id": story[idx]["chapter_id"],
            "title": story[idx]["title"],
            "reason": reasons[idx],
            "plot_updated": True,
            "dialogue_updated": True
        })

    return story, dialogue_result, propagation_log
