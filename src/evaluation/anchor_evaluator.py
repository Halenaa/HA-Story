import os
import json
import argparse
from tqdm import tqdm
from src.utils.utils import load_json, generate_response
from src.utils.utils import convert_json_safe as convert_json


# 👇 LLM 模型判断两锚点是否同义（支持 markdown 包裹）
def is_similar(a: str, b: str, threshold=0.85, model="claude-sonnet-4-20250514") -> bool:
    prompt = f"""
你是一个叙事结构专家，请判断以下两个锚点是否表达相同的结构功能：

A: 「{a}」
B: 「{b}」

如果它们语义相近、承担相似情节角色（如任务开始、危机爆发、反派出现），请判断为同义。

请返回如下格式（仅 JSON）：
{{"is_paraphrase": true 或 false, "reason": "简要说明"}}
    """.strip()

    response = generate_response([{"role": "user", "content": prompt}], model=model)

    try:
        result = convert_json(response)
        return result.get("is_paraphrase", False)
    except Exception as e:
        print(f"❌ 无法解析模型输出: {e}\n原始返回：{response[:80]}")
        return False

def flatten_dual_anchors(path, level="core"):
    data = load_json(path)
    anchors = []
    key = f"{level}_anchors"
    for ch in data:
        for a in ch.get(key, []):
            anchor = a.copy()
            anchor["chapter_id"] = ch["chapter_id"]
            anchors.append(anchor)
    return anchors

def load_reference(path):
    data = load_json(path)
    if isinstance(data, dict) and "anchors" in data:
        # 支持 { "anchors": ["任务1", "任务2", ...] }
        return [{"surface": s, "type": None} for s in data["anchors"]]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("不支持的参考锚点格式")

def match_surface(ref_surface, generated_surfaces, threshold=0.85):
    for g in generated_surfaces:
        if is_similar(ref_surface, g, threshold=threshold):
            return g
    return None

def match_functional(ref_type, generated_types):
    return ref_type in generated_types

def evaluate_anchors(generated_path, reference_path, use_surface=True, use_functional=True,
                     explain=False, generated_level=None):
    # 读取生成锚点
    if generated_level:
        generated = flatten_dual_anchors(generated_path, level=generated_level)
    else:
        generated = load_json(generated_path)

    # 读取参考锚点
    reference = load_reference(reference_path)

    results = []
    total = len(reference)
    surface_hits = 0
    type_hits = 0

    gen_surfaces = [a.get("surface", "") for a in generated]
    gen_types = [a.get("type", "") for a in generated]

    for ref in tqdm(reference, desc="🔍 匹配锚点"):
        match = {"ref": ref, "surface_match": False, "type_match": False, "matched_to": None}

        if use_surface and ref.get("surface"):
            matched_surface = match_surface(ref["surface"], gen_surfaces)
            if matched_surface:
                match["surface_match"] = True
                match["matched_to"] = matched_surface
                surface_hits += 1

        if use_functional and ref.get("type"):
            if match_functional(ref["type"], gen_types):
                match["type_match"] = True
                type_hits += 1

        if explain and not match["surface_match"]:
            prompt = f"参考锚点：{ref['surface']}\n未匹配生成锚点，请判断为何未命中？是否表达方式变化或结构遗漏？"
            match["llm_reason"] = generate_response([{"role": "user", "content": prompt}])

        results.append(match)

    print("\n✅ 锚点对齐统计结果：")
    if use_surface:
        print(f"🔹 Surface 命中数：{surface_hits} / {total}（命中率 {surface_hits / total:.2%}）")
    if use_functional:
        print(f"🔹 Functional 类型匹配：{type_hits} / {total}（命中率 {type_hits / total:.2%}）")

    return results

def save_result(results, output_path="anchor_eval_result.json"):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 匹配详情已保存至：{output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated", type=str, required=True, help="生成的 anchors 路径")
    parser.add_argument("--reference", type=str, required=True, help="参考 anchors 路径")
    parser.add_argument("--surface", action="store_true", help="是否启用 surface 匹配")
    parser.add_argument("--functional", action="store_true", help="是否启用 functional 类型匹配")
    parser.add_argument("--explain", action="store_true", help="是否启用 LLM 错误解释")
    parser.add_argument("--generated_level", choices=["core", "fine"], help="dual结构中提取的层级")
    parser.add_argument("--output", type=str, default="anchor_eval_result.json")

    args = parser.parse_args()
    results = evaluate_anchors(
        generated_path=args.generated,
        reference_path=args.reference,
        use_surface=args.surface,
        use_functional=args.functional,
        explain=args.explain,
        generated_level=args.generated_level
    )
    save_result(results, args.output)
