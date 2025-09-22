#!/usr/bin/env python3
"""
GPU版本baseline流畅性分析 - 自包含版本
用于在GPU服务器上运行
"""

import os
import json
import time
from datetime import datetime

def install_dependencies():
    """安装必要的依赖"""
    print("🔧 安装必要的依赖...")
    os.system("pip install transformers torch datasets pandas numpy")
    print("✅ 依赖安装完成")

class SimpleFluencyAnalyzer:
    """简化版流畅性分析器 - GPU专用"""
    
    def __init__(self):
        """初始化分析器"""
        print("🚀 初始化GPU流畅性分析器...")
        
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForMaskedLM
            import torch
            
            # 检查GPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"🔥 使用设备: {device}")
            
            # 使用RoBERTa-large进行流畅性评估
            model_name = "roberta-large"
            print(f"📦 加载模型: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(model_name).to(device)
            self.device = device
            
            print("✅ 模型加载完成")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def calculate_perplexity(self, text):
        """计算伪困惑度"""
        import torch
        
        # 分词
        tokens = self.tokenizer.encode(text, return_tensors='pt', truncation=True, max_length=512)
        tokens = tokens.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(tokens, labels=tokens)
            loss = outputs.loss
            perplexity = torch.exp(loss).item()
        
        return perplexity
    
    def count_grammar_errors(self, text):
        """简单的语法错误计数"""
        import re
        
        errors = 0
        
        # 检查常见错误模式
        error_patterns = [
            r'\s+[.!?]',  # 标点前的空格
            r'[.!?]{2,}',  # 重复标点
            r'\b[a-z]+[A-Z]',  # 单词内大小写错误
            r'\s{2,}',  # 多余空格
        ]
        
        for pattern in error_patterns:
            errors += len(re.findall(pattern, text))
        
        return errors
    
    def analyze_fluency(self, text):
        """分析文本流畅性"""
        print("🔍 分析流畅性...")
        
        # 基本统计
        words = text.split()
        word_count = len(words)
        
        # 计算困惑度
        try:
            perplexity = self.calculate_perplexity(text)
        except Exception as e:
            print(f"⚠️  困惑度计算失败: {e}")
            perplexity = float('inf')
        
        # 语法错误
        error_count = self.count_grammar_errors(text)
        err_per_100w = (error_count / word_count) * 100 if word_count > 0 else 0
        
        result = {
            'pseudo_ppl': perplexity,
            'error_count': error_count,
            'err_per_100w': err_per_100w,
            'word_count': word_count,
            'char_count': len(text),
            'analysis_time': datetime.now().isoformat()
        }
        
        print(f"   ✅ PPL: {perplexity:.2f}, 错误率: {err_per_100w:.2f}%, 词数: {word_count}")
        return result

def analyze_baseline_files():
    """分析所有baseline文件"""
    
    # baseline文件列表
    baseline_files = {
        'baseline_s1': 'baseline_s1.md',
        'baseline_s2': 'baseline_s2.md', 
        'baseline_s3': 'normal_baseline.md'
    }
    
    print("🎯 开始GPU流畅性分析")
    print("=" * 60)
    
    # 检查文件
    missing_files = []
    for name, filename in baseline_files.items():
        if not os.path.exists(filename):
            missing_files.append(filename)
            print(f"❌ {name}: {filename} - 文件不存在")
        else:
            size = os.path.getsize(filename)
            print(f"✅ {name}: {filename} ({size:,} bytes)")
    
    if missing_files:
        print(f"\n❌ 缺少 {len(missing_files)} 个文件，请上传后再运行")
        return None
    
    # 初始化分析器
    try:
        analyzer = SimpleFluencyAnalyzer()
    except Exception as e:
        print(f"❌ 分析器初始化失败: {e}")
        return None
    
    # 分析每个文件
    results = {}
    
    for baseline_name, filename in baseline_files.items():
        print(f"\n📝 [{baseline_name}] 分析 {filename}...")
        
        # 读取文件
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            continue
        
        # 分析流畅性
        try:
            result = analyzer.analyze_fluency(content)
            result['baseline_name'] = baseline_name
            result['source_file'] = filename
            
            results[baseline_name] = result
            
            # 保存单个结果
            output_file = f"{baseline_name}_fluency_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"   💾 结果保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            continue
    
    # 保存汇总结果
    if results:
        summary_file = "baseline_fluency_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n🎉 GPU流畅性分析完成!")
        print(f"📊 成功分析: {len(results)}/{len(baseline_files)} 个文件")
        print(f"📁 汇总结果: {summary_file}")
        
        # 显示结果概览
        print(f"\n📋 分析结果概览:")
        print("-" * 60)
        for name, result in results.items():
            print(f"• {name}:")
            print(f"  - PPL: {result['pseudo_ppl']:.2f}")
            print(f"  - 错误率: {result['err_per_100w']:.2f}%")
            print(f"  - 词数: {result['word_count']:,}")
    
    return results

def main():
    """主函数"""
    print("🚀 GPU Baseline流畅性分析系统")
    print("=" * 60)
    print("此脚本将使用GPU分析3个baseline文件的流畅性")
    print("确保已上传以下文件:")
    print("• baseline_s1.md")
    print("• baseline_s2.md") 
    print("• normal_baseline.md")
    print("=" * 60)
    
    try:
        # 安装依赖
        install_dependencies()
        
        # 运行分析
        results = analyze_baseline_files()
        
        if results:
            print("\n✨ 成功! 请下载以下结果文件:")
            print("• baseline_fluency_summary.json (汇总)")
            print("• baseline_s1_fluency_result.json")
            print("• baseline_s2_fluency_result.json")
            print("• baseline_s3_fluency_result.json")
            
            return True
        else:
            print("❌ 分析失败")
            return False
            
    except Exception as e:
        print(f"💥 程序异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
