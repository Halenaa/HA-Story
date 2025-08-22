import os
import json
from main_pipeline_glm import main as run_pipeline

topics = ["小红帽"]
reorder_modes = ["nonlinear"]
temperatures = [0.3]
seeds = [3]

log_file = "run_loop_status.json"
finished = set()

# 加载已完成记录
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f_log:
        finished = set(json.load(f_log))

# 总任务数
total = len(topics) * len(reorder_modes) * len(temperatures) * len(seeds)
count = 0

# 开始执行组合
for topic in topics:
    for order in reorder_modes:
        for temp in temperatures:
            for seed in seeds:
                task_key = f"{topic}_{order}_T{temp}_S{seed}"
                if task_key in finished:
                    count += 1
                    continue

                print(f"Running {task_key} ({count+1}/{total})")
                try:
                    run_pipeline(
                        version="test",
                        reorder_mode=order,
                        use_cache=False,
                        topic=topic,
                        style="科幻改写",
                        behavior_model="gpt-4.1",
                        temperature=temp,
                        seed=seed
                    )
                    finished.add(task_key)
                    with open(log_file, "w", encoding="utf-8") as f_log:
                        json.dump(sorted(finished), f_log, ensure_ascii=False, indent=2)
                    count += 1
                except Exception as e:
                    print(f"Error on {task_key}: {e}")
                    continue

print(f"实验执行完毕！共完成 {len(finished)} / {total} 个组合。")
