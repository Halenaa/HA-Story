#!/usr/bin/env python3
"""
分析故事的具体性 vs 抽象性
检测是否缺乏具体事件和行动
"""

import json
import re
from pathlib import Path

def analyze_story_concreteness(story_data):
    """分析故事的具体性程度"""
    
    # 情感词汇模式
    emotion_patterns = [
        r'\b(felt|feeling|emotion|heart|soul|spirit)\b',
        r'\b(trembling|shiver|ache|yearning|longing|dread|hope|fear|anxiety|wonder)\b', 
        r'\b(uncertain|unsure|hesitant|wary|anxious|nervous|conflicted)\b',
        r'\b(memory|remember|thought|mind|consciousness|awareness)\b',
        r'\b(gentle|tender|soft|warm|cold|harsh|bitter|sweet)\b'
    ]
    
    # 具体行动词汇模式
    action_patterns = [
        r'\b(ran|walked|flew|swam|jumped|climbed|fell|grabbed|threw|hit|kicked)\b',
        r'\b(opened|closed|broke|built|created|destroyed|attacked|defended)\b',
        r'\b(said|shouted|whispered|called|announced|declared|argued|questioned)\b',
        r'\b(ate|drank|slept|woke|arrived|left|entered|exited|moved|stopped)\b',
        r'\b(picked|dropped|carried|pushed|pulled|lifted|placed|removed)\b'
    ]
    
    # 具体对象/地点模式
    concrete_patterns = [
        r'\b(door|window|tree|rock|bridge|path|road|house|building)\b',
        r'\b(food|bread|water|fire|sword|stick|rope|bag|box|key)\b',
        r'\b(morning|noon|evening|yesterday|tomorrow|hour|minute|day)\b'
    ]
    
    results = {
        'total_chapters': len(story_data),
        'chapters_analysis': [],
        'overall_stats': {
            'total_sentences': 0,
            'emotion_heavy_sentences': 0,
            'action_sentences': 0,
            'concrete_sentences': 0,
            'abstract_ratio': 0,
            'concrete_ratio': 0
        }
    }
    
    for chapter in story_data:
        plot = chapter.get('plot', '')
        chapter_title = chapter.get('title', 'Unknown')
        
        # 分句分析
        sentences = re.split(r'[.!?]+', plot)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chapter_stats = {
            'title': chapter_title,
            'total_sentences': len(sentences),
            'emotion_sentences': 0,
            'action_sentences': 0,
            'concrete_sentences': 0,
            'sample_emotion_sentences': [],
            'sample_action_sentences': [],
            'abstract_ratio': 0
        }
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # 检测情感/抽象内容
            emotion_match = any(re.search(pattern, sentence_lower) for pattern in emotion_patterns)
            if emotion_match:
                chapter_stats['emotion_sentences'] += 1
                if len(chapter_stats['sample_emotion_sentences']) < 2:
                    chapter_stats['sample_emotion_sentences'].append(sentence[:100] + '...')
            
            # 检测具体行动
            action_match = any(re.search(pattern, sentence_lower) for pattern in action_patterns)
            if action_match:
                chapter_stats['action_sentences'] += 1
                if len(chapter_stats['sample_action_sentences']) < 2:
                    chapter_stats['sample_action_sentences'].append(sentence[:100] + '...')
            
            # 检测具体对象/细节
            concrete_match = any(re.search(pattern, sentence_lower) for pattern in concrete_patterns)
            if concrete_match:
                chapter_stats['concrete_sentences'] += 1
        
        # 计算抽象比例
        if chapter_stats['total_sentences'] > 0:
            chapter_stats['abstract_ratio'] = chapter_stats['emotion_sentences'] / chapter_stats['total_sentences']
        
        results['chapters_analysis'].append(chapter_stats)
        
        # 更新总体统计
        results['overall_stats']['total_sentences'] += chapter_stats['total_sentences']
        results['overall_stats']['emotion_heavy_sentences'] += chapter_stats['emotion_sentences']
        results['overall_stats']['action_sentences'] += chapter_stats['action_sentences']
        results['overall_stats']['concrete_sentences'] += chapter_stats['concrete_sentences']
    
    # 计算总体比例
    total_sentences = results['overall_stats']['total_sentences']
    if total_sentences > 0:
        results['overall_stats']['abstract_ratio'] = results['overall_stats']['emotion_heavy_sentences'] / total_sentences
        results['overall_stats']['concrete_ratio'] = results['overall_stats']['action_sentences'] / total_sentences
    
    return results

def print_concreteness_analysis(results):
    """打印具体性分析结果"""
    
    print("📊 故事具体性分析报告")
    print("=" * 50)
    
    stats = results['overall_stats']
    print(f"📝 总体统计:")
    print(f"   总句数: {stats['total_sentences']}")
    print(f"   情感描述句: {stats['emotion_heavy_sentences']} ({stats['abstract_ratio']:.1%})")
    print(f"   具体行动句: {stats['action_sentences']} ({stats['concrete_ratio']:.1%})")
    print(f"   具体细节句: {stats['concrete_sentences']}")
    
    print(f"\n🎯 问题严重程度判定:")
    if stats['abstract_ratio'] > 0.7:
        print("   🔴 严重问题：过度情感化，缺乏具体事件")
    elif stats['abstract_ratio'] > 0.5:
        print("   🟡 中等问题：情感描述过多，需要更多具体行动") 
    elif stats['abstract_ratio'] > 0.3:
        print("   🟢 轻微问题：情感与行动平衡较好")
    else:
        print("   ✅ 良好：具体事件丰富")
    
    print(f"\n📋 各章节分析:")
    for i, chapter in enumerate(results['chapters_analysis'], 1):
        print(f"\n章节 {i}: {chapter['title']}")
        print(f"   抽象比例: {chapter['abstract_ratio']:.1%}")
        print(f"   情感句/行动句: {chapter['emotion_sentences']}/{chapter['action_sentences']}")
        
        if chapter['sample_emotion_sentences']:
            print(f"   情感描述样例:")
            for sample in chapter['sample_emotion_sentences']:
                print(f"     • {sample}")
        
        if chapter['sample_action_sentences']:
            print(f"   具体行动样例:")
            for sample in chapter['sample_action_sentences']:
                print(f"     • {sample}")

def main():
    """主分析函数"""
    experiment_dir = Path("data/output/theuglyduckling_abo_nonlinear_T0.7_s2")
    story_file = experiment_dir / "story_updated.json"
    
    if not story_file.exists():
        print(f"❌ 故事文件不存在: {story_file}")
        return
    
    with open(story_file, 'r', encoding='utf-8') as f:
        story_data = json.load(f)
    
    # 执行分析
    results = analyze_story_concreteness(story_data)
    
    # 打印结果
    print_concreteness_analysis(results)
    
    # 保存详细结果
    output_file = experiment_dir / "story_concreteness_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细分析结果已保存: {output_file}")

if __name__ == "__main__":
    main()
