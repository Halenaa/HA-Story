import json
import logging
import os
from datetime import datetime
from src.utils.utils import generate_response, convert_json, split_plot_into_sentences, extract_behavior_llm

# 🆕 添加日志设置函数
def setup_dialogue_logger():
    """简单的日志设置，输出到文件和控制台"""
    logger = logging.getLogger('dialogue_gen')
    if logger.handlers:  # 避免重复设置
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 文件handler - 输出到data/output/logs/dialogue.log
    try:
        log_dir = "data/output/logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(f"{log_dir}/dialogue_generation.log", encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 格式
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except:
        pass  # 如果日志文件创建失败，不影响主流程
    
    return logger

def analyze_dialogue_insertions(plot_list, character_list_json):
    """
    判断每句话是否需要插入对话，返回结构建议
    """
    msg = [{
        "role": "system",
        "content": f"""
你的角色是一个编剧，需要控制在剧情中哪个节点加入对话情节，并选择对应的演员进行演绎。你需要对以下我给你的 plot 每一句进行分析：

如果在某个句子后需要插入对话，你则返回 1，并选择对应的演员；否则返回 0，演员列表为空。

#Output Format：
[
{{
  "sentence": "...",
  "need_to_action": 0 or 1,
  "actor_list": ["演员A", "演员B"]
}},
...
]

以下是 plot 列表：{plot_list}

这是演员表：{character_list_json}
只返回符合上述格式的 JSON，不要添加任何解释说明或额外文字。
        """
    }]
    response = generate_response(msg)
    print("\n analyze_dialogue_insertions 原始返回内容：\n", response, "\n")  # ✅ 添加这一行

    return convert_json(response)

def analyze_dialogue_insertions_v2(story, characters):
    """
    增强版：确保sentence_results包含完整对话数据
    """
    from src.utils.utils import split_plot_into_sentences, generate_response, convert_json, extract_behavior_llm
    from src.generation.dialogue_inserter import generate_dialogue_for_insertion
    
    chapter_results = []
    behavior_timeline = []
    sentence_results = []
    
    for chapter in story:
        chapter_id = chapter.get("chapter_id", "Unknown")
        scene = chapter.get("scene", "")
        plot = chapter.get("plot", "")
        
        sentences = split_plot_into_sentences(plot)
        print(f"章节{chapter_id}分割为{len(sentences)}个句子")
        
        # LLM分析句子
        msg = [{
            "role": "system", 
            "content": f"""对每句剧情判断是否需要插入对话：
句子列表：{sentences}
演员表：{characters}
格式：[{{"sentence":"...", "need_to_action":0 or 1, "actor_list":["演员A"]}}]
只返回JSON。"""
        }]
        response = generate_response(msg)
        sentence_analysis = convert_json(response)
        
        chapter_dialogues = []
        all_actors = set()
        
        for sent_idx, result in enumerate(sentence_analysis):
            # 🎯 为每个句子生成独立的对话
            sentence_dialogue = []
            
            if result.get("need_to_action") == 1:
                # 生成这个句子的对话
                dialogue = generate_dialogue_for_insertion(
                    result["sentence"], 
                    result["actor_list"],
                    [plot],
                    characters
                )
                sentence_dialogue = dialogue
                chapter_dialogues.extend(dialogue)
                all_actors.update(result["actor_list"])
                
                # behavior提取
                if dialogue:
                    try:
                        behavior = extract_behavior_llm(dialogue)
                        for character, behaviors in behavior.items():
                            for behavior_state in behaviors:
                                behavior_timeline.append({
                                    "chapter_id": chapter_id,
                                    "sentence_index": sent_idx,
                                    "sentence": result["sentence"][:50] + "..." if len(result["sentence"]) > 50 else result["sentence"],
                                    "character": character,
                                    "behavior": behavior_state,
                                    "scene_context": scene,
                                    "dialogue_trigger": True
                                })
                    except Exception as e:
                        print(f"⚠️ Behavior提取失败: {e}")
            
            # 🎯 关键：sentence_results包含dialogue字段
            sentence_result = {
                "chapter_id": chapter_id,
                "sentence_index": sent_idx,
                "sentence": result.get("sentence", ""),
                "need_to_action": result.get("need_to_action", 0),
                "actor_list": result.get("actor_list", []),
                "dialogue": sentence_dialogue,  # 🎯 每个句子的独立对话
                "scene_context": scene
            }
            sentence_results.append(sentence_result)
        
        # 章节级结果（兼容后续模块）
        chapter_result = {
            "sentence": plot,
            "need_to_action": 1 if chapter_dialogues else 0,
            "actor_list": list(all_actors),
            "dialogue": chapter_dialogues
        }
        chapter_results.append(chapter_result)
    
    return chapter_results, sentence_results, behavior_timeline

# def generate_dialogue_for_insertion(sentence_context, candidate_characters, full_plot, character_personality):
#     """
#     在某一句剧情之后插入对话，loop 判断是否说、谁说、说几轮
#     """
#     print(f"\n🔍 开始生成对话，候选角色: {candidate_characters}")
    
#     # 改用列表直接存储完整对话数据
#     dialogue_list = []
#     history = ""

#     # 第一个发言人
#     speaker = candidate_characters[0]
#     prompt_first = [{
#         "role": "system",
#         "content": f"""你是 {speaker}，请基于以下剧情做出第一句发言。
# 剧情背景是：{sentence_context}
# 你可以向其他角色说话：{[c for c in candidate_characters if c != speaker]}
# 用以下json格式返回：
# {{"dialogue": "...", "action": "..."}}"""
#     }]
    
#     print(f"  📤 发送第一个prompt给{speaker}")
#     response = generate_response(prompt_first)
#     print(f"  📥 LLM原始返回: {response[:200]}...")
    
#     parsed = convert_json(response)
#     print(f"  🔍 解析后的类型: {type(parsed)}, 内容: {parsed}")
    
#     # 处理第一个回复
#     if not isinstance(parsed, dict):
#         print(f"  ⚠️ parsed不是字典，而是{type(parsed)}")
#         # 如果返回的是列表，处理每个元素
#         for each in parsed:
#             if isinstance(each, dict):
#                 spoken_line = each.get("dialogue", "")
#                 action = each.get("action", "")
#                 if spoken_line:
#                     dialogue_list.append({
#                         "speaker": speaker,
#                         "dialogue": spoken_line,
#                         "action": action or ""  # 保存action
#                     })
#                     history += f"{speaker}: {spoken_line}\n"
#     else:
#         # 处理字典格式
#         spoken_line = parsed.get("dialogue", "")
#         action = parsed.get("action", "")
#         if spoken_line:
#             dialogue_list.append({
#                 "speaker": speaker,
#                 "dialogue": spoken_line,
#                 "action": action or ""  # 保存action
#             })
#             history += f"{speaker}: {spoken_line}\n"
#         else:
#             print(f"  ⚠️ 没有获取到dialogue字段")

#     # 多轮对话循环
#     state = 1
#     MAX_ROUNDS = 10
#     round_count = 0

#     while state != 0 and round_count < MAX_ROUNDS:
#         round_count += 1
#         print(f"\n  🔄 第{round_count}轮对话")
        
#         # 判断下一个发言人
#         speaker_prompt = [{
#             "role": "system",
#             "content": f"""你是故事编剧。
# 当前剧情：{sentence_context}
# 当前已有对话历史：
# {history}

# 只能从以下角色中选择发言：{candidate_characters}
# 请判断下一位发言人是谁？如果不需要继续对话，返回"NONE"。
# 格式：{{"next_speaker": "角色"}}"""
#         }]
        
#         next_res = generate_response(speaker_prompt)
#         print(f"    📥 下一个发言人返回: {next_res[:100]}...")
        
#         next_data = convert_json(next_res)
#         if not isinstance(next_data, dict):
#             print(f"    ⚠️ next_data不是字典: {type(next_data)}")
#             break
            
#         next_speaker = next_data.get("next_speaker", "NONE")
        
#         if next_speaker == "NONE" or next_speaker not in candidate_characters:
#             print(f"结束对话，next_speaker={next_speaker}")
#             break

#         # 生成发言内容
#         prompt_reply = [{
#             "role": "system",
#             "content": f"""你是 {next_speaker}，你要基于剧情：
# {sentence_context}
# 以及对话历史：
# {history}
# 继续说一句话，格式如下：
# {{"dialogue": "...", "action": "..."}}"""
#         }]
        
#         response = generate_response(prompt_reply)
#         parsed = convert_json(response)
        
#         if isinstance(parsed, dict) and "dialogue" in parsed:
#             spoken_line = parsed.get("dialogue", "")
#             action = parsed.get("action", "")
            
#             dialogue_list.append({
#                 "speaker": next_speaker,
#                 "dialogue": spoken_line,
#                 "action": action or ""  # 保存action
#             })
#             history += f"{next_speaker}: {spoken_line}\n"
#         else:
#             print(f"    ⚠️ 无法解析{next_speaker}的回复")
    
#     print(f"  ✅ 生成了{len(dialogue_list)}条对话")
#     return dialogue_list

def generate_dialogue_for_insertion(sentence_context, candidate_characters, full_plot, character_personality):
    """
    完全信任LLM判断版：保持原有格式，移除所有人为限制
    """
    # 🆕 初始化日志
    logger = setup_dialogue_logger()
    session_id = datetime.now().strftime("%H%M%S")
    
    print(f"\n🔍 开始生成对话，候选角色: {candidate_characters}")
    # 🆕 记录会话开始
    logger.info(f"SESSION_START | session_id={session_id} | characters={candidate_characters} | context={sentence_context[:100]}...")
    
    dialogue_list = []
    history = ""

    # 分析对话目标 - 修复JSON格式问题
    goal_prompt = [{
        "role": "system",
        "content": f"""你是故事编剧。分析以下剧情片段需要用对话表达什么：

剧情：{sentence_context}
可用角色：{candidate_characters}

请分析：这段剧情最需要通过对话表达什么？预期几轮对话比较合适？

⚠️ 重要：expected_rounds必须是单个整数（如2、3、4），不能是范围（如3-5）

格式：{{"goal": "对话目标描述", "expected_rounds": 整数}}"""
    }]
    
    try:
        goal_response = generate_response(goal_prompt)
        goal_data = convert_json(goal_response)
        
        # 强化防错处理
        if isinstance(goal_data, dict):
            dialogue_goal = goal_data.get("goal", "推进剧情")
            expected_rounds = goal_data.get("expected_rounds", 3)
            
            # 处理非数字情况
            try:
                expected_rounds = int(expected_rounds)
            except (ValueError, TypeError):
                expected_rounds = 3
        else:
            print(f"⚠️ 目标分析返回非dict格式: {type(goal_data)}")
            dialogue_goal = "推进剧情"
            expected_rounds = 3
            
    except Exception as e:
        print(f"⚠️ 目标分析失败: {e}")
        dialogue_goal = "推进剧情"
        expected_rounds = 3

    # 🆕 记录目标设定
    logger.info(f"GOAL_SET | session_id={session_id} | goal='{dialogue_goal}' | expected_rounds={expected_rounds}")

    # 第一个发言人
    speaker = candidate_characters[0]
    prompt_first = [{
        "role": "system",
        "content": f"""你是 {speaker}，请基于以下剧情做出第一句发言。
剧情背景：{sentence_context}
对话目标：{dialogue_goal}
其他角色：{[c for c in candidate_characters if c != speaker]}
格式：{{"dialogue": "...", "action": "..."}}"""
    }]
    
    try:
        response = generate_response(prompt_first)
        parsed = convert_json(response)
        
        if isinstance(parsed, dict) and "dialogue" in parsed:
            spoken_line = parsed.get("dialogue", "")
            action = parsed.get("action", "")
            dialogue_list.append({
                "speaker": speaker,
                "dialogue": spoken_line,
                "action": action
            })
            history += f"{speaker}: {spoken_line}\n"
            # 🆕 记录首句对话
            logger.info(f"FIRST_DIALOGUE | session_id={session_id} | speaker={speaker} | length={len(spoken_line)}")
    except Exception as e:
        print(f"⚠️ 第一句对话生成失败: {e}")
        # 🆕 记录错误
        logger.error(f"FIRST_DIALOGUE_FAILED | session_id={session_id} | error={e}")
        return []

    # 🎯 完全信任LLM的循环判断
    round_count = 0
    SAFETY_LIMIT = 20  # 仅作保底
    
    while round_count < SAFETY_LIMIT:
        round_count += 1
        
        # 保持原有判断格式，LLM已经习惯了
        judge_prompt = [{
            "role": "system",
            "content": f"""你是故事编剧。请分析当前对话状态：

【剧情背景】：{sentence_context}
【对话目标】：{dialogue_goal}
【预期轮数】：{expected_rounds}
【当前轮数】：{round_count}
【对话历史】：
{history}

请回答两个问题：
1. 对话目标是否已经达成？(0-10分评分)
2. 如果未充分达成，下一个发言人是谁？

可选角色：{candidate_characters}

格式：{{"goal_achieved": 分数, "should_continue": true/false, "next_speaker": "角色名或NONE", "reason": "判断理由"}}"""
        }]
        
        try:
            judge_res = generate_response(judge_prompt)
            judge_data = convert_json(judge_res)
            
            # 强化类型检查
            if not isinstance(judge_data, dict):
                print(f"⚠️ 判断返回非dict格式: {type(judge_data)}")
                # 🆕 记录判断失败
                logger.warning(f"JUDGE_FAILED | session_id={session_id} | round={round_count} | type={type(judge_data)}")
                break
                
            goal_achieved = judge_data.get("goal_achieved", 5)
            should_continue = judge_data.get("should_continue", False)
            next_speaker = judge_data.get("next_speaker", "NONE")
            reason = judge_data.get("reason", "")
            
            print(f"    📊 LLM判断: goal_achieved={goal_achieved}, should_continue={should_continue}, next_speaker={next_speaker}")
            # 🆕 记录LLM判断详情
            logger.info(f"LLM_JUDGE | session_id={session_id} | round={round_count} | goal_achieved={goal_achieved} | should_continue={should_continue} | next_speaker={next_speaker} | reason={reason[:50]}...")
                
        except Exception as e:
            print(f"⚠️ 对话判断失败: {e}，结束对话")
            # 🆕 记录判断错误
            logger.error(f"JUDGE_ERROR | session_id={session_id} | round={round_count} | error={e}")
            break
        
        # 🎯 完全信任LLM：只看LLM的should_continue判断
        if (not should_continue or
            next_speaker == "NONE" or 
            next_speaker not in candidate_characters):
            print(f"  🛑 LLM决定结束对话")
            # 🆕 记录停止原因
            stop_reasons = []
            if not should_continue:
                stop_reasons.append("LLM_STOP")
            if next_speaker == "NONE":
                stop_reasons.append("SPEAKER_NONE")
            if next_speaker not in candidate_characters:
                stop_reasons.append("INVALID_SPEAKER")
            logger.info(f"DIALOGUE_END | session_id={session_id} | round={round_count} | reasons={stop_reasons}")
            break

        # 生成发言内容
        prompt_reply = [{
            "role": "system",
            "content": f"""你是 {next_speaker}，基于剧情：{sentence_context}
对话目标：{dialogue_goal}
对话历史：{history}
继续说一句话，格式：{{"dialogue": "...", "action": "..."}}"""
        }]
        
        try:
            response = generate_response(prompt_reply)
            parsed = convert_json(response)
            
            if isinstance(parsed, dict) and "dialogue" in parsed:
                spoken_line = parsed.get("dialogue", "")
                action = parsed.get("action", "")
                dialogue_list.append({
                    "speaker": next_speaker,
                    "dialogue": spoken_line,
                    "action": action
                })
                history += f"{next_speaker}: {spoken_line}\n"
                # 🆕 记录每轮对话
                logger.info(f"DIALOGUE_ADD | session_id={session_id} | round={round_count} | speaker={next_speaker} | length={len(spoken_line)}")
        except Exception as e:
            print(f"⚠️ 发言生成失败: {e}，跳过这轮")
            # 🆕 记录生成失败
            logger.warning(f"DIALOGUE_FAILED | session_id={session_id} | round={round_count} | speaker={next_speaker} | error={e}")
            continue
    
    if round_count >= SAFETY_LIMIT:
        print(f"⚠️ 达到安全保底({SAFETY_LIMIT}轮)")
        # 🆕 记录安全限制触发
        logger.warning(f"SAFETY_LIMIT | session_id={session_id} | limit={SAFETY_LIMIT}")
    
    # 🆕 记录最终统计
    final_rounds = len(dialogue_list)
    logger.info(f"SESSION_END | session_id={session_id} | final_rounds={final_rounds} | expected={expected_rounds} | characters_used={[d['speaker'] for d in dialogue_list]}")
    
    print(f"  ✅ 生成了{final_rounds}条对话")
    return dialogue_list


def run_dialogue_insertion(plot_list, character_json):
    """
    整合控制流程：先判断哪些句子后要插入，再生成每段对话
    """
    marks = analyze_dialogue_insertions(plot_list, character_json)
    
    # ✅ 添加错误处理
    if not marks or not isinstance(marks, list):
        print(f"⚠️ analyze_dialogue_insertions 返回无效数据: {type(marks)}")
        # 返回空对话结构，确保每个plot都有对应的对话块
        return [{
            "sentence": plot,
            "need_to_action": 0,
            "actor_list": [],
            "dialogue": []
        } for plot in plot_list]
    
    final_result = []

    # ✅ 确保返回的结果数量与plot_list匹配
    plot_index = 0
    for item in marks:
        dialogue_block = {
            "sentence": item.get("sentence", ""),
            "need_to_action": item.get("need_to_action", 0),
            "actor_list": item.get("actor_list", []),
            "dialogue": []
        }
        
        if item.get("need_to_action") == 1 and item.get("actor_list"):
            # try:
            dialogue_memory = generate_dialogue_for_insertion(
                sentence_context=item["sentence"],
                candidate_characters=item["actor_list"],
                full_plot=plot_list,
                character_personality=character_json
            )
            dialogue_block["dialogue"] = dialogue_memory
            # except Exception as e:
            #     print(f"⚠️ 生成对话失败: {e}")
            #     dialogue_block["dialogue"] = []
                
        final_result.append(dialogue_block)
        plot_index += 1
    
    # ✅ 如果marks数量少于plot_list，补充空对话块
    while len(final_result) < len(plot_list):
        final_result.append({
            "sentence": plot_list[len(final_result)] if len(final_result) < len(plot_list) else "",
            "need_to_action": 0,
            "actor_list": [],
            "dialogue": []
        })
    
    print(f"✅ 生成对话块数量: {len(final_result)}, plot数量: {len(plot_list)}")
    
    return final_result
def apply_structure_to_generate_dialogue(structure_marks, plot_list, characters):
    final_result = []
    for item in structure_marks:
        dialogue_block = {
            "sentence": item["sentence"],
            "need_to_action": item["need_to_action"],
            "actor_list": item["actor_list"],
            "dialogue": []
        }
        if item["need_to_action"] == 1:
            dialogue = generate_dialogue_for_insertion(
                sentence_context=item["sentence"],
                candidate_characters=item["actor_list"],
                full_plot=plot_list,
                character_personality=characters
            )
            dialogue_block["dialogue"] = dialogue
        final_result.append(dialogue_block)
    return final_result



def pretty_print_dialogue(dialogue_result):
    """
    美观打印完整对话插入结构，适合人类调试或写入 Markdown 文件
    """
    for i, block in enumerate(dialogue_result):
        print(f"\n第 {i+1} 句剧情：{block['sentence'][:80]}...")
        if block["need_to_action"] == 0:
            print("无需插入对话。")
        else:
            print(f"插入角色：{', '.join(block['actor_list'])}")
            dialogue = block.get("dialogue", {})
            for role, lines in dialogue.items():
                for line in lines:
                    print(f"  {line}")



def generate_dialogue_for_plot(instruction, characters):
    from src.utils.utils import generate_response, convert_json
    character_list = ", ".join([c["name"] for c in characters])
    prompt = f"""
剧情内容如下：
{instruction}

角色有：{character_list}

请为该场景生成5-6轮简洁自然的对话，展现角色风格与互动张力，格式如下：
[
  {{"speaker": "角色A", "line": "说的话"}},
  ...
]
"""
    response = generate_response([{"role": "user", "content": prompt}])
    return convert_json(response)
