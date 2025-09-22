#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Fairy Tale Generator - Generate and Save as MD File
"""

import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_KEY"), 
    base_url=os.getenv("OPENAI_API_BASE")
)

def generate_fairy():
    """Generate fairy tale and save as MD file"""
    prompt = """You are an excellent writer. Please use your writing skills to help me rewrite a new excellent fairy tale based on the following requirements: 
1. The theme is Little Red Riding Hood 
2. No restrictions on rewriting style and narrative approach 
3. Must include character dialogues 
4. Word count requirement: 7000-7500 words
5. Please generate the COMPLETE story in one response, do not ask for continuation
6. Structure the story with chapter headings like # Chapter 1:, # Chapter 2:, etc.
7. Make sure to tell a full, complete story from beginning to end

Please generate the complete English version of the story now:"""
    
    print("Generating fairy tale...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000
        )
        
        story = response.choices[0].message.content
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"baseline_{timestamp}.md"
        
        # Save as MD file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Baseline Story - {timestamp}\n\n")
            f.write(story)
        
        print(f"Story saved to: {filename}")
        
        return story
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return None

if __name__ == "__main__":
    generate_fairy()
