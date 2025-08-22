import os
import re
from src.utils.utils import load_json, save_json
from src.constant import output_dir

def clean_punctuation(text):
    """清理标点符号问题"""
    if not text:
        return text
    
    # 统一中英文标点符号
    text = text.replace(',', '，').replace('.', '。')
    text = text.replace('!', '！').replace('?', '？')
    
    # 修复错误的标点组合
    text = re.sub(r'。，+', '，', text)  # 句号+逗号 -> 逗号
    text = re.sub(r'，。+', '。', text)  # 逗号+句号 -> 句号
    text = re.sub(r'，{2,}', '，', text)  # 多个逗号 -> 单个
    text = re.sub(r'。{2,}', '。', text)  # 多个句号 -> 单个
    
    return text.strip()

def compile_full_story_by_chapter(story_json, dialogue_json):
    """
    章节级编译（兼容旧格式，但修正字段检查）
    """
    full_story = ""

    for idx, chapter in enumerate(story_json):
        chapter_id = chapter.get("chapter_id", f"第{idx+1}章")
        title = chapter.get("title", f"场景{idx+1}")
        plot = chapter.get("plot", "").strip()

        full_story += f"# {chapter_id}：{title}\n\n"
        full_story += plot + "\n\n"

        # 拼接对应章节对白（按 index 匹配）
        if idx < len(dialogue_json):
            dlg_block = dialogue_json[idx].get("dialogue", [])
            for line in dlg_block:
                if isinstance(line, dict) and "speaker" in line:
                    # 🔧 兼容不同的对话字段名
                    dialogue_text = line.get("dialogue", line.get("line", ""))
                    if dialogue_text:
                        full_story += f'"{dialogue_text.strip()}" ——{line["speaker"].strip()}\n\n'
                elif isinstance(line, str):
                    full_story += line.strip() + "\n\n"
                else:
                    print(f"⚠️ 无法识别的对话格式：{line}")

        full_story += "-" * 40 + "\n\n"

    return full_story

def compile_full_story_by_sentence(story_json, sentence_dialogues):
    """
    句子级编译：按句子精确插入对话
    """
    from src.utils.utils import split_plot_into_sentences
    
    # 组织句子级对话数据
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
        
        full_story += f"# {chapter_id}：{title}\n\n"
        
        # 🎯 按句子分割并插入对话
        sentences = split_plot_into_sentences(plot)
        
        for sent_idx, sentence in enumerate(sentences):
            # 添加叙述句子
            clean_sentence = clean_punctuation(sentence)
            full_story += clean_sentence + "\n\n"

            # 检查是否需要插入对话
            if (chapter_id in dialogue_map and 
                sent_idx in dialogue_map[chapter_id]):
                
                dialogues = dialogue_map[chapter_id][sent_idx]
                
                if dialogues:
                    for line in dialogues:
                        if isinstance(line, dict):
                            speaker = line.get("speaker", "")
                            # 🔧 兼容不同的对话字段名
                            dialogue_text = clean_punctuation(line.get("dialogue", line.get("line", "")))
                            action = line.get("action", "")  # 🎯 获取action字段
                            
                            if speaker and dialogue_text:
                                # 🎯 根据是否有action选择不同的格式
                                if action and action.strip():
                                    action_clean = action.strip()
                                    # 检查action是否已经包含角色名
                                    if action_clean.startswith(speaker):
                                        # 如果包含，直接使用（不重复添加）
                                        formatted_action = clean_punctuation(action_clean) 
                                    else:
                                        formatted_action = clean_punctuation(f'{speaker}{action_clean}')
                                    
                                    if formatted_action.endswith(('。', '！', '？')):
                                        # action已经有结尾标点，直接加空格
                                        full_story += f'{formatted_action} "{dialogue_text.strip()}" ——{speaker}\n\n'
                                    else:
                                        # action没有结尾标点，加句号和空格
                                        full_story += f'{formatted_action}。 "{dialogue_text.strip()}" ——{speaker}\n\n'
                                                                        # 方案1：将action融入对话（更自然）
                                    # full_story += f'{speaker}{action}说道："{dialogue_text.strip()}"\n\n'
                                    # full_story += f'{speaker}{action}，'  # 注意是逗号
                                    # full_story += f'"{dialogue_text.strip()}" ——{speaker}\n\n'
                                    # 方案2：保持原格式，但在对话前加上动作描述
                                    # full_story += f'{speaker}{action}。\n\n'
                                    # full_story += f'"{dialogue_text.strip()}" ——{speaker}\n\n'
                                else:
                                    # 无action时保持原格式
                                    full_story += f'"{dialogue_text.strip()}" ——{speaker}\n\n'
                        elif isinstance(line, str):
                            full_story += line.strip() + "\n\n"
                        else:
                            print(f"⚠️ 无法识别的对话格式：{line}")
        
        full_story += "-" * 40 + "\n\n"
    
    return full_story

if __name__ == "__main__":
    version = "test"
    base_dir = os.path.join(output_dir, version)

    story_json = load_json(os.path.join(base_dir, "story.json"))
    
    # 🎯 优先使用句子级数据
    sentence_dialogues_path = os.path.join(base_dir, "sentence_dialogues.json")
    if os.path.exists(sentence_dialogues_path):
        sentence_dialogues = load_json(sentence_dialogues_path)
        novel = compile_full_story_by_sentence(story_json, sentence_dialogues)
        print("使用句子级数据编译小说")
    else:
        # 回退到章节级
        dialogue_json = load_json(os.path.join(base_dir, "dialogue_marks.json"))
        novel = compile_full_story_by_chapter(story_json, dialogue_json)
        print("⚠️ 回退使用章节级数据编译小说")

    with open(os.path.join(base_dir, "novel_story.md"), "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"故事小说已生成：{base_dir}/novel_story.md")
