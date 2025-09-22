#!/usr/bin/env python3
"""
一键运行完整的baseline分析流程
1. 运行综合分析 (多样性、流畅性、连贯性、情感、结构)
2. 更新metrics_master_clean.csv
"""

import os
import sys
import time
from datetime import datetime

# 添加当前目录到路径
sys.path.append('/Users/haha/Story')

def run_command_with_output(description, command_func):
    """运行命令并显示输出"""
    print(f"\n{'='*80}")
    print(f"🚀 {description}")
    print(f"{'='*80}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        result = command_func()
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ {description} - 完成!")
        print(f"⏱️  耗时: {elapsed_time:.1f} 秒")
        return True, result
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ {description} - 失败!")
        print(f"💥 错误: {e}")
        print(f"⏱️  耗时: {elapsed_time:.1f} 秒")
        
        # 打印详细错误信息
        import traceback
        traceback.print_exc()
        
        return False, None

def check_baseline_files():
    """检查baseline文件是否存在"""
    baseline_files = {
        'baseline_s1': '/Users/haha/Story/baseline_s1.md',
        'baseline_s2': '/Users/haha/Story/baseline_s2.md', 
        'baseline_s3': '/Users/haha/Story/baseline_s3.md'
    }
    
    print("📁 检查baseline文件...")
    missing_files = []
    
    for name, path in baseline_files.items():
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"   ✅ {name}: {path} ({file_size:,} bytes)")
        else:
            print(f"   ❌ {name}: {path} - 文件不存在!")
            missing_files.append((name, path))
    
    if missing_files:
        print(f"\n❌ 发现 {len(missing_files)} 个文件缺失:")
        for name, path in missing_files:
            print(f"   • {name}: {path}")
        print("\n请确保所有baseline文件都存在后再运行!")
        return False
    
    print(f"✅ 所有 {len(baseline_files)} 个baseline文件检查通过!")
    return True

def run_comprehensive_analysis():
    """运行综合分析"""
    from comprehensive_baseline_analyzer import ComprehensiveBaselineAnalyzer
    
    analyzer = ComprehensiveBaselineAnalyzer()
    results = analyzer.run_all_analysis()
    return results

def update_metrics_csv():
    """更新metrics CSV"""
    from update_metrics_with_baselines import BaselineMetricsUpdater
    
    updater = BaselineMetricsUpdater()
    df = updater.update_metrics_csv()
    return df

def show_final_summary(analysis_results, csv_df):
    """显示最终总结"""
    print(f"\n{'='*80}")
    print("🎉 BASELINE分析流程完成总结")
    print(f"{'='*80}")
    
    # 分析结果总结
    if analysis_results:
        print(f"\n📊 分析结果:")
        success_count = len(analysis_results)
        total_count = 3
        print(f"   ✅ 成功分析: {success_count}/{total_count} 个baseline文件")
        
        for baseline_name, result in analysis_results.items():
            if 'text_features' in result:
                features = result['text_features']
                print(f"   📝 {baseline_name}:")
                print(f"       - 总词数: {features.get('total_words', 'N/A'):,}")
                print(f"       - 章节数: {features.get('chapter_count', 'N/A')}")
                print(f"       - 句子数: {features.get('total_sentences', 'N/A'):,}")
    
    # CSV更新总结
    if csv_df is not None:
        print(f"\n📈 CSV更新结果:")
        baseline_count = len(csv_df[csv_df['is_baseline'] == 1])
        total_count = len(csv_df)
        print(f"   📊 总行数: {total_count}")
        print(f"   🎯 baseline行数: {baseline_count}")
        print(f"   📁 文件路径: /Users/haha/Story/metrics_master_clean.csv")
    
    # 提供下一步建议
    print(f"\n🔍 接下来可以做什么:")
    print("   1. 查看详细分析结果:")
    print("      📂 /Users/haha/Story/baseline_analysis_results/")
    print("   2. 检查更新后的CSV:")
    print("      📊 /Users/haha/Story/metrics_master_clean.csv")
    print("   3. 运行进一步的统计分析或可视化")
    
    print(f"\n✨ 分析维度完成情况:")
    dimensions = [
        "✅ 多样性分析 (distinct_avg, diversity_group_score)",
        "⏭️  流畅性分析 (pseudo_ppl, err_per_100w) - 跳过，使用GPU单独运行", 
        "✅ 语义连续性分析 (avg_semantic_continuity, semantic_continuity_std)",
        "✅ 情感分析 (roberta_avg_score, correlation_coefficient)",
        "✅ 结构分析 (chapter_count, tp_coverage, li_function_diversity)",
        "✅ 基本统计 (total_words, total_sentences)"
    ]
    
    for dim in dimensions:
        print(f"   {dim}")

def main():
    """主函数"""
    print("🎯 BASELINE综合分析流程")
    print("=" * 80)
    print("将为3个baseline文件生成完整的metrics数据:")
    print("• baseline_s1.md (baseline小红帽1)")
    print("• baseline_s2.md (baseline小红帽2)")  
    print("• baseline_s3.md (baseline小红帽3)")
    print()
    print("分析维度包括:")
    print("• 多样性 (Diversity)")
    print("• 语义连续性 (Semantic Continuity)")
    print("• 情感弧 (Emotional Arc)")  
    print("• 结构完整性 (Structure)")
    print("• 流畅性 (Fluency) - ⚠️  跳过，用户将使用GPU单独运行")
    print("=" * 80)
    
    # 检查文件
    if not check_baseline_files():
        return False
    
    # 询问用户确认
    try:
        confirm = input("\n🤔 确认开始分析吗? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return False
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        return False
    
    print("\n🚀 开始执行分析流程...")
    
    # 总计时器
    total_start_time = time.time()
    
    analysis_results = None
    csv_df = None
    
    # 步骤1: 运行综合分析
    success1, analysis_results = run_command_with_output(
        "步骤1: 运行综合分析 (多样性+语义连续性+情感+结构，跳过流畅性)",
        run_comprehensive_analysis
    )
    
    if not success1:
        print("❌ 综合分析失败，停止执行")
        return False
    
    # 步骤2: 更新CSV
    success2, csv_df = run_command_with_output(
        "步骤2: 更新metrics_master_clean.csv",
        update_metrics_csv
    )
    
    if not success2:
        print("❌ CSV更新失败，但分析结果已保存")
    
    # 计算总时间
    total_time = time.time() - total_start_time
    
    # 显示最终总结
    show_final_summary(analysis_results, csv_df)
    
    print(f"\n⏱️  总执行时间: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
    print(f"📅 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success1 and success2:
        print("\n🎉 所有步骤执行成功! ✨")
        return True
    elif success1:
        print("\n⚠️  分析完成，但CSV更新有问题")
        return True
    else:
        print("\n❌ 执行过程中出现错误")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
