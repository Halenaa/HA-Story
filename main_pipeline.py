import os
import argparse
from src.constant import output_dir
from src.utils.utils import save_md  
from src.utils.utils import save_json, load_json, extract_plot_list
from src.generation.outline_generator import generate_outline
from src.generation.chapter_reorder import reorder_chapters
from src.generation.generate_characters import generate_characters_v1
from src.generation.expand_story import expand_story_v1
from src.compile_story import compile_full_story_by_chapter
from src.enhance_story import enhance_story_with_transitions, polish_dialogues_in_story
from src.generation.dialogue_inserter import (
    analyze_dialogue_insertions,
    run_dialogue_insertion
)
from dotenv import load_dotenv
load_dotenv()

def interactive_loop_generate_outline_single(chapter_idx, old_chapter, generate_fn):
    print(f"\n正在处理第 {chapter_idx+1} 章：{old_chapter['title']}")
    instruction = input("请输入你的修改要求（如留空则默认生成）: ")

    while True:
        new_chapter = generate_fn(old_chapter, instruction)
        print("\n生成的新章节标题和内容：")
        print(f"chapter_id: {new_chapter['chapter_id']}")
        print(f"title     : {new_chapter['title']}")
        ans = input("是否接受这个版本？（y=接受, n=再生成, m=手动输入）: ").strip().lower()
        if ans == 'y':
            return new_chapter
        elif ans == 'm':
            new_title = input("请输入新的章节标题: ")

            # 🔧 自动生成 summary
            from src.utils.utils import generate_response  # 确保你 utils.py 中已有该函数
            prompt = f"你是一个小说编剧，请为章节标题“{new_title}”生成一句话 summary（1~2句话）"
            summary_text = generate_response([{"role": "user", "content": prompt}])

            print(f"生成的章节 summary：{summary_text.strip()}")
            use_it = input("是否使用这个 summary？（y=接受, m=手动输入）: ").strip().lower()
            if use_it != "y":
                summary_text = input("请输入你自己的 summary 内容: ")

            new_chapter = {
                "chapter_id": f"Chapter {chapter_idx+1}",
                "title": new_title,
                "summary": summary_text.strip()
            }
            return new_chapter
        instruction = input("请重新输入提示（可回车保留上次）: ") or instruction

def regenerate_outline_single(old_chapter, instruction):
    from src.generation.outline_generator import generate_outline

    chapter_id = old_chapter['chapter_id']
    idx = int(chapter_id.split(" ")[-1]) - 1

    # outline_list = generate_outline(topic="小红帽", style="科幻改写", custom_instruction=instruction)
    from dotenv import load_dotenv
    load_dotenv()
    custom_prompt = os.getenv("CUSTOM_PROMPT", "")
    combined_instruction = (instruction + "\n" + custom_prompt).strip()
    outline_list = generate_outline(topic="小红帽", style="科幻改写", custom_instruction=combined_instruction)

    if idx >= len(outline_list):
        print("生成的章节数不够，返回最后一章。")
        return outline_list[-1]

    return outline_list[idx]

def regenerate_plot_single(chapter_outline, characters, instruction):
    from src.generation.expand_story import expand_story_v1
    story = expand_story_v1([chapter_outline], characters, custom_instruction=instruction)
    return story[0]

def interactive_loop_generate_plot_single(chapter_idx, old_plot, chapter_outline, characters, behavior_hint=""):
    print(f"\n正在处理第 {chapter_idx+1} 章 plot：")
    print(f"当前情节（旧版）:\n{old_plot[:120]}...\n")

    instruction = input("请输入你的修改要求（如留空则默认生成）: ")
    if behavior_hint:
        instruction = (instruction + "\n" if instruction else "") + behavior_hint

    while True:
        new_chapter = regenerate_plot_single(chapter_outline, characters, instruction)
        print("\n生成的新章节内容：\n")
        print(new_chapter['plot'])

        ans = input("是否接受这个版本？（y=接受, n=再生成, m=手动输入）: ").strip().lower()

        if ans == 'y':
            return new_chapter

        elif ans == 'm':
            print("请输入你自定义的 plot 内容（可多行，空行结束）:")
            manual_plot = ""
            while True:
                line = input()
                if line.strip() == "":
                    break
                manual_plot += line.strip() + " "
            return {
                "chapter_id": chapter_outline["chapter_id"],
                "title": chapter_outline["title"],
                "plot": manual_plot.strip()
            }

        # 否则，重新输入提示继续循环
        instruction = input("请重新输入提示（可回车保留上次）: ") or instruction

def interactive_run_dialogue_insertion(plot_list, characters):
    from src.generation.dialogue_inserter import generate_dialogue_for_plot  # 你原来的核心函数

    dialogue_marks = []
    for idx, plot in enumerate(plot_list):
        print(f"\n第 {idx+1} 章：")
        print(f"剧情概要：{plot[:80]}...")

        use_dialogue = input("是否为该段剧情插入对话？（y/n）: ").strip().lower()
        if use_dialogue != 'y':
            dialogue_marks.append({"sentence": plot, "dialogue": None})
            continue

        style_hint = input("请输入对话风格提示（如留空则默认）：")
        instruction = f"{plot}\n风格要求：{style_hint}" if style_hint else plot

        while True:
            result = generate_dialogue_for_plot(instruction, characters)
            print("\n生成的对话内容：")
            for line in result:
                print(f"{line['speaker']}: {line['line']}")

            ans = input("是否接受？（y=接受, n=重试, m=手动输入）: ").strip().lower()
            if ans == 'y':
                dialogue_marks.append({"sentence": plot, "dialogue": result})
                break
            elif ans == 'm':
                manual_lines = []
                while True:
                    line = input("输入角色对话（格式：角色: 内容，留空结束）: ")
                    if not line:
                        break
                    if ":" not in line:
                        print("⚠️ 格式错误，请使用 '角色: 内容' 格式重新输入。")
                        continue
                    spk, txt = line.split(":", 1)
                    manual_lines.append({"speaker": spk.strip(), "line": txt.strip()})
                dialogue_marks.append({"sentence": plot, "dialogue": manual_lines})
                break
    return dialogue_marks

def extract_behavior_signals_from_dialogue(dialogue_result):
    from src.utils.utils import extract_behavior_llm
    behavior_signals = []
    recommendations = []

    for d in dialogue_result:
        dlg = d.get("dialogue")
        if dlg:
            try:
                result = extract_behavior_llm(dlg)
                behavior_signals.extend(result.get("behaviors", []))
                recommendations.append(result.get("recommendation", ""))
            except Exception as e:
                print(f"LLM 行为提取失败：{e}")

    return behavior_signals, recommendations

def ensure_output_dir(version):
    folder = os.path.join(output_dir, version)
    os.makedirs(folder, exist_ok=True)
    return folder


def step_file(version, filename):
    return os.path.join(output_dir, version, filename)


def main(version="test", reorder_mode="random", use_cache=True, topic="小红帽", style="科幻改写", behavior_model="gpt-4.1"):
    print(f"\n开始运行 main_pipeline")
    print(f"版本: {version}，顺序模式: {reorder_mode}，使用缓存: {use_cache}")
    print(f"题材: {topic}，风格: {style}\n")
    folder = ensure_output_dir(version)
    role_state = {}



    # === Step 1: Outline Generation ===
    behavior_hint = ""
    recommendation_hint = ""
    custom_prompt = os.getenv("CUSTOM_PROMPT", "")

    outline_path = step_file(version, "test_outline.json")

    if use_cache and os.path.exists(outline_path):
        outline = load_json(outline_path)
        print("已加载 outline：")
        for idx, ch in enumerate(outline):
            print(f"{idx+1}. {ch['chapter_id']} - {ch['title']}")
    else:
        outline = generate_outline(topic=topic, style=style, custom_instruction=custom_prompt)
        print("已生成 outline：")
        for idx, ch in enumerate(outline):
            print(f"{idx+1}. {ch['chapter_id']} - {ch['title']}")

    mode = input("是否要修改 outline？（r=重新生成新结构, a=重写全部章节, s=选择部分章节, 回车跳过）: ").strip().lower()

    if mode == "r":
        while True:
            outline = generate_outline(topic=topic, style=style, custom_instruction=custom_prompt)
            print("已重新生成全新 outline：")
            for idx, ch in enumerate(outline):
                print(f"{idx+1}. {ch['chapter_id']} - {ch['title']}")

            confirm = input("是否接受这个版本？（y=接受, n=再生成, m=手动编辑）: ").strip().lower()
            if confirm == "y":
                break
            elif confirm == "m":
                print("当前生成的大纲为：")
                for idx, ch in enumerate(outline):
                    print(f"{idx+1}. {ch['chapter_id']} - {ch['title']}")

                idxs = input("请输入要修改的章节编号（可多个，用逗号分隔，回车跳过）: ").strip()
                if idxs:
                    idxs = [int(i.strip()) - 1 for i in idxs.split(",")]
                    for idx in idxs:
                        old_ch = outline[idx]
                        new_ch = interactive_loop_generate_outline_single(idx, old_ch, regenerate_outline_single)
                        outline[idx] = new_ch
                else:
                    print("未修改任何章节，保留当前版本")
                break


    elif mode == "a":
        for idx, old_ch in enumerate(outline):
            outline[idx] = interactive_loop_generate_outline_single(idx, old_ch, regenerate_outline_single)

    elif mode == "s":
        while True:
            ans = input("是否要修改某个章节？（y/n）: ").strip().lower()
            if ans != 'y':
                break
            idx = int(input("请输入要修改的章节编号（1开始）: ")) - 1
            old_ch = outline[idx]
            new_ch = interactive_loop_generate_outline_single(idx, old_ch, regenerate_outline_single)
            outline[idx] = new_ch

    # 最终保存
    save_json(outline, version, "test_outline.json")
    print("outline 保存完成")

    # === Step 2: Chapter Reordering ===
    reorder_outline = reorder_chapters(outline, mode=reorder_mode)
    save_json(reorder_outline, version, "test_reorder_outline.json")
    print(f"章节顺序处理完成（{reorder_mode}）")

    # === Step 3: Character Generation ===
    character_path = step_file(version, "characters.json")
    if use_cache and os.path.exists(character_path):
        characters = load_json(character_path)
        print("已加载角色设定")
    else:
        characters = generate_characters_v1(reorder_outline)
        save_json(characters, version, "characters.json")
        print("生成角色设定完成")

    # === Step 4: Story Expansion ===
    plot_path = step_file(version, "story.json")
    if use_cache and os.path.exists(plot_path):
        story = load_json(plot_path)
        print("已加载故事内容：")
        for idx, ch in enumerate(story):
            print(f"{idx+1}. {reorder_outline[idx]['chapter_id']} - {ch.get('plot', '')[:30]}...")

        mode = input("是否要修改 plot？（a=全部重写, s=选择部分章节, 回车跳过）: ").strip().lower()

        if mode == "a":
            for idx, ch in enumerate(reorder_outline):
                story[idx] = interactive_loop_generate_plot_single(
                    idx,
                    story[idx].get("plot", ""),
                    ch,
                    characters,
                    behavior_hint
                )

        elif mode == "s":
            idxs = input("请输入要修改的章节编号（可多个，用逗号分隔）: ").strip()
            idxs = [int(i.strip()) - 1 for i in idxs.split(",")]
            for idx in idxs:
                ch_outline = reorder_outline[idx]
                old_plot = story[idx].get("plot", "")
                story[idx] = interactive_loop_generate_plot_single(
                    idx,
                    old_plot,
                    ch_outline,
                    characters,
                    behavior_hint
                )

        save_json(story, version, "story.json")
        print("plot 修改已保存")
    else:
        combined_instruction = behavior_hint + "\n" + recommendation_hint
        story = expand_story_v1(reorder_outline, characters, custom_instruction=combined_instruction)
        
                # ✅ 添加 chapter_id 字段，确保后续模块不会崩溃
        for idx, ch in enumerate(story):
            if "chapter_id" not in ch:
                ch["chapter_id"] = reorder_outline[idx]["chapter_id"]
            if "title" not in ch:
                ch["title"] = reorder_outline[idx]["title"]

        save_json(story, version, "story.json")
        print("故事内容生成完成")

    # === Step 5: Dialogue Structure Marks ===
    plot_list = extract_plot_list(story)
    structure_marks = analyze_dialogue_insertions(plot_list, characters)
    save_json(structure_marks, version, "structure_marks.json")
    print("对话插入结构分析完成")

    # === Step 6: Dialogue Generation ===
    use_manual = input("是否手动控制对话生成？（y/n）: ").strip().lower()
    if use_manual == 'y':
        dialogue_result = interactive_run_dialogue_insertion(plot_list, characters)
    else:
        dialogue_result = run_dialogue_insertion(plot_list, characters)

    save_json(dialogue_result, version, "dialogue_marks.json")

    # === Step 6.5: LLM行为提取（支持自动或手动对话结构）
    # === Step 6.5: LLM行为提取（支持自动或手动对话结构）
    from src.utils.utils import extract_behavior_llm
    from src.utils.utils import convert_dialogue_dict_to_list
    behavior_signals = []
    recommendations = []

    for idx, d in enumerate(dialogue_result):
        dlg = d.get("dialogue")

        if not dlg:
            print(f"⚠️ 第 {idx+1} 章对白为空，已跳过行为提取")
            continue
        
        # ✅ 自动修复：如果是 dict，就转换为 list[dict]
        if isinstance(dlg, dict):
            dlg = convert_dialogue_dict_to_list(dlg)
            d["dialogue"] = dlg  # 修复原始对象，后续也能用

        if not dlg or not isinstance(dlg, list):
            print(f"⚠️ 第 {idx+1} 章对白格式错误，已跳过行为提取（应为 list[dict]）")
            continue


        try:
            result = extract_behavior_llm(dlg, model=behavior_model, confirm=True)

            # ✅ 更新角色状态记录 role_state
            for role, states in result.items():
                if role not in role_state:
                    role_state[role] = []
                for s in states:
                    if s not in role_state[role]:
                        role_state[role].append(s)

            # ✅ 构造行为提示
            for role, states in result.items():
                for s in states:
                    behavior_signals.append(f"{role}：{s}")

        except Exception as e:
            print(f"⚠️ 第 {idx+1} 章行为提取失败：{e}")

    # === 拼接行为提示与建议提示 ===
    if behavior_signals:
        behavior_hint = "上一章出现如下角色行为变化：\n" + "\n".join(behavior_signals)
    else:
        behavior_hint = ""

    if recommendations:
        recommendation_hint = "叙事建议：\n" + "\n".join([r for r in recommendations if r])
    else:
        recommendation_hint = ""

    # === 保存行为日志 ===
    behavior_log = {
        "behaviors": behavior_signals,
        "recommendations": recommendations
    }
    save_json(behavior_log, version, "behavior_trace.json")
    print("对话内容生成完成")

    # === Step 6.6: 是否根据行为重写 plot ===
    if behavior_signals:
        print("\n系统检测到以下角色行为变化：")
        for b in behavior_signals:
            print(" -", b)

        print("\n当前 story.json 已生成，但尚未体现上述行为变化。")
        replot = input("是否根据这些行为重新生成某些章节的 plot？（y/n）: ").strip().lower()

        if replot == 'y':
            idxs = input("请输入要重新生成的章节编号（可多个，用逗号分隔）: ").strip()
            idxs = [int(i.strip()) - 1 for i in idxs.split(",") if i.strip().isdigit()]
            
            for idx in idxs:
                ch_outline = reorder_outline[idx]
                old_plot = story[idx].get("plot", "")
                story[idx] = interactive_loop_generate_plot_single(
                    idx,
                    old_plot,
                    ch_outline,
                    characters,
                    behavior_hint  #关键：将行为提示注入
                )
            
            # 覆盖保存
            save_json(story, version, "story.json")
            print("plot 已根据行为提示更新完成！")
    for i, ch in enumerate(story):
        if "plot" not in ch:
            print(f" 警告：第 {i+1} 章缺少 plot，请先运行 Story Expansion 或手动添加！")
            exit(1)

    # === Step 6.7: 联动机制 - 根据对话更新 plot → 再更新对话 ===
    from src.sync.update_plot_from_dialogue import update_plot_from_dialogue
    from src.sync.regenerate_dialogue_from_plot import regenerate_dialogue_from_plot
    from src.sync.plot_sync_manager import sync_plot_and_dialogue_from_behavior

    story, dialogue_result, revision_log = sync_plot_and_dialogue_from_behavior(
        story, dialogue_result, characters, model=behavior_model
    )

    # === Step 6.8: plot 改动传播机制（调用 auto_propagate_plot_update）===
    from src.sync.auto_propagate_plot_update import auto_propagate_plot_update

    propagate = input("是否将当前 plot 改动自动传播到后续章节？（y/n）: ").strip().lower()
    if propagate == 'y':
        try:
            changed_idx = int(input("请输入你修改的章节编号（从1开始）: ")) - 1
        except:
            changed_idx = -1

        if 0 <= changed_idx < len(story):
            story, dialogue_result, propagation_log = auto_propagate_plot_update(
                story,
                dialogue_result,
                characters,
                changed_idx,
                model=behavior_model,
                behavior_hint=behavior_hint
            )
            save_json(propagation_log, version, "propagation_log.json")
            print("后续章节已传播更新，并保存为 propagation_log.json")
        else:
            print("无效章节编号，跳过传播")


    # === Step 7: 保存更新后的所有输出（新增 _updated 文件 + 修改日志） ===

    # 1. 保存角色状态
    save_json(role_state, version, "role_state.json")

    # 2. 保存更新后的 JSON 版本
    save_json(story, version, "story_updated.json")
    save_json(dialogue_result, version, "dialogue_updated.json")
    save_json(revision_log, version, "revision_log.json")

    # 4. 合成 story + dialogue 为 markdown
    from src.compile_story import compile_full_story_by_chapter
    compiled_updated = compile_full_story_by_chapter(story, dialogue_result)
    save_md(compiled_updated, os.path.join(folder, "novel_story_updated.md"))
    print("novel_story_updated.md 已生成（包含最新改写）")

    # 5. 结构增强 + 对话润色版本（基于更新后内容）
    enhance_story_with_transitions(task_name=version, input_story_file="story_updated.json")
    polish_dialogues_in_story(task_name=version, input_dialogue_file="dialogue_updated.json")
    print("enhanced_story_updated.md 与 enhanced_story_dialogue_updated.md 已完成")

    # === Step 8: 提取角色状态时间线（用于一致性分析） ===
    from src.analysis.character_state_tracker import run_character_state_tracker
    run_character_state_tracker(
        version=version,
        dialogue_file="dialogue_updated.json",
        model=behavior_model
    )

    # # === Step 7: 保存三个版本 .md 文件 ===
    
    # save_json(role_state, version, "role_state.json")

    # # 1. 原始剧情版本（未插入结构或对话）
    # compiled_story = compile_full_story_by_chapter(story, dialogue_result)
    # save_md(compiled_story, os.path.join(folder, "novel_story.md"))
    # print("novel_story.md 已通过 compile_story.py 生成")

    # # 2. 结构增强版本（根据结构点增强，可选带章节标题）
    # enhance_story_with_transitions(task_name=version)
    # polish_dialogues_in_story(task_name=version)
    # print("enhanced_story.md 和 enhanced_story_dialogue.md 已生成完成")


    print(f"\n全部流程执行完毕！结果保存在：{folder}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="test", help="版本名称（对应输出子目录）")
    parser.add_argument("--reorder", type=str, default="random", choices=["sequential", "reverse", "random"], help="章节顺序控制模式")
    parser.add_argument("--no-cache", action="store_true", help="是否忽略已有结果，强制全部重新生成")
    parser.add_argument("--topic", type=str, default="小红帽", help="故事题材")
    parser.add_argument("--style", type=str, default="科幻改写", help="故事风格")
    parser.add_argument("--behavior-model", type=str, default="gpt-4.1", help="行为识别使用的模型")

    args = parser.parse_args()
    main(
        version=args.version,
        reorder_mode=args.reorder,
        use_cache=not args.no_cache,
        topic=args.topic,
        style=args.style,
        behavior_model=args.behavior_model
    )      

# # 使用默认缓存数据运行
# python main_pipeline.py

# # 强制全部重新生成
# python main_pipeline.py --no-cache

# # 以顺序顺序生成章节结构
# python main_pipeline.py --reorder sequential

# # 输出到另一个版本目录
# python main_pipeline.py --version demo --reorder reverse
