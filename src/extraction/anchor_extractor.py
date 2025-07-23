import os
import re
import json
import argparse
from tqdm import tqdm
from src.utils.utils import generate_response, load_json, save_json_absolute

def extract_plot_list_from_json(story_json):
    return [c.get("plot", "") for c in story_json]

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

def llm_extract_anchors(text, mode="fine", model="gpt-4o"):
    if mode == "fine":
        prompt = f"""
你是一个叙事结构分析助手，请阅读以下文本，提取出其中的所有重要结构锚点。每条锚点需包含：

- "surface"：自然语言描述该锚点事件或行为（如：红帽子遇到狼）
- "type"：结构功能分类，如“任务引导”、“路径出发”、“反派先发制人”、“主角陷入危机”、“外力救援”、“真相揭示”、“反思成长”等

请以 JSON 列表格式返回，例如：
[
  {{
    "surface": "红帽子踏上旅程",
    "type": "路径出发"
  }},
  ...
]

请处理以下文本：
{text}
"""
    elif mode == "coarse":
        prompt = f"""
你是一个叙事结构总结者，请从以下文本中识别最多 **2 个**“关键剧情节点”，这些节点代表了本章最重要的情节转折、冲突、结盟或揭示。

每个节点需包含：
- "surface"：自然语言描述该事件（如：红帽子被狼欺骗）
- "type"：结构功能分类（如“任务引导”、“反派先发制人”、“真相揭示”、“危机转折”等）

请以 JSON 列表返回：
[
  {{
    "surface": "...",
    "type": "..."
  }}
]

请处理以下文本：
{text}
"""
    else:
        raise ValueError("mode 必须为 fine 或 coarse")

    resp = generate_response([{"role": "user", "content": prompt}], model=model)
    try:
        if "```json" in resp:
            resp = resp.split("```json")[1].split("```")[0].strip()
        elif "```" in resp:
            resp = resp.split("```")[1].strip()
        return json.loads(resp)
    except:
        print("⚠️ 无法解析 LLM 返回格式，内容如下：\n", resp[:300])
        return []

def extract_anchors(input_path, output_filename, model="gpt-4o", mode="both"):
    print(f"\n🔍 正在提取锚点：{input_path}")
    if input_path.endswith(".json"):
        story = load_json(input_path)
        contents = extract_plot_list_from_json(story)
        chapter_ids = [f"Chapter {i+1}" for i in range(len(contents))]
    elif input_path.endswith(".md"):
        chapters = extract_chapter_texts_from_md(input_path)
        chapter_ids = [c["chapter_id"] for c in chapters]
        contents = [c["content"] for c in chapters]
    else:
        raise ValueError("只支持 .json 或 .md 文件输入")

    result = []
    print()
    for chapter_id, text in tqdm(list(zip(chapter_ids, contents)), desc="🔎 提取每章锚点"):
        if mode == "fine":
            fine = llm_extract_anchors(text, mode="fine", model=model)
            for a in fine:
                a["chapter_id"] = chapter_id
                result.append(a)
        elif mode == "coarse":
            coarse = llm_extract_anchors(text, mode="coarse", model=model)
            for a in coarse:
                a["chapter_id"] = chapter_id
                result.append(a)
        elif mode == "both":
            coarse = llm_extract_anchors(text, mode="coarse", model=model)
            fine = llm_extract_anchors(text, mode="fine", model=model)
            result.append({
                "chapter_id": chapter_id,
                "core_anchors": coarse,
                "fine_anchors": fine
            })
        else:
            raise ValueError("mode 必须是 fine / coarse / both")

    save_json_absolute(result, output_filename)
    print(f"\n✅ 提取完成，共生成 {len(result)} 条章节记录，结果已保存至：{output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="输入文件路径：story.json 或 enhanced_story_dialogue.md")
    parser.add_argument("--output", type=str, default="generated_anchors.json", help="输出 JSON 文件路径")
    parser.add_argument("--model", type=str, default="gpt-4o", help="使用的模型名称")
    parser.add_argument("--mode", type=str, default="both", choices=["fine", "coarse", "both"], help="提取粒度：fine（细致）/ coarse（关键）/ both（双层）")

    args = parser.parse_args()
    extract_anchors(args.input, args.output, model=args.model, mode=args.mode)
