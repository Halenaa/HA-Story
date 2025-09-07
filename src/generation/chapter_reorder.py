import json
import os
from src.utils.utils import generate_response
from src.constant import output_dir


def build_prompt_from_ordered_chapters(ordered_chapters):
    outline = "\n".join([f"- {item['chapter_id']}：{item['title']}" for item in ordered_chapters])
    return f"""
You are a screenwriter skilled in non-linear narrative structures.

Below is the chapter title list of the story, currently in linear order (from Chapter 1 to Chapter N):

{outline}

Please rearrange the narrative order of these chapters (you can use interpolation, flashback, cross-narrative and other techniques) to make the story more compelling.

The output format is a JSON list containing the following fields:
- chapter_id
- title
- new_order (numbered from 1)

Format example:
[
  {{"chapter_id": "Chapter 6", "title": "Sky Castle Challenge", "new_order": 1}},
  {{"chapter_id": "Chapter 2", "title": "Elf's Guidance", "new_order": 2}},
  ...
]

Please return only standard JSON, do not add explanations.
The order of `new_order` must be different from the original order.
    """


def reorder_chapters(chapter_list, mode="linear", model="gpt-4.1", performance_analyzer=None):
    if mode == "linear":
        return chapter_list

    elif mode == "nonlinear":
        prompt = build_prompt_from_ordered_chapters(chapter_list)
        response = generate_response([{"role": "user", "content": prompt}], model=model, performance_analyzer=performance_analyzer, stage_name="chapter_reorder")
        try:
            reordered = json.loads(response)
        except Exception as e:
            print("Non-linear reordering failed, returning original order")
            return chapter_list

        # Sort by new_order
        reordered = sorted(reordered, key=lambda x: x["new_order"])
        return reordered

    else:
        raise ValueError("Order mode must be 'linear' or 'nonlinear'")


if __name__ == "__main__":
    test_file = os.path.join(output_dir, "test", "test_outline.json")
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    reorder_result = reorder_chapters(data, mode="nonlinear")
    print(json.dumps(reorder_result, ensure_ascii=False, indent=2))
