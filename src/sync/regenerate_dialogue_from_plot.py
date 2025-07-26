from src.utils.utils import generate_response, convert_json_safe

def regenerate_dialogue_from_plot(chapter_id, plot, character_info, style_hint=None, model="gpt-4.1"):
    """
    根据 plot 与角色设定，生成角色之间的自然对话。
    返回：List[Dict]
    """
    role_profiles = "\n".join([
        f"{char['name']}（性格：{char['traits']}，动机：{char['motivation']}）"
        for char in character_info
    ])

    style_instruction = f"\n风格提示：{style_hint}" if style_hint else ""

    prompt = f"""
你是一位优秀的小说剧本编剧。

请你根据以下 plot，为其对应的角色生成一段“推动情节、反映性格”的自然对话：
- 使用 json 数组形式输出
- 包含所有角色轮流发言
- 每个角色发言 1~2 句，注意语言风格体现性格
- 无需重述 plot，仅写对话

【章节编号】：{chapter_id}

【剧情概要】：
{plot}

【角色设定】：
{role_profiles}
{style_instruction}

【输出格式】（严格为 json）：
[
  {{"speaker": "角色名", "line": "台词内容"}},
  ...
]
""".strip()

    response = generate_response([{"role": "user", "content": prompt}], model=model)
    return convert_json_safe(response)
