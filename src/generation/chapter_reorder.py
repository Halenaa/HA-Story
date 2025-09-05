import json
import os
from src.utils.utils import generate_response
from src.constant import output_dir


def build_prompt_from_ordered_chapters(ordered_chapters):
    outline = "\n".join([f"- {item['chapter_id']}：{item['title']}" for item in ordered_chapters])
    return f"""
你是一位擅长非线性叙事结构的编剧。

以下是故事的章节标题清单，目前是线性顺序（从 Chapter 1 到 Chapter N）：

{outline}

请你重新安排这些章节的讲述顺序（可以采用插叙、倒叙、交叉叙事等手法），使故事更有张力。

输出格式为 JSON 列表，包含如下字段：
- chapter_id
- title
- new_order（从 1 开始编号）

格式示例如下：
[
  {{"chapter_id": "Chapter 6", "title": "天空城堡的挑战", "new_order": 1}},
  {{"chapter_id": "Chapter 2", "title": "精灵的指引", "new_order": 2}},
  ...
]

请仅返回标准 JSON，不要加入解释说明。
`new_order` 的顺序必须与原顺序不同。
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
            print("非线性重排失败，返回原始顺序")
            return chapter_list

        # 按 new_order 排序
        reordered = sorted(reordered, key=lambda x: x["new_order"])
        return reordered

    else:
        raise ValueError("顺序模式必须为 'linear' 或 'nonlinear'")


if __name__ == "__main__":
    test_file = os.path.join(output_dir, "test", "test_outline.json")
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    reorder_result = reorder_chapters(data, mode="nonlinear")
    print(json.dumps(reorder_result, ensure_ascii=False, indent=2))
