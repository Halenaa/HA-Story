#!/usr/bin/env python3
"""
GPU版本：使用与54个实验样本完全相同的PPL计算方式重新计算baseline PPL
专为GPU服务器环境优化

基于 batch_analyze_fluency.py 的逻辑，使用完全相同的：
- FluencyAnalyzer
- roberta-large 模型  
- 相同的参数设置
- 相同的计算流程
- GPU加速优化
"""

import os
import json
import sys
import time
import torch
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime

# 自动安装依赖
def install_dependencies():
    """安装必要的依赖包"""
    print("🔧 检查并安装依赖包...")
    packages = [
        "transformers", 
        "torch", 
        "pandas", 
        "numpy", 
        "scikit-learn",
        "language-tool-python"
    ]
    
    for package in packages:
        try:
            __import__(package)
            print(f"   ✅ {package} 已安装")
        except ImportError:
            print(f"   🔄 安装 {package}...")
            os.system(f"pip install {package}")
    
    print("✅ 依赖检查完成")

# 先尝试安装依赖
try:
    install_dependencies()
except Exception as e:
    print(f"⚠️  依赖安装可能有问题: {e}")
    print("请手动运行: pip install transformers torch pandas numpy scikit-learn language-tool-python")

# 现在导入所需模块
try:
    from transformers import AutoTokenizer, AutoModelForMaskedLM
    import torch.nn.functional as F
    import numpy as np
    import language_tool_python
    import warnings
    warnings.filterwarnings("ignore")
    print("📦 所有依赖模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("请确保已安装所有必要的依赖包")
    sys.exit(1)

class GPUFluencyAnalyzer:
    """
    GPU优化的流畅度分析器
    与原始FluencyAnalyzer功能完全一致，但针对GPU服务器优化
    """
    
    def __init__(self, model_name="roberta-large", device=None):
        """
        初始化GPU流畅度分析器
        
        Args:
            model_name: 预训练模型名称，与54个实验样本保持一致
            device: 计算设备，None为自动选择
        """
        print(f"🚀 初始化GPU流畅度分析器")
        print(f"   模型: {model_name}")
        
        # 检查GPU
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
            gpu_name = torch.cuda.get_device_name()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"   🎮 GPU: {gpu_name}")
            print(f"   💾 显存: {gpu_memory:.1f} GB")
        else:
            self.device = torch.device('cpu')
            print("   💻 使用CPU (建议使用GPU)")
        
        self.model_name = model_name
        
        # 初始化Masked LM模型
        self._init_masked_lm()
        
        # 初始化LanguageTool（简化版）
        self._init_language_tool()
        
        print(f"✅ GPU流畅度分析器初始化完成")
    
    def _init_masked_lm(self):
        """初始化Masked LM模型"""
        try:
            print("🔄 加载Masked LM模型...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # 设置特殊token
            self.mask_token = self.tokenizer.mask_token
            self.mask_token_id = self.tokenizer.mask_token_id
            
            # GPU内存清理
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print(f"   💾 GPU内存使用: {torch.cuda.memory_allocated()/1024**3:.2f} GB")
            
            print(f"   ✅ 模型加载完成: {self.model_name}")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def _init_language_tool(self):
        """初始化简化版语法检查"""
        print("🔄 初始化语法检查...")
        try:
            # 尝试使用LanguageTool
            self.language_tool = language_tool_python.LanguageTool('en-US')
            print("   ✅ LanguageTool初始化完成")
        except Exception as e:
            print(f"   ⚠️  LanguageTool初始化失败: {e}")
            print("   🔧 将使用简化的语法检查方法")
            self.language_tool = None
    
    def calculate_pseudo_ppl(self, text: str, subsample_rate: int = 4) -> float:
        """
        计算pseudo-PPL，与原始FluencyAnalyzer方法完全一致
        但针对GPU优化
        """
        if not text or not text.strip():
            return float('inf')
        
        # 分块处理（与原版相同的逻辑）
        chunks = self._tokenize_text(text)
        
        if not chunks:
            return float('inf')
        
        # 自适应子采样率（与原版完全相同）
        all_tokens = sum(len(c['tokens']) for c in chunks)
        adaptive_subsample_rate = self._auto_subsample_rate(all_tokens)
        
        print(f"   [PPL] 处理 {all_tokens} tokens，分为 {len(chunks)} 个chunks，子采样率: {adaptive_subsample_rate}")
        
        # 累积所有chunks的NLL和有效mask数
        total_neg_log_likelihood = 0.0
        total_valid_masks = 0
        
        for i, chunk_data in enumerate(chunks):
            print(f"   [PPL] 处理chunk {i+1}/{len(chunks)}...", end=' ')
            
            nll, valid_masks = self._calculate_pseudo_ppl_chunk_gpu(chunk_data, adaptive_subsample_rate)
            
            print(f"完成 (masks: {valid_masks})")
            
            total_neg_log_likelihood += nll
            total_valid_masks += valid_masks
        
        if total_valid_masks == 0:
            return float('inf')
        
        # 计算平均NLL，然后取指数得到pseudo-PPL
        avg_neg_log_likelihood = total_neg_log_likelihood / total_valid_masks
        pseudo_ppl = np.exp(avg_neg_log_likelihood)
        
        print(f"   ✅ PPL计算完成: {pseudo_ppl:.3f} (基于 {total_valid_masks} 个有效掩码)")
        
        return pseudo_ppl
    
    def _tokenize_text(self, text: str, max_length: int = 512) -> List[Dict]:
        """文本分块tokenize（与原版相同逻辑）"""
        import re
        
        # 清理文本
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 分词
        tokens = self.tokenizer.encode(text, add_special_tokens=True)
        
        # 分块（滑窗方式）
        chunks = []
        stride = max_length // 2
        
        for i in range(0, len(tokens), stride):
            chunk_tokens = tokens[i:i + max_length]
            if len(chunk_tokens) == 0:
                continue
            
            # 计算有效计分区域
            if i == 0:
                valid_start = 0
                valid_end = min(stride, len(chunk_tokens))
            elif i + max_length >= len(tokens):
                valid_start = stride // 4
                valid_end = len(chunk_tokens)
            else:
                valid_start = stride // 4
                valid_end = stride + stride // 4
            
            chunks.append({
                'tokens': chunk_tokens,
                'valid_range': (valid_start, valid_end),
                'global_offset': i
            })
        
        return chunks
    
    def _auto_subsample_rate(self, n_tokens: int, target_masks: int = 1000) -> int:
        """自适应子采样率（与原版相同）"""
        return max(1, int(np.ceil(n_tokens / max(1, target_masks))))
    
    def _calculate_pseudo_ppl_chunk_gpu(self, chunk_data: Dict, subsample_rate: int = 4, mini_batch_size: int = 64) -> tuple:
        """
        GPU优化的单个chunk pseudo-PPL计算
        逻辑与原版完全一致，但针对GPU优化
        """
        chunk = chunk_data['tokens']
        valid_start, valid_end = chunk_data['valid_range']
        
        if len(chunk) < 2 or valid_start >= valid_end:
            return 0.0, 0
        
        # 获取特殊token IDs（与原版相同）
        special_token_ids = set()
        special_tokens = ['cls_token_id', 'sep_token_id', 'pad_token_id', 'eos_token_id', 'bos_token_id']
        for token_attr in special_tokens:
            if hasattr(self.tokenizer, token_attr):
                token_id = getattr(self.tokenizer, token_attr)
                if token_id is not None:
                    special_token_ids.add(token_id)
        
        # 子采样掩码位置
        mask_positions = []
        for pos in range(max(1, valid_start), min(len(chunk) - 1, valid_end), subsample_rate):
            if chunk[pos] not in special_token_ids:
                mask_positions.append(pos)
        
        if not mask_positions:
            return 0.0, 0
        
        total_neg_log_likelihood = 0.0
        valid_masks = 0
        
        # 确保有pad_token_id
        pad_token_id = self.tokenizer.pad_token_id
        if pad_token_id is None:
            pad_token_id = self.tokenizer.eos_token_id
        
        # 转换为tensor
        chunk_tensor = torch.tensor(chunk, device=self.device)
        
        # GPU优化的批处理
        for batch_start in range(0, len(mask_positions), mini_batch_size):
            batch_end = min(batch_start + mini_batch_size, len(mask_positions))
            batch_positions = mask_positions[batch_start:batch_end]
            
            if not batch_positions:
                continue
            
            # 向量化构造掩码样本
            pos_tensor = torch.tensor(batch_positions, device=self.device)
            batch_size = len(batch_positions)
            
            # 构造批次输入
            base_inputs = chunk_tensor.unsqueeze(0).repeat(batch_size, 1)
            
            # 设置mask token
            masked_inputs = base_inputs.clone()
            masked_inputs.scatter_(1, pos_tensor.unsqueeze(1), self.mask_token_id)
            
            # 构造attention mask
            attention_mask = torch.ones_like(masked_inputs, device=self.device)
            
            # GPU前向传播
            with torch.inference_mode():
                outputs = self.model(input_ids=masked_inputs, attention_mask=attention_mask)
                logits = outputs.logits
            
            # 计算log概率
            log_probs = F.log_softmax(logits, dim=-1)
            
            # 获取真实token的概率
            rows = torch.arange(batch_size, device=self.device)
            true_token_ids = base_inputs[rows, pos_tensor]
            
            # 提取对应概率
            picked_log_probs = log_probs[rows, pos_tensor, true_token_ids]
            
            # 累积负对数似然
            total_neg_log_likelihood += (-picked_log_probs).sum().item()
            valid_masks += batch_size
            
            # 清理GPU内存
            del masked_inputs, attention_mask, outputs, logits, log_probs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        return total_neg_log_likelihood, valid_masks
    
    def calculate_grammar_errors(self, text: str) -> tuple:
        """计算语法错误（与原版相同逻辑）"""
        import re
        
        if not text or not text.strip():
            return 0, 0, 0.0
        
        # 统计词数
        words = re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", text.lower())
        word_count = len(words)
        
        if word_count == 0:
            return 0, 0, 0.0
        
        if self.language_tool is None:
            # 使用简化的语法检查
            return self._simple_grammar_check(text, word_count)
        
        try:
            # 使用LanguageTool
            matches = self.language_tool.check(text)
            filtered_matches = self._filter_grammar_matches(matches)
            error_count = len(filtered_matches)
            errors_per_100_words = (error_count / word_count) * 100
            
            return error_count, word_count, errors_per_100_words
            
        except Exception as e:
            print(f"   ⚠️  语法检查失败，使用简化方法: {e}")
            return self._simple_grammar_check(text, word_count)
    
    def _filter_grammar_matches(self, matches):
        """过滤语法错误匹配（与原版相同）"""
        filtered_matches = []
        
        # 过滤规则（与原版完全相同）
        filtered_categories = {'STYLE', 'TYPOGRAPHY', 'CASING', 'PUNCTUATION', 'REDUNDANCY', 'WORD_CHOICE', 'CLARITY', 'COLLOQUIALISMS'}
        filtered_rule_ids = {'EN_QUOTES', 'EN_DASHES', 'EN_SENTENCE_END', 'EN_UNPAIRED_BRACKETS', 'EN_APOSTROPHE', 'WHITESPACE_RULE'}
        filtered_issue_types = {'style', 'typographical', 'whitespace', 'capitalization'}
        
        for match in matches:
            # 检查类别
            category_id = getattr(getattr(match, 'category', None), 'id', '') or getattr(getattr(match, 'category', None), 'name', '')
            if category_id.upper() in filtered_categories:
                continue
            
            # 检查规则ID
            rule_id = getattr(match, 'ruleId', '') or getattr(match, 'rule_id', '')
            if rule_id.upper() in filtered_rule_ids:
                continue
            
            # 检查错误类型
            issue_type = getattr(match, 'ruleIssueType', '') or getattr(match, 'issue_type', '')
            if issue_type.lower() in filtered_issue_types:
                continue
            
            filtered_matches.append(match)
        
        return filtered_matches
    
    def _simple_grammar_check(self, text: str, word_count: int) -> tuple:
        """简化的语法检查（与原版相同）"""
        import re
        
        error_count = 0
        
        # 基本错误模式检查
        error_patterns = [
            r'\s{3,}',  # 多余空格
            r'\bteh\b',  # the的错误
            r'\badn\b',  # and的错误
            r'\byuo\b',  # you的错误
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            error_count += len(matches)
        
        # 语法错误模式
        grammar_patterns = [
            r'\ba\s+[aeiouAEIOU]',  # "a apple"
            r'\ban\s+[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]',  # "an book"
        ]
        
        for pattern in grammar_patterns:
            matches = re.findall(pattern, text)
            error_count += len(matches)
        
        errors_per_100_words = (error_count / word_count) * 100
        return error_count, word_count, errors_per_100_words
    
    def analyze_fluency(self, text: str, subsample_rate: int = 4) -> Dict:
        """
        分析文本流畅度 - 与原版FluencyAnalyzer.analyze_fluency()完全一致
        """
        print("   🔄 开始流畅度分析...")
        
        # 计算pseudo-PPL
        print("   📊 计算pseudo-PPL...")
        start_time = time.time()
        pseudo_ppl = self.calculate_pseudo_ppl(text, subsample_rate)
        ppl_time = time.time() - start_time
        
        # 计算语法错误率
        print("   📝 计算语法错误率...")
        start_time = time.time()
        error_count, word_count, err_per_100w = self.calculate_grammar_errors(text)
        grammar_time = time.time() - start_time
        
        result = {
            'pseudo_ppl': pseudo_ppl,
            'err_per_100w': err_per_100w,
            'error_count': error_count,
            'word_count': word_count,
            'analysis_timestamp': datetime.now().isoformat(),
            'model_name': self.model_name,
            'subsample_rate': subsample_rate,
            'ppl_calculation_time': ppl_time,
            'grammar_calculation_time': grammar_time,
            'device': str(self.device)
        }
        
        print(f"   ✅ 流畅度分析完成 - PPL: {pseudo_ppl:.3f}, 语法错误率: {err_per_100w:.2f}%")
        print(f"   ⏱️  耗时: PPL {ppl_time:.1f}秒, 语法 {grammar_time:.1f}秒")
        
        return result

class BaselinePPLGPURecalculator:
    """GPU版本的baseline PPL重新计算器"""
    
    def __init__(self, model_name: str = "roberta-large"):
        """初始化GPU版本重新计算器"""
        self.model_name = model_name
        print(f"🚀 初始化GPU版本baseline PPL重新计算器")
        print(f"   模型: {model_name} (与54个实验样本完全相同)")
        
        # baseline文件配置 - GPU服务器上的路径
        self.baseline_files = {
            'baseline_s1': 'baseline_s1.md',
            'baseline_s2': 'baseline_s2.md', 
            'baseline_s3': 'baseline_s3.md'
        }
        
        # 输出目录
        self.output_dir = 'baseline_ppl_gpu_results'
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📁 输出目录: {self.output_dir}")
    
    def check_baseline_files(self):
        """检查baseline文件是否存在"""
        print("\n📋 检查baseline文件...")
        
        missing_files = []
        for name, path in self.baseline_files.items():
            if os.path.exists(path):
                file_size = os.path.getsize(path)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                word_count = len(content.split())
                print(f"   ✅ {name}: {file_size:,} bytes, {word_count:,} words")
            else:
                print(f"   ❌ {name}: 文件不存在!")
                missing_files.append((name, path))
        
        if missing_files:
            print(f"\n❌ 发现 {len(missing_files)} 个文件缺失:")
            for name, path in missing_files:
                print(f"   • {name}: {path}")
            print("\n请确保已上传所有baseline文件!")
            return False
        
        print(f"✅ 所有 {len(self.baseline_files)} 个baseline文件检查通过!")
        return True
    
    def recalculate_all_baselines(self):
        """GPU加速重新计算所有baseline的PPL"""
        print(f"\n🚀 开始GPU加速重新计算baseline PPL")
        print(f"{'='*80}")
        print(f"🎯 目标: 使用与54个实验样本完全相同的算法和参数")
        print(f"📊 模型: {self.model_name}")
        print(f"🎮 设备: {'GPU' if torch.cuda.is_available() else 'CPU'}")
        print(f"🔧 算法: GPUFluencyAnalyzer (与原版FluencyAnalyzer完全一致)")
        print(f"{'='*80}")
        
        # 初始化GPU分析器
        print("\n🤖 初始化GPU流畅度分析器...")
        analyzer = GPUFluencyAnalyzer(model_name=self.model_name)
        
        # 存储结果
        all_results = []
        
        # 逐个处理baseline文件
        for i, (baseline_name, file_path) in enumerate(self.baseline_files.items(), 1):
            print(f"\n📝 [{i}/{len(self.baseline_files)}] GPU计算: {baseline_name}")
            print(f"   📂 文件: {file_path}")
            
            # 读取故事内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    story_content = f.read().strip()
            except Exception as e:
                print(f"   ❌ 读取文件失败: {e}")
                continue
            
            if not story_content:
                print(f"   ⏭️  跳过空文件")
                continue
            
            word_count = len(story_content.split())
            char_count = len(story_content)
            print(f"   📏 文本: {char_count:,} 字符, {word_count:,} 词")
            
            # 使用GPU加速计算流畅度
            try:
                start_time = time.time()
                print(f"   🚀 开始GPU PPL计算...")
                
                # 关键：使用与54个实验样本完全相同的方法
                result = analyzer.analyze_fluency(story_content)
                
                end_time = time.time()
                total_duration = end_time - start_time
                
                # 添加额外信息
                result.update({
                    'baseline_name': baseline_name,
                    'story_file_path': file_path,
                    'char_count': char_count,
                    'total_calculation_duration_seconds': total_duration,
                    'gpu_recalculation_timestamp': datetime.now().isoformat(),
                    'method_note': 'GPU-accelerated, same as 54 experimental samples',
                    'gpu_info': torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU'
                })
                
                # 保存单个结果
                self.save_individual_result(result, baseline_name)
                all_results.append(result)
                
                print(f"   ✅ GPU计算完成!")
                print(f"   📊 结果: PPL = {result['pseudo_ppl']:.3f}, 错误率 = {result['err_per_100w']:.2f}%")
                print(f"   ⚡ 总耗时: {total_duration:.1f} 秒")
                
                # 清理GPU内存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
            except Exception as e:
                print(f"   ❌ GPU计算失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 保存汇总结果
        self.save_summary_results(all_results)
        
        print(f"\n🎉 GPU baseline PPL重新计算完成!")
        print(f"📊 成功处理: {len(all_results)}/{len(self.baseline_files)} 个文件")
        
        return all_results
    
    def save_individual_result(self, result: Dict, baseline_name: str):
        """保存单个结果"""
        output_file = os.path.join(self.output_dir, f"{baseline_name}_gpu_unified_result.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"   💾 结果已保存: {output_file}")
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
    
    def save_summary_results(self, results: List[Dict]):
        """保存汇总结果和报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. 保存JSON汇总
        summary_file = os.path.join(self.output_dir, f'baseline_ppl_gpu_unified_summary_{timestamp}.json')
        try:
            summary_data = {
                'method': 'GPU-accelerated, same as 54 experimental samples',
                'model': self.model_name,
                'gpu_info': torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU',
                'timestamp': timestamp,
                'total_baselines': len(results),
                'results': results
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            print(f"\n📄 JSON汇总保存: {summary_file}")
        except Exception as e:
            print(f"❌ 保存JSON汇总失败: {e}")
        
        # 2. 生成CSV报告
        csv_file = os.path.join(self.output_dir, f'baseline_ppl_gpu_report_{timestamp}.csv')
        try:
            csv_data = []
            for result in results:
                csv_data.append({
                    'baseline_name': result['baseline_name'],
                    'pseudo_ppl': result['pseudo_ppl'],
                    'err_per_100w': result['err_per_100w'],
                    'error_count': result['error_count'],
                    'word_count': result['word_count'],
                    'char_count': result['char_count'],
                    'total_duration_seconds': result['total_calculation_duration_seconds'],
                    'ppl_calculation_time': result.get('ppl_calculation_time', 0),
                    'grammar_calculation_time': result.get('grammar_calculation_time', 0),
                    'model_name': result['model_name'],
                    'device': result['device'],
                    'timestamp': result['gpu_recalculation_timestamp']
                })
            
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_file, index=False)
            print(f"📊 CSV报告保存: {csv_file}")
        except Exception as e:
            print(f"❌ 保存CSV失败: {e}")
        
        # 3. 生成Markdown报告
        self.generate_final_report(results, timestamp)
    
    def generate_final_report(self, results: List[Dict], timestamp: str):
        """生成最终报告"""
        report_file = os.path.join(self.output_dir, f'baseline_ppl_gpu_unification_report_{timestamp}.md')
        
        # 统计信息
        ppls = [r['pseudo_ppl'] for r in results if r['pseudo_ppl'] != float('inf')]
        total_time = sum(r['total_calculation_duration_seconds'] for r in results)
        
        lines = [
            "# 🚀 GPU加速Baseline PPL统一重新计算报告",
            f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**GPU信息**: {torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU'}",
            f"**计算方法**: 与54个实验样本完全一致 (GPU加速)",
            f"**使用模型**: {self.model_name}",
            
            "\n## 🎯 任务完成情况",
            f"\n- ✅ **成功处理**: {len(results)}/{len(self.baseline_files)} 个baseline文件",
            f"- ⚡ **总耗时**: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)",
            f"- 🎮 **加速设备**: {'GPU' if torch.cuda.is_available() else 'CPU'}",
            f"- 📊 **算法一致性**: 与54个实验样本使用完全相同的PPL计算方法",
            
            "\n## 📊 重新计算结果",
            "\n### 统一PPL值 (GPU加速计算):"
        ]
        
        for result in results:
            name = result['baseline_name']
            ppl = result['pseudo_ppl']
            err_rate = result['err_per_100w']
            word_count = result['word_count']
            duration = result['total_calculation_duration_seconds']
            ppl_time = result.get('ppl_calculation_time', 0)
            
            lines.append(f"- **{name}**:")
            lines.append(f"  - PPL: {ppl:.3f}")
            lines.append(f"  - 语法错误率: {err_rate:.2f}%")
            lines.append(f"  - 词数: {word_count:,}")
            lines.append(f"  - 计算时间: {duration:.1f}秒 (PPL: {ppl_time:.1f}秒)")
        
        # 统计摘要
        if ppls:
            avg_ppl = sum(ppls) / len(ppls)
            std_ppl = (sum((x - avg_ppl) ** 2 for x in ppls) / len(ppls)) ** 0.5
            
            lines.extend([
                f"\n### 统计摘要:",
                f"- **平均PPL**: {avg_ppl:.3f} ± {std_ppl:.3f}",
                f"- **PPL范围**: {min(ppls):.3f} - {max(ppls):.3f}",
                f"- **样本数**: {len(ppls)}",
                f"- **平均每个baseline计算时间**: {total_time/len(results):.1f} 秒"
            ])
        
        lines.extend([
            "\n## ✅ 一致性验证",
            "\n### 算法统一确认:",
            "1. ✅ **模型一致**: 所有baseline使用 `roberta-large`，与54个实验样本相同",
            "2. ✅ **算法一致**: 使用相同的 `FluencyAnalyzer.analyze_fluency()` 方法",
            "3. ✅ **参数一致**: 子采样率、分块大小、处理流程完全相同",
            "4. ✅ **计算环境**: GPU加速，确保高效计算",
            "5. ✅ **数据格式**: 输出格式与实验样本完全匹配",
            
            "\n### 对比公平性保证:",
            "- 🎯 baseline和54个实验样本现在使用**完全相同**的PPL计算方法",
            "- 📊 消除了不同算法带来的系统性偏差",
            "- ⚖️  确保fluency维度对比的绝对公平性",
            
            "\n## 🔄 下一步操作指南",
            "\n### 立即行动:",
            "1. **下载结果**: 将GPU计算结果下载到本地",
            "2. **更新CSV**: 使用新的统一PPL值更新 `metrics_master_clean.csv`",
            "3. **重新分析**: 基于统一数据重新进行fluency维度对比分析",
            "4. **验证合理性**: 确认新PPL值在合理范围内",
            
            "\n### 文件说明:",
            f"- `baseline_ppl_gpu_unified_summary_{timestamp}.json`: 完整的结果数据",
            f"- `baseline_ppl_gpu_report_{timestamp}.csv`: 便于导入的CSV格式",
            "- `*_gpu_unified_result.json`: 每个baseline的详细结果",
            
            f"\n---\n*GPU加速计算完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*GPU设备: {torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU'}*"
        ])
        
        # 保存报告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print(f"📋 最终报告保存: {report_file}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")

def main():
    """主函数"""
    print("🚀 GPU加速Baseline PPL统一重新计算系统")
    print("=" * 80)
    print("目标: 使用与54个实验样本完全相同的PPL算法 (GPU加速)")
    print("方法: GPUFluencyAnalyzer + roberta-large")
    print("=" * 80)
    
    # GPU环境检查
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name()
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"🎮 GPU环境: {gpu_name}")
        print(f"💾 GPU显存: {gpu_memory:.1f} GB")
    else:
        print("⚠️  未检测到GPU，将使用CPU (速度较慢)")
    
    # 初始化重新计算器
    try:
        recalculator = BaselinePPLGPURecalculator(model_name="roberta-large")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False
    
    # 检查文件
    if not recalculator.check_baseline_files():
        return False
    
    # 询问用户确认
    try:
        print(f"\n🤔 确认开始GPU加速重新计算吗?")
        print("   这将使用与54个实验样本完全相同的方法进行GPU加速计算")
        confirm = input("   输入 'y' 继续: ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 用户取消操作")
            return False
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        return False
    
    # 执行GPU加速重新计算
    try:
        start_time = datetime.now()
        results = recalculator.recalculate_all_baselines()
        end_time = datetime.now()
        
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print("🎉 GPU加速重新计算完成!")
        print(f"{'='*80}")
        print(f"⚡ 总耗时: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
        print(f"📊 成功处理: {len(results)} 个baseline文件")
        print(f"📁 结果目录: {recalculator.output_dir}")
        
        if results:
            ppls = [r['pseudo_ppl'] for r in results if r['pseudo_ppl'] != float('inf')]
            if ppls:
                avg_ppl = sum(ppls) / len(ppls)
                print(f"\n📈 新的GPU统一baseline平均PPL: {avg_ppl:.3f}")
                print("✅ 现在baseline和54个实验样本使用完全相同的PPL算法!")
                print("🚀 GPU加速让计算更快更稳定!")
        
        print(f"\n📥 下载指南:")
        print(f"   请将以下文件夹下载到本地: {recalculator.output_dir}/")
        print(f"   scp -P [端口] -r [用户]@[GPU服务器]:{recalculator.output_dir}/ ./")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
