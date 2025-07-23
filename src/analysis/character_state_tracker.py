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
    提取每章每个角色的行为状态，生成角色状态随章节演化时间线。
    返回结构：{Chapter X: {角色: [状态, ...]}}
    """
    state_log = {}

    for idx, item in enumerate(dialogue_data):
        chapter_key = f"Chapter {idx + 1}"
        dialogue_block = item.get("dialogue", [])
        if not dialogue_block:
            continue

        try:
            result = extract_behavior_llm(dialogue_block, model=model, confirm=confirm)
            state_log[chapter_key] = result
        except Exception as e:
            print(f"第 {chapter_key} 章提取失败：{e}")
            state_log[chapter_key] = {}

    return state_log

def run_character_state_tracker(
    version: str = "test",
    dialogue_file: str = "dialogue_updated.json",
    model: str = None
) -> Dict[str, Dict[str, List[str]]]:
    """
    主函数：加载 dialogue，提取角色状态，保存为 role_state.json
    """
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o")

    print(f"开始提取角色状态：版本={version}, 模型={model}")
    base_dir = os.path.join(output_dir, version)
    dialogue_path = os.path.join(base_dir, dialogue_file)

    if not os.path.exists(dialogue_path):
        print(f"未找到 dialogue 文件：{dialogue_path}")
        return {}

    dialogue_data = load_json(dialogue_path)
    state_log = extract_character_state_timeline(dialogue_data, model=model)

    save_json(state_log, version, "role_state.json")
    print(f"已保存角色状态时间线：{os.path.join(base_dir, 'role_state.json')}")
    return state_log
