import json

from src.utils import generate_response,convert_json


def generate_characters_v1(outline, max_characters=20):
    chapter_json = json.dumps(outline, ensure_ascii=False, indent=2)
    msg = [{
        "role": "user",
        "content": f"""
你是一位擅长人物设定的故事设计师。

以下是一个故事的章节大纲：

{chapter_json}

请你根据这些章节信息，分析故事中可能出现的重要角色，并生成一个统一的“角色设定列表”。

每个角色包含：name, role, traits, background, motivation
角色不超过 {max_characters} 个。

#OUTPUT FORMAT:
[
    {{
    "name":"",
    "role":"",
    "traits":"",
    "background":"",
    "motivation":"",
    }},
    ...
]

#最后以json结构返回，不需要其他多余的解释
        """
    }]
    response = generate_response(msg)
    return convert_json(response)