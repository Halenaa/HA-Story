import json

from src.utils.utils import generate_response,convert_json


def generate_characters_v1(outline, max_characters=20, performance_analyzer=None):
    chapter_json = json.dumps(outline, ensure_ascii=False, indent=2)
    msg = [{
        "role": "user",
        "content": f"""
You are a story designer skilled in character creation.

Below is the chapter outline of a story:

{chapter_json}

Please analyze the important characters that may appear in the story based on this chapter information, and generate a unified "character setting list".

Each character includes: name, role, traits, background, motivation
No more than {max_characters} characters.

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

#Finally return in json structure, no other redundant explanations needed
        """
    }]
    response = generate_response(msg, performance_analyzer=performance_analyzer, stage_name="character_generation")
    return convert_json(response)