from src.utils import generate_response,convert_json

def analyze_dialogue_insertions(plot_list, character_list_json):
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

以下是具体的 plot：{plot_list}

这是演员表：{character_list_json}
        """
    }]
    response = generate_response(msg)
    return convert_json(response)
