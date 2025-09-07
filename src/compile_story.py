import os
import re
from src.utils.utils import load_json, save_json
from src.constant import output_dir

def clean_punctuation(text):
    """Clean punctuation issues - Smart detection of text language"""
    if not text:
        return text
    
    # Detect if text is primarily Chinese or English
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    # If primarily English text, use English punctuation
    if english_chars > chinese_chars:
        # Normalize to English punctuation
        text = text.replace('，', ',').replace('。', '.')
        text = text.replace('！', '!').replace('？', '?')
        text = text.replace('：', ':').replace('；', ';')
        
        # Fix incorrect punctuation combinations (English)
        text = re.sub(r'\.，+', ',', text)  # period+comma -> comma
        text = re.sub(r'，\.+', '.', text)  # comma+period -> period
        text = re.sub(r'，{2,}', ',', text)  # multiple commas -> single
        text = re.sub(r'\.{2,}', '.', text)  # multiple periods -> single
    else:
        # Normalize to Chinese punctuation (original behavior)
        text = text.replace(',', '，').replace('.', '。')
        text = text.replace('!', '！').replace('?', '？')
        
        # Fix incorrect punctuation combinations (Chinese)
        text = re.sub(r'。，+', '，', text)  # period+comma -> comma
        text = re.sub(r'，。+', '。', text)  # comma+period -> period
        text = re.sub(r'，{2,}', '，', text)  # multiple commas -> single
        text = re.sub(r'。{2,}', '。', text)  # multiple periods -> single
    
    return text.strip()

def compile_full_story_by_chapter(story_json, dialogue_json):
    """
    Chapter-level compilation (compatible with old format, but corrected field checking)
    """
    full_story = ""

    for idx, chapter in enumerate(story_json):
        chapter_id = chapter.get("chapter_id", f"Chapter {idx+1}")
        title = chapter.get("title", f"Scene {idx+1}")
        plot = chapter.get("plot", "").strip()

        full_story += f"# {chapter_id}: {title}\n\n"
        full_story += plot + "\n\n"

        # Concatenate corresponding chapter dialogue (matched by index)
        if idx < len(dialogue_json):
            dlg_block = dialogue_json[idx].get("dialogue", [])
            for line in dlg_block:
                if isinstance(line, dict) and "speaker" in line:
                    # Compatible with different dialogue field names
                    dialogue_text = line.get("dialogue", line.get("line", ""))
                    if dialogue_text:
                        full_story += f'"{dialogue_text.strip()}" ——{line["speaker"].strip()}\n\n'
                elif isinstance(line, str):
                    full_story += line.strip() + "\n\n"
                else:
                    print(f"Warning: Unrecognizable dialogue format: {line}")

        full_story += "-" * 40 + "\n\n"

    return full_story

def compile_full_story_by_sentence(story_json, sentence_dialogues):
    """
    Sentence-level compilation: precisely insert dialogue by sentence
    """
    from src.utils.utils import split_plot_into_sentences
    
    # Organize sentence-level dialogue data
    dialogue_map = {}
    for item in sentence_dialogues:
        if item.get("need_to_action") == 1 and item.get("dialogue"):
            chapter_id = item["chapter_id"]
            sentence_idx = item["sentence_index"]
            
            if chapter_id not in dialogue_map:
                dialogue_map[chapter_id] = {}
            dialogue_map[chapter_id][sentence_idx] = item["dialogue"]
    
    full_story = ""
    
    for chapter in story_json:
        chapter_id = chapter.get("chapter_id", f"Unknown")
        title = chapter.get("title", f"Unknown")
        plot = chapter.get("plot", "").strip()
        
        full_story += f"# {chapter_id}: {title}\n\n"
        
        # Split by sentence and insert dialogue
        sentences = split_plot_into_sentences(plot)
        
        for sent_idx, sentence in enumerate(sentences):
            # Add narrative sentence
            clean_sentence = clean_punctuation(sentence)
            full_story += clean_sentence + "\n\n"

            # Check if dialogue insertion is needed
            if (chapter_id in dialogue_map and 
                sent_idx in dialogue_map[chapter_id]):
                
                dialogues = dialogue_map[chapter_id][sent_idx]
                
                if dialogues:
                    for line in dialogues:
                        if isinstance(line, dict):
                            speaker = line.get("speaker", "")
                            # Compatible with different dialogue field names
                            dialogue_text = clean_punctuation(line.get("dialogue", line.get("line", "")))
                            action = line.get("action", "")  # Get action field
                            
                            if speaker and dialogue_text:
                                # Choose different format based on action presence
                                if action and action.strip():
                                    action_clean = action.strip()
                                    # Check if action already contains character name
                                    if action_clean.startswith(speaker):
                                        # If included, use directly (no duplicate addition)
                                        formatted_action = clean_punctuation(action_clean) 
                                    else:
                                        formatted_action = clean_punctuation(f'{speaker}{action_clean}')
                                    
                                    if formatted_action.endswith(('.', '!', '?', '。', '！', '？')):
                                        # Action already has ending punctuation, add space directly
                                        full_story += f'{formatted_action} "{dialogue_text.strip()}" ——{speaker}\n\n'
                                    else:
                                        # Action has no ending punctuation, add period and space
                                        full_story += f'{formatted_action}. "{dialogue_text.strip()}" ——{speaker}\n\n'
                                                                        # Option 1: Integrate action into dialogue (more natural)
                                    # full_story += f'{speaker}{action} said: "{dialogue_text.strip()}"\n\n'
                                    # full_story += f'{speaker}{action},'  # Note: comma
                                    # full_story += f'"{dialogue_text.strip()}" ——{speaker}\n\n'
                                    # Option 2: Keep original format, but add action description before dialogue
                                    # full_story += f'{speaker}{action}.\n\n'
                                    # full_story += f'"{dialogue_text.strip()}" ——{speaker}\n\n'
                                else:
                                    # When no action, maintain original format
                                    full_story += f'"{dialogue_text.strip()}" ——{speaker}\n\n'
                        elif isinstance(line, str):
                            full_story += line.strip() + "\n\n"
                        else:
                            print(f"Warning: Unrecognizable dialogue format: {line}")
        
        full_story += "-" * 40 + "\n\n"
    
    return full_story

if __name__ == "__main__":
    version = "test"
    base_dir = os.path.join(output_dir, version)

    story_json = load_json(os.path.join(base_dir, "story.json"))
    
    # Prioritize using sentence-level data
    sentence_dialogues_path = os.path.join(base_dir, "sentence_dialogues.json")
    if os.path.exists(sentence_dialogues_path):
        sentence_dialogues = load_json(sentence_dialogues_path)
        novel = compile_full_story_by_sentence(story_json, sentence_dialogues)
        print("Using sentence-level data to compile novel")
    else:
        # Fall back to chapter-level
        dialogue_json = load_json(os.path.join(base_dir, "dialogue_marks.json"))
        novel = compile_full_story_by_chapter(story_json, dialogue_json)
        print("Warning: Falling back to using chapter-level data to compile novel")

    with open(os.path.join(base_dir, "novel_story.md"), "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"Story novel has been generated: {base_dir}/novel_story.md")
