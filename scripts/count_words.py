#!/usr/bin/env python3
import re

def count_words_like_word(text):
    if not text:
        return 0
    
    # remove markdown format tags
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # remove extra blank lines and spaces
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # split into words
    words = re.findall(r'\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\b', text)
    
    return len(words)

# read file
with open('/Users/haha/Story/data/sci_baseline.md', 'r', encoding='utf-8') as f:
    content = f.read()

word_count = count_words_like_word(content)
char_count = len(content)

print('file: sci_baseline.md')
print(f'total word count: {char_count:,}')
print(f'total english word count: {word_count:,}')
print(f'average words per line: {word_count/204:.1f}')
