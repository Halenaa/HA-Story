# reorder_chapters 改编
import random
import json
import os

from src.utils import save_json
from src.constant import output_dir

def reorder_chapters(chapter_list, mode="sequential"):
    chapters = [{
        "original_index": i+1,
        "chapter_id": ch["chapter_id"],
        "title": ch["title"]
    } for i, ch in enumerate(chapter_list)]

    if mode == "sequential":
        ordered = chapters
    elif mode == "reverse":
        ordered = list(reversed(chapters))
    elif mode == "random":
        ordered = random.sample(chapters, len(chapters))
    else:
        raise ValueError("顺序模式应为：'sequential', 'reverse', 或 'random'")

    return ordered


if __name__ == "__main__":
    with open(os.path.join(output_dir,"test","test_reorder_outline.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    print("raw outline:",data)
    reorder_outline = reorder_chapters(data,"random")
    print("reorder_outline:", reorder_outline)

