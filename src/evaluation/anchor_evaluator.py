
import os
import re
import json
import argparse
import numpy as np
from tqdm import tqdm
from src.utils.utils import generate_response, load_json, save_json_absolute

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    COHERENCE_AVAILABLE = True
except ImportError:
    COHERENCE_AVAILABLE = False
    print("⚠️  未安装 sentence-transformers，将跳过连贯性分析")


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


def llm_extract_events(text, model="gpt-4.1"):
    """步骤1：提取关键事件"""
    prompt = f"""
请从以下故事中提取所有关键事件。要求：
1. 每个事件用一句话描述（10-20字）
2. 只提取推动情节发展的事件，忽略纯描述
3. 按时间顺序排列
4. 输出格式：["事件1", "事件2", "事件3", ...]

故事文本：
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
        print(f"⚠️ 事件提取失败：{e}")
        return []


def llm_papalampidi_annotate(events, model="gpt-4.1"):
    """步骤2A：Papalampidi标注"""
    events_str = json.dumps(events, ensure_ascii=False, indent=2)
    
    prompt = f"""
给定事件列表，请标注5个关键转折点(TP)和6个阶段：

事件列表：{events_str}

转折点定义：
- TP1 (Opportunity): 引入主要情节的关键事件
- TP2 (Change of Plans): 目标/计划发生改变的时刻  
- TP3 (Point of No Return): 角色全力投入、无法后退的承诺点
- TP4 (Major Setback): 最大危机/挫折时刻
- TP5 (Climax): 主要冲突的最终解决时刻

阶段定义：
- Setup: 背景设定和角色介绍
- New Situation: 新环境/新挑战的建立
- Progress: 朝目标前进的过程
- Complications: 冲突和困难的升级
- Final Push: 最终的决定性行动
- Aftermath: 结果和长期影响

输出格式：
{{
  "转折点": {{
    "TP1": "事件X",
    "TP2": "事件Y", 
    "TP3": "事件Z",
    "TP4": "事件A",
    "TP5": "事件B"
  }},
  "阶段划分": {{
    "Setup": ["事件1", "事件2"],
    "New Situation": ["事件3"],
    "Progress": ["事件4", "事件5"],
    "Complications": ["事件6", "事件7", "事件8"],
    "Final Push": ["事件9"],
    "Aftermath": ["事件10"]
  }}
}}
"""
    
    response = generate_response([{"role": "user", "content": prompt}], model=model)
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].strip()
        return json.loads(response)
    except Exception as e:
        print(f"⚠️ Papalampidi标注失败：{e}")
        return {"转折点": {}, "阶段划分": {}}


def llm_li_annotate(events, model="gpt-4.1"):
    """步骤2B：Li标注"""
    events_str = json.dumps(events, ensure_ascii=False, indent=2)
    
    prompt = f"""
给定事件列表，请用10个功能标签标注每个事件：

事件列表：{events_str}

功能标签定义：
- Abstract: 故事要点的总结
- Orientation: 背景设定（时间、地点、人物）
- Complicating Action: 增加张力、推动情节的事件
- MRE (Most Reportable Event): 最重要/最值得报告的事件
- Minor Resolution: 部分缓解张力的事件
- Return of MRE: MRE主题的重新出现
- Resolution: 解决主要冲突的事件  
- Aftermath: 主要事件后的长期影响
- Evaluation: 叙述者对故事意义的评论
- Direct Comment: 对观众的直接评论

输出格式：
{{
  "事件1": "Orientation",
  "事件2": "Complicating Action",
  "事件3": "MRE",
  ...
}}
"""
    
    response = generate_response([{"role": "user", "content": prompt}], model=model)
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].strip()
        return json.loads(response)
    except Exception as e:
        print(f"⚠️ Li标注失败：{e}")
        return {}


def score_papalampidi(result):
    """Papalampidi评分（10分制）"""
    score = 0
    
    # TP清晰度 (5分)
    tp_count = len([tp for tp in result.get("转折点", {}).values() if tp and tp.strip()])
    score += tp_count  # 每个清晰TP得1分
    
    # 阶段完整性 (5分) 
    stages = result.get("阶段划分", {})
    stage_count = len([stage for stage in stages.values() if stage and len(stage) > 0])
    score += min(stage_count, 5)  # 最多5分
    
    return min(score, 10)


def score_li(result):
    """Li评分（10分制）"""
    score = 0
    labels = list(result.values())
    
    # 核心功能检查 (6分)
    core_functions = ["Orientation", "Complicating Action", "MRE", "Resolution"]
    for func in core_functions:
        if func in labels:
            score += 1.5  # 每个核心功能1.5分
    
    # 功能多样性 (4分)
    unique_labels = len(set(labels))
    score += min(unique_labels * 0.4, 4)  # 标签种类越多分越高
    
    return min(score, 10)


def calculate_coherence(events):
    """计算连贯性分数"""
    if not COHERENCE_AVAILABLE or len(events) < 2:
        return {"平均连贯性": 0, "连贯性等级": "无法计算"}
    
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        event_embeddings = model.encode(events)
        
        coherence_scores = []
        for i in range(len(event_embeddings) - 1):
            similarity = cosine_similarity([event_embeddings[i]], [event_embeddings[i+1]])[0][0]
            coherence_scores.append(similarity)
        
        avg_coherence = np.mean(coherence_scores)
        min_coherence = np.min(coherence_scores)
        worst_gap = np.argmin(coherence_scores)
        
        if avg_coherence >= 0.7:
            level = "优秀"
        elif avg_coherence >= 0.5:
            level = "良好" 
        elif avg_coherence >= 0.3:
            level = "及格"
        else:
            level = "需改进"
        
        return {
            "平均连贯性": round(avg_coherence, 3),
            "最低连贯性": round(min_coherence, 3),
            "最大跳跃位置": worst_gap,
            "连贯性等级": level,
            "详细分数": [round(s, 3) for s in coherence_scores]
        }
    except Exception as e:
        print(f"⚠️ 连贯性计算失败：{e}")
        return {"平均连贯性": 0, "连贯性等级": "计算失败"}


def evaluate_story_dual_track(input_path, output_path, model="gpt-4.1"):
    """主函数：双轨并行故事评价"""
    print(f"\n🔍 开始双轨评价：{input_path}")
    
    # 读取输入文件
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

    # 合并所有章节文本
    full_text = "\n\n".join([f"{cid}: {content}" for cid, content in zip(chapter_ids, contents)])
    
    print("\n📋 步骤1：提取关键事件...")
    events = llm_extract_events(full_text, model=model)
    
    print(f"✅ 提取到 {len(events)} 个事件")
    
    print("\n📊 步骤2A：Papalampidi结构分析...")
    papalampidi_result = llm_papalampidi_annotate(events, model=model)
    papalampidi_score = score_papalampidi(papalampidi_result)
    
    print("\n🏷️  步骤2B：Li功能分析...")
    li_result = llm_li_annotate(events, model=model)
    li_score = score_li(li_result)
    
    print("\n🔗 步骤3：连贯性分析...")
    coherence_result = calculate_coherence(events)
    
    # 汇总结果
    evaluation_result = {
        "基本信息": {
            "文件路径": input_path,
            "章节数量": len(contents),
            "事件数量": len(events)
        },
        "事件列表": events,
        "Papalampidi评价": {
            "得分": f"{papalampidi_score}/10",
            "详细结果": papalampidi_result
        },
        "Li评价": {
            "得分": f"{li_score}/10", 
            "详细结果": li_result
        },
        "连贯性评价": coherence_result,
        "综合诊断": {
            "结构质量": "优秀" if papalampidi_score >= 8 else "良好" if papalampidi_score >= 6 else "需改进",
            "功能质量": "优秀" if li_score >= 8 else "良好" if li_score >= 6 else "需改进",
            "连贯性质量": coherence_result.get("连贯性等级", "无法计算")
        }
    }
    
    # 保存结果
    save_json_absolute(evaluation_result, output_path)
    
    # 打印摘要
    print(f"""
📊 评价完成！结果摘要：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 结构质量 (Papalampidi): {papalampidi_score}/10 ({evaluation_result['综合诊断']['结构质量']})
🏷️  功能质量 (Li):        {li_score}/10 ({evaluation_result['综合诊断']['功能质量']})
🔗 连贯性质量:            {coherence_result.get('平均连贯性', 0)} ({coherence_result.get('连贯性等级', '无法计算')})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 详细结果已保存至：{output_path}
""")
    
    return evaluation_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="双轨并行故事评价系统")
    parser.add_argument("--input", type=str, required=True, help="输入文件路径：.json 或 .md")
    parser.add_argument("--output", type=str, default="story_evaluation_result.json", help="输出结果文件路径")
    parser.add_argument("--model", type=str, default="gpt-4.1", help="使用的 LLM 模型名称")

    args = parser.parse_args()
    evaluate_story_dual_track(args.input, args.output, args.model)

# import os
# import json
# import argparse
# from tqdm import tqdm
# from src.utils.utils import load_json, generate_response
# from src.utils.utils import convert_json_safe as convert_json


# # 👇 LLM 模型判断两锚点是否同义（支持 markdown 包裹）
# def is_similar(a: str, b: str, threshold=0.85, model="gpt-4.1") -> bool:
#     prompt = f"""
# 你是一个叙事结构专家，请判断以下两个锚点是否表达相同的结构功能：

# A: 「{a}」
# B: 「{b}」

# 如果它们语义相近、承担相似情节角色（如任务开始、危机爆发、反派出现），请判断为同义。

# 请返回如下格式（仅 JSON）：
# {{"is_paraphrase": true 或 false, "reason": "简要说明"}}
#     """.strip()

#     response = generate_response([{"role": "user", "content": prompt}], model=model)

#     try:
#         result = convert_json(response)
#         return result.get("is_paraphrase", False)
#     except Exception as e:
#         print(f"❌ 无法解析模型输出: {e}\n原始返回：{response[:80]}")
#         return False

# def flatten_dual_anchors(path, level="core"):
#     data = load_json(path)
#     anchors = []
#     key = f"{level}_anchors"
#     for ch in data:
#         for a in ch.get(key, []):
#             anchor = a.copy()
#             anchor["chapter_id"] = ch["chapter_id"]
#             anchors.append(anchor)
#     return anchors

# def load_reference(path):
#     data = load_json(path)
#     if isinstance(data, dict) and "anchors" in data:
#         # 支持 { "anchors": ["任务1", "任务2", ...] }
#         return [{"surface": s, "type": None} for s in data["anchors"]]
#     elif isinstance(data, list):
#         return data
#     else:
#         raise ValueError("不支持的参考锚点格式")

# def match_surface(ref_surface, generated_surfaces, threshold=0.85):
#     for g in generated_surfaces:
#         if is_similar(ref_surface, g, threshold=threshold):
#             return g
#     return None

# def match_functional(ref_type, generated_types):
#     return ref_type in generated_types

# def evaluate_anchors(generated_path, reference_path, use_surface=True, use_functional=True,
#                      explain=False, generated_level=None):
#     # 读取生成锚点
#     if generated_level:
#         generated = flatten_dual_anchors(generated_path, level=generated_level)
#     else:
#         generated = load_json(generated_path)

#     # 读取参考锚点
#     reference = load_reference(reference_path)

#     results = []
#     total = len(reference)
#     surface_hits = 0
#     type_hits = 0

#     gen_surfaces = [a.get("surface", "") for a in generated]
#     gen_types = [a.get("type", "") for a in generated]

#     for ref in tqdm(reference, desc="🔍 匹配锚点"):
#         match = {"ref": ref, "surface_match": False, "type_match": False, "matched_to": None}

#         if use_surface and ref.get("surface"):
#             matched_surface = match_surface(ref["surface"], gen_surfaces)
#             if matched_surface:
#                 match["surface_match"] = True
#                 match["matched_to"] = matched_surface
#                 surface_hits += 1

#         if use_functional and ref.get("type"):
#             if match_functional(ref["type"], gen_types):
#                 match["type_match"] = True
#                 type_hits += 1

#         if explain and not match["surface_match"]:
#             prompt = f"参考锚点：{ref['surface']}\n未匹配生成锚点，请判断为何未命中？是否表达方式变化或结构遗漏？"
#             match["llm_reason"] = generate_response([{"role": "user", "content": prompt}])

#         results.append(match)

#     print("\n✅ 锚点对齐统计结果：")
#     if use_surface:
#         print(f"🔹 Surface 命中数：{surface_hits} / {total}（命中率 {surface_hits / total:.2%}）")
#     if use_functional:
#         print(f"🔹 Functional 类型匹配：{type_hits} / {total}（命中率 {type_hits / total:.2%}）")

#     return results

# def save_result(results, output_path="anchor_eval_result.json"):
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(results, f, ensure_ascii=False, indent=2)
#     print(f"\n📄 匹配详情已保存至：{output_path}")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--generated", type=str, required=True, help="生成的 anchors 路径")
#     parser.add_argument("--reference", type=str, required=True, help="参考 anchors 路径")
#     parser.add_argument("--surface", action="store_true", help="是否启用 surface 匹配")
#     parser.add_argument("--functional", action="store_true", help="是否启用 functional 类型匹配")
#     parser.add_argument("--explain", action="store_true", help="是否启用 LLM 错误解释")
#     parser.add_argument("--generated_level", choices=["core", "fine"], help="dual结构中提取的层级")
#     parser.add_argument("--output", type=str, default="anchor_eval_result.json")

#     args = parser.parse_args()
#     results = evaluate_anchors(
#         generated_path=args.generated,
#         reference_path=args.reference,
#         use_surface=args.surface,
#         use_functional=args.functional,
#         explain=args.explain,
#         generated_level=args.generated_level
#     )
#     save_result(results, args.output)
