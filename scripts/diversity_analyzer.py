#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容多样性分析系统
实现B1: 逐篇多样性分析 (distinct_1, distinct_2, distinct_avg, distinct_score)
实现B2: 组内Self-BLEU分析和条件级聚合
实现B3: 自动学习α权重参数
"""

import os
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import argparse
from scipy.stats import spearmanr
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import nltk
from nltk.tokenize import word_tokenize
try:
    import spacy
except ImportError:
    spacy = None

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

class DiversityAnalyzer:
    """内容多样性分析器"""
    
    def __init__(self, data_dir: str = "/Users/haha/Story/data/output/regression_test"):
        self.data_dir = Path(data_dir)
        self.results = {}
        self.group_results = {}
        
        # 初始化spaCy模型
        if spacy:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("警告: 无法加载spaCy模型，将使用NLTK分词")
                self.nlp = None
        else:
            print("警告: spaCy未安装，将使用NLTK分词")
            self.nlp = None
            
        # BLEU平滑函数
        self.smoothing = SmoothingFunction().method1
        
    def extract_parameters_from_folder(self, folder_name: str) -> Dict[str, str]:
        """从文件夹名提取参数"""
        # 格式: thelittleredridinghood_sciencefictionrewrite_linear_T0.3_s1
        parts = folder_name.split('_')
        if len(parts) >= 4:
            genre = parts[1]  # sciencefictionrewrite
            structure = parts[2]  # linear/nonlinear
            temperature = parts[3].replace('T', '')  # 0.3
            seed = parts[4].replace('s', '')  # 1
            return {
                'genre': genre,
                'structure': structure, 
                'temperature': temperature,
                'seed': seed,
                'folder_name': folder_name
            }
        return {}
    
    def tokenize_text(self, text: str) -> List[str]:
        """使用spaCy或NLTK进行分词"""
        if self.nlp:
            doc = self.nlp(text)
            return [token.text.lower() for token in doc if not token.is_space and not token.is_punct]
        else:
            return word_tokenize(text.lower())
    
    def calculate_distinct_n(self, tokens: List[str], n: int, window_size: int = None, step_size: int = None) -> float:
        """计算distinct-n分数"""
        if len(tokens) < n:
            return 0.0
            
        if window_size and len(tokens) > window_size:
            # 使用滑动窗口
            distinct_scores = []
            for i in range(0, len(tokens) - window_size + 1, step_size or window_size // 2):
                window_tokens = tokens[i:i + window_size]
                window_ngrams = [tuple(window_tokens[j:j+n]) for j in range(len(window_tokens) - n + 1)]
                unique_ngrams = len(set(window_ngrams))
                total_ngrams = len(window_ngrams)
                distinct_scores.append(unique_ngrams / (total_ngrams + 1))
            return np.mean(distinct_scores)
        else:
            # 全文计算
            ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
            unique_ngrams = len(set(ngrams))
            total_ngrams = len(ngrams)
            return unique_ngrams / (total_ngrams + 1)
    
    def analyze_single_story(self, story_path: Path) -> Dict[str, float]:
        """分析单篇故事的多样性"""
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 清理文本，移除markdown标记
            content = re.sub(r'#+\s*.*?\n', '', content)  # 移除标题
            content = re.sub(r'[*_`]', '', content)  # 移除markdown格式
            content = re.sub(r'\n+', ' ', content)  # 合并换行
            
            # 分词
            tokens = self.tokenize_text(content)
            
            if len(tokens) < 10:  # 文本太短
                return {
                    'distinct_1': 0.0,
                    'distinct_2': 0.0,
                    'distinct_avg': 0.0,
                    'distinct_score': 0.0,
                    'word_count': len(tokens)
                }
            
            # 计算distinct-1和distinct-2
            distinct_1 = self.calculate_distinct_n(tokens, 1)
            distinct_2 = self.calculate_distinct_n(tokens, 2)
            
            # 计算平均distinct
            distinct_avg = 0.5 * distinct_1 + 0.5 * distinct_2
            
            return {
                'distinct_1': distinct_1,
                'distinct_2': distinct_2,
                'distinct_avg': distinct_avg,
                'distinct_score': 0.0,  # 将在归一化后计算
                'word_count': len(tokens)
            }
            
        except Exception as e:
            print(f"分析故事时出错 {story_path}: {e}")
            return {
                'distinct_1': 0.0,
                'distinct_2': 0.0,
                'distinct_avg': 0.0,
                'distinct_score': 0.0,
                'word_count': 0
            }
    
    def normalize_distinct_scores(self, results: Dict[str, Dict]) -> Dict[str, Dict]:
        """对distinct_avg进行p5-p95归一化到[0,1]"""
        distinct_avg_values = [r['distinct_avg'] for r in results.values()]
        
        if len(distinct_avg_values) < 2:
            # 数据太少，无法归一化
            for key in results:
                results[key]['distinct_score'] = results[key]['distinct_avg']
            return results
        
        p5 = np.percentile(distinct_avg_values, 5)
        p95 = np.percentile(distinct_avg_values, 95)
        
        if p95 == p5:  # 避免除零
            for key in results:
                results[key]['distinct_score'] = 0.5
        else:
            for key in results:
                normalized = (results[key]['distinct_avg'] - p5) / (p95 - p5)
                results[key]['distinct_score'] = max(0.0, min(1.0, normalized))
        
        return results
    
    def calculate_self_bleu(self, texts: List[str]) -> float:
        """计算3篇文本的Self-BLEU分数"""
        if len(texts) != 3:
            return 0.0
        
        bleu_scores = []
        
        for i in range(3):
            # 当前文本作为候选
            candidate = word_tokenize(texts[i].lower())
            
            # 其他两篇作为参考
            references = [word_tokenize(texts[j].lower()) for j in range(3) if j != i]
            
            # 计算BLEU-2分数
            bleu_score = sentence_bleu(references, candidate, 
                                    weights=(0.5, 0.5), 
                                    smoothing_function=self.smoothing)
            bleu_scores.append(bleu_score)
        
        return np.mean(bleu_scores)
    
    def analyze_group_diversity(self, group_stories: List[Dict]) -> Dict[str, float]:
        """分析组内多样性"""
        if len(group_stories) != 3:
            return {
                'self_bleu_group': 0.0,
                'distinct_group': 0.0,
                'one_minus_self_bleu': 0.0,
                'alpha': 0.7,
                'diversity_score': 0.0
            }
        
        # 提取文本内容
        texts = []
        distinct_scores = []
        
        for story in group_stories:
            story_path = self.data_dir / story['folder_name'] / 'enhanced_story_dialogue_updated.md'
            try:
                with open(story_path, 'r', encoding='utf-8') as f:
                    content = f.read()
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
                    'distinct_group': 0.0,
                    'one_minus_self_bleu': 0.0,
                    'alpha': 0.7,
                    'diversity_score': 0.0
                }
        
        # 计算Self-BLEU
        self_bleu_group = self.calculate_self_bleu(texts)
        
        # 计算组内distinct平均
        distinct_group = np.mean(distinct_scores)
        
        return {
            'self_bleu_group': self_bleu_group,
            'distinct_group': distinct_group,
            'one_minus_self_bleu': 0.0,  # 将在归一化后计算
            'alpha': 0.7,  # 将在B3中计算
            'diversity_score': 0.0  # 将在最终计算中得出
        }
    
    def learn_alpha_weights(self, group_results: Dict[str, Dict]) -> Dict[str, Dict]:
        """B3: 自动学习α权重参数"""
        if len(group_results) < 3:  # 需要足够的数据
            return group_results
        
        # 提取数据
        temperatures = []
        one_minus_self_bleu_values = []
        distinct_group_values = []
        
        for key, result in group_results.items():
            params = self.extract_parameters_from_folder(key.split('_group')[0])
            if params:
                temperatures.append(float(params['temperature']))
                one_minus_self_bleu_values.append(result['one_minus_self_bleu'])
                distinct_group_values.append(result['distinct_group'])
        
        if len(temperatures) < 3:
            return group_results
        
        # 计算区分度 (对温度敏感)
        rho1 = abs(spearmanr(one_minus_self_bleu_values, temperatures)[0])
        rho2 = abs(spearmanr(distinct_group_values, temperatures)[0])
        
        # 计算稳定度 (跨seed方差小)
        # 按genre×structure分组计算变异系数
        genre_structure_groups = defaultdict(list)
        for key, result in group_results.items():
            params = self.extract_parameters_from_folder(key.split('_group')[0])
            if params:
                group_key = f"{params['genre']}_{params['structure']}"
                genre_structure_groups[group_key].append({
                    'one_minus_self_bleu': result['one_minus_self_bleu'],
                    'distinct_group': result['distinct_group']
                })
        
        cv_one_minus_self_bleu = []
        cv_distinct = []
        
        for group_data in genre_structure_groups.values():
            if len(group_data) >= 2:  # 需要至少2个样本计算CV
                om_sb_values = [d['one_minus_self_bleu'] for d in group_data]
                dg_values = [d['distinct_group'] for d in group_data]
                
                if np.std(om_sb_values) > 0:
                    cv_one_minus_self_bleu.append(np.std(om_sb_values) / np.mean(om_sb_values))
                if np.std(dg_values) > 0:
                    cv_distinct.append(np.std(dg_values) / np.mean(dg_values))
        
        stab1 = 1 - np.mean(cv_one_minus_self_bleu) if cv_one_minus_self_bleu else 0.5
        stab2 = 1 - np.mean(cv_distinct) if cv_distinct else 0.5
        
        # 信噪综合
        R1 = rho1 * stab1
        R2 = rho2 * stab2
        
        # 计算权重
        if R1 + R2 > 0:
            alpha = R1 / (R1 + R2)
            alpha = max(0.4, min(0.8, alpha))  # 截断到[0.4, 0.8]
        else:
            alpha = 0.7
        
        # 更新所有组的结果
        for key in group_results:
            group_results[key]['alpha'] = alpha
            group_results[key]['diversity_score'] = (
                alpha * group_results[key]['one_minus_self_bleu'] + 
                (1 - alpha) * group_results[key]['distinct_group']
            )
        
        return group_results
    
    def run_analysis(self) -> Tuple[Dict, Dict]:
        """运行完整的多样性分析"""
        print("开始内容多样性分析...")
        
        # B1: 逐篇分析
        print("B1: 进行逐篇多样性分析...")
        individual_results = {}
        
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
        
        # 按条件分组 (genre × structure × temperature)
        groups = defaultdict(list)
        for key, result in individual_results.items():
            group_key = f"{result['genre']}_{result['structure']}_{result['temperature']}"
            groups[group_key].append(result)
        
        group_results = {}
        for group_key, stories in groups.items():
            if len(stories) == 3:  # 确保有3个seed
                print(f"分析组: {group_key}")
                group_result = self.analyze_group_diversity(stories)
                group_result['genre'] = stories[0]['genre']
                group_result['structure'] = stories[0]['structure']
                group_result['temperature'] = stories[0]['temperature']
                group_results[group_key] = group_result
        
        # 归一化组内结果
        if group_results:
            # 归一化self_bleu_group和distinct_group
            self_bleu_values = [r['self_bleu_group'] for r in group_results.values()]
            distinct_values = [r['distinct_group'] for r in group_results.values()]
            
            if len(self_bleu_values) > 1:
                p5_sb = np.percentile(self_bleu_values, 5)
                p95_sb = np.percentile(self_bleu_values, 95)
                p5_d = np.percentile(distinct_values, 5)
                p95_d = np.percentile(distinct_values, 95)
                
                for key, result in group_results.items():
                    # 归一化self_bleu_group
                    if p95_sb != p5_sb:
                        sb_norm = (result['self_bleu_group'] - p5_sb) / (p95_sb - p5_sb)
                        sb_norm = max(0.0, min(1.0, sb_norm))
                    else:
                        sb_norm = 0.5
                    
                    # 归一化distinct_group
                    if p95_d != p5_d:
                        d_norm = (result['distinct_group'] - p5_d) / (p95_d - p5_d)
                        d_norm = max(0.0, min(1.0, d_norm))
                    else:
                        d_norm = 0.5
                    
                    # Self-BLEU转正向
                    result['one_minus_self_bleu'] = 1 - sb_norm
                    result['distinct_group'] = d_norm
        
        # B3: 学习α权重
        print("B3: 学习α权重参数...")
        group_results = self.learn_alpha_weights(group_results)
        
        self.results = individual_results
        self.group_results = group_results
        
        print("分析完成!")
        return individual_results, group_results
    
    def save_results(self, output_dir: str = "/Users/haha/Story/diversity_results"):
        """保存分析结果"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存逐篇结果
        individual_df = pd.DataFrame.from_dict(self.results, orient='index')
        individual_df.to_csv(output_path / 'individual_diversity_analysis.csv')
        
        # 保存组内结果
        group_df = pd.DataFrame.from_dict(self.group_results, orient='index')
        group_df.to_csv(output_path / 'group_diversity_analysis.csv')
        
        # 保存JSON格式
        with open(output_path / 'individual_diversity_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        with open(output_path / 'group_diversity_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(self.group_results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='内容多样性分析')
    parser.add_argument('--data_dir', default='/Users/haha/Story/data/output/regression_test',
                       help='数据目录路径')
    parser.add_argument('--output_dir', default='/Users/haha/Story/diversity_results',
                       help='输出目录路径')
    
    args = parser.parse_args()
    
    analyzer = DiversityAnalyzer(args.data_dir)
    individual_results, group_results = analyzer.run_analysis()
    analyzer.save_results(args.output_dir)
    
    print(f"分析完成! 共分析了 {len(individual_results)} 篇故事，{len(group_results)} 个条件组")

if __name__ == "__main__":
    main()
