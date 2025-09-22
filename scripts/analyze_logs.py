import re
import json
import pandas as pd
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt

def analyze_dialogue_logs(log_file_path):
    """分析对话生成日志"""
    
    with open(log_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 🔍 提取会话统计信息
    session_stats_pattern = r'SESSION_STATS \| ({.*?})'
    stats_matches = re.findall(session_stats_pattern, content)
    
    sessions = []
    for match in stats_matches:
        try:
            stats = json.loads(match)
            sessions.append(stats)
        except:
            continue
    
    if not sessions:
        print("❌ 没有找到会话统计信息")
        return
    
    # 📊 生成分析报告
    df = pd.DataFrame(sessions)
    
    print("=" * 60)
    print("📊 对话生成分析报告")
    print("=" * 60)
    
    print(f"\n📈 基本统计:")
    print(f"   总会话数: {len(sessions)}")
    print(f"   平均对话轮数: {df['actual_rounds'].mean():.1f}")
    print(f"   最多轮数: {df['actual_rounds'].max()}")
    print(f"   最少轮数: {df['actual_rounds'].min()}")
    print(f"   触发安全限制: {df['reached_safety_limit'].sum()}次")
    
    print(f"\n🎯 目标达成分析:")
    print(f"   预期轮数平均: {df['expected_rounds'].mean():.1f}")
    print(f"   实际轮数平均: {df['actual_rounds'].mean():.1f}")
    print(f"   轮数差异平均: {(df['actual_rounds'] - df['expected_rounds']).mean():.1f}")
    
    print(f"\n👥 角色使用统计:")
    all_speakers = []
    for speakers in df['speakers_used']:
        all_speakers.extend(speakers)
    speaker_counts = Counter(all_speakers)
    for speaker, count in speaker_counts.most_common():
        print(f"   {speaker}: {count}次")
    
    # 🔍 提取停止原因
    stop_reasons_pattern = r'STOP_DECISION_R\d+ \| reasons=\[(.*?)\]'
    stop_matches = re.findall(stop_reasons_pattern, content)
    
    if stop_matches:
        print(f"\n🛑 停止原因统计:")
        all_reasons = []
        for match in stop_matches:
            reasons = [r.strip().strip('"\'') for r in match.split(',')]
            all_reasons.extend(reasons)
        reason_counts = Counter(all_reasons)
        for reason, count in reason_counts.most_common():
            print(f"   {reason}: {count}次")
    
    # 📈 生成图表
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    df['actual_rounds'].hist(bins=range(1, df['actual_rounds'].max()+2), alpha=0.7)
    plt.title('对话轮数分布')
    plt.xlabel('轮数')
    plt.ylabel('频次')
    
    plt.subplot(2, 2, 2)
    plt.scatter(df['expected_rounds'], df['actual_rounds'], alpha=0.6)
    plt.plot([0, 10], [0, 10], 'r--', alpha=0.5)  # 对角线
    plt.title('预期轮数 vs 实际轮数')
    plt.xlabel('预期轮数')
    plt.ylabel('实际轮数')
    
    plt.subplot(2, 2, 3)
    if speaker_counts:
        speakers, counts = zip(*speaker_counts.most_common())
        plt.bar(speakers, counts)
        plt.title('角色使用频次')
        plt.xticks(rotation=45)
    
    plt.subplot(2, 2, 4)
    if stop_matches:
        reasons, counts = zip(*reason_counts.most_common())
        plt.bar(reasons, counts)
        plt.title('停止原因分布')
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(log_file_path.parent / 'dialogue_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return df

# 使用示例
if __name__ == "__main__":
    # 找到最新的日志文件
    log_dir = Path("data/output/logs")  # 调整为你的路径
    if log_dir.exists():
        log_files = list(log_dir.glob("dialogue_generation_*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            print(f"分析日志文件: {latest_log}")
            df = analyze_dialogue_logs(latest_log)
        else:
            print("没有找到对话生成日志文件")
    else:
        print("日志目录不存在")