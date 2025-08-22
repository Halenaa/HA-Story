import os
import json
import numpy as np
from collections import Counter
from src.utils.utils import generate_response, save_json, load_json


# def extract_events_from_story(story_data, model="gpt-4.1"):
#     """
#     改进版：两步法提取事件
#     第一步：提取事件描述
#     第二步：验证原文依据
#     """
#     # 准备原文
#     chapters_with_ids = []
#     for i, ch in enumerate(story_data):
#         chapter_text = f"【{ch.get('chapter_id', f'Chapter {i+1}')}】{ch.get('plot', '')}"
#         chapters_with_ids.append(chapter_text)
    
#     full_plot = "\n\n".join(chapters_with_ids)
    
#     print("  第一步：提取事件描述...")
    
#     # 第一步：只提取事件，不要求原文依据
#     step1_prompt = f"""
# 请从以下故事中提取所有关键事件。

# 要求：
# 1. 每个事件用10-20字简洁描述
# 2. 按时间顺序排列
# 3. 只输出事件描述，不需要原文依据

# 输出格式：
# [
#   "事件描述1",
#   "事件描述2", 
#   "事件描述3"
# ]

# 故事文本：
# {full_plot}
# """
    
#     response1 = generate_response([{"role": "user", "content": step1_prompt}], model=model)
    
#     try:
#         from src.utils.utils import convert_json
#         events_only = convert_json(response1)
#         if not isinstance(events_only, list):
#             print(f"⚠️ 第一步事件提取格式错误，期望list，得到{type(events_only)}")
#             return []
#     except Exception as e:
#         print(f"⚠️ 第一步事件提取失败：{e}")
#         return []
    
#     print(f"  ✅ 第一步提取到 {len(events_only)} 个事件")
#     print("  第二步：验证原文依据...")
    
#     # 第二步：为每个事件找原文依据
#     step2_prompt = f"""
# 给定事件列表和原文，请为每个事件找到最匹配的原文句子作为依据。

# 事件列表：
# {json.dumps(events_only, ensure_ascii=False, indent=2)}

# 原文：
# {full_plot}

# 要求：
# 1. 为每个事件找到原文中最相关的句子
# 2. 如果找不到支撑句子，source字段填写"无法找到原文依据"
# 3. 确定该事件来自哪个章节

# 输出格式：
# [
#   {{
#     "event": "事件描述",
#     "source": "原文中的具体句子或'无法找到原文依据'",
#     "chapter": "Chapter X"
#   }}
# ]
# """
    
#     response2 = generate_response([{"role": "user", "content": step2_prompt}], model=model)
    
#     try:
#         events_with_source = convert_json(response2)
#         if not isinstance(events_with_source, list):
#             print(f"⚠️ 第二步匹配格式错误，期望list，得到{type(events_with_source)}")
#             return []
            
#         # 过滤掉无法找到原文依据的事件
#         valid_events = []
#         filtered_count = 0
        
#         for event in events_with_source:
#             if event.get("source") != "无法找到原文依据":
#                 valid_events.append(event)
#             else:
#                 filtered_count += 1
#                 print(f"  ⚠️ 过滤事件（无原文依据）：{event.get('event', '')}")
        
#         print(f"  ✅ 第二步验证完成，过滤了 {filtered_count} 个无依据事件")
#         return valid_events
        
#     except Exception as e:
#         print(f"⚠️ 第二步验证失败：{e}")
#         return []


def extract_events_no_hallucination(story_data, model="gpt-4.1", temperature=None):
    """
    无幻觉版本：先分句编号，再让LLM选择
    temperature: None使用默认值，0表示固定模式，>0表示随机模式
    """
    from src.utils.utils import split_plot_into_sentences
    
    # 第一步：预处理原文，给每个句子编号
    all_sentences = []
    sentence_map = {}
    sentence_counter = 0
    
    for ch in story_data:
        chapter_id = ch.get('chapter_id', '')
        plot = ch.get('plot', '')
        sentences = split_plot_into_sentences(plot)
        
        for sent in sentences:
            sentence_map[sentence_counter] = {
                "sentence": sent,
                "chapter": chapter_id
            }
            all_sentences.append(f"{sentence_counter}: {sent}")
            sentence_counter += 1

    concat_story_plot = ""
    for i in story_data:
        concat_story_plot += i.get('chapter_id', '') + "\n" + i.get('plot', '') + "\n\n"
        
    # 准备编号句子列表
    numbered_sentences = "\n".join(all_sentences)
    double_newline = "\n\n"

    print("  第一步：提取事件...")
    # 第二步：提取事件
    step1_prompt = f"""
请从以下故事中提取所有关键事件。

要求：
1. 每个事件用10-20字简洁描述
2. 按时间顺序排列

重要限制：
1. 只提取每个章节内明确描述发生的事件, 不要添加任何假设或未明确描述的事件, 不要推断章节之间发生了什么
2. 准确描述动作的性质, 保持动作描述的准确性，不要夸大或改变其性质,比如不要把"准备做X"理解为"已经完成X"也不要把"威胁要做Y"理解为"已经做了Y"
3. 提取事件的同时需要标注事件来源

输出格式：
[
  {{"description":"事件描述1","reference":"chapter 1:文本原文"}},
  {{"description":"事件描述2","reference":"chapter 2:文本原文"}},
  ...
]
"""
    
    # 根据temperature参数调用
    if temperature is not None:
        response1 = generate_response([{"role": "user", "content": step1_prompt}], model=model, temperature=temperature)
        response1 = generate_response([
            {"role": "user", "content":step1_prompt},
        {"role": "user", "content": f"extract the key events base on the following story plot:\n\n{concat_story_plot}"}
        ], model=model, temperature=temperature)

    else:
        response1 = generate_response([{"role": "user", "content": step1_prompt}], model=model)
        response1 = generate_response([
            {"role": "user", "content":step1_prompt},
        {"role": "user", "content": f"extract the key events base on the following story plot:\n\n{concat_story_plot}"}
        ], model=model)
    try:
        from src.utils.utils import convert_json
        events_only = convert_json(response1)
        if not isinstance(events_only, list):
            print(f"⚠️ 事件提取失败")
            return []
    except Exception as e:
        print(f"⚠️ 事件提取失败：{e}")
        return []
    
    print(f"  ✅ 提取到 {len(events_only)} 个事件")
    print("  第二步：匹配原文句子...")
    
    # 第三步：让LLM为每个事件选择句子编号
    step2_prompt = f"""
给定事件列表和编号的原文句子，请为每个事件选择最匹配的句子编号。

事件列表：
{json.dumps(events_only, ensure_ascii=False, indent=2)}

编号的原文句子：
{numbered_sentences}

要求：
1. 为每个事件选择一个最匹配的句子编号
2. 如果找不到匹配的句子，编号填写-1
3. 只能选择已给出的编号，不能填写其他数字

输出格式：
[
  {{
    "event": "事件描述",
    "sentence_number": 编号数字,
    "confidence": "high/medium/low"
  }}
]
"""
    
    # 根据temperature参数调用
    if temperature is not None:
        response2 = generate_response([{"role": "user", "content": step2_prompt}], model=model, temperature=temperature)
    else:
        response2 = generate_response([{"role": "user", "content": step2_prompt}], model=model)
    
    try:
        matches = convert_json(response2)
        if not isinstance(matches, list):
            print(f"⚠️ 匹配失败")
            return []
        
        # 构建最终结果
        final_events = []
        filtered_count = 0
        
        for match in matches:
            sentence_num = match.get("sentence_number", -1)
            
            if sentence_num == -1 or sentence_num not in sentence_map:
                filtered_count += 1
                print(f"  ⚠️ 过滤事件（无匹配句子）：{match.get('event', '')}")
                continue
            
            sentence_info = sentence_map[sentence_num]
            final_events.append({
                "event": match.get("event", ""),
                "source": sentence_info["sentence"],
                "chapter": sentence_info["chapter"],
                "confidence": match.get("confidence", "unknown")
            })
        
        print(f"  ✅ 匹配完成，过滤了 {filtered_count} 个无匹配事件")

        validated_events = validate_events_against_source(final_events, model=model, temperature=temperature)
        return validated_events

        
    except Exception as e:
        print(f"⚠️ 匹配失败：{e}")
        return []

def validate_events_against_source(events, model="gpt-4.1", temperature=None):
    """
    第三步：验证事件与原文的一致性，消除幻觉
    """
    if not events:
        return []
    
    print("  第三步：验证事件准确性...")
    
    # 格式化事件和原文对照
    event_source_pairs = []
    for i, event in enumerate(events):
        event_source_pairs.append(f"""
事件{i+1}: {event['event']}
原文: {event['source']}
章节: {event['chapter']}
---""")
    
    formatted_pairs = "\n".join(event_source_pairs)
    
    validation_prompt = f"""
你现在是一个严格的事实检查员，需要验证事件描述与原文是否完全匹配。

特别要关注以下高危幻觉行为：
1. 原文说“准备/打算”，不能说成“已完成”；
2. 原文说“威胁/试图”，不能说成“已经做到”；
3. 原文中没有明确描述“交付/抵达/完成”，不能假设已经完成；
4. 一切未经证实的“获得/拿到/实施成功”行为都要质疑。

请逐句对比每个事件与原始章节内容，判断是否存在“完成状态幻觉”。如果发现需要修改成正确的事件描述.

{formatted_pairs}

输出格式：
[
  {{
    "original_event": "原始事件描述",
    "corrected_event": "修正后的事件描述（如无问题则与原始相同）",
    "has_issue": true/false,
    "issue_type": "问题类型（如果有的话）"
  }}
]

重要：只输出纯JSON，不要添加任何注释。
"""
    
    # 根据temperature参数调用
    if temperature is not None:
        response = generate_response([{"role": "user", "content": validation_prompt}], model=model, temperature=temperature)
    else:
        response = generate_response([{"role": "user", "content": validation_prompt}], model=model)
    
    try:
        from src.utils.utils import convert_json
        validation_results = convert_json(response)
        if not isinstance(validation_results, list):
            print("⚠️ 验证步骤格式错误，保持原事件")
            return events
        
        # 应用验证结果
        validated_events = []
        corrected_count = 0
        
        for i, (original_event, validation) in enumerate(zip(events, validation_results)):
            if validation.get("has_issue", False):
                corrected_count += 1
                print(f"  🔧 修正事件{i+1}: {validation.get('original_event', '')} → {validation.get('corrected_event', '')}")
                # 使用修正后的事件描述
                corrected_event = original_event.copy()
                corrected_event["event"] = validation.get("corrected_event", original_event["event"])
                validated_events.append(corrected_event)
            else:
                validated_events.append(original_event)
        
        print(f"  ✅ 验证完成，修正了 {corrected_count} 个事件")
        return validated_events
        
    except Exception as e:
        print(f"⚠️ 验证步骤失败：{e}，保持原事件")
        return events

def extract_events_fixed_mode(story_data, model="gpt-4.1"):
    """
    固定模式：完全可重现的事件提取
    """
    print("  🔒 固定模式（temperature=0）")
    return extract_events_no_hallucination(story_data, model=model, temperature=0)


def extract_events_statistical_mode(story_data, model="gpt-4.1", runs=3):
    """
    统计模式：多次运行，带统计分析
    """
    print(f"  📊 统计模式：运行 {runs} 次...")
    
    all_results = []
    all_event_counts = []
    
    for i in range(runs):
        print(f"    🔄 第 {i+1}/{runs} 次运行...")
        
        # 每次使用随机性（不设置temperature=0）
        events = extract_events_no_hallucination(story_data, model=model, temperature=0.3)
        
        if events:
            all_results.append(events)
            all_event_counts.append(len(events))
            print(f"      ✅ 第{i+1}次：{len(events)}个事件")
        else:
            print(f"      ❌ 第{i+1}次：提取失败")
    
    if not all_results:
        print("⚠️ 所有运行都失败了")
        return []
    
    # 统计分析
    event_counts = np.array(all_event_counts)
    avg_count = np.mean(event_counts)
    std_count = np.std(event_counts)
    min_count = np.min(event_counts)
    max_count = np.max(event_counts)
    
    # 计算置信区间（95%）
    if len(event_counts) > 1:
        confidence_interval = 1.96 * std_count / np.sqrt(len(event_counts))
        ci_lower = avg_count - confidence_interval
        ci_upper = avg_count + confidence_interval
    else:
        ci_lower = ci_upper = avg_count
    
    # 计算稳定性分数
    stability_score = 1 - (std_count / avg_count) if avg_count > 0 else 0
    
    print(f"  📈 统计分析结果：")
    print(f"    - 事件数量范围：{min_count}-{max_count}个")
    print(f"    - 平均事件数量：{avg_count:.1f} ± {std_count:.1f}")
    print(f"    - 95%置信区间：[{ci_lower:.1f}, {ci_upper:.1f}]")
    print(f"    - 稳定性评分：{stability_score:.3f} (0-1，越高越稳定)")
    
    # 选择最接近平均值的结果作为代表
    best_idx = np.argmin(np.abs(event_counts - avg_count))
    representative_result = all_results[best_idx]
    
    # 添加统计信息到每个事件
    for event in representative_result:
        event["statistical_info"] = {
            "run_index": int(best_idx + 1),
            "total_runs": runs,
            "avg_event_count": round(float(avg_count), 1),
            "std_event_count": round(float(std_count), 1),
            "stability_score": round(float(stability_score), 3),
            "confidence_interval_95": [round(float(ci_lower), 1), round(float(ci_upper), 1)],
            "event_count_range": [int(min_count), int(max_count)]
        }
    
    # 添加整体统计信息
    statistical_summary = {
        "runs_completed": len(all_results),
        "runs_failed": runs - len(all_results),
        "success_rate": len(all_results) / runs,
        "event_counts_by_run": all_event_counts,
        "statistical_metrics": {
            "mean": round(float(avg_count), 1),
            "std": round(float(std_count), 1),
            "min": int(min_count),
            "max": int(max_count),
            "stability_score": round(float(stability_score), 3),
            "confidence_interval_95": [round(float(ci_lower), 1), round(float(ci_upper), 1)]
        }
    }
    
    print(f"  ✅ 选择第{best_idx+1}次结果作为代表（最接近平均值）")
    
    return representative_result, statistical_summary


def analyze_papalampidi_structure(events, model="gpt-4.1", temperature=None):
    """
    使用Papalampidi框架分析故事结构
    """
    # 只传递事件描述给分析
    event_descriptions = [event.get("event", "") if isinstance(event, dict) else str(event) for event in events]
    events_str = json.dumps(event_descriptions, ensure_ascii=False, indent=2)
    
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
    "TP1": "具体事件描述",
    "TP2": "具体事件描述", 
    "TP3": "具体事件描述",
    "TP4": "具体事件描述",
    "TP5": "具体事件描述"
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

重要：只输出纯JSON，不要添加任何注释或说明文字。
"""
    
    # 根据temperature参数调用
    if temperature is not None:
        response = generate_response([{"role": "user", "content": prompt}], model=model, temperature=temperature)
    else:
        response = generate_response([{"role": "user", "content": prompt}], model=model)
    
    try:
        from src.utils.utils import convert_json
        result = convert_json(response)
        if not isinstance(result, dict):
            print(f"⚠️ Papalampidi分析格式错误")
            return {"转折点": {}, "阶段划分": {}}
        return result
    except Exception as e:
        print(f"⚠️ Papalampidi分析失败：{e}")
        return {"转折点": {}, "阶段划分": {}}


def analyze_li_functions(events, model="gpt-4.1", temperature=None):
    """
    使用Li框架分析故事功能
    """
    # 只传递事件描述给分析
    event_descriptions = [event.get("event", "") if isinstance(event, dict) else str(event) for event in events]
    events_str = json.dumps(event_descriptions, ensure_ascii=False, indent=2)
    
    prompt = f"""
给定事件列表，请用10个功能标签标注每个事件：

事件列表：{events_str}

功能标签定义：
- Abstract: 故事要点的总结
- Orientation: 背景设定（时间、地点、人物）
- Complicating Action: 增加张力、推动情节的事件
- MRE : 最重要/最值得报告的事件 (Most Reportable Event)
- Minor Resolution: 部分缓解张力的事件
- Return of MRE: MRE主题的重新出现
- Resolution: 解决主要冲突的事件  
- Aftermath: 主要事件后的长期影响
- Evaluation: 叙述者对故事意义的评论
- Direct Comment: 对观众的直接评论

输出格式：
{{
  "事件1": "标签名",
  "事件2": "标签名",
  "事件3": "标签名",
  ...
}}

重要：只输出纯JSON，不要添加任何注释或说明文字。
"""
    
    # 根据temperature参数调用
    if temperature is not None:
        response = generate_response([{"role": "user", "content": prompt}], model=model, temperature=temperature)
    else:
        response = generate_response([{"role": "user", "content": prompt}], model=model)
    
    try:
        from src.utils.utils import convert_json
        result = convert_json(response)
        if not isinstance(result, dict):
            print(f"⚠️ Li分析格式错误")
            return {}
        return result
    except Exception as e:
        print(f"⚠️ Li分析失败：{e}")
        return {}


def analyze_story_structure(events, papalampidi_result, li_result, mode="default", statistical_summary=None):
    """
    客观分析故事结构
    """
    analysis = {
        "基本信息": {
            "事件总数": len(events),
            "分析模式": mode,
            "分析时间": None
        },
        "Papalampidi结构分析": {
            "转折点完整性": {},
            "阶段完整性": {}
        },
        "Li功能分析": {
            "核心功能检查": {},
            "功能分布": {},
            "功能多样性": 0
        }
    }
    
    # 添加统计信息（如果是统计模式）
    if statistical_summary:
        analysis["统计分析摘要"] = statistical_summary
    
    # 分析Papalampidi结构
    required_tps = ["TP1", "TP2", "TP3", "TP4", "TP5"]
    found_tps = [tp for tp in required_tps if papalampidi_result.get("转折点", {}).get(tp)]
    missing_tps = [tp for tp in required_tps if tp not in found_tps]
    
    analysis["Papalampidi结构分析"]["转折点完整性"] = {
        "识别到的TP": found_tps,
        "缺失的TP": missing_tps,
        "TP覆盖率": f"{len(found_tps)}/5"
    }
    
    required_stages = ["Setup", "New Situation", "Progress", "Complications", "Final Push", "Aftermath"]
    found_stages = [stage for stage in required_stages if papalampidi_result.get("阶段划分", {}).get(stage)]
    missing_stages = [stage for stage in required_stages if stage not in found_stages]
    
    analysis["Papalampidi结构分析"]["阶段完整性"] = {
        "识别到的阶段": found_stages,
        "缺失的阶段": missing_stages,
        "阶段覆盖率": f"{len(found_stages)}/6"
    }
    
    # 分析Li功能
    core_functions = ["Orientation", "Complicating Action", "MRE", "Resolution"]
    for func in core_functions:
        exists = any(func in value for value in li_result.values())
        analysis["Li功能分析"]["核心功能检查"][func] = "存在" if exists else "缺失"

    # 功能分布统计
    func_counts = Counter(li_result.values())
    analysis["Li功能分析"]["功能分布"] = dict(func_counts)
    analysis["Li功能分析"]["功能多样性"] = len(set(li_result.values()))
    
    return analysis


def run_story_evaluation(version, mode="default", runs=3, story_file="story_updated.json", model="gpt-4.1"):
    """
    主函数：运行完整的故事评价
    mode: "default", "fixed", "statistical"
    """
    from src.constant import output_dir
    
    print(f"\n🔍 开始故事结构评价：{version}")
    
    # 读取故事数据
    story_path = os.path.join(output_dir, version, story_file)
    if not os.path.exists(story_path):
        print(f"⚠️ 故事文件不存在：{story_path}")
        return None
    
    story_data = load_json(story_path)
    
    # Step 1: 根据模式提取关键事件
    statistical_summary = None
    
    if mode == "fixed":
        print("📋 步骤1：固定模式提取关键事件...")
        events = extract_events_fixed_mode(story_data, model=model)
        temp_for_analysis = 0  # 分析阶段也使用固定模式

    elif mode == "statistical":
        print(f"📋 步骤1：统计模式提取关键事件（{runs}次运行）...")
        result = extract_events_statistical_mode(story_data, model=model, runs=runs)
        if isinstance(result, tuple):
            events, statistical_summary = result
        else:
            events = result
        temp_for_analysis = 0  # 分析阶段使用固定模式，确保同样事件得到一致分析

    # elif mode == "statistical":
    #     print(f"📋 步骤1：统计模式提取关键事件（{runs}次运行）...")
    #     result = extract_events_statistical_mode(story_data, model=model, runs=runs)
    #     if isinstance(result, tuple):
    #         events, statistical_summary = result
    #     else:
    #         events = result
    #     temp_for_analysis = 0  
    else:
        print("📋 步骤1：默认模式提取关键事件...")
        events = extract_events_no_hallucination(story_data, model=model)
        temp_for_analysis = None  # 使用默认temperature
    
    print(f"✅ 最终提取到 {len(events)} 个有效事件")
    
    if len(events) == 0:
        print("⚠️ 没有提取到有效事件，终止分析")
        return None
    
    # Step 2: Papalampidi结构分析
    print("📊 步骤2：Papalampidi结构分析...")
    papalampidi_result = analyze_papalampidi_structure(events, model=model, temperature=temp_for_analysis)
    
    # Step 3: Li功能分析
    print("🏷️ 步骤3：Li功能分析...")
    li_result = analyze_li_functions(events, model=model, temperature=temp_for_analysis)
    
    # Step 4: 综合分析
    print("📈 步骤4：综合分析...")
    structure_analysis = analyze_story_structure(events, papalampidi_result, li_result, mode, statistical_summary)
    
    # 汇总结果
    evaluation_result = {
        "评价模式": f"{mode}模式" + (f"（{runs}次运行）" if mode == "statistical" else ""),
        "事件列表": events,
        "Papalampidi详细结果": papalampidi_result,
        "Li详细结果": li_result,
        "结构分析": structure_analysis
    }
    
    # 保存结果
    output_filename = f"story_structure_analysis_{mode}.json"
    if mode == "statistical":
        output_filename = f"story_structure_analysis_{mode}_{runs}runs.json"
    save_json(evaluation_result, version, output_filename)
    
    # 打印摘要
    print_evaluation_summary(structure_analysis, mode, statistical_summary)
    
    return evaluation_result


def print_evaluation_summary(structure_analysis, mode, statistical_summary=None):
    """打印评价摘要"""
    tp_coverage = structure_analysis["Papalampidi结构分析"]["转折点完整性"]["TP覆盖率"]
    stage_coverage = structure_analysis["Papalampidi结构分析"]["阶段完整性"]["阶段覆盖率"]
    core_missing = [k for k, v in structure_analysis["Li功能分析"]["核心功能检查"].items() if v == "缺失"]
    function_diversity = structure_analysis["Li功能分析"]["功能多样性"]
    
    mode_display = f"{mode}模式"
    
    print(f"""
📊 {mode_display}评价完成！结果摘要：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Papalampidi结构:
   - 转折点覆盖: {tp_coverage}
   - 阶段覆盖: {stage_coverage}
🏷️ Li功能分析:
   - 缺失核心功能: {core_missing if core_missing else '无'}
   - 功能多样性: {function_diversity}种""")
    
    # 如果是统计模式，显示统计信息
    if statistical_summary and mode == "statistical":
        metrics = statistical_summary["statistical_metrics"]
        print(f"""📊 统计分析摘要:
   - 成功率: {statistical_summary['success_rate']:.1%}
   - 事件数量: {metrics['mean']} ± {metrics['std']} (范围: {metrics['min']}-{metrics['max']})
   - 95%置信区间: [{metrics['confidence_interval_95'][0]}, {metrics['confidence_interval_95'][1]}]
   - 稳定性评分: {metrics['stability_score']:.3f}/1.000""")
    
    print(f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 详细结果已保存
""")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="增强版故事结构评价工具")
    parser.add_argument("--version", type=str, required=True, help="版本文件夹名")
    parser.add_argument("--mode", type=str, choices=["default", "fixed", "statistical"], default="default", 
                       help="评价模式：default（默认）、fixed（固定可重现）或 statistical（统计分析）")
    parser.add_argument("--runs", type=int, default=3, help="统计模式的运行次数")
    parser.add_argument("--story-file", type=str, default="story_updated.json", help="故事文件名")
    parser.add_argument("--model", type=str, default="gpt-4.1", help="使用的LLM模型")
    
    args = parser.parse_args()
    run_story_evaluation(args.version, args.mode, args.runs, args.story_file, args.model)