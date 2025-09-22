#!/usr/bin/env python3
"""
PPL计算一致性验证脚本 - GPU优化版本
专门为GPU环境优化，加速PPL计算

运行方法:
1. 确保有CUDA环境: nvidia-smi
2. 安装依赖: pip install torch transformers pandas numpy
3. 运行脚本: python verify_ppl_calculation_gpu.py
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
import gc
warnings.filterwarnings('ignore')

class GPUOptimizedPPLCalculator:
    """GPU优化的PPL计算器"""
    
    def __init__(self, method='bert_masked_lm', batch_size=32):
        """
        初始化GPU优化PPL计算器
        
        Args:
            method: 'bert_masked_lm' 或 'gpt2_autoregressive'
            batch_size: 批处理大小，GPU内存允许的情况下可以调大
        """
        self.method = method
        self.batch_size = batch_size
        
        # 检查GPU
        if not torch.cuda.is_available():
            print("❌ 未检测到CUDA支持！")
            print("请确保：")
            print("1. 有NVIDIA GPU")
            print("2. 安装了CUDA")
            print("3. 安装了支持CUDA的PyTorch")
            raise RuntimeError("需要GPU支持")
        
        self.device = torch.device('cuda')
        gpu_name = torch.cuda.get_device_name()
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        print(f"🚀 GPU环境检测成功！")
        print(f"   GPU: {gpu_name}")
        print(f"   显存: {gpu_memory:.1f} GB")
        print(f"   方法: {method}")
        print(f"   批大小: {batch_size}")
        
        # 加载模型
        if method == 'bert_masked_lm':
            self.model_name = 'bert-base-uncased'
            print(f"🔄 加载BERT模型...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(self.model_name)
        elif method == 'gpt2_autoregressive':
            self.model_name = 'gpt2'
            print(f"🔄 加载GPT-2模型...")
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        else:
            raise ValueError(f"不支持的方法: {method}")
        
        self.model.to(self.device)
        self.model.eval()
        
        # 清理GPU内存
        torch.cuda.empty_cache()
        
        print(f"✅ 模型加载完成并移至GPU")
        print(f"   GPU内存使用: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
    
    def calculate_bert_pseudo_ppl_gpu(self, text: str, subsample_rate: int = 4) -> float:
        """
        GPU优化的BERT pseudo-PPL计算
        使用批处理加速计算
        """
        if not text or not text.strip():
            return float('inf')
        
        # 分词
        tokens = self.tokenizer.tokenize(text)
        if len(tokens) < 2:
            return float('inf')
        
        # 限制最大长度以适应GPU内存
        max_tokens = 480  # 为特殊token留空间
        if len(tokens) > max_tokens:
            print(f"   文本过长({len(tokens)} tokens)，截取前{max_tokens}个tokens")
            tokens = tokens[:max_tokens]
        
        total_neg_log_likelihood = 0.0
        valid_predictions = 0
        
        # 确保子采样率合理
        actual_subsample_rate = max(1, min(subsample_rate, len(tokens)))
        positions_to_mask = list(range(0, len(tokens), actual_subsample_rate))
        
        print(f"   处理 {len(tokens)} tokens，{len(positions_to_mask)} 个掩码位置")
        
        # 批处理
        batches = [positions_to_mask[i:i+self.batch_size] 
                  for i in range(0, len(positions_to_mask), self.batch_size)]
        
        for batch_idx, batch_positions in enumerate(batches):
            try:
                batch_inputs = []
                batch_original_tokens = []
                batch_mask_positions = []
                
                for pos in batch_positions:
                    if pos >= len(tokens):
                        continue
                    
                    original_token = tokens[pos]
                    
                    # 跳过特殊token
                    if original_token in ['[CLS]', '[SEP]', '[PAD]']:
                        continue
                    
                    # 创建masked版本
                    masked_tokens = ['[CLS]'] + tokens[:pos] + ['[MASK]'] + tokens[pos+1:] + ['[SEP]']
                    
                    # 截断以适应模型限制
                    if len(masked_tokens) > 512:
                        masked_tokens = masked_tokens[:512]
                    
                    input_text = ' '.join(masked_tokens)
                    batch_inputs.append(input_text)
                    batch_original_tokens.append(original_token)
                    
                    # 找到[MASK]在input_ids中的位置
                    temp_encoded = self.tokenizer(input_text, return_tensors='pt')
                    mask_pos = (temp_encoded['input_ids'] == self.tokenizer.mask_token_id).nonzero(as_tuple=True)[1]
                    batch_mask_positions.append(mask_pos[0].item() if len(mask_pos) > 0 else -1)
                
                if not batch_inputs:
                    continue
                
                # 批量编码
                batch_encoded = self.tokenizer(
                    batch_inputs, 
                    padding=True, 
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                )
                
                # 移至GPU
                batch_encoded = {k: v.to(self.device) for k, v in batch_encoded.items()}
                
                with torch.no_grad():
                    outputs = self.model(**batch_encoded)
                    logits = outputs.logits  # [batch_size, seq_len, vocab_size]
                
                # 计算每个样本的log概率
                for i, (original_token, mask_pos) in enumerate(zip(batch_original_tokens, batch_mask_positions)):
                    if mask_pos == -1:
                        continue
                    
                    try:
                        original_token_id = self.tokenizer.convert_tokens_to_ids(original_token)
                        log_probs = torch.log_softmax(logits[i, mask_pos], dim=-1)
                        token_log_prob = log_probs[original_token_id].item()
                        
                        total_neg_log_likelihood += (-token_log_prob)
                        valid_predictions += 1
                        
                    except Exception as e:
                        print(f"      警告: 批次{batch_idx}样本{i}处理出错: {e}")
                        continue
                
                # 清理GPU内存
                del batch_encoded, outputs, logits
                torch.cuda.empty_cache()
                
                if (batch_idx + 1) % 10 == 0:
                    print(f"   处理进度: {batch_idx + 1}/{len(batches)} 批次")
                
            except Exception as e:
                print(f"   批次{batch_idx}处理失败: {e}")
                continue
        
        if valid_predictions == 0:
            return float('inf')
        
        # 计算pseudo-PPL
        avg_neg_log_likelihood = total_neg_log_likelihood / valid_predictions
        pseudo_ppl = math.exp(avg_neg_log_likelihood)
        
        print(f"   ✅ 计算完成: {valid_predictions} 个有效预测，pseudo-PPL = {pseudo_ppl:.2f}")
        return pseudo_ppl
    
    def calculate_gpt2_ppl_gpu(self, text: str) -> float:
        """
        GPU优化的GPT-2困惑度计算
        """
        if not text or not text.strip():
            return float('inf')
        
        # 分块处理长文本
        max_length = 512
        words = text.split()
        
        if len(words) > 400:  # 大概对应512 tokens
            # 分块计算
            chunk_size = 400
            chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            
            total_loss = 0.0
            total_chunks = 0
            
            print(f"   长文本分为{len(chunks)}块处理")
            
            for chunk in chunks:
                inputs = self.tokenizer(chunk, return_tensors='pt', max_length=max_length, truncation=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs, labels=inputs['input_ids'])
                    loss = outputs.loss
                    total_loss += loss.item()
                    total_chunks += 1
                
                # 清理内存
                del inputs, outputs
                torch.cuda.empty_cache()
            
            avg_loss = total_loss / total_chunks
            perplexity = math.exp(avg_loss)
            
        else:
            # 单次计算
            inputs = self.tokenizer(text, return_tensors='pt', max_length=max_length, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs, labels=inputs['input_ids'])
                loss = outputs.loss
                perplexity = torch.exp(loss).item()
            
            # 清理内存
            del inputs, outputs
            torch.cuda.empty_cache()
        
        print(f"   ✅ GPT-2 PPL计算完成: {perplexity:.2f}")
        return perplexity
    
    def calculate_ppl(self, text: str, **kwargs) -> float:
        """统一PPL计算接口"""
        if self.method == 'bert_masked_lm':
            return self.calculate_bert_pseudo_ppl_gpu(text, **kwargs)
        elif self.method == 'gpt2_autoregressive':
            return self.calculate_gpt2_ppl_gpu(text)
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
            word_count = len(content.split())
            print(f"✅ 加载 {name}: {word_count} 词")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    return stories

def get_sample_experimental_stories(limit=3) -> Dict[str, str]:
    """获取少量实验故事样本进行快速验证"""
    try:
        df = pd.read_csv('/Users/haha/Story/metrics_master_clean.csv')
        experimental_stories = {}
        
        # 筛选非baseline数据，只取少量样本
        exp_df = df[df['is_baseline'] != 1].head(limit)
        
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
                    word_count = len(content.split())
                    print(f"✅ 加载实验故事 {story_id}: {word_count} 词")
                    break
        
        return experimental_stories
        
    except Exception as e:
        print(f"❌ 无法加载实验故事: {e}")
        return {}

def quick_gpu_verification():
    """快速GPU验证 - 只测试关键样本"""
    print("🚀 快速GPU PPL验证")
    print("=" * 80)
    
    # 加载数据
    print("\n📖 加载数据...")
    baseline_stories = load_baseline_stories()
    experimental_stories = get_sample_experimental_stories(limit=2)  # 只取2个实验样本
    
    if not baseline_stories:
        print("❌ 无法加载baseline数据，停止验证")
        return
    
    # 只测试BERT方法 (主要方法)
    print(f"\n🧮 使用BERT masked LM方法进行验证")
    print("-" * 50)
    
    calculator = GPUOptimizedPPLCalculator(method='bert_masked_lm', batch_size=16)
    results = {'baseline': {}, 'experimental': {}}
    
    # 计算baseline PPL
    print("\n📊 计算baseline PPL...")
    baseline_ppls = []
    for story_name, content in baseline_stories.items():
        print(f"\n🔄 处理 {story_name}...")
        
        start_time = datetime.now()
        ppl = calculator.calculate_ppl(content, subsample_rate=4)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        results['baseline'][story_name] = ppl
        
        print(f"   ✅ 结果: PPL = {ppl:.2f} (耗时: {duration:.1f}秒)")
        
        if ppl != float('inf'):
            baseline_ppls.append(ppl)
    
    # 计算实验故事PPL
    experimental_ppls = []
    if experimental_stories:
        print("\n📊 计算实验故事PPL...")
        for story_id, content in experimental_stories.items():
            print(f"\n🔄 处理 {story_id}...")
            
            start_time = datetime.now()
            ppl = calculator.calculate_ppl(content, subsample_rate=4)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            results['experimental'][story_id] = ppl
            
            print(f"   ✅ 结果: PPL = {ppl:.2f} (耗时: {duration:.1f}秒)")
            
            if ppl != float('inf'):
                experimental_ppls.append(ppl)
    
    # 立即显示关键结果
    print("\n" + "="*80)
    print("🎯 关键发现")
    print("="*80)
    
    if baseline_ppls:
        baseline_avg = np.mean(baseline_ppls)
        baseline_std = np.std(baseline_ppls)
        print(f"\n📊 Baseline PPL统计:")
        print(f"   平均值: {baseline_avg:.2f} ± {baseline_std:.2f}")
        print(f"   范围: {min(baseline_ppls):.2f} - {max(baseline_ppls):.2f}")
        
        # 和之前报告的11.5对比
        print(f"\n❗ 对比之前的报告:")
        print(f"   之前报告的baseline PPL: 11.5")
        print(f"   重新计算的baseline PPL: {baseline_avg:.2f}")
        
        if abs(baseline_avg - 11.5) > 2:
            print(f"   ⚠️  差异显著: {abs(baseline_avg - 11.5):.1f}点差异")
        else:
            print(f"   ✅ 差异合理: {abs(baseline_avg - 11.5):.1f}点差异")
    
    if experimental_ppls:
        exp_avg = np.mean(experimental_ppls)
        exp_std = np.std(experimental_ppls)
        print(f"\n📊 实验样本PPL统计:")
        print(f"   平均值: {exp_avg:.2f} ± {exp_std:.2f}")
        print(f"   范围: {min(experimental_ppls):.2f} - {max(experimental_ppls):.2f}")
        
        # 和之前报告的2.6对比
        print(f"\n❗ 对比之前的报告:")
        print(f"   之前报告的实验PPL: 2.6")
        print(f"   重新计算的实验PPL: {exp_avg:.2f}")
        
        if abs(exp_avg - 2.6) > 1:
            print(f"   ⚠️  差异显著: {abs(exp_avg - 2.6):.1f}点差异")
        else:
            print(f"   ✅ 差异合理: {abs(exp_avg - 2.6):.1f}点差异")
    
    # 计算比值
    if baseline_ppls and experimental_ppls:
        ratio = baseline_avg / exp_avg
        print(f"\n📈 PPL比值分析:")
        print(f"   baseline/experimental = {ratio:.1f}")
        print(f"   之前报告的比值: {11.5/2.6:.1f}")
        
        if abs(ratio - 11.5/2.6) > 1:
            print(f"   ⚠️  比值差异较大，需要进一步调查")
        else:
            print(f"   ✅ 比值相对一致")
    
    # 保存快速验证结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f'/Users/haha/Story/gpu_ppl_quick_verification_{timestamp}.json'
    
    full_results = {
        'method': 'bert_masked_lm',
        'timestamp': timestamp,
        'baseline_stats': {
            'mean': baseline_avg if baseline_ppls else None,
            'std': baseline_std if baseline_ppls else None,
            'values': results['baseline']
        },
        'experimental_stats': {
            'mean': exp_avg if experimental_ppls else None,
            'std': exp_std if experimental_ppls else None,
            'values': results['experimental']
        },
        'comparison': {
            'baseline_reported': 11.5,
            'experimental_reported': 2.6,
            'ratio_reported': 11.5/2.6,
            'ratio_calculated': ratio if (baseline_ppls and experimental_ppls) else None
        }
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 快速验证结果保存到: {results_file}")
    
    return full_results

def main():
    """主函数"""
    print("🎯 GPU优化PPL计算验证")
    print("快速验证fluency维度数据一致性问题")
    print("="*80)
    
    # 检查GPU
    try:
        gpu_info = torch.cuda.get_device_name() if torch.cuda.is_available() else "无GPU"
        print(f"🖥️  硬件环境: {gpu_info}")
        
        if not torch.cuda.is_available():
            print("\n❌ 需要GPU环境!")
            print("请在有NVIDIA GPU的机器上运行")
            print("或使用CPU版本: verify_ppl_calculation.py")
            return
    except:
        print("❌ GPU环境检查失败")
        return
    
    try:
        # 运行快速验证
        results = quick_gpu_verification()
        
        if results:
            print("\n🎉 GPU快速验证完成！")
            print("\n📋 下一步建议:")
            print("1. 如果发现显著差异，需要统一PPL计算方法")
            print("2. 重新计算所有故事的PPL数据")
            print("3. 更新metrics_master_clean.csv")
        else:
            print("\n❌ 验证失败")
            
    except Exception as e:
        print(f"\n💥 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print(f"\n🧹 GPU内存已清理")

if __name__ == "__main__":
    main()
