# src/compile_story.py
import os
from src.utils.utils import load_json, save_json
from src.constant import output_dir

def compile_full_story_by_chapter(story_json, dialogue_json):
    full_story = ""

    for idx, chapter in enumerate(story_json):
        title = f"# 第 {idx+1} 章：{chapter.get('scene', f'场景{idx+1}')}"
        plot = chapter.get("plot", "").strip()

        # 找对应 dialogue（根据 sentence 匹配）
        matched = next((d for d in dialogue_json if d.get("sentence", "").strip() == plot), None)

        story_text = plot

        if matched and matched.get("dialogue"):
            if isinstance(matched["dialogue"], dict):
                for speaker, lines in matched["dialogue"].items():
                    for line in lines:
                        story_text += f"\n\n“{line.strip()}” {speaker.strip()}说。"
            elif isinstance(matched["dialogue"], list):
                for line in matched["dialogue"]:
                    story_text += f"\n\n“{line['line'].strip()}” {line['speaker'].strip()}说。"

        full_story += f"{title}\n\n{story_text}\n\n{'-'*50}\n\n"

    return full_story


if __name__ == "__main__":
    version = "test"
    base_dir = os.path.join(output_dir, version)
    
    story_json = load_json(os.path.join(base_dir, "story.json"))
    dialogue_json = load_json(os.path.join(base_dir, "dialogue_marks.json"))

    novel = compile_full_story_by_chapter(story_json, dialogue_json)

    with open(os.path.join(base_dir, "novel_story.md"), "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"故事小说已生成：{base_dir}/original_novel_story.md")
