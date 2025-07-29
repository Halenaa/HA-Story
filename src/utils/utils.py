import os
import re
import json
import ast
from openai import OpenAI
import anthropic
from src.constant import output_dir
from dotenv import load_dotenv
load_dotenv()



client = OpenAI(api_key=os.getenv("OPENAI_KEY"), base_url=os.getenv("OPENAI_API_BASE"),
)




def generate_response(msg,model="gpt-4.1"):
    response = client.chat.completions.create(model=model,
                                messages=msg,temperature=0.1,)
    return response.choices[0].message.content

def convert_dialogue_dict_to_list(dialogue_dict):
    """
    将 dict 格式的对白（{角色名: [对白字符串]}) 转为 list[dict] 格式
    ✅ 修改：使用 "dialogue" 字段，与 dialogue_inserter.py 核心模块保持一致
    """
    result = []
    for speaker, lines in dialogue_dict.items():
        for line in lines:
            # 去掉 "角色名: ..." 前缀（如有）
            if line.startswith(speaker + ":"):
                line = line[len(speaker)+1:].strip()
            result.append({"speaker": speaker, "dialogue": line})  # ✅ 使用 "dialogue" 字段
    return result

def extract_behavior_llm(dialogue_block, model="gpt-4.1", confirm=False):
    from src.utils.utils import generate_response

    # 整理对话为字符串（无论是 list 还是 dict）
    if isinstance(dialogue_block, dict):
        dialogue_items = []
        for speaker, lines in dialogue_block.items():
            for line in lines:
                dialogue_items.append(f"{speaker}: {line}")
    else:
        # ✅ 修复：兼容两种字段名：'dialogue' 和 'line'
        dialogue_items = []
        for d in dialogue_block:
            speaker = d.get('speaker', '')
            # ✅ 关键修复：先尝试 'dialogue'，再尝试 'line'
            content = d.get('dialogue', d.get('line', ''))
            dialogue_items.append(f"{speaker}: {content}")

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

    # ✅ 如果解析失败，返回空字典而不是让程序崩溃
    if not isinstance(result, dict):
        print(f"⚠️ extract_behavior_llm 解析失败，返回空结果")
        return {}

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

def fix_plot_illegal_quotes(content):
    """
    修复 plot 字符串中出现的非法未转义引号，比如："plot": "...“外婆”..."
    会把 plot 中的 "角色" → 『角色』
    """
    pattern = r'"plot"\s*:\s*"(.*?)"'
    matches = re.findall(pattern, content, re.DOTALL)
    if matches:
        plot_text = matches[0]
        fixed_plot = plot_text.replace('"', '“')  # 替换非法引号为中文引号
        content = re.sub(pattern, f'"plot": "{fixed_plot}"', content, count=1)
    return content

def convert_json(content):
    print(f"yuanshi content: {content}...")  # 打印前100个字符以便调试
    content = content.replace("，", ",").replace("。", ".")

    try:
        # 去除 Markdown 包裹
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        # 修复粘连 JSON 对象 {..}{..} 为 [{..},{..}]
        if re.search(r"}\s*{", content):
            content = "[" + re.sub(r"}\s*{", "},{", content) + "]"
        
        # ✅ 新增：修复粘连 JSON 数组 [...][...] 
        if re.search(r"\]\s*\[", content):
            # 找到第一个完整的JSON数组
            # 使用更智能的方法：计算括号平衡
            bracket_count = 0
            end_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i
                            break
            
            if end_pos > 0:
                # 只取第一个完整的JSON数组
                content = content[:end_pos + 1]
        
        # ✅ 提取第一个 JSON 结构（改进版）
        content = content.strip()
        if content.startswith("["):
            # 对于数组，使用括号平衡方法
            bracket_count = 0
            end_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i
                            break
            
            if end_pos > 0:
                json_text = content[:end_pos + 1]
                return json.loads(json_text)
        
        elif content.startswith("{"):
            # 对于对象，类似处理
            brace_count = 0
            end_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i
                            break
            
            if end_pos > 0:
                json_text = content[:end_pos + 1]
                return json.loads(json_text)

        # 尝试直接解析
        print(f"尝试直接解析 JSON: {content}...")
        return json.loads(content)

    except Exception as e:
        print(f"⚠️ convert_json 出错：{e}")
        print(f"🧾 内容片段（前200字）：{content[:200]}")
        return []  # 返回空列表而不是空字典，因为大多数情况期望列表
       
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

def split_plot_into_sentences(plot_text, min_length=2):
    """
    最佳实践版本：结合各种方法的优点
    """
    if not plot_text: 
        return []
    
    text = plot_text.strip()
    
    # 替换省略号
    text = text.replace("...", "〈ELLIPSIS〉")
    text = text.replace("……", "〈ELLIPSIS_CN〉")
    
    # 使用正则表达式找到所有句子
    # 贪婪匹配到标点符号为止
    pattern = r'.+?[.。!！?？;；]+'
    
    # 找到所有匹配的句子
    sentences = re.findall(pattern, text)
    
    # 检查是否有剩余的文本（没有标点结尾的）
    last_pos = 0
    for match in re.finditer(pattern, text):
        last_pos = match.end()
    
    if last_pos < len(text):
        remaining = text[last_pos:].strip()
        if remaining:
            sentences.append(remaining)
    
    # 处理结果
    result = []
    for sentence in sentences:
        # 还原省略号
        sentence = sentence.replace("〈ELLIPSIS〉", "...")
        sentence = sentence.replace("〈ELLIPSIS_CN〉", "……")
        sentence = sentence.strip()
        
        # 只过滤真正太短的（比如单个字符）
        if sentence and len(sentence) >= min_length:
            result.append(sentence)
    
    return result

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
    # 修复常见拼写错误
    content = content.replace('"peaker"', '"speaker"')

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        return json.loads(content)
    except Exception as e:
        print("convert_json_safe 出错：", e)
        return {}
