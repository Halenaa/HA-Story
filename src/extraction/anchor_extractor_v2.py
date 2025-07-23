import os
import re
import json
import argparse
from tqdm import tqdm
from src.utils.utils import generate_response, load_json, save_json_absolute


def extract_chapter_texts_from_md(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"# Chapter \d+[:：][^\n]*"
    matches = list(re.finditer(pattern, content))
    chapters = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        title_line = content[start:matches[i].end()].strip()
        body = content[matches[i].end():end].strip()
        chapters.append({"chapter_id": title_line, "content": body})
    return chapters


def llm_extract_dual_anchor_outputs(text, model="gpt-4o"):
    prompt = f"""
你是一个叙事结构提取专家，请从以下文本中提取两类信息：

1. functional anchors（结构功能锚点）：请选出最能代表本段结构功能的一组锚点，每个锚点包括：
  - anchor_id: 自动编号，如 A1, A2...
  - type: 功能类别名称（如“任务引导”、“反派先发制人”...）
  - description: 对该功能类别的抽象解释

2. surface anchors（故事具体锚点）：仅列出该段落中的关键自然语言事件描述（如“艾琳娜准备踏入森林”）即可。

请用以下 JSON 格式返回：
{{
  "functional": [{{"anchor_id": "A1", "type": "任务引导", "description": "主角接收到一个目标导向性的任务"}}],
  "surface": ["...", "..."]
}}

请尽量按照以下风格提取:
[
  {{
    "anchor_id": "A1",
    "type": "任务引导",
    "description": "母亲让小红帽给外婆送食物"
  }},
  {{
    "anchor_id": "A2",
    "type": "路径出发",
    "description": "小红帽穿越森林前往外婆家"
  }},
  
  ...
]

以下是文本：
{text}
"""

    response = generate_response([{"role": "user", "content": prompt}], model=model)
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].strip()
        return json.loads(response)
    except Exception as e:
        print("⚠️ 无法解析 LLM 返回格式：", e)
        return {"functional": [], "surface": []}


def extract_anchors(input_path, output_path, model="gpt-4o"):
    print(f"\n🔍 正在提取锚点：{input_path}")
    if input_path.endswith(".json"):
        story = load_json(input_path)
        contents = [c.get("plot", "") for c in story]
        chapter_ids = [f"Chapter {i+1}" for i in range(len(contents))]
    elif input_path.endswith(".md"):
        chapters = extract_chapter_texts_from_md(input_path)
        chapter_ids = [c["chapter_id"] for c in chapters]
        contents = [c["content"] for c in chapters]
    else:
        raise ValueError("只支持 .json 或 .md 文件输入")

    functional_anchors = []
    surface_anchors = []

    print()
    for chapter_id, text in tqdm(list(zip(chapter_ids, contents)), desc="🔎 提取每章锚点"):
        out = llm_extract_dual_anchor_outputs(text, model=model)
        for f in out.get("functional", []):
            f["chapter_id"] = chapter_id
            functional_anchors.append(f)
        for s in out.get("surface", []):
            surface_anchors.append({"chapter_id": chapter_id, "surface": s})

    base = os.path.splitext(output_path)[0]
    save_json_absolute(functional_anchors, base + "_functional.json")
    save_json_absolute({"anchors": [s["surface"] for s in surface_anchors]}, base + "_surface.json")

    print(f"\n✅ 提取完成，共生成 {len(functional_anchors)} 条功能锚点、{len(surface_anchors)} 条故事锚点")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="输入文件路径：.json 或 .md")
    parser.add_argument("--output", type=str, default="generated_anchors_dual.json", help="输出 JSON 文件路径前缀")
    parser.add_argument("--model", type=str, default="gpt-4o", help="使用的 LLM 模型名称")

    args = parser.parse_args()
    extract_anchors(args.input, args.output, model=args.model)