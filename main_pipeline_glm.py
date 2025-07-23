import os
import argparse
from src.constant import output_dir
from src.utils.utils import save_md, save_json, load_json, extract_plot_list
from src.generation.outline_generator import generate_outline
from src.generation.chapter_reorder import reorder_chapters
from src.generation.generate_characters import generate_characters_v1
from src.generation.expand_story import expand_story_v1
from src.compile_story import compile_full_story_by_chapter
from src.enhance_story import enhance_story_with_transitions, polish_dialogues_in_story
from src.generation.dialogue_inserter import analyze_dialogue_insertions, run_dialogue_insertion
from src.utils.utils import extract_behavior_llm, convert_dialogue_dict_to_list
from src.sync.plot_sync_manager import sync_plot_and_dialogue_from_behavior
from src.sync.auto_propagate_plot_update import auto_propagate_plot_update
from src.analysis.character_state_tracker import run_character_state_tracker


def ensure_output_dir(version):
    folder = os.path.join(output_dir, version)
    os.makedirs(folder, exist_ok=True)
    return folder

def step_file(version, filename):
    return os.path.join(output_dir, version, filename)

def main(version="test", reorder_mode="sequential", use_cache=True, topic="小红帽", style="科幻改写", behavior_model="gpt-4o"):
    print(f"\n开始运行 main_pipeline")
    print(f"版本: {version}，顺序模式: {reorder_mode}，使用缓存: {use_cache}")
    print(f"题材: {topic}，风格: {style}\n")
    folder = ensure_output_dir(version)
    role_state = {}

    # Step 1: Outline Generation
    outline_path = step_file(version, "test_outline.json")
    if use_cache and os.path.exists(outline_path):
        outline = load_json(outline_path)
        print("已加载 outline")
    else:
        outline = generate_outline(topic=topic, style=style, custom_instruction="")
        save_json(outline, version, "test_outline.json")
        print("outline 保存完成")

    # Step 2: Chapter Reordering
    reorder_outline = reorder_chapters(outline, mode=reorder_mode)
    save_json(reorder_outline, version, "test_reorder_outline.json")
    print("章节顺序处理完成")

    # Step 3: Character Generation
    character_path = step_file(version, "characters.json")
    if use_cache and os.path.exists(character_path):
        characters = load_json(character_path)
        print("已加载角色设定")
    else:
        characters = generate_characters_v1(reorder_outline)
        save_json(characters, version, "characters.json")
        print("生成角色设定完成")

    # Step 4: Story Expansion
    plot_path = step_file(version, "story.json")
    if use_cache and os.path.exists(plot_path):
        story = load_json(plot_path)
        print("已加载故事内容")
    else:
        story = expand_story_v1(reorder_outline, characters, custom_instruction="")
        for idx, ch in enumerate(story):
            ch.setdefault("chapter_id", reorder_outline[idx]["chapter_id"])
            ch.setdefault("title", reorder_outline[idx]["title"])
        save_json(story, version, "story.json")
        print("故事内容生成完成")

    # Step 5: Dialogue Structure Marks
    plot_list = extract_plot_list(story)
    structure_marks = analyze_dialogue_insertions(plot_list, characters)
    save_json(structure_marks, version, "structure_marks.json")
    print("对话插入结构分析完成")

    # Step 6: Dialogue Generation
    dialogue_result = run_dialogue_insertion(plot_list, characters)
    save_json(dialogue_result, version, "dialogue_marks.json")

    # Step 6.5: LLM行为提取
    behavior_signals, recommendations = [], []
    for idx, d in enumerate(dialogue_result):
        dlg = d.get("dialogue")
        if isinstance(dlg, dict):
            dlg = convert_dialogue_dict_to_list(dlg)
            d["dialogue"] = dlg
        if isinstance(dlg, list):
            try:
                result = extract_behavior_llm(dlg, model=behavior_model, confirm=True)
                for role, states in result.items():
                    role_state.setdefault(role, []).extend([s for s in states if s not in role_state[role]])
                    behavior_signals.extend([f"{role}：{s}" for s in states])
            except Exception as e:
                print(f"⚠️ 第 {idx+1} 章行为提取失败：{e}")

    save_json({"behaviors": behavior_signals, "recommendations": recommendations}, version, "behavior_trace.json")
    print("对话内容生成完成")

    # Step 6.7: 联动机制
    story, dialogue_result, revision_log = sync_plot_and_dialogue_from_behavior(
        story, dialogue_result, characters, model=behavior_model)

    # Step 7: 保存输出
    save_json(role_state, version, "role_state.json")
    save_json(story, version, "story_updated.json")
    save_json(dialogue_result, version, "dialogue_updated.json")
    save_json(revision_log, version, "revision_log.json")

    compiled_updated = compile_full_story_by_chapter(story, dialogue_result)
    save_md(compiled_updated, os.path.join(folder, "novel_story_updated.md"))
    print("novel_story_updated.md 已生成")

    enhance_story_with_transitions(task_name=version, input_story_file="story_updated.json")
    polish_dialogues_in_story(task_name=version, input_dialogue_file="dialogue_updated.json")
    print("增强版本已完成")

    run_character_state_tracker(version=version, dialogue_file="dialogue_updated.json", model=behavior_model)
    print(f"\n全部流程执行完毕！结果保存在：{folder}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="test", help="版本名称")
    parser.add_argument("--reorder", type=str, default="random", choices=["sequential", "reverse", "random"], help="章节顺序控制")
    parser.add_argument("--no-cache", action="store_true", help="是否忽略已有结果")
    parser.add_argument("--topic", type=str, default="小红帽", help="故事题材")
    parser.add_argument("--style", type=str, default="科幻改写", help="故事风格")
    parser.add_argument("--behavior-model", type=str, default="gpt-4o", help="行为识别模型")
    args = parser.parse_args()

    main(
        version=args.version,
        reorder_mode=args.reorder,
        use_cache=not args.no_cache,
        topic=args.topic,
        style=args.style,
        behavior_model=args.behavior_model
    )
