import os
import json
from typing import List, Dict
from main_pipeline import main as run_story_pipeline
# 引入你已有的 main_pipeline 主函数


def normalize_name(s):
    return s.replace(" ", "").replace("：", "").replace(":", "").replace("/", "_")

def run_multi_task(task_list: List[Dict], base_version_prefix="batch", reorder="sequential"):
    for idx, task in enumerate(task_list):
        topic = task["topic"]
        style = task["style"]
        version = f"{base_version_prefix}_{normalize_name(topic)}_{normalize_name(style)}"

        print(f"\n==============================")
        print(f"正在生成第 {idx+1}/{len(task_list)} 个任务：{topic} / {style}")
        print(f"输出版本目录: output/{version}")
        print(f"==============================")

        run_story_pipeline(
            version=version,
            reorder_mode=reorder,
            use_cache=False,
            topic=topic,
            style=style,
            behavior_model="gpt-4o"
        )

def load_task_file(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    task_file_path = "data/tasks.json"
    if os.path.exists(task_file_path):
        task_list = load_task_file(task_file_path)
        run_multi_task(task_list, base_version_prefix="exp")
    else:
        print("未找到任务文件 tasks.json")


    # {"topic": "三只小猪", "style": "寓言故事"},
    # {"topic": "丑小鸭", "style": "成长故事"},
    # {"topic": "睡美人", "style": "奇幻爱情"},
    # {"topic": "海的女儿", "style": "悲剧爱情"},
    # {"topic": "卖火柴的小女孩", "style": "感人故事"},
    # {"topic": "小王子", "style": "哲理童话"},
    # {"topic": "彼得潘", "style": "奇幻冒险"},
    # {"topic": "木偶奇遇记", "style": "成长冒险"},
    # {"topic": "青蛙与公主", "style": "爱情童话"},
    # {"topic": "三个小猪", "style": "寓言"},