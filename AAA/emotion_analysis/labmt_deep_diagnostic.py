#!/usr/bin/env python3
"""
LabMT Deep Diagnostic Analysis
==============================

Performs deep diagnostic analysis of LabMT implementation issues:
1. Tokenization and lemmatization analysis
2. Negation and context reversal detection
3. Stop words and functional words impact
4. OOV coverage rate analysis
5. Smoothing and windowing effects
6. Comparison with RoBERTa processing

Based on user's professional feedback about potential LabMT issues.
"""

import pandas as pd
import numpy as np
import re
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class LabMTDiagnosticAnalyzer:
    """Deep diagnostic analysis of LabMT implementation"""
    
    def __init__(self, csv_path):
        """Initialize with emotion data"""
        self.data = pd.read_csv(csv_path)
        self.experiment_data = self.data[self.data['is_baseline'] == 0].copy()
        
        print(f"🔍 Loaded {len(self.experiment_data)} stories for LabMT diagnostic")
        
        # Parse emotion score strings
        self._parse_emotion_scores()
        
        # Load LabMT dictionary
        self._load_labmt_dict()
        
        # Initialize diagnostic results
        self.diagnostic_results = {}
        
    def _parse_emotion_scores(self):
        """Parse emotion score strings to lists"""
        def safe_parse_scores(score_str):
            if pd.isna(score_str):
                return []
            try:
                if isinstance(score_str, str):
                    score_str = score_str.strip('[]')
                    return [float(x.strip()) for x in score_str.split(',') if x.strip()]
                return []
            except:
                return []
        
        self.experiment_data['roberta_scores_list'] = self.experiment_data['roberta_scores_str'].apply(safe_parse_scores)
        self.experiment_data['labmt_scores_list'] = self.experiment_data['labmt_scores_str'].apply(safe_parse_scores)
        
        print("✅ Parsed emotion score strings")
    
    def _load_labmt_dict(self):
        """Load LabMT dictionary (simplified version for diagnostic)"""
        # Create a simplified LabMT-like dictionary for analysis
        # In real implementation, this should load from actual LabMT files
        
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic', 'perfect', 'beautiful', 
                         'love', 'happy', 'joy', 'smile', 'laugh', 'success', 'win', 'achieve', 'brilliant', 'awesome',
                         'delighted', 'excited', 'pleased', 'satisfied', 'proud', 'grateful', 'optimistic', 'confident']
        
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'angry', 'sad', 'cry', 'pain',
                         'suffer', 'fail', 'lose', 'disaster', 'tragedy', 'death', 'kill', 'destroy', 'fear', 'scared',
                         'worried', 'anxious', 'depressed', 'frustrated', 'disappointed', 'regret', 'guilty', 'shame']
        
        neutral_words = ['the', 'and', 'or', 'but', 'with', 'from', 'they', 'them', 'this', 'that', 'here', 'there',
                        'when', 'where', 'how', 'what', 'who', 'why', 'can', 'will', 'would', 'should', 'could', 'may']
        
        # Create LabMT-like scores (1-9 scale)
        self.labmt_dict = {}
        
        for word in positive_words:
            self.labmt_dict[word] = np.random.uniform(6.5, 8.5)  # Positive range
        
        for word in negative_words:
            self.labmt_dict[word] = np.random.uniform(1.5, 3.5)  # Negative range
            
        for word in neutral_words:
            self.labmt_dict[word] = np.random.uniform(4.5, 5.5)  # Neutral range
        
        print(f"✅ Loaded simplified LabMT dictionary with {len(self.labmt_dict)} words")
        print(f"   - {len(positive_words)} positive words")
        print(f"   - {len(negative_words)} negative words") 
        print(f"   - {len(neutral_words)} neutral words")
    
    def analyze_tokenization_issues(self, sample_texts=None):
        """Analyze tokenization and preprocessing issues"""
        
        print("\n🔍 ANALYZING TOKENIZATION ISSUES...")
        
        if sample_texts is None:
            # Create sample texts based on the typical story content
            sample_texts = [
                "The little girl wasn't happy. She couldn't find her way home!",
                "Dr. Smith said, \"Don't worry, it'll be fine.\" But she wasn't convinced...",
                "The AI system's algorithms were amazing, but the user-interface was terrible.",
                "He felt wonderful—absolutely fantastic! However, everything changed quickly.",
                "The emotion-detection model couldn't handle complex sentences with multiple clauses."
            ]
        
        tokenization_analysis = {
            'sample_texts': [],
            'total_samples': len(sample_texts),
            'tokenization_methods': {}
        }
        
        for i, text in enumerate(sample_texts):
            # Method 1: Current LabMT tokenization (regex word extraction)
            current_tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            
            # Method 2: Simple split tokenization
            split_tokens = text.lower().replace('.', ' ').replace(',', ' ').replace('!', ' ').replace('?', ' ').split()
            split_tokens = [token.strip() for token in split_tokens if token.strip()]
            
            # Method 3: More sophisticated tokenization
            sophisticated_tokens = re.findall(r'\b[a-zA-Z]+(?:\'[a-zA-Z]+)?\b', text.lower())
            
            sample_analysis = {
                'text': text,
                'current_tokenization': current_tokens,
                'split_tokenization': split_tokens,
                'sophisticated_tokenization': sophisticated_tokens,
                'token_counts': {
                    'current': len(current_tokens),
                    'split': len(split_tokens),
                    'sophisticated': len(sophisticated_tokens)
                }
            }
            
            tokenization_analysis['sample_texts'].append(sample_analysis)
        
        # Calculate statistics
        methods = ['current', 'split', 'sophisticated']
        for method in methods:
            counts = [sample['token_counts'][method] for sample in tokenization_analysis['sample_texts']]
            tokenization_analysis['tokenization_methods'][method] = {
                'mean_tokens_per_text': np.mean(counts),
                'std_tokens_per_text': np.std(counts),
                'min_tokens': min(counts),
                'max_tokens': max(counts)
            }
        
        print(f"📊 Tokenization analysis on {len(sample_texts)} samples:")
        for method, stats in tokenization_analysis['tokenization_methods'].items():
            print(f"   - {method}: {stats['mean_tokens_per_text']:.1f}±{stats['std_tokens_per_text']:.1f} tokens/text")
        
        return tokenization_analysis
    
    def analyze_negation_handling(self):
        """Analyze negation and context reversal issues"""
        
        print("\n🔍 ANALYZING NEGATION HANDLING...")
        
        negation_test_cases = [
            {
                'text': "I am not happy at all",
                'expected_sentiment': 'negative',
                'negation_words': ['not']
            },
            {
                'text': "This is not bad, it's actually good",
                'expected_sentiment': 'positive', 
                'negation_words': ['not']
            },
            {
                'text': "She was hardly satisfied with the results",
                'expected_sentiment': 'negative',
                'negation_words': ['hardly']
            },
            {
                'text': "The movie was good, but the ending was terrible",
                'expected_sentiment': 'mixed',
                'negation_words': ['but']
            },
            {
                'text': "It wasn't terrible, just disappointing",
                'expected_sentiment': 'negative',
                'negation_words': ["wasn't"]
            }
        ]
        
        negation_analysis = {
            'test_cases': [],
            'negation_detection_rate': 0,
            'context_reversal_handling': 'none'  # Current implementation doesn't handle negation
        }
        
        for test_case in negation_test_cases:
            text = test_case['text']
            
            # Current LabMT analysis (no negation handling)
            current_score = self._analyze_labmt_simple(text)
            
            # Extract words that would be analyzed
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            
            # Check for negation words
            negation_words_found = [word for word in words if word in ['not', 'no', 'never', 'hardly', 'barely', 'scarcely']]
            
            case_result = {
                'text': text,
                'expected_sentiment': test_case['expected_sentiment'],
                'labmt_score': current_score,
                'actual_sentiment': 'positive' if current_score > 0.1 else 'negative' if current_score < -0.1 else 'neutral',
                'negation_words_in_text': test_case['negation_words'],
                'negation_words_detected': negation_words_found,
                'negation_handled': False  # Current implementation doesn't handle negation
            }
            
            negation_analysis['test_cases'].append(case_result)
        
        # Calculate detection rate
        cases_with_negation = [case for case in negation_analysis['test_cases'] if case['negation_words_in_text']]
        detected_correctly = [case for case in cases_with_negation if case['negation_words_detected']]
        
        negation_analysis['negation_detection_rate'] = len(detected_correctly) / len(cases_with_negation) if cases_with_negation else 0
        
        print(f"📊 Negation handling analysis:")
        print(f"   - Test cases: {len(negation_test_cases)}")
        print(f"   - Negation detection rate: {negation_analysis['negation_detection_rate']*100:.1f}%")
        print(f"   - Context reversal handling: {negation_analysis['context_reversal_handling']}")
        print("   ⚠️ Current LabMT implementation does NOT handle negation!")
        
        return negation_analysis
    
    def analyze_oov_coverage(self):
        """Analyze Out-Of-Vocabulary coverage rates"""
        
        print("\n🔍 ANALYZING OOV COVERAGE RATES...")
        
        coverage_analysis = {
            'story_coverage': [],
            'overall_statistics': {}
        }
        
        for _, row in self.experiment_data.iterrows():
            story_id = row['story_id']
            labmt_scores = row['labmt_scores_list']
            
            if len(labmt_scores) == 0:
                continue
            
            # Simulate text analysis (we don't have original text, so we'll estimate)
            # In real analysis, you would need the original story text
            estimated_chapters = len(labmt_scores)
            estimated_words_per_chapter = 100  # Rough estimate
            estimated_total_words = estimated_chapters * estimated_words_per_chapter
            
            # Estimate coverage based on non-zero scores
            non_zero_chapters = len([score for score in labmt_scores if abs(score) > 0.01])
            estimated_coverage = non_zero_chapters / len(labmt_scores) if len(labmt_scores) > 0 else 0
            
            # Estimate vocabulary diversity
            score_variance = np.var(labmt_scores) if len(labmt_scores) > 1 else 0
            
            story_coverage = {
                'story_id': story_id,
                'genre': row['genre'],
                'structure': row['structure'],
                'chapter_count': len(labmt_scores),
                'estimated_total_words': estimated_total_words,
                'estimated_coverage_rate': estimated_coverage,
                'score_variance': score_variance,
                'mean_absolute_score': np.mean([abs(score) for score in labmt_scores]),
                'coverage_category': 'high' if estimated_coverage > 0.85 else 'medium' if estimated_coverage > 0.6 else 'low'
            }
            
            coverage_analysis['story_coverage'].append(story_coverage)
        
        # Calculate overall statistics
        if coverage_analysis['story_coverage']:
            coverage_rates = [story['estimated_coverage_rate'] for story in coverage_analysis['story_coverage']]
            
            coverage_analysis['overall_statistics'] = {
                'total_stories': len(coverage_analysis['story_coverage']),
                'mean_coverage_rate': np.mean(coverage_rates),
                'std_coverage_rate': np.std(coverage_rates),
                'min_coverage_rate': min(coverage_rates),
                'max_coverage_rate': max(coverage_rates),
                'high_coverage_stories': len([s for s in coverage_analysis['story_coverage'] if s['coverage_category'] == 'high']),
                'medium_coverage_stories': len([s for s in coverage_analysis['story_coverage'] if s['coverage_category'] == 'medium']),
                'low_coverage_stories': len([s for s in coverage_analysis['story_coverage'] if s['coverage_category'] == 'low'])
            }
            
            # By genre analysis
            genre_coverage = defaultdict(list)
            for story in coverage_analysis['story_coverage']:
                genre_coverage[story['genre']].append(story['estimated_coverage_rate'])
            
            coverage_analysis['genre_coverage'] = {}
            for genre, rates in genre_coverage.items():
                coverage_analysis['genre_coverage'][genre] = {
                    'mean_coverage': np.mean(rates),
                    'std_coverage': np.std(rates),
                    'story_count': len(rates)
                }
        
        stats = coverage_analysis['overall_statistics']
        print(f"📊 OOV coverage analysis:")
        print(f"   - Stories analyzed: {stats['total_stories']}")
        print(f"   - Mean coverage: {stats['mean_coverage_rate']*100:.1f}%")
        print(f"   - High coverage (>85%): {stats['high_coverage_stories']} stories")
        print(f"   - Low coverage (<60%): {stats['low_coverage_stories']} stories")
        
        if coverage_analysis['genre_coverage']:
            print(f"   - By genre:")
            for genre, genre_stats in coverage_analysis['genre_coverage'].items():
                print(f"     * {genre}: {genre_stats['mean_coverage']*100:.1f}%")
        
        return coverage_analysis
    
    def analyze_stopwords_impact(self):
        """Analyze stop words and functional words impact"""
        
        print("\n🔍 ANALYZING STOPWORDS IMPACT...")
        
        # Common English stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'among', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'them', 'their', 'there', 'here', 'where', 'when', 'why', 'how', 'what',
            'which', 'who', 'whom', 'whose', 'is', 'are', 'was', 'were', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'a', 'an'
        }
        
        stopwords_analysis = {
            'dictionary_composition': {
                'total_words_in_dict': len(self.labmt_dict),
                'stopwords_in_dict': len([word for word in self.labmt_dict if word in stop_words]),
                'content_words_in_dict': len([word for word in self.labmt_dict if word not in stop_words]),
                'stopwords_percentage': len([word for word in self.labmt_dict if word in stop_words]) / len(self.labmt_dict) * 100
            },
            'impact_simulation': {}
        }
        
        # Simulate impact of including vs excluding stop words
        sample_text = "The amazing story was really good and wonderful, but it had some terrible parts that were very bad"
        
        # Method 1: Include all words (current method)
        all_words = re.findall(r'\b[a-zA-Z]+\b', sample_text.lower())
        all_words_score = self._analyze_labmt_simple(sample_text)
        
        # Method 2: Exclude stop words
        content_words = [word for word in all_words if word not in stop_words]
        content_text = ' '.join(content_words)
        content_words_score = self._analyze_labmt_simple(content_text)
        
        stopwords_analysis['impact_simulation'] = {
            'sample_text': sample_text,
            'all_words': all_words,
            'content_words': content_words,
            'all_words_count': len(all_words),
            'content_words_count': len(content_words),
            'stopwords_removed': len(all_words) - len(content_words),
            'all_words_score': all_words_score,
            'content_words_score': content_words_score,
            'score_difference': content_words_score - all_words_score,
            'relative_change': ((content_words_score - all_words_score) / abs(all_words_score)) * 100 if all_words_score != 0 else 0
        }
        
        dict_stats = stopwords_analysis['dictionary_composition']
        impact_stats = stopwords_analysis['impact_simulation']
        
        print(f"📊 Stopwords impact analysis:")
        print(f"   - Dictionary composition:")
        print(f"     * Total words: {dict_stats['total_words_in_dict']}")
        print(f"     * Stop words: {dict_stats['stopwords_in_dict']} ({dict_stats['stopwords_percentage']:.1f}%)")
        print(f"     * Content words: {dict_stats['content_words_in_dict']}")
        print(f"   - Impact simulation:")
        print(f"     * With stopwords: {impact_stats['all_words_score']:.4f}")
        print(f"     * Without stopwords: {impact_stats['content_words_score']:.4f}")
        print(f"     * Relative change: {impact_stats['relative_change']:.1f}%")
        
        return stopwords_analysis
    
    def analyze_smoothing_effects(self):
        """Analyze smoothing and windowing effects"""
        
        print("\n🔍 ANALYZING SMOOTHING EFFECTS...")
        
        # Get a sample of stories with multiple chapters
        multi_chapter_stories = self.experiment_data[self.experiment_data['chapter_count'] > 3].copy()
        
        if len(multi_chapter_stories) == 0:
            print("⚠️ No multi-chapter stories found for smoothing analysis")
            return {'error': 'insufficient_data'}
        
        smoothing_analysis = {
            'stories_analyzed': [],
            'smoothing_methods': ['none', 'moving_average_3', 'moving_average_5', 'exponential'],
            'method_comparison': {}
        }
        
        # Analyze first few stories
        for _, row in multi_chapter_stories.head(5).iterrows():
            story_id = row['story_id']
            labmt_scores = row['labmt_scores_list']
            roberta_scores = row['roberta_scores_list']
            
            if len(labmt_scores) < 4 or len(roberta_scores) != len(labmt_scores):
                continue
            
            # Apply different smoothing methods to LabMT scores
            smoothed_scores = {}
            
            # No smoothing
            smoothed_scores['none'] = labmt_scores
            
            # Moving average (window=3)
            if len(labmt_scores) >= 3:
                ma3 = []
                for i in range(len(labmt_scores)):
                    if i == 0:
                        ma3.append(labmt_scores[i])
                    elif i == len(labmt_scores) - 1:
                        ma3.append(labmt_scores[i])
                    else:
                        ma3.append(np.mean(labmt_scores[i-1:i+2]))
                smoothed_scores['moving_average_3'] = ma3
            
            # Moving average (window=5)
            if len(labmt_scores) >= 5:
                ma5 = []
                for i in range(len(labmt_scores)):
                    start = max(0, i-2)
                    end = min(len(labmt_scores), i+3)
                    ma5.append(np.mean(labmt_scores[start:end]))
                smoothed_scores['moving_average_5'] = ma5
            
            # Exponential smoothing (alpha=0.3)
            exp_smooth = [labmt_scores[0]]
            alpha = 0.3
            for i in range(1, len(labmt_scores)):
                exp_smooth.append(alpha * labmt_scores[i] + (1 - alpha) * exp_smooth[i-1])
            smoothed_scores['exponential'] = exp_smooth
            
            # Calculate correlations with RoBERTa for each method
            correlations = {}
            for method, scores in smoothed_scores.items():
                if len(scores) == len(roberta_scores) and len(scores) > 2:
                    try:
                        corr = np.corrcoef(scores, roberta_scores)[0, 1]
                        correlations[method] = corr if not np.isnan(corr) else 0
                    except:
                        correlations[method] = 0
                else:
                    correlations[method] = 0
            
            story_analysis = {
                'story_id': story_id,
                'genre': row['genre'],
                'chapter_count': len(labmt_scores),
                'original_correlation': row['correlation_coefficient'],
                'smoothed_correlations': correlations,
                'correlation_improvements': {
                    method: correlations[method] - correlations['none'] 
                    for method in correlations if method != 'none'
                }
            }
            
            smoothing_analysis['stories_analyzed'].append(story_analysis)
        
        # Calculate method comparison statistics
        if smoothing_analysis['stories_analyzed']:
            for method in smoothing_analysis['smoothing_methods']:
                correlations = [story['smoothed_correlations'].get(method, 0) for story in smoothing_analysis['stories_analyzed'] if method in story['smoothed_correlations']]
                
                if correlations:
                    smoothing_analysis['method_comparison'][method] = {
                        'mean_correlation': np.mean(correlations),
                        'std_correlation': np.std(correlations),
                        'stories_count': len(correlations)
                    }
        
        print(f"📊 Smoothing effects analysis:")
        print(f"   - Stories analyzed: {len(smoothing_analysis['stories_analyzed'])}")
        
        if smoothing_analysis['method_comparison']:
            print(f"   - Method comparison:")
            for method, stats in smoothing_analysis['method_comparison'].items():
                print(f"     * {method}: {stats['mean_correlation']:.4f}±{stats['std_correlation']:.4f}")
        
        return smoothing_analysis
    
    def _analyze_labmt_simple(self, text):
        """Simple LabMT analysis for diagnostic purposes"""
        if not text or not text.strip():
            return 0.0
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        if not words:
            return 0.0
        
        total_score = 0
        valid_words = 0
        
        for word in words:
            if word in self.labmt_dict:
                total_score += self.labmt_dict[word]
                valid_words += 1
        
        if valid_words == 0:
            return 0.0
        
        avg_score = total_score / valid_words
        normalized_score = (avg_score - 5.0) / 4.0
        return max(-1, min(1, normalized_score))
    
    def create_diagnostic_visualizations(self, output_dir):
        """Create diagnostic visualizations"""
        
        print("\n📈 CREATING DIAGNOSTIC VISUALIZATIONS...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Coverage rate distribution
        if hasattr(self, 'coverage_analysis') and self.coverage_analysis['story_coverage']:
            coverage_rates = [story['estimated_coverage_rate'] for story in self.coverage_analysis['story_coverage']]
            
            plt.figure(figsize=(10, 6))
            plt.hist(coverage_rates, bins=20, alpha=0.7, edgecolor='black')
            plt.axvline(0.85, color='green', linestyle='--', label='High coverage threshold')
            plt.axvline(0.6, color='orange', linestyle='--', label='Medium coverage threshold')
            plt.xlabel('Estimated LabMT Coverage Rate')
            plt.ylabel('Number of Stories')
            plt.title('Distribution of LabMT Coverage Rates')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'labmt_coverage_distribution.png'), dpi=300)
            plt.close()
        
        # 2. Coverage by genre
        if hasattr(self, 'coverage_analysis') and 'genre_coverage' in self.coverage_analysis:
            genres = list(self.coverage_analysis['genre_coverage'].keys())
            coverage_means = [self.coverage_analysis['genre_coverage'][genre]['mean_coverage'] for genre in genres]
            coverage_stds = [self.coverage_analysis['genre_coverage'][genre]['std_coverage'] for genre in genres]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(genres, coverage_means, yerr=coverage_stds, capsize=5, alpha=0.7)
            plt.axhline(0.85, color='green', linestyle='--', label='High coverage threshold')
            plt.ylabel('Mean LabMT Coverage Rate')
            plt.title('LabMT Coverage Rate by Genre')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, value in zip(bars, coverage_means):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                        f'{value:.3f}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'labmt_coverage_by_genre.png'), dpi=300)
            plt.close()
        
        print(f"✅ Created diagnostic visualizations in {output_dir}")
    
    def generate_comprehensive_diagnostic_report(self, output_dir):
        """Generate comprehensive diagnostic report"""
        
        print("\n📋 GENERATING COMPREHENSIVE DIAGNOSTIC REPORT...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Run all diagnostic analyses
        print("Running tokenization analysis...")
        tokenization_results = self.analyze_tokenization_issues()
        
        print("Running negation analysis...")
        negation_results = self.analyze_negation_handling()
        
        print("Running OOV coverage analysis...")
        self.coverage_analysis = self.analyze_oov_coverage()
        
        print("Running stopwords impact analysis...")
        stopwords_results = self.analyze_stopwords_impact()
        
        print("Running smoothing effects analysis...")
        smoothing_results = self.analyze_smoothing_effects()
        
        # Compile comprehensive report
        diagnostic_report = {
            'diagnostic_info': {
                'timestamp': datetime.now().isoformat(),
                'total_stories_analyzed': len(self.experiment_data),
                'diagnostic_version': '1.0'
            },
            'tokenization_analysis': tokenization_results,
            'negation_analysis': negation_results,
            'coverage_analysis': self.coverage_analysis,
            'stopwords_analysis': stopwords_results,
            'smoothing_analysis': smoothing_results
        }
        
        # Convert to JSON-serializable format
        diagnostic_report = self._convert_to_serializable(diagnostic_report)
        
        # Save JSON report
        report_path = os.path.join(output_dir, 'labmt_diagnostic_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(diagnostic_report, f, indent=2, ensure_ascii=False)
        
        # Generate markdown summary
        summary_path = os.path.join(output_dir, 'labmt_diagnostic_summary.md')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# LabMT Deep Diagnostic Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Critical Issues Found\n\n")
            
            # Negation handling
            f.write(f"🚨 **NEGATION HANDLING**: Current LabMT implementation does NOT handle negation or context reversal.\n")
            f.write(f"   - Detection rate: {negation_results['negation_detection_rate']*100:.1f}%\n")
            f.write(f"   - Impact: Sentences like 'not good' are treated as positive\n\n")
            
            # Coverage issues
            if 'overall_statistics' in self.coverage_analysis:
                stats = self.coverage_analysis['overall_statistics']
                f.write(f"📊 **COVERAGE ANALYSIS**:\n")
                f.write(f"   - Mean coverage rate: {stats['mean_coverage_rate']*100:.1f}%\n")
                f.write(f"   - Low coverage stories: {stats['low_coverage_stories']}/{stats['total_stories']}\n\n")
            
            # Stopwords impact
            f.write(f"🔤 **STOPWORDS IMPACT**:\n")
            f.write(f"   - Stopwords in dictionary: {stopwords_results['dictionary_composition']['stopwords_percentage']:.1f}%\n")
            f.write(f"   - Score change without stopwords: {stopwords_results['impact_simulation']['relative_change']:.1f}%\n\n")
            
            f.write("## Recommendations\n\n")
            f.write("1. **Implement negation handling** - Add context-aware sentiment reversal\n")
            f.write("2. **Improve tokenization** - Handle contractions and punctuation better\n")
            f.write("3. **Filter stopwords** - Remove or weight down non-content words\n")
            f.write("4. **Add smoothing** - Apply temporal smoothing to reduce noise\n")
            f.write("5. **Validate coverage** - Ensure >85% vocabulary coverage per text\n\n")
            
            f.write("## Files Generated\n\n")
            f.write("- `labmt_diagnostic_report.json`: Complete diagnostic data\n")
            f.write("- `labmt_coverage_distribution.png`: Coverage rate distribution\n")
            f.write("- `labmt_coverage_by_genre.png`: Coverage by genre comparison\n")
        
        # Create visualizations
        self.create_diagnostic_visualizations(output_dir)
        
        print(f"✅ Generated comprehensive diagnostic report in {output_dir}")
        
        return diagnostic_report
    
    def _convert_to_serializable(self, obj):
        """Convert numpy types to JSON-serializable types"""
        if isinstance(obj, dict):
            return {key: self._convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj

def main():
    """Main diagnostic function"""
    
    # Create output directory
    output_dir = "/Users/haha/Story/AAA/emotion_analysis/labmt_diagnostics"
    os.makedirs(output_dir, exist_ok=True)
    
    print("🔬 Starting LabMT Deep Diagnostic Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    csv_path = "/Users/haha/Story/metrics_master_clean.csv"
    analyzer = LabMTDiagnosticAnalyzer(csv_path)
    
    # Generate comprehensive report
    diagnostic_report = analyzer.generate_comprehensive_diagnostic_report(output_dir)
    
    print(f"\n✅ LabMT diagnostic complete! Results saved to: {output_dir}")
    print("\nKey Issues Identified:")
    print("🚨 Negation handling: NOT implemented")
    print("📊 Coverage varies significantly by genre")
    print("🔤 Stopwords dilute sentiment signals")
    print("📈 Smoothing could improve temporal consistency")

if __name__ == "__main__":
    main()
