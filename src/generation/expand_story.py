import json
from src.utils.utils import generate_response,convert_json

def expand_story_v1(chapters, characters, custom_instruction=None):
    character_json = json.dumps(characters, ensure_ascii=False, indent=2)
    story = []
    for ch in chapters:
        msg_content = f"""
根据以下内容，生成具体的场景、选择出场的人物名称和详细描述：
章节编号：{ch["chapter_id"]}
标题：{ch["title"]}
人物设定：{character_json}
"""

        # ✅ 插入用户定制指令
        if custom_instruction:
            msg_content += f"\n【特别要求】：{custom_instruction}"

        msg_content += """
#OUTPUT FORMAT:
{
    "scene":"故事发生的场景",
    "characters": ["人物名称1","人物名称2",...],
    "plot":"对于场景的细致刻画，以一段文字描述返回"
}
"""

        msg = [{"role": "user", "content": msg_content}]
        response = generate_response(msg)
        print("chapters", response)
        story.append(convert_json(response))
    return story

