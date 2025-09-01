# 待匹配 regenerate_dialogue_from_plot.py
import os
import json
from src.constant import output_dir
from src.utils.utils import load_json, save_json

def edit_plot_interactively(story):
    print("\n当前章节列表：")
    for idx, ch in enumerate(story):
        print(f"{idx+1}. {ch['chapter_id']} - {ch.get('title', '')}")

    idxs = input("\n请输入要修改的章节编号（可多个，用逗号分隔）: ").strip()
    idxs = [int(i.strip()) - 1 for i in idxs.split(",") if i.strip().isdigit()]

    for idx in idxs:
        print(f"\n当前 plot（第 {idx+1} 章）：")
        print(story[idx].get("plot", "")[:200] + "...")

        print("请输入新的 plot 内容（支持多行，空行结束）:")
        new_plot = ""
        while True:
            line = input()
            if line.strip() == "":
                break
            new_plot += line.strip() + " "
        story[idx]["plot"] = new_plot.strip()
        story[idx]["edited"] = True  # ✅ 标记为手动编辑
        print(f"第 {idx+1} 章已更新完成！")

    return story

def main():
    version = input("请输入版本名称（如 test 或 demo）：").strip()
    story_path = os.path.join(output_dir, version, "story.json")

    if not os.path.exists(story_path):
        print(f"未找到 {story_path}，请确认版本名是否正确")
        return

    story = load_json(story_path)
    updated_story = edit_plot_interactively(story)

    save_name = input("请输入保存文件名（默认: story_manual.json）: ").strip() or "story_manual.json"
    save_json(updated_story, version, save_name)
    print(f"\n修改后的 story 已保存为：{os.path.join(output_dir, version, save_name)}")

if __name__ == "__main__":
    main()
