#!/usr/bin/env python3
"""
使用与54个实验样本完全相同的PPL计算方式重新计算baseline PPL
确保对比的公平性和一致性

基于 batch_analyze_fluency.py 的逻辑，使用相同的：
- FluencyAnalyzer
- roberta-large 模型  
- 相同的参数设置
- 相同的计算流程
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime

# 添加src路径到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from analysis.fluency_analyzer import FluencyAnalyzer

class BaselinePPLRecalculator:
    """使用与实验样本相同方法的baseline PPL重新计算器"""
    
    def __init__(self, model_name: str = "roberta-large"):
        """
        初始化重新计算器
        
        Args:
            model_name: 使用的模型名称，必须与实验样本一致
        """
        self.model_name = model_name
        print(f"🔄 初始化baseline PPL重新计算器")
        print(f"   使用模型: {model_name} (与54个实验样本完全相同)")
        
        # baseline文件配置
        self.baseline_files = {
            'baseline_s1': '/Users/haha/Story/baseline_s1.md',
            'baseline_s2': '/Users/haha/Story/baseline_s2.md', 
            'baseline_s3': '/Users/haha/Story/baseline_s3.md'
        }
        
        # 输出目录
        self.output_dir = '/Users/haha/Story/baseline_ppl_recalculation_results'
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📁 输出目录: {self.output_dir}")
    
    def check_baseline_files(self):
        """检查baseline文件是否存在"""
        print("\n📋 检查baseline文件...")
        
        missing_files = []
        for name, path in self.baseline_files.items():
            if os.path.exists(path):
                file_size = os.path.getsize(path)
                word_count = len(open(path, 'r', encoding='utf-8').read().split())
                print(f"   ✅ {name}: {file_size:,} bytes, ~{word_count:,} words")
            else:
                print(f"   ❌ {name}: 文件不存在!")
                missing_files.append((name, path))
        
        if missing_files:
            print(f"\n❌ 发现 {len(missing_files)} 个文件缺失，请检查!")
            return False
        
        print(f"✅ 所有 {len(self.baseline_files)} 个baseline文件检查通过!")
        return True
    
    def read_story_content(self, file_path: str) -> str:
        """读取故事内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content.strip()
        except Exception as e:
            print(f"❌ 读取文件失败 {file_path}: {e}")
            return ""
    
    def save_individual_result(self, result: Dict, baseline_name: str):
        """保存单个baseline的结果"""
        output_file = os.path.join(self.output_dir, f"{baseline_name}_unified_ppl_result.json")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"   💾 单个结果保存: {output_file}")
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
    
    def recalculate_all_baselines(self):
        """重新计算所有baseline的PPL"""
        print(f"\n🚀 开始重新计算baseline PPL")
        print(f"{'='*80}")
        print(f"🎯 目标: 使用与54个实验样本完全相同的算法和参数")
        print(f"📊 模型: {self.model_name}")
        print(f"🔧 算法: FluencyAnalyzer (roberta-large + Masked LM pseudo-PPL)")
        print(f"{'='*80}")
        
        # 初始化分析器（与实验样本使用完全相同的方式）
        print("\n🤖 初始化流畅度分析器...")
        analyzer = FluencyAnalyzer(model_name=self.model_name)
        print(f"   ✅ 分析器初始化完成")
        
        # 存储所有结果
        all_results = []
        comparison_data = []
        
        # 读取现有的baseline PPL数据作为对比
        original_ppls = self.load_original_baseline_ppls()
        
        # 逐个处理baseline文件
        for i, (baseline_name, file_path) in enumerate(self.baseline_files.items(), 1):
            print(f"\n📝 [{i}/{len(self.baseline_files)}] 重新计算: {baseline_name}")
            print(f"   📂 文件: {file_path}")
            
            # 读取故事内容
            story_content = self.read_story_content(file_path)
            if not story_content:
                print(f"   ⏭️  跳过空文件")
                continue
            
            word_count = len(story_content.split())
            char_count = len(story_content)
            print(f"   📏 文本: {char_count:,} 字符, {word_count:,} 词")
            
            # 使用与实验样本完全相同的方法分析流畅度
            try:
                start_time = datetime.now()
                print(f"   🔄 开始PPL计算...")
                
                # 关键：使用与实验样本完全相同的analyze_fluency方法
                result = analyzer.analyze_fluency(story_content)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # 添加额外信息（与实验样本保持一致的格式）
                result.update({
                    'baseline_name': baseline_name,
                    'story_file_path': file_path,
                    'word_count': word_count,
                    'char_count': char_count,
                    'calculation_duration_seconds': duration,
                    'recalculation_timestamp': datetime.now().isoformat(),
                    'method_note': 'Same as 54 experimental samples: FluencyAnalyzer + roberta-large'
                })
                
                # 保存单个结果
                self.save_individual_result(result, baseline_name)
                
                # 添加到结果列表
                all_results.append(result)
                
                # 对比数据
                original_ppl = original_ppls.get(baseline_name, 'N/A')
                new_ppl = result['pseudo_ppl']
                
                comparison_data.append({
                    'baseline_name': baseline_name,
                    'original_ppl': original_ppl,
                    'new_ppl_unified': new_ppl,
                    'difference': abs(new_ppl - original_ppl) if original_ppl != 'N/A' else 'N/A',
                    'word_count': word_count
                })
                
                print(f"   ✅ 完成 - PPL: {new_ppl:.3f}, 错误率: {result['err_per_100w']:.2f}%, 耗时: {duration:.1f}秒")
                if original_ppl != 'N/A':
                    diff = abs(new_ppl - original_ppl)
                    print(f"   📊 对比 - 原PPL: {original_ppl:.3f}, 新PPL: {new_ppl:.3f}, 差异: {diff:.3f}")
                
            except Exception as e:
                print(f"   ❌ 计算失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 归一化分数（与实验样本使用相同方法）
        if all_results:
            print(f"\n🔢 应用归一化分数（与实验样本相同方法）...")
            try:
                all_results = analyzer.normalize_scores(all_results)
                print(f"   ✅ 归一化完成")
            except Exception as e:
                print(f"   ⚠️  归一化失败: {e}")
        
        # 保存汇总结果
        self.save_summary_results(all_results, comparison_data)
        
        print(f"\n🎉 Baseline PPL重新计算完成！")
        print(f"📊 成功处理: {len(all_results)}/{len(self.baseline_files)} 个文件")
        
        return all_results, comparison_data
    
    def load_original_baseline_ppls(self) -> Dict:
        """加载原始的baseline PPL数据用于对比"""
        original_ppls = {}
        
        # 从现有的JSON文件中读取
        ppl_files = {
            'baseline_s1': '/Users/haha/Story/baseline_s1_fluency_result.json',
            'baseline_s2': '/Users/haha/Story/baseline_s2_fluency_result.json',
            'baseline_s3': '/Users/haha/Story/baseline_s3_fluency_result.json'
        }
        
        for name, file_path in ppl_files.items():
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    original_ppls[name] = data.get('pseudo_ppl', 'N/A')
                    print(f"   📄 加载原始PPL {name}: {original_ppls[name]}")
            except Exception as e:
                print(f"   ⚠️  无法加载原始PPL {name}: {e}")
                original_ppls[name] = 'N/A'
        
        return original_ppls
    
    def save_summary_results(self, results: List[Dict], comparison_data: List[Dict]):
        """保存汇总结果和对比报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. 保存详细结果
        summary_file = os.path.join(self.output_dir, f'baseline_ppl_unified_summary_{timestamp}.json')
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'method': 'Same as 54 experimental samples',
                    'model': self.model_name,
                    'timestamp': timestamp,
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            print(f"📄 详细汇总保存: {summary_file}")
        except Exception as e:
            print(f"❌ 保存详细汇总失败: {e}")
        
        # 2. 保存对比CSV
        comparison_file = os.path.join(self.output_dir, f'baseline_ppl_comparison_{timestamp}.csv')
        try:
            df = pd.DataFrame(comparison_data)
            df.to_csv(comparison_file, index=False)
            print(f"📊 对比CSV保存: {comparison_file}")
        except Exception as e:
            print(f"❌ 保存对比CSV失败: {e}")
        
        # 3. 生成对比报告
        self.generate_comparison_report(results, comparison_data, timestamp)
    
    def generate_comparison_report(self, results: List[Dict], comparison_data: List[Dict], timestamp: str):
        """生成详细的对比报告"""
        report_file = os.path.join(self.output_dir, f'baseline_ppl_unification_report_{timestamp}.md')
        
        # 计算统计信息
        new_ppls = [r['pseudo_ppl'] for r in results if r['pseudo_ppl'] != float('inf')]
        
        lines = [
            "# 🔄 Baseline PPL统一重新计算报告",
            f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**计算方法**: 与54个实验样本完全一致",
            f"**使用模型**: {self.model_name}",
            
            "\n## 🎯 目标",
            "\n确保baseline和54个实验样本使用**完全相同**的PPL计算方法：",
            "- 相同的模型: `roberta-large`",
            "- 相同的算法: `FluencyAnalyzer.analyze_fluency()`", 
            "- 相同的参数: `subsample_rate=4`, 自适应子采样",
            "- 相同的处理流程: 分块、掩码、归一化",
            
            "\n## 📊 重新计算结果",
            "\n### 新的统一PPL值:"
        ]
        
        for i, result in enumerate(results):
            name = result['baseline_name']
            ppl = result['pseudo_ppl']
            err_rate = result['err_per_100w']
            word_count = result['word_count']
            duration = result.get('calculation_duration_seconds', 0)
            
            lines.append(f"- **{name}**: PPL = {ppl:.3f}, 错误率 = {err_rate:.2f}%, {word_count:,} 词 ({duration:.1f}秒)")
        
        # 统计摘要
        if new_ppls:
            avg_ppl = sum(new_ppls) / len(new_ppls)
            std_ppl = (sum((x - avg_ppl) ** 2 for x in new_ppls) / len(new_ppls)) ** 0.5
            
            lines.extend([
                f"\n### 统计摘要:",
                f"- **平均PPL**: {avg_ppl:.3f} ± {std_ppl:.3f}",
                f"- **PPL范围**: {min(new_ppls):.3f} - {max(new_ppls):.3f}",
                f"- **样本数**: {len(new_ppls)}"
            ])
        
        # 对比表格
        lines.extend([
            "\n## 📈 新旧对比",
            "\n| Baseline | 原PPL | 新PPL (统一) | 差异 | 词数 |",
            "|----------|-------|-------------|------|------|"
        ])
        
        for comp in comparison_data:
            name = comp['baseline_name']
            orig = comp['original_ppl']
            new = comp['new_ppl_unified']
            diff = comp['difference']
            words = comp['word_count']
            
            orig_str = f"{orig:.3f}" if orig != 'N/A' else 'N/A'
            diff_str = f"{diff:.3f}" if diff != 'N/A' else 'N/A'
            
            lines.append(f"| {name} | {orig_str} | {new:.3f} | {diff_str} | {words:,} |")
        
        # 结论和建议
        lines.extend([
            "\n## ✅ 结论",
            "\n### 成功完成统一:",
            "1. ✅ 所有baseline现在使用与54个实验样本相同的PPL计算方法",
            "2. ✅ 使用相同的`roberta-large`模型和`FluencyAnalyzer`",
            "3. ✅ 应用相同的参数设置和处理流程",
            "4. ✅ 数据对比现在具有完全的公平性",
            
            "\n### 下一步行动:",
            "1. **更新CSV文件**: 将新的统一PPL值更新到`metrics_master_clean.csv`",
            "2. **重新分析**: 基于统一的PPL数据重新进行fluency维度分析",
            "3. **验证结果**: 确保新的PPL值合理且与实验样本在同一量级",
            "4. **归档备份**: 保留原始数据作为参考",
            
            f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        # 保存报告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print(f"📋 对比报告保存: {report_file}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

def main():
    """主函数"""
    print("🔄 Baseline PPL统一重新计算系统")
    print("=" * 80)
    print("目标: 使用与54个实验样本完全相同的PPL算法重新计算baseline")
    print("方法: FluencyAnalyzer + roberta-large (完全一致)")
    print("=" * 80)
    
    # 初始化重新计算器
    try:
        recalculator = BaselinePPLRecalculator(model_name="roberta-large")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 检查文件
    if not recalculator.check_baseline_files():
        return False
    
    # 询问用户确认
    try:
        print(f"\n🤔 确认开始重新计算吗?")
        print("   这将使用与54个实验样本完全相同的方法重新计算所有baseline PPL")
        confirm = input("   输入 'y' 继续: ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return False
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        return False
    
    # 执行重新计算
    try:
        start_time = datetime.now()
        results, comparison_data = recalculator.recalculate_all_baselines()
        end_time = datetime.now()
        
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print("🎉 重新计算完成!")
        print(f"{'='*80}")
        print(f"⏱️  总耗时: {total_time:.1f} 秒")
        print(f"📊 成功处理: {len(results)} 个baseline文件")
        print(f"📁 结果目录: {recalculator.output_dir}")
        
        if results:
            ppls = [r['pseudo_ppl'] for r in results if r['pseudo_ppl'] != float('inf')]
            if ppls:
                avg_ppl = sum(ppls) / len(ppls)
                print(f"\n📈 新的统一baseline平均PPL: {avg_ppl:.3f}")
                print("✅ 现在baseline和54个实验样本使用完全相同的PPL算法!")
        
        return True
        
    except Exception as e:
        print(f"❌ 重新计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
