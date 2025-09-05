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
from src.generation.narrative_analyzer import analyze_narrative_structure, enhance_summaries_with_narrative
from src.analysis.performance_analyzer import PerformanceAnalyzer


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
    seed=1,
    generation_mode="traditional",
    user_description=None,
    file_content=None
):
    #  自动构建版本名称
    if version == "test":
        if generation_mode == "traditional":
            version = build_version_name(
                topic=topic,
                style=style,
                temperature=temperature,
                seed=seed,
                order_mode=reorder_mode
            )
        else:  # description_based 模式
            import hashlib
            import datetime
            # 基于用户描述生成简短标识
            desc_hash = hashlib.md5(user_description.encode('utf-8')).hexdigest()[:8] if user_description else "nodesc"
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            version = f"custom_{desc_hash}_{reorder_mode}_T{temperature}_s{seed}_{timestamp}"

    print(f"\n开始运行 main_pipeline")
    print(f"版本: {version}，顺序模式: {reorder_mode}，使用缓存: {use_cache}")
    if generation_mode == "traditional":
        print(f"生成模式: 传统模式，题材: {topic}，风格: {style}")
    else:
        print(f"生成模式: 自定义描述模式")
        print(f"用户描述: {user_description[:100]}..." if user_description and len(user_description) > 100 else f"用户描述: {user_description}")
        print(f"文件内容: {'已提供' if file_content else '无'}")
    print()
    folder = ensure_output_dir(version)
    role_state = {}

    # 初始化性能分析器
    experiment_config = {
        'topic': topic,
        'style': style,
        'temperature': temperature,
        'seed': seed,
        'behavior_model': behavior_model,
        'generation_mode': generation_mode,
        'reorder_mode': reorder_mode,
        'use_cache': use_cache,
        'user_description': user_description,
        'file_content': file_content is not None
    }
    
    performance_analyzer = PerformanceAnalyzer(
        task_name=version, 
        experiment_config=experiment_config
    )
    performance_analyzer.start_total_timing()
    print("性能分析器已启动")

    plot_log_path = init_log_path(folder, "plot")
    dialogue_log_path = init_log_path(folder, "dialogue")

    # Step 1: Outline Generation
    performance_analyzer.start_stage("outline_generation", {"topic": topic, "style": style, "generation_mode": generation_mode})
    
    if generation_mode == "traditional":
        # 传统模式：使用共享的 outline 缓存
        outline_base_path = os.path.join(output_dir, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
        os.makedirs(os.path.dirname(outline_base_path), exist_ok=True)

        if os.path.exists(outline_base_path) and use_cache:
            outline = load_json(outline_base_path)
            performance_analyzer.record_cache_usage("outline_generation", True, outline_base_path)
            print(f"已加载共享 outline：{outline_base_path}")
        else:
            performance_analyzer.record_cache_usage("outline_generation", False, outline_base_path)
            outline = generate_outline(
                topic=topic, 
                style=style, 
                custom_instruction="",
                generation_mode="traditional",
                performance_analyzer=performance_analyzer
            )
            save_json(outline, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
            print(f"生成并保存共享 outline：{outline_base_path}")
    else:
        # 描述模式：每次都重新生成（不使用共享缓存）
        outline_path = step_file(version, "test_outline.json")
        if os.path.exists(outline_path) and use_cache:
            outline = load_json(outline_path)
            performance_analyzer.record_cache_usage("outline_generation", True, outline_path)
            print(f"已加载自定义 outline：{outline_path}")
        else:
            performance_analyzer.record_cache_usage("outline_generation", False, outline_path)
            outline = generate_outline(
                topic=topic,  # 这里可能为空，但generate_outline会处理
                style=style,  # 这里可能为空，但generate_outline会处理
                custom_instruction="",
                generation_mode="description_based",
                user_description=user_description,
                file_content=file_content,
                performance_analyzer=performance_analyzer
            )
            save_json(outline, version, "test_outline.json")
            print(f"生成自定义 outline 完成")
    
    performance_analyzer.end_stage("outline_generation", outline)


    # Step 2: 章节顺序处理
    performance_analyzer.start_stage("chapter_reorder", {"reorder_mode": reorder_mode, "chapters": len(outline)})
    
    if reorder_mode == "linear":
        reorder_outline_raw = outline
        save_json(outline, version, "test_outline.json")
        print("使用 linear 顺序（直接来自 outline）")


    elif reorder_mode == "nonlinear":
        save_json(outline, version, "test_outline_linear.json")
        reorder_path = os.path.join(output_dir, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
        os.makedirs(os.path.dirname(reorder_path), exist_ok=True)

        if os.path.exists(reorder_path):
            reorder_outline_raw = load_json(reorder_path)
            print(f"已加载 cached nonlinear 顺序：{reorder_path}")
        else:
            # Step 2.1: 章节重排
            reorder_outline_raw = reorder_chapters(outline, mode="nonlinear", performance_analyzer=performance_analyzer)
            
            # 检查重排是否成功
            if not any("new_order" in ch for ch in reorder_outline_raw):
                print("LLM 重排失败：未检测到任何 new_order 字段，回退为原始顺序")
                reorder_mode = "linear"  # 回退到线性模式
                reorder_outline_raw = outline
            else:
                print("reorder_chapters 成功生成非线性顺序")
                
                # Step 2.2: 叙述结构分析
                print("开始叙述结构分析...")
                reorder_outline_raw = analyze_narrative_structure(
                    reorder_outline_raw, outline, topic=topic, style=style, performance_analyzer=performance_analyzer
                )
                
                # 显示分析结果
                print("📖 叙述结构分析结果：")
                for ch in reorder_outline_raw:
                    role = ch.get('narrative_role', '未分析')
                    print(f"  {ch['chapter_id']}: {role}")

            save_json(reorder_outline_raw, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
            print(f"生成 nonlinear 顺序并缓存：{reorder_path}")

        # 添加日志记录
        reorder_log_path = init_log_path(folder, "reorder")
        reorder_log = build_simple_log(
            module="chapter_reorder_with_narrative",
            task_name=version,
            input_data={"outline": outline, "reorder_mode": reorder_mode},
            output_data={"reorder_result": reorder_outline_raw, "narrative_mode": reorder_mode}
        )
        append_log(reorder_log_path, reorder_log)

    # 统一结构：补全 summary 字段，保留叙述分析字段
    reorder_outline = []
    for reordered_ch in reorder_outline_raw:
        match = next((x for x in outline if x["chapter_id"] == reordered_ch["chapter_id"]), None)
        if match:
            merged = {
                "chapter_id": reordered_ch["chapter_id"],
                "title": reordered_ch["title"],
                "summary": match.get("summary", "")
            }
            
            # 保留重排和叙述分析相关字段
            narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint"]
            for field in narrative_fields:
                if field in reordered_ch:
                    merged[field] = reordered_ch[field]
            
            reorder_outline.append(merged)

    save_json(reorder_outline, version, "test_reorder_outline.json")

    # 显示最终结构
    if reorder_mode == "nonlinear":
        print("章节顺序处理完成（已保留 summary 和叙述指导）")
        print("🎭 最终章节结构：")
        for idx, ch in enumerate(reorder_outline):
            role = ch.get('narrative_role', '线性叙述')
            orig_pos = next((i+1 for i, x in enumerate(outline) if x["chapter_id"] == ch["chapter_id"]), "?")
            print(f"  {idx+1}. {ch['chapter_id']} (原第{orig_pos}章) - {role}")
    else:
        print("章节顺序处理完成（已保留 summary）")
    
    performance_analyzer.end_stage("chapter_reorder", reorder_outline)

    # Step 3: Character Generation
    performance_analyzer.start_stage("character_generation", {"chapters": len(reorder_outline)})
    
    character_path = step_file(version, "characters.json")
    if use_cache and os.path.exists(character_path):
        characters = load_json(character_path)
        performance_analyzer.record_cache_usage("character_generation", True, character_path)
        print("已加载角色设定")
    else:
        performance_analyzer.record_cache_usage("character_generation", False, character_path)
        characters = generate_characters_v1(reorder_outline, performance_analyzer=performance_analyzer)
        save_json(characters, version, "characters.json")
        print("生成角色设定完成")
    
    performance_analyzer.end_stage("character_generation", characters)

    # Step 4: Story Expansion
    performance_analyzer.start_stage("story_expansion", {"chapters": len(reorder_outline), "characters": len(characters)})
    
    plot_path = step_file(version, "story.json")
    if use_cache and os.path.exists(plot_path):
        story = load_json(plot_path)
        performance_analyzer.record_cache_usage("story_expansion", True, plot_path)
        print("已加载故事内容")
    else:
        performance_analyzer.record_cache_usage("story_expansion", False, plot_path)
        story = expand_story_v1(reorder_outline, characters, custom_instruction="", performance_analyzer=performance_analyzer)
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
    
    performance_analyzer.end_stage("story_expansion", story)

    # Step 5 & 6: 新版对话生成（句子级分析 + 章节级兼容）
    performance_analyzer.start_stage("dialogue_generation", {"story_chapters": len(story), "characters": len(characters)})
    
    chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(story, characters, performance_analyzer=performance_analyzer)

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
    
    performance_analyzer.end_stage("dialogue_generation", {
        "chapter_results": len(chapter_results_updated),
        "sentence_results": len(sentence_results),
        "behavior_timeline": len(behavior_timeline)
    })


    # Step 7: 保存输出
    # save_json(role_state, version, "role_state.json")
    save_json(story, version, "story_updated.json")
    save_json(sentence_results, version, "dialogue_updated.json") 
    save_json(revision_log, version, "revision_log.json")

    compiled_updated = compile_full_story_by_sentence(story, sentence_results)
    save_md(compiled_updated, os.path.join(folder, "novel_story.md")) 
    print("novel_story.md 已生成")

    # Step 8: Enhancement
    performance_analyzer.start_stage("story_enhancement", {"compiled_story_length": len(compiled_updated)})
    
    enhance_story_with_transitions(task_name=version, input_story_file="story_updated.json")
    polish_dialogues_in_story(task_name=version, input_dialogue_file="dialogue_updated.json")
    print("增强版本已完成")
    
    performance_analyzer.end_stage("story_enhancement", {"enhanced": True})

    def generate_role_state_from_behavior_trace(behavior_trace_data):
        """从behavior_trace直接生成role_state，避免重复LLM调用和错误映射"""
        from collections import defaultdict
        
        timeline = behavior_trace_data.get("timeline", [])
        role_state_by_chapter = defaultdict(lambda: defaultdict(set))
        
        for item in timeline:
            chapter_id = item["chapter_id"]
            character = item["character"]
            behavior = item["behavior"]
            role_state_by_chapter[chapter_id][character].add(behavior)
        
        # 转换为最终格式
        result = {}
        for chapter_id in sorted(role_state_by_chapter.keys()):
            result[chapter_id] = {}
            for character, behaviors in role_state_by_chapter[chapter_id].items():
                result[chapter_id][character] = sorted(list(behaviors))
        
        return result

    # 从已有的正确数据生成 role_state
    correct_role_state = generate_role_state_from_behavior_trace(behavior_trace)
    save_json(correct_role_state, version, "role_state.json")
    print(f"从 behavior_trace 生成正确的 role_state.json ({len(correct_role_state)} 个章节)")
    # run_character_state_tracker(version=version, dialogue_file="dialogue_updated.json", model=behavior_model)
    
    # 生成性能分析报告
    print("\n正在生成性能分析报告...")
    performance_analyzer.analyze_text_features(story, sentence_results, characters)
    
    # 计算内存vs角色数量的关系
    memory_per_character = performance_analyzer.calculate_memory_per_character(characters)
    if memory_per_character:
        print(f"内存效率: {memory_per_character.get('peak_memory_per_character', 0):.2f} MB/角色")
    
    performance_report_path = performance_analyzer.save_report(folder, f"performance_analysis_{version}.json")
    
    # 显示性能摘要
    complexity_metrics = performance_analyzer.calculate_complexity_metrics()
    total_time = performance_analyzer.get_total_time()
    
    print(f"\n性能摘要:")
    print(f"   总执行时间: {performance_analyzer._format_duration(total_time)}")
    print(f"   生成文本: {performance_analyzer.text_features.get('total_word_count', 0)} 字")
    print(f"   生成效率: {complexity_metrics.get('efficiency_metrics', {}).get('words_per_second', 0):.2f} 字/秒")
    print(f"   峰值内存使用: {performance_analyzer.peak_memory_usage:.2f} MB")
    print(f"   总API成本: ${performance_analyzer.total_api_cost:.4f}")
    print(f"   总Token消耗: {performance_analyzer.total_tokens:,}")
    print(f"   时间复杂度估算: {performance_analyzer._estimate_complexity_class()}")
    
    # 显示各阶段耗时
    print(f"\n各阶段耗时:")
    stage_percentages = performance_analyzer._calculate_stage_percentages()
    for stage, duration in performance_analyzer.stage_times.items():
        percentage = stage_percentages.get(stage, 0)
        # 显示该阶段的内存增长
        memory_increase = performance_analyzer.stage_memory_usage.get(f"{stage}_increase", 0)
        memory_info = f", 内存+{memory_increase:.2f}MB" if memory_increase > 0 else ""
        print(f"   {stage}: {performance_analyzer._format_duration(duration)} ({percentage:.1f}%){memory_info}")
    
    # 显示API成本分解
    if performance_analyzer.token_consumption:
        print(f"\nAPI成本分解:")
        for stage, tokens in performance_analyzer.token_consumption.items():
            print(f"   {stage}: ${tokens['total_cost']:.4f} ({tokens['total_tokens']:,} tokens, {tokens['api_calls']} 次调用)")
    
    print(f"\n全部流程执行完毕！结果保存在：{folder}")
    print(f"性能分析报告: {performance_report_path}\n")

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
    
    # 新增参数：支持描述模式
    parser.add_argument("--generation-mode", type=str, default="traditional", 
                       choices=["traditional", "description_based"], help="生成模式：traditional或description_based")
    parser.add_argument("--user-description", type=str, default=None, help="用户故事描述（description_based模式使用）")
    parser.add_argument("--file-content", type=str, default=None, help="参考文件内容（可选）")

    args = parser.parse_args()

    main(
        version=args.version,
        reorder_mode=args.reorder,
        use_cache=not args.no_cache,
        topic=args.topic,
        style=args.style,
        behavior_model=args.behavior_model,
        temperature=args.temperature,
        seed=args.seed,
        generation_mode=args.generation_mode,
        user_description=args.user_description,
        file_content=args.file_content
    )

