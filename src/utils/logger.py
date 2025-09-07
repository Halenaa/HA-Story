# logger.py
import os
import json
import datetime

def init_log_path(base_dir, log_type):
    """Initialize log path"""
    os.makedirs(os.path.join(base_dir, "logs"), exist_ok=True)
    log_path = os.path.join(base_dir, "logs", f"{log_type}_log.jsonl")
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            pass  # Create empty file
    return log_path

def append_log(log_path, record):
    """Append log record to file, one JSON per line"""
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
    """Build standardized log record dictionary"""
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
    """Applicable for logs without chapter ID like polish / enhance / behavior-trace"""
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "module": module,
        "task": task_name,
        "input": input_data,
        "output": output_data
    }
