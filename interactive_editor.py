import os
import json
from src.constant import output_dir
from src.utils.utils import load_json, convert_json
from src.dialogue_agent import DialogueAgent


def load_story_and_characters(version="test", chapter_id=0):
    characters = load_json(os.path.join(output_dir, version, "characters.json"))
    story = load_json(os.path.join(output_dir, version, "story.json"))[chapter_id]
    return story, characters

def build_agents(story, characters):
    agents = []
    for name in story["characters"]:
        speaker_info = next(c for c in characters if c["name"] == name)
        agents.append(DialogueAgent(
            name=name,
            speaker_info=speaker_info,
            plot=story["plot"],
            scene=story["scene"]
        ))
    return agents

def handler_each_plot_manual(story, agents):
    plot = story["plot"]
    sentences = [s.strip() for s in plot.split("。") if s]
    run_history = []

    for idx, sentence in enumerate(sentences, 1):
        print(f"\n🎬 第 {idx} 句：{sentence}")

        choice = input("是否需要说话？(1=是, 0=跳过): ")
        if choice.strip() != "1":
            continue

        actor = input("选择发言角色名: ")
        mode = input("选择发言模式（dialogue / monologue）: ")

        agent = next(a for a in agents if a.name == actor)
        response = agent.send(sentence=sentence, mode=mode)
        print(f"{actor} ({mode}): {response['output']}")

        for other_agent in agents:
            other_agent.receive(response, mode, curr_speaker=actor)

        run_history.append({
            "scene": sentence,
            "actor": actor,
            "mode": mode,
            "output": response["output"],
            "action": response.get("action", "")
        })

    return run_history


if __name__ == "__main__":
    version = "test"
    chapter_id = 0  # 未来可以支持输入选章节

    story, characters = load_story_and_characters(version, chapter_id)
    agents = build_agents(story, characters)

    results = handler_each_plot_manual(story, agents)

    # 可保存为 json/markdown
    save_path = os.path.join(output_dir, version, f"manual_dialogue_chapter{chapter_id}.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n已保存人工对话结果至：{save_path}")
