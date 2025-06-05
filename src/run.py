# import os
# import json
# from src.generation.outline_generator import generate_outline
# from src.generation.chapter_reorder import reorder_chapters
# from src.generation.generate_characters import generate_characters_v1
# from src.generation.expand_story import expand_story_v1
# from src.generation.dialogue_inserter import analyze_dialogue_insertions, run_dialogue_insertion
# from src.generation.dialogue_inserter import apply_structure_to_generate_dialogue
# # from src.generation.insertion import analyze_dialogue_insertions
# from src.utils import save_json,extract_plot_list
# from src.constant import output_dir

# if __name__ == "__main__":
#     version = "test"
#     # outline = generate_outline()
#     # save_json(outline,version,"test_outline.json")
#     # print("GEN outline")
#     # reorder_outline = reorder_chapters(outline,"random")
#     # save_json(reorder_outline, version, "test_reorder_outline.json")
#     # print("GEN reorder_outline")
#     # characters = generate_characters_v1(reorder_outline)
#     # save_json(characters, version, "characters.json")
#     # print("GEN characters")
#     # story = expand_story_v1(reorder_outline, characters)
#     # save_json(story, version, "story.json")
#     # print("GEN story")
#     with open(os.path.join(output_dir,"test","characters.json"), "r", encoding="utf-8") as f:
#         characters = json.load(f)
#     with open(os.path.join(output_dir,"test","story.json"), "r", encoding="utf-8") as f:
#         story = json.load(f)

#     print("story",story)
#     plot_list = extract_plot_list(story)
#     print("plot_list", plot_list)
#     #初始化人物个性（根据characters里的描述）

#     #loop
#     #next speaker 根据每个句子和历史对话来判断当前要不要发言，如果发言的话角色是谁

#     structure_marks = analyze_dialogue_insertions(plot_list, characters)
#     save_json(structure_marks, version, "structure_marks.json")
#     # 能不能直接从 analyze_dialogue_insertions() 的结果继续生成对话  
    
#     dialogue_result = apply_structure_to_generate_dialogue(structure_marks, plot_list, characters)
#     save_json(dialogue_result, version, "dialogue_marks.json")

#     result = run_dialogue_insertion(plot_list, characters)
#     save_json(result, version, "dialogue_marks.json")



import json
from src.utils import save_json, load_json
from src.constant import output_dir
from src.generation.dialogue_inserter import apply_structure_to_generate_dialogue
from src.generation.dialogue_inserter import pretty_print_dialogue

if __name__ == "__main__":
    version = "test"

    # 加载文件
    with open(f"{output_dir}/{version}/characters.json", "r", encoding="utf-8") as f:
        characters = json.load(f)
    with open(f"{output_dir}/{version}/story.json", "r", encoding="utf-8") as f:
        story = json.load(f)
    with open(f"{output_dir}/{version}/structure_marks.json", "r", encoding="utf-8") as f:
        structure_marks = json.load(f)

    # 提取 plot_list（你之前的逻辑）
    plot_list = [item["plot"] for item in story]

    # 只用结构标记生成对话
    print("开始基于结构生成对话...")
    result = apply_structure_to_generate_dialogue(structure_marks, plot_list, characters)
    save_json(result, version, "dialogue_marks.json")

    pretty_print_dialogue(result)
    print("对话插入完成")
