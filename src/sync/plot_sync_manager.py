# File path suggestion: src/sync/plot_sync_manager.py

from src.sync.update_plot_from_dialogue import update_plot_from_dialogue
from src.sync.regenerate_dialogue_from_plot import regenerate_dialogue_from_plot

def sync_plot_and_dialogue_from_behavior(story, dialogue_result, characters, model="gpt-4.1"):
    """
    Linked update module: based on behavior in dialogue → update plot → regenerate dialogue.

    Returns:
        - Updated story
        - Updated dialogue_result  
        - revision_log: Records whether each chapter was modified, change summaries, etc.
    """
    revision_log = []
    updated_story = story.copy()
    updated_dialogue = dialogue_result.copy()

    for idx, (ch, dlg_entry) in enumerate(zip(updated_story, updated_dialogue)):

        if not dlg_entry.get("dialogue"):
            revision_log.append({
                "chapter_id": ch["chapter_id"],
                "title": ch.get("title", ""),
                "plot_updated": False,
                "plot_change_note": "",
                "dialogue_updated": False
            })
            continue

        # Step 1: Dialogue-driven plot update
        result = update_plot_from_dialogue(
            chapter_id = ch.get("chapter_id", f"chapter_{idx}"),
            original_plot=ch["plot"],
            dialogue=dlg_entry["dialogue"],
            character_info=characters,
            model=model
        )

        if result.get("changed"):
            ch["plot"] = result["updated_plot"]
            ch["plot_updated"] = True
            ch["plot_change_note"] = result["change_summary"]

            # Step 2: Plot changed → linked update dialogue
            new_dialogue = regenerate_dialogue_from_plot(
                chapter_id=ch["chapter_id"],
                plot=result["updated_plot"],
                character_info=characters,
                model=model
            )
            dlg_entry["dialogue"] = new_dialogue
            dlg_entry["regenerated"] = True
        else:
            ch["plot_updated"] = False
            ch["plot_change_note"] = ""
            dlg_entry["regenerated"] = False

        revision_log.append({
            "chapter_id": ch["chapter_id"],
            "title": ch.get("title", ""),
            "plot_updated": ch["plot_updated"],
            "plot_change_note": ch["plot_change_note"],
            "dialogue_updated": dlg_entry["regenerated"]
        })

    return updated_story, updated_dialogue, revision_log
