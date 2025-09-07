import os
import re
import json
from src.utils.utils import generate_response
from src.constant import output_dir

# ------------------------------
# Split markdown into chapters (backup)
# ------------------------------
def split_novel_by_chapter(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Support both Chinese and English chapter formats
    # Chinese: # 第1章：title, English: # Chapter 1: title
    chapters = re.split(r'#\s*(?:第\s*\d+\s*章|Chapter\s+\d+)[:：]\s*', content)[1:]
    titles = re.findall(r'#\s*(?:第\s*\d+\s*章|Chapter\s+\d+)[:：]\s*(.*)', content)

    return [
        {"title": titles[i].strip(), "content": chap.strip()}
        for i, chap in enumerate(chapters)
    ]

# ------------------------------
# Generate transition sentences between chapters
# ------------------------------
def generate_transition(prev_title, next_title, prev_summary, prev_content):
    messages = [
        {"role": "system", "content": "You are a novelist"},
        {"role": "user", "content": f"""Please generate natural transition sentences based on the following information to connect contexts and guide readers from the current chapter to the next.

【Current Chapter Title】{prev_title}
【Current Chapter Summary】{prev_summary}
【Current Chapter Text Fragment】{prev_content.strip()}...
【Next Chapter Title】{next_title}

Please generate natural connecting transition sentences without quotes or explanations.
"""}
    ]
    return generate_response(messages).strip()

# ------------------------------
# Generate final ending sentence
# ------------------------------
def generate_ending(last_title, last_content):
    messages = [
        {"role": "system", "content": "You are a novelist"},
        {"role": "user", "content": f"""This is the last chapter of the novel, titled "{last_title}". The content is as follows:

{last_content.strip()}

Please write an ending sentence with a sense of closure to wrap up the entire text and let readers feel the story has ended satisfactorily. Don't add quotes or explanations.
"""}
    ]
    return generate_response(messages).strip()

# ------------------------------
# Process chapter content (merge plot and dialogue)
# ------------------------------
def process_chapter_content(plot, dialogues):
    """Merge plot and dialogue list into chapter content"""
    content = plot.strip()
    seen_lines = set()
    
    for line in dialogues:
        if isinstance(line, dict):
            speaker = line.get("speaker", "")
            text = line.get("line", line.get("dialogue", ""))
            if text and speaker:
                quoted = f'"{text}" ——{speaker}'
                if quoted not in seen_lines:
                    content += f'\n\n{quoted}'
                    seen_lines.add(quoted)
        elif isinstance(line, str):
            if line not in seen_lines:
                content += f'\n\n{line}'
                seen_lines.add(line)
    
    return content

# ------------------------------
# Main function: plot+dialogue concatenation + chapter transition generation
# ------------------------------
def enhance_story_with_transitions(task_name="test", input_story_file=None):
    base_dir = os.path.join(output_dir, task_name)
    reorder_path = os.path.join(base_dir, "test_reorder_outline.json")
    outline_path = reorder_path if os.path.exists(reorder_path) else os.path.join(base_dir, "test_outline.json")
    
    if input_story_file:
        story_path = os.path.join(base_dir, input_story_file)
        dialogue_path = os.path.join(base_dir, "dialogue_updated.json")
        
        with open(story_path, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        with open(dialogue_path, 'r', encoding='utf-8') as f:
            dialogue_data = json.load(f)
        
        # Detect data type
        if len(dialogue_data) > 0 and "sentence_index" in dialogue_data[0]:
            # Sentence-level data processing
            print("Detected sentence-level dialogue data, using sentence-level compilation...")
            
            from src.compile_story import compile_full_story_by_sentence
            full_content = compile_full_story_by_sentence(story_data, dialogue_data)
            
            # Split content by chapters
            chapters = []
            current_chapter = None
            chapter_lines = []
            
            for line in full_content.split('\n'):
                if line.startswith('# Chapter'):
                    if current_chapter is not None:
                        chapters.append({
                            "title": current_chapter["title"],
                            "content": '\n'.join(chapter_lines).strip()
                        })
                    
                    title_match = re.match(r'# Chapter \d+:\s*(.+)', line)
                    current_chapter = {
                        "title": title_match.group(1) if title_match else "Unknown Chapter"
                    }
                    chapter_lines = []
                else:
                    chapter_lines.append(line)
            
            if current_chapter and chapter_lines:
                chapters.append({
                    "title": current_chapter["title"],
                    "content": '\n'.join(chapter_lines).strip()
                })
        else:
            # Chapter-level processing (as backup)
            print("Using chapter-level dialogue data...")
            chapters = []
            for idx, (story_item, dialogue_item) in enumerate(zip(story_data, dialogue_data)):
                chapter_title = story_item.get("title", f"Chapter {idx+1}")
                chapter_plot = story_item.get("plot", "")
                chapter_dialogue = dialogue_item.get("dialogue", [])
                
                chapter_content = process_chapter_content(chapter_plot, chapter_dialogue)
                chapters.append({
                    "title": chapter_title,
                    "content": chapter_content
                })
    else:
        # Read from markdown
        md_path = os.path.join(base_dir, "novel_story.md")
        chapters = split_novel_by_chapter(md_path)
    
    # Load outline
    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)
    
    # Ensure chapter count matches
    if len(chapters) != len(outline):
        print(f"Warning: chapters has {len(chapters)} chapters, outline has {len(outline)} chapters")
        min_len = min(len(chapters), len(outline))
        chapters = chapters[:min_len]
        outline = outline[:min_len]
    
    # Generate enhanced content
    enhanced_content = ""
    for idx, chapter in enumerate(chapters):
        if idx < len(outline):
            # Add chapter title
            chapter_id = outline[idx].get("chapter_id", f"Chapter {idx+1}")
            title = outline[idx].get("title", chapter["title"])
            enhanced_content += f"# {chapter_id}: {title}\n\n"
            enhanced_content += chapter['content']
            
            # Generate transition
            if idx < len(chapters) - 1 and idx < len(outline) - 1:
                current_title = outline[idx]["title"]
                next_title = outline[idx + 1]["title"]
                current_summary = outline[idx].get("summary", "")
                
                # Use the last part of chapter content as context
                content_preview = chapter['content'][-500:] if len(chapter['content']) > 500 else chapter['content']
                
                transition = generate_transition(
                    current_title, next_title, 
                    current_summary, content_preview
                )
                enhanced_content += f"\n\n{transition}\n\n"
    
    # Generate ending
    if chapters and outline:
        last_title = outline[-1]["title"]
        last_content = chapters[-1]["content"]
        ending = generate_ending(last_title, last_content)
        enhanced_content += f"\n\n{ending}\n"
    
    # Save enhanced version
    output_path = os.path.join(base_dir, "enhanced_story_updated.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print(f"Enhanced story has been generated: {output_path}")

# ------------------------------
# Dialogue polishing support functions
# ------------------------------
def load_character_info(character_path):
    with open(character_path, "r", encoding="utf-8") as f:
        characters = json.load(f)
    return {char["name"]: char for char in characters}

def guess_speaker(text, character_names):
    for name in character_names:
        if name in text:
            return name
    return None

def build_polish_prompt(speaker, dialogue, character_info, action="", context=""):
    traits = character_info.get("traits", "")
    background = character_info.get("background", "")
    
    action_hint = f"\nCharacter action: {action}" if action else ""
    context_hint = f"\nScene context: {context[:100]}..." if context else ""
    
    return [
        {"role": "system", "content": "You are a novelist skilled at naturally integrating dialogue into narrative"},
        {"role": "user", "content": f"""Please rewrite the following dialogue into natural novel narration:

Character: {speaker}
Personality: {traits}
Background: {background}{action_hint}{context_hint}
Original dialogue: "{dialogue}"

Requirements:
1. Naturally integrate dialogue into action and emotional descriptions
2. If there are action prompts, skillfully integrate them into the narrative
3. Keep the core content of the dialogue unchanged
4. Output smooth and natural novel paragraphs

Example output format:
- "Little Red Riding Hood!" The investigator frowned and stared intently at Little Red Riding Hood, solemnly instructing, "This sealed container holds an extremely important medical chip. You must ensure it is safely and punctually delivered to the designated hospital without any mishaps."
- Little Red Riding Hood adjusted the spacecraft's direction while frowning and asking: "Navigation assistant, please confirm the asteroid belt data ahead."

Please generate natural novel paragraphs:"""},
    ]
# ------------------------------
# Main dialogue polishing function
# ------------------------------
def polish_dialogues_in_story(task_name="test", input_dialogue_file=None):
    base_dir = os.path.join(output_dir, task_name)
    
    # Read all required data
    md_path = os.path.join(base_dir, "enhanced_story_updated.md")
    char_path = os.path.join(base_dir, "characters.json")
    dialogue_path = os.path.join(base_dir, "dialogue_updated.json")  # Sentence-level data
    behavior_path = os.path.join(base_dir, "behavior_timeline_raw.json")
    
    # Load data
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    char_dict = load_character_info(char_path)
    sentence_dialogues = json.load(open(dialogue_path))
    behavior_timeline = json.load(open(behavior_path)) if os.path.exists(behavior_path) else []
    
    # Build action lookup table
    action_map = {}
    for sentence in sentence_dialogues:
        if sentence.get("dialogue"):
            chapter_id = sentence["chapter_id"]
            sent_idx = sentence["sentence_index"]
            for dialogue in sentence["dialogue"]:
                speaker = dialogue.get("speaker", "")
                text = dialogue.get("dialogue", "")
                action = dialogue.get("action", "")
                if speaker and text:
                    key = f"{text}——{speaker}"  # For matching original text
                    action_map[key] = {
                        "action": action,
                        "context": sentence["sentence"],
                        "chapter_id": chapter_id,
                        "sentence_index": sent_idx
                    }
    
    # Match and polish
    # Match dialogue pattern: "dialogue content" ——speaker
    # Support both Chinese and English punctuation
    pattern = r'"([^"]{1,500}?)"\s*[——–—-]+\s*([^\n\r]*?)\s*(?=\n|$)'
    
    def replace_dialogue(match):
        original_text = match.group(1)
        speaker = match.group(2)
        full_match = match.group(0)
        
        if speaker in char_dict:
            # Find corresponding action
            lookup_key = f"{original_text}——{speaker}"
            action_info = action_map.get(lookup_key, {})
            
            # Build enhanced prompt
            prompt = build_polish_prompt(
                speaker, 
                original_text, 
                char_dict[speaker],
                action_info.get("action", ""),
                action_info.get("context", "")
            )
            
            try:
                polished = generate_response(prompt).strip()
                print(f"Polishing successful: {speaker}'s dialogue")
                return polished
            except Exception as e:
                print(f"Warning: Polishing failed: {e}")
                return full_match
        
        return full_match
    
    # Use regular expression replacement
    polished_content = re.sub(pattern, replace_dialogue, content)
    
    # Save results
    output_path = os.path.join(base_dir, "enhanced_story_dialogue_updated.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(polished_content)
    
    print(f"Dialogue polishing completed: {output_path}")
