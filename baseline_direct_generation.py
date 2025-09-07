#!/usr/bin/env python3
"""
Baseline 1: 直接LLM生成完整故事
使用简单prompt "Generate a complete story about [topic]" 直接生成完整故事
用于与多步骤pipeline进行性能和质量比较
"""

import os
import json
import time
import argparse
from datetime import datetime
from src.utils.utils import generate_response, save_json, save_md
from src.constant import output_dir
from src.analysis.performance_analyzer import PerformanceAnalyzer


def create_baseline_prompt(topic, style):
    """创建baseline提示词"""
    if style and style.strip():
        return f"Generate a complete story about '{topic}' in the style of '{style}'. Write a full narrative story with multiple scenes, character development, dialogue, and a complete plot arc. The story should be engaging, well-structured, and include detailed descriptions of characters, settings, and events."
    else:
        return f"Generate a complete story about '{topic}'. Write a full narrative story with multiple scenes, character development, dialogue, and a complete plot arc. The story should be engaging, well-structured, and include detailed descriptions of characters, settings, and events."


def direct_story_generation(topic, style="", temperature=0.7, model="gpt-4.1", performance_analyzer=None):
    """直接生成完整故事"""
    
    # 创建简单的baseline prompt
    prompt = create_baseline_prompt(topic, style)
    
    print(f"使用prompt: {prompt[:100]}...")
    
    # 调用LLM生成故事
    messages = [{"role": "user", "content": prompt}]
    
    # 记录开始时间
    start_time = time.time()
    
    # 生成故事
    story_content = generate_response(
        messages, 
        model=model, 
        temperature=temperature,
        performance_analyzer=performance_analyzer,
        stage_name="direct_generation" if performance_analyzer else None
    )
    
    # 记录结束时间
    generation_time = time.time() - start_time
    
    return {
        "story": story_content,
        "generation_time": generation_time,
        "prompt": prompt,
        "model": model,
        "temperature": temperature
    }


def run_baseline_experiment(
    topics_and_styles=None,
    temperature=0.7, 
    model="gpt-4.1",
    seed=1,
    output_prefix="baseline1"
):
    """运行baseline实验"""
    
    # 默认测试topics（与主项目保持一致）
    if topics_and_styles is None:
        topics_and_styles = [
            {"topic": "Little Red Riding Hood", "style": "Sci-fi rewrite"},
            {"topic": "灰姑娘", "style": "现代改写"},
            {"topic": "青蛙王子", "style": "ABO恋爱"},
            {"topic": "小红帽", "style": "科幻改写"},
            {"topic": "白雪公主", "style": "军事改写"},
            {"topic": "Chang'e's flight to the moon", "style": "magic"}
        ]
    
    print(f"开始Baseline实验 - 直接LLM生成")
    print(f"模型: {model}, 温度: {temperature}, 种子: {seed}")
    print(f"测试 {len(topics_and_styles)} 个topic")
    print()
    
    results = []
    
    for i, item in enumerate(topics_and_styles):
        topic = item["topic"]
        style = item.get("style", "")
        
        print(f"[{i+1}/{len(topics_and_styles)}] 生成故事: {topic} ({style})")
        
        # 创建版本名称
        topic_clean = topic.lower().replace(" ", "").replace("'", "")
        style_clean = style.lower().replace(" ", "").replace("-", "") if style else "nostyle"
        version_name = f"{output_prefix}_{topic_clean}_{style_clean}_T{temperature}_s{seed}"
        
        # 创建输出目录
        output_folder = os.path.join(output_dir, version_name)
        os.makedirs(output_folder, exist_ok=True)
        
        # 初始化性能分析器
        experiment_config = {
            'baseline_type': 'direct_generation',
            'topic': topic,
            'style': style,
            'temperature': temperature,
            'seed': seed,
            'model': model,
            'method': 'single_prompt'
        }
        
        performance_analyzer = PerformanceAnalyzer(
            task_name=version_name,
            experiment_config=experiment_config
        )
        performance_analyzer.start_total_timing()
        performance_analyzer.start_stage("direct_generation", {
            "topic": topic, 
            "style": style, 
            "method": "single_prompt"
        })
        
        try:
            # 生成故事
            result = direct_story_generation(
                topic=topic,
                style=style,
                temperature=temperature,
                model=model,
                performance_analyzer=performance_analyzer
            )
            
            # 结束阶段记录
            performance_analyzer.end_stage("direct_generation", {
                "story_length": len(result["story"]),
                "success": True
            })
            
            # 保存结果
            result_data = {
                "version": version_name,
                "topic": topic,
                "style": style,
                "model": model,
                "temperature": temperature,
                "seed": seed,
                "timestamp": datetime.now().isoformat(),
                "story_content": result["story"],
                "prompt_used": result["prompt"],
                "generation_time": result["generation_time"],
                "method": "direct_llm_generation"
            }
            
            # 保存JSON格式
            save_json(result_data, version_name, "baseline_result.json")
            
            # 保存Markdown格式的故事
            story_md = f"# {topic}\n\n**Style:** {style}\n**Generated by:** Baseline Direct LLM\n**Model:** {model}\n**Temperature:** {temperature}\n\n---\n\n{result['story']}"
            save_md(story_md, os.path.join(output_folder, "story.md"))
            
            # 进行简单的文本分析
            word_count = len(result["story"].split())
            char_count = len(result["story"])
            lines_count = len(result["story"].split('\n'))
            
            # 分析文本特征
            performance_analyzer.analyze_text_features(
                story_data=[{"plot": result["story"]}],  # 简化格式以适配分析器
                dialogue_data=[],
                characters_data=[]
            )
            
            # 保存性能分析报告
            performance_report_path = performance_analyzer.save_report(
                output_folder, 
                f"performance_analysis_{version_name}.json"
            )
            
            # 记录结果
            experiment_result = {
                "version": version_name,
                "topic": topic,
                "style": style,
                "success": True,
                "story_length": len(result["story"]),
                "word_count": word_count,
                "generation_time": result["generation_time"],
                "output_folder": output_folder,
                "performance_report": performance_report_path
            }
            
            results.append(experiment_result)
            
            # 显示统计信息
            total_time = performance_analyzer.get_total_time()
            print(f"   ✓ 完成生成 ({len(result['story'])} 字符, {word_count} 词)")
            print(f"   ⏱️ 生成时间: {result['generation_time']:.2f}秒")
            print(f"   💰 API成本: ${performance_analyzer.total_api_cost:.4f}")
            print(f"   📊 Token数: {performance_analyzer.total_tokens:,}")
            print()
            
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            experiment_result = {
                "version": version_name,
                "topic": topic,
                "style": style,
                "success": False,
                "error": str(e),
                "output_folder": output_folder
            }
            results.append(experiment_result)
        
        # 避免API限流
        time.sleep(1)
    
    # 保存实验总结
    experiment_summary = {
        "baseline_type": "direct_llm_generation",
        "experiment_timestamp": datetime.now().isoformat(),
        "model": model,
        "temperature": temperature,
        "seed": seed,
        "total_topics": len(topics_and_styles),
        "successful_generations": len([r for r in results if r["success"]]),
        "failed_generations": len([r for r in results if not r["success"]]),
        "results": results
    }
    
    summary_path = os.path.join(output_dir, f"{output_prefix}_experiment_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(experiment_summary, f, ensure_ascii=False, indent=2)
    
    print("="*50)
    print("Baseline实验完成!")
    print(f"总计: {len(topics_and_styles)} 个topics")
    print(f"成功: {experiment_summary['successful_generations']} 个")
    print(f"失败: {experiment_summary['failed_generations']} 个")
    print(f"实验总结保存至: {summary_path}")
    print("="*50)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Baseline 1: 直接LLM生成完整故事")
    parser.add_argument("--model", type=str, default="gpt-4.1", help="使用的LLM模型")
    parser.add_argument("--temperature", type=float, default=0.7, help="生成温度")
    parser.add_argument("--seed", type=int, default=1, help="随机种子")
    parser.add_argument("--topic", type=str, help="单个topic测试")
    parser.add_argument("--style", type=str, default="", help="故事风格")
    parser.add_argument("--output-prefix", type=str, default="baseline1", help="输出前缀")
    
    args = parser.parse_args()
    
    # 如果指定了单个topic，只测试该topic
    if args.topic:
        topics_and_styles = [{"topic": args.topic, "style": args.style}]
    else:
        topics_and_styles = None  # 使用默认的topics列表
    
    # 运行实验
    results = run_baseline_experiment(
        topics_and_styles=topics_and_styles,
        temperature=args.temperature,
        model=args.model,
        seed=args.seed,
        output_prefix=args.output_prefix
    )
    
    return results


if __name__ == "__main__":
    main()
