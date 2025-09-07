#!/usr/bin/env python3
"""
测试修复后的复杂度分析逻辑
"""

from src.analysis.performance_analyzer import PerformanceAnalyzer
import time

def test_complexity_analysis():
    """测试复杂度分析的修复效果"""
    
    print("🧪 测试复杂度分析修复效果")
    print("=" * 50)
    
    # 创建测试场景
    test_cases = [
        {
            'name': '小数据集',
            'chars': 100,
            'time': 0.5,
            'expected': 'Data size too small'
        },
        {
            'name': '线性复杂度模拟', 
            'chars': 10000,
            'time': 10.0,  # 1ms per char, should be linear
            'expected': 'Linear'
        },
        {
            'name': 'N-log-N复杂度模拟',
            'chars': 10000,
            'time': 132.8,  # 10000 * log(10000) * 0.0001 = 132.8
            'expected': 'N-log-N'
        },
        {
            'name': '二次复杂度模拟',
            'chars': 1000,  
            'time': 1.0,  # 1000^2 * 0.000001 = 1.0
            'expected': 'Quadratic'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        
        # 创建分析器实例
        analyzer = PerformanceAnalyzer(f"test_{i}", enable_memory_monitoring=False)
        
        # 模拟文本特征
        analyzer.text_features = {
            'total_char_count': test_case['chars'],
            'total_word_count': test_case['chars'] // 4,  # 估算
            'chapter_count': 5
        }
        
        # 模拟执行时间
        analyzer.total_start_time = time.time() - test_case['time']
        
        # 测试复杂度分析
        complexity_class = analyzer._estimate_complexity_class()
        
        print(f"   输入: {test_case['chars']} chars, {test_case['time']} seconds")
        print(f"   预期: {test_case['expected']}")
        print(f"   结果: {complexity_class}")
        
        # 检验是否符合预期
        if test_case['expected'] in complexity_class:
            print("   ✅ 通过")
        else:
            print("   ❌ 不匹配")
    
    print("\n" + "=" * 50)
    print("📊 复杂度分析修复测试完成")

def test_word_count_fix():
    """测试词汇统计修复"""
    print("\n🔤 测试词汇统计修复效果")
    print("=" * 30)
    
    analyzer = PerformanceAnalyzer("word_test", enable_memory_monitoring=False)
    
    # 模拟英文故事数据
    story_data = [
        {
            'chapter_id': 'Chapter 1',
            'title': 'The Beginning',
            'plot': 'The swan stood at the water edge. It was beautiful and graceful.'
        },
        {
            'chapter_id': 'Chapter 2', 
            'title': 'The Journey',
            'plot': 'Across the lake, other swans were swimming. They welcomed the newcomer.'
        }
    ]
    
    # 分析文本特征
    features = analyzer.analyze_text_features(story_data)
    
    print(f"   总字符数: {features['total_char_count']}")
    print(f"   总词汇数: {features['total_word_count']}")
    print(f"   章节数: {features['chapter_count']}")
    
    # 验证词汇数不为0
    if features['total_word_count'] > 0:
        print("   ✅ 词汇统计修复成功")
    else:
        print("   ❌ 词汇统计仍有问题")

if __name__ == "__main__":
    test_complexity_analysis()
    test_word_count_fix()
