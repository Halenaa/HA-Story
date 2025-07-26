# logger.py
import os
import json
import datetime

def init_log_path(base_dir, log_type):
    """初始化日志路径"""
    os.makedirs(os.path.join(base_dir, "logs"), exist_ok=True)
    log_path = os.path.join(base_dir, "logs", f"{log_type}_log.jsonl")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            pass  # 创建空文件
    return log_path

def append_log(log_path, record):
    """追加日志记录到文件中，每条一行 JSON"""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def build_log_record(
    module,
    step,
    task_name,
    chapter_id,
    model,
    input_data,
    output_data,
    temperature,
    seed,
    prompt_type=None,
    prompt_style=None
):
    """构建标准化日志记录字典"""
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "module": module,
        "step": step,
        "task": task_name,
        "chapter_id": chapter_id,
        "model": model,
        "prompt_type": prompt_type,
        "prompt_style": prompt_style,
        "temperature": temperature,
        "seed": seed,
        "input": input_data,
        "output": output_data
    }

def build_simple_log(module, task_name, input_data, output_data):
    """适用于 polish / enhance / behavior-trace 等无章节 ID 的日志"""
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "module": module,
        "task": task_name,
        "input": input_data,
        "output": output_data
    }
