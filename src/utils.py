import os
import json
from openai import OpenAI

from src.constant import output_dir
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_KEY"), base_url="https://api.chatanywhere.com.cn/v1",
)


def generate_response(msg,model="gpt-4o"):
    response = client.chat.completions.create(model=model,
                                messages=msg,temperature=0.7,)
    return response.choices[0].message.content


# def convert_json(content):
#     content = content.replace("，",",")
#     if "```json" in content:
#         return eval(
#             content.split("```json")[1].split("```")[0])
#     else:
#         return eval(content)

def convert_json(content):
    """
    更稳妥的 JSON 解析：支持 ```json 包裹、自动剥离自然语言错误部分
    """
    content = content.replace("，",",")
    content = content.replace("。",".")
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

def extract_plot_list(chapter_json_list):
    return [ch.get("plot", "") for ch in chapter_json_list]

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
