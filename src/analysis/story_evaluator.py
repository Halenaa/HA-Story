import os
import json
import numpy as np
from collections import Counter
from src.utils.utils import generate_response, save_json, load_json

def extract_events_no_hallucination(story_data, model="gpt-4.1", temperature=None):
    """
    No hallucination version: first sentence number, then let LLM choose
    temperature: None use default value, 0 represents fixed mode, >0 represents random mode
    """
    from src.utils.utils import split_plot_into_sentences
    
    # Step 1: Preprocess original text, number each sentence
    all_sentences = []
    sentence_map = {}
    sentence_counter = 0
    
    for ch in story_data:
        chapter_id = ch.get('chapter_id', '')
        plot = ch.get('plot', '')
        sentences = split_plot_into_sentences(plot)
        
        for sent in sentences:
            sentence_map[sentence_counter] = {
                "sentence": sent,
                "chapter": chapter_id
            }
            all_sentences.append(f"{sentence_counter}: {sent}")
            sentence_counter += 1

    concat_story_plot = ""
    for i in story_data:
        concat_story_plot += i.get('chapter_id', '') + "\n" + i.get('plot', '') + "\n\n"
        
    # Prepare numbered sentence list
    numbered_sentences = "\n".join(all_sentences)
    double_newline = "\n\n"

    print("  Step 1: Extract events...")
    # Step 2: Extract events
    step1_prompt = f"""
Please extract all key events from the following story.

Requirements:
1. Each event should be described concisely in 10-20 words
2. Arrange in chronological order

Important limitations:
1. Only extract events that are explicitly described as happening within each chapter, do not add any assumptions or events not explicitly described, do not infer what happened between chapters
2. Accurately describe the nature of actions, maintain accuracy of action descriptions, do not exaggerate or change their nature, for example do not understand "preparing to do X" as "already completed X" and do not understand "threatening to do Y" as "already did Y"
3. When extracting events, also need to annotate the event source

Output format:
[
  {{"description":"event description 1","reference":"chapter 1:original text"}},
  {{"description":"event description 2","reference":"chapter 2:original text"}},
  ...
]
"""
    
    # Call based on temperature parameter
    if temperature is not None:
        response1 = generate_response([{"role": "user", "content": step1_prompt}], model=model, temperature=temperature)
        response1 = generate_response([
            {"role": "user", "content":step1_prompt},
        {"role": "user", "content": f"extract the key events base on the following story plot:\n\n{concat_story_plot}"}
        ], model=model, temperature=temperature)

    else:
        response1 = generate_response([{"role": "user", "content": step1_prompt}], model=model)
        response1 = generate_response([
            {"role": "user", "content":step1_prompt},
        {"role": "user", "content": f"extract the key events base on the following story plot:\n\n{concat_story_plot}"}
        ], model=model)
    try:
        from src.utils.utils import convert_json
        events_only = convert_json(response1)
        if not isinstance(events_only, list):
            print(f"WARNING: Event extraction failed")
            return []
    except Exception as e:
        print(f"WARNING: Event extraction failed: {e}")
        return []
    
    print(f"  Extracted {len(events_only)} events")
    print("  Step 2: Match original sentences...")
    
    # Step 3: Let LLM select sentence numbers for each event
    step2_prompt = f"""
Given a list of events and numbered original sentences, please select the most matching sentence number for each event.

Event list:
{json.dumps(events_only, ensure_ascii=False, indent=2)}

Numbered original sentences:
{numbered_sentences}

Requirements:
1. Select one most matching sentence number for each event
2. If no matching sentence is found, fill in -1 for the number
3. Can only select from the given numbers, cannot fill in other numbers

Output format:
[
  {{
    "event": "event description",
    "sentence_number": number,
    "confidence": "high/medium/low"
  }}
]
"""
    
    # Call based on temperature parameter
    if temperature is not None:
        response2 = generate_response([{"role": "user", "content": step2_prompt}], model=model, temperature=temperature)
    else:
        response2 = generate_response([{"role": "user", "content": step2_prompt}], model=model)
    
    try:
        matches = convert_json(response2)
        if not isinstance(matches, list):
            print(f"WARNING: Matching failed")
            return []
        
        # Build final results
        final_events = []
        filtered_count = 0
        
        for match in matches:
            sentence_num = match.get("sentence_number", -1)
            
            if sentence_num == -1 or sentence_num not in sentence_map:
                filtered_count += 1
                print(f"  WARNING: Filtered event (no matching sentence): {match.get('event', '')}")
                continue
            
            sentence_info = sentence_map[sentence_num]
            final_events.append({
                "event": match.get("event", ""),
                "source": sentence_info["sentence"],
                "chapter": sentence_info["chapter"],
                "confidence": match.get("confidence", "unknown")
            })
        
        print(f"  Matching completed, filtered {filtered_count} events with no matches")

        validated_events = validate_events_against_source(final_events, model=model, temperature=temperature)
        return validated_events

        
    except Exception as e:
        print(f"WARNING: Matching failed: {e}")
        return []

def validate_events_against_source(events, model="gpt-4.1", temperature=None):
    """
    Step 3: Verify consistency between events and original text, eliminate hallucinations
    """
    if not events:
        return []
    
    print("  Step 3: Verify event accuracy...")
    
    # Format event and original text comparison
    event_source_pairs = []
    for i, event in enumerate(events):
        event_source_pairs.append(f"""
Event {i+1}: {event['event']}
Original text: {event['source']}
Chapter: {event['chapter']}
---""")
    
    formatted_pairs = "\n".join(event_source_pairs)
    
    validation_prompt = f"""
You are now a strict fact-checker who needs to verify whether event descriptions exactly match the original text.

Pay special attention to the following high-risk hallucination behaviors:
1. If the original text says "preparing/intending", it cannot be said as "already completed";
2. If the original text says "threatening/attempting", it cannot be said as "already accomplished";
3. If the original text does not explicitly describe "delivery/arrival/completion", it cannot be assumed to be completed;
4. All unverified "obtaining/getting/successful implementation" behaviors should be questioned.

Please compare each event with the original chapter content sentence by sentence to determine if there is "completion status hallucination". If you find that it needs to be modified to the correct event description.

{formatted_pairs}

Output format:
[
  {{
    "original_event": "original event description",
    "corrected_event": "corrected event description (same as original if no issues)",
    "has_issue": true/false,
    "issue_type": "issue type (if any)"
  }}
]

Important: Only output pure JSON, do not add any comments.
"""
    
    # Call based on temperature parameter
    if temperature is not None:
        response = generate_response([{"role": "user", "content": validation_prompt}], model=model, temperature=temperature)
    else:
        response = generate_response([{"role": "user", "content": validation_prompt}], model=model)
    
    try:
        from src.utils.utils import convert_json
        validation_results = convert_json(response)
        if not isinstance(validation_results, list):
            print("WARNING: Validation step format error, keeping original events")
            return events
        
        # Apply validation results
        validated_events = []
        corrected_count = 0
        
        for i, (original_event, validation) in enumerate(zip(events, validation_results)):
            if validation.get("has_issue", False):
                corrected_count += 1
                print(f"  Corrected event {i+1}: {validation.get('original_event', '')} → {validation.get('corrected_event', '')}")
                # Use corrected event description
                corrected_event = original_event.copy()
                corrected_event["event"] = validation.get("corrected_event", original_event["event"])
                validated_events.append(corrected_event)
            else:
                validated_events.append(original_event)
        
        print(f"  Validation completed, corrected {corrected_count} events")
        return validated_events
        
    except Exception as e:
        print(f"WARNING: Validation step failed: {e}, keeping original events")
        return events

def extract_events_fixed_mode(story_data, model="gpt-4.1"):
    """
    Fixed mode: completely reproducible event extraction
    """
    print("  Fixed mode (temperature=0)")
    return extract_events_no_hallucination(story_data, model=model, temperature=0)


def extract_events_statistical_mode(story_data, model="gpt-4.1", runs=3):
    """
    Statistical mode: multiple runs with statistical analysis
    """
    print(f"  Statistical mode: running {runs} times...")
    
    all_results = []
    all_event_counts = []
    
    for i in range(runs):
        print(f"    Run {i+1}/{runs}...")
        
        # Use randomness each time (not setting temperature=0)
        events = extract_events_no_hallucination(story_data, model=model, temperature=0.3)
        
        if events:
            all_results.append(events)
            all_event_counts.append(len(events))
            print(f"      Run {i+1}: {len(events)} events")
        else:
            print(f"      Run {i+1}: extraction failed")
    
    if not all_results:
        print("WARNING: All runs failed")
        return []
    
    # Statistical analysis
    event_counts = np.array(all_event_counts)
    avg_count = np.mean(event_counts)
    std_count = np.std(event_counts)
    min_count = np.min(event_counts)
    max_count = np.max(event_counts)
    
    # Calculate confidence interval (95%)
    if len(event_counts) > 1:
        confidence_interval = 1.96 * std_count / np.sqrt(len(event_counts))
        ci_lower = avg_count - confidence_interval
        ci_upper = avg_count + confidence_interval
    else:
        ci_lower = ci_upper = avg_count
    
    # Calculate stability score
    stability_score = 1 - (std_count / avg_count) if avg_count > 0 else 0
    
    print(f"  Statistical analysis results:")
    print(f"    - Event count range: {min_count}-{max_count}")
    print(f"    - Average event count: {avg_count:.1f} ± {std_count:.1f}")
    print(f"    - 95% confidence interval: [{ci_lower:.1f}, {ci_upper:.1f}]")
    print(f"    - Stability score: {stability_score:.3f} (0-1, higher is more stable)")
    
    # Select the result closest to the average as representative
    best_idx = np.argmin(np.abs(event_counts - avg_count))
    representative_result = all_results[best_idx]
    
    # Add statistical information to each event
    for event in representative_result:
        event["statistical_info"] = {
            "run_index": int(best_idx + 1),
            "total_runs": runs,
            "avg_event_count": round(float(avg_count), 1),
            "std_event_count": round(float(std_count), 1),
            "stability_score": round(float(stability_score), 3),
            "confidence_interval_95": [round(float(ci_lower), 1), round(float(ci_upper), 1)],
            "event_count_range": [int(min_count), int(max_count)]
        }
    
    # Add overall statistical information
    statistical_summary = {
        "runs_completed": len(all_results),
        "runs_failed": runs - len(all_results),
        "success_rate": len(all_results) / runs,
        "event_counts_by_run": all_event_counts,
        "statistical_metrics": {
            "mean": round(float(avg_count), 1),
            "std": round(float(std_count), 1),
            "min": int(min_count),
            "max": int(max_count),
            "stability_score": round(float(stability_score), 3),
            "confidence_interval_95": [round(float(ci_lower), 1), round(float(ci_upper), 1)]
        }
    }
    
    print(f"  Selected run {best_idx+1} result as representative (closest to average)")
    
    return representative_result, statistical_summary


def analyze_papalampidi_structure(events, model="gpt-4.1", temperature=None):
    """
    Analyze story structure using Papalampidi framework
    """
    # Only pass event descriptions to analysis
    event_descriptions = [event.get("event", "") if isinstance(event, dict) else str(event) for event in events]
    events_str = json.dumps(event_descriptions, ensure_ascii=False, indent=2)
    
    prompt = f"""
Given a list of events, please annotate 5 key turning points (TP) and 6 stages:

Event list: {events_str}

Turning point definitions:
- TP1 (Opportunity): Key event that introduces the main plot
- TP2 (Change of Plans): Moment when goals/plans change
- TP3 (Point of No Return): Commitment point where characters fully engage and cannot retreat
- TP4 (Major Setback): Moment of greatest crisis/setback
- TP5 (Climax): Final resolution moment of main conflict

Stage definitions:
- Setup: Background setting and character introduction
- New Situation: Establishment of new environment/new challenges
- Progress: Process of moving toward goals
- Complications: Escalation of conflicts and difficulties
- Final Push: Final decisive action
- Aftermath: Results and long-term effects

Output format:
{{
  "turning_points": {{
    "TP1": "specific event description",
    "TP2": "specific event description", 
    "TP3": "specific event description",
    "TP4": "specific event description",
    "TP5": "specific event description"
  }},
  "stage_division": {{
    "Setup": ["event1", "event2"],
    "New Situation": ["event3"],
    "Progress": ["event4", "event5"],
    "Complications": ["event6", "event7", "event8"],
    "Final Push": ["event9"],
    "Aftermath": ["event10"]
  }}
}}

Important: Only output pure JSON, do not add any comments or explanatory text.
"""
    
    # Call based on temperature parameter
    if temperature is not None:
        response = generate_response([{"role": "user", "content": prompt}], model=model, temperature=temperature)
    else:
        response = generate_response([{"role": "user", "content": prompt}], model=model)
    
    try:
        from src.utils.utils import convert_json
        result = convert_json(response)
        if not isinstance(result, dict):
            print(f"WARNING: Papalampidi analysis format error")
            return {"turning_points": {}, "stage_division": {}}
        return result
    except Exception as e:
        print(f"WARNING: Papalampidi analysis failed: {e}")
        return {"turning_points": {}, "stage_division": {}}


def analyze_li_functions(events, model="gpt-4.1", temperature=None):
    """
    Analyze story functions using Li framework
    """
    # Only pass event descriptions to analysis
    event_descriptions = [event.get("event", "") if isinstance(event, dict) else str(event) for event in events]
    events_str = json.dumps(event_descriptions, ensure_ascii=False, indent=2)
    
    prompt = f"""
Given a list of events, please annotate each event with 10 function labels:

Event list: {events_str}

Function label definitions:
- Abstract: Summary of story points
- Orientation: Background setting (time, place, characters)
- Complicating Action: Events that increase tension and drive the plot
- MRE: Most important/most reportable event (Most Reportable Event)
- Minor Resolution: Events that partially relieve tension
- Return of MRE: Reappearance of MRE theme
- Resolution: Events that resolve main conflicts
- Aftermath: Long-term effects after main events
- Evaluation: Narrator's comments on story meaning
- Direct Comment: Direct comments to the audience

Output format:
{{
  "event1": "label name",
  "event2": "label name",
  "event3": "label name",
  ...
}}

Important: Only output pure JSON, do not add any comments or explanatory text.
"""
    
    # Call based on temperature parameter
    if temperature is not None:
        response = generate_response([{"role": "user", "content": prompt}], model=model, temperature=temperature)
    else:
        response = generate_response([{"role": "user", "content": prompt}], model=model)
    
    try:
        from src.utils.utils import convert_json
        result = convert_json(response)
        if not isinstance(result, dict):
            print(f"WARNING: Li analysis format error")
            return {}
        return result
    except Exception as e:
        print(f"WARNING: Li analysis failed: {e}")
        return {}


def analyze_story_structure(events, papalampidi_result, li_result, mode="default", statistical_summary=None):
    """
    Objectively analyze story structure
    """
    analysis = {
        "basic_info": {
            "total_events": len(events),
            "analysis_mode": mode,
            "analysis_time": None
        },
        "Papalampidi_structure_analysis": {
            "turning_point_integrity": {},
            "stage_integrity": {}
        },
        "Li_function_analysis": {
            "core_function_check": {},
            "function_distribution": {},
            "function_diversity": 0
        }
    }
    
    # Add statistical information (if statistical mode)
    if statistical_summary:
        analysis["statistical_analysis_summary"] = statistical_summary
    
    # Analyze Papalampidi structure
    required_tps = ["TP1", "TP2", "TP3", "TP4", "TP5"]
    found_tps = [tp for tp in required_tps if papalampidi_result.get("turning_points", {}).get(tp)]
    missing_tps = [tp for tp in required_tps if tp not in found_tps]
    
    analysis["Papalampidi_structure_analysis"]["turning_point_integrity"] = {
        "identified_tps": found_tps,
        "missing_tps": missing_tps,
        "TP_coverage": f"{len(found_tps)}/5"
    }
    
    required_stages = ["Setup", "New Situation", "Progress", "Complications", "Final Push", "Aftermath"]
    found_stages = [stage for stage in required_stages if papalampidi_result.get("stage_division", {}).get(stage)]
    missing_stages = [stage for stage in required_stages if stage not in found_stages]
    
    analysis["Papalampidi_structure_analysis"]["stage_integrity"] = {
        "identified_stages": found_stages,
        "missing_stages": missing_stages,
        "stage_coverage": f"{len(found_stages)}/6"
    }
    
    # Analyze Li functions
    core_functions = ["Orientation", "Complicating Action", "MRE", "Resolution"]
    for func in core_functions:
        exists = any(func in value for value in li_result.values())
        analysis["Li_function_analysis"]["core_function_check"][func] = "exists" if exists else "missing"

    # Function distribution statistics
    func_counts = Counter(li_result.values())
    analysis["Li_function_analysis"]["function_distribution"] = dict(func_counts)
    analysis["Li_function_analysis"]["function_diversity"] = len(set(li_result.values()))
    
    return analysis


def read_story_file(story_path):
    """
    Read story file, supports JSON and Markdown formats
    """
    if not os.path.exists(story_path):
        print(f"WARNING: Story file does not exist: {story_path}")
        return None, None
    
    file_extension = os.path.splitext(story_path)[1].lower()
    
    if file_extension == '.json':
        print("Detected JSON format file")
        story_data = load_json(story_path)
        return story_data, 'json'
    
    elif file_extension == '.md':
        print("Detected Markdown format file")
        with open(story_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 'markdown'
    
    else:
        print(f"WARNING: Unsupported file format: {file_extension}")
        return None, None

def parse_markdown_story(markdown_content):
    """
    Parse Markdown format story content
    Returns chapter list in JSON-like structure
    """
    import re
    
    # Split by chapters
    chapter_sections = re.split(r'\n# ', markdown_content)
    
    # Handle first chapter (may not have leading newline)
    if chapter_sections[0].startswith('# '):
        chapter_sections[0] = chapter_sections[0][2:]  # Remove leading '# '
    
    chapters = []
    
    for i, section in enumerate(chapter_sections):
        if not section.strip():
            continue
            
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # First line is title
        title = lines[0].strip()
        
        # Rest is content
        content_lines = lines[1:]
        content = '\n'.join(content_lines).strip()
        
        # Remove markdown syntax markers (simple processing)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*([^*]+)\*', r'\1', content)      # Italic
        content = re.sub(r'`([^`]+)`', r'\1', content)        # Code
        content = re.sub(r'---+', '', content)               # Separator lines
        
        # Create JSON-like structure
        chapter = {
            'chapter_id': f"Chapter {i+1}",
            'title': title,
            'plot': content
        }
        chapters.append(chapter)
    
    print(f"Parsed {len(chapters)} chapters")
    return chapters

def run_story_evaluation(version, mode="default", runs=3, story_file="story_updated.json", model="gpt-4.1"):
    """
    Main function: run complete story evaluation
    mode: "default", "fixed", "statistical"
    Supports JSON and Markdown formats
    """
    from src.constant import output_dir
    
    print(f"\nStarting story structure evaluation: {version}")
    
    # Read story data
    story_path = os.path.join(output_dir, version, story_file)
    story_data, file_format = read_story_file(story_path)
    
    if story_data is None:
        return None
    
    # Process data based on file format
    if file_format == 'markdown':
        story_data = parse_markdown_story(story_data)
    elif file_format == 'json':
        # JSON format remains unchanged
        pass
    
    # Step 1: Extract key events based on mode
    statistical_summary = None
    
    if mode == "fixed":
        print("Step 1: Fixed mode key event extraction...")
        events = extract_events_fixed_mode(story_data, model=model)
        temp_for_analysis = 0  # Analysis stage also uses fixed mode

    elif mode == "statistical":
        print(f"Step 1: Statistical mode key event extraction ({runs} runs)...")
        result = extract_events_statistical_mode(story_data, model=model, runs=runs)
        if isinstance(result, tuple):
            events, statistical_summary = result
        else:
            events = result
        temp_for_analysis = 0  # Analysis stage uses fixed mode to ensure consistent analysis for same events

    else:
        print("Step 1: Default mode key event extraction...")
        events = extract_events_no_hallucination(story_data, model=model)
        temp_for_analysis = None  # Use default temperature
    
    print(f"Finally extracted {len(events)} valid events")
    
    if len(events) == 0:
        print("WARNING: No valid events extracted, terminating analysis")
        return None
    
    # Step 2: Papalampidi structure analysis
    print("Step 2: Papalampidi structure analysis...")
    papalampidi_result = analyze_papalampidi_structure(events, model=model, temperature=temp_for_analysis)
    
    # Step 3: Li function analysis
    print("Step 3: Li function analysis...")
    li_result = analyze_li_functions(events, model=model, temperature=temp_for_analysis)
    
    # Step 4: Comprehensive analysis
    print("Step 4: Comprehensive analysis...")
    structure_analysis = analyze_story_structure(events, papalampidi_result, li_result, mode, statistical_summary)
    
    # Summarize results
    evaluation_result = {
        "evaluation_mode": f"{mode} mode" + (f" ({runs} runs)" if mode == "statistical" else ""),
        "event_list": events,
        "Papalampidi_detailed_results": papalampidi_result,
        "Li_detailed_results": li_result,
        "structure_analysis": structure_analysis
    }
    
    # Save results
    output_filename = f"story_structure_analysis_{mode}.json"
    if mode == "statistical":
        output_filename = f"story_structure_analysis_{mode}_{runs}runs.json"
    save_json(evaluation_result, version, output_filename)
    
    # Print summary
    print_evaluation_summary(structure_analysis, mode, statistical_summary)
    
    return evaluation_result


def print_evaluation_summary(structure_analysis, mode, statistical_summary=None):
    """Print evaluation summary"""
    tp_coverage = structure_analysis["Papalampidi_structure_analysis"]["turning_point_integrity"]["TP_coverage"]
    stage_coverage = structure_analysis["Papalampidi_structure_analysis"]["stage_integrity"]["stage_coverage"]
    core_missing = [k for k, v in structure_analysis["Li_function_analysis"]["core_function_check"].items() if v == "missing"]
    function_diversity = structure_analysis["Li_function_analysis"]["function_diversity"]
    
    mode_display = f"{mode} mode"
    
    print(f"""
{mode_display} evaluation completed! Result summary:
-------------------------------
Papalampidi structure:
   - Turning point coverage: {tp_coverage}
   - Stage coverage: {stage_coverage}
Li function analysis:
   - Missing core functions: {core_missing if core_missing else 'None'}
   - Function diversity: {function_diversity} types""")
    
    # If statistical mode, display statistical information
    if statistical_summary and mode == "statistical":
        metrics = statistical_summary["statistical_metrics"]
        print(f"""Statistical analysis summary:
   - Success rate: {statistical_summary['success_rate']:.1%}
   - Event count: {metrics['mean']} ± {metrics['std']} (range: {metrics['min']}-{metrics['max']})
   - 95% confidence interval: [{metrics['confidence_interval_95'][0]}, {metrics['confidence_interval_95'][1]}]
   - Stability score: {metrics['stability_score']:.3f}/1.000""")
    
    print(f"""-------------------------------
Detailed results saved
""")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced story structure evaluation tool")
    parser.add_argument("--version", type=str, required=True, help="Version folder name")
    parser.add_argument("--mode", type=str, choices=["default", "fixed", "statistical"], default="default", 
                       help="Evaluation mode: default (default), fixed (fixed reproducible) or statistical (statistical analysis)")
    parser.add_argument("--runs", type=int, default=3, help="Number of runs for statistical mode")
    parser.add_argument("--story-file", type=str, default="story_updated.json", help="Story file name")
    parser.add_argument("--model", type=str, default="gpt-4.1", help="LLM model to use")
    
    args = parser.parse_args()
    run_story_evaluation(args.version, args.mode, args.runs, args.story_file, args.model)