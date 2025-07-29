import os
import re
import json
from src.utils.utils import generate_response
from src.constant import output_dir

# ------------------------------
# 拆分 markdown 为章节（备用）
# ------------------------------
def split_novel_by_chapter(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    chapters = re.split(r'#\s*第\s*\d+\s*章[:：]', content)[1:]
    titles = re.findall(r'#\s*第\s*\d+\s*章[:：](.*)', content)

    return [
        {"title": titles[i].strip(), "content": chap.strip()}
        for i, chap in enumerate(chapters)
    ]

# ------------------------------
# 生成章节之间的过渡句
# ------------------------------
def generate_transition(prev_title, next_title, prev_summary, prev_content):
    messages = [
        {"role": "system", "content": "你是小说作者"},
        {"role": "user", "content": f"""请基于以下信息生成自然的过渡句，衔接上下文，引导读者从当前章节进入下一章。

【当前章节标题】{prev_title}
【当前章节概要】{prev_summary}
【当前章节正文片段】{prev_content.strip()}...
【下一章节标题】{next_title}

请生成自然衔接的过渡句，不加引号，不加解释。
"""}
    ]
    return generate_response(messages).strip()

# ------------------------------
# 生成最终结尾句
# ------------------------------
def generate_ending(last_title, last_content):
    messages = [
        {"role": "system", "content": "你是小说作者"},
        {"role": "user", "content": f"""这是小说的最后一章，标题为"{last_title}"。内容如下：

{last_content.strip()}

请写一段具有结束感的结尾句子，用来收束全文，让读者感受到故事圆满结束。不要加引号，不要解释。
"""}
    ]
    return generate_response(messages).strip()

# ------------------------------
# 处理章节内容（合并plot和dialogue）
# ------------------------------
def process_chapter_content(plot, dialogues):
    """将plot和dialogue列表合并成章节内容"""
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
# 主函数：剧情+对话拼接 + 章节过渡生成
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
        
        # 检测数据类型
        if len(dialogue_data) > 0 and "sentence_index" in dialogue_data[0]:
            # 句子级数据处理
            print("📝 检测到句子级对话数据，使用句子级编译...")
            
            from src.compile_story import compile_full_story_by_sentence
            full_content = compile_full_story_by_sentence(story_data, dialogue_data)
            
            # 将内容按章节分割
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
                    
                    title_match = re.match(r'# Chapter \d+[：:]\s*(.+)', line)
                    current_chapter = {
                        "title": title_match.group(1) if title_match else "未知章节"
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
            # 章节级处理（作为后备）
            print("📝 使用章节级对话数据...")
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
        # 从 markdown 读取
        md_path = os.path.join(base_dir, "novel_story.md")
        chapters = split_novel_by_chapter(md_path)
    
    # 加载 outline
    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)
    
    # 确保章节数量匹配
    if len(chapters) != len(outline):
        print(f"⚠️ 警告：chapters有{len(chapters)}章，outline有{len(outline)}章")
        min_len = min(len(chapters), len(outline))
        chapters = chapters[:min_len]
        outline = outline[:min_len]
    
    # 生成增强内容
    enhanced_content = ""
    for idx, chapter in enumerate(chapters):
        if idx < len(outline):
            # 添加章节标题
            chapter_id = outline[idx].get("chapter_id", f"Chapter {idx+1}")
            title = outline[idx].get("title", chapter["title"])
            enhanced_content += f"# {chapter_id}：{title}\n\n"
            enhanced_content += chapter['content']
            
            # 生成过渡
            if idx < len(chapters) - 1 and idx < len(outline) - 1:
                current_title = outline[idx]["title"]
                next_title = outline[idx + 1]["title"]
                current_summary = outline[idx].get("summary", "")
                
                # 使用章节内容的最后部分作为上下文
                content_preview = chapter['content'][-500:] if len(chapter['content']) > 500 else chapter['content']
                
                transition = generate_transition(
                    current_title, next_title, 
                    current_summary, content_preview
                )
                enhanced_content += f"\n\n{transition}\n\n"
    
    # 生成结尾
    if chapters and outline:
        last_title = outline[-1]["title"]
        last_content = chapters[-1]["content"]
        ending = generate_ending(last_title, last_content)
        enhanced_content += f"\n\n{ending}\n"
    
    # 保存增强版本
    output_path = os.path.join(base_dir, "enhanced_story_updated.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_content)
    
    print(f"✅ 增强版故事已生成：{output_path}")

# ------------------------------
# 对话润色支持函数
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
    
    action_hint = f"\n角色动作：{action}" if action else ""
    context_hint = f"\n场景上下文：{context[:100]}..." if context else ""
    
    return [
        {"role": "system", "content": "你是小说作家，擅长将对话自然融入叙事"},
        {"role": "user", "content": f"""请将以下对话改写成自然的小说叙述：

角色：{speaker}
性格：{traits}
背景：{background}{action_hint}{context_hint}
原始对话："{dialogue}"

要求：
1. 将对话自然融入动作和情绪描写中
2. 如果有动作提示，巧妙地将其融入叙述
3. 保持对话核心内容不变
4. 输出流畅自然的小说段落

示例输出格式：
- "小红帽!"调查员皱起眉头，紧紧盯着小红帽,语气严肃地叮嘱道,"这枚密封舱里装着极其重要的医疗芯片,务必确保它安全准时送达指定医院,途中绝不能有任何闪失."
- 小红帽一边调整飞船航向，一边皱眉问道："导航助手，请确认前方的陨石带数据。"

请生成自然的小说段落："""},
    ]
# ------------------------------
# 对话润色主函数
# ------------------------------
def polish_dialogues_in_story(task_name="test", input_dialogue_file=None):
    base_dir = os.path.join(output_dir, task_name)
    
    # 读取所有需要的数据
    md_path = os.path.join(base_dir, "enhanced_story_updated.md")
    char_path = os.path.join(base_dir, "characters.json")
    dialogue_path = os.path.join(base_dir, "dialogue_updated.json")  # 句子级数据
    behavior_path = os.path.join(base_dir, "behavior_timeline_raw.json")
    
    # 加载数据
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    char_dict = load_character_info(char_path)
    sentence_dialogues = json.load(open(dialogue_path))
    behavior_timeline = json.load(open(behavior_path)) if os.path.exists(behavior_path) else []
    
    # 构建action查找表
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
                    key = f"{text}——{speaker}"  # 用于匹配原文
                    action_map[key] = {
                        "action": action,
                        "context": sentence["sentence"],
                        "chapter_id": chapter_id,
                        "sentence_index": sent_idx
                    }
    
    # 匹配并润色
    pattern = r'"([^"]{1,500}?)"\s*——\s*([^\n\r：：，,。！？]*)'
    
    def replace_dialogue(match):
        original_text = match.group(1)
        speaker = match.group(2)
        full_match = match.group(0)
        
        if speaker in char_dict:
            # 查找对应的action
            lookup_key = f"{original_text}——{speaker}"
            action_info = action_map.get(lookup_key, {})
            
            # 构建增强的prompt
            prompt = build_polish_prompt(
                speaker, 
                original_text, 
                char_dict[speaker],
                action_info.get("action", ""),
                action_info.get("context", "")
            )
            
            try:
                polished = generate_response(prompt).strip()
                print(f"✅ 润色成功：{speaker} 的对白")
                return polished
            except Exception as e:
                print(f"⚠️ 润色失败：{e}")
                return full_match
        
        return full_match
    
    # 使用正则表达式替换
    polished_content = re.sub(pattern, replace_dialogue, content)
    
    # 保存结果
    output_path = os.path.join(base_dir, "enhanced_story_dialogue_updated.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(polished_content)
    
    print(f"对白已润色完成：{output_path}")
