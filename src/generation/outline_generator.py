# 原来的 generate_linear_story_outline 函数

from src.utils import convert_json,generate_response


def generate_outline(topic="小红帽", style="科幻改写"):
    msg = [{
        "role": "user",
        "content": f"""
你是一个编剧，现在要创作一个名为《{topic}》的故事，请你为这个故事生成一个线性的大纲章节列表（不需要分支）。

请根据以下要求返回一个标准 JSON 格式的列表，每个元素表示一章，包括：
- chapter_id：章节编号（如 \"Chapter 1\"）
- title：章节标题
- summary：该章内容的简要介绍（1~2句话）

故事风格为：{style}

只返回标准 JSON 列表，不需要返回其他多余解释。
        """
    }]
    raw = generate_response(msg)
    return convert_json(raw)


if __name__ == "__main__":
    res = generate_outline()
    print(res)
