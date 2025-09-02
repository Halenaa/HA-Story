#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = "/Users/haha/Story"
sys.path.append(PROJECT_ROOT)

# 导入你的模块
from src.utils.utils import load_json, save_json
from src.generation.dialogue_inserter import analyze_dialogue_insertions_v2

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 数据路径
DATA_DIR = "/Users/haha/Story/data/output/小红帽_科幻_nonlinear_T0.3_s2"
LOGS_DIR = Path(DATA_DIR) / "logs"

print("=" * 60)
print("🚀 重新生成对话并分析轮数统计")
print("=" * 60)
print(f"数据目录: {DATA_DIR}")

# Step 1: 加载已有数据
def load_existing_data():
    """加载已有的story和characters数据"""
    story_file = Path(DATA_DIR) / "story.json"
    characters_file = Path(DATA_DIR) / "characters.json"
    
    if not story_file.exists():
        print(f"❌ story.json 不存在: {story_file}")
        return None, None
    
    if not characters_file.exists():
        print(f"❌ characters.json 不存在: {characters_file}")
        return None, None
    
    story = load_json(str(story_file))
    characters = load_json(str(characters_file))
    
    print(f"✅ 加载story: {len(story)} 个章节")
    print(f"✅ 加载characters: {len(characters)} 个角色")
    
    return story, characters

# Step 2: 重新生成对话（这会触发统计）
def regenerate_dialogues(story, characters):
    """重新生成对话，触发轮数统计"""
    print("\n🔄 开始重新生成对话...")
    
    # 清理旧的统计文件
    stats_file = LOGS_DIR / "rounds_statistics.jsonl"
    if stats_file.exists():
        backup_file = LOGS_DIR / f"rounds_statistics_backup_{pd.Timestamp.now().strftime('%H%M%S')}.jsonl"
        stats_file.rename(backup_file)
        print(f"📦 旧统计文件已备份到: {backup_file}")
    
    # 确保logs目录存在
    LOGS_DIR.mkdir(exist_ok=True)
    
    # 调用你的v2函数重新生成对话
    chapter_results, sentence_results, behavior_timeline = analyze_dialogue_insertions_v2(story, characters)
    
    print(f"✅ 重新生成完成:")
    print(f"  - 章节级结果: {len(chapter_results)} 条")
    print(f"  - 句子级结果: {len(sentence_results)} 条") 
    print(f"  - 行为时间线: {len(behavior_timeline)} 条")
    
    # 保存新的对话结果（用测试后缀避免覆盖原文件）
    save_json(sentence_results, DATA_DIR.split('/')[-1], "sentence_dialogues_test.json")
    print(f"✅ 新对话数据已保存到: sentence_dialogues_test.json")
    
    return chapter_results, sentence_results, behavior_timeline

# Step 3: 读取并分析新生成的统计数据
def analyze_rounds_statistics():
    """分析新生成的轮数统计"""
    stats_file = LOGS_DIR / "rounds_statistics.jsonl"
    
    if not stats_file.exists():
        print(f"❌ 统计文件未生成: {stats_file}")
        return pd.DataFrame()
    
    # 读取JSONL文件
    data = []
    with open(stats_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"⚠️ 解析JSON行失败: {e}")
    
    if not data:
        print("❌ 统计文件为空")
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    print(f"✅ 加载 {len(df)} 条轮数统计记录")
    
    return df

# Step 4: 可视化分析
def visualize_rounds_analysis(df):
    """可视化轮数分析结果"""
    if df.empty:
        print("⚠️ 没有数据进行可视化")
        return
    
    # 基础统计
    print("\n📊 轮数统计结果:")
    print(f"总对话场景: {len(df)}")
    print(f"预期轮数: 平均={df['expected_rounds'].mean():.2f}, 范围=[{df['expected_rounds'].min()}-{df['expected_rounds'].max()}]")
    print(f"实际轮数: 平均={df['actual_rounds'].mean():.2f}, 范围=[{df['actual_rounds'].min()}-{df['actual_rounds'].max()}]")
    print(f"平均偏差: {df['deviation'].mean():.2f} ± {df['deviation'].std():.2f}")
    
    # 准确率分析
    perfect = (df['deviation'] == 0).sum()
    over = (df['deviation'] > 0).sum()
    under = (df['deviation'] < 0).sum()
    
    print(f"\n🎯 预测准确性:")
    print(f"完全匹配: {perfect}/{len(df)} ({perfect/len(df)*100:.1f}%)")
    print(f"超出预期: {over}/{len(df)} ({over/len(df)*100:.1f}%)")
    print(f"少于预期: {under}/{len(df)} ({under/len(df)*100:.1f}%)")
    
    # 创建可视化
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. 预期vs实际散点图
    axes[0, 0].scatter(df['expected_rounds'], df['actual_rounds'], alpha=0.6, s=60)
    min_val = min(df['expected_rounds'].min(), df['actual_rounds'].min())
    max_val = max(df['expected_rounds'].max(), df['actual_rounds'].max())
    axes[0, 0].plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='完美预测线')
    axes[0, 0].set_xlabel('预期轮数')
    axes[0, 0].set_ylabel('实际轮数')
    axes[0, 0].set_title('预期轮数 vs 实际轮数')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 偏差分布
    axes[0, 1].hist(df['deviation'], bins=15, alpha=0.7, edgecolor='black')
    axes[0, 1].axvline(0, color='red', linestyle='--', alpha=0.7, label='零偏差')
    axes[0, 1].set_xlabel('偏差 (实际 - 预期)')
    axes[0, 1].set_ylabel('频次')
    axes[0, 1].set_title('轮数偏差分布')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 轮数分布对比
    rounds_comparison = pd.DataFrame({
        '预期轮数': df['expected_rounds'].value_counts().sort_index(),
        '实际轮数': df['actual_rounds'].value_counts().sort_index()
    }).fillna(0)
    
    rounds_comparison.plot(kind='bar', ax=axes[1, 0])
    axes[1, 0].set_title('预期轮数 vs 实际轮数分布对比')
    axes[1, 0].set_xlabel('轮数')
    axes[1, 0].set_ylabel('场景数量')
    axes[1, 0].tick_params(axis='x', rotation=0)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 按角色数量分析
    df['character_count'] = df['characters'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    char_analysis = df.groupby('character_count').agg({
        'expected_rounds': 'mean',
        'actual_rounds': 'mean',
        'deviation': 'mean'
    })
    
    char_analysis[['expected_rounds', 'actual_rounds']].plot(kind='bar', ax=axes[1, 1])
    axes[1, 1].set_title('按角色数量的平均轮数')
    axes[1, 1].set_xlabel('角色数量')
    axes[1, 1].set_ylabel('平均轮数')
    axes[1, 1].tick_params(axis='x', rotation=0)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

# Step 5: 显示具体案例
def show_extreme_cases(df):
    """显示极端偏差案例"""
    if df.empty:
        return
    
    print(f"\n🔍 极端案例分析:")
    
    # 最大正偏差
    if len(df[df['deviation'] > 0]) > 0:
        max_over_idx = df['deviation'].idxmax()
        max_over = df.loc[max_over_idx]
        print(f"\n【最大正偏差案例】 (session_id: {max_over['session_id']})")
        print(f"预期: {max_over['expected_rounds']} → 实际: {max_over['actual_rounds']} (偏差: +{max_over['deviation']})")
        print(f"剧情: {max_over['sentence_context'][:80]}...")
        print(f"角色: {max_over['characters']}")
    
    # 最大负偏差
    if len(df[df['deviation'] < 0]) > 0:
        max_under_idx = df['deviation'].idxmin()
        max_under = df.loc[max_under_idx]
        print(f"\n【最大负偏差案例】 (session_id: {max_under['session_id']})")
        print(f"预期: {max_under['expected_rounds']} → 实际: {max_under['actual_rounds']} (偏差: {max_under['deviation']})")
        print(f"剧情: {max_under['sentence_context'][:80]}...")
        print(f"角色: {max_under['characters']}")
    
    # 完美匹配案例
    perfect = df[df['deviation'] == 0]
    if len(perfect) > 0:
        print(f"\n【完美匹配案例】 ({len(perfect)} 个)")
        for idx, row in perfect.head(3).iterrows():
            print(f"轮数: {row['actual_rounds']}, 剧情: {row['sentence_context'][:50]}...")

# 主执行流程
def main():
    print("🔄 Step 1: 加载已有数据")
    story, characters = load_existing_data()
    
    if story is None or characters is None:
        print("❌ 无法加载必要的数据文件")
        return
    
    print(f"\n🔄 Step 2: 重新生成对话（触发统计）")
    chapter_results, sentence_results, behavior_timeline = regenerate_dialogues(story, characters)
    
    print(f"\n🔄 Step 3: 分析新生成的统计数据")
    # 等待一下让文件写入完成
    import time
    time.sleep(1)
    
    stats_df = analyze_rounds_statistics()
    
    if not stats_df.empty:
        print(f"\n🔄 Step 4: 可视化分析")
        visualize_rounds_analysis(stats_df)
        
        print(f"\n🔄 Step 5: 案例分析")
        show_extreme_cases(stats_df)
        
        # 保存分析结果
        analysis_file = Path(DATA_DIR) / "rounds_analysis_summary.json"
        summary = {
            "total_scenes": len(stats_df),
            "avg_expected": stats_df['expected_rounds'].mean(),
            "avg_actual": stats_df['actual_rounds'].mean(),
            "avg_deviation": stats_df['deviation'].mean(),
            "accuracy_rate": (stats_df['deviation'] == 0).sum() / len(stats_df) * 100,
            "over_expected_rate": (stats_df['deviation'] > 0).sum() / len(stats_df) * 100,
            "under_expected_rate": (stats_df['deviation'] < 0).sum() / len(stats_df) * 100
        }
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 分析摘要已保存到: {analysis_file}")
        
    else:
        print("❌ 未能获取统计数据，请检查日志功能是否正常")

# 运行主流程
if __name__ == "__main__":
    main()

print("\n" + "=" * 60)
print("🎉 测试完成!")
print("💡 现在你可以查看:")
print(f"  1. logs/rounds_statistics.jsonl - 详细轮数统计")
print(f"  2. logs/dialogue_generation.log - 生成过程日志")
print(f"  3. sentence_dialogues_test.json - 新生成的对话数据")
print(f"  4. rounds_analysis_summary.json - 分析摘要")
print("=" * 60)