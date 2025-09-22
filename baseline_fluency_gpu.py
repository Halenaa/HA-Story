#!/usr/bin/env python3
"""
使用GPU运行baseline文件的流畅性分析
在完成其他分析后单独运行此脚本
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# 添加路径
sys.path.append('/Users/haha/Story')
sys.path.append('/Users/haha/Story/src')

from src.analysis.fluency_analyzer import FluencyAnalyzer

class BaselineFluencyGPU:
    def __init__(self):
        """初始化GPU流畅性分析器"""
        self.baseline_files = {
            'baseline_s1': '/Users/haha/Story/output/baseline_s1.md',
            'baseline_s2': '/Users/haha/Story/output/baseline_s2.md', 
            'baseline_s3': '/Users/haha/Story/data/normal_baseline.md'
        }
        
        self.output_dir = '/Users/haha/Story/baseline_analysis_results'
        self.analyzer = None
    
    def run_fluency_analysis(self):
        """运行GPU流畅性分析"""
        print("🚀 开始GPU流畅性分析...")
        print("📍 确保你的GPU环境已配置完成")
        
        # 初始化分析器
        print("🔧 初始化RoBERTa流畅性分析器...")
        self.analyzer = FluencyAnalyzer(model_name="roberta-large")
        
        results = {}
        
        for baseline_name, file_path in self.baseline_files.items():
            if not os.path.exists(file_path):
                print(f"❌ {baseline_name}: 文件不存在 {file_path}")
                continue
            
            print(f"\n📝 [{baseline_name}] 分析流畅性...")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 运行分析
            result = self.analyzer.analyze_fluency(content)
            
            # 添加基本信息
            result.update({
                'baseline_name': baseline_name,
                'source_file': file_path,
                'word_count': len(content.split()),
                'char_count': len(content)
            })
            
            # 保存结果
            output_file = f"{self.output_dir}/{baseline_name}/fluency_analysis.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            results[baseline_name] = result
            
            print(f"   ✅ 完成 - PPL: {result['pseudo_ppl']:.2f}, 错误率: {result['err_per_100w']:.2f}")
        
        # 保存汇总结果
        summary_file = f"{self.output_dir}/fluency_gpu_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n🎉 GPU流畅性分析完成!")
        print(f"📊 成功分析: {len(results)}/{len(self.baseline_files)} 个文件")
        print(f"📁 结果保存到: {self.output_dir}/")
        
        return results
    
    def update_comprehensive_results(self):
        """更新综合分析结果，加入流畅性数据"""
        print("\n🔄 更新综合分析结果...")
        
        for baseline_name in self.baseline_files.keys():
            # 加载流畅性结果
            fluency_file = f"{self.output_dir}/{baseline_name}/fluency_analysis.json"
            if not os.path.exists(fluency_file):
                print(f"⚠️  {baseline_name}: 未找到流畅性结果")
                continue
            
            with open(fluency_file, 'r', encoding='utf-8') as f:
                fluency_data = json.load(f)
            
            # 加载综合结果
            comprehensive_file = f"{self.output_dir}/{baseline_name}/comprehensive_analysis.json"
            if os.path.exists(comprehensive_file):
                with open(comprehensive_file, 'r', encoding='utf-8') as f:
                    comprehensive_data = json.load(f)
                
                # 添加流畅性数据
                comprehensive_data['fluency'] = fluency_data
                
                # 保存更新后的结果
                with open(comprehensive_file, 'w', encoding='utf-8') as f:
                    json.dump(comprehensive_data, f, ensure_ascii=False, indent=2, default=str)
                
                print(f"   ✅ {baseline_name}: 综合结果已更新")
            else:
                print(f"   ⚠️  {baseline_name}: 未找到综合分析结果")

def main():
    """主函数"""
    print("🎯 Baseline GPU流畅性分析")
    print("=" * 60)
    print("此脚本将使用GPU为3个baseline文件运行流畅性分析")
    print("确保在其他分析完成后运行此脚本")
    print("=" * 60)
    
    analyzer = BaselineFluencyGPU()
    
    try:
        # 运行流畅性分析
        results = analyzer.run_fluency_analysis()
        
        # 更新综合结果
        analyzer.update_comprehensive_results()
        
        print("\n✨ 完成! 现在可以运行update_metrics_with_baselines.py更新CSV")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
