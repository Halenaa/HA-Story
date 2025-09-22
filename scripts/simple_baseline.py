#!/usr/bin/env python3
"""
最简单的故事生成器 - 输入提示词直接生成
"""

import time
import os
from datetime import datetime
from src.utils.utils import generate_response

def generate_story(prompt):
    """根据提示词生成故事"""
    print(f"💭 提示词: {prompt}")
    print("🔄 生成中...")
    
    start_time = time.time()
    
    try:
        messages = [{"role": "user", "content": prompt}]
        story = generate_response(messages, model="gpt-4.1")
        
        generation_time = time.time() - start_time
        word_count = len(story.split())
        
        print(f"✅ 完成！生成了 {word_count} 词，耗时 {generation_time:.1f}秒")
        print("\n📖 生成的故事：")
        print("-" * 50)
        print(story)
        print("-" * 50)
        
        # 保存到文件
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"story_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"生成时间: {datetime.now().isoformat()}\n")
            f.write(f"提示词: {prompt}\n")
            f.write(f"字数: {word_count}\n")
            f.write(f"生成时间: {generation_time:.1f}秒\n")
            f.write("-" * 80 + "\n\n")
            f.write(story)
        
        print(f"\n💾 故事已保存到: {filepath}")
        
        return story
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return None

if __name__ == "__main__":
    prompt = """You are a writer. Write a complete any version of Little Red Riding Hood. Begin immediately and write the full story with detailed descriptions, dialogue, and scenes. Write at least 3000-5000 words. 

Start now:
"""
    
    generate_story(prompt)
