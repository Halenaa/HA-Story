import os
import argparse
from src.constant import output_dir
from src.utils.utils import save_md, save_json, load_json, extract_plot_list
from src.generation.outline_generator import generate_outline
from src.generation.chapter_reorder import reorder_chapters
from src.generation.generate_characters import generate_characters_v1
from src.generation.expand_story import expand_story_v1
from src.compile_story import compile_full_story_by_sentence
from src.enhance_story import enhance_story_with_transitions, polish_dialogues_in_story
from src.generation.dialogue_inserter import analyze_dialogue_insertions, run_dialogue_insertion, analyze_dialogue_insertions_v2
from src.utils.utils import extract_behavior_llm, convert_dialogue_dict_to_list
from src.sync.plot_sync_manager import sync_plot_and_dialogue_from_behavior
from src.sync.auto_propagate_plot_update import auto_propagate_plot_update
from src.analysis.character_state_tracker import run_character_state_tracker
from src.utils.logger import append_log, build_log_record, build_simple_log, init_log_path
from src.version_namer import build_version_name 



def ensure_output_dir(version):
    folder = os.path.join(output_dir, version)
    os.makedirs(folder, exist_ok=True)
    return folder

def step_file(version, filename):
    return os.path.join(output_dir, version, filename)

def main( 
    version="test",
    reorder_mode="linear",
    use_cache=False,
    topic="小红帽",
    style="科幻改写",
    behavior_model="gpt-4.1",
    temperature=0.7,
    seed=1
):
    #  自动构建版本名称
    if version == "test":
        version = build_version_name(
            topic=topic,
            style=style,
            temperature=temperature,
            seed=seed,
            order_mode=reorder_mode
        )

    print(f"\n开始运行 main_pipeline")
    print(f"版本: {version}，顺序模式: {reorder_mode}，使用缓存: {use_cache}")
    print(f"题材: {topic}，风格: {style}\n")
    folder = ensure_output_dir(version)
    role_state = {}

    plot_log_path = init_log_path(folder, "plot")
    dialogue_log_path = init_log_path(folder, "dialogue")

    # Step 1: Outline Generation
    # Step 1: Outline Generation (shared across versions)
    outline_base_path = os.path.join(output_dir, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}outline.json")
    os.makedirs(os.path.dirname(outline_base_path), exist_ok=True)

    if os.path.exists(outline_base_path):
        outline = load_json(outline_base_path)
        print(f"已加载共享 outline：{outline_base_path}")
    else:
        outline = generate_outline(topic=topic, style=style, custom_instruction="")
        save_json(outline, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
        print(f"生成并保存共享 outline：{outline_base_path}")

    

    # outline_path = step_file(version, "test_outline.json")
    # if use_cache and os.path.exists(outline_path):
    #     outline = load_json(outline_path)
    #     print("已加载 outline")
    # else:
    #     outline = generate_outline(topic=topic, style=style, custom_instruction="")
    #     save_json(outline, version, "test_outline.json")
    #     print("outline 保存完成")

    # Step 2: Chapter Reordering
    # reorder_outline = reorder_chapters(outline, mode=reorder_mode)
    # save_json(reorder_outline, version, "test_reorder_outline.json")
    # for ch in reorder_outline:
    #     match = next((x for x in outline if x["chapter_id"] == ch["chapter_id"]), None)
    #     if match:
    #         ch["summary"] = match["summary"]

    # print("章节顺序处理完成")

    # Step 2: 章节顺序处理
    if reorder_mode == "linear":
        reorder_outline_raw = outline
        save_json(outline, version, "test_outline.json")
        print("✅ 使用 linear 顺序（直接来自 outline）")

    elif reorder_mode == "nonlinear":
        save_json(outline, version, "test_outline_linear.json")
        reorder_path = os.path.join(output_dir, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
        os.makedirs(os.path.dirname(reorder_path), exist_ok=True)

        if os.path.exists(reorder_path):
            reorder_outline_raw = load_json(reorder_path)
            print(f"✅ 已加载 cached nonlinear 顺序：{reorder_path}")
        else:
            reorder_outline_raw = reorder_chapters(outline, mode="nonlinear")

            # ✅ 添加日志记录
            reorder_log_path = init_log_path(folder, "reorder")
            reorder_log = build_simple_log(
                module="chapter_reorder",
                task_name=version,
                input_data={"outline": outline},
                output_data={"reorder_result": reorder_outline_raw}
            )
            append_log(reorder_log_path, reorder_log)

            # ✅ 检查是否真的生成了 new_order 字段
            if not any("new_order" in ch for ch in reorder_outline_raw):
                print("⚠️ LLM 重排失败：未检测到任何 new_order 字段，回退为原始顺序")
            else:
                print("✅ reorder_chapters 成功生成非线性顺序")

            save_json(reorder_outline_raw, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
            print(f"✅ 生成 nonlinear 顺序并缓存：{reorder_path}")

    else:
        raise ValueError("order_mode 必须为 'linear' 或 'nonlinear'")

    # ✅ 统一结构：补全 summary 字段
    reorder_outline = []
    for reordered_ch in reorder_outline_raw:
        match = next((x for x in outline if x["chapter_id"] == reordered_ch["chapter_id"]), None)
        if match:
            merged = {
                "chapter_id": reordered_ch["chapter_id"],
                "title": reordered_ch["title"],
                "summary": match.get("summary", "")
            }
            if "new_order" in reordered_ch:
                merged["new_order"] = reordered_ch["new_order"]
            reorder_outline.append(merged)

    save_json(reorder_outline, version, "test_reorder_outline.json")
    print("✅ 章节顺序处理完成（已保留 summary）")



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

            log = build_log_record(
                module="expand_story", step="plot",
                task_name=version, chapter_id=ch["chapter_id"],
                model=behavior_model, 
                input_data={"outline": reorder_outline[idx]},
                output_data={"plot": ch["plot"]},
                temperature=temperature, 
                seed=seed
            )
            append_log(plot_log_path, log)

        save_json(story, version, "story.json")
        print("故事内容生成完成")

    # Step 5 & 6: 新版对话生成（句子级分析 + 章节级兼容）
    chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(story, characters)

    # 保存三种格式的数据
    save_json(chapter_results, version, "dialogue_marks.json")        # 兼容格式
    save_json(sentence_results, version, "sentence_dialogues.json")    # 句子级详细分析
    save_json(behavior_timeline, version, "behavior_timeline_raw.json")  # 原始behavior数据

    # 如果需要sync，用章节级
    if len(story) == len(chapter_results):
        story, chapter_results_updated, revision_log = sync_plot_and_dialogue_from_behavior(
            story, chapter_results, characters, model=behavior_model)
    else:
        chapter_results_updated = chapter_results  # 🔴 添加这行
        revision_log = []

    # 记录日志（用章节级保持兼容）
    for ch, dlg in zip(story, chapter_results_updated):  # 🔴 使用 chapter_results_updated
        log = build_log_record(
            module="dialogue_inserter", step="dialogue",
            task_name=version, chapter_id=ch["chapter_id"],
            model=behavior_model,
            input_data={"plot": ch["plot"]},
            output_data={"dialogue": dlg["dialogue"]},
            temperature=temperature, seed=seed
        )
        append_log(dialogue_log_path, log)
    # # 🎯 compile_story 使用句子级数据
    # compiled_story = compile_full_story_by_sentence(story, sentence_results)
    # save_md(compiled_story, os.path.join(folder, "novel_story.md"))
    # # 设置dialogue_result为chapter_results以保持后续流程兼容
    # dialogue_result = chapter_results
    # print("新版对话生成完成（句子级分析 + 章节级兼容）")

    # # ✅ 放这里，运行对白生成后立即检查长度是否匹配
    # if len(story) != len(dialogue_result):
    #     print(f"⚠️ 警告：story 有 {len(story)} 章，但 dialogue_result 只有 {len(dialogue_result)} 条对白，可能有章节对白生成失败。")
    
    # for ch, dlg in zip(story, dialogue_result):
    #     log = build_log_record(
    #         module="dialogue_inserter", step="dialogue",
    #         task_name=version, chapter_id=ch["chapter_id"],
    #         model=behavior_model,
    #         input_data={"plot": ch["plot"]},
    #         output_data={"dialogue": dlg["dialogue"]},
    #         temperature=temperature, seed=seed
    #     )
    #     append_log(dialogue_log_path, log)

    # 替换为：
    # Step 6.5: 新版behavior保存（已在v2中提取）
    # 组织角色弧线
    character_arcs = {}
    for item in behavior_timeline:
        char = item["character"]
        if char not in character_arcs:
            character_arcs[char] = []
        character_arcs[char].append({
            "chapter": item["chapter_id"],
            "sentence": item["sentence_index"],
            "behavior": item["behavior"],
            "scene": item["scene_context"][:30] + "..." if len(item["scene_context"]) > 30 else item["scene_context"]
        })

    # 生成完整的behavior_trace
    behavior_trace = {
        "timeline": behavior_timeline,
        "character_arcs": character_arcs,
        "statistics": {
            "total_dialogue_moments": len(behavior_timeline),
            "characters_behavior_count": {char: len(arcs) for char, arcs in character_arcs.items()}
        },
        "legacy_behaviors": [f"{item['character']}：{item['behavior']}" for item in behavior_timeline]
    }

    save_json(behavior_trace, version, "behavior_trace.json")

    # 兼容role_state
    role_state = {}
    for item in behavior_timeline:
        role = item["character"]
        behavior = item["behavior"]
        role_state.setdefault(role, [])
        if behavior not in role_state[role]:
            role_state[role].append(behavior)

    print("新版behavior trace生成完成")

    # # Step 6.5: LLM行为提取
    # behavior_signals, recommendations = [], []
    # for idx, d in enumerate(dialogue_result):
    #     dlg = d.get("dialogue")
    #     if isinstance(dlg, dict):
    #         dlg = convert_dialogue_dict_to_list(dlg)
    #         d["dialogue"] = dlg
    #     if isinstance(dlg, list):
    #         try:
    #             result = extract_behavior_llm(dlg, model=behavior_model, confirm=False)
    #             for role, states in result.items():
    #                 role_state.setdefault(role, []).extend([s for s in states if s not in role_state[role]])
    #                 behavior_signals.extend([f"{role}：{s}" for s in states])
    #         except Exception as e:
    #             print(f"⚠️ 第 {idx+1} 章行为提取失败：{e}")

    # save_json({"behaviors": behavior_signals, "recommendations": recommendations}, version, "behavior_trace.json")
    # print("对话内容生成完成")


    # Step 7: 保存输出
    save_json(role_state, version, "role_state.json")
    save_json(story, version, "story_updated.json")
    save_json(sentence_results, version, "dialogue_updated.json") 
    save_json(revision_log, version, "revision_log.json")

    # ✅ 保存最初的 novel_story.md（plot + dialogue 原始合并版）
    # from src.compile_story import compile_full_story_by_chapter
    # compiled_story = compile_full_story_by_chapter(story, dialogue_result)
    # save_md(compiled_story, os.path.join(folder, "novel_story.md"))
    # print("novel_story.md 已生成（原始合成版）")

    compiled_updated = compile_full_story_by_sentence(story, sentence_results)
    save_md(compiled_updated, os.path.join(folder, "novel_story.md")) 
    print("novel_story.md 已生成")

    enhance_story_with_transitions(task_name=version, input_story_file="story_updated.json")
    polish_dialogues_in_story(task_name=version, input_dialogue_file="dialogue_updated.json")
    print("增强版本已完成")

    run_character_state_tracker(version=version, dialogue_file="dialogue_updated.json", model=behavior_model)
    print(f"\n全部流程执行完毕！结果保存在：{folder}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="test", help="版本名称")
    parser.add_argument("--reorder", type=str, default="linear", choices=["linear", "nonlinear"], help="章节顺序控制")
    parser.add_argument("--no-cache", action="store_true", help="是否忽略已有结果")
    parser.add_argument("--topic", type=str, default="小红帽", help="故事题材")
    parser.add_argument("--style", type=str, default="科幻改写", help="故事风格")
    parser.add_argument("--behavior-model", type=str, default="gpt-4.1", help="行为识别模型")
    parser.add_argument("--temperature", type=float, default=0.7, help="LLM temperature")
    parser.add_argument("--seed", type=int, default=42, help="生成随机种子")

    args = parser.parse_args()


    main(
        version=args.version,
        reorder_mode=args.reorder,
        use_cache=not args.no_cache,
        topic=args.topic,
        style=args.style,
        behavior_model=args.behavior_model,
        temperature=args.temperature,
        seed=args.seed
    )

