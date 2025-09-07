import json
import logging
import os
from datetime import datetime
from src.utils.utils import generate_response, convert_json, split_plot_into_sentences, extract_behavior_llm

# Add logging setup function
def setup_dialogue_logger():
    """Simple logging setup, output to file and console"""
    logger = logging.getLogger('dialogue_gen')
    if logger.handlers:  # Avoid duplicate setup
        return logger
    
    logger.setLevel(logging.INFO)
    
    # File handler - output to data/output/logs/dialogue.log
    try:
        log_dir = "data/output/logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f"{log_dir}/dialogue_generation.log", encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except:
        pass  # If log file creation fails, does not affect main process
    
    return logger


def analyze_dialogue_insertions(plot_list, character_list_json):
    """
    Judge whether each sentence needs dialogue insertion, return structural suggestions
    """
    msg = [{
        "role": "system",
        "content": f"""
Your role is a screenwriter who needs to control at which plot points to add dialogue scenes and select corresponding actors for performance. You need to analyze each sentence of the plot I give you:

If dialogue needs to be inserted after a sentence, return 1 and select corresponding actors; otherwise return 0 with empty actor list.

#Output Format：
[
{{
  "sentence": "...",
  "need_to_action": 0 or 1,
  "actor_list": ["Actor A", "Actor B"]
}},
...
]

Here is the plot list: {plot_list}

This is the actor list: {character_list_json}
Only return JSON that conforms to the above format, do not add any explanations or extra text.
        """
    }]
    response = generate_response(msg)  # This function is not in main process, keep original
    print("\n analyze_dialogue_insertions raw response content:\n", response, "\n")  # Add this line

    return convert_json(response)

def analyze_dialogue_insertions_v2(story, characters, performance_analyzer=None):
    """
    Enhanced version: Ensure sentence_results contains complete dialogue data
    """
    from src.utils.utils import split_plot_into_sentences, generate_response, convert_json, extract_behavior_llm
    from src.generation.dialogue_inserter import generate_dialogue_for_insertion
    
    chapter_results = []
    behavior_timeline = []
    sentence_results = []
    
    for chapter in story:
        chapter_id = chapter.get("chapter_id", "Unknown")
        scene = chapter.get("scene", "")
        plot = chapter.get("plot", "")
        
        sentences = split_plot_into_sentences(plot)
        print(f"Chapter {chapter_id} split into {len(sentences)} sentences")
        
        # LLM analyze sentences
        msg = [{
            "role": "system", 
            "content": f"""Judge whether each plot sentence needs dialogue insertion:
Sentence list: {sentences}
Actor list: {characters}
Format: [{{"sentence":"...", "need_to_action":0 or 1, "actor_list":["Actor A"]}}]
Only return JSON."""
        }]
        response = generate_response(msg, performance_analyzer=performance_analyzer, stage_name="dialogue_generation")
        sentence_analysis = convert_json(response)
        
        chapter_dialogues = []
        all_actors = set()
        
        for sent_idx, result in enumerate(sentence_analysis):
            # Generate independent dialogue for each sentence
            sentence_dialogue = []
            
            if result.get("need_to_action") == 1:
                # Generate dialogue for this sentence
                dialogue = generate_dialogue_for_insertion(
                    result["sentence"], 
                    result["actor_list"],
                    [plot],
                    characters,
                    performance_analyzer
                )
                sentence_dialogue = dialogue
                chapter_dialogues.extend(dialogue)
                all_actors.update(result["actor_list"])
                
                # behavior extraction
                if dialogue:
                    try:
                        behavior = extract_behavior_llm(dialogue)
                        for character, behaviors in behavior.items():
                            for behavior_state in behaviors:
                                behavior_timeline.append({
                                    "chapter_id": chapter_id,
                                    "sentence_index": sent_idx,
                                    "sentence": result["sentence"][:50] + "..." if len(result["sentence"]) > 50 else result["sentence"],
                                    "character": character,
                                    "behavior": behavior_state,
                                    "scene_context": scene,
                                    "dialogue_trigger": True
                                })
                    except Exception as e:
                        print(f"Behavior extraction failed: {e}")
            
            # Key: sentence_results contains dialogue field
            sentence_result = {
                "chapter_id": chapter_id,
                "sentence_index": sent_idx,
                "sentence": result.get("sentence", ""),
                "need_to_action": result.get("need_to_action", 0),
                "actor_list": result.get("actor_list", []),
                "dialogue": sentence_dialogue,  # Independent dialogue for each sentence
                "scene_context": scene
            }
            sentence_results.append(sentence_result)
        
        # Chapter-level results (compatible with subsequent modules)
        chapter_result = {
            "sentence": plot,
            "need_to_action": 1 if chapter_dialogues else 0,
            "actor_list": list(all_actors),
            "dialogue": chapter_dialogues
        }
        chapter_results.append(chapter_result)
    
    return chapter_results, sentence_results, behavior_timeline

# Legacy commented code removed - outdated implementation

def generate_dialogue_for_insertion(sentence_context, candidate_characters, full_plot, character_personality, performance_analyzer=None):
    """
    Fully trust LLM version: Keep original format, remove all artificial restrictions
    """
    # Initialize logging
    logger = setup_dialogue_logger()
    session_id = datetime.now().strftime("%H%M%S")
    
    print(f"\nStarting dialogue generation, candidate characters: {candidate_characters}")
    # Record session start
    logger.info(f"SESSION_START | session_id={session_id} | characters={candidate_characters} | context={sentence_context[:100]}...")
    
    dialogue_list = []
    history = ""

    # Analyze dialogue goals - fix JSON format issues
    goal_prompt = [{
        "role": "system",
        "content": f"""You are a story screenwriter. Analyze what needs to be expressed through dialogue in the following plot segment:

Plot: {sentence_context}
Available characters: {candidate_characters}

Please analyze: What does this plot segment most need to express through dialogue? How many rounds of dialogue are appropriate?
Allocate expected dialogue rounds (expected_rounds) based on actual plot, increase dialogue rounds appropriately if plot is complex.
Important: expected_rounds must be a single integer, not a range.

Format: {{"goal": "dialogue goal description", "expected_rounds": integer}}"""
    }]
    
    try:
        goal_response = generate_response(goal_prompt, performance_analyzer=performance_analyzer, stage_name="dialogue_generation")
        goal_data = convert_json(goal_response)
        print(f"  Goal analysis returned: {goal_data.get('expected_rounds')}")

        # Enhanced error handling
        if isinstance(goal_data, dict):
            dialogue_goal = goal_data.get("goal", "Advance plot")
            expected_rounds = goal_data.get("expected_rounds", 3)
            
            # Handle non-numeric situations
            try:
                expected_rounds = int(expected_rounds)
            except (ValueError, TypeError):
                expected_rounds = 3
        else:
            print(f"Goal analysis returned non-dict format: {type(goal_data)}")
            dialogue_goal = "Advance plot"
            expected_rounds = 3
            
    except Exception as e:
        print(f"Goal analysis failed: {e}")
        dialogue_goal = "Advance plot"
        expected_rounds = 3

    # 🆕 Record goal setting
    logger.info(f"GOAL_SET | session_id={session_id} | goal='{dialogue_goal}' | expected_rounds={expected_rounds}")

    # First speaker
    speaker = candidate_characters[0]
    prompt_first = [{
        "role": "system",
        "content": f"""You are {speaker}, please make the first statement based on the following plot.
Plot background: {sentence_context}
Dialogue goal: {dialogue_goal}
Other characters: {[c for c in candidate_characters if c != speaker]}
Format: {{"dialogue": "...", "action": "..."}}"""
    }]
    
    try:
        response = generate_response(prompt_first, performance_analyzer=performance_analyzer, stage_name="dialogue_generation")
        parsed = convert_json(response)
        
        if isinstance(parsed, dict) and "dialogue" in parsed:
            spoken_line = parsed.get("dialogue", "")
            action = parsed.get("action", "")
            dialogue_list.append({
                "speaker": speaker,
                "dialogue": spoken_line,
                "action": action
            })
            history += f"{speaker}: {spoken_line}\n"
            # Record first dialogue
            logger.info(f"FIRST_DIALOGUE | session_id={session_id} | speaker={speaker} | length={len(spoken_line)}")
    except Exception as e:
        print(f"First dialogue generation failed: {e}")
        # Record error
        logger.error(f"FIRST_DIALOGUE_FAILED | session_id={session_id} | error={e}")
        return []

    # Fully trust LLM's loop judgment
    round_count = 0
    SAFETY_LIMIT = 20  # Only as safety fallback
    
    while round_count < SAFETY_LIMIT:
        round_count += 1
        
        # rounds_guidance = ""
        # if round_count > expected_rounds * 1.5:
        #     rounds_guidance = f"\nWarning: Current {round_count} rounds, expected {expected_rounds} rounds, please consider whether to end."

        # Maintain original judgment format, LLM is used to it
        judge_prompt = [{
            "role": "system",
            "content": f"""You are a story screenwriter. Analyze whether the current dialogue has reached a natural stopping point:

【Plot Background】: {sentence_context}
【Dialogue Goal】: {dialogue_goal}
【Current Round】: {round_count}
【Dialogue History】:
{history}

Please judge: Has this dialogue naturally ended? Consider factors including:
- Whether the dialogue has achieved relatively complete communication
- Whether obvious repetition or dragging is avoided
- Whether character interactions have reached a reasonable level

Available characters: {candidate_characters}

Format: {{"should_continue": true/false, "next_speaker": "character name or NONE", "reason": "judgment reasoning"}}"""
        }]
        
        try:
            judge_res = generate_response(judge_prompt, performance_analyzer=performance_analyzer, stage_name="dialogue_generation")
            judge_data = convert_json(judge_res)
            
            # Enhanced type checking
            if not isinstance(judge_data, dict):
                print(f"Judgment returned non-dict format: {type(judge_data)}")
                # Record judgment failure
                logger.warning(f"JUDGE_FAILED | session_id={session_id} | round={round_count} | type={type(judge_data)}")
                break
                
            # goal_achieved = judge_data.get("goal_achieved", 5)
            should_continue = judge_data.get("should_continue", False)
            next_speaker = judge_data.get("next_speaker", "NONE")
            reason = judge_data.get("reason", "")
            
            # print(f"    📊 LLM判断: goal_achieved={goal_achieved}, should_continue={should_continue}, next_speaker={next_speaker}")
            # # 🆕 记录LLM判断详情
            # logger.info(f"LLM_JUDGE | session_id={session_id} | round={round_count} | goal_achieved={goal_achieved} | should_continue={should_continue} | next_speaker={next_speaker} | reason={reason[:50]}...")
                
        except Exception as e:
            print(f"Dialogue judgment failed: {e}, ending dialogue")
            # Record judgment error
            logger.error(f"JUDGE_ERROR | session_id={session_id} | round={round_count} | error={e}")
            break
        
        # Fully trust LLM: only look at LLM's should_continue judgment
        if (not should_continue or
            next_speaker == "NONE" or 
            next_speaker not in candidate_characters):
            print(f"  LLM decided to end dialogue")
            # Record stop reasons
            stop_reasons = []
            if not should_continue:
                stop_reasons.append("LLM_STOP")
            if next_speaker == "NONE":
                stop_reasons.append("SPEAKER_NONE")
            if next_speaker not in candidate_characters:
                stop_reasons.append("INVALID_SPEAKER")
            logger.info(f"DIALOGUE_END | session_id={session_id} | round={round_count} | reasons={stop_reasons}")
            break

        # Generate speech content
        prompt_reply = [{
            "role": "system",
            "content": f"""You are {next_speaker}, based on plot: {sentence_context}
Dialogue goal: {dialogue_goal}
Dialogue history: {history}
Continue with one sentence, format: {{"dialogue": "...", "action": "..."}}"""
        }]
        
        try:
            response = generate_response(prompt_reply, performance_analyzer=performance_analyzer, stage_name="dialogue_generation")
            parsed = convert_json(response)
            
            if isinstance(parsed, dict) and "dialogue" in parsed:
                spoken_line = parsed.get("dialogue", "")
                action = parsed.get("action", "")
                dialogue_list.append({
                    "speaker": next_speaker,
                    "dialogue": spoken_line,
                    "action": action
                })
                history += f"{next_speaker}: {spoken_line}\n"
                # Record each round of dialogue
                logger.info(f"DIALOGUE_ADD | session_id={session_id} | round={round_count} | speaker={next_speaker} | length={len(spoken_line)}")
        except Exception as e:
            print(f"Speech generation failed: {e}, skipping this round")
            # Record generation failure
            logger.warning(f"DIALOGUE_FAILED | session_id={session_id} | round={round_count} | speaker={next_speaker} | error={e}")
            continue
    
    if round_count >= SAFETY_LIMIT:
        print(f"Reached safety fallback ({SAFETY_LIMIT} rounds)")
        # Record safety limit triggered
        logger.warning(f"SAFETY_LIMIT | session_id={session_id} | limit={SAFETY_LIMIT}")
    
    # Record final statistics
    final_rounds = len(dialogue_list)
    logger.info(f"SESSION_END | session_id={session_id} | final_rounds={final_rounds} | expected={expected_rounds} | characters_used={[d['speaker'] for d in dialogue_list]}")
    
    print(f"  Generated {final_rounds} dialogues")

    rounds_data = {
        "session_id": session_id,
        "expected_rounds": expected_rounds,
        "actual_rounds": final_rounds,
        "deviation": final_rounds - expected_rounds,
        "sentence_context": sentence_context[:100],
        "characters": candidate_characters,
        "timestamp": datetime.now().isoformat()
    }

    # Save to statistics file
    try:
        stats_dir = "data/output/logs"
        os.makedirs(stats_dir, exist_ok=True)
        stats_file = f"{stats_dir}/rounds_statistics.jsonl"
        with open(stats_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(rounds_data, ensure_ascii=False) + "\n")
    except:
        pass    
    return dialogue_list


def run_dialogue_insertion(plot_list, character_json):
    """
    Integrated control flow: first judge which sentences need insertion, then generate each dialogue segment
    """
    marks = analyze_dialogue_insertions(plot_list, character_json)
    
    # Add error handling
    if not marks or not isinstance(marks, list):
        print(f"analyze_dialogue_insertions returned invalid data: {type(marks)}")
        # Return empty dialogue structure, ensure each plot has corresponding dialogue block
        return [{
            "sentence": plot,
            "need_to_action": 0,
            "actor_list": [],
            "dialogue": []
        } for plot in plot_list]
    
    final_result = []

    # Ensure returned result count matches plot_list
    plot_index = 0
    for item in marks:
        dialogue_block = {
            "sentence": item.get("sentence", ""),
            "need_to_action": item.get("need_to_action", 0),
            "actor_list": item.get("actor_list", []),
            "dialogue": []
        }
        
        if item.get("need_to_action") == 1 and item.get("actor_list"):
            # try:
            dialogue_memory = generate_dialogue_for_insertion(
                sentence_context=item["sentence"],
                candidate_characters=item["actor_list"],
                full_plot=plot_list,
                character_personality=character_json,
                performance_analyzer=None
            )
            dialogue_block["dialogue"] = dialogue_memory
            # except Exception as e:
            #     print(f"⚠️ 生成对话失败: {e}")
            #     dialogue_block["dialogue"] = []
                
        final_result.append(dialogue_block)
        plot_index += 1
    
    # If marks count is less than plot_list, supplement empty dialogue blocks
    while len(final_result) < len(plot_list):
        final_result.append({
            "sentence": plot_list[len(final_result)] if len(final_result) < len(plot_list) else "",
            "need_to_action": 0,
            "actor_list": [],
            "dialogue": []
        })
    
    print(f"Generated dialogue blocks count: {len(final_result)}, plot count: {len(plot_list)}")
    
    return final_result
def apply_structure_to_generate_dialogue(structure_marks, plot_list, characters):
    final_result = []
    for item in structure_marks:
        dialogue_block = {
            "sentence": item["sentence"],
            "need_to_action": item["need_to_action"],
            "actor_list": item["actor_list"],
            "dialogue": []
        }
        if item["need_to_action"] == 1:
            dialogue = generate_dialogue_for_insertion(
                sentence_context=item["sentence"],
                candidate_characters=item["actor_list"],
                full_plot=plot_list,
                character_personality=characters,
                performance_analyzer=None
            )
            dialogue_block["dialogue"] = dialogue
        final_result.append(dialogue_block)
    return final_result



def pretty_print_dialogue(dialogue_result):
    """
    Pretty print complete dialogue insertion structure, suitable for human debugging or writing to Markdown files
    """
    for i, block in enumerate(dialogue_result):
        print(f"\nPlot sentence {i+1}: {block['sentence'][:80]}...")
        if block["need_to_action"] == 0:
            print("No dialogue insertion needed.")
        else:
            print(f"Insert characters: {', '.join(block['actor_list'])}")
            dialogue = block.get("dialogue", {})
            for role, lines in dialogue.items():
                for line in lines:
                    print(f"  {line}")



def generate_dialogue_for_plot(instruction, characters):
    from src.utils.utils import generate_response, convert_json
    character_list = ", ".join([c["name"] for c in characters])
    prompt = f"""
Plot content as follows:
{instruction}

Characters include: {character_list}

Please generate 5-6 rounds of concise and natural dialogue for this scene, showcasing character style and interaction dynamics, format as follows:
[
  {{"speaker": "Character A", "line": "dialogue content"}},
  ...
]
"""
    response = generate_response([{"role": "user", "content": prompt}])
    return convert_json(response)
