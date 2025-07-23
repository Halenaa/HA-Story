import os
import re
import json
from src.utils.utils import generate_response
from src.constant import output_dir

# 拆分 markdown 文件为章节
def split_novel_by_chapter(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 “# Chapter X：标题” 并拆分章节
    # chapters = re.split(r'# Chapter\s*\d+[:：]', content)[1:]
    # titles = re.findall(r'# Chapter\s*\d+[:：](.*)', content)
    # 支持 “# 第1章：标题” 或 “# Chapter 1: 标题”
# 支持 "# 第 1 章：标题"
    chapters = re.split(r'#\s*第\s*\d+\s*章[:：]', content)[1:]
    titles = re.findall(r'#\s*第\s*\d+\s*章[:：](.*)', content)


    return [
        {"title": titles[i].strip(), "content": chap.strip()}
        for i, chap in enumerate(chapters)
    ]

# 调用 LLM 生成章节间的过渡句
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

# 生成收尾句
def generate_ending(last_title, last_content):
    messages = [
        {"role": "system", "content": "你是小说作者"},
        {"role": "user", "content": f"""这是小说的最后一章，标题为“{last_title}”。内容如下：

{last_content.strip()}

请写一段具有结束感的结尾句子，用来收束全文，让读者感受到故事圆满结束。不要加引号，不要解释。
"""}
    ]
    return generate_response(messages).strip()

# 主函数：拼接增强版故事
def enhance_story_with_transitions(task_name="test", input_story_file=None):
    base_dir = os.path.join(output_dir, task_name)
    outline_path = os.path.join(base_dir, "test_outline.json")

    # ✅ 新增逻辑：使用 story_updated.json 提供正文
    if input_story_file:
        # 使用更新后的 story.json（含 plot 字段）
        story_path = os.path.join(base_dir, input_story_file)
        with open(story_path, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        chapters = [{"title": ch["title"], "content": ch["plot"]} for ch in story_data]
        suffix = "_updated"
    else:
        # 默认方式：从 novel_story.md 拆章节
        md_path = os.path.join(base_dir, "novel_story.md")
        chapters = split_novel_by_chapter(md_path)
        suffix = ""

    # 读取章节概要
    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    # 拼接正文 + 过渡句
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

    # 添加最终结尾
    ending = generate_ending(outline[-1]["title"], chapters[-1]["content"])
    enhanced_text += f"{ending}\n"

    # 保存为 enhanced_story[_updated].md
    output_path = os.path.join(base_dir, f"enhanced_story{suffix}.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_text)

    print(f"增强版故事已生成：{output_path}")

# 从角色列表中构建角色字典（名字 -> 信息）
def load_character_info(character_path):
    with open(character_path, "r", encoding="utf-8") as f:
        characters = json.load(f)
    return {char["name"]: char for char in characters}

# 尝试从一句话中找出说话人名字
def guess_speaker(text, character_names):
    for name in character_names:
        if name in text:
            return name
    return None

# 构造润色提示
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

# 主函数：润色对话
def polish_dialogues_in_story(task_name="test", input_dialogue_file=None):
    base_dir = os.path.join(output_dir, task_name)
    md_path = os.path.join(base_dir, "enhanced_story.md")
    char_path = os.path.join(base_dir, "characters.json")

    # 新增：判断是否传入更新后对话文件
    if input_dialogue_file:
        dialogue_path = os.path.join(base_dir, input_dialogue_file)
        dialogue_data = json.load(open(dialogue_path, "r", encoding="utf-8"))
        paragraphs = []
        for d in dialogue_data:
            for line in d.get("dialogue", []):
                if isinstance(line, dict) and "speaker" in line and "line" in line:
                    paragraphs.append(f"{line['speaker']}：“{line['line']}”")
                elif isinstance(line, str):
                    paragraphs.append(line)
                else:
                    print(f"⚠️ 无法解析的对白格式：{line}")

                # paragraphs.append(f"{line['speaker']}：“{line['line']}”")
        content = "\n\n".join(paragraphs)
    else:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

    char_dict = load_character_info(char_path)
    character_names = list(char_dict.keys())

    pattern = r"“([^”]{1,100}?)”([^。\n]*)?"
    matches = re.findall(pattern, content)

    replacements = []

    for match in matches:
        original_line, suffix = match
        full_text = f"“{original_line}”{suffix}"

        speaker = guess_speaker(full_text, character_names)
        if speaker and speaker in char_dict:
            prompt = build_polish_prompt(speaker, original_line, char_dict[speaker])
            polished = generate_response(prompt).strip()
            replacements.append((full_text, polished))

    for old, new in replacements:
        content = content.replace(old, new)

    suffix = "_updated" if input_dialogue_file else ""
    output_path = os.path.join(base_dir, f"enhanced_story_dialogue{suffix}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"对白已润色完成：{output_path}")

if __name__ == "__main__":
    enhance_story_with_transitions()
    polish_dialogues_in_story()




# # 默认生成版
# enhance_story_with_transitions(task_name="test")
# polish_dialogues_in_story(task_name="test")

# # 更新后联动版
# enhance_story_with_transitions(task_name="test", input_story_file="story_updated.json")
# polish_dialogues_in_story(task_name="test", input_dialogue_file="dialogue_updated.json")
