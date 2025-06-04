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


def convert_json(content):
    content = content.replace("，",",")
    if "```json" in content:
        return eval(
            content.split("```json")[1].split("```")[0])
    else:
        return eval(content)

def save_json(obj, folder,file_name):
    folder_path = os.path.join(output_dir,folder)
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def extract_plot_list(chapter_json_list):
    return [ch.get("plot", "") for ch in chapter_json_list]