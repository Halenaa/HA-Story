import os
from src.utils.utils import load_json, save_json
from src.constant import output_dir

def compile_full_story_by_chapter(story_json, dialogue_json):
    full_story = ""

    for idx, chapter in enumerate(story_json):
        chapter_id = chapter.get("chapter_id", f"第{idx+1}章")
        title = chapter.get("title", f"场景{idx+1}")
        plot = chapter.get("plot", "").strip()

        full_story += f"# {chapter_id}：{title}\n\n"
        full_story += plot + "\n\n"

        # 拼接对应章节对白（按 index 匹配）
        if idx < len(dialogue_json):
            dlg_block = dialogue_json[idx].get("dialogue", [])
            for line in dlg_block:
                if isinstance(line, dict) and "speaker" in line and "line" in line:
                    full_story += f'“{line["line"].strip()}” ——{line["speaker"].strip()}\n\n'
                elif isinstance(line, str):
                    full_story += line.strip() + "\n\n"
                else:
                    print(f"⚠️ 无法识别的对话格式：{line}")

        full_story += "-" * 40 + "\n\n"

    return full_story


if __name__ == "__main__":
    version = "test"
    base_dir = os.path.join(output_dir, version)

    story_json = load_json(os.path.join(base_dir, "story.json"))
    dialogue_json = load_json(os.path.join(base_dir, "dialogue_marks.json"))

    novel = compile_full_story_by_chapter(story_json, dialogue_json)

    with open(os.path.join(base_dir, "novel_story.md"), "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"故事小说已生成：{base_dir}/novel_story.md")
