import json
from src.utils.utils import generate_response,convert_json

def expand_story_v1(chapters, characters, custom_instruction=None):
    import time
    character_json = json.dumps(characters, ensure_ascii=False, indent=2)
    story = []

    for ch in chapters:
        msg_content = f"""
根据以下内容，生成具体的场景、选择出场的人物名称和详细描述：
章节编号：{ch["chapter_id"]}
标题：{ch["title"]}
人物设定：{character_json}
"""
        if custom_instruction:
            msg_content += f"\n【特别要求】：{custom_instruction}"

        msg_content += """
#OUTPUT FORMAT:
{
    "scene": "故事发生的场景",
    "characters": ["人物名称1", "人物名称2"],
    "plot": "对于场景的细致刻画，以一段文字描述返回"
}
不要加入注释、解释或其他多余内容，只返回 JSON。请确保返回结果为合法 JSON（可以被 json.loads 正确解析），并不要在字符串中使用未闭合的双引号。
请注意：请严格返回一个 JSON 对象（即以 { 开头），不要返回 JSON 数组或句子列表结构。
"""

        msg = [{"role": "user", "content": msg_content}]
        response = generate_response(msg)

        print(f"📨 第 {ch['chapter_id']} 章 LLM 返回片段：", response[:150].replace("\n", "\\n"))

        result = convert_json(response)
        print(f"📨 原始 LLM 返回内容：\n{response}")
        
        # 如果不是字典或缺字段，就报错并中止
        if not isinstance(result, dict):
            print(f"❌ 第 {ch['chapter_id']} 章解析失败（不是 dict）")
            raise ValueError(f"第 {ch['chapter_id']} 章返回内容格式错误！")

        if "plot" not in result:
            print(f"❌ 第 {ch['chapter_id']} 章缺失 'plot' 字段")
            raise ValueError(f"第 {ch['chapter_id']} 章缺少 plot 字段，LLM 可能没按格式输出")

        story.append(result)

        # Optional: 防止触发速率限制
        time.sleep(1)

    return story
