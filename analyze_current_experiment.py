#!/usr/bin/env python3
"""
分析当前实验的剧情指标
基于现有数据进行分析
"""

import os
import json
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_role_state_complexity(role_state_data):
    """分析角色状态复杂度"""
    total_states = 0
    role_count = 0
    role_complexity = {}
    
    for chapter_id, roles in role_state_data.items():
        for role_name, states in roles.items():
            if role_name not in role_complexity:
                role_complexity[role_name] = []
            role_complexity[role_name].extend(states)
            total_states += len(states)
            
    role_count = len(role_complexity)
    
    # 计算每个角色的状态统计
    role_stats = {}
    for role_name, all_states in role_complexity.items():
        unique_states = len(set(all_states))
        total_appearances = len(all_states)
        role_stats[role_name] = {
            'unique_states': unique_states,
            'total_appearances': total_appearances,
            'state_diversity': unique_states / total_appearances if total_appearances > 0 else 0
        }
    
    return {
        'total_roles': role_count,
        'total_states': total_states,
        'avg_states_per_role': total_states / role_count if role_count > 0 else 0,
        'role_details': role_stats
    }

def analyze_behavior_trace(behavior_trace_data):
    """分析行为轨迹"""
    timeline = behavior_trace_data.get('timeline', [])
    character_arcs = behavior_trace_data.get('character_arcs', {})
    
    return {
        'total_behavior_records': len(timeline),
        'characters_with_behavior': len(character_arcs),
        'avg_behaviors_per_character': len(timeline) / len(character_arcs) if character_arcs else 0,
        'behavior_distribution': {
            char: len(arc) for char, arc in character_arcs.items()
        }
    }

def analyze_story_structure(story_data):
    """分析故事结构"""
    chapter_count = len(story_data)
    total_plot_length = sum(len(ch.get('plot', '')) for ch in story_data)
    avg_chapter_length = total_plot_length / chapter_count if chapter_count > 0 else 0
    
    # 分析字符组成
    total_chars = sum(len(ch.get('plot', '')) for ch in story_data)
    total_sentences = 0
    
    import re
    for ch in story_data:
        plot = ch.get('plot', '')
        sentences = re.split(r'[.!?]+', plot.strip())
        total_sentences += len([s for s in sentences if s.strip()])
    
    return {
        'chapter_count': chapter_count,
        'total_plot_chars': total_chars,
        'total_sentences': total_sentences,
        'avg_chapter_length': avg_chapter_length,
        'avg_sentence_length': total_chars / total_sentences if total_sentences > 0 else 0
    }

def analyze_dialogue_quality(dialogue_data):
    """分析对话质量"""
    total_dialogues = 0
    total_dialogue_chars = 0
    speakers = set()
    
    for item in dialogue_data:
        if isinstance(item, dict) and 'dialogue' in item:
            dialogues = item['dialogue']
            if isinstance(dialogues, list):
                for dialogue in dialogues:
                    if isinstance(dialogue, dict):
                        total_dialogues += 1
                        content = dialogue.get('dialogue', '')
                        total_dialogue_chars += len(content)
                        speaker = dialogue.get('speaker', '')
                        if speaker:
                            speakers.add(speaker)
    
    return {
        'total_dialogue_count': total_dialogues,
        'unique_speakers': len(speakers),
        'avg_dialogue_length': total_dialogue_chars / total_dialogues if total_dialogues > 0 else 0,
        'speakers_list': list(speakers)
    }

def main():
    """主分析函数"""
    experiment_dir = Path("data/output/theuglyduckling_abo_nonlinear_T0.7_s2")
    
    print(f"📊 分析实验: {experiment_dir.name}")
    print("=" * 50)
    
    analysis_results = {}
    
    # 1. 角色状态分析
    role_state_path = experiment_dir / "role_state.json"
    if role_state_path.exists():
        print("🎭 角色状态复杂度分析...")
        role_state_data = load_json(role_state_path)
        role_analysis = analyze_role_state_complexity(role_state_data)
        analysis_results['role_complexity'] = role_analysis
        
        print(f"   总角色数: {role_analysis['total_roles']}")
        print(f"   总状态数: {role_analysis['total_states']}")
        print(f"   平均状态/角色: {role_analysis['avg_states_per_role']:.2f}")
    
    # 2. 行为轨迹分析  
    behavior_trace_path = experiment_dir / "behavior_trace.json"
    if behavior_trace_path.exists():
        print("\n🎯 行为轨迹分析...")
        behavior_trace_data = load_json(behavior_trace_path)
        behavior_analysis = analyze_behavior_trace(behavior_trace_data)
        analysis_results['behavior_analysis'] = behavior_analysis
        
        print(f"   行为记录总数: {behavior_analysis['total_behavior_records']}")
        print(f"   有行为的角色: {behavior_analysis['characters_with_behavior']}")
        print(f"   平均行为/角色: {behavior_analysis['avg_behaviors_per_character']:.2f}")
    
    # 3. 故事结构分析
    story_path = experiment_dir / "story_updated.json"
    if story_path.exists():
        print("\n📖 故事结构分析...")
        story_data = load_json(story_path)
        structure_analysis = analyze_story_structure(story_data)
        analysis_results['story_structure'] = structure_analysis
        
        print(f"   章节数: {structure_analysis['chapter_count']}")
        print(f"   总字符数: {structure_analysis['total_plot_chars']}")
        print(f"   平均章节长度: {structure_analysis['avg_chapter_length']:.0f}")
        print(f"   平均句子长度: {structure_analysis['avg_sentence_length']:.1f}")
    
    # 4. 对话质量分析
    dialogue_path = experiment_dir / "dialogue_updated.json"
    if dialogue_path.exists():
        print("\n💬 对话质量分析...")
        dialogue_data = load_json(dialogue_path)
        dialogue_analysis = analyze_dialogue_quality(dialogue_data)
        analysis_results['dialogue_quality'] = dialogue_analysis
        
        print(f"   对话总数: {dialogue_analysis['total_dialogue_count']}")
        print(f"   说话者数量: {dialogue_analysis['unique_speakers']}")
        print(f"   平均对话长度: {dialogue_analysis['avg_dialogue_length']:.1f}")
    
    # 5. 保存分析结果
    output_path = experiment_dir / "plot_metrics_analysis.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 剧情指标分析完成！")
    print(f"📄 详细结果保存至: {output_path}")
    
    return analysis_results

if __name__ == "__main__":
    main()
