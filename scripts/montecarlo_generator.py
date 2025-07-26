import os
import json
from typing import List
from src.main_pipeline import main as run_story_pipeline
from src.utils.utils import load_json

def normalize(s):
    return s.replace(" ", "").replace("：", "").replace(":", "").replace("/", "_")

def extract_anchor_and_behavior_info(base_dir: str):
    """
    从输出目录中提取 anchor 数量和角色状态统计信息
    """
    anchor_path = os.path.join(base_dir, "generated_anchors_dual_surface.json")
    role_state_path = os.path.join(base_dir, "role_state.json")
    anchor_count = 0
    avg_state_count = 0

    if os.path.exists(anchor_path):
        anchors = load_json(anchor_path).get("anchors", [])
        anchor_count = len(anchors)

    if os.path.exists(role_state_path):
        state_data = load_json(role_state_path)
        total, count = 0, 0
        for chapter in state_data.values():
            for states in chapter.values():
                total += len(states)
                count += 1
        if count > 0:
            avg_state_count = round(total / count, 2)

    return anchor_count, avg_state_count

def run_montecarlo_generation_v2(
    topic: str,
    style: str,
    temperature_list: List[float] = [0.3, 0.7, 1.0],
    base_version_prefix="monte",
    output_root="output",
    log_path="sampling_log.json"
):
    """
    运行多轮采样，记录结构锚点与角色状态信息
    """
    sampling_log = []
    for temp in temperature_list:
        version = f"{base_version_prefix}_{normalize(topic)}_T{str(temp).replace('.', '')}"
        print(f"\n🌡️ Generating: topic={topic}, style={style}, temperature={temp} → version: {version}")

        # 调用主流程
        run_story_pipeline(
            version=version,
            reorder_mode="linear",
            use_cache=False,
            topic=topic,
            style=style,
            behavior_model="claude-sonnet-4-20250514"
        )

        # 提取锚点与状态信息
        output_dir = os.path.join(output_root, version)
        anchor_count, avg_state_count = extract_anchor_and_behavior_info(output_dir)

        sampling_log.append({
            "version": version,
            "temperature": temp,
            "topic": topic,
            "style": style,
            "anchor_count": anchor_count,
            "avg_states_per_role": avg_state_count
        })

    # 保存采样记录日志
    os.makedirs(output_root, exist_ok=True)
    log_file = os.path.join(output_root, log_path)
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(sampling_log, f, ensure_ascii=False, indent=2)
    print(f"\n所有版本生成完成，采样日志已保存至 {log_file}")


# ✅ 示例使用（可注释）
if __name__ == "__main__":
    run_montecarlo_generation_v2(
        topic="灰姑娘",
        style="奇幻童话",
        temperature_list=[0.3, 0.7, 1.0]
    )

