#!/usr/bin/env python3
"""
正确的文档级Self-BLEU计算
逐seed、整篇文档级的Self-BLEU，使用sacrebleu/corpus_bleu
"""

import pandas as pd
import numpy as np
import os
import re
import json
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

try:
    import sacrebleu
    USE_SACREBLEU = True
    print("使用sacrebleu库进行文档级BLEU计算")
except ImportError:
    USE_SACREBLEU = False
    print("sacrebleu未安装，使用NLTK corpus_bleu")
    from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction

class DocumentLevelSelfBLEU:
    def __init__(self, data_dirs):
        self.data_dirs = data_dirs
        self.stories_data = {}
        self.tokenization = 'intl'  # sacrebleu tokenization
        self.use_sacrebleu = USE_SACREBLEU
        
    def load_story_text(self, story_dir):
        """从故事目录加载文本"""
        story_file = story_dir / 'enhanced_story_dialogue_updated.md'
        
        if not story_file.exists():
            alt_files = ['enhanced_story_updated.md', 'novel_story.md']
            for alt_file in alt_files:
                alt_path = story_dir / alt_file
                if alt_path.exists():
                    with open(alt_path, 'r', encoding='utf-8') as f:
                        return f.read()
        else:
            with open(story_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        return ""
    
    def clean_text_for_bleu(self, text):
        """清理文本用于BLEU计算"""
        # 移除markdown标记
        text = re.sub(r'#.*?\n', ' ', text)
        text = re.sub(r'\*\*.*?\*\*', lambda m: m.group(0)[2:-2], text)  # 保持加粗内容
        text = re.sub(r'\*.*?\*', lambda m: m.group(0)[1:-1], text)      # 保持斜体内容
        
        # 规范化空白字符
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def parse_config_name(self, dir_name):
        """从目录名解析配置信息"""
        parts = dir_name.split('_')
        
        if 'sciencefictionrewrite' in dir_name:
            genre = 'sciencefiction'
            structure = parts[2] 
            temp_seed = parts[3:]
        elif 'horror-suspenserewrite' in dir_name:
            genre = 'horror'
            structure = parts[2]
            temp_seed = parts[3:]
        elif 'romanticrewrite' in dir_name:
            genre = 'romantic'
            structure = parts[2]
            temp_seed = parts[3:]
        else:
            return None
            
        # 解析温度和种子
        temp_match = re.search(r'T(0\.[379])', ''.join(temp_seed))
        seed_match = re.search(r's([123])', ''.join(temp_seed))
        
        if temp_match and seed_match:
            temperature = temp_match.group(1)
            seed = seed_match.group(1)
            
            return {
                'genre': genre,
                'structure': structure, 
                'temperature': temperature,
                'seed': seed,
                'story_id': f"{genre}_{structure}_T{temperature}_s{seed}",
                'group_key': f"{genre}_{structure}_T{temperature}"
            }
        
        return None
    
    def collect_stories(self):
        """收集所有故事数据"""
        print("收集故事文本数据...")
        
        for data_dir in self.data_dirs:
            print(f"\n处理目录: {data_dir}")
            
            if not os.path.exists(data_dir):
                continue
                
            for story_dir_name in os.listdir(data_dir):
                story_dir_path = Path(data_dir) / story_dir_name
                
                if not story_dir_path.is_dir():
                    continue
                
                config = self.parse_config_name(story_dir_name)
                if not config:
                    continue
                
                story_text = self.load_story_text(story_dir_path)
                if not story_text:
                    continue
                
                cleaned_text = self.clean_text_for_bleu(story_text)
                
                self.stories_data[config['story_id']] = {
                    **config,
                    'raw_text': story_text,
                    'clean_text': cleaned_text,
                    'text_length': len(cleaned_text.split()),
                    'dir_name': story_dir_name
                }
                
                print(f"  ✓ {config['story_id']}: {len(cleaned_text.split())} words")
        
        print(f"\n总共收集 {len(self.stories_data)} 个故事")
    
    def calculate_document_self_bleu_sacrebleu(self, hypothesis, references):
        """使用sacrebleu计算文档级BLEU"""
        if not references:
            return 0.0
        
        try:
            bleu = sacrebleu.sentence_bleu(
                hypothesis, 
                references,
                tokenize=self.tokenization,
                smooth_method='exp',  # 指数平滑
                smooth_value=0.01,
                use_effective_order=True
            )
            return bleu.score / 100.0  # sacrebleu返回百分制，转换为小数
        except Exception as e:
            print(f"    sacrebleu计算失败: {e}")
            return 0.0
    
    def calculate_document_self_bleu_nltk(self, hypothesis, references):
        """使用NLTK计算文档级BLEU"""
        if not references:
            return 0.0
        
        try:
            # 分词
            hyp_tokens = hypothesis.lower().split()
            ref_tokens_list = [ref.lower().split() for ref in references]
            
            smoothing = SmoothingFunction().method1
            
            bleu = corpus_bleu(
                [ref_tokens_list],  # 每个候选对应的参考列表
                [hyp_tokens],       # 候选列表
                smoothing_function=smoothing,
                weights=(0.25, 0.25, 0.25, 0.25)
            )
            return bleu
        except Exception as e:
            print(f"    NLTK BLEU计算失败: {e}")
            return 0.0
    
    def calculate_group_self_bleu(self, group_stories):
        """计算组内每个故事的Self-BLEU"""
        if len(group_stories) < 2:
            return {}
        
        results = {}
        
        for i, (story_id, story_data) in enumerate(group_stories):
            hypothesis = story_data['clean_text']
            
            # 获取其他故事作为参考
            references = []
            for j, (other_story_id, other_story_data) in enumerate(group_stories):
                if i != j:
                    references.append(other_story_data['clean_text'])
            
            # 计算Self-BLEU
            if self.use_sacrebleu:
                self_bleu = self.calculate_document_self_bleu_sacrebleu(hypothesis, references)
            else:
                self_bleu = self.calculate_document_self_bleu_nltk(hypothesis, references)
            
            one_minus_self_bleu = 1.0 - self_bleu
            
            results[story_id] = {
                'self_bleu': self_bleu,
                'one_minus_self_bleu': one_minus_self_bleu,
                'hypothesis_length': len(hypothesis.split()),
                'reference_count': len(references),
                'reference_lengths': [len(ref.split()) for ref in references]
            }
            
            print(f"    {story_id}:")
            print(f"      self_bleu: {self_bleu:.6f}")
            print(f"      one_minus_self_bleu: {one_minus_self_bleu:.6f}")
            print(f"      text_length: {len(hypothesis.split())} words")
        
        return results
    
    def calculate_all_self_bleu(self):
        """计算所有组的Self-BLEU"""
        print("\n" + "="*80)
        print("计算文档级Self-BLEU")
        print("="*80)
        
        # 按组组织数据
        groups = defaultdict(list)
        for story_id, story_data in self.stories_data.items():
            groups[story_data['group_key']].append((story_id, story_data))
        
        all_results = {}
        
        for group_key, group_stories in groups.items():
            print(f"\n处理组: {group_key} ({len(group_stories)} stories)")
            
            if len(group_stories) != 3:
                print(f"  警告: 组内故事数 = {len(group_stories)}, 跳过")
                continue
            
            group_results = self.calculate_group_self_bleu(group_stories)
            all_results.update(group_results)
            
            # 组级统计
            if group_results:
                self_bleus = [r['self_bleu'] for r in group_results.values()]
                one_minus_bleus = [r['one_minus_self_bleu'] for r in group_results.values()]
                
                print(f"  组级统计:")
                print(f"    self_bleu: {np.mean(self_bleus):.6f} ± {np.std(self_bleus):.6f}")
                print(f"    self_bleu CV: {np.std(self_bleus)/np.mean(self_bleus):.6f}")
                print(f"    one_minus_self_bleu: {np.mean(one_minus_bleus):.6f} ± {np.std(one_minus_bleus):.6f}")
                print(f"    one_minus_self_bleu CV: {np.std(one_minus_bleus)/np.mean(one_minus_bleus):.6f}")
        
        return all_results
    
    def generate_corrected_dataset(self, self_bleu_results):
        """生成修正后的数据集"""
        print("\n" + "="*80)
        print("生成修正后的数据集")
        print("="*80)
        
        # 读取原始diversity数据
        original_df = pd.read_csv('/Users/haha/Story/corrected_diversity_per_seed.csv')
        
        corrected_rows = []
        
        for _, row in original_df.iterrows():
            story_id = row['story_id']
            
            # 获取修正的Self-BLEU数据
            if story_id in self_bleu_results:
                bleu_data = self_bleu_results[story_id]
                new_self_bleu = bleu_data['self_bleu']
                new_one_minus_self_bleu = bleu_data['one_minus_self_bleu']
            else:
                new_self_bleu = np.nan
                new_one_minus_self_bleu = np.nan
            
            corrected_row = {
                'story_id': story_id,
                'genre': row['genre'],
                'structure': row['structure'],
                'temperature': row['temperature'],
                'seed': row['seed'],
                'distinct_avg': row['distinct_avg'],
                'self_bleu_corrected': new_self_bleu,
                'one_minus_self_bleu_corrected': new_one_minus_self_bleu,
                'word_count': row['word_count'],
                'dir_name': row['dir_name']
            }
            
            corrected_rows.append(corrected_row)
        
        corrected_df = pd.DataFrame(corrected_rows)
        corrected_df = corrected_df.sort_values(['genre', 'structure', 'temperature', 'seed'])
        
        
    
    # 5. 计算per-seed diversity分数 (避免组级泄漏)
    print("\n计算per-seed diversity分数 (避免组级泄漏)...")
    alpha = 0.6  # 固定alpha值，后续可学习
    
    # 直接逐seed计算，避免组级泄漏
    corrected_df['diversity_score_seed'] = (
        alpha * corrected_df['one_minus_self_bleu_corrected'] + 
        (1 - alpha) * corrected_df['distinct_avg']
    )
    
    # 设置alpha相关字段
    corrected_df['alpha_value'] = alpha
    corrected_df['alpha_genre'] = alpha
    
    print(f"   ✅ 为 {len(corrected_df)} 个故事计算了per-seed diversity分数")
    
    # 验证无组级泄漏
    leakage_check = corrected_df.groupby(['genre', 'structure', 'temperature']).agg({
        'diversity_score_seed': 'nunique',
        'distinct_avg': 'nunique'
    })
    
    diversity_fixed = (leakage_check['diversity_score_seed'] > 1).sum()
    total_groups = len(leakage_check)
    
    print(f"   ✅ 验证结果: {diversity_fixed}/{total_groups} 组有真实变异性")
    
    return corrected_df

def calculate_diversity_group_score(corrected_df):
        """重新计算diversity_group_score"""
        print("\n重新计算diversity_group_score...")
        
        # 按组计算alpha权重和diversity_score
        groups = corrected_df.groupby(['genre', 'structure', 'temperature'])
        
        for group_key, group_df in groups:
            genre, structure, temp = group_key
            print(f"\n组 {genre}_{structure}_T{temp}:")
            
            # 获取组内数据
            distinct_avgs = group_df['distinct_avg'].values
            one_minus_bleus = group_df['one_minus_self_bleu_corrected'].values
            
            if len(distinct_avgs) == 3 and not np.any(pd.isna(one_minus_bleus)):
                # 计算简化的alpha (暂时使用0.6作为默认值)
                alpha = 0.6
                
                # 计算组内平均和diversity_score
                avg_distinct = np.mean(distinct_avgs)
                avg_one_minus_bleu = np.mean(one_minus_bleus)
                
                diversity_group_score = alpha * avg_one_minus_bleu + (1 - alpha) * avg_distinct
                
                # 为组内所有故事设置相同的组级分数
                mask = ((corrected_df['genre'] == genre) & 
                       (corrected_df['structure'] == structure) & 
                       (corrected_df['temperature'] == temp))
                
                corrected_df.loc[mask, 'diversity_group_score'] = diversity_group_score
                corrected_df.loc[mask, 'alpha_value'] = alpha
                
                print(f"  distinct_avg: {avg_distinct:.6f}")
                print(f"  one_minus_self_bleu: {avg_one_minus_bleu:.6f}")
                print(f"  alpha: {alpha:.3f}")
                print(f"  diversity_group_score: {diversity_group_score:.6f}")
            else:
                print(f"  数据不完整，跳过diversity_group_score计算")
        
        
    
    # 5. 计算per-seed diversity分数 (避免组级泄漏)
    print("\n计算per-seed diversity分数 (避免组级泄漏)...")
    alpha = 0.6  # 固定alpha值，后续可学习
    
    # 直接逐seed计算，避免组级泄漏
    corrected_df['diversity_score_seed'] = (
        alpha * corrected_df['one_minus_self_bleu_corrected'] + 
        (1 - alpha) * corrected_df['distinct_avg']
    )
    
    # 设置alpha相关字段
    corrected_df['alpha_value'] = alpha
    corrected_df['alpha_genre'] = alpha
    
    print(f"   ✅ 为 {len(corrected_df)} 个故事计算了per-seed diversity分数")
    
    # 验证无组级泄漏
    leakage_check = corrected_df.groupby(['genre', 'structure', 'temperature']).agg({
        'diversity_score_seed': 'nunique',
        'distinct_avg': 'nunique'
    })
    
    diversity_fixed = (leakage_check['diversity_score_seed'] > 1).sum()
    total_groups = len(leakage_check)
    
    print(f"   ✅ 验证结果: {diversity_fixed}/{total_groups} 组有真实变异性")
    
    return corrected_df
    
    def run_complete_correction(self):
        """运行完整的修正流程"""
        print("="*80)
        print("文档级Self-BLEU完整修正流程")
        print("="*80)
        
        # 1. 收集故事数据
        self.collect_stories()
        
        # 2. 计算Self-BLEU
        self_bleu_results = self.calculate_all_self_bleu()
        
        # 3. 生成修正数据集
        corrected_df = self.generate_corrected_dataset(self_bleu_results)
        
        # 4. 重新计算diversity_group_score
        final_df = self.calculate_diversity_group_score(corrected_df)
        
        # 5. 保存结果
        output_file = '/Users/haha/Story/final_corrected_diversity_data.csv'
        final_df.to_csv(output_file, index=False, encoding='utf-8')
        
        # 6. 输出统计结果
        print(f"\n" + "="*80)
        print("修正完成统计")
        print("="*80)
        
        print(f"✅ 修正后数据已保存到: {output_file}")
        print(f"📊 数据统计:")
        print(f"   总故事数: {len(final_df)}")
        print(f"   有效Self-BLEU数: {final_df['self_bleu_corrected'].notna().sum()}")
        print(f"   Self-BLEU范围: [{final_df['self_bleu_corrected'].min():.6f}, {final_df['self_bleu_corrected'].max():.6f}]")
        
        return final_df, self_bleu_results

def main():
    """主函数"""
    data_dirs = [
        '/Users/haha/Story/data/output/regression_test',
        '/Users/haha/Story/data/output/horror_test', 
        '/Users/haha/Story/data/output/romantic_test'
    ]
    
    calculator = DocumentLevelSelfBLEU(data_dirs)
    final_df, results = calculator.run_complete_correction()
    
    return final_df, results

if __name__ == "__main__":
    df, results = main()
