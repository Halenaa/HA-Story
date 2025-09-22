#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级内容多样性分析系统
按照学术标准实现B1、B2、B3三个步骤
"""

import os
import sys
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from collections import defaultdict
import argparse
from scipy.stats import spearmanr
import sacrebleu
from collections import OrderedDict

try:
    import blingfire
    BLINGFIRE_AVAILABLE = True
except (ImportError, OSError) as e:
    BLINGFIRE_AVAILABLE = False
    print(f"警告: blingfire不可用 ({e})，将使用简单分词")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

class AdvancedDiversityAnalyzer:
    """高级内容多样性分析器"""
    
    def __init__(self, 
                 data_dir: str = "data/output/regression_test",
                 output_dir: str = "diversity_results",
                 window: int = 1000,
                 stride: int = 500,
                 bleu_sample_every: int = 1,
                 tokenizer: str = "blingfire",
                 p_low: int = 5,
                 p_high: int = 95,
                 alpha_min: float = 0.4,
                 alpha_max: float = 0.8):
        
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.window = window
        self.stride = stride
        self.bleu_sample_every = bleu_sample_every
        self.tokenizer_type = tokenizer
        self.p_low = p_low
        self.p_high = p_high
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        
        self.results = OrderedDict()
        self.group_results = OrderedDict()
        
        # 文本缓存，避免B2重复读盘
        self._text_cache = {}
        
        # 初始化分词器
        self._init_tokenizer()
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
    def _init_tokenizer(self):
        """初始化分词器"""
        if self.tokenizer_type == "blingfire" and BLINGFIRE_AVAILABLE:
            self.tokenizer = "blingfire"
            print("使用blingfire分词器")
        elif self.tokenizer_type == "spacy" and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.tokenizer = "spacy"
                print("使用spaCy分词器")
            except OSError:
                self.tokenizer = "simple"
                print("spaCy模型未找到，使用简单分词器")
        else:
            self.tokenizer = "simple"
            print("使用简单分词器")
    
    def tokenize_text(self, text: str) -> List[str]:
        """分词"""
        if self.tokenizer == "blingfire":
            # 修复：添加小写化确保一致性
            return blingfire.text_to_words(text).lower().split()
        elif self.tokenizer == "spacy":
            doc = self.nlp(text)
            return [token.text.lower() for token in doc if not token.is_space and not token.is_punct]
        else:
            # 简单分词
            text = re.sub(r'[^\w\s]', ' ', text.lower())
            tokens = text.split()
            return [token for token in tokens if len(token) > 1]
    
    def extract_parameters_from_folder(self, folder_name: str) -> Dict[str, Union[str, float, int]]:
        """从文件夹名提取参数 - 更稳健的解析"""
        try:
            # 使用正则表达式提取温度和seed
            temp_match = re.search(r'T([\d.]+)', folder_name)
            seed_match = re.search(r's(\d+)', folder_name)
            
            if not temp_match or not seed_match:
                return {}
            
            # 修复：固定温度浮点精度，避免分组错误
            temperature = round(float(temp_match.group(1)), 3)
            seed = int(seed_match.group(1))
            
            # 处理genre映射 - 包含式匹配
            if "sciencefiction" in folder_name.lower():
                genre = "sciencefiction"
            elif "horror" in folder_name.lower():
                genre = "horror"
            elif "romantic" in folder_name.lower():
                genre = "romantic"
            elif "baseline" in folder_name.lower():
                genre = "baseline"
            else:
                # 尝试从parts中提取
                parts = folder_name.split('_')
                if len(parts) >= 2:
                    genre = parts[1]
                else:
                    return {}
            
            # 提取structure - 注意nonlinear包含linear，要先检查nonlinear
            if "nonlinear" in folder_name:
                structure = "nonlinear"
            elif "linear" in folder_name:
                structure = "linear"
            else:
                return {}
            
            return {
                'genre': genre,
                'structure': structure, 
                'temperature': temperature,
                'seed': seed,
                'folder_name': folder_name
            }
        except Exception as e:
            print(f"解析文件夹名出错 {folder_name}: {e}")
            return {}
    
    def calculate_distinct_with_window(self, tokens: List[str]) -> Tuple[float, float]:
        """B1: 使用滑动窗口计算distinct-1和distinct-2"""
        if len(tokens) < self.window:
            # 文本太短，直接计算
            return self._calculate_distinct_single_window(tokens)
        
        d1_windows = []
        d2_windows = []
        
        # 滑动窗口 - 改进：覆盖尾部
        last_start = max(0, len(tokens) - self.window)
        starts = list(range(0, len(tokens) - self.window + 1, self.stride))
        if not starts or starts[-1] != last_start:
            starts.append(last_start)
        
        for i in starts:
            window_tokens = tokens[i:i + self.window]
            d1_win, d2_win = self._calculate_distinct_single_window(window_tokens)
            d1_windows.append(d1_win)
            d2_windows.append(d2_win)
        
        # 取窗口平均
        d1 = np.mean(d1_windows)
        d2 = np.mean(d2_windows)
        
        return d1, d2
    
    def _calculate_distinct_single_window(self, tokens: List[str]) -> Tuple[float, float]:
        """计算单个窗口的distinct分数"""
        if len(tokens) < 2:
            return 0.0, 0.0
        
        # distinct-1
        unigrams = tokens
        unique_unigrams = len(set(unigrams))
        d1 = unique_unigrams / (len(unigrams) + 1)  # +1 长度平滑
        
        # distinct-2
        bigrams = [tuple(tokens[i:i+2]) for i in range(len(tokens)-1)]
        unique_bigrams = len(set(bigrams))
        d2 = unique_bigrams / (max(len(tokens)-1, 1) + 1)  # +1 长度平滑
        
        return d1, d2
    
    def analyze_single_story(self, story_path: Path) -> Dict[str, Union[str, float, int]]:
        """分析单篇故事"""
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清理文本
            content = re.sub(r'#+\s*.*?\n', '', content)  # 移除标题
            content = re.sub(r'[*_`]', '', content)  # 移除markdown格式
            content = re.sub(r'\n+', ' ', content)  # 合并换行
            
            # 分词
            tokens = self.tokenize_text(content)
            
            if len(tokens) < 10:
                return {
                    'distinct_1': 0.0,
                    'distinct_2': 0.0,
                    'distinct_avg': 0.0,
                    'distinct_score': 0.0,
                    'total_words': len(tokens),
                    'total_sentences': 0
                }
            
            # 计算distinct分数
            d1, d2 = self.calculate_distinct_with_window(tokens)
            distinct_avg = 0.5 * d1 + 0.5 * d2
            
            # 计算句子数（简单估算）
            sentences = len(re.split(r'[.!?]+', content))
            
            # 缓存文本内容，避免B2重复读盘
            self._text_cache[str(story_path)] = content
            
            return {
                'distinct_1': d1,
                'distinct_2': d2,
                'distinct_avg': distinct_avg,
                'distinct_score': 0.0,  # 将在归一化后计算
                'total_words': len(tokens),
                'total_sentences': sentences
            }
            
        except Exception as e:
            print(f"分析故事时出错 {story_path}: {e}")
            return {
                'distinct_1': 0.0,
                'distinct_2': 0.0,
                'distinct_avg': 0.0,
                'distinct_score': 0.0,
                'total_words': 0,
                'total_sentences': 0
            }
    
    def normalize_distinct_scores(self, results: Dict[str, Dict]) -> Dict[str, Dict]:
        """B1: 对distinct_avg进行P5-P95归一化"""
        distinct_avg_values = [r['distinct_avg'] for r in results.values()]
        
        if len(distinct_avg_values) < 2:
            for key in results:
                results[key]['distinct_score'] = results[key]['distinct_avg']
            return results
        
        p5 = np.percentile(distinct_avg_values, self.p_low)
        p95 = np.percentile(distinct_avg_values, self.p_high)
        
        if p95 == p5:
            for key in results:
                results[key]['distinct_score'] = 0.5
        else:
            for key in results:
                normalized = (results[key]['distinct_avg'] - p5) / (p95 - p5)
                results[key]['distinct_score'] = max(0.0, min(1.0, normalized))
        
        return results
    
    def _sentences(self, text: str) -> List[str]:
        """切分句子"""
        if self.tokenizer == "blingfire":
            try:
                sentences = blingfire.text_to_sentences(text).split('\n')
            except:
                sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        else:
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]
    
    def calculate_self_bleu_group(self, texts: List[str]) -> Tuple[float, List[float]]:
        """B2: 计算组内Self-BLEU分数，返回(均值, 每个seed的分数列表)"""
        if len(texts) != 3:
            return 0.0, [0.0, 0.0, 0.0]
        
        bleu_scores = []
        
        for i in range(3):
            # 按句子采样而不是token采样
            candidate_sentences = self._sentences(texts[i])
            reference_sentences_list = [self._sentences(texts[j]) for j in range(3) if j != i]
            
            # 句子采样（如果启用）
            if self.bleu_sample_every > 1:
                candidate_sentences = candidate_sentences[::self.bleu_sample_every]
                reference_sentences_list = [ref[::self.bleu_sample_every] for ref in reference_sentences_list]
            
            # 使用sacrebleu计算BLEU
            try:
                # 转换为sacrebleu格式
                candidate_text = ' '.join(candidate_sentences)
                reference_texts = [' '.join(ref) for ref in reference_sentences_list]
                
                # 修复：正确的sacrebleu格式和参数
                sys = [candidate_text]
                refs = [[reference_texts[0]], [reference_texts[1]]]
                
                # 修复：sacreBLEU版本兼容性
                try:
                    # 新版本优先：lowercase + use_effective_order
                    bleu_obj = sacrebleu.corpus_bleu(
                        sys, refs,
                        tokenize='13a',
                        smooth_method='exp',
                        lowercase=True,
                        use_effective_order=True
                    )
                except TypeError:
                    # 回退：lc + effective_order（旧参数名）
                    bleu_obj = sacrebleu.corpus_bleu(
                        sys, refs,
                        tokenize='13a',
                        smooth_method='exp',
                        lc=True,
                        effective_order=True
                    )
                
                bleu_score = bleu_obj.score / 100.0  # 转换为0-1范围
                bleu_scores.append(bleu_score)
            except Exception as e:
                print(f"BLEU计算出错: {e}")
                bleu_scores.append(0.0)
        
        return np.mean(bleu_scores), bleu_scores
    
    def analyze_group_diversity(self, group_stories: List[Dict]) -> Dict[str, Union[str, float, List[float]]]:
        """B2: 分析组内多样性"""
        if len(group_stories) != 3:
            return {
                'self_bleu_group': 0.0,
                'self_bleu_group_norm': 0.0,
                'one_minus_self_bleu': 0.0,
                'distinct_group': 0.0,
                'seed_self_bleus': [0.0, 0.0, 0.0],
                'seed_distinct_scores': [0.0, 0.0, 0.0],
                'alpha': 0.7,
                'diversity_score': 0.0
            }
        
        # 提取文本内容
        texts = []
        distinct_scores = []
        
        for story in group_stories:
            story_path = self.data_dir / story['folder_name'] / 'enhanced_story_dialogue_updated.md'
            try:
                # 优先从缓存获取，避免重复读盘
                if str(story_path) in self._text_cache:
                    content = self._text_cache[str(story_path)]
                else:
                    with open(story_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._text_cache[str(story_path)] = content
                # 清理文本
                content = re.sub(r'#+\s*.*?\n', '', content)
                content = re.sub(r'[*_`]', '', content)
                content = re.sub(r'\n+', ' ', content)
                texts.append(content)
                distinct_scores.append(story['distinct_score'])
            except Exception as e:
                print(f"读取故事文件出错: {e}")
                return {
                    'self_bleu_group': 0.0,
                    'self_bleu_group_norm': 0.0,
                    'one_minus_self_bleu': 0.0,
                    'distinct_group': 0.0,
                    'seed_self_bleus': [0.0, 0.0, 0.0],
                    'seed_distinct_scores': [0.0, 0.0, 0.0],
                    'alpha': 0.7,
                    'diversity_score': 0.0
                }
        
        # 计算Self-BLEU（返回均值和per-seed列表）
        self_bleu_group, per_seed_bleus = self.calculate_self_bleu_group(texts)
        
        # 计算组内distinct平均
        distinct_group = float(np.mean(distinct_scores))
        
        return {
            'self_bleu_group': self_bleu_group,
            'self_bleu_group_norm': 0.0,  # 将在归一化后计算
            'one_minus_self_bleu': 0.0,  # 将在归一化后计算
            'distinct_group': distinct_group,
            'seed_self_bleus': per_seed_bleus,      # 新增：用于稳定度计算
            'seed_distinct_scores': distinct_scores, # 新增：用于稳定度计算
            'alpha': 0.7,  # 将在B3中计算
            'diversity_score': 0.0  # 将在最终计算中得出
        }
    
    def _cv(self, x: List[float]) -> float:
        """计算变异系数"""
        x = np.asarray(x, dtype=float)
        m = np.mean(x)
        s = np.std(x, ddof=1) if len(x) > 1 else 0.0
        return 0.0 if m == 0 else float(s / (abs(m) + 1e-8))
    
    def learn_alpha_weights(self, group_results: Dict[str, Dict]) -> Tuple[Dict[str, Dict], Dict[str, float]]:
        """B3: 自动学习α权重参数"""
        diagnostics = {}
        if len(group_results) < 3:
            return group_results, diagnostics
        
        # 提取数据
        temperatures = []
        one_minus_self_bleu_values = []
        distinct_group_values = []
        
        for key, result in group_results.items():
            if 'temperature' in result:
                temperatures.append(result['temperature'])
                one_minus_self_bleu_values.append(result['one_minus_self_bleu'])
                distinct_group_values.append(result['distinct_group'])
        
        if len(temperatures) < 3:
            return group_results, diagnostics
        
        # 1) 区分度计算 - 按(genre, structure)子集计算
        genre_structure_groups = defaultdict(list)
        for key, result in group_results.items():
            group_key = (result['genre'], result['structure'])
            genre_structure_groups[group_key].append({
                'temperature': result['temperature'],
                'one_minus_self_bleu': result['one_minus_self_bleu'],
                'distinct_group': result['distinct_group']
            })
        
        rho1_values = []
        rho2_values = []
        
        for group_data in genre_structure_groups.values():
            if len(group_data) >= 3:  # 需要至少3个温度点
                temps = [d['temperature'] for d in group_data]
                om_sb_values = [d['one_minus_self_bleu'] for d in group_data]
                dg_values = [d['distinct_group'] for d in group_data]
                
                try:
                    rho1 = abs(spearmanr(om_sb_values, temps)[0])
                    rho2 = abs(spearmanr(dg_values, temps)[0])
                    rho1_values.append(rho1)
                    rho2_values.append(rho2)
                except:
                    pass
        
        rho1 = np.mean(rho1_values) if rho1_values else 0.5
        rho2 = np.mean(rho2_values) if rho2_values else 0.5
        
        # 2) 修复：稳定度计算 - 正确使用跨seed的变异系数
        cv1s, cv2s = [], []
        for result in group_results.values():
            # 使用每个组内3个seed的per-seed数据计算CV
            if 'seed_self_bleus' in result and len(result['seed_self_bleus']) == 3:
                cv1s.append(self._cv(result['seed_self_bleus']))
            if 'seed_distinct_scores' in result and len(result['seed_distinct_scores']) == 3:
                cv2s.append(self._cv(result['seed_distinct_scores']))
        
        stab1 = float(np.clip(1 - np.mean(cv1s), 0.0, 1.0)) if cv1s else 0.5
        stab2 = float(np.clip(1 - np.mean(cv2s), 0.0, 1.0)) if cv2s else 0.5
        
        # 3) 信噪综合
        R1 = rho1 * stab1
        R2 = rho2 * stab2
        
        # 4) 权重计算
        if R1 + R2 > 0:
            alpha = R1 / (R1 + R2)
            alpha = max(self.alpha_min, min(self.alpha_max, alpha))
        else:
            alpha = 0.7
        
        # 保存诊断量
        diagnostics = {
            'rho1': float(rho1),
            'rho2': float(rho2),
            'stab1': float(stab1),
            'stab2': float(stab2),
            'R1': float(R1),
            'R2': float(R2),
            'alpha': float(alpha)
        }
        
        # 添加全局相关性（便于论文报告）
        try:
            from scipy.stats import spearmanr
            global_rho_omSB = abs(spearmanr(one_minus_self_bleu_values, temperatures)[0])
            global_rho_distinct = abs(spearmanr(distinct_group_values, temperatures)[0])
            diagnostics['global_rho_omSB_vs_temp'] = float(global_rho_omSB)
            diagnostics['global_rho_distinct_vs_temp'] = float(global_rho_distinct)
        except Exception as e:
            print(f"计算全局相关性时出错: {e}")
            diagnostics['global_rho_omSB_vs_temp'] = 0.0
            diagnostics['global_rho_distinct_vs_temp'] = 0.0
        
        # 更新所有组的结果
        for key in group_results:
            group_results[key]['alpha'] = alpha
            diversity_score = (
                alpha * group_results[key]['one_minus_self_bleu'] + 
                (1 - alpha) * group_results[key]['distinct_group']
            )
            group_results[key]['diversity_score'] = diversity_score
        
        return group_results, diagnostics
    
    def run_analysis(self) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """运行完整的多样性分析"""
        print("开始高级内容多样性分析...")
        
        # B1: 逐篇分析
        print("B1: 进行逐篇多样性分析...")
        individual_results = OrderedDict()
        
        for folder in self.data_dir.iterdir():
            if folder.is_dir():
                params = self.extract_parameters_from_folder(folder.name)
                if not params:
                    continue
                
                story_path = folder / 'enhanced_story_dialogue_updated.md'
                if story_path.exists():
                    print(f"分析: {folder.name}")
                    result = self.analyze_single_story(story_path)
                    result.update(params)
                    individual_results[folder.name] = result
        
        # 归一化distinct分数
        individual_results = self.normalize_distinct_scores(individual_results)
        
        # B2: 组内分析
        print("B2: 进行组内Self-BLEU分析...")
        
        # 按条件分组
        groups = defaultdict(list)
        for key, result in individual_results.items():
            group_key = (result['genre'], result['structure'], result['temperature'])
            groups[group_key].append(result)
        
        group_results = OrderedDict()
        for group_key, stories in groups.items():
            # 对于baseline，允许单个story；对于其他，需要3个seed
            if len(stories) == 3 or (len(stories) == 1 and group_key[0] == 'baseline'):
                print(f"分析组: {group_key} ({len(stories)} 个样本)")
                group_result = self.analyze_group_diversity(stories)
                group_result['genre'] = group_key[0]
                group_result['structure'] = group_key[1]
                group_result['temperature'] = group_key[2]
                group_results[group_key] = group_result
        
        # 归一化组内结果
        if group_results:
            # 归一化self_bleu_group
            self_bleu_values = [r['self_bleu_group'] for r in group_results.values()]
            
            if len(self_bleu_values) > 1:
                p5_sb = np.percentile(self_bleu_values, self.p_low)
                p95_sb = np.percentile(self_bleu_values, self.p_high)
                
                for key, result in group_results.items():
                    if p95_sb != p5_sb:
                        sb_norm = (result['self_bleu_group'] - p5_sb) / (p95_sb - p5_sb)
                        sb_norm = max(0.0, min(1.0, sb_norm))
                    else:
                        sb_norm = 0.5
                    
                    result['self_bleu_group_norm'] = sb_norm
                    result['one_minus_self_bleu'] = 1 - sb_norm
        
        # B3: 学习α权重
        print("B3: 学习α权重参数...")
        alpha_diagnostics = {}
        if group_results:
            group_results, alpha_diagnostics = self.learn_alpha_weights(group_results)
        
        self.results = individual_results
        self.group_results = group_results
        self.alpha_diagnostics = alpha_diagnostics
        
        print("分析完成!")
        return individual_results, group_results
    
    def save_results(self, output_dir: Optional[str] = None):
        """保存分析结果"""
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
        else:
            output_path = self.output_dir
        
        # 保存逐篇结果
        individual_data = []
        for key, result in self.results.items():
            row = {
                'folder_name': key,  # 便于回溯原始样本目录
                'genre': result['genre'],
                'structure': result['structure'],
                'temperature': result['temperature'],
                'seed': result['seed'],
                'total_words': result['total_words'],
                'total_sentences': result['total_sentences'],
                'distinct_1': result['distinct_1'],
                'distinct_2': result['distinct_2'],
                'distinct_avg': result['distinct_avg'],
                'distinct_score': result['distinct_score']
            }
            individual_data.append(row)
        
        individual_df = pd.DataFrame(individual_data)
        # 排序让结果更易读
        individual_df = individual_df.sort_values(by=['genre', 'structure', 'temperature', 'seed']).reset_index(drop=True)
        individual_df.to_csv(output_path / 'individual_diversity_analysis.csv', index=False)
        
        # 保存组内结果
        group_data = []
        for key, result in self.group_results.items():
            # 找到该组的三个样本
            group_stories = []
            for story_key, story_result in self.results.items():
                if (story_result['genre'] == result['genre'] and 
                    story_result['structure'] == result['structure'] and 
                    story_result['temperature'] == result['temperature']):
                    group_stories.append(story_key)
            
            stories_in_group = '; '.join(sorted(group_stories))  # 分号分隔，便于追溯
            
            row = {
                'group_id': f"{result['genre']}_{result['structure']}_T{result['temperature']}",  # 组标识
                'stories_in_group': stories_in_group,  # 三个子样本的folder名
                'genre': result['genre'],
                'structure': result['structure'],
                'temperature': result['temperature'],
                'self_bleu_group': result['self_bleu_group'],
                'self_bleu_group_norm': result['self_bleu_group_norm'],
                'one_minus_self_bleu': result['one_minus_self_bleu'],
                'distinct_group': result['distinct_group'],
                'alpha': result['alpha'],
                'diversity_score': result['diversity_score'],
                'bleu_type': 'sacreBLEU-4',
                'window': self.window,
                'stride': self.stride,
                'bleu_sample_every': self.bleu_sample_every
            }
            group_data.append(row)
        
        group_df = pd.DataFrame(group_data)
        # 排序让结果更易读
        group_df = group_df.sort_values(by=['genre', 'structure', 'temperature']).reset_index(drop=True)
        group_df.to_csv(output_path / 'group_diversity_analysis.csv', index=False)
        
        # 保存JSON格式
        with open(output_path / 'individual_diversity_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(dict(self.results), f, ensure_ascii=False, indent=2)
        
        # 修复：将tuple键转换为列表格式保存JSON
        group_list = []
        for (g, s, t), r in self.group_results.items():
            row = dict(r)
            row.update({'genre': g, 'structure': s, 'temperature': t})
            group_list.append(row)
        
        with open(output_path / 'group_diversity_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(group_list, f, ensure_ascii=False, indent=2)
        
        # 记录关键包版本，提升论文复现性
        versions = {}
        try:
            import sacrebleu as _sb
            versions['sacrebleu'] = getattr(_sb, '__version__', 'unknown')
        except ImportError:
            versions['sacrebleu'] = 'not_installed'
        try:
            import blingfire as _bf
            versions['blingfire'] = getattr(_bf, '__version__', 'unknown')
        except (ImportError, OSError):
            versions['blingfire'] = 'not_available'
        try:
            import spacy as _sp
            versions['spacy'] = getattr(_sp, '__version__', 'unknown')
        except ImportError:
            versions['spacy'] = 'not_installed'
        
        # 保存元数据
        meta = {
            'parameters': {
                'window': self.window,
                'stride': self.stride,
                'bleu_type': 'sacreBLEU-4 (13a, exp smoothing, lowercase, effective_order)',
                'bleu_sample_every': self.bleu_sample_every,
                'tokenizer': self.tokenizer,
                'p_low': self.p_low,
                'p_high': self.p_high,
                'alpha_min': self.alpha_min,
                'alpha_max': self.alpha_max
            },
            'summary': {
                'individual_count': len(self.results),
                'group_count': len(self.group_results),
                'genres': list(set(r['genre'] for r in self.results.values())),
                'structures': list(set(r['structure'] for r in self.results.values())),
                'temperatures': list(set(r['temperature'] for r in self.results.values()))
            },
            'env': {
                'python': sys.version,
                'packages': versions
            }
        }
        
        # 添加α权重学习的诊断量
        if hasattr(self, 'alpha_diagnostics') and self.alpha_diagnostics:
            meta['learn_alpha'] = self.alpha_diagnostics
        
        with open(output_path / 'meta.json', 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='高级内容多样性分析')
    parser.add_argument('--data_dir', default='data/output/regression_test',
                       help='数据目录路径')
    parser.add_argument('--output_dir', default='diversity_results',
                       help='输出目录路径')
    parser.add_argument('--window', type=int, default=1000,
                       help='滑动窗口大小')
    parser.add_argument('--stride', type=int, default=500,
                       help='滑动窗口步长')
    parser.add_argument('--bleu_sample_every', type=int, default=1,
                       help='句子采样步长')
    parser.add_argument('--tokenizer', default='blingfire',
                       choices=['blingfire', 'spacy', 'simple'],
                       help='分词器类型')
    parser.add_argument('--p_low', type=int, default=5,
                       help='归一化低百分位')
    parser.add_argument('--p_high', type=int, default=95,
                       help='归一化高百分位')
    parser.add_argument('--alpha_min', type=float, default=0.4,
                       help='α权重最小值')
    parser.add_argument('--alpha_max', type=float, default=0.8,
                       help='α权重最大值')
    
    args = parser.parse_args()
    
    analyzer = AdvancedDiversityAnalyzer(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        window=args.window,
        stride=args.stride,
        bleu_sample_every=args.bleu_sample_every,
        tokenizer=args.tokenizer,
        p_low=args.p_low,
        p_high=args.p_high,
        alpha_min=args.alpha_min,
        alpha_max=args.alpha_max
    )
    
    individual_results, group_results = analyzer.run_analysis()
    analyzer.save_results()
    
    print(f"分析完成! 共分析了 {len(individual_results)} 篇故事，{len(group_results)} 个条件组")

if __name__ == "__main__":
    main()
