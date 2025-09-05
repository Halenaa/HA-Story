"""
计算复杂度分析器
用于收集和分析故事生成流程的性能数据，包括时间复杂度、文本统计等
"""

import time
import json
import datetime
import re
import os
import psutil
import threading
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import numpy as np
from src.utils.utils import split_plot_into_sentences, save_json, load_json


class PerformanceAnalyzer:
    """性能分析器：监控生成时间、内存使用、API成本和文本统计"""
    
    def __init__(self, task_name: str = "default", enable_memory_monitoring: bool = True, experiment_config: Dict = None):
        self.task_name = task_name
        self.stage_times = {}
        self.stage_start_times = {}
        self.text_features = {}
        self.raw_data = {}
        self.total_start_time = None
        
        # 实验配置参数
        self.experiment_config = experiment_config or {}
        
        # API响应时间统计
        self.api_response_times = {}
        
        # 错误和异常记录
        self.error_log = {
            'api_failures': 0,
            'parsing_errors': 0, 
            'retry_attempts': 0,
            'error_details': []
        }
        
        # 缓存使用统计
        self.cache_usage = {
            'cache_hits': {},
            'total_cache_hits': 0,
            'total_cache_attempts': 0
        }
        
        # 内存监控
        self.enable_memory_monitoring = enable_memory_monitoring
        self.memory_timeline = []
        self.stage_memory_usage = {}
        self.peak_memory_usage = 0
        self.memory_monitor_thread = None
        self.memory_monitoring_active = False
        self.process = psutil.Process(os.getpid())
        
        # API成本和Token跟踪
        self.api_costs = {}
        self.token_consumption = {}
        self.total_api_cost = 0.0
        self.total_tokens = 0
        
        # 角色复杂度相关
        self.character_features = {}
        
        # 获取初始内存基线
        if self.enable_memory_monitoring:
            self.baseline_memory = self._get_current_memory_usage()
        
    def start_total_timing(self):
        """开始总计时"""
        self.total_start_time = time.time()
        
        # 开始内存监控
        if self.enable_memory_monitoring:
            self.start_memory_monitoring()
    
    def _get_current_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # 转换为MB
        except:
            return 0.0
    
    def start_memory_monitoring(self):
        """开始内存监控线程"""
        if not self.enable_memory_monitoring or self.memory_monitoring_active:
            return
            
        self.memory_monitoring_active = True
        self.memory_monitor_thread = threading.Thread(target=self._memory_monitor_loop, daemon=True)
        self.memory_monitor_thread.start()
        print("内存监控已启动")
    
    def stop_memory_monitoring(self):
        """停止内存监控"""
        if self.memory_monitoring_active:
            self.memory_monitoring_active = False
            if self.memory_monitor_thread and self.memory_monitor_thread.is_alive():
                self.memory_monitor_thread.join(timeout=1)
            print("内存监控已停止")
    
    def _memory_monitor_loop(self):
        """内存监控循环"""
        while self.memory_monitoring_active:
            try:
                current_memory = self._get_current_memory_usage()
                timestamp = time.time() - self.total_start_time if self.total_start_time else 0
                
                self.memory_timeline.append({
                    'timestamp': timestamp,
                    'memory_mb': current_memory
                })
                
                # 更新峰值内存
                if current_memory > self.peak_memory_usage:
                    self.peak_memory_usage = current_memory
                
                time.sleep(0.5)  # 每0.5秒监控一次
            except Exception as e:
                print(f"内存监控出错: {e}")
                break
        
    def start_stage(self, stage_name: str, input_data: Any = None):
        """开始某个生成阶段的计时"""
        self.stage_start_times[stage_name] = time.time()
        self.raw_data[f"{stage_name}_input"] = self._serialize_data(input_data)
        
        # 记录阶段开始时的内存使用
        if self.enable_memory_monitoring:
            current_memory = self._get_current_memory_usage()
            self.stage_memory_usage[f"{stage_name}_start"] = current_memory
        
    def end_stage(self, stage_name: str, output_data: Any = None):
        """结束某个生成阶段的计时"""
        if stage_name not in self.stage_start_times:
            print(f"警告：{stage_name} 阶段未开始计时")
            return 0
            
        duration = time.time() - self.stage_start_times[stage_name]
        self.stage_times[stage_name] = duration
        self.raw_data[f"{stage_name}_output"] = self._serialize_data(output_data)
        
        # 记录阶段结束时的内存使用和增长
        if self.enable_memory_monitoring:
            current_memory = self._get_current_memory_usage()
            start_memory = self.stage_memory_usage.get(f"{stage_name}_start", 0)
            self.stage_memory_usage[f"{stage_name}_end"] = current_memory
            self.stage_memory_usage[f"{stage_name}_increase"] = current_memory - start_memory
        
        print(f"{stage_name} 耗时: {duration:.3f}s")
        return duration
        
    def get_total_time(self) -> float:
        """获取总执行时间"""
        if self.total_start_time is None:
            return sum(self.stage_times.values())
        return time.time() - self.total_start_time
    
    def add_api_cost(self, stage_name: str, model: str, input_tokens: int, output_tokens: int, 
                     cost: float, api_call_type: str = "completion", response_time: float = 0.0):
        """记录API调用成本和Token消耗"""
        if stage_name not in self.api_costs:
            self.api_costs[stage_name] = []
        
        api_record = {
            'model': model,
            'api_call_type': api_call_type,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'response_time': response_time,
            'timestamp': time.time() - (self.total_start_time or 0)
        }
        
        self.api_costs[stage_name].append(api_record)
        self.total_api_cost += cost
        self.total_tokens += input_tokens + output_tokens
        
        # 记录API响应时间
        if response_time > 0:
            if stage_name not in self.api_response_times:
                self.api_response_times[stage_name] = []
            self.api_response_times[stage_name].append(response_time)
        
        # 更新token消耗统计
        if stage_name not in self.token_consumption:
            self.token_consumption[stage_name] = {
                'input_tokens': 0,
                'output_tokens': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'api_calls': 0
            }
        
        stage_tokens = self.token_consumption[stage_name]
        stage_tokens['input_tokens'] += input_tokens
        stage_tokens['output_tokens'] += output_tokens
        stage_tokens['total_tokens'] += input_tokens + output_tokens
        stage_tokens['total_cost'] += cost
        stage_tokens['api_calls'] += 1
        
        print(f"{stage_name} API调用: {model}, Tokens: {input_tokens + output_tokens}, 成本: ${cost:.4f}")
    
    def record_cache_usage(self, stage_name: str, cache_hit: bool, cache_key: str = None):
        """记录缓存使用情况"""
        self.cache_usage['total_cache_attempts'] += 1
        
        if cache_hit:
            self.cache_usage['total_cache_hits'] += 1
            if stage_name not in self.cache_usage['cache_hits']:
                self.cache_usage['cache_hits'][stage_name] = 0
            self.cache_usage['cache_hits'][stage_name] += 1
            
        print(f"{stage_name} 缓存{'命中' if cache_hit else '未命中'}: {cache_key or 'default'}")
    
    def record_error(self, stage_name: str, error_type: str, error_message: str, resolved: bool = False):
        """记录错误和异常"""
        if error_type == 'api_failure':
            self.error_log['api_failures'] += 1
        elif error_type == 'parsing_error':
            self.error_log['parsing_errors'] += 1
        elif error_type == 'retry':
            self.error_log['retry_attempts'] += 1
            
        self.error_log['error_details'].append({
            'stage': stage_name,
            'error_type': error_type,
            'error_message': error_message,
            'timestamp': time.time() - (self.total_start_time or 0),
            'resolved': resolved
        })
        
        print(f"{stage_name} 错误记录: {error_type} - {error_message}")
    
    def calculate_memory_per_character(self, characters_data: List[Dict]) -> Dict:
        """计算每个角色的内存开销"""
        if not self.enable_memory_monitoring or not characters_data:
            return {}
        
        # 分析角色复杂度
        character_features = self.analyze_character_complexity(characters_data)
        
        # 计算内存相关指标
        memory_metrics = {
            'total_characters': len(characters_data),
            'peak_memory_per_character': self.peak_memory_usage / len(characters_data) if characters_data else 0,
            'character_complexity_features': character_features
        }
        
        # 如果有角色生成阶段的内存增长数据
        char_gen_increase = self.stage_memory_usage.get('character_generation_increase', 0)
        if char_gen_increase > 0:
            memory_metrics['memory_per_character_generation'] = char_gen_increase / len(characters_data)
        
        return memory_metrics
    
    def analyze_character_complexity(self, characters_data: List[Dict]) -> Dict:
        """分析角色复杂度特征"""
        if not characters_data:
            return {}
        
        character_features = {
            'character_count': len(characters_data),
            'total_description_length': 0,
            'avg_description_length': 0,
            'character_complexity_scores': [],
            'character_descriptions_total_length': 0
        }
        
        for char in characters_data:
            # 计算角色描述总长度
            description_parts = [
                char.get('name', ''),
                char.get('role', ''),  
                char.get('traits', ''),
                char.get('background', ''),
                char.get('motivation', '')
            ]
            
            char_description_length = sum(len(str(part)) for part in description_parts)
            character_features['total_description_length'] += char_description_length
            character_features['character_descriptions_total_length'] += char_description_length
            
            # 简单的复杂度评分（基于描述长度和结构化信息）
            complexity_score = (
                len(char.get('traits', '')) * 0.3 +
                len(char.get('background', '')) * 0.4 +
                len(char.get('motivation', '')) * 0.3
            )
            character_features['character_complexity_scores'].append(complexity_score)
        
        character_features['avg_description_length'] = (
            character_features['total_description_length'] / len(characters_data)
        )
        
        # 计算角色复杂度总分
        character_features['character_complexity_score'] = sum(character_features['character_complexity_scores'])
        
        self.character_features = character_features
        return character_features
    
    def calculate_quality_efficiency_tradeoff(self, story_data: Any = None, dialogue_data: Any = None) -> Dict:
        """
        计算质量-效率权衡指标
        
        质量指标包括：
        - 文本长度和丰富度
        - 角色一致性
        - 叙事连贯性
        - 对话质量
        
        效率指标包括：
        - 生成速度
        - API成本效率
        - 内存使用效率
        """
        quality_metrics = self._calculate_quality_metrics(story_data, dialogue_data)
        efficiency_metrics = self._calculate_efficiency_metrics()
        
        # 计算质量-效率平衡分数
        quality_score = quality_metrics.get('overall_quality_score', 0)
        efficiency_score = efficiency_metrics.get('overall_efficiency_score', 0)
        
        # 权衡分析
        tradeoff_analysis = {
            'quality_metrics': quality_metrics,
            'efficiency_metrics': efficiency_metrics,
            'balance_score': (quality_score + efficiency_score) / 2,
            'quality_efficiency_ratio': quality_score / efficiency_score if efficiency_score > 0 else 0,
            'optimization_suggestions': self._generate_optimization_suggestions(quality_metrics, efficiency_metrics)
        }
        
        return tradeoff_analysis
    
    def _calculate_quality_metrics(self, story_data: Any = None, dialogue_data: Any = None) -> Dict:
        """计算质量指标"""
        quality_score = 0
        quality_breakdown = {}
        
        # 1. 文本丰富度评分 (0-10分)
        total_words = self.text_features.get('total_word_count', 0)
        total_chars = self.text_features.get('total_char_count', 0)
        sentence_count = self.text_features.get('sentence_count', 0)
        
        if total_words > 0:
            # 平均句子长度
            avg_sentence_length = total_words / sentence_count if sentence_count > 0 else 0
            richness_score = min(avg_sentence_length / 15, 5)  # 理想句子长度15词左右
            
            # 词汇多样性（简单估算）
            diversity_score = min(total_chars / total_words / 3, 5) if total_words > 0 else 0  # 中文平均字长
            
            text_quality_score = richness_score + diversity_score
        else:
            text_quality_score = 0
        
        quality_breakdown['text_richness'] = text_quality_score
        quality_score += text_quality_score
        
        # 2. 角色复杂度评分 (0-10分)
        char_complexity = self.character_features.get('character_complexity_score', 0)
        char_quality_score = min(char_complexity / 100, 10)  # 标准化到0-10分
        quality_breakdown['character_complexity'] = char_quality_score
        quality_score += char_quality_score
        
        # 3. 结构完整性评分 (0-10分)
        chapter_count = self.text_features.get('chapter_count', 0)
        if chapter_count > 0:
            # 章节平衡性
            avg_chapter_length = total_words / chapter_count if chapter_count > 0 else 0
            structure_score = min(avg_chapter_length / 500, 5)  # 理想章节长度500词左右
            
            # 章节数量合理性
            count_score = 5 if 3 <= chapter_count <= 12 else max(0, 5 - abs(chapter_count - 7))
            
            structure_quality_score = structure_score + count_score
        else:
            structure_quality_score = 0
        
        quality_breakdown['narrative_structure'] = structure_quality_score
        quality_score += structure_quality_score
        
        # 4. 如果有对话数据，评估对话质量 (0-10分)
        if dialogue_data:
            dialogue_quality_score = self._assess_dialogue_quality(dialogue_data)
            quality_breakdown['dialogue_quality'] = dialogue_quality_score
            quality_score += dialogue_quality_score
        
        # 计算总质量分数 (0-100分)
        max_possible_score = 40 if dialogue_data else 30
        overall_quality_score = min((quality_score / max_possible_score) * 100, 100)
        
        return {
            'overall_quality_score': overall_quality_score,
            'quality_breakdown': quality_breakdown,
            'text_metrics': {
                'word_richness': total_words / sentence_count if sentence_count > 0 else 0,
                'character_density': total_chars / total_words if total_words > 0 else 0,
                'narrative_balance': avg_chapter_length if 'avg_chapter_length' in locals() else 0
            }
        }
    
    def _calculate_efficiency_metrics(self) -> Dict:
        """计算效率指标"""
        total_time = self.get_total_time()
        total_words = self.text_features.get('total_word_count', 0)
        total_chars = self.text_features.get('total_char_count', 0)
        
        efficiency_breakdown = {}
        efficiency_score = 0
        
        # 1. 时间效率 (0-25分)
        if total_time > 0 and total_words > 0:
            words_per_second = total_words / total_time
            # 评分标准：5字/秒为满分
            time_efficiency_score = min(words_per_second / 5 * 25, 25)
        else:
            time_efficiency_score = 0
        
        efficiency_breakdown['time_efficiency'] = time_efficiency_score
        efficiency_score += time_efficiency_score
        
        # 2. 成本效率 (0-25分)
        if self.total_api_cost > 0 and total_words > 0:
            cost_per_word = self.total_api_cost / total_words
            # 评分标准：每词$0.001为满分
            cost_efficiency_score = min(0.001 / cost_per_word * 25, 25) if cost_per_word > 0 else 0
        else:
            cost_efficiency_score = 25  # 如果没有成本，给满分
        
        efficiency_breakdown['cost_efficiency'] = cost_efficiency_score
        efficiency_score += cost_efficiency_score
        
        # 3. 内存效率 (0-25分)
        if self.peak_memory_usage > 0 and total_words > 0:
            memory_per_word = self.peak_memory_usage / total_words
            # 评分标准：每词0.01MB为满分
            memory_efficiency_score = min(0.01 / memory_per_word * 25, 25) if memory_per_word > 0 else 0
        else:
            memory_efficiency_score = 25  # 如果没有内存数据，给满分
        
        efficiency_breakdown['memory_efficiency'] = memory_efficiency_score
        efficiency_score += memory_efficiency_score
        
        # 4. Token效率 (0-25分)
        if self.total_tokens > 0 and total_words > 0:
            tokens_per_word = self.total_tokens / total_words
            # 评分标准：每词2个token为满分（中文）
            token_efficiency_score = min(2 / tokens_per_word * 25, 25) if tokens_per_word > 0 else 0
        else:
            token_efficiency_score = 25  # 如果没有token数据，给满分
        
        efficiency_breakdown['token_efficiency'] = token_efficiency_score
        efficiency_score += token_efficiency_score
        
        return {
            'overall_efficiency_score': efficiency_score,
            'efficiency_breakdown': efficiency_breakdown,
            'efficiency_metrics': {
                'words_per_second': total_words / total_time if total_time > 0 else 0,
                'cost_per_word': self.total_api_cost / total_words if total_words > 0 else 0,
                'memory_per_word': self.peak_memory_usage / total_words if total_words > 0 else 0,
                'tokens_per_word': self.total_tokens / total_words if total_words > 0 else 0
            }
        }
    
    def _assess_dialogue_quality(self, dialogue_data: Any) -> float:
        """评估对话质量"""
        dialogue_count = 0
        total_dialogue_length = 0
        
        if isinstance(dialogue_data, list):
            for item in dialogue_data:
                if isinstance(item, dict) and 'dialogue' in item:
                    dialogue_count += 1
                    total_dialogue_length += len(item['dialogue'])
                elif isinstance(item, list):
                    for sub_item in item:
                        if isinstance(sub_item, dict) and 'dialogue' in sub_item:
                            dialogue_count += 1
                            total_dialogue_length += len(sub_item['dialogue'])
        
        if dialogue_count > 0:
            avg_dialogue_length = total_dialogue_length / dialogue_count
            # 评分：理想对话长度20-50字符
            if 20 <= avg_dialogue_length <= 50:
                return 10
            elif 10 <= avg_dialogue_length <= 80:
                return 7
            else:
                return 5
        
        return 0
    
    def _generate_optimization_suggestions(self, quality_metrics: Dict, efficiency_metrics: Dict) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        quality_score = quality_metrics.get('overall_quality_score', 0)
        efficiency_score = efficiency_metrics.get('overall_efficiency_score', 0)
        quality_breakdown = quality_metrics.get('quality_breakdown', {})
        efficiency_breakdown = efficiency_metrics.get('efficiency_breakdown', {})
        
        # 质量方面的建议
        if quality_score < 60:
            if quality_breakdown.get('text_richness', 0) < 5:
                suggestions.append("建议增加文本的丰富度，使用更多样化的词汇和句式")
            
            if quality_breakdown.get('character_complexity', 0) < 5:
                suggestions.append("建议增强角色设定的复杂性和完整性")
            
            if quality_breakdown.get('narrative_structure', 0) < 5:
                suggestions.append("建议优化故事结构，平衡章节长度和内容分布")
        
        # 效率方面的建议
        if efficiency_score < 60:
            if efficiency_breakdown.get('time_efficiency', 0) < 15:
                suggestions.append("建议优化生成速度，可能需要升级硬件或优化算法")
            
            if efficiency_breakdown.get('cost_efficiency', 0) < 15:
                suggestions.append("建议优化API调用成本，考虑使用更经济的模型或减少不必要的调用")
            
            if efficiency_breakdown.get('memory_efficiency', 0) < 15:
                suggestions.append("建议优化内存使用，考虑分批处理或清理无用数据")
        
        # 权衡建议
        if quality_score > 80 and efficiency_score < 40:
            suggestions.append("质量很高但效率偏低，建议在保持质量的前提下优化性能")
        elif efficiency_score > 80 and quality_score < 40:
            suggestions.append("效率很高但质量偏低，建议适当牺牲一些速度来提升内容质量")
        elif quality_score > 70 and efficiency_score > 70:
            suggestions.append("质量和效率都很好，可以考虑进一步微调以达到最佳平衡")
        
        if not suggestions:
            suggestions.append("系统运行良好，建议持续监控并根据实际需求进行微调")
        
        return suggestions
        
    def analyze_text_features(self, story_data: List[Dict], dialogue_data: List[Dict] = None, 
                             characters_data: List[Dict] = None):
        """分析文本特征：字数、句子数等"""
        
        # 故事文本统计
        total_plot_text = ""
        chapter_stats = []
        
        for i, chapter in enumerate(story_data):
            plot = chapter.get('plot', '')
            title = chapter.get('title', f'第{i+1}章')
            
            # 章节级统计
            chapter_char_count = len(plot)
            chapter_word_count = len(re.findall(r'[\u4e00-\u9fff]', plot))  # 中文字数
            
            try:
                sentences = split_plot_into_sentences(plot)
                chapter_sentence_count = len(sentences)
            except:
                chapter_sentence_count = len(re.split(r'[。！？.!?]+', plot.strip()))
            
            chapter_stats.append({
                'chapter_id': chapter.get('chapter_id', f'chapter_{i+1}'),
                'title': title,
                'char_count': chapter_char_count,
                'word_count': chapter_word_count,
                'sentence_count': chapter_sentence_count
            })
            
            total_plot_text += plot
            
        # 总体统计
        total_char_count = len(total_plot_text)
        total_word_count = len(re.findall(r'[\u4e00-\u9fff]', total_plot_text))
        
        try:
            all_sentences = split_plot_into_sentences(total_plot_text)
            total_sentence_count = len(all_sentences)
        except:
            total_sentence_count = len(re.split(r'[。！？.!?]+', total_plot_text.strip()))
        
        # 对话统计（如果提供）
        dialogue_stats = {}
        if dialogue_data:
            dialogue_stats = self._analyze_dialogue_features(dialogue_data)
        
        # 角色特征分析（如果提供）
        character_analysis = {}
        if characters_data:
            character_analysis = self.analyze_character_complexity(characters_data)
        
        self.text_features = {
            'total_char_count': total_char_count,
            'total_word_count': total_word_count,
            'total_sentence_count': total_sentence_count,
            'chapter_count': len(story_data),
            'avg_chapter_length': total_char_count / len(story_data) if story_data else 0,
            'avg_sentence_length': total_char_count / total_sentence_count if total_sentence_count > 0 else 0,
            'chapter_details': chapter_stats,
            'dialogue_features': dialogue_stats,
            'character_features': character_analysis
        }
        
        return self.text_features
        
    def _analyze_dialogue_features(self, dialogue_data: List[Dict]) -> Dict:
        """分析对话特征"""
        total_dialogues = 0
        total_dialogue_chars = 0
        speakers = set()
        
        for chapter_dialogue in dialogue_data:
            if isinstance(chapter_dialogue, dict):
                dialogues = chapter_dialogue.get('dialogue', [])
                if isinstance(dialogues, list):
                    for dialogue in dialogues:
                        if isinstance(dialogue, dict):
                            total_dialogues += 1
                            content = dialogue.get('dialogue', '')
                            total_dialogue_chars += len(content)
                            speaker = dialogue.get('speaker', '')
                            if speaker:
                                speakers.add(speaker)
        
        return {
            'total_dialogue_count': total_dialogues,
            'total_dialogue_chars': total_dialogue_chars,
            'unique_speakers': len(speakers),
            'avg_dialogue_length': total_dialogue_chars / total_dialogues if total_dialogues > 0 else 0,
            'speakers_list': list(speakers)
        }
        
    def calculate_complexity_metrics(self) -> Dict:
        """计算复杂度指标"""
        if not self.text_features:
            return {}
            
        total_time = self.get_total_time()
        total_chars = self.text_features.get('total_char_count', 1)
        total_words = self.text_features.get('total_word_count', 1)
        chapter_count = self.text_features.get('chapter_count', 1)
        
        # 基本复杂度指标
        time_per_char = total_time / total_chars if total_chars > 0 else 0
        time_per_word = total_time / total_words if total_words > 0 else 0
        time_per_chapter = total_time / chapter_count if chapter_count > 0 else 0
        
        # 复杂度分析（假设不同的复杂度模型）
        # T(n) = a*n^b 的形式分析
        complexity_indicators = {}
        
        if total_chars > 0:
            # 线性复杂度指标: T(n)/n
            complexity_indicators['linear_indicator'] = total_time / total_chars
            
            # 对数线性复杂度: T(n)/(n*log(n))
            if total_chars > 1:
                import math
                complexity_indicators['n_log_n_indicator'] = total_time / (total_chars * math.log(total_chars))
            
            # 平方根复杂度: T(n)/sqrt(n)
            complexity_indicators['sqrt_n_indicator'] = total_time / (total_chars ** 0.5)
            
            # 二次复杂度: T(n)/n^2
            complexity_indicators['quadratic_indicator'] = total_time / (total_chars ** 2)
            
        return {
            'total_generation_time_seconds': total_time,
            'time_per_char': time_per_char,
            'time_per_word': time_per_word,
            'time_per_chapter': time_per_chapter,
            'complexity_indicators': complexity_indicators,
            'efficiency_metrics': {
                'chars_per_second': total_chars / total_time if total_time > 0 else 0,
                'words_per_second': total_words / total_time if total_time > 0 else 0,
                'chapters_per_minute': chapter_count * 60 / total_time if total_time > 0 else 0
            }
        }
        
    def generate_performance_report(self) -> Dict:
        """生成完整的性能分析报告"""
        # 停止内存监控
        if self.enable_memory_monitoring:
            self.stop_memory_monitoring()
            
        complexity_metrics = self.calculate_complexity_metrics()
        
        # 构建内存复杂度数据
        memory_complexity_data = {
            'peak_memory_usage_mb': self.peak_memory_usage,
            'memory_timeline': self.memory_timeline,
            'stage_memory_usage': {
                stage: usage for stage, usage in self.stage_memory_usage.items() 
                if stage.endswith('_increase') or stage.endswith('_peak')
            },
            'memory_per_character': 0.0  # 如果有角色数据会被更新
        }
        
        # 如果有角色特征数据，计算每角色内存开销
        if self.character_features:
            char_count = self.character_features.get('character_count', 1)
            if char_count > 0:
                memory_complexity_data['memory_per_character'] = self.peak_memory_usage / char_count
                memory_complexity_data['story_features'] = {
                    'character_count': char_count,
                    'character_description_total_length': self.character_features.get('character_descriptions_total_length', 0),
                    'character_complexity_score': self.character_features.get('character_complexity_score', 0)
                }
        
        # 简化版：只保存原始数据，质量分析留到后续离线处理
        raw_analysis = {
            'data_available_for_offline_analysis': True,
            'story_data_summary': {
                'chapters': len(self.raw_data.get('story_expansion_output', {}).get('sample', [])) if 'story_expansion_output' in self.raw_data else 0,
                'characters': len(self.raw_data.get('character_generation_output', {}).get('sample', [])) if 'character_generation_output' in self.raw_data else 0
            },
            'note': '详细质量分析请使用离线分析工具处理完整的性能报告JSON文件'
        }
        
        # 计算API响应时间统计
        api_response_stats = self._calculate_api_response_stats()
        
        # 计算缓存效率
        cache_efficiency = self.cache_usage['total_cache_hits'] / max(self.cache_usage['total_cache_attempts'], 1)
        
        report = {
            'metadata': {
                'task_name': self.task_name,
                'analysis_timestamp': datetime.datetime.now().isoformat(),
                'total_execution_time': self.get_total_time(),
                'total_api_cost': self.total_api_cost,
                'total_tokens': self.total_tokens,
                'peak_memory_usage_mb': self.peak_memory_usage
            },
            'experiment_config': self.experiment_config,
            'stage_performance': {
                'stage_times': self.stage_times,
                'stage_breakdown_percentage': self._calculate_stage_percentages()
            },
            'text_features': self.text_features,
            'complexity_analysis': complexity_metrics,
            'memory_complexity_data': memory_complexity_data,
            'offline_analysis_ready': raw_analysis,
            'api_cost_breakdown': {
                'total_cost': self.total_api_cost,
                'total_tokens': self.total_tokens,
                'cost_per_stage': self.token_consumption,
                'detailed_api_calls': self.api_costs,
                'response_time_stats': api_response_stats
            },
            'cache_performance': {
                'total_cache_attempts': self.cache_usage['total_cache_attempts'],
                'total_cache_hits': self.cache_usage['total_cache_hits'],
                'cache_efficiency': cache_efficiency,
                'cache_hits_by_stage': self.cache_usage['cache_hits']
            },
            'error_and_reliability': {
                'total_errors': len(self.error_log['error_details']),
                'api_failures': self.error_log['api_failures'],
                'parsing_errors': self.error_log['parsing_errors'],
                'retry_attempts': self.error_log['retry_attempts'],
                'error_details': self.error_log['error_details']
            },
            'performance_summary': self._generate_summary()
        }
        
        return report
        
    def _calculate_api_response_stats(self) -> Dict:
        """计算API响应时间统计"""
        if not self.api_response_times:
            return {}
        
        stats = {}
        all_response_times = []
        
        for stage, times in self.api_response_times.items():
            if times:
                stats[stage] = {
                    'avg_response_time': sum(times) / len(times),
                    'max_response_time': max(times),
                    'min_response_time': min(times),
                    'total_calls': len(times)
                }
                all_response_times.extend(times)
        
        if all_response_times:
            stats['overall'] = {
                'avg_response_time': sum(all_response_times) / len(all_response_times),
                'max_response_time': max(all_response_times),
                'min_response_time': min(all_response_times),
                'total_api_calls': len(all_response_times)
            }
        
        return stats
    
    def _calculate_stage_percentages(self) -> Dict[str, float]:
        """计算各阶段时间占比"""
        total = sum(self.stage_times.values())
        if total == 0:
            return {}
            
        return {
            stage: (time_val / total) * 100 
            for stage, time_val in self.stage_times.items()
        }
        
    def _generate_summary(self) -> Dict:
        """生成性能摘要"""
        total_time = self.get_total_time()
        
        # 找出最耗时的阶段
        slowest_stage = max(self.stage_times.items(), key=lambda x: x[1]) if self.stage_times else (None, 0)
        
        # 效率评级
        chars_per_sec = self.text_features.get('total_char_count', 0) / total_time if total_time > 0 else 0
        
        efficiency_rating = "未知"
        if chars_per_sec > 100:
            efficiency_rating = "极快"
        elif chars_per_sec > 50:
            efficiency_rating = "快速"
        elif chars_per_sec > 20:
            efficiency_rating = "正常"
        elif chars_per_sec > 10:
            efficiency_rating = "较慢"
        else:
            efficiency_rating = "慢"
            
        return {
            'total_time_seconds': total_time,
            'total_time_formatted': self._format_duration(total_time),
            'slowest_stage': slowest_stage[0] if slowest_stage[0] else "无数据",
            'slowest_stage_time': slowest_stage[1] if slowest_stage[0] else 0,
            'efficiency_rating': efficiency_rating,
            'throughput_chars_per_second': chars_per_sec,
            'estimated_complexity_class': self._estimate_complexity_class()
        }
        
    def _estimate_complexity_class(self) -> str:
        """估算时间复杂度类别"""
        if 'complexity_indicators' not in self.calculate_complexity_metrics():
            return "数据不足"
            
        indicators = self.calculate_complexity_metrics()['complexity_indicators']
        
        # 简单的启发式判断
        if 'linear_indicator' in indicators and 'sqrt_n_indicator' in indicators:
            linear_val = indicators['linear_indicator']
            sqrt_val = indicators['sqrt_n_indicator']
            
            if linear_val < sqrt_val * 0.1:
                return "接近线性 O(n)"
            elif sqrt_val > linear_val * 10:
                return "超线性，可能 O(n log n) 或更高"
            else:
                return "介于线性和超线性之间"
        
        return "需要更多数据分析"
        
    def _format_duration(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}分{secs:.1f}秒"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}小时{mins}分钟"
            
    def _serialize_data(self, data: Any) -> Any:
        """序列化数据用于存储"""
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, (list, dict)):
            try:
                # 只保存数据结构摘要，避免过大
                if isinstance(data, list):
                    return {
                        'type': 'list',
                        'length': len(data),
                        'sample': data[:2] if len(data) > 2 else data  # 只保存前两个样本
                    }
                elif isinstance(data, dict):
                    return {
                        'type': 'dict',
                        'keys': list(data.keys())[:10],  # 只保存前10个键
                        'size': len(data)
                    }
            except:
                return str(type(data))
        else:
            return str(type(data))
            
    def save_report(self, output_dir: str, filename: str = None):
        """保存性能分析报告"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{self.task_name}_{timestamp}.json"
            
        report = self.generate_performance_report()
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"性能分析报告已保存: {filepath}")
        return filepath


class PerformanceBenchmark:
    """性能基准测试和比较工具"""
    
    @staticmethod
    def load_reports(report_dir: str) -> List[Dict]:
        """加载多个性能报告进行比较"""
        reports = []
        for filename in os.listdir(report_dir):
            if filename.startswith("performance_report_") and filename.endswith(".json"):
                filepath = os.path.join(report_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    reports.append(report)
                except Exception as e:
                    print(f"无法加载报告 {filename}: {e}")
        return reports
        
    @staticmethod
    def compare_performance(reports: List[Dict]) -> Dict:
        """比较多个性能报告"""
        if len(reports) < 2:
            return {"error": "至少需要2个报告进行比较"}
            
        comparison = {
            'report_count': len(reports),
            'time_analysis': {},
            'efficiency_analysis': {},
            'complexity_trends': {}
        }
        
        # 提取时间数据
        times = [r['metadata']['total_execution_time'] for r in reports]
        chars = [r['text_features']['total_char_count'] for r in reports if 'text_features' in r]
        
        if times:
            comparison['time_analysis'] = {
                'avg_time': np.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'time_std': np.std(times),
                'time_trend': 'increasing' if times[-1] > times[0] else 'decreasing'
            }
        
        if chars and len(chars) == len(times):
            throughputs = [c/t for c, t in zip(chars, times) if t > 0]
            if throughputs:
                comparison['efficiency_analysis'] = {
                    'avg_throughput': np.mean(throughputs),
                    'throughput_trend': 'improving' if throughputs[-1] > throughputs[0] else 'declining',
                    'efficiency_variance': np.var(throughputs)
                }
        
        return comparison
        
    @staticmethod
    def generate_benchmark_report(reports: List[Dict], output_path: str):
        """生成基准测试报告"""
        comparison = PerformanceBenchmark.compare_performance(reports)
        
        benchmark_report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'benchmark_data': comparison,
            'detailed_reports': len(reports),
            'recommendations': PerformanceBenchmark._generate_recommendations(comparison)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(benchmark_report, f, ensure_ascii=False, indent=2)
            
        return benchmark_report
        
    @staticmethod
    def _generate_recommendations(comparison: Dict) -> List[str]:
        """基于分析结果生成优化建议"""
        recommendations = []
        
        if 'time_analysis' in comparison:
            time_data = comparison['time_analysis']
            if time_data.get('time_std', 0) > time_data.get('avg_time', 0) * 0.3:
                recommendations.append("时间波动较大，建议检查缓存策略和网络稳定性")
                
        if 'efficiency_analysis' in comparison:
            eff_data = comparison['efficiency_analysis']
            if eff_data.get('throughput_trend') == 'declining':
                recommendations.append("效率呈下降趋势，建议优化生成算法或硬件配置")
                
        if not recommendations:
            recommendations.append("性能表现稳定，可考虑进一步优化以提升速度")
            
        return recommendations
