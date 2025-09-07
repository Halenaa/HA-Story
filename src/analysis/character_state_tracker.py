import os
import json
from typing import Dict, List
from src.utils.utils import extract_behavior_llm, load_json, save_json
from src.constant import output_dir

def extract_character_state_timeline(
    dialogue_data: List[Dict],
    model: str,
    confirm: bool = False
) -> Dict[str, Dict[str, List[str]]]:
    """
    Extract behavior states of each character in each chapter, generate character state evolution timeline.
    Return structure: {Chapter X: {character: [state, ...]}}
    """
    state_log = {}

    for idx, item in enumerate(dialogue_data):
        # Fix: Read real chapter_id from data
        if isinstance(item, list) and len(item) > 0:
            # sentence_results format: each item is sentence-level data
            chapter_id = item[0].get("chapter_id", f"Chapter {idx + 1}")
        else:
            # chapter_results format: each item is chapter-level data
            chapter_id = item.get("chapter_id", f"Chapter {idx + 1}")
        
        chapter_key = chapter_id  #  Use real ID directly
        dialogue_block = item.get("dialogue", [])
        if not dialogue_block:
            continue

        try:
            result = extract_behavior_llm(dialogue_block, model=model, confirm=confirm)
            state_log[chapter_key] = result
        except Exception as e:
            print(f"Chapter {chapter_key} extraction failed: {e}")
            state_log[chapter_key] = {}

    return state_log


def run_character_state_tracker(
    version: str = "test",
    dialogue_file: str = "dialogue_updated.json",
    model: str = None
) -> Dict[str, Dict[str, List[str]]]:
    """
    Main function: Load dialogue, extract character states, save as role_state.json
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4.1")

    print(f"Starting character state extraction: version={version}, model={model}")
    base_dir = os.path.join(output_dir, version)
    dialogue_path = os.path.join(base_dir, dialogue_file)

    if not os.path.exists(dialogue_path):
        print(f"Dialogue file not found: {dialogue_path}")
        return {}

    dialogue_data = load_json(dialogue_path)
    state_log = extract_character_state_timeline(dialogue_data, model=model)

    save_json(state_log, version, "role_state.json")
    print(f"Character state timeline saved: {os.path.join(base_dir, 'role_state.json')}")
    return state_log
