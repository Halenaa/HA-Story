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
    topic="Little Red Riding Hood",
    style="Sci-fi rewrite",
    behavior_model="gpt-4.1",
    temperature=0.7,
    seed=1,
    generation_mode="traditional",
    user_description=None,
    file_content=None
):
    #  Automatically build version name
    if version == "test":
        if generation_mode == "traditional":
            version = build_version_name(
                topic=topic,
                style=style,
                temperature=temperature,
                seed=seed,
                order_mode=reorder_mode
            )
        else:  # description_based mode
            import hashlib
            import datetime
            # Generate short identifier based on user description
            desc_hash = hashlib.md5(user_description.encode('utf-8')).hexdigest()[:8] if user_description else "nodesc"
            timestamp = datetime.datetime.now().strftime("%m%d_%H%M")
            version = f"custom_{desc_hash}_{reorder_mode}_T{temperature}_s{seed}_{timestamp}"

    print(f"\nStarting main_pipeline")
    print(f"Version: {version}, Order mode: {reorder_mode}, Use cache: {use_cache}")
    if generation_mode == "traditional":
        print(f"Generation mode: Traditional mode, Topic: {topic}, Style: {style}")
    else:
        print(f"Generation mode: Custom description mode")
        print(f"User description: {user_description[:100]}..." if user_description and len(user_description) > 100 else f"User description: {user_description}")
        print(f"File content: {'Provided' if file_content else 'None'}")
    print()
    folder = ensure_output_dir(version)
    role_state = {}

    # Initialize performance analyzer
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
    print("Performance analyzer started")

    plot_log_path = init_log_path(folder, "plot")
    dialogue_log_path = init_log_path(folder, "dialogue")

    # Step 1: Outline Generation
    performance_analyzer.start_stage("outline_generation", {"topic": topic, "style": style, "generation_mode": generation_mode})
    
    if generation_mode == "traditional":
        # Traditional mode: use shared outline cache
        outline_base_path = os.path.join(output_dir, "reference_outline", f"{topic}_{style}_T{temperature}_s{seed}_outline.json")
        os.makedirs(os.path.dirname(outline_base_path), exist_ok=True)

        if os.path.exists(outline_base_path) and use_cache:
            outline = load_json(outline_base_path)
            performance_analyzer.record_cache_usage("outline_generation", True, outline_base_path)
            print(f"Loaded shared outline: {outline_base_path}")
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
            print(f"Generated and saved shared outline: {outline_base_path}")
    else:
        # Description mode: regenerate each time (no shared cache)
        outline_path = step_file(version, "test_outline.json")
        if os.path.exists(outline_path) and use_cache:
            outline = load_json(outline_path)
            performance_analyzer.record_cache_usage("outline_generation", True, outline_path)
            print(f"Loaded custom outline: {outline_path}")
        else:
            performance_analyzer.record_cache_usage("outline_generation", False, outline_path)
            outline = generate_outline(
                topic=topic,  # May be empty, but generate_outline will handle it
                style=style,  # May be empty, but generate_outline will handle it
                custom_instruction="",
                generation_mode="description_based",
                user_description=user_description,
                file_content=file_content,
                performance_analyzer=performance_analyzer
            )
            save_json(outline, version, "test_outline.json")
            print(f"Custom outline generation completed")
    
    performance_analyzer.end_stage("outline_generation", outline)


    # Step 2: Chapter order processing
    performance_analyzer.start_stage("chapter_reorder", {"reorder_mode": reorder_mode, "chapters": len(outline)})
    
    if reorder_mode == "linear":
        reorder_outline_raw = outline
        save_json(outline, version, "test_outline.json")
        print("Using linear order (directly from outline)")


    elif reorder_mode == "nonlinear":
        save_json(outline, version, "test_outline_linear.json")
        reorder_path = os.path.join(output_dir, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
        os.makedirs(os.path.dirname(reorder_path), exist_ok=True)

        if os.path.exists(reorder_path):
            reorder_outline_raw = load_json(reorder_path)
            print(f"Loaded cached nonlinear order: {reorder_path}")
        else:
            # Step 2.1: Chapter reordering
            reorder_outline_raw = reorder_chapters(outline, mode="nonlinear", performance_analyzer=performance_analyzer)
            
            # Check if reordering was successful
            if not any("new_order" in ch for ch in reorder_outline_raw):
                print("LLM reorder failed: No new_order fields detected, falling back to original order")
                reorder_mode = "linear"  # Fallback to linear mode
                reorder_outline_raw = outline
            else:
                print("reorder_chapters successfully generated nonlinear order")
                
                # Step 2.2: Narrative structure analysis
                print("Starting narrative structure analysis...")
                reorder_outline_raw = analyze_narrative_structure(
                    reorder_outline_raw, outline, topic=topic, style=style, performance_analyzer=performance_analyzer
                )
                
                # Display analysis results
                print("📖 Narrative structure analysis results:")
                for ch in reorder_outline_raw:
                    role = ch.get('narrative_role', 'Not analyzed')
                    print(f"  {ch['chapter_id']}: {role}")

            save_json(reorder_outline_raw, "reference_reorder", f"{topic}_{style}_T{temperature}_s{seed}_nonlinear.json")
            print(f"Generated nonlinear order and cached: {reorder_path}")

        # Add log records
        reorder_log_path = init_log_path(folder, "reorder")
        reorder_log = build_simple_log(
            module="chapter_reorder_with_narrative",
            task_name=version,
            input_data={"outline": outline, "reorder_mode": reorder_mode},
            output_data={"reorder_result": reorder_outline_raw, "narrative_mode": reorder_mode}
        )
        append_log(reorder_log_path, reorder_log)

    # Unified structure: complete summary fields, preserve narrative analysis fields
    reorder_outline = []
    for reordered_ch in reorder_outline_raw:
        match = next((x for x in outline if x["chapter_id"] == reordered_ch["chapter_id"]), None)
        if match:
            merged = {
                "chapter_id": reordered_ch["chapter_id"],
                "title": reordered_ch["title"],
                "summary": match.get("summary", "")
            }
            
            # Preserve reordering and narrative analysis related fields
            narrative_fields = ["new_order", "narrative_role", "narrative_instruction", "transition_hint"]
            for field in narrative_fields:
                if field in reordered_ch:
                    merged[field] = reordered_ch[field]
            
            reorder_outline.append(merged)

    save_json(reorder_outline, version, "test_reorder_outline.json")

    # Display final structure
    if reorder_mode == "nonlinear":
        print("Chapter order processing completed (summary and narrative guidance preserved)")
        print("Final chapter structure:")
        for idx, ch in enumerate(reorder_outline):
            role = ch.get('narrative_role', 'Linear narrative')
            orig_pos = next((i+1 for i, x in enumerate(outline) if x["chapter_id"] == ch["chapter_id"]), "?")
            print(f"  {idx+1}. {ch['chapter_id']} (originally chapter {orig_pos}) - {role}")
    else:
        print("Chapter order processing completed (summary preserved)")
    
    performance_analyzer.end_stage("chapter_reorder", reorder_outline)

    # Step 3: Character Generation
    performance_analyzer.start_stage("character_generation", {"chapters": len(reorder_outline)})
    
    character_path = step_file(version, "characters.json")
    if use_cache and os.path.exists(character_path):
        characters = load_json(character_path)
        performance_analyzer.record_cache_usage("character_generation", True, character_path)
        print("Character settings loaded")
    else:
        performance_analyzer.record_cache_usage("character_generation", False, character_path)
        characters = generate_characters_v1(reorder_outline, performance_analyzer=performance_analyzer)
        save_json(characters, version, "characters.json")
        print("Character generation completed")
    
    performance_analyzer.end_stage("character_generation", characters)

    # Step 4: Story Expansion
    performance_analyzer.start_stage("story_expansion", {"chapters": len(reorder_outline), "characters": len(characters)})
    
    plot_path = step_file(version, "story.json")
    if use_cache and os.path.exists(plot_path):
        story = load_json(plot_path)
        performance_analyzer.record_cache_usage("story_expansion", True, plot_path)
        print("Story content loaded")
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
        print("Story content generation completed")
    
    performance_analyzer.end_stage("story_expansion", story)

    # Step 5 & 6: New dialogue generation (sentence-level analysis + chapter-level compatibility)
    performance_analyzer.start_stage("dialogue_generation", {"story_chapters": len(story), "characters": len(characters)})
    
    chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(story, characters, performance_analyzer=performance_analyzer)

    # Save data in three formats
    save_json(chapter_results, version, "dialogue_marks.json")        # Compatible format
    save_json(sentence_results, version, "sentence_dialogues.json")    # Sentence-level detailed analysis
    save_json(behavior_timeline, version, "behavior_timeline_raw.json")  # Raw behavior data

    # If sync is needed, use chapter-level
    if len(story) == len(chapter_results):
        story, chapter_results_updated, revision_log = sync_plot_and_dialogue_from_behavior(
            story, chapter_results, characters, model=behavior_model)
    else:
        chapter_results_updated = chapter_results  # 🔴 Added this line
        revision_log = []

    # Record logs (use chapter-level to maintain compatibility)
    for ch, dlg in zip(story, chapter_results_updated):  # 🔴 Use chapter_results_updated
        log = build_log_record(
            module="dialogue_inserter", step="dialogue",
            task_name=version, chapter_id=ch["chapter_id"],
            model=behavior_model,
            input_data={"plot": ch["plot"]},
            output_data={"dialogue": dlg["dialogue"]},
            temperature=temperature, seed=seed
        )
        append_log(dialogue_log_path, log)
 

    # Step 6.5: New behavior saving (extracted in v2)
    # Organize character arcs
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

    # Generate complete behavior_trace
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

    # Compatible role_state
    role_state = {}
    for item in behavior_timeline:
        role = item["character"]
        behavior = item["behavior"]
        role_state.setdefault(role, [])
        if behavior not in role_state[role]:
            role_state[role].append(behavior)

    print("New behavior trace generation completed")
    
    performance_analyzer.end_stage("dialogue_generation", {
        "chapter_results": len(chapter_results_updated),
        "sentence_results": len(sentence_results),
        "behavior_timeline": len(behavior_timeline)
    })


    # Step 7: Save output
    # save_json(role_state, version, "role_state.json")
    save_json(story, version, "story_updated.json")
    save_json(sentence_results, version, "dialogue_updated.json") 
    save_json(revision_log, version, "revision_log.json")

    compiled_updated = compile_full_story_by_sentence(story, sentence_results)
    save_md(compiled_updated, os.path.join(folder, "novel_story.md")) 
    print("novel_story.md generated")

    # Step 8: Enhancement
    performance_analyzer.start_stage("story_enhancement", {"compiled_story_length": len(compiled_updated)})
    
    enhance_story_with_transitions(task_name=version, input_story_file="story_updated.json")
    polish_dialogues_in_story(task_name=version, input_dialogue_file="dialogue_updated.json")
    print("Enhanced version completed")
    
    performance_analyzer.end_stage("story_enhancement", {"enhanced": True})

    def generate_role_state_from_behavior_trace(behavior_trace_data):
        """Generate role_state directly from behavior_trace, avoiding duplicate LLM calls and incorrect mapping"""
        from collections import defaultdict
        
        timeline = behavior_trace_data.get("timeline", [])
        role_state_by_chapter = defaultdict(lambda: defaultdict(set))
        
        for item in timeline:
            chapter_id = item["chapter_id"]
            character = item["character"]
            behavior = item["behavior"]
            role_state_by_chapter[chapter_id][character].add(behavior)
        
        # Convert to final format
        result = {}
        for chapter_id in sorted(role_state_by_chapter.keys()):
            result[chapter_id] = {}
            for character, behaviors in role_state_by_chapter[chapter_id].items():
                result[chapter_id][character] = sorted(list(behaviors))
        
        return result

    # Generate role_state from existing correct data
    correct_role_state = generate_role_state_from_behavior_trace(behavior_trace)
    save_json(correct_role_state, version, "role_state.json")
    print(f"Generated correct role_state.json from behavior_trace ({len(correct_role_state)} chapters)")
    # run_character_state_tracker(version=version, dialogue_file="dialogue_updated.json", model=behavior_model)
    
    # Generate performance analysis report
    print("\nGenerating performance analysis report...")
    performance_analyzer.analyze_text_features(story, sentence_results, characters)
    
    # Calculate memory vs character count relationship
    memory_per_character = performance_analyzer.calculate_memory_per_character(characters)
    if memory_per_character:
        print(f"Memory efficiency: {memory_per_character.get('peak_memory_per_character', 0):.2f} MB/character")
    
    performance_report_path = performance_analyzer.save_report(folder, f"performance_analysis_{version}.json")
    
    # Display performance summary
    complexity_metrics = performance_analyzer.calculate_complexity_metrics()
    total_time = performance_analyzer.get_total_time()
    
    print(f"\nPerformance Summary:")
    print(f"   Total execution time: {performance_analyzer._format_duration(total_time)}")
    print(f"   Generated text: {performance_analyzer.text_features.get('total_word_count', 0)} words")
    print(f"   Generation efficiency: {complexity_metrics.get('efficiency_metrics', {}).get('words_per_second', 0):.2f} words/sec")
    print(f"   Peak memory usage: {performance_analyzer.peak_memory_usage:.2f} MB")
    print(f"   Total API cost: ${performance_analyzer.total_api_cost:.4f}")
    print(f"   Total token consumption: {performance_analyzer.total_tokens:,}")
    print(f"   Time complexity estimate: {performance_analyzer._estimate_complexity_class()}")
    
    # Display time consumption by stage
    print(f"\nTime consumption by stage:")
    stage_percentages = performance_analyzer._calculate_stage_percentages()
    for stage, duration in performance_analyzer.stage_times.items():
        percentage = stage_percentages.get(stage, 0)
        # Display memory growth for this stage
        memory_increase = performance_analyzer.stage_memory_usage.get(f"{stage}_increase", 0)
        memory_info = f", Memory+{memory_increase:.2f}MB" if memory_increase > 0 else ""
        print(f"   {stage}: {performance_analyzer._format_duration(duration)} ({percentage:.1f}%){memory_info}")
    
    # Display API cost breakdown
    if performance_analyzer.token_consumption:
        print(f"\nAPI cost breakdown:")
        for stage, tokens in performance_analyzer.token_consumption.items():
            print(f"   {stage}: ${tokens['total_cost']:.4f} ({tokens['total_tokens']:,} tokens, {tokens['api_calls']} calls)")
    
    print(f"\nAll processes completed! Results saved in: {folder}")
    print(f"Performance analysis report: {performance_report_path}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", type=str, default="test", help="Version name")
    parser.add_argument("--reorder", type=str, default="linear", choices=["linear", "nonlinear"], help="Chapter order control")
    parser.add_argument("--no-cache", action="store_true", help="Whether to ignore existing results")
    parser.add_argument("--topic", type=str, default="Little Red Riding Hood", help="Story topic")
    parser.add_argument("--style", type=str, default="Sci-fi rewrite", help="Story style")
    parser.add_argument("--behavior-model", type=str, default="gpt-4.1", help="Behavior recognition model")
    parser.add_argument("--temperature", type=float, default=0.7, help="LLM temperature")
    parser.add_argument("--seed", type=int, default=42, help="Generation random seed")
    
    # New parameters: support description mode
    parser.add_argument("--generation-mode", type=str, default="traditional", 
                       choices=["traditional", "description_based"], help="Generation mode: traditional or description_based")
    parser.add_argument("--user-description", type=str, default=None, help="User story description (used in description_based mode)")
    parser.add_argument("--file-content", type=str, default=None, help="Reference file content (optional)")

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

