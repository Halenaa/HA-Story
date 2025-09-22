import os
import csv
from src.evaluation.anchor_evaluator_dual import load_anchor_list, match_items

results = []

# === 小红帽 - surface ===
ref = load_anchor_list("data/anchors/reference_小红帽_surface.json", field="surface")
gen = load_anchor_list("data/output/exp_小红帽_科幻改写/anchor_output_surface.json", field="surface")
res_exact = match_items(ref, gen, field="surface", use_llm=False)
res_llm = match_items(ref, gen, field="surface", use_llm=True)
results.append({
    "story": "小红帽",
    "type": "surface",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 小红帽 - functional ===
ref = load_anchor_list("data/anchors/reference_小红帽_functional.json", field="type")
gen = load_anchor_list("data/output/exp_小红帽_科幻改写/anchor_output_functional.json", field="type")
res_exact = match_items(ref, gen, field="type", use_llm=False)
res_llm = match_items(ref, gen, field="type", use_llm=True)
results.append({
    "story": "小红帽",
    "type": "functional",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 青蛙王子 - surface ===
ref = load_anchor_list("data/anchors/reference_青蛙王子_surface.json", field="surface")
gen = load_anchor_list("data/output/exp_青蛙王子_ABO改写/anchor_output_surface.json", field="surface")
res_exact = match_items(ref, gen, field="surface", use_llm=False)
res_llm = match_items(ref, gen, field="surface", use_llm=True)
results.append({
    "story": "青蛙王子",
    "type": "surface",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 青蛙王子 - functional ===
ref = load_anchor_list("data/anchors/reference_青蛙王子_functional.json", field="type")
gen = load_anchor_list("data/output/exp_青蛙王子_ABO改写/anchor_output_functional.json", field="type")
res_exact = match_items(ref, gen, field="type", use_llm=False)
res_llm = match_items(ref, gen, field="type", use_llm=True)
results.append({
    "story": "青蛙王子",
    "type": "functional",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 灰姑娘 - surface ===
ref = load_anchor_list("data/anchors/reference_灰姑娘_surface.json", field="surface")
gen = load_anchor_list("data/output/exp_灰姑娘_现代改写/anchor_output_surface.json", field="surface")
res_exact = match_items(ref, gen, field="surface", use_llm=False)
res_llm = match_items(ref, gen, field="surface", use_llm=True)
results.append({
    "story": "灰姑娘",
    "type": "surface",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 灰姑娘 - functional ===
ref = load_anchor_list("data/anchors/reference_灰姑娘_functional.json", field="type")
gen = load_anchor_list("data/output/exp_灰姑娘_现代改写/anchor_output_functional.json", field="type")
res_exact = match_items(ref, gen, field="type", use_llm=False)
res_llm = match_items(ref, gen, field="type", use_llm=True)
results.append({
    "story": "灰姑娘",
    "type": "functional",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 白雪公主 - surface ===
ref = load_anchor_list("data/anchors/reference_白雪公主_surface.json", field="surface")
gen = load_anchor_list("data/output/exp_白雪公主_军事改写/anchor_output_surface.json", field="surface")
res_exact = match_items(ref, gen, field="surface", use_llm=False)
res_llm = match_items(ref, gen, field="surface", use_llm=True)
results.append({
    "story": "白雪公主",
    "type": "surface",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

# === 白雪公主 - functional ===
ref = load_anchor_list("data/anchors/reference_白雪公主_functional.json", field="type")
gen = load_anchor_list("data/output/exp_白雪公主_军事改写/anchor_output_functional.json", field="type")
res_exact = match_items(ref, gen, field="type", use_llm=False)
res_llm = match_items(ref, gen, field="type", use_llm=True)
results.append({
    "story": "白雪公主",
    "type": "functional",
    "hit_rate_exact": res_exact["hit_rate"],
    "hit_rate_llm": res_llm["hit_rate"],
})

with open('structure_match_summary_llm.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['story', 'type', 'hit_rate_exact', 'hit_rate_llm'])
    writer.writeheader()
    writer.writerows(results)
print('\n✅ 精确匹配 + LLM 模糊匹配结果已保存到 structure_match_summary_llm.csv')