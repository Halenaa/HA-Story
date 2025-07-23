import json
from src.utils.utils import generate_response, convert_json

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
        """
    }]
    response = generate_response(msg)
    return convert_json(response)


def generate_dialogue_for_insertion(sentence_context, candidate_characters, full_plot, character_personality):
    """
    在某一句剧情之后插入对话，loop 判断是否说、谁说、说几轮
    """
    character_memory = {char: [] for char in candidate_characters}
    history = ""

    # 第一个发言人
    speaker = candidate_characters[0]
    prompt_first = [{
        "role": "system",
        "content": f"""你是 {speaker}，请基于以下剧情做出第一句发言。
剧情背景是：{sentence_context}
你可以向其他角色说话：{[c for c in candidate_characters if c != speaker]}
返回格式：
{{"dialogue": "...", "action": "..."}}"""
    }]
    response = generate_response(prompt_first)
    parsed = convert_json(response)
    character_memory[speaker].append(f"{speaker}: {parsed['dialogue']}")
    history += f"{speaker}: {parsed['dialogue']}\n"

    state = 1
    while state != 0:
        # 判断下一个发言人
        speaker_prompt = [{
            "role": "system",
            "content": f"""你是故事编剧。
当前剧情：{sentence_context}
当前已有对话历史：
{character_memory}

只能从以下角色中选择发言：{candidate_characters}
请判断下一位发言人是谁？如果不需要继续对话，返回"NONE"。
格式：{{"next_speaker": "角色"}}"""
        }]
        next_res = generate_response(speaker_prompt)
        next_speaker = convert_json(next_res).get("next_speaker", "NONE")
        if next_speaker == "NONE" or next_speaker not in character_memory:
            print(f"非法角色名: {next_speaker}, 已跳过。")
            break

        # 发言内容
        prompt_reply = [{
            "role": "system",
            "content": f"""你是 {next_speaker}，你要基于剧情：
{sentence_context}
以及对话历史：
{character_memory}
继续说一句话，格式如下：
{{"dialogue": "...", "action": "..."}}"""
        }]
        response = generate_response(prompt_reply)
        parsed = convert_json(response)
        character_memory[next_speaker].append(f"{next_speaker}: {parsed['dialogue']}")
        history += f"{next_speaker}: {parsed['dialogue']}\n"

        # 判断是否继续
        state_prompt = [{
            "role": "user",
            "content": f"""对话背景：
{sentence_context}
当前已有对话：
{character_memory}
请判断是否继续下一轮发言？返回格式：{{"state": 0 或 1}}"""
        }]
        state_res = generate_response(state_prompt)
        state = convert_json(state_res)["state"]

    return character_memory


def run_dialogue_insertion(plot_list, character_json):
    """
    整合控制流程：先判断哪些句子后要插入，再生成每段对话
    """
    marks = analyze_dialogue_insertions(plot_list, character_json)
    final_result = []

    for item in marks:
        dialogue_block = {
            "sentence": item["sentence"],
            "need_to_action": item["need_to_action"],
            "actor_list": item["actor_list"],
            "dialogue": []
        }
        if item["need_to_action"] == 1:
            dialogue_memory = generate_dialogue_for_insertion(
                sentence_context=item["sentence"],
                candidate_characters=item["actor_list"],
                full_plot=plot_list,
                character_personality=character_json
            )
            dialogue_block["dialogue"] = dialogue_memory
        final_result.append(dialogue_block)

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
