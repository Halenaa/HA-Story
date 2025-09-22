"""
语义连续性系统集成示例
展示如何使用新的相对比较系统替代主观阈值
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent if 'src' in str(current_dir) else current_dir
sys.path.append(str(project_root))

from src.utils.semantic_continuity_relative_comparison import (
    SemanticContinuityRelativeComparison,
    create_comparison_system_from_existing_data
)
from src.analysis.hred_coherence_evaluator import HREDSemanticContinuityEvaluator


def integrate_relative_comparison_into_evaluation():
    """
    将相对比较系统集成到现有评估流程中的示例
    """
    print("🔧 语义连续性评估系统集成示例")
    print("=" * 50)
    
    # 1. 创建相对比较系统
    comparison_system = SemanticContinuityRelativeComparison()
    
    # 2. 从现有CSV数据中加载基准分数
    csv_files = [
        "/Users/haha/Story/metrics_master_clean.csv",
        # 可以添加更多基准数据文件
    ]
    
    try:
        # 尝试从CSV文件加载数据
        df = pd.read_csv("/Users/haha/Story/metrics_master_clean.csv")
        
        # 检查新的列名是否存在
        if 'avg_semantic_continuity' in df.columns:
            baseline_scores = df['avg_semantic_continuity'].dropna().tolist()
            comparison_system.add_baseline_data(baseline_scores, "existing_stories")
            print(f"✅ 从CSV加载了 {len(baseline_scores)} 个基准分数")
        else:
            print("⚠️  CSV文件中未找到 'avg_semantic_continuity' 列")
            print(f"可用列: {list(df.columns)}")
            # 为演示目的创建示例数据
            baseline_scores = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
            comparison_system.add_baseline_data(baseline_scores, "demo_baseline")
            print("✅ 使用演示基准数据")
    
    except Exception as e:
        print(f"⚠️  无法加载CSV数据: {e}")
        # 创建演示数据
        baseline_scores = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
        comparison_system.add_baseline_data(baseline_scores, "demo_baseline")
        print("✅ 使用演示基准数据")
    
    # 3. 展示相对比较功能
    test_scores = [0.30, 0.45, 0.55, 0.65, 0.75]
    dataset_name = "existing_stories" if 'avg_semantic_continuity' in df.columns else "demo_baseline"
    
    print(f"\n📊 语义连续性相对比较结果:")
    print("-" * 50)
    
    for score in test_scores:
        result = comparison_system.compare_to_baseline(score, dataset_name)
        print(f"分数: {score:.3f} | {result['comparison_description']} | {result['position_description']}")
    
    # 4. 生成分布总结
    print(f"\n📈 基准数据分布总结:")
    print("-" * 50)
    summary = comparison_system.generate_distribution_summary(dataset_name)
    
    print(f"样本数量: {summary['sample_count']}")
    print(f"平均值: {summary['distribution_summary']['mean']}")
    print(f"标准差: {summary['distribution_summary']['std']}")
    print(f"范围: {summary['distribution_summary']['min']} - {summary['distribution_summary']['max']}")
    
    print("\n百分位阈值:")
    for percentile, value in summary['percentile_thresholds'].items():
        print(f"  {percentile}: {value}")
    
    print(f"\n⚠️  重要说明: {summary['measurement_limitation']}")
    
    return comparison_system


def demonstrate_semantic_continuity_evaluation(story_text_sample):
    """
    演示新的语义连续性评估方法（不使用主观阈值）
    """
    print(f"\n🔍 语义连续性评估演示")
    print("-" * 50)
    
    # 模拟句子（实际使用时会从故事中提取）
    sentences = [
        "小红帽准备去看望生病的外婆。",
        "她在森林中遇到了一只狼。", 
        "狼询问小红帽要去哪里。",
        "小红帽告诉了狼外婆住的地方。",
        "狼想出了一个邪恶的计划。"
    ]
    
    print("示例句子序列:")
    for i, sentence in enumerate(sentences, 1):
        print(f"  {i}. {sentence}")
    
    # 使用语义连续性评估器
    try:
        evaluator = HREDSemanticContinuityEvaluator(model_name='all-MiniLM-L6-v2')  # 使用更轻量的模型进行演示
        
        # 创建模拟的故事数据格式
        story_data = [{"plot": " ".join(sentences)}]
        
        # 进行评估
        result = evaluator.evaluate_story_semantic_continuity(story_data, include_details=False)
        
        continuity_score = result['HRED_semantic_continuity_evaluation']['average_semantic_continuity']
        print(f"\n语义连续性分数: {continuity_score:.4f}")
        print(f"测量说明: {result['HRED_semantic_continuity_evaluation']['objective_description']['explanation']}")
        print(f"局限性说明: {result['HRED_semantic_continuity_evaluation']['objective_description']['limitation']}")
        
        # 使用相对比较系统
        comparison_system = integrate_relative_comparison_into_evaluation()
        dataset_name = list(comparison_system.reference_data.keys())[0]
        comparison_result = comparison_system.compare_to_baseline(continuity_score, dataset_name)
        
        print(f"\n相对比较结果:")
        print(f"  {comparison_result['comparison_description']}")
        print(f"  水平评价: {comparison_result['position_description']}")
        print(f"  百分位排名: {comparison_result['percentile_rank']}%")
        
    except ImportError:
        print("⚠️  sentence-transformers未安装，无法运行语义连续性评估演示")
    except Exception as e:
        print(f"⚠️  评估演示失败: {e}")


if __name__ == "__main__":
    # 运行集成示例
    comparison_system = integrate_relative_comparison_into_evaluation()
    
    # 运行评估演示
    sample_story = "这是一个示例故事文本"
    demonstrate_semantic_continuity_evaluation(sample_story)
    
    print(f"\n✅ 语义连续性系统集成完成!")
    print("\n主要改进:")
    print("  ❌ 删除了主观阈值 (0.7='优秀' 等)")
    print("  ✅ 实现了相对比较系统")
    print("  ✅ 诚实说明了测量局限性")
    print("  ✅ 提供了客观的百分位排名")
