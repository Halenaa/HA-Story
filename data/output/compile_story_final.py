# compile_story_final.py

import os
import json
import re

def split_plot_sentences(text):
    """将剧情按句子分割（保留标点）"""
    parts = re.split(r'(。|！|？|\!|\?)', text)
    return ["".join(parts[i:i+2]).strip() for i in range(0, len(parts), 2) if parts[i].strip()]

def compile_story_with_dialogue(version="exp_青蛙王子_ABO改写"):
    base_path = f"./{version}"
    story_path = os.path.join(base_path, "story_updated.json")
    dialogue_path = os.path.join(base_path, "dialogue_updated.json")
    output_path = os.path.join(base_path, "full_story_compiled.md")

    # 读取 story
    with open(story_path, "r", encoding="utf-8") as f:
        story = json.load(f)

    # 读取 dialogue
    with open(dialogue_path, "r", encoding="utf-8") as f:
        dialogue_data = json.load(f)

    output_lines = []
    dlg_idx = 0

    for chapter_idx, chapter in enumerate(story):
        chapter_id = chapter.get("chapter_id", f"Chapter {chapter_idx+1}")
        title = chapter.get("title", f"无标题章节")
        plot = chapter.get("plot", "").strip()

        output_lines.append(f"# {chapter_id}：{title}\n")

        # 按句分割 plot 并逐句插入对白
        plot_sentences = split_plot_sentences(plot)
        for sent in plot_sentences:
            output_lines.append(sent)

            if dlg_idx < len(dialogue_data):
                dlg_block = dialogue_data[dlg_idx]
                dlg_idx += 1

                if dlg_block and isinstance(dlg_block.get("dialogue"), list):
                    for d in dlg_block["dialogue"]:
                        speaker = d.get("speaker", "").strip()
                        line = d.get("line", "").strip()
                        if speaker and line:
                            output_lines.append(f'{speaker}：“{line}”')

        output_lines.append("\n" + "-" * 40 + "\n")

    # 保存结果
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"✅ 已成功生成完整故事文件：{output_path}")

if __name__ == "__main__":
    compile_story_with_dialogue()
