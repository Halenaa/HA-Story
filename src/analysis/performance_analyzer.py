"""
Computational complexity analyzer
Used to collect and analyze performance data from story generation processes, including time complexity, text statistics, etc.
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
    """Performance analyzer: Monitor generation time, memory usage, API costs and text statistics"""
    
    def __init__(self, task_name: str = "default", enable_memory_monitoring: bool = True, experiment_config: Dict = None):
        self.task_name = task_name
        self.stage_times = {}
        self.stage_start_times = {}
        self.text_features = {}
        self.raw_data = {}
        self.total_start_time = None
        
        # Experiment configuration parameters
        self.experiment_config = experiment_config or {}
        
        # API response time statistics
        self.api_response_times = {}
        
        # Error and exception logging
        self.error_log = {
            'api_failures': 0,
            'parsing_errors': 0, 
            'retry_attempts': 0,
            'error_details': []
        }
        
        # Cache usage statistics
        self.cache_usage = {
            'cache_hits': {},
            'total_cache_hits': 0,
            'total_cache_attempts': 0
        }
        
        # Memory monitoring
        self.enable_memory_monitoring = enable_memory_monitoring
        self.memory_timeline = []
        self.stage_memory_usage = {}
        self.peak_memory_usage = 0
        self.memory_monitor_thread = None
        self.memory_monitoring_active = False
        self.process = psutil.Process(os.getpid())
        
        # API cost and Token tracking
        self.api_costs = {}
        self.token_consumption = {}
        self.total_api_cost = 0.0
        self.total_tokens = 0
        
        # Character complexity related
        self.character_features = {}
        
        # Get baseline memory usage
        if self.enable_memory_monitoring:
            self.baseline_memory = self._get_current_memory_usage()
        
    def start_total_timing(self):
        """Start total timing"""
        self.total_start_time = time.time()
        
        # Start memory monitoring
        if self.enable_memory_monitoring:
            self.start_memory_monitoring()
    
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage (MB)"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except:
            return 0.0
    
    def start_memory_monitoring(self):
        """Start memory monitoring thread"""
        if not self.enable_memory_monitoring or self.memory_monitoring_active:
            return
            
        self.memory_monitoring_active = True
        self.memory_monitor_thread = threading.Thread(target=self._memory_monitor_loop, daemon=True)
        self.memory_monitor_thread.start()
        print("Memory monitoring started")
    
    def stop_memory_monitoring(self):
        """Stop memory monitoring"""
        if self.memory_monitoring_active:
            self.memory_monitoring_active = False
            if self.memory_monitor_thread and self.memory_monitor_thread.is_alive():
                self.memory_monitor_thread.join(timeout=1)
            print("Memory monitoring stopped")
    
    def _memory_monitor_loop(self):
        """Memory monitoring loop"""
        while self.memory_monitoring_active:
            try:
                current_memory = self._get_current_memory_usage()
                timestamp = time.time() - self.total_start_time if self.total_start_time else 0
                
                self.memory_timeline.append({
                    'timestamp': timestamp,
                    'memory_mb': current_memory
                })
                
                # Update peak memory
                if current_memory > self.peak_memory_usage:
                    self.peak_memory_usage = current_memory
                
                time.sleep(0.5)  # Monitor every 0.5 seconds
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                break
        
    def start_stage(self, stage_name: str, input_data: Any = None):
        """Start timing for a generation stage"""
        self.stage_start_times[stage_name] = time.time()
        self.raw_data[f"{stage_name}_input"] = self._serialize_data(input_data)
        
        # Record memory usage at stage start
        if self.enable_memory_monitoring:
            current_memory = self._get_current_memory_usage()
            self.stage_memory_usage[f"{stage_name}_start"] = current_memory
        
    def end_stage(self, stage_name: str, output_data: Any = None):
        """End timing for a generation stage"""
        if stage_name not in self.stage_start_times:
            print(f"Warning: {stage_name} stage timing not started")
            return 0
            
        duration = time.time() - self.stage_start_times[stage_name]
        self.stage_times[stage_name] = duration
        self.raw_data[f"{stage_name}_output"] = self._serialize_data(output_data)
        
        # Record memory usage and growth at stage end
        if self.enable_memory_monitoring:
            current_memory = self._get_current_memory_usage()
            start_memory = self.stage_memory_usage.get(f"{stage_name}_start", 0)
            self.stage_memory_usage[f"{stage_name}_end"] = current_memory
            self.stage_memory_usage[f"{stage_name}_increase"] = current_memory - start_memory
        
        print(f"{stage_name} duration: {duration:.3f}s")
        return duration
        
    def get_total_time(self) -> float:
        """Get total execution time"""
        if self.total_start_time is None:
            return sum(self.stage_times.values())
        return time.time() - self.total_start_time
    
    def add_api_cost(self, stage_name: str, model: str, input_tokens: int, output_tokens: int, 
                     cost: float, api_call_type: str = "completion", response_time: float = 0.0):
        """Record API call cost and token consumption"""
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
        
        # Record API response time
        if response_time > 0:
            if stage_name not in self.api_response_times:
                self.api_response_times[stage_name] = []
            self.api_response_times[stage_name].append(response_time)
        
        # Update token consumption statistics
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
        
        print(f"{stage_name} API call: {model}, Tokens: {input_tokens + output_tokens}, Cost: ${cost:.4f}")
    
    def record_cache_usage(self, stage_name: str, cache_hit: bool, cache_key: str = None):
        """Record cache usage"""
        self.cache_usage['total_cache_attempts'] += 1
        
        if cache_hit:
            self.cache_usage['total_cache_hits'] += 1
            if stage_name not in self.cache_usage['cache_hits']:
                self.cache_usage['cache_hits'][stage_name] = 0
            self.cache_usage['cache_hits'][stage_name] += 1
            
        print(f"{stage_name} cache {'hit' if cache_hit else 'miss'}: {cache_key or 'default'}")
    
    def record_error(self, stage_name: str, error_type: str, error_message: str, resolved: bool = False):
        """Record errors and exceptions"""
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
        
        print(f"{stage_name} error log: {error_type} - {error_message}")
    
    def calculate_memory_per_character(self, characters_data: List[Dict]) -> Dict:
        """Calculate memory overhead per character"""
        if not self.enable_memory_monitoring or not characters_data:
            return {}
        
        # Analyze character complexity
        character_features = self.analyze_character_complexity(characters_data)
        
        # Calculate memory-related metrics
        memory_metrics = {
            'total_characters': len(characters_data),
            'peak_memory_per_character': self.peak_memory_usage / len(characters_data) if characters_data else 0,
            'character_complexity_features': character_features
        }
        
        # If there is memory growth data for character generation stage
        char_gen_increase = self.stage_memory_usage.get('character_generation_increase', 0)
        if char_gen_increase > 0:
            memory_metrics['memory_per_character_generation'] = char_gen_increase / len(characters_data)
        
        return memory_metrics
    
    def analyze_character_complexity(self, characters_data: List[Dict]) -> Dict:
        """Analyze character complexity features"""
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
            # Calculate total character description length
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
            
            # Simple complexity score (based on description length and structured information)
            complexity_score = (
                len(char.get('traits', '')) * 0.3 +
                len(char.get('background', '')) * 0.4 +
                len(char.get('motivation', '')) * 0.3
            )
            character_features['character_complexity_scores'].append(complexity_score)
        
        character_features['avg_description_length'] = (
            character_features['total_description_length'] / len(characters_data)
        )
        
        # Calculate total character complexity score
        character_features['character_complexity_score'] = sum(character_features['character_complexity_scores'])
        
        self.character_features = character_features
        return character_features
    
    def calculate_quality_efficiency_tradeoff(self, story_data: Any = None, dialogue_data: Any = None) -> Dict:
        """
        Calculate quality-efficiency tradeoff metrics
        
        Quality metrics include:
        - Text length and richness
        - Character consistency
        - Narrative coherence
        - Dialogue quality
        
        Efficiency metrics include:
        - Generation speed
        - API cost efficiency
        - Memory usage efficiency
        """
        quality_metrics = self._calculate_quality_metrics(story_data, dialogue_data)
        efficiency_metrics = self._calculate_efficiency_metrics()
        
        # Calculate quality-efficiency balance score
        quality_score = quality_metrics.get('overall_quality_score', 0)
        efficiency_score = efficiency_metrics.get('overall_efficiency_score', 0)
        
        # Tradeoff analysis
        tradeoff_analysis = {
            'quality_metrics': quality_metrics,
            'efficiency_metrics': efficiency_metrics,
            'balance_score': (quality_score + efficiency_score) / 2,
            'quality_efficiency_ratio': quality_score / efficiency_score if efficiency_score > 0 else 0,
            'optimization_suggestions': self._generate_optimization_suggestions(quality_metrics, efficiency_metrics)
        }
        
        return tradeoff_analysis
    
    def _calculate_quality_metrics(self, story_data: Any = None, dialogue_data: Any = None) -> Dict:
        """Calculate quality metrics"""
        quality_score = 0
        quality_breakdown = {}
        
        # 1. Text richness score (0-10 points)
        total_words = self.text_features.get('total_word_count', 0)
        total_chars = self.text_features.get('total_char_count', 0)
        sentence_count = self.text_features.get('sentence_count', 0)
        
        if total_words > 0:
            # Average sentence length
            avg_sentence_length = total_words / sentence_count if sentence_count > 0 else 0
            richness_score = min(avg_sentence_length / 15, 5)  # Ideal sentence length around 15 words
            
            # Vocabulary diversity (simple estimation)
            diversity_score = min(total_chars / total_words / 3, 5) if total_words > 0 else 0  # Average Chinese character length
            
            text_quality_score = richness_score + diversity_score
        else:
            text_quality_score = 0
        
        quality_breakdown['text_richness'] = text_quality_score
        quality_score += text_quality_score
        
        # 2. Character complexity score (0-10 points)
        char_complexity = self.character_features.get('character_complexity_score', 0)
        char_quality_score = min(char_complexity / 100, 10)  # Normalize to 0-10 points
        quality_breakdown['character_complexity'] = char_quality_score
        quality_score += char_quality_score
        
        # 3. Structural integrity score (0-10 points)
        chapter_count = self.text_features.get('chapter_count', 0)
        if chapter_count > 0:
            # Chapter balance
            avg_chapter_length = total_words / chapter_count if chapter_count > 0 else 0
            structure_score = min(avg_chapter_length / 500, 5)  # Ideal chapter length around 500 words
            
            # Chapter count reasonableness
            count_score = 5 if 3 <= chapter_count <= 12 else max(0, 5 - abs(chapter_count - 7))
            
            structure_quality_score = structure_score + count_score
        else:
            structure_quality_score = 0
        
        quality_breakdown['narrative_structure'] = structure_quality_score
        quality_score += structure_quality_score
        
        # 4. If dialogue data available, evaluate dialogue quality (0-10 points)
        if dialogue_data:
            dialogue_quality_score = self._assess_dialogue_quality(dialogue_data)
            quality_breakdown['dialogue_quality'] = dialogue_quality_score
            quality_score += dialogue_quality_score
        
        # Calculate total quality score (0-100 points)
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
        """Calculate efficiency metrics"""
        total_time = self.get_total_time()
        total_words = self.text_features.get('total_word_count', 0)
        total_chars = self.text_features.get('total_char_count', 0)
        
        efficiency_breakdown = {}
        efficiency_score = 0
        
        # 1. Time efficiency (0-25 points)
        if total_time > 0 and total_words > 0:
            words_per_second = total_words / total_time
            # Scoring standard: 5 chars/sec for full score
            time_efficiency_score = min(words_per_second / 5 * 25, 25)
        else:
            time_efficiency_score = 0
        
        efficiency_breakdown['time_efficiency'] = time_efficiency_score
        efficiency_score += time_efficiency_score
        
        # 2. Cost efficiency (0-25 points)
        if self.total_api_cost > 0 and total_words > 0:
            cost_per_word = self.total_api_cost / total_words
            # Scoring standard: $0.001 per word for full score
            cost_efficiency_score = min(0.001 / cost_per_word * 25, 25) if cost_per_word > 0 else 0
        else:
            cost_efficiency_score = 25  # If no cost, give full score
        
        efficiency_breakdown['cost_efficiency'] = cost_efficiency_score
        efficiency_score += cost_efficiency_score
        
        # 3. Memory efficiency (0-25 points)
        if self.peak_memory_usage > 0 and total_words > 0:
            memory_per_word = self.peak_memory_usage / total_words
            # Scoring standard: 0.01MB per word for full score
            memory_efficiency_score = min(0.01 / memory_per_word * 25, 25) if memory_per_word > 0 else 0
        else:
            memory_efficiency_score = 25  # If no memory data, give full score
        
        efficiency_breakdown['memory_efficiency'] = memory_efficiency_score
        efficiency_score += memory_efficiency_score
        
        # 4. Token efficiency (0-25 points)
        if self.total_tokens > 0 and total_words > 0:
            tokens_per_word = self.total_tokens / total_words
            # Scoring standard: 2 tokens per word for full score (Chinese)
            token_efficiency_score = min(2 / tokens_per_word * 25, 25) if tokens_per_word > 0 else 0
        else:
            token_efficiency_score = 25  # If no token data, give full score
        
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
        """Evaluate dialogue quality"""
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
            # Scoring: ideal dialogue length 20-50 characters
            if 20 <= avg_dialogue_length <= 50:
                return 10
            elif 10 <= avg_dialogue_length <= 80:
                return 7
            else:
                return 5
        
        return 0
    
    def _generate_optimization_suggestions(self, quality_metrics: Dict, efficiency_metrics: Dict) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        quality_score = quality_metrics.get('overall_quality_score', 0)
        efficiency_score = efficiency_metrics.get('overall_efficiency_score', 0)
        quality_breakdown = quality_metrics.get('quality_breakdown', {})
        efficiency_breakdown = efficiency_metrics.get('efficiency_breakdown', {})
        
        # Quality-related suggestions
        if quality_score < 60:
            if quality_breakdown.get('text_richness', 0) < 5:
                suggestions.append("Recommend increasing text richness, using more diverse vocabulary and sentence patterns")
            
            if quality_breakdown.get('character_complexity', 0) < 5:
                suggestions.append("Recommend enhancing character setting complexity and completeness")
            
            if quality_breakdown.get('narrative_structure', 0) < 5:
                suggestions.append("Recommend optimizing story structure, balancing chapter length and content distribution")
        
        # Efficiency-related suggestions
        if efficiency_score < 60:
            if efficiency_breakdown.get('time_efficiency', 0) < 15:
                suggestions.append("Recommend optimizing generation speed, may need hardware upgrade or algorithm optimization")
            
            if efficiency_breakdown.get('cost_efficiency', 0) < 15:
                suggestions.append("Recommend optimizing API call costs, consider using more economical models or reducing unnecessary calls")
            
            if efficiency_breakdown.get('memory_efficiency', 0) < 15:
                suggestions.append("Recommend optimizing memory usage, consider batch processing or cleaning unused data")
        
        # Tradeoff suggestions
        if quality_score > 80 and efficiency_score < 40:
            suggestions.append("High quality but low efficiency, recommend optimizing performance while maintaining quality")
        elif efficiency_score > 80 and quality_score < 40:
            suggestions.append("High efficiency but low quality, recommend sacrificing some speed to improve content quality")
        elif quality_score > 70 and efficiency_score > 70:
            suggestions.append("Both quality and efficiency are good, consider further fine-tuning to achieve optimal balance")
        
        if not suggestions:
            suggestions.append("System running well, recommend continuous monitoring and fine-tuning based on actual needs")
        
        return suggestions
        
    def analyze_text_features(self, story_data: List[Dict], dialogue_data: List[Dict] = None, 
                             characters_data: List[Dict] = None):
        """Analyze text features: word count, sentence count, etc."""
        
        # Story text statistics
        total_plot_text = ""
        chapter_stats = []
        
        for i, chapter in enumerate(story_data):
            plot = chapter.get('plot', '')
            title = chapter.get('title', f'Chapter {i+1}')
            
            # Chapter-level statistics
            chapter_char_count = len(plot)
            # Smart word counting for mixed language text
            chapter_chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', plot))
            chapter_english_words = len(re.findall(r'\b[a-zA-Z]+\b', plot))
            chapter_word_count = chapter_chinese_chars + chapter_english_words  # Chinese character count
            
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
            
        # Overall statistics
        total_char_count = len(total_plot_text)
        
        # Smart word counting for mixed language text
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', total_plot_text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', total_plot_text))
        # For mixed text: count Chinese characters + English words
        total_word_count = chinese_chars + english_words
        
        try:
            all_sentences = split_plot_into_sentences(total_plot_text)
            total_sentence_count = len(all_sentences)
        except:
            total_sentence_count = len(re.split(r'[。！？.!?]+', total_plot_text.strip()))
        
        # Dialogue statistics (if provided)
        dialogue_stats = {}
        if dialogue_data:
            dialogue_stats = self._analyze_dialogue_features(dialogue_data)
        
        # Character feature analysis (if provided)
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
        """Analyze dialogue features"""
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
        """Calculate complexity metrics"""
        if not self.text_features:
            return {}
            
        total_time = self.get_total_time()
        total_chars = self.text_features.get('total_char_count', 1)
        total_words = self.text_features.get('total_word_count', 1)
        chapter_count = self.text_features.get('chapter_count', 1)
        
        # Basic complexity metrics
        time_per_char = total_time / total_chars if total_chars > 0 else 0
        time_per_word = total_time / total_words if total_words > 0 else 0
        time_per_chapter = total_time / chapter_count if chapter_count > 0 else 0
        
        # Complexity analysis (assuming different complexity models)
        # Analysis in T(n) = a*n^b form
        complexity_indicators = {}
        
        if total_chars > 0:
            # Linear complexity indicator: T(n)/n
            complexity_indicators['linear_indicator'] = total_time / total_chars
            
            # N-log-n complexity: T(n)/(n*log(n))
            if total_chars > 1:
                import math
                complexity_indicators['n_log_n_indicator'] = total_time / (total_chars * math.log(total_chars))
            
            # Square root complexity: T(n)/sqrt(n)
            complexity_indicators['sqrt_n_indicator'] = total_time / (total_chars ** 0.5)
            
            # Quadratic complexity: T(n)/n^2
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
        """Generate complete performance analysis report"""
        # Stop memory monitoring
        if self.enable_memory_monitoring:
            self.stop_memory_monitoring()
            
        complexity_metrics = self.calculate_complexity_metrics()
        
        # Build memory complexity data
        memory_complexity_data = {
            'peak_memory_usage_mb': self.peak_memory_usage,
            'memory_timeline': self.memory_timeline,
            'stage_memory_usage': {
                stage: usage for stage, usage in self.stage_memory_usage.items() 
                if stage.endswith('_increase') or stage.endswith('_peak')
            },
            'memory_per_character': 0.0  # Will be updated if character data is available
        }
        
        # If character feature data available, calculate memory overhead per character
        if self.character_features:
            char_count = self.character_features.get('character_count', 1)
            if char_count > 0:
                memory_complexity_data['memory_per_character'] = self.peak_memory_usage / char_count
                memory_complexity_data['story_features'] = {
                    'character_count': char_count,
                    'character_description_total_length': self.character_features.get('character_descriptions_total_length', 0),
                    'character_complexity_score': self.character_features.get('character_complexity_score', 0)
                }
        
        # Simplified version: only save raw data, quality analysis for offline processing
        raw_analysis = {
            'data_available_for_offline_analysis': True,
            'story_data_summary': {
                'chapters': len(self.raw_data.get('story_expansion_output', {}).get('sample', [])) if 'story_expansion_output' in self.raw_data else 0,
                'characters': len(self.raw_data.get('character_generation_output', {}).get('sample', [])) if 'character_generation_output' in self.raw_data else 0
            },
            'note': 'For detailed quality analysis, please use offline analysis tools to process the complete performance report JSON file'
        }
        
        # Calculate API response time statistics
        api_response_stats = self._calculate_api_response_stats()
        
        # Calculate cache efficiency
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
        """Calculate API response time statistics"""
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
        """Calculate stage time percentages"""
        total = sum(self.stage_times.values())
        if total == 0:
            return {}
            
        return {
            stage: (time_val / total) * 100 
            for stage, time_val in self.stage_times.items()
        }
        
    def _generate_summary(self) -> Dict:
        """Generate performance summary"""
        total_time = self.get_total_time()
        
        # Find most time-consuming stage
        slowest_stage = max(self.stage_times.items(), key=lambda x: x[1]) if self.stage_times else (None, 0)
        
        # Efficiency rating
        chars_per_sec = self.text_features.get('total_char_count', 0) / total_time if total_time > 0 else 0
        
        efficiency_rating = "Unknown"
        if chars_per_sec > 100:
            efficiency_rating = "Very fast"
        elif chars_per_sec > 50:
            efficiency_rating = "Fast"
        elif chars_per_sec > 20:
            efficiency_rating = "Normal"
        elif chars_per_sec > 10:
            efficiency_rating = "Slow"
        else:
            efficiency_rating = "Very slow"
            
        return {
            'total_time_seconds': total_time,
            'total_time_formatted': self._format_duration(total_time),
            'slowest_stage': slowest_stage[0] if slowest_stage[0] else "No data",
            'slowest_stage_time': slowest_stage[1] if slowest_stage[0] else 0,
            'efficiency_rating': efficiency_rating,
            'throughput_chars_per_second': chars_per_sec,
            'estimated_complexity_class': self._estimate_complexity_class()
        }
        
    def _estimate_complexity_class(self) -> str:
        """Estimate time complexity class using correct mathematical analysis"""
        metrics = self.calculate_complexity_metrics()
        if 'complexity_indicators' not in metrics:
            return "Insufficient data"
            
        indicators = metrics['complexity_indicators']
        total_chars = self.text_features.get('total_char_count', 1)
        total_time = self.get_total_time()
        
        if total_chars <= 1 or total_time <= 0:
            return "Insufficient data for complexity analysis"
            
        # For small data sizes, complexity analysis is unreliable
        if total_chars < 100:
            return "Data size too small for reliable complexity analysis"
            
        # Model-based complexity estimation using relative efficiency
        import math
        
        # Expected time for different complexity models (normalized baselines)
        expected_linear = total_chars * 0.001      # 1ms per character
        expected_nlogn = total_chars * math.log(total_chars) * 0.0001  # 0.1ms per char*log(n)
        expected_quadratic = (total_chars ** 2) * 0.000001   # 1μs per char²
        
        # Calculate relative deviations from expected models
        linear_error = abs(total_time - expected_linear) / expected_linear if expected_linear > 0 else float('inf')
        nlogn_error = abs(total_time - expected_nlogn) / expected_nlogn if expected_nlogn > 0 else float('inf')
        quadratic_error = abs(total_time - expected_quadratic) / expected_quadratic if expected_quadratic > 0 else float('inf')
        
        # Find best-fit model (smallest relative error)
        complexity_models = [
            (linear_error, "Linear O(n)"),
            (nlogn_error, "N-log-N O(n log n)"), 
            (quadratic_error, "Quadratic O(n²)")
        ]
        
        best_fit = min(complexity_models, key=lambda x: x[0])
        best_error, complexity_class = best_fit
        
        # Add confidence qualifier based on relative error
        if best_error > 2.0:
            confidence = "low confidence - limited data"
        elif best_error > 0.5:
            confidence = "moderate confidence"
        else:
            confidence = "high confidence"
            
        return f"{complexity_class} ({confidence})"
        
    def _format_duration(self, seconds: float) -> str:
        """Format time display"""
        if seconds < 60:
            return f"{seconds:.2f} seconds"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"
            
    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for storage"""
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, (list, dict)):
            try:
                # Only save data structure summary to avoid being too large
                if isinstance(data, list):
                    return {
                        'type': 'list',
                        'length': len(data),
                        'sample': data[:2] if len(data) > 2 else data  # Only save first two samples
                    }
                elif isinstance(data, dict):
                    return {
                        'type': 'dict',
                        'keys': list(data.keys())[:10],  # Only save first 10 keys
                        'size': len(data)
                    }
            except:
                return str(type(data))
        else:
            return str(type(data))
            
    def save_report(self, output_dir: str, filename: str = None):
        """Save performance analysis report"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{self.task_name}_{timestamp}.json"
            
        report = self.generate_performance_report()
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"Performance analysis report saved: {filepath}")
        return filepath


class PerformanceBenchmark:
    """Performance benchmark testing and comparison tools"""
    
    @staticmethod
    def load_reports(report_dir: str) -> List[Dict]:
        """Load multiple performance reports for comparison"""
        reports = []
        for filename in os.listdir(report_dir):
            if filename.startswith("performance_report_") and filename.endswith(".json"):
                filepath = os.path.join(report_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    reports.append(report)
                except Exception as e:
                    print(f"Cannot load report {filename}: {e}")
        return reports
        
    @staticmethod
    def compare_performance(reports: List[Dict]) -> Dict:
        """Compare multiple performance reports"""
        if len(reports) < 2:
            return {"error": "At least 2 reports needed for comparison"}
            
        comparison = {
            'report_count': len(reports),
            'time_analysis': {},
            'efficiency_analysis': {},
            'complexity_trends': {}
        }
        
        # Extract time data
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
        """Generate benchmark report"""
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
        """Generate optimization suggestions based on analysis results"""
        recommendations = []
        
        if 'time_analysis' in comparison:
            time_data = comparison['time_analysis']
            if time_data.get('time_std', 0) > time_data.get('avg_time', 0) * 0.3:
                recommendations.append("Large time fluctuations, recommend checking cache strategy and network stability")
                
        if 'efficiency_analysis' in comparison:
            eff_data = comparison['efficiency_analysis']
            if eff_data.get('throughput_trend') == 'declining':
                recommendations.append("Efficiency shows declining trend, recommend optimizing generation algorithms or hardware configuration")
                
        if not recommendations:
            recommendations.append("Performance is stable, consider further optimization to improve speed")
            
        return recommendations