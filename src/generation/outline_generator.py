from src.utils.utils import convert_json, generate_response

def generate_outline(topic="小红帽", style="科幻改写", custom_instruction=None):
    # 构造基本 prompt 内容
    base_prompt = f"""
你是一个编剧，现在要创作一个名为《{topic}》的故事，请你为这个故事生成一个线性的大纲章节列表（不需要分支）。

请根据以下要求返回一个标准 JSON 格式的列表，每个元素表示一章，包括：
- chapter_id：章节编号（如 "Chapter 1"）
- title：章节标题
- summary：该章内容的简要介绍（1~2句话）

故事风格为：{style}
不要加入冒号、解释或其他多余格式，只返回 JSON 格式的内容。
"""

    # 如果用户提供了自定义指令，就加入进来
    if custom_instruction:
        base_prompt = f"\n请特别注意以下风格或内容提示：{custom_instruction}"

    base_prompt += "\n只返回标准 JSON 列表，不需要返回其他多余解释。"

    msg = [{"role": "user", "content": base_prompt}]
    raw = generate_response(msg)
    print(raw)
    return convert_json(raw)
