"""
Fluency Analyzer for Story Evaluation
计算文本流畅度指标：pseudo-PPL 和语法错误率
"""

import re
import numpy as np
import json
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM
import language_tool_python
import warnings
warnings.filterwarnings("ignore")

class FluencyAnalyzer:
    """
    流畅度分析器
    主要指标：pseudo-PPL (Masked LM)
    辅助指标：语法错误率 (LanguageTool)
    """
    
    def __init__(self, model_name="roberta-large", device=None):
        """
        初始化流畅度分析器
        
        Args:
            model_name: 预训练模型名称，推荐 'roberta-large' 或 'microsoft/deberta-v3-large'
            device: 计算设备，None为自动选择
        """
        print(f"初始化流畅度分析器，使用模型: {model_name}")
        
        self.model_name = model_name
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        
        # 初始化Masked LM模型
        self._init_masked_lm()
        
        # 初始化LanguageTool
        self._init_language_tool()
        
        print(f"流畅度分析器初始化完成，使用设备: {self.device}")
    
    def _init_masked_lm(self):
        """初始化Masked LM模型"""
        try:
            print("加载Masked LM模型...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # 设置特殊token
            self.mask_token = self.tokenizer.mask_token
            self.mask_token_id = self.tokenizer.mask_token_id
            
            print(f"Masked LM模型加载完成: {self.model_name}")
            
        except Exception as e:
            print(f"Masked LM模型加载失败: {e}")
            raise
    
    def _init_language_tool(self):
        """初始化LanguageTool"""
        try:
            print("初始化LanguageTool...")
            self.language_tool = language_tool_python.LanguageTool('en-US')
            
            # 注意：LanguageTool不支持运行时动态设置规则，
            # 实际的过滤在_filter_grammar_matches()中进行
            
            print("LanguageTool初始化完成")
            
        except Exception as e:
            print(f"LanguageTool初始化失败: {e}")
            print("将使用简化的语法检查方法")
            self.language_tool = None
    
    def _filter_grammar_rules(self):
        """
        过滤语法规则，减少创作体裁的误报
        注意：此函数已废弃，因为language_tool_python不支持运行时动态设置规则
        实际的过滤在_filter_grammar_matches()中进行
        """
        try:
            # 获取所有规则
            all_rules = self.language_tool.get_rules()
            
            # 要过滤的规则类别（风格类和非致命规则）
            filtered_categories = [
                'STYLE', 'TYPOGRAPHY', 'CASING', 'PUNCTUATION',
                'REDUNDANCY', 'WORD_CHOICE', 'CLARITY'
            ]
            
            # 要过滤的具体规则ID
            filtered_rule_ids = [
                'EN_QUOTES', 'EN_DASHES', 'EN_SENTENCE_END',
                'EN_UNPAIRED_BRACKETS', 'EN_APOSTROPHE'
            ]
            
            # 过滤规则
            filtered_rules = []
            for rule in all_rules:
                if (rule.category not in filtered_categories and 
                    rule.ruleId not in filtered_rule_ids):
                    filtered_rules.append(rule)
            
            # 重新设置规则
            self.language_tool = language_tool_python.LanguageTool('en-US')
            # 注意：language_tool_python可能不支持动态设置规则，这里先保持原样
            
        except Exception as e:
            print(f"规则过滤失败，使用默认规则: {e}")
    
    def _tokenize_text(self, text: str, max_length: int = 512) -> List[Dict]:
        """
        将文本分块tokenize，并标记有效计分区域
        
        Args:
            text: 输入文本
            max_length: 每块最大长度
            
        Returns:
            List of dicts with 'tokens' and 'valid_range' (start, end) for scoring
        """
        # 清理文本
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 分词
        tokens = self.tokenizer.encode(text, add_special_tokens=True)
        
        # 分块（滑窗方式）
        chunks = []
        stride = max_length // 2  # 步长为块大小的一半
        overlap = max_length - stride  # 重叠区域大小
        
        for i in range(0, len(tokens), stride):
            chunk_tokens = tokens[i:i + max_length]
            if len(chunk_tokens) == 0:
                continue
            
            # 计算有效计分区域（避免重叠区域的双计数）
            if i == 0:
                # 第一个chunk：从开始到 stride 位置
                valid_start = 0
                valid_end = min(stride, len(chunk_tokens))
            elif i + max_length >= len(tokens):
                # 最后一个chunk：从 overlap 位置到结束
                valid_start = overlap // 2
                valid_end = len(chunk_tokens)
            else:
                # 中间chunk：只计算中间区域
                valid_start = overlap // 2
                valid_end = stride + overlap // 2
            
            chunks.append({
                'tokens': chunk_tokens,
                'valid_range': (valid_start, valid_end),
                'global_offset': i
            })
        
        return chunks
    
    def _calculate_pseudo_ppl_chunk(self, chunk_data: Dict, subsample_rate: int = 4, mini_batch_size: int = 128) -> Tuple[float, int]:
        """
        计算单个chunk的pseudo-PPL（返回累积NLL和有效mask数）
        
        Args:
            chunk_data: 包含tokens和valid_range的字典
            subsample_rate: 子采样率，每N个token才mask一次
            mini_batch_size: mini-batch大小，避免显存爆炸
            
        Returns:
            (累积负对数似然, 有效mask数)
        """
        chunk = chunk_data['tokens']
        valid_start, valid_end = chunk_data['valid_range']
        
        if len(chunk) < 2 or valid_start >= valid_end:
            return 0.0, 0
        
        # 获取特殊token IDs
        special_token_ids = set()
        if hasattr(self.tokenizer, 'cls_token_id') and self.tokenizer.cls_token_id is not None:
            special_token_ids.add(self.tokenizer.cls_token_id)
        if hasattr(self.tokenizer, 'sep_token_id') and self.tokenizer.sep_token_id is not None:
            special_token_ids.add(self.tokenizer.sep_token_id)
        if hasattr(self.tokenizer, 'pad_token_id') and self.tokenizer.pad_token_id is not None:
            special_token_ids.add(self.tokenizer.pad_token_id)
        if hasattr(self.tokenizer, 'eos_token_id') and self.tokenizer.eos_token_id is not None:
            special_token_ids.add(self.tokenizer.eos_token_id)
        if hasattr(self.tokenizer, 'bos_token_id') and self.tokenizer.bos_token_id is not None:
            special_token_ids.add(self.tokenizer.bos_token_id)
        
        # 子采样：只在有效区域内mask，跳过特殊token
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
        
        # 转换为tensor用于向量化操作
        chunk_tensor = torch.tensor(chunk, device=self.device)
        
        # 分批处理，避免显存爆炸
        for batch_start in range(0, len(mask_positions), mini_batch_size):
            batch_end = min(batch_start + mini_batch_size, len(mask_positions))
            batch_positions = mask_positions[batch_start:batch_end]
            
            if not batch_positions:
                continue
            
            # 向量化构造掩码样本
            pos_tensor = torch.tensor(batch_positions, device=self.device)
            batch_size = len(batch_positions)
            
            # 构造 (B, L) 的批次，每行都是原始chunk
            base_inputs = chunk_tensor.unsqueeze(0).repeat(batch_size, 1)  # (B, L)
            
            # 使用scatter_向量化地设置mask token
            masked_inputs = base_inputs.clone()
            masked_inputs.scatter_(1, pos_tensor.unsqueeze(1), self.mask_token_id)
            
            # 构造attention mask
            attention_mask = torch.ones_like(masked_inputs, device=self.device)
            
            # 前向传播（使用inference_mode优化）
            with torch.inference_mode():
                outputs = self.model(input_ids=masked_inputs, attention_mask=attention_mask)
                logits = outputs.logits  # (B, L, V)
            
            # 向量化计算log概率
            import torch.nn.functional as F
            log_probs = F.log_softmax(logits, dim=-1)  # (B, L, V)
            
            # 获取每个样本在其mask位置的真实token概率
            rows = torch.arange(batch_size, device=self.device)
            true_token_ids = base_inputs[rows, pos_tensor]  # (B,) 真实token IDs
            
            # 提取对应位置和token的log概率
            picked_log_probs = log_probs[rows, pos_tensor, true_token_ids]  # (B,)
            
            # 累积负对数似然
            total_neg_log_likelihood += (-picked_log_probs).sum().item()
            valid_masks += batch_size
        
        return total_neg_log_likelihood, valid_masks
    
    def _auto_subsample_rate(self, n_tokens: int, target_masks: int = 1000) -> int:
        """
        自适应子采样率，控制算力消耗
        
        Args:
            n_tokens: 总token数
            target_masks: 目标掩码位置数
            
        Returns:
            自适应的子采样率
        """
        return max(1, int(np.ceil(n_tokens / max(1, target_masks))))
    
    def calculate_pseudo_ppl(self, text: str, subsample_rate: int = 4) -> float:
        """
        计算文本的pseudo-PPL（正确的聚合方式）
        
        Args:
            text: 输入文本
            subsample_rate: 子采样率（会被自适应调整）
            
        Returns:
            pseudo-PPL值
        """
        if not text or not text.strip():
            return float('inf')
        
        # 分块处理
        chunks = self._tokenize_text(text)
        
        if not chunks:
            return float('inf')
        
        # 自适应子采样率，控制算力消耗
        all_tokens = sum(len(c['tokens']) for c in chunks)
        adaptive_subsample_rate = self._auto_subsample_rate(all_tokens)
        
        print(f"[PPL] 处理 {all_tokens} tokens，分为 {len(chunks)} 个chunks，子采样率: {adaptive_subsample_rate}")
        
        # 累积所有chunks的NLL和有效mask数
        total_neg_log_likelihood = 0.0
        total_valid_masks = 0
        invalid_segments = 0
        
        for i, chunk_data in enumerate(chunks):
            print(f"[PPL] 处理chunk {i+1}/{len(chunks)}...", end=' ')
            nll, valid_masks = self._calculate_pseudo_ppl_chunk(chunk_data, adaptive_subsample_rate)
            print(f"完成 (masks: {valid_masks})")
            
            if valid_masks == 0:
                invalid_segments += 1
                if chunk_data['valid_range'][1] - chunk_data['valid_range'][0] > 2:
                    print(f"Warning: 无效片段被跳过，有效范围: {chunk_data['valid_range']}")
            total_neg_log_likelihood += nll
            total_valid_masks += valid_masks
        
        if total_valid_masks == 0:
            return float('inf')
        
        # 掩码位置覆盖率自检
        approx_total_positions = all_tokens - 2 * len(chunks)  # 粗估可计位置数
        coverage = total_valid_masks / max(1, approx_total_positions)
        print(f"[PPL] mask coverage ~ {coverage:.2%} (masks={total_valid_masks}, tokens={all_tokens})")
        
        if invalid_segments > 0:
            print(f"[PPL] 跳过了 {invalid_segments} 个无效片段")
        
        # 计算平均NLL，然后取指数得到pseudo-PPL
        avg_neg_log_likelihood = total_neg_log_likelihood / total_valid_masks
        pseudo_ppl = np.exp(avg_neg_log_likelihood)
        
        return pseudo_ppl
    
    def calculate_grammar_errors(self, text: str) -> Tuple[int, int, float]:
        """
        计算语法错误率
        
        Args:
            text: 输入文本
            
        Returns:
            (错误数, 总词数, 每百词错误数)
        """
        if not text or not text.strip():
            return 0, 0, 0.0
        
        # 统计词数（支持英文缩写，如don't, it's等）
        words = re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", text.lower())
        word_count = len(words)
        
        if word_count == 0:
            return 0, 0, 0.0
        
        if self.language_tool is None:
            # 使用简化的语法检查
            return self._simple_grammar_check(text, word_count)
        
        try:
            # 检测语法错误
            matches = self.language_tool.check(text)
            
            # 过滤掉风格类和非致命规则
            filtered_matches = self._filter_grammar_matches(matches)
            error_count = len(filtered_matches)
            
            # 计算每百词错误数
            errors_per_100_words = (error_count / word_count) * 100
            
            return error_count, word_count, errors_per_100_words
            
        except Exception as e:
            print(f"语法检查失败: {e}")
            return self._simple_grammar_check(text, word_count)
    
    def _filter_grammar_matches(self, matches):
        """
        过滤语法错误匹配结果，去除风格类和非致命错误
        
        Args:
            matches: LanguageTool检测到的错误列表
            
        Returns:
            过滤后的错误列表
        """
        filtered_matches = []
        
        # 要过滤的规则类别
        filtered_categories = {
            'STYLE', 'TYPOGRAPHY', 'CASING', 'PUNCTUATION',
            'REDUNDANCY', 'WORD_CHOICE', 'CLARITY', 'COLLOQUIALISMS'
        }
        
        # 要过滤的具体规则ID
        filtered_rule_ids = {
            'EN_QUOTES', 'EN_DASHES', 'EN_SENTENCE_END',
            'EN_UNPAIRED_BRACKETS', 'EN_APOSTROPHE', 'WHITESPACE_RULE',
            'COMMA_PARENTHESIS_WHITESPACE', 'SENTENCE_WHITESPACE',
            'UPPERCASE_SENTENCE_START', 'ENGLISH_WORD_REPEAT_BEGINNING_RULE'
        }
        
        # 要过滤的错误类型
        filtered_issue_types = {
            'style', 'typographical', 'whitespace', 'capitalization'
        }
        
        for match in matches:
            # 检查类别（正确获取category属性，统一大写比较）
            category_id = getattr(getattr(match, 'category', None), 'id', '') or getattr(getattr(match, 'category', None), 'name', '')
            if category_id.upper() in filtered_categories:
                continue
            
            # 检查规则ID（统一大写比较）
            rule_id = getattr(match, 'ruleId', '') or getattr(match, 'rule_id', '')
            if rule_id.upper() in filtered_rule_ids:
                continue
            
            # 检查错误类型（统一小写比较）
            issue_type = getattr(match, 'ruleIssueType', '') or getattr(match, 'issue_type', '')
            if issue_type.lower() in filtered_issue_types:
                continue
            
            # 通过所有过滤条件，保留此错误
            filtered_matches.append(match)
        
        return filtered_matches
    
    def _simple_grammar_check(self, text: str, word_count: int) -> Tuple[int, int, float]:
        """
        简化的语法检查（当LanguageTool不可用时）
        
        Args:
            text: 输入文本
            word_count: 词数
            
        Returns:
            (错误数, 总词数, 每百词错误数)
        """
        error_count = 0
        
        # 检查一些基本的语法问题
        # 1. 检查重复的空格
        if re.search(r'\s{3,}', text):  # 3个或更多空格才算错误
            error_count += len(re.findall(r'\s{3,}', text))
        
        # 2. 检查常见拼写错误模式
        common_errors = [
            r'\bteh\b',      # the的常见错误
            r'\badn\b',      # and的常见错误
            r'\byuo\b',      # you的常见错误
            r'\brecieve\b',  # receive的常见错误
            r'\boccur\b',    # occur的常见错误
            r'\bseparate\b', # separate的常见错误（实际是正确的，这里只是示例）
        ]
        
        for pattern in common_errors:
            matches = re.findall(pattern, text, re.IGNORECASE)
            error_count += len(matches)
        
        # 3. 检查明显的语法错误模式
        grammar_patterns = [
            r'\ba\s+[aeiouAEIOU]',  # "a apple" 应该是 "an apple"
            r'\ban\s+[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]',  # "an book" 应该是 "a book"
        ]
        
        for pattern in grammar_patterns:
            matches = re.findall(pattern, text)
            error_count += len(matches)
        
        # 计算每百词错误数
        errors_per_100_words = (error_count / word_count) * 100
        
        return error_count, word_count, errors_per_100_words
    
    def analyze_fluency(self, text: str, subsample_rate: int = 4) -> Dict:
        """
        分析文本流畅度
        
        Args:
            text: 输入文本
            subsample_rate: pseudo-PPL计算的子采样率
            
        Returns:
            流畅度分析结果
        """
        print("开始流畅度分析...")
        
        # 计算pseudo-PPL
        print("计算pseudo-PPL...")
        pseudo_ppl = self.calculate_pseudo_ppl(text, subsample_rate)
        
        # 计算语法错误率
        print("计算语法错误率...")
        error_count, word_count, err_per_100w = self.calculate_grammar_errors(text)
        
        result = {
            'pseudo_ppl': pseudo_ppl,
            'err_per_100w': err_per_100w,
            'error_count': error_count,
            'word_count': word_count,
            'analysis_timestamp': datetime.now().isoformat(),
            'model_name': self.model_name,
            'subsample_rate': subsample_rate
        }
        
        print(f"流畅度分析完成 - Pseudo-PPL: {pseudo_ppl:.2f}, 语法错误率: {err_per_100w:.2f}")
        
        return result
    
    def normalize_scores(self, results: List[Dict]) -> List[Dict]:
        """
        归一化分数
        
        Args:
            results: 分析结果列表
            
        Returns:
            添加归一化分数的结果列表
        """
        if not results:
            return results
        
        # 提取pseudo_ppl和err_per_100w
        pseudo_ppls = [r['pseudo_ppl'] for r in results if r['pseudo_ppl'] != float('inf')]
        err_rates = [r['err_per_100w'] for r in results]
        
        if not pseudo_ppls:
            print("警告：没有有效的pseudo-PPL值进行归一化")
            return results
        
        # 计算分位数
        p5_ppl, p95_ppl = np.percentile(pseudo_ppls, [5, 95])
        p5_err, p95_err = np.percentile(err_rates, [5, 95])
        
        # 除零保护
        eps = 1e-6
        ppl_range = max(p95_ppl - p5_ppl, eps)
        err_range = max(p95_err - p5_err, eps)
        
        print(f"Pseudo-PPL分位数: P5={p5_ppl:.2f}, P95={p95_ppl:.2f}")
        print(f"语法错误率分位数: P5={p5_err:.2f}, P95={p95_err:.2f}")
        
        # 归一化并计算最终分数
        for result in results:
            # pseudo-PPL分数（越低越好）
            if result['pseudo_ppl'] != float('inf'):
                ppl_score = np.clip((p95_ppl - result['pseudo_ppl']) / ppl_range, 0, 1)
            else:
                ppl_score = 0.0
            
            # 语法分数（越低越好）
            grammar_score = np.clip((p95_err - result['err_per_100w']) / err_range, 0, 1)
            
            # 分数裁剪，处理极端outlier
            ppl_score = float(np.clip(ppl_score, 0, 1))
            grammar_score = float(np.clip(grammar_score, 0, 1))
            
            # 综合流畅度分数（加权平均：0.8 pseudo-PPL + 0.2 语法）
            fluency_score = 0.8 * ppl_score + 0.2 * grammar_score
            
            result.update({
                'pseudo_ppl_score': ppl_score,
                'grammar_score': grammar_score,
                'fluency_score': fluency_score
            })
        
        return results

def main():
    """测试函数"""
    # 测试文本
    test_text = """
    Once upon a time, there was a little girl who lived in a village near the forest. 
    She always wore a red riding hood, so everyone called her Little Red Riding Hood. 
    One day, her mother asked her to take some food to her grandmother who was sick. 
    The grandmother lived in a house on the other side of the forest.
    """
    
    # 初始化分析器
    analyzer = FluencyAnalyzer()
    
    # 分析流畅度
    result = analyzer.analyze_fluency(test_text)
    
    print("\n流畅度分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
