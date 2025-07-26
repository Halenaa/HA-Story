import os
import json
import argparse
from tqdm import tqdm
from src.utils.utils import load_json, generate_response, convert_json_safe as convert_json

def is_similar(a: str, b: str, model="claude-sonnet-4-20250514") -> bool:
    prompt = f"""
你是一个叙事结构专家，请判断以下两个内容是否表达相同的结构功能：

A: 「{a}」
B: 「{b}」

如果它们语义相近、承担相似的结构角色（如任务开始、反派先动手、主角陷入困境），请判断为 true。

请返回如下 JSON：
{{"is_paraphrase": true 或 false, "reason": "简要说明"}}
""".strip()

    response = generate_response([{"role": "user", "content": prompt}], model=model)
    try:
        result = convert_json(response)
        return result.get("is_paraphrase", False)
    except Exception as e:
        print(f"❌ 无法解析模型输出：{e}\n原始返回：{response[:80]}")
        return False

def load_anchor_list(path, field="surface"):
    data = load_json(path)
    if isinstance(data, dict) and "anchors" in data:
        return [{"value": s} for s in data["anchors"]]
    elif isinstance(data, list):
        if all("type" in d and "description" in d for d in data):
            return [{"value": d.get(field), "full": d} for d in data]
        elif all(isinstance(d, str) for d in data):
            return [{"value": d} for d in data]
        else:
            return [{"value": d.get(field)} for d in data]
    raise ValueError("不支持的 anchor 文件结构")

def match_items(ref_list, gen_list, field="surface", use_llm=False, model="claude-sonnet-4-20250514"):
    matched = []
    missed = []
    for ref in ref_list:
        found = False
        for gen in gen_list:
            if ref["value"] == gen["value"]:
                matched.append((ref["value"], gen["value"]))
                found = True
                break
            elif use_llm and is_similar(ref["value"], gen["value"], model=model):
                matched.append((ref["value"], gen["value"]))
                found = True
                break
        if not found:
            missed.append(ref["value"])
    extra = [g["value"] for g in gen_list if g["value"] not in [m[1] for m in matched]]
    return {
        "matched": matched,
        "missed": missed,
        "extra": extra,
        "hit_rate": round(len(matched) / len(ref_list), 3) if ref_list else 0
    }

def print_report(report):
    print("\n✅ 匹配结果报告")
    print(f"🎯 命中率: {report['hit_rate']*100:.1f}%")
    print("\n✔️ 匹配锚点：")
    for r, g in report["matched"]:
        mark = "≈" if r != g else "✓"
        print(f"  {mark} {r} ≈ {g}")
    print("\n❌ 未命中参考锚点：")
    for m in report["missed"]:
        print(f"  - {m}")
    print("\n⚠️ 多余生成锚点：")
    for e in report["extra"]:
        print(f"  - {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", required=True, help="参考锚点文件路径（支持 surface.json / functional.json）")
    parser.add_argument("--gen", required=True, help="生成锚点文件路径")
    parser.add_argument("--field", choices=["surface", "type", "description"], default="surface", help="使用哪个字段进行比对")
    parser.add_argument("--llm", action="store_true", help="是否使用 LLM 模糊匹配")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="LLM 模型名称")

    args = parser.parse_args()

    ref_list = load_anchor_list(args.ref, field=args.field)
    gen_list = load_anchor_list(args.gen, field=args.field)

    report = match_items(ref_list, gen_list, field=args.field, use_llm=args.llm, model=args.model)
    print_report(report)
