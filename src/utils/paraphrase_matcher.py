# paraphrase_matcher.py

import json
import argparse
import os
from src.utils.utils import generate_response


def is_paraphrase_llm(a: str, b: str, model: str = "gpt-4o", verbose: bool = False) -> bool:
    prompt = f"""
你是一个叙事结构专家，请判断以下两个锚点是否表达相同的结构功能：

A: 「{a}」
B: 「{b}」

如果它们语义相近、承担相似情节角色（如任务开始、危机爆发、反派出现），请判断为同义。

请返回如下格式（仅 JSON）：
{{"is_paraphrase": true 或 false, "reason": "简要说明"}}
    """.strip()

    messages = [{"role": "user", "content": prompt}]
    raw = generate_response(messages, model=model)

    try:
        result = eval(raw.strip())
        if verbose:
            print(f"\nA: {a}\n🔍 B: {b}")
            print(f"同义: {result['is_paraphrase']}\n🧠 理由: {result['reason']}")
        return result["is_paraphrase"]
    except Exception as e:
        print(f"无法解析模型输出: {e}\n原始返回：{raw[:80]}")
        return False


def match_lists(ref_list, gen_list, model="gpt-4o", verbose=True):
    matched = []
    missed = []
    for ref in ref_list:
        found = False
        for gen in gen_list:
            if ref == gen:
                matched.append((ref, gen))
                found = True
                break
            elif is_paraphrase_llm(ref, gen, model=model, verbose=verbose):
                matched.append((ref, gen))
                found = True
                break
        if not found:
            missed.append(ref)

    extra = [g for g in gen_list if all(g != m[1] for m in matched)]

    return {
        "matched": matched,
        "missed": missed,
        "extra": extra,
        "hit_rate": round(len(matched) / len(ref_list), 3) if ref_list else 0
    }


def print_report(report):
    print("\n命中锚点：")
    for r, g in report["matched"]:
        mark = "≈" if r != g else "✓"
        print(f" - {mark} {r} ≈ {g}")

    print("\n未命中参考锚点：")
    for m in report["missed"]:
        print(f" - {m}")

    print("\n多余生成锚点：")
    for e in report["extra"]:
        print(f" - {e}")

    print(f"\n命中率: {report['hit_rate']*100:.1f}% "
          f"(匹配 {len(report['matched'])} / {len(report['matched']) + len(report['missed'])})")


def load_anchor_list(path):
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if "anchors" in data:
            return [a["description"] if isinstance(a, dict) else a for a in data["anchors"]]
        else:
            anchors = []
            for ch in data.values():
                anchors.extend(ch if isinstance(ch, list) else [ch])
            return anchors
    raise ValueError("Unsupported anchor file format")


def extract_story_plot_list(story_json_path):
    story = json.load(open(story_json_path, encoding="utf-8"))
    return [item["plot"] for item in story if "plot" in item]


def extract_md_sentences(md_path, min_len=15):
    result = []
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and len(line) >= min_len:
                result.append(line)
    return result


def auto_detect_file_format(path):
    if path.endswith(".md"):
        return "md"
    elif path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return "json_list"
            elif "plot" in str(data).lower():
                return "story"
            elif "anchors" in data or isinstance(list(data.values())[0], list):
                return "anchors"
    raise ValueError(f"未知格式：{path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True, help="参考锚点文件路径（支持 anchors json）")
    parser.add_argument("--gen", required=True, help="生成锚点来源（.json/.md/story.json）")
    parser.add_argument("--model", default="gpt-4o", help="调用的模型")
    parser.add_argument("--verbose", action="store_true", help="是否打印详细匹配过程")

    args = parser.parse_args()

    ref_list = load_anchor_list(args.ref)

    # 根据输入格式选择提取方式
    gen_format = auto_detect_file_format(args.gen)
    if gen_format == "md":
        gen_list = extract_md_sentences(args.gen)
    elif gen_format == "json_list":
        gen_list = load_anchor_list(args.gen)
    elif gen_format == "story":
        gen_list = extract_story_plot_list(args.gen)
    else:
        raise ValueError("不支持的生成格式")

    report = match_lists(ref_list, gen_list, model=args.model, verbose=args.verbose)
    print_report(report)

# alias 统一接口供 evaluator 使用
def is_similar(a: str, b: str, threshold=0.85):
    return is_paraphrase_llm(a, b, model="gpt-4o")
