import os
import json
from openai import OpenAI

from src.constant import output_dir
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_KEY"), base_url=os.getenv("OPENAI_API_BASE"),
)


def generate_response(msg,model="gpt-4o"):
    response = client.chat.completions.create(model=model,
                                messages=msg,temperature=0.7,)
    return response.choices[0].message.content

def convert_dialogue_dict_to_list(dialogue_dict):
    """
    将 dict 格式的对白（{角色名: [对白字符串]}) 转为 list[dict] 格式
    """
    result = []
    for speaker, lines in dialogue_dict.items():
        for line in lines:
            # 去掉 "角色名: ..." 前缀（如有）
            if line.startswith(speaker + ":"):
                line = line[len(speaker)+1:].strip()
            result.append({"speaker": speaker, "line": line})
    return result

def extract_behavior_llm(dialogue_block, model="gpt-4o", confirm=True):
    from src.utils.utils import generate_response

    # 整理对话为字符串（无论是 list 还是 dict）
    if isinstance(dialogue_block, dict):
        dialogue_items = []
        for speaker, lines in dialogue_block.items():
            for line in lines:
                dialogue_items.append(f"{speaker}: {line}")
    else:
        dialogue_items = [f"{d['speaker']}: {d['line']}" for d in dialogue_block]

    dialogue_text = "\n".join(dialogue_items)

    # 🔧 Prompt：让 LLM 返回 dict[str: list[str]] 格式
    prompt = f"""
你是一个叙事行为分析器。请阅读以下多轮角色对话，提取每个角色当前的关键行为状态（如：愤怒、背叛、冷静、反派、退缩等），并以 JSON 格式输出。

输出格式如下：
{{
  "角色A": ["状态1", "状态2"],
  "角色B": ["状态3"]
}}

请注意：状态要贴合每位角色的语言风格和行为暗示，不需要解释，只返回 JSON。
对话如下：
{dialogue_text}
"""

    response = generate_response([{"role": "user", "content": prompt}], model=model)

    # 结构化解析
    from src.utils.utils import convert_json
    result = convert_json(response)

    # 人工确认机制
    if confirm:
        print("\n 系统提取角色行为如下：")
        for role, states in result.items():
            print(f"- {role}: {', '.join(states)}")
        fix = input("是否要手动修改任何角色状态？（y/n）: ").strip().lower()
        if fix == 'y':
            for role in result:
                manual = input(f"请为 {role} 重新输入状态（用逗号分隔，留空跳过）: ").strip()
                if manual:
                    result[role] = [s.strip() for s in manual.split(",")]

    return result

def convert_json(content):
    """
    更稳妥的 JSON 解析：支持 ```json 包裹、自动剥离自然语言错误部分
    """
    content = content.replace("，",",")
    content = content.replace("。",".")
    content = content.replace("false", "False").replace("true", "True").replace("null", "None")

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        # 如果前面不是 markdown 包裹，而是直接输出一段 dict-like 内容
        if content.strip().startswith("{") or content.strip().startswith("["):
            return eval(content)
        else:
            # 报错前打印有问题的返回（可选）
            raise ValueError("LLM返回非结构化文本：" + content[:100])
    except Exception as e:
        print("convert_json 出错：", e)
        return {}
    
def save_json(obj, folder,file_name):
    folder_path = os.path.join(output_dir,folder)
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def save_json_absolute(obj, full_path):
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def extract_plot_list(chapter_json_list):
    return [ch.get("plot", "") for ch in chapter_json_list]

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_md(text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def convert_json_safe(content):
    """
    兼容 true/false/null 的 JSON 解析器（用于 LLM 返回）
    """
    import json
    content = content.replace("，", ",").replace("。", ".")
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        return json.loads(content)
    except Exception as e:
        print("convert_json_safe 出错：", e)
        return {}
