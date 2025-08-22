"""
主次法情感弧线分析器 (更新版)
主要方法：RoBERTa（现代深度学习模型）
验证方法：LabMT（经典方法，与Reagan原文一致）
"""

import re
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import requests
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from scipy.stats import pearsonr, spearmanr

class DualMethodEmotionalAnalyzer:
    """
    主次法情感分析器 (更新版)
    主要：RoBERTa分析
    验证：LabMT分析
    """
    
    def __init__(self, labmt_version='v1'):
        """
        初始化双方法分析器
        
        Args:
            labmt_version: 'v1' (2011, 与Reagan一致) 或 'v2' (2020, 更现代)
        """
        print("🚀 初始化主次法情感分析器（RoBERTa版）...")
        
        self.labmt_version = labmt_version
        print(f"📋 选择LabMT版本: {labmt_version} ({'与Reagan原文一致' if labmt_version == 'v1' else '更现代的版本'})")
        
        # 初始化RoBERTa（主要方法）
        self._init_roberta()
        
        # 初始化LabMT（验证方法）
        self._init_labmt()
        
        print("✅ 双方法分析器准备就绪")
    
    def _init_roberta(self):
        """初始化RoBERTa分析器"""
        try:
            from transformers import pipeline
            
            print("📥 加载RoBERTa模型...")
            # 使用你测试过的RoBERTa模型
            self.roberta_classifier = pipeline(
                "sentiment-analysis", 
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                truncation=True,
                max_length=512
            )
            print("✅ RoBERTa分析器初始化成功（主要方法）")
            
        except ImportError:
            print("❌ RoBERTa初始化失败，请安装transformers")
            raise ImportError("请运行: pip install transformers torch")
        except Exception as e:
            print(f"❌ RoBERTa模型加载失败: {e}")
            # 尝试备选模型
            try:
                print("🔄 尝试备选模型...")
                self.roberta_classifier = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    truncation=True,
                    max_length=512
                )
                print("✅ 备选模型DistilBERT加载成功")
            except:
                raise ImportError("所有模型加载失败，请检查网络连接")
    
    def _init_labmt(self):
        """初始化LabMT词典"""
        # 尝试加载本地LabMT文件
        possible_paths = [
            '/Users/haha/Story/data/Hedonometer.csv',
            './labMT.csv',
            './data/labMT.csv',
            '../data/labMT.csv'
        ]
        
        labmt_found = False
        for path in possible_paths:
            if os.path.exists(path):
                print(f"📁 发现本地LabMT词典文件: {path}")
                self._load_labmt_local(path)
                labmt_found = True
                break
        
        if not labmt_found:
            print("📥 下载LabMT词典...")


    
    def _load_labmt_local(self, file_path='/Users/haha/Story/data/Hedonometer.csv'):
        """加载本地LabMT文件 - 修复版"""
        import pandas as pd
        
        try:
            print(f"🔍 读取LabMT文件: {file_path}")
            
            # 使用逗号分隔符读取
            df = pd.read_csv(file_path, sep=',')
            print(f"📊 数据形状: {df.shape}")
            
            # 使用正确的列名
            word_col = 'Word'
            happiness_col = 'Happiness Score'
            
            # 构建词典
            self.labmt_dict = {}
            valid_count = 0
            
            for _, row in df.iterrows():
                try:
                    word = str(row[word_col]).lower().strip()
                    score = float(row[happiness_col])
                    
                    # 过滤中性词
                    if len(word) > 1 and 1.0 <= score <= 9.0 and not (4.0 <= score <= 6.0):
                        self.labmt_dict[word] = score
                        valid_count += 1
                except:
                    continue
            
            print(f"✅ LabMT词典加载成功，有效词汇: {valid_count}")
            
        except Exception as e:
            print(f"❌ 文件读取失败: {e}")
            self._init_simple_labmt()
        

    def analyze_with_roberta_correct(self, text: str) -> float:
        """RoBERTa情感分析（主要方法）- 修复版"""
        if not text or not text.strip():
            return 0.0
        
        try:
            if len(text) <= 500:
                result = self.roberta_classifier(text)[0]
                return self.convert_roberta_score(result)
            else:
                # 分句分析（修复版）
                sentences = [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 10]
                scores = []
                
                for sentence in sentences[:15]:  # 分析前15句
                    try:
                        result = self.roberta_classifier(sentence)[0]
                        score = self.convert_roberta_score(result)
                        scores.append(score)
                    except:
                        continue
                
                return sum(scores) / len(scores) if scores else 0.0
                
        except Exception as e:
            print(f"RoBERTa分析错误: {e}")
            return 0.0
    
    def convert_roberta_score(self, result):
        """正确转换RoBERTa分数"""
        label = result['label'].lower()
        score = result['score']
        
        if label == 'positive':
            return score  # 0到1的正值
        elif label == 'negative':
            return -score  # 0到-1的负值
        elif label == 'neutral':
            return 0.0  # 中性为0
        else:
            print(f"未知标签: {label}")
            return 0.0
    
    def analyze_labmt(self, text: str) -> float:
        """LabMT情感分析（验证方法）"""
        if not text or not text.strip():
            return 0.0  # 改为0.0以与RoBERTa保持一致
        
        # 文本预处理
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        if not words:
            return 0.0
        
        # 计算情感分数
        total_score = 0
        valid_words = 0
        
        for word in words:
            if word in self.labmt_dict:
                total_score += self.labmt_dict[word]
                valid_words += 1
        
        if valid_words == 0:
            return 0.0
        
        avg_score = total_score / valid_words
        
        # 转换为-1到1范围（为了与RoBERTa对比）
        # LabMT: 1-9 -> 转换为 -1到1
        normalized_score = (avg_score - 5.0) / 4.0  # (score-5)/4
        return max(-1, min(1, normalized_score))
    
    def parse_story(self, md_content: str) -> List[Dict]:
        """解析story文件"""
        chapters = []
        
        # 按章节分割
        chapter_pattern = r'# Chapter (\d+)[：:]([^\n]+)'
        splits = re.split(chapter_pattern, md_content)
        
        if len(splits) < 3:
            print("⚠️ 未检测到标准章节格式，尝试按# 分割")
            parts = md_content.split('\n# ')
            for i, part in enumerate(parts[1:], 1):
                lines = part.split('\n')
                title = lines[0].strip()
                content = '\n'.join(lines[1:]).strip()
                if content:
                    chapters.append({
                        'chapter_num': i,
                        'title': title,
                        'content': content
                    })
        else:
            for i in range(1, len(splits), 3):
                if i + 2 < len(splits):
                    chapter_num = int(splits[i])
                    title = splits[i + 1].strip()
                    content = splits[i + 2].strip()
                    
                    # 清理内容
                    content = re.sub(r'-{20,}', '', content)
                    content = content.strip()
                    
                    chapters.append({
                        'chapter_num': chapter_num,
                        'title': title,
                        'content': content
                    })
        
        print(f"✅ 解析到 {len(chapters)} 个章节")
        return chapters
    
    def analyze_story_dual_method(self, chapters: List[Dict]) -> Dict:
        """双方法分析故事情感弧线（RoBERTa版）"""
        if not chapters:
            return {"error": "没有章节数据"}
        
        print("🔍 开始双方法情感分析（RoBERTa + LabMT）...")
        
        # 1. 对每章进行双方法分析
        chapter_analysis = []
        roberta_scores = []
        labmt_scores = []
        
        for chapter in chapters:
            print(f"  分析第 {chapter['chapter_num']} 章: {chapter['title'][:30]}...")
            
            # RoBERTa分析（主要）
            roberta_score = self.analyze_with_roberta_correct(chapter['content'])
            
            # LabMT分析（验证）
            labmt_score = self.analyze_labmt(chapter['content'])
            
            chapter_analysis.append({
                'chapter_num': chapter['chapter_num'],
                'title': chapter['title'],
                'roberta_score': round(roberta_score, 4),
                'labmt_score': round(labmt_score, 4),
                'content_length': len(chapter['content'])
            })
            
            roberta_scores.append(roberta_score)
            labmt_scores.append(labmt_score)
        
        # 2. 计算两种方法的相关性
        correlation_analysis = self._analyze_correlation(roberta_scores, labmt_scores)
        
        # 3. Reagan六型分类（基于主要方法RoBERTa）
        reagan_classification = self._classify_reagan_arc(roberta_scores, method="RoBERTa")
        
        # 4. 验证分类（基于LabMT）
        labmt_classification = self._classify_reagan_arc(labmt_scores, method="LabMT")
        
        # 5. 生成对比分析
        comparison_analysis = self._generate_comparison_analysis(
            roberta_scores, labmt_scores, reagan_classification, labmt_classification
        )
        
        # 6. 组装结果（标准格式）
        result = {
            'metadata': {
                'total_chapters': len(chapters),
                'primary_method': 'RoBERTa',
                'validation_method': f'LabMT-en-{getattr(self, "actual_labmt_version", self.labmt_version)}',
                'analysis_timestamp': datetime.now().isoformat()
            },
            'chapter_analysis': chapter_analysis,
            'primary_analysis': {
                'method': 'RoBERTa',
                'scores': roberta_scores,
                'reagan_classification': reagan_classification
            },
            'validation_analysis': {
                'method': 'LabMT', 
                'scores': labmt_scores,
                'reagan_classification': labmt_classification
            },
            'correlation_analysis': correlation_analysis,
            'comparison_analysis': comparison_analysis,
            'final_conclusion': self._generate_final_conclusion(correlation_analysis, comparison_analysis)
        }
        
        print("✅ 双方法分析完成！")
        print(f"📊 相关系数: {correlation_analysis['pearson_correlation']['r']:.3f}")
        print(f"🎯 RoBERTa分类: {reagan_classification['best_match']} (置信度: {reagan_classification['confidence']:.3f})")
        print(f"🔍 LabMT分类: {labmt_classification['best_match']} (置信度: {labmt_classification['confidence']:.3f})")
        
        return result
    
    # 保留原有的其他方法不变
    def _analyze_correlation(self, scores1: List[float], scores2: List[float]) -> Dict:
        """分析两种方法的相关性"""
        if len(scores1) != len(scores2) or len(scores1) < 2:
            return {"error": "数据不足"}
        
        # 计算相关系数
        pearson_r, pearson_p = pearsonr(scores1, scores2)
        spearman_r, spearman_p = spearmanr(scores1, scores2)
        
        # 计算方向一致性
        direction_agreement = 0
        for i in range(1, len(scores1)):
            roberta_direction = np.sign(scores1[i] - scores1[i-1])
            labmt_direction = np.sign(scores2[i] - scores2[i-1])
            if roberta_direction == labmt_direction:
                direction_agreement += 1
        
        direction_consistency = direction_agreement / max(1, len(scores1) - 1)
        
        return {
            'pearson_correlation': {
                'r': round(pearson_r, 4),
                'p_value': round(pearson_p, 4),
                'significance': 'Significant' if pearson_p < 0.05 else 'Not Significant'
            },
            'spearman_correlation': {
                'r': round(spearman_r, 4),
                'p_value': round(spearman_p, 4)
            },
            'direction_consistency': round(direction_consistency, 4),
            'consistency_level': 'High' if abs(pearson_r) > 0.7 else 'Medium' if abs(pearson_r) > 0.5 else 'Low',
            'interpretation': f"RoBERTa与LabMT相关系数为{pearson_r:.3f}，属于{'强相关' if abs(pearson_r) > 0.7 else '中等相关' if abs(pearson_r) > 0.5 else '弱相关'}"
        }
    
    def _classify_reagan_arc(self, scores: List[float], method: str) -> Dict:
        """Reagan六种弧线分类"""
        if len(scores) < 3:
            return {
                'best_match': 'Unknown',
                'confidence': 0.0,
                'method': method,
                'all_similarities': {}
            }
        
        # 生成标准弧线模式
        standard_arcs = self._generate_standard_arcs(len(scores))
        
        # 计算相似度
        similarities = {}
        for arc_name, arc_pattern in standard_arcs.items():
            similarity = self._cosine_similarity(scores, arc_pattern)
            similarities[arc_name] = round(max(0, similarity), 4)
        
        best_match = max(similarities, key=similarities.get)
        confidence = similarities[best_match]
        
        return {
            'method': method,
            'best_match': best_match,
            'confidence': confidence,
            'all_similarities': similarities,
            'reagan_category': self._get_reagan_category(best_match)
        }
    
    def _generate_standard_arcs(self, length: int) -> Dict[str, List[float]]:
        """生成标准弧线模式"""
        x = np.linspace(0, 1, length)
        
        return {
            'Rags to riches': [0.8 * (t - 0.2) for t in x],
            'Tragedy': [0.8 * (0.8 - t) for t in x],
            'Man in a hole': [0.5 * np.sin(np.pi * t - np.pi/2) for t in x],
            'Icarus': [0.5 * np.sin(np.pi * t + np.pi/2) for t in x],
            'Cinderella': [0.5 * np.sin(2 * np.pi * t - np.pi/2) for t in x],
            'Oedipus': [0.5 * np.sin(2 * np.pi * t + np.pi/2) for t in x]
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return max(0, dot_product / (norm1 * norm2))
    
    def _get_reagan_category(self, arc_type: str) -> str:
        """获取Reagan原文分类代码"""
        categories = {
            "Rags to riches": "RR",
            "Tragedy": "TR", 
            "Man in a hole": "MH",
            "Icarus": "IC",
            "Cinderella": "CN",
            "Oedipus": "OE"
        }
        return categories.get(arc_type, "UK")
    
    def _generate_comparison_analysis(self, roberta_scores, labmt_scores, 
                                    roberta_class, labmt_class) -> Dict:
        """生成对比分析"""
        
        # 分析分歧点
        disagreement_points = []
        for i, (r_score, l_score) in enumerate(zip(roberta_scores, labmt_scores)):
            diff = abs(r_score - l_score)
            if diff > 0.3:  # 分歧阈值
                disagreement_points.append({
                    'chapter': i + 1,
                    'roberta_score': r_score,
                    'labmt_score': l_score,
                    'difference': round(diff, 4)
                })
        
        # 方法优势分析
        method_advantages = {
            'RoBERTa': {
                'strengths': [
                    "深度学习模型，对上下文理解更好",
                    "适合现代文本和对话",
                    "对科幻、技术类文本敏感度高"
                ],
                'classification': roberta_class['best_match'],
                'confidence': roberta_class['confidence']
            },
            'LabMT': {
                'strengths': [
                    "与Reagan原文方法完全一致",
                    "基于大规模人工标注",
                    "适合传统文学分析"
                ],
                'classification': labmt_class['best_match'],
                'confidence': labmt_class['confidence']
            }
        }
        
        # 一致性评估
        consistency_assessment = {
            'classification_agreement': roberta_class['best_match'] == labmt_class['best_match'],
            'major_disagreements': len(disagreement_points),
            'recommendation': self._generate_recommendation(roberta_class, labmt_class, disagreement_points)
        }
        
        return {
            'disagreement_points': disagreement_points,
            'method_advantages': method_advantages,
            'consistency_assessment': consistency_assessment
        }
    
    def _generate_recommendation(self, roberta_class, labmt_class, disagreements) -> str:
        """生成使用建议"""
        if roberta_class['best_match'] == labmt_class['best_match']:
            return f"两种方法都识别为{roberta_class['best_match']}，结果高度一致，建议以RoBERTa为主要分析结果"
        elif len(disagreements) <= 2:
            return f"分类略有差异但整体一致，建议以RoBERTa为主，LabMT为验证，体现了现代深度学习模型的优势"
        else:
            return f"两种方法差异较大，建议详细分析差异原因，可能需要更深入的文本特征分析"
    
    def _generate_final_conclusion(self, correlation_analysis, comparison_analysis) -> str:
        """生成最终结论"""
        pearson_r = correlation_analysis['pearson_correlation']['r']
        consistency_level = correlation_analysis['consistency_level']
        
        conclusion = f"""
📊 RoBERTa + LabMT 双方法分析结论：

📈 相关性分析：
- Pearson相关系数: r = {pearson_r:.3f} ({consistency_level})
- 一致性水平: {correlation_analysis['interpretation']}

🎯 分类结果：
- RoBERTa (主要): {comparison_analysis['method_advantages']['RoBERTa']['classification']}
- LabMT (验证): {comparison_analysis['method_advantages']['LabMT']['classification']}

📝 方法学说明：
本研究采用RoBERTa作为主要分析方法（现代深度学习模型），
使用LabMT进行交叉验证（与Reagan et al. 2016保持一致）。
相关系数为{pearson_r:.3f}，两种方法{consistency_level.lower()}一致。

建议：以RoBERTa结果为主，LabMT作为学术基准验证。
        """.strip()
        
        return conclusion
    
    def save_results(self, result: Dict, output_dir: str = "./output/") -> str:
        """保存分析结果"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roberta_labmt_analysis_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 分析结果已保存至：{filepath}")
        return filepath


def analyze_story_dual_method(file_path: str, output_dir: str = "./output/") -> Dict:
    """
    RoBERTa + LabMT 双方法故事分析完整流程
    
    Args:
        file_path: 故事文件路径
        output_dir: 输出目录
    
    Returns:
        标准格式的完整分析结果
    """
    print("🚀 开始RoBERTa + LabMT双方法情感弧线分析...")
    print(f"📄 主要方法: RoBERTa (深度学习)")
    print(f"🔍 验证方法: LabMT (Reagan原文一致)")
    
    # 1. 读取文件
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ 成功读取文件：{file_path}")
    except Exception as e:
        return {"error": f"文件读取失败：{e}"}
    
    # 2. 初始化分析器
    analyzer = DualMethodEmotionalAnalyzer()
    
    # 3. 解析故事
    chapters = analyzer.parse_story(content)
    if not chapters:
        return {"error": "未能解析到章节内容"}
    
    # 4. 双方法分析
    result = analyzer.analyze_story_dual_method(chapters)
    if "error" in result:
        return result
    
    # 5. 保存结果
    try:
        json_path = analyzer.save_results(result, output_dir)
        result['output_files'] = {'analysis_json': json_path}
    except Exception as e:
        print(f"⚠️ 保存结果失败：{e}")
        result['output_files'] = {}
    
    # 6. 打印结果摘要
    print("\n" + "="*60)
    print("📊 RoBERTa + LabMT 双方法分析完成！")
    print("="*60)
    
    # 打印主要结果
    primary = result['primary_analysis']
    validation = result['validation_analysis']
    correlation = result['correlation_analysis']
    
    print(f"🎯 主要分析 (RoBERTa): {primary['reagan_classification']['best_match']}")
    print(f"🔍 验证分析 (LabMT): {validation['reagan_classification']['best_match']}")
    print(f"📈 相关系数: r={correlation['pearson_correlation']['r']:.3f} ({correlation['consistency_level']})")
    
    print(f"\n📋 各章节分数对比:")
    for ch in result['chapter_analysis']:
        print(f"  第{ch['chapter_num']}章: RoBERTa={ch['roberta_score']:.3f}, LabMT={ch['labmt_score']:.3f}")
    
    print(f"\n{result['final_conclusion']}")
    
    return result


# 直接运行示例
if __name__ == "__main__":
    print("🎭 RoBERTa + LabMT 双方法情感弧线分析器")
    print("主要方法：RoBERTa（现代深度学习模型）")
    print("验证方法：LabMT（与Reagan原文一致）")
    
    # 检查是否有故事文件
    possible_files = [
        '/Users/haha/Story/data/output/小红帽_科幻_linear_T0.7_s1/enhance.md',  # 用户的具体文件
        'enhanced_story_dialogue_updated.md',
        'data/enhanced_story_dialogue_updated.md',
        './output/小红帽_科幻_linear_T0.7_s1/enhance.md',
        './小红帽_科幻_linear_T0.7_s1/enhance.md'
    ]
    
    story_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            story_file = file_path
            break
    
    if story_file:
        print(f"\n📁 找到故事文件: {story_file}")
        print("🚀 开始分析...")
        
        try:
            result = analyze_story_dual_method(story_file, "./output/")
            
            # 保存result变量供后续使用
            print(f"\n💾 result变量已生成，可用于可视化:")
            print(f"   - 类型: {type(result)}")
            print(f"   - 章节数: {result['metadata']['total_chapters']}")
            print(f"   - 相关性: {result['correlation_analysis']['pearson_correlation']['r']:.3f}")
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            print("\n💡 可能的解决方案：")
            print("1. 检查故事文件格式是否正确")
            print("2. 安装缺失的依赖: pip install transformers torch nltk pandas requests scipy")
            print("3. 检查网络连接（下载模型需要）")
    else:
        print("\n❌ 未找到故事文件")
        print("📁 请确保文件在以下位置之一：")
        for fp in possible_files:
            print(f"   - {fp}")
        print("\n💡 或者手动指定文件路径：")
        print("   from emotional_arc_analyzer import analyze_story_dual_method")
        print("   result = analyze_story_dual_method('你的文件路径.md')")