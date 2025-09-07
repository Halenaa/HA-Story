#!/usr/bin/env python3
"""
超简单基线生成器 - 只用一句话提示词
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime

# 导入LLM
from glm_llm import LLMCall

def generate_simple_baseline(topic="Little Red Riding Hood", temperature=0.7, seed=1):
    """最简单的基线：一句话生成完整故事"""
    
    # 超简单的提示词
    prompt = f"Generate a complete story about {topic}."
    
    print(f"📝 Baseline: {topic} (T{temperature}, s{seed})")
    print(f"💭 Prompt: {prompt}")
    
    start_time = time.time()
    
    try:
        llm_call = LLMCall()
        story = llm_call.generate_response(
            prompt=prompt,
            temperature=temperature,
            seed=seed
        )
        
        generation_time = time.time() - start_time
        word_count = len(story.split())
        
        result = {
            "prompt": prompt,
            "story": story,
            "stats": {
                "temperature": temperature,
                "seed": seed, 
                "generation_time": generation_time,
                "word_count": word_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        print(f"✅ Generated: {word_count} words in {generation_time:.1f}s")
        return result
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def run_baseline_matrix():
    """运行基线实验矩阵"""
    print("🚀 Running Baseline Matrix")
    print("=" * 40)
    
    topic = "Little Red Riding Hood"
    temperatures = [0.3, 0.7, 0.9]
    seeds = [1, 2, 3]
    
    output_dir = Path("data/output/baseline_results")
    output_dir.mkdir(exist_ok=True)
    
    results = []
    
    for temp in temperatures:
        for seed in seeds:
            print(f"\n📝 T{temp}_s{seed}")
            result = generate_simple_baseline(topic, temp, seed)
            
            if result:
                # 保存结果
                filename = f"baseline_T{temp}_s{seed}.json"
                filepath = output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                # 保存纯文本版本
                text_file = output_dir / f"baseline_T{temp}_s{seed}.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(result['story'])
                
                results.append(result)
                print(f"💾 Saved: {filename}")
            
            time.sleep(1)  # 避免API限制
    
    print(f"\n✅ Generated {len(results)}/9 baseline stories")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Baseline Generator")
    parser.add_argument("--mode", choices=["single", "matrix"], default="single")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=1)
    
    args = parser.parse_args()
    
    if args.mode == "single":
        result = generate_simple_baseline(temperature=args.temperature, seed=args.seed)
        if result:
            output_dir = Path("data/output/baseline_results")
            output_dir.mkdir(exist_ok=True)
            
            filename = f"baseline_test_T{args.temperature}_s{args.seed}.txt"
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result['story'])
            print(f"💾 Saved: {filepath}")
    else:
        run_baseline_matrix()
