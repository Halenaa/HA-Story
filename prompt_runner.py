import os
import json
import argparse
import subprocess
from datetime import datetime

PROMPT_FILE = "data/prompts.json"
OUTPUT_DIR = "output"
PIPELINE_SCRIPT = "main_pipeline.py"  # 如果你用的是 CLI 调用形式

def normalize_name(s):
    return s.replace(" ", "_").replace("：", "").replace(":", "").replace("/", "_")

def load_prompt_tasks(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_pipeline(task, model="gpt-4o", no_cache=True):
    version = f"prompt_{task['prompt_type']}_{normalize_name(task['id'])}"
    print(f"\n 运行任务: {task['id']} → version={version}")

    # CLI 方式运行主流程
    cmd = [
        "python", PIPELINE_SCRIPT,
        "--version", version,
        "--topic", task["topic"],
        "--style", task["style"],
        "--behavior-model", model,
    ]
    if no_cache:
        cmd.append("--no-cache")

    # 设置环境变量，传入 prompt
    env = os.environ.copy()
    env["CUSTOM_PROMPT"] = task["prompt"]

    # 执行子进程
    subprocess.run(cmd, env=env)

def run_all(model="gpt-4o", prompt_file=PROMPT_FILE):
    tasks = load_prompt_tasks(prompt_file)
    for task in tasks:
        run_pipeline(task, model=model)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4o", help="使用的LLM模型")
    parser.add_argument("--prompt-file", type=str, default=PROMPT_FILE, help="Prompt配置文件")
    args = parser.parse_args()

    run_all(model=args.model, prompt_file=args.prompt_file)
