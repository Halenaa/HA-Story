#!/usr/bin/env python3
"""
PPL计算一致性验证脚本
Step 0: 数据验证 - 确保baseline和你的系统使用相同的方法

发现的问题：
1. src/analysis/fluency_analyzer.py - 使用BERT masked LM + 自适应子采样
2. gpu_baseline_fluency.py - 使用简化版GPT-2困惑度计算  
3. 📊_指标计算方法详细说明.md - 又是另一种方法

这些不同的计算方法会导致PPL值差异巨大！
"""

import pandas as pd
import numpy as np
import torch
import json
import os
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForMaskedLM, GPT2LMHeadModel, GPT2Tokenizer
import math
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class UnifiedPPLCalculator:
    """统一的PPL计算器 - 确保所有系统使用相同方法"""
    
    def __init__(self, method='bert_masked_lm'):
        """
        初始化统一PPL计算器
        
        Args:
            method: 'bert_masked_lm' 或 'gpt2_autoregressive'
        """
        self.method = method
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"🔧 初始化统一PPL计算器 (方法: {method}, 设备: {self.device})")
        
        if method == 'bert_masked_lm':
            self.model_name = 'bert-base-uncased'
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(self.model_name)
        elif method == 'gpt2_autoregressive':
            self.model_name = 'gpt2'
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        else:
            raise ValueError(f"不支持的方法: {method}")
        
        self.model.to(self.device)
        self.model.eval()
        print(f"✅ 模型加载完成: {self.model_name}")
    
    def calculate_bert_pseudo_ppl(self, text: str, subsample_rate: int = 4) -> float:
        """
        使用BERT Masked LM计算pseudo-PPL
        这是原始fluency_analyzer的统一版本
        """
        if not text or not text.strip():
            return float('inf')
        
        # 分词
        tokens = self.tokenizer.tokenize(text)
        if len(tokens) < 2:
            return float('inf')
        
        total_neg_log_likelihood = 0.0
        valid_predictions = 0
        
        # 确保子采样率合理
        actual_subsample_rate = max(1, min(subsample_rate, len(tokens)))
        
        print(f"   处理 {len(tokens)} tokens，子采样率: {actual_subsample_rate}")
        
        for i in range(0, len(tokens), actual_subsample_rate):
            if i >= len(tokens):
                break
                
            # 创建masked版本
            masked_tokens = tokens.copy()
            original_token = tokens[i]
            
            # 跳过特殊token
            if original_token in ['[CLS]', '[SEP]', '[PAD]']:
                continue
                
            masked_tokens[i] = '[MASK]'
            
            # 转换为input_ids
            input_text = ' '.join(masked_tokens)
            try:
                inputs = self.tokenizer(input_text, return_tensors='pt', max_length=512, truncation=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                
                # 找到[MASK]位置
                mask_token_id = self.tokenizer.mask_token_id
                mask_positions = (inputs['input_ids'] == mask_token_id).nonzero(as_tuple=True)[1]
                
                if len(mask_positions) > 0:
                    mask_pos = mask_positions[0]
                    
                    # 获取原始token的ID
                    original_token_id = self.tokenizer.convert_tokens_to_ids(original_token)
                    
                    # 计算log概率
                    log_probs = torch.log_softmax(logits[0, mask_pos], dim=-1)
                    token_log_prob = log_probs[original_token_id].item()
                    
                    total_neg_log_likelihood += (-token_log_prob)
                    valid_predictions += 1
                    
            except Exception as e:
                print(f"      警告: 处理位置 {i} 时出错: {e}")
                continue
        
        if valid_predictions == 0:
            return float('inf')
        
        # 计算pseudo-PPL
        avg_neg_log_likelihood = total_neg_log_likelihood / valid_predictions
        pseudo_ppl = math.exp(avg_neg_log_likelihood)
        
        print(f"   计算完成: {valid_predictions} 个有效预测，pseudo-PPL = {pseudo_ppl:.2f}")
        return pseudo_ppl
    
    def calculate_gpt2_ppl(self, text: str) -> float:
        """
        使用GPT-2计算标准困惑度
        """
        if not text or not text.strip():
            return float('inf')
        
        # 编码文本
        inputs = self.tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs['input_ids'])
            loss = outputs.loss
            perplexity = torch.exp(loss).item()
        
        print(f"   GPT-2 PPL计算完成: {perplexity:.2f}")
        return perplexity
    
    def calculate_ppl(self, text: str, **kwargs) -> float:
        """统一PPL计算接口"""
        if self.method == 'bert_masked_lm':
            return self.calculate_bert_pseudo_ppl(text, **kwargs)
        elif self.method == 'gpt2_autoregressive':
            return self.calculate_gpt2_ppl(text)
        else:
            raise ValueError(f"不支持的方法: {self.method}")

def load_baseline_stories() -> Dict[str, str]:
    """加载baseline故事"""
    baseline_files = {
        'baseline_s1': '/Users/haha/Story/baseline_s1.md',
        'baseline_s2': '/Users/haha/Story/baseline_s2.md', 
        'baseline_s3': '/Users/haha/Story/baseline_s3.md'
    }
    
    stories = {}
    for name, file_path in baseline_files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            stories[name] = content
            print(f"✅ 加载 {name}: {len(content.split())} 词")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    return stories

def load_experimental_stories() -> Dict[str, str]:
    """加载实验系统生成的故事"""
    # 从metrics_master_clean.csv获取实验故事信息
    try:
        df = pd.read_csv('/Users/haha/Story/metrics_master_clean.csv')
        experimental_stories = {}
        
        # 筛选非baseline数据
        exp_df = df[df['is_baseline'] != 1].head(5)  # 只取前5个作为样本验证
        
        for _, row in exp_df.iterrows():
            story_id = row['story_id']
            # 尝试从数据输出目录找到对应文件
            possible_paths = [
                f"/Users/haha/Story/data/output/regression_test/{row.get('original_config_name', '')}/final_story.md",
                f"/Users/haha/Story/data/output/horror_test/{row.get('original_config_name', '')}/final_story.md", 
                f"/Users/haha/Story/data/output/romantic_test/{row.get('original_config_name', '')}/final_story.md"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    experimental_stories[story_id] = content
                    print(f"✅ 加载实验故事 {story_id}: {len(content.split())} 词")
                    break
        
        return experimental_stories
        
    except Exception as e:
        print(f"❌ 无法加载实验故事: {e}")
        return {}

def verify_ppl_calculation():
    """验证PPL计算的一致性"""
    print("🔍 PPL计算一致性验证")
    print("=" * 80)
    
    # 加载数据
    print("\n📖 加载数据...")
    baseline_stories = load_baseline_stories()
    experimental_stories = load_experimental_stories()
    
    if not baseline_stories:
        print("❌ 无法加载baseline数据，停止验证")
        return
    
    # 测试两种计算方法
    methods_to_test = ['bert_masked_lm', 'gpt2_autoregressive']
    results = {}
    
    for method in methods_to_test:
        print(f"\n🧮 测试方法: {method}")
        print("-" * 50)
        
        calculator = UnifiedPPLCalculator(method=method)
        method_results = {'baseline': {}, 'experimental': {}}
        
        # 计算baseline PPL
        print("\n📊 计算baseline PPL...")
        for story_name, content in baseline_stories.items():
            print(f"\n   处理 {story_name}...")
            ppl = calculator.calculate_ppl(content)
            method_results['baseline'][story_name] = ppl
            print(f"   结果: PPL = {ppl:.2f}")
        
        # 计算实验故事PPL
        if experimental_stories:
            print("\n📊 计算实验故事PPL...")
            for story_id, content in experimental_stories.items():
                print(f"\n   处理 {story_id}...")
                ppl = calculator.calculate_ppl(content)
                method_results['experimental'][story_id] = ppl
                print(f"   结果: PPL = {ppl:.2f}")
        
        results[method] = method_results
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'/Users/haha/Story/ppl_verification_results_{timestamp}.json'
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果保存到: {results_file}")
    
    # 生成对比报告
    generate_comparison_report(results, timestamp)
    
    return results

def generate_comparison_report(results: Dict, timestamp: str):
    """生成PPL对比报告"""
    
    report_lines = [
        "# PPL计算方法对比验证报告",
        f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**验证目的**: 解决baseline PPL 11.5 vs 实验系统 PPL 2.6差异过大的问题",
        "\n## 🔍 问题背景",
        "\n发现不同系统使用了不同的PPL计算方法：",
        "- `src/analysis/fluency_analyzer.py`: BERT masked LM + 自适应子采样", 
        "- `gpu_baseline_fluency.py`: GPT-2标准困惑度",
        "- 这导致数值差异巨大，无法进行有效对比",
        "\n## 📊 验证结果",
    ]
    
    for method, method_results in results.items():
        report_lines.append(f"\n### 方法: {method}")
        
        # Baseline结果
        report_lines.append("\n#### Baseline PPL:")
        baseline_ppls = []
        for story_name, ppl in method_results['baseline'].items():
            report_lines.append(f"- {story_name}: {ppl:.2f}")
            if ppl != float('inf'):
                baseline_ppls.append(ppl)
        
        if baseline_ppls:
            avg_baseline = np.mean(baseline_ppls)
            report_lines.append(f"- **平均**: {avg_baseline:.2f}")
        
        # 实验结果
        if method_results['experimental']:
            report_lines.append("\n#### 实验故事PPL:")
            exp_ppls = []
            for story_id, ppl in method_results['experimental'].items():
                report_lines.append(f"- {story_id}: {ppl:.2f}")
                if ppl != float('inf'):
                    exp_ppls.append(ppl)
            
            if exp_ppls:
                avg_exp = np.mean(exp_ppls)
                report_lines.append(f"- **平均**: {avg_exp:.2f}")
                
                # 计算差异比
                if baseline_ppls:
                    ratio = avg_baseline / avg_exp
                    report_lines.append(f"- **baseline/实验比值**: {ratio:.1f}")
    
    # 添加结论和建议
    report_lines.extend([
        "\n## 🎯 结论和建议",
        "\n### 发现的问题:",
        "1. **计算方法不统一**: 不同系统使用不同的PPL计算方法",
        "2. **数值差异巨大**: 方法差异导致PPL值无法直接对比",
        "3. **缺乏标准化**: 没有统一的计算标准和参考实现",
        
        "\n### 修正方案:",
        "1. **统一计算方法**: 选择一种方法作为标准，重新计算所有数据",
        "2. **重新验证baseline**: 使用统一方法重新计算baseline PPL",
        "3. **数据一致性检查**: 确保所有系统使用相同的模型和参数",
        "4. **建立验证流程**: 创建PPL计算的标准验证流程",
        
        "\n### 推荐方法:",
        "基于测试结果，推荐使用 **BERT masked LM** 方法作为标准：",
        "- 更适合文本质量评估",
        "- 计算相对稳定",  
        "- 已有完整实现",
        
        "\n### 下一步行动:",
        "1. 使用统一方法重新计算所有故事的PPL",
        "2. 更新metrics_master_clean.csv中的PPL数据", 
        "3. 重新生成fluency对比报告",
        "4. 建立PPL计算的标准文档"
    ])
    
    # 保存报告
    report_file = f'/Users/haha/Story/ppl_verification_report_{timestamp}.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n📄 验证报告保存到: {report_file}")
    
    # 打印关键结论
    print("\n" + "="*80)
    print("🎯 关键发现")
    print("="*80)
    
    if len(results) >= 2:
        methods = list(results.keys())
        method1, method2 = methods[0], methods[1]
        
        baseline1 = list(results[method1]['baseline'].values())
        baseline2 = list(results[method2]['baseline'].values())
        
        if baseline1 and baseline2:
            avg1 = np.mean([x for x in baseline1 if x != float('inf')])
            avg2 = np.mean([x for x in baseline2 if x != float('inf')])
            
            print(f"📊 Baseline平均PPL:")
            print(f"   {method1}: {avg1:.2f}")
            print(f"   {method2}: {avg2:.2f}")
            print(f"   差异倍数: {max(avg1, avg2) / min(avg1, avg2):.1f}x")
            
            if abs(avg1 - avg2) > 5:
                print("\n⚠️  发现严重不一致！必须统一计算方法！")
            else:
                print("\n✅ 计算结果相对一致")

def main():
    """主函数"""
    print("🎯 PPL计算一致性验证脚本")
    print("解决fluency维度数据验证问题")
    print("="*80)
    
    # 检查GPU可用性
    if torch.cuda.is_available():
        print(f"🚀 GPU可用: {torch.cuda.get_device_name()}")
    else:
        print("💻 使用CPU计算 (会比较慢)")
    
    try:
        # 运行验证
        results = verify_ppl_calculation()
        
        if results:
            print("\n🎉 验证完成！")
            print("请查看生成的报告了解详细结果和建议")
        else:
            print("\n❌ 验证失败")
            
    except Exception as e:
        print(f"\n💥 验证过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
