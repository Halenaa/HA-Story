# src/compile_story.py
import os
from src.utils import load_json, save_json
from src.constant import output_dir

def compile_full_story_by_chapter(story_json, dialogue_json):
    full_story = ""

    for idx, chapter in enumerate(story_json):
        title = f"# 第 {idx+1} 章：{chapter.get('scene', f'场景{idx+1}')}"
        plot = chapter["plot"]

        # 找对应 dialogue（根据 sentence 精确匹配）
        matched = next((d for d in dialogue_json if d["sentence"].strip() == plot.strip()), None)

        story_text = plot.strip()

        if matched and matched["need_to_action"] == 1 and matched["dialogue"]:
            # 拼入自然语言对话
            for speaker, lines in matched["dialogue"].items():
                for line in lines:
                    if ":" in line:
                        role, content = line.split(":", 1)
                        story_text += f"\n\n“{content.strip()}” {role.strip()}说。"
                    else:
                        story_text += f"\n\n{line.strip()}"

        # 拼成章节段落
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

    print(f"故事小说已生成：{base_dir}/novel_story.md")
