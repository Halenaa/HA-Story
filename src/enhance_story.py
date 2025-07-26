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
        {"role": "user", "content": f"""这是小说的最后一章，标题为“{last_title}”。内容如下：

{last_content.strip()}

请写一段具有结束感的结尾句子，用来收束全文，让读者感受到故事圆满结束。不要加引号，不要解释。
"""}
    ]
    return generate_response(messages).strip()

# ------------------------------
# 主函数：剧情+对话拼接 + 章节过渡生成
# ------------------------------
def enhance_story_with_transitions(task_name="test", input_story_file=None):
    base_dir = os.path.join(output_dir, task_name)
    # outline_path = os.path.join(base_dir, "test_outline.json")
    reorder_path = os.path.join(base_dir, "test_reorder_outline.json")
    outline_path = reorder_path if os.path.exists(reorder_path) else os.path.join(base_dir, "test_outline.json")

    if input_story_file:
        story_path = os.path.join(base_dir, input_story_file)
        with open(story_path, 'r', encoding='utf-8') as f:
            story_data = json.load(f)

        dialogue_path = os.path.join(base_dir, "dialogue_updated.json")
        with open(dialogue_path, 'r', encoding='utf-8') as f:
            dialogue_data = json.load(f)

        chapters = []
        seen_lines = set()
        
        print(f"共加载章节数：{len(story_data)}，对白数：{len(dialogue_data)}")

        for ch, dlg in zip(story_data, dialogue_data):
            content = ch["plot"].strip()

            # ⚠️ 无论是否有 dialogue，都保底构造 content，防止后面 chapters 为空
            if dlg.get("dialogue"):
                for line in dlg["dialogue"]:
                    if isinstance(line, dict):
                        quoted = f'"{line["line"]}" ——{line["speaker"]}'
                        if quoted not in seen_lines:
                            content += f'\n\n{quoted}'
                            seen_lines.add(quoted)
                    elif isinstance(line, str):
                        if line not in seen_lines:
                            content += f'\n\n{line}'
                            seen_lines.add(line)

            # ✅ 每一章都 append，防止 chapters 为空
            chapters.append({
                "title": ch["title"],
                "content": content
            })
        suffix = "_updated"
    else:
        md_path = os.path.join(base_dir, "novel_story.md")
        chapters = split_novel_by_chapter(md_path)
        suffix = ""
    
    print(f"最终生成的章节数（含对白）：{len(chapters)}")
    
    # ✅ 添加保护性检查
    if not chapters:
        print("⚠️ 错误：没有章节数据，跳过增强处理")
        # 创建一个空文件，避免后续流程出错
        output_path = os.path.join(base_dir, f"enhanced_story{suffix}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 故事生成失败\n\n没有成功生成章节内容。")
        return

    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)
    
    # ✅ 检查outline和chapters长度是否匹配
    if len(outline) != len(chapters):
        print(f"⚠️ 警告：outline有{len(outline)}章，但chapters只有{len(chapters)}章")
        # 只处理有效的章节
        min_len = min(len(outline), len(chapters))
        outline = outline[:min_len]
        chapters = chapters[:min_len]
    
    # ✅ 如果处理后仍然没有章节，退出
    if not chapters:
        print("⚠️ 错误：处理后没有有效章节，跳过增强处理")
        output_path = os.path.join(base_dir, f"enhanced_story{suffix}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 故事生成失败\n\n没有成功生成章节内容。")
        return

    enhanced_text = ""
    for i, chap in enumerate(chapters):
        title = outline[i]["title"]
        summary = outline[i]["summary"]
        chapter_id = outline[i]["chapter_id"]

        enhanced_text += f"# {chapter_id}：{title}\n\n"
        enhanced_text += chap["content"].strip() + "\n\n"

        if i < len(chapters) - 1:
            next_title = outline[i + 1]["title"]
            transition = generate_transition(title, next_title, summary, chap["content"])
            enhanced_text += f"{transition}\n\n"

    # ✅ 保护性检查：确保有内容和outline才生成结尾
    if chapters and outline:
        ending = generate_ending(outline[-1]["title"], chapters[-1]["content"])
        enhanced_text += f"{ending}\n"

    output_path = os.path.join(base_dir, f"enhanced_story{suffix}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_text)

    print(f"增强版故事已生成：{output_path}")
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

def build_polish_prompt(speaker, original_dialogue, character_info):
    traits = character_info.get("traits", "")
    background = character_info.get("background", "")
    motivation = character_info.get("motivation", "")
    return [
        {"role": "system", "content": "你是一个小说润色专家，擅长将对白自然嵌入小说情节中"},
        {"role": "user", "content": f"""请将以下对白润色为小说风格，增加角色动作、神态、情绪、语气变化，使对白自然融入场景中。

角色：{speaker}
性格：{traits}
背景：{background}
动机：{motivation}

对白原文：
“{original_dialogue}”

请生成润色后的自然小说段落。不加引号，不要解释。"""},
    ]

# ------------------------------
# 对话润色主函数
# ------------------------------
def polish_dialogues_in_story(task_name="test", input_dialogue_file=None):
    base_dir = os.path.join(output_dir, task_name)
    md_path = os.path.join(base_dir, "enhanced_story_updated.md")  # ✅ 指定新版完整内容
    char_path = os.path.join(base_dir, "characters.json")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    char_dict = load_character_info(char_path)
    character_names = list(char_dict.keys())

    # ✅ 匹配 “对白” ——角色名 的格式
    pattern = r'“([^”]{1,100}?)”\s*——\s*([^\n\r：：，,。！？]*)'
    matches = re.findall(pattern, content)

    replacements = []
    for original_line, speaker in matches:
        if speaker in char_dict:
            prompt = build_polish_prompt(speaker, original_line, char_dict[speaker])
            try:
                polished = generate_response(prompt).strip()
                full_original = f'“{original_line}” ——{speaker}'
                replacements.append((full_original, polished))
            except Exception as e:
                print(f"⚠️ 润色失败：{original_line} by {speaker}：{e}")

    for old, new in replacements:
        content = content.replace(old, new)

    output_path = os.path.join(base_dir, "enhanced_story_dialogue_updated.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"对白已润色完成：{output_path}")
