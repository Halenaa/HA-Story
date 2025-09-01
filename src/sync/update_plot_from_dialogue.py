import os
from src.utils.utils import generate_response, convert_json

def update_plot_from_dialogue(chapter_id, original_plot, dialogue, character_info, model="gpt-4.1"):
    """
    根据对话和角色信息，自动更新当前章节的 plot。
    返回：dict，含 updated_plot / change_summary / changed
    """
    role_profiles = "\n".join([
        f"{char['name']}（性格：{char['traits']}，动机：{char['motivation']}）"
        for char in character_info
    ])
        
    # ✅ 防御式检查，确保 dialogue 是 list，并兼容不同字段名
    if isinstance(dialogue, str):
        dialogue_lines = dialogue  # 如果已经是字符串了，直接用
    elif isinstance(dialogue, list):
        dialogue_lines = "\n".join([
            f"{d['speaker']}: {d.get('dialogue', d.get('line', ''))}" for d in dialogue  # ✅ 优先 'dialogue'，兼容 'line'
        ])
    else:
        dialogue_lines = ""
    
    prompt = f"""
你是一个叙事结构专家。现在有一个章节的剧情概要（plot）和对应的角色对话，请你判断：

- 当前对话是否已经偏离了原来的 plot（比如角色动机、立场发生变化）
- 如果是，请你帮我生成一个 **更新后的 plot**，使其与对话行为一致
- 保持人物逻辑与前后情节衔接自然

# 输入信息如下：

章节编号：{chapter_id}

原始 plot：
{original_plot}

角色设定：
{role_profiles}

本章对话：
{dialogue_lines}

# 输出格式如下（严格使用 JSON 返回）：
{{
  "updated_plot": "新的 plot（如无变化可与原 plot 一致）",
  "change_summary": "本次修改的原因说明，如：对话中卡尔背叛，与 plot 中描述不符，已更新。",
  "changed": true 或 false
}}
""".strip()
    
    response = generate_response([{"role": "user", "content": prompt}], model=model)
    return convert_json(response)