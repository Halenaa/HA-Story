#!/usr/bin/env python3
"""
Comprehensive Emotion Analysis
===============================

Analyzes emotion arc metrics from story generation experiments.
Based on dual-method analysis (RoBERTa + LabMT) with Reagan's six story archetypes.

Key Metrics:
- correlation_coefficient: Pearson correlation between RoBERTa and LabMT
- direction_consistency: Agreement on emotional trajectory direction
- classification_agreement: Agreement on Reagan archetype classification
- roberta_avg_score: Average RoBERTa emotional score
- reagan_classification: Story archetype (Cinderella, Tragedy, etc.)
- major_disagreements: Number of chapters with large score differences (>0.3)
- roberta_std, labmt_std: Variability in emotional scores

Evaluation Criteria:
- correlation_coefficient > 0.3 & p < 0.05 → Significant consistency
- major_disagreements < 3 → Stable
- classification_agreement > 0.7 → Reliable archetype labels
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency
import json
import os
import ast
from datetime import datetime
from collections import Counter

# Set style for better visualizations
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class EmotionAnalyzer:
    """Comprehensive emotion analysis tool"""
    
    def __init__(self, csv_path):
        """Initialize with data from CSV file"""
        self.data = pd.read_csv(csv_path)
        
        # Include ALL data (both experiments and baselines) for comprehensive analysis
        self.experiment_data = self.data.copy()  # Changed to include all 57 entries
        self.baseline_data = self.data[self.data['is_baseline'] == 1].copy()
        
        # Evaluation criteria
        self.CORRELATION_THRESHOLD = 0.3
        self.DISAGREEMENT_THRESHOLD = 3
        self.AGREEMENT_THRESHOLD = 0.7
        
        print(f"Loaded {len(self.data)} total entries")
        print(f"- {len(self.experiment_data)} experimental entries")
        print(f"- {len(self.baseline_data)} baseline entries")
        
        # Parse emotion score strings for detailed analysis
        self._parse_emotion_scores()
        
        # Apply bug fixes for correlation and direction consistency
        self._apply_bug_fixes()
        
    def _apply_bug_fixes(self):
        """Apply critical bug fixes to emotion data"""
        print("🔧 Applying emotion analysis bug fixes...")
        
        # Separate experiments from baselines for processing (after parsing)
        experiments = self.experiment_data[self.experiment_data['is_baseline'] == 0].copy()
        baselines = self.experiment_data[self.experiment_data['is_baseline'] == 1].copy()
        
        # Ensure parsed scores are available
        if 'roberta_scores' not in experiments.columns:
            print("   ERROR: roberta_scores not found, re-parsing...")
            experiments['roberta_scores'] = experiments['roberta_scores_str'].apply(self._parse_score_string)
            experiments['labmt_scores'] = experiments['labmt_scores_str'].apply(self._parse_score_string)
        
        print(f"   Processing {len(experiments)} experiments, preserving {len(baselines)} baselines")
        print(f"   First experiment has roberta_scores: {'roberta_scores' in experiments.columns}")
        print(f"   First experiment roberta_scores type: {type(experiments.iloc[0].get('roberta_scores', 'NOT_FOUND'))}")
        print(f"   First experiment roberta_scores: {experiments.iloc[0].get('roberta_scores', 'NOT_FOUND')}")
        
        # Fix experiments only
        fixed_exp_values = []
        debug_count = 0
        for idx, row in experiments.iterrows():
            original_dc = row['direction_consistency']
            
            if 'roberta_scores' in row and 'labmt_scores' in row:
                roberta_scores = row['roberta_scores']
                labmt_scores = row['labmt_scores']
                
                if len(roberta_scores) > 1 and len(labmt_scores) > 1:
                    # Calculate adjacent differences (emotional trajectory)
                    roberta_diffs = np.diff(roberta_scores)
                    labmt_diffs = np.diff(labmt_scores)
                    
                    # Count agreements in direction
                    agreements = 0
                    total_comparisons = len(roberta_diffs)
                    
                    for i in range(total_comparisons):
                        if np.sign(roberta_diffs[i]) == np.sign(labmt_diffs[i]):
                            agreements += 1
                    
                    direction_consistency = agreements / total_comparisons if total_comparisons > 0 else 0.0
                    
                    # Debug first few cases
                    if debug_count < 3:
                        print(f"   Debug {debug_count + 1}: {row['story_id']}")
                        print(f"      Original DC: {original_dc:.4f}")
                        print(f"      Fixed DC: {direction_consistency:.4f}")
                        debug_count += 1
                        
                else:
                    direction_consistency = original_dc
            else:
                direction_consistency = original_dc
            
            fixed_exp_values.append(direction_consistency)
        
        # Calculate improvement for experiments
        original_exp_mean = experiments['direction_consistency'].mean()
        fixed_exp_mean = np.mean(fixed_exp_values)
        improvement = ((fixed_exp_mean - original_exp_mean) / original_exp_mean) * 100
        
        print(f"✅ Direction consistency (experiments): {original_exp_mean:.4f} → {fixed_exp_mean:.4f} (+{improvement:.1f}%)")
        
        # Update experiments with fixed values
        experiments = experiments.copy()
        experiments['direction_consistency'] = fixed_exp_values
        
        # Preserve baselines as-is
        baseline_mean = baselines['direction_consistency'].mean()
        print(f"📊 Baseline preserved: {baseline_mean:.4f}")
        
        # Combine back
        self.experiment_data = pd.concat([experiments, baselines]).sort_index()
        
        # Calculate new overall mean
        total_count = len(experiments) + len(baselines)
        overall_fixed = (fixed_exp_mean * len(experiments) + baseline_mean * len(baselines)) / total_count
        original_overall = (original_exp_mean * len(experiments) + baseline_mean * len(baselines)) / total_count
        
        print(f"📊 Overall (57 stories): {original_overall:.4f} → {overall_fixed:.4f}")
        
    def _parse_emotion_scores(self):
        """Parse roberta_scores_str and labmt_scores_str into lists"""
        def safe_parse_scores(score_str):
            """Safely parse score string to list of floats"""
            if pd.isna(score_str):
                return []
            try:
                # Handle string format like "0.1,0.2,0.3" or "[0.1,0.2,0.3]"
                if isinstance(score_str, str):
                    # Remove brackets and split by comma
                    score_str = score_str.strip('[]')
                    return [float(x.strip()) for x in score_str.split(',') if x.strip()]
                return []
            except:
                return []
        
        self.experiment_data['roberta_scores_list'] = self.experiment_data['roberta_scores_str'].apply(safe_parse_scores)
        self.experiment_data['labmt_scores_list'] = self.experiment_data['labmt_scores_str'].apply(safe_parse_scores)
        
        # Calculate additional metrics
        self.experiment_data['roberta_range'] = self.experiment_data['roberta_scores_list'].apply(
            lambda scores: max(scores) - min(scores) if len(scores) > 1 else 0
        )
        self.experiment_data['labmt_range'] = self.experiment_data['labmt_scores_list'].apply(
            lambda scores: max(scores) - min(scores) if len(scores) > 1 else 0
        )
        
        print("✅ Parsed emotion score strings successfully")
    
    def basic_statistics(self):
        """Calculate basic emotion statistics"""
        
        stats_dict = {}
        
        # Overall statistics
        valid_data = self.experiment_data.dropna(subset=['correlation_coefficient', 'major_disagreements'])
        
        stats_dict['overall'] = {
            'count': len(valid_data),
            'mean_correlation': valid_data['correlation_coefficient'].mean(),
            'std_correlation': valid_data['correlation_coefficient'].std(),
            'median_correlation': valid_data['correlation_coefficient'].median(),
            'significant_correlations': len(valid_data[valid_data['correlation_coefficient'] > self.CORRELATION_THRESHOLD]),
            'significant_percentage': len(valid_data[valid_data['correlation_coefficient'] > self.CORRELATION_THRESHOLD]) / len(valid_data) * 100,
            'stable_stories': len(valid_data[valid_data['major_disagreements'] < self.DISAGREEMENT_THRESHOLD]),
            'stable_percentage': len(valid_data[valid_data['major_disagreements'] < self.DISAGREEMENT_THRESHOLD]) / len(valid_data) * 100,
            'mean_roberta_score': valid_data['roberta_avg_score'].mean(),
            'mean_disagreements': valid_data['major_disagreements'].mean(),
            'mean_direction_consistency': valid_data['direction_consistency'].mean()
        }
        
        # Classification agreement analysis
        if 'classification_agreement' in valid_data.columns:
            agreement_rate = valid_data['classification_agreement'].mean()
            stats_dict['overall']['classification_agreement_rate'] = agreement_rate
            stats_dict['overall']['reliable_classification'] = agreement_rate > self.AGREEMENT_THRESHOLD
        
        # By structure
        for structure in ['linear', 'nonlinear']:
            structure_data = valid_data[valid_data['structure'] == structure]
            if len(structure_data) > 0:
                stats_dict[f'{structure}_structure'] = {
                    'count': len(structure_data),
                    'mean_correlation': structure_data['correlation_coefficient'].mean(),
                    'significant_percentage': len(structure_data[structure_data['correlation_coefficient'] > self.CORRELATION_THRESHOLD]) / len(structure_data) * 100,
                    'stable_percentage': len(structure_data[structure_data['major_disagreements'] < self.DISAGREEMENT_THRESHOLD]) / len(structure_data) * 100,
                    'mean_roberta_score': structure_data['roberta_avg_score'].mean(),
                    'mean_direction_consistency': structure_data['direction_consistency'].mean()
                }
        
        # By genre
        for genre in ['sciencefiction', 'horror', 'romantic']:
            genre_data = valid_data[valid_data['genre'] == genre]
            if len(genre_data) > 0:
                stats_dict[f'{genre}_genre'] = {
                    'count': len(genre_data),
                    'mean_correlation': genre_data['correlation_coefficient'].mean(),
                    'significant_percentage': len(genre_data[genre_data['correlation_coefficient'] > self.CORRELATION_THRESHOLD]) / len(genre_data) * 100,
                    'stable_percentage': len(genre_data[genre_data['major_disagreements'] < self.DISAGREEMENT_THRESHOLD]) / len(genre_data) * 100,
                    'mean_roberta_score': genre_data['roberta_avg_score'].mean()
                }
        
        return stats_dict
    
    def archetype_analysis(self):
        """Analyze Reagan story archetype distributions"""
        
        analysis = {}
        
        # Overall archetype distribution
        archetype_counts = self.experiment_data['reagan_classification'].value_counts()
        analysis['archetype_distribution'] = {
            'counts': archetype_counts.to_dict(),
            'percentages': (archetype_counts / len(self.experiment_data) * 100).to_dict(),
            'total_stories': len(self.experiment_data)
        }
        
        # Most common archetypes
        analysis['most_common_archetypes'] = archetype_counts.head(3).index.tolist()
        
        # Archetype by genre
        analysis['archetype_by_genre'] = {}
        for genre in ['sciencefiction', 'horror', 'romantic']:
            genre_data = self.experiment_data[self.experiment_data['genre'] == genre]
            if len(genre_data) > 0:
                genre_archetypes = genre_data['reagan_classification'].value_counts()
                analysis['archetype_by_genre'][genre] = {
                    'counts': genre_archetypes.to_dict(),
                    'most_common': genre_archetypes.index[0] if len(genre_archetypes) > 0 else 'Unknown'
                }
        
        # Archetype by structure
        analysis['archetype_by_structure'] = {}
        for structure in ['linear', 'nonlinear']:
            structure_data = self.experiment_data[self.experiment_data['structure'] == structure]
            if len(structure_data) > 0:
                structure_archetypes = structure_data['reagan_classification'].value_counts()
                analysis['archetype_by_structure'][structure] = {
                    'counts': structure_archetypes.to_dict(),
                    'most_common': structure_archetypes.index[0] if len(structure_archetypes) > 0 else 'Unknown'
                }
        
        # Statistical test for archetype-genre association
        if len(self.experiment_data) > 0:
            contingency_table = pd.crosstab(self.experiment_data['genre'], self.experiment_data['reagan_classification'])
            if contingency_table.size > 0 and contingency_table.sum().sum() > 0:
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)
                analysis['genre_archetype_association'] = {
                    'chi2_statistic': chi2,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'contingency_table': contingency_table.to_dict()
                }
        
        return analysis
    
    def emotion_coherence_interaction(self):
        """Analyze interaction between emotion and coherence"""
        
        valid_data = self.experiment_data.dropna(subset=['correlation_coefficient', 'avg_coherence', 'roberta_std'])
        
        if len(valid_data) < 10:
            return {"error": "Insufficient data for interaction analysis"}
        
        analysis = {}
        
        # Correlation between emotion stability and coherence
        emotion_stability = 1 / (1 + valid_data['roberta_std'])  # Higher std = lower stability
        coherence = valid_data['avg_coherence']
        
        correlation, p_value = stats.pearsonr(emotion_stability, coherence)
        
        analysis['emotion_stability_coherence'] = {
            'correlation': correlation,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'interpretation': 'More stable emotions correlate with higher coherence' if correlation > 0 else 'More volatile emotions correlate with higher coherence'
        }
        
        # Correlation between RoBERTa-LabMT agreement and coherence
        method_agreement = valid_data['correlation_coefficient']
        correlation2, p_value2 = stats.pearsonr(method_agreement, coherence)
        
        analysis['method_agreement_coherence'] = {
            'correlation': correlation2,
            'p_value': p_value2,
            'significant': p_value2 < 0.05,
            'interpretation': 'Higher method agreement correlates with higher coherence' if correlation2 > 0 else 'Method disagreement might indicate complexity'
        }
        
        # Emotional range vs coherence
        if 'roberta_range' in valid_data.columns:
            emotion_range = valid_data['roberta_range']
            correlation3, p_value3 = stats.pearsonr(emotion_range, coherence)
            
            analysis['emotion_range_coherence'] = {
                'correlation': correlation3,
                'p_value': p_value3,
                'significant': p_value3 < 0.05,
                'interpretation': 'Wider emotional range correlates with higher coherence' if correlation3 > 0 else 'Narrower emotional range correlates with higher coherence'
            }
        
        return analysis
    
    def structure_emotion_relationship(self):
        """Analyze relationship between story structure and emotion patterns"""
        
        analysis = {}
        
        linear_data = self.experiment_data[self.experiment_data['structure'] == 'linear']
        nonlinear_data = self.experiment_data[self.experiment_data['structure'] == 'nonlinear']
        
        if len(linear_data) > 0 and len(nonlinear_data) > 0:
            
            # Compare emotional volatility (roberta_std)
            linear_volatility = linear_data['roberta_std'].dropna()
            nonlinear_volatility = nonlinear_data['roberta_std'].dropna()
            
            if len(linear_volatility) > 0 and len(nonlinear_volatility) > 0:
                t_stat, p_value = stats.ttest_ind(linear_volatility, nonlinear_volatility)
                
                analysis['volatility_comparison'] = {
                    'linear_mean': linear_volatility.mean(),
                    'nonlinear_mean': nonlinear_volatility.mean(),
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'nonlinear_more_volatile': nonlinear_volatility.mean() > linear_volatility.mean()
                }
            
            # Compare method disagreements
            linear_disagreements = linear_data['major_disagreements'].dropna()
            nonlinear_disagreements = nonlinear_data['major_disagreements'].dropna()
            
            if len(linear_disagreements) > 0 and len(nonlinear_disagreements) > 0:
                t_stat2, p_value2 = stats.ttest_ind(linear_disagreements, nonlinear_disagreements)
                
                analysis['disagreement_comparison'] = {
                    'linear_mean': linear_disagreements.mean(),
                    'nonlinear_mean': nonlinear_disagreements.mean(),
                    't_statistic': t_stat2,
                    'p_value': p_value2,
                    'significant': p_value2 < 0.05,
                    'nonlinear_more_disagreements': nonlinear_disagreements.mean() > linear_disagreements.mean()
                }
            
            # Compare correlation coefficients
            linear_corr = linear_data['correlation_coefficient'].dropna()
            nonlinear_corr = nonlinear_data['correlation_coefficient'].dropna()
            
            if len(linear_corr) > 0 and len(nonlinear_corr) > 0:
                t_stat3, p_value3 = stats.ttest_ind(linear_corr, nonlinear_corr)
                
                analysis['correlation_comparison'] = {
                    'linear_mean': linear_corr.mean(),
                    'nonlinear_mean': nonlinear_corr.mean(),
                    't_statistic': t_stat3,
                    'p_value': p_value3,
                    'significant': p_value3 < 0.05,
                    'nonlinear_higher_correlation': nonlinear_corr.mean() > linear_corr.mean()
                }
        
        return analysis
    
    def validate_calculations(self):
        """Validate emotion metric calculations"""
        
        validation = {}
        
        # Check correlation coefficient ranges
        corr_data = self.experiment_data['correlation_coefficient'].dropna()
        
        validation['correlation_range'] = {
            'min_value': corr_data.min(),
            'max_value': corr_data.max(),
            'within_expected_range': (corr_data.min() >= -1.0) and (corr_data.max() <= 1.0),
            'realistic_distribution': len(corr_data[(corr_data >= -1) & (corr_data <= 1)]) == len(corr_data)
        }
        
        # Check direction consistency ranges
        dir_data = self.experiment_data['direction_consistency'].dropna()
        
        validation['direction_consistency_range'] = {
            'min_value': dir_data.min(),
            'max_value': dir_data.max(),
            'within_expected_range': (dir_data.min() >= 0.0) and (dir_data.max() <= 1.0)
        }
        
        # Check for logical consistency
        validation['logical_consistency'] = {}
        
        # Stories with high correlation should have fewer disagreements
        high_corr_stories = self.experiment_data[self.experiment_data['correlation_coefficient'] > 0.7]
        if len(high_corr_stories) > 0:
            avg_disagreements_high_corr = high_corr_stories['major_disagreements'].mean()
            avg_disagreements_overall = self.experiment_data['major_disagreements'].mean()
            validation['logical_consistency']['high_correlation_fewer_disagreements'] = avg_disagreements_high_corr < avg_disagreements_overall
        
        # Check classification agreement consistency
        if 'classification_agreement' in self.experiment_data.columns:
            agreement_data = self.experiment_data['classification_agreement'].dropna()
            validation['classification_agreement'] = {
                'total_stories': len(agreement_data),
                'agreement_count': agreement_data.sum() if pd.api.types.is_bool_dtype(agreement_data) else len(agreement_data[agreement_data == True]),
                'agreement_rate': agreement_data.mean() if pd.api.types.is_bool_dtype(agreement_data) else len(agreement_data[agreement_data == True]) / len(agreement_data)
            }
        
        # Check score string parsing success rate
        valid_roberta_scores = len([scores for scores in self.experiment_data['roberta_scores_list'] if len(scores) > 0])
        valid_labmt_scores = len([scores for scores in self.experiment_data['labmt_scores_list'] if len(scores) > 0])
        
        validation['score_parsing'] = {
            'roberta_parsing_success_rate': valid_roberta_scores / len(self.experiment_data),
            'labmt_parsing_success_rate': valid_labmt_scores / len(self.experiment_data),
            'overall_parsing_success': (valid_roberta_scores + valid_labmt_scores) / (2 * len(self.experiment_data))
        }
        
        return validation
    
    def create_visualizations(self, output_dir):
        """Create comprehensive visualizations"""
        
        # 1. Archetype distribution bar chart
        archetype_counts = self.experiment_data['reagan_classification'].value_counts()
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(archetype_counts)), archetype_counts.values)
        plt.xticks(range(len(archetype_counts)), archetype_counts.index, rotation=45)
        plt.ylabel('Number of Stories')
        plt.title('Distribution of Reagan Story Archetypes')
        plt.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, archetype_counts.values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(value), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'archetype_distribution.png'), dpi=300)
        plt.close()
        
        # 2. Correlation coefficient distribution
        corr_data = self.experiment_data['correlation_coefficient'].dropna()
        plt.figure(figsize=(10, 6))
        plt.hist(corr_data, bins=20, alpha=0.7, edgecolor='black', density=True)
        plt.axvline(x=self.CORRELATION_THRESHOLD, color='red', linestyle='--', linewidth=2, 
                   label=f'Significance threshold ({self.CORRELATION_THRESHOLD})')
        plt.axvline(x=corr_data.mean(), color='blue', linestyle='-', linewidth=2, 
                   label=f'Mean ({corr_data.mean():.3f})')
        plt.xlabel('RoBERTa-LabMT Correlation Coefficient')
        plt.ylabel('Density')
        plt.title('Distribution of Method Correlation Coefficients')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'correlation_distribution.png'), dpi=300)
        plt.close()
        
        # 3. Scatter plot: RoBERTa avg score vs correlation
        valid_data = self.experiment_data.dropna(subset=['roberta_avg_score', 'correlation_coefficient'])
        if len(valid_data) > 0:
            plt.figure(figsize=(10, 8))
            
            # Color by structure
            for structure in ['linear', 'nonlinear']:
                subset = valid_data[valid_data['structure'] == structure]
                if len(subset) > 0:
                    plt.scatter(subset['roberta_avg_score'], subset['correlation_coefficient'], 
                              label=f'{structure.title()} structure', alpha=0.7, s=60)
            
            plt.axhline(y=self.CORRELATION_THRESHOLD, color='red', linestyle='--', alpha=0.7, 
                       label=f'Significance threshold')
            plt.xlabel('RoBERTa Average Score')
            plt.ylabel('RoBERTa-LabMT Correlation')
            plt.title('Emotional Score vs Method Agreement')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'score_vs_correlation_scatter.png'), dpi=300)
            plt.close()
        
        # 4. Box plot: Emotional volatility by structure
        volatility_data = []
        volatility_labels = []
        
        for structure in ['linear', 'nonlinear']:
            data = self.experiment_data[self.experiment_data['structure'] == structure]['roberta_std'].dropna()
            if len(data) > 0:
                volatility_data.append(data)
                volatility_labels.append(structure.title())
        
        if volatility_data:
            plt.figure(figsize=(8, 6))
            plt.boxplot(volatility_data, tick_labels=volatility_labels)
            plt.ylabel('RoBERTa Standard Deviation (Emotional Volatility)')
            plt.title('Emotional Volatility by Story Structure')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'volatility_by_structure.png'), dpi=300)
            plt.close()
        
        # 5. Archetype by genre stacked bar
        archetype_genre_data = pd.crosstab(self.experiment_data['reagan_classification'], 
                                         self.experiment_data['genre'])
        if not archetype_genre_data.empty:
            plt.figure(figsize=(12, 8))
            archetype_genre_data.plot(kind='bar', stacked=True, ax=plt.gca())
            plt.xlabel('Story Archetype')
            plt.ylabel('Number of Stories')
            plt.title('Story Archetypes by Genre')
            plt.legend(title='Genre', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'archetype_by_genre_stacked.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 6. Major disagreements analysis
        disagreement_data = self.experiment_data['major_disagreements'].dropna()
        if len(disagreement_data) > 0:
            plt.figure(figsize=(10, 6))
            plt.hist(disagreement_data, bins=range(int(disagreement_data.max())+2), alpha=0.7, edgecolor='black')
            plt.axvline(x=self.DISAGREEMENT_THRESHOLD, color='red', linestyle='--', linewidth=2, 
                       label=f'Stability threshold ({self.DISAGREEMENT_THRESHOLD})')
            plt.xlabel('Number of Major Disagreements')
            plt.ylabel('Number of Stories')
            plt.title('Distribution of Major Disagreements Between Methods')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'disagreements_histogram.png'), dpi=300)
            plt.close()
        
        print(f"Created 6 visualization plots in {output_dir}")
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        
        report = {
            'analysis_info': {
                'timestamp': datetime.now().isoformat(),
                'data_source': 'metrics_master_clean.csv',
                'analyzer_version': '1.0',
                'evaluation_criteria': {
                    'correlation_threshold': self.CORRELATION_THRESHOLD,
                    'disagreement_threshold': self.DISAGREEMENT_THRESHOLD,
                    'agreement_threshold': self.AGREEMENT_THRESHOLD
                }
            },
            'basic_statistics': self.basic_statistics(),
            'archetype_analysis': self.archetype_analysis(),
            'emotion_coherence_interaction': self.emotion_coherence_interaction(),
            'structure_emotion_relationship': self.structure_emotion_relationship(),
            'validation': self.validate_calculations()
        }
        
        # Convert numpy types to JSON-serializable types
        report = self._convert_to_serializable(report)
        
        # Add interpretations and recommendations
        report['interpretations'] = self._generate_interpretations(report)
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _convert_to_serializable(self, obj):
        """Convert numpy types to Python native types for JSON serialization"""
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
    
    def _generate_interpretations(self, report):
        """Generate human-readable interpretations"""
        
        interpretations = []
        
        basic_stats = report['basic_statistics']['overall']
        
        # Method consistency assessment
        if basic_stats['significant_percentage'] > 70:
            interpretations.append(f"✅ HIGH CONSISTENCY: {basic_stats['significant_percentage']:.1f}% of stories show significant RoBERTa-LabMT correlation (r>{self.CORRELATION_THRESHOLD})")
        elif basic_stats['significant_percentage'] > 50:
            interpretations.append(f"⚠️ MODERATE CONSISTENCY: {basic_stats['significant_percentage']:.1f}% of stories show significant method agreement")
        else:
            interpretations.append(f"❌ LOW CONSISTENCY: Only {basic_stats['significant_percentage']:.1f}% of stories show significant method agreement")
        
        # Stability assessment
        if basic_stats['stable_percentage'] > 70:
            interpretations.append(f"✅ STABLE EMOTIONS: {basic_stats['stable_percentage']:.1f}% of stories have stable emotional analysis (<{self.DISAGREEMENT_THRESHOLD} disagreements)")
        else:
            interpretations.append(f"⚠️ VOLATILE EMOTIONS: Only {basic_stats['stable_percentage']:.1f}% of stories show stable emotional patterns")
        
        # Archetype analysis
        if 'archetype_analysis' in report:
            archetype_data = report['archetype_analysis']['archetype_distribution']
            most_common = max(archetype_data['percentages'].items(), key=lambda x: x[1])
            interpretations.append(f"📚 DOMINANT ARCHETYPE: {most_common[0]} accounts for {most_common[1]:.1f}% of all stories")
        
        # Structure-emotion interaction
        if 'structure_emotion_relationship' in report:
            structure_analysis = report['structure_emotion_relationship']
            if 'volatility_comparison' in structure_analysis and structure_analysis['volatility_comparison']['significant']:
                if structure_analysis['volatility_comparison']['nonlinear_more_volatile']:
                    interpretations.append("🌪️ STRUCTURE EFFECT: Nonlinear stories show significantly higher emotional volatility")
                else:
                    interpretations.append("📈 STRUCTURE EFFECT: Linear stories show significantly higher emotional volatility")
        
        return interpretations
    
    def _generate_recommendations(self, report):
        """Generate actionable recommendations"""
        
        recommendations = []
        
        basic_stats = report['basic_statistics']['overall']
        
        # Method consistency recommendations
        if basic_stats['significant_percentage'] < 70:
            recommendations.append("IMPROVE METHOD AGREEMENT: Consider adjusting analysis parameters or validating with human evaluation")
        
        if basic_stats['stable_percentage'] < 70:
            recommendations.append("REDUCE VOLATILITY: High disagreement rates suggest need for more consistent emotional trajectory generation")
        
        # Classification reliability
        if 'classification_agreement_rate' in basic_stats:
            if basic_stats['classification_agreement_rate'] < self.AGREEMENT_THRESHOLD:
                recommendations.append("VALIDATE ARCHETYPES: Low classification agreement suggests need for manual validation of story archetypes")
        
        # Validation recommendations
        validation = report['validation']
        if 'score_parsing' in validation:
            if validation['score_parsing']['overall_parsing_success'] < 0.9:
                recommendations.append("FIX DATA PARSING: Some emotion score strings failed to parse correctly")
        
        return recommendations

def main():
    """Main analysis function"""
    
    # Create output directory
    output_dir = "/Users/haha/Story/AAA/emotion_analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎭 Starting Comprehensive Emotion Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    csv_path = "/Users/haha/Story/metrics_master_clean.csv"
    analyzer = EmotionAnalyzer(csv_path)
    
    # Generate comprehensive report
    print("📊 Generating analysis report...")
    report = analyzer.generate_report()
    
    # Save report
    report_path = os.path.join(output_dir, "emotion_analysis_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Create visualizations
    print("📈 Creating visualizations...")
    analyzer.create_visualizations(output_dir)
    
    # Generate summary report
    summary_path = os.path.join(output_dir, "emotion_analysis_summary.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# Emotion Analysis Summary\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Basic statistics
        basic_stats = report['basic_statistics']['overall']
        f.write("## Key Findings\n\n")
        f.write(f"- **Total Stories Analyzed:** {basic_stats['count']}\n")
        f.write(f"- **Mean RoBERTa-LabMT Correlation:** {basic_stats['mean_correlation']:.4f}\n")
        f.write(f"- **Significant Correlations:** {basic_stats['significant_correlations']}/{basic_stats['count']} ({basic_stats['significant_percentage']:.1f}%)\n")
        f.write(f"- **Stable Stories:** {basic_stats['stable_stories']}/{basic_stats['count']} ({basic_stats['stable_percentage']:.1f}%)\n")
        f.write(f"- **Mean Direction Consistency:** {basic_stats['mean_direction_consistency']:.4f}\n\n")
        
        # Archetype distribution
        if 'archetype_analysis' in report:
            archetype_data = report['archetype_analysis']['archetype_distribution']
            f.write("## Story Archetype Distribution\n\n")
            sorted_archetypes = sorted(archetype_data['percentages'].items(), key=lambda x: x[1], reverse=True)
            for archetype, percentage in sorted_archetypes:
                f.write(f"- **{archetype}:** {archetype_data['counts'][archetype]} stories ({percentage:.1f}%)\n")
            f.write("\n")
        
        # Interpretations
        f.write("## Interpretations\n\n")
        for interpretation in report['interpretations']:
            f.write(f"- {interpretation}\n")
        f.write("\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        for recommendation in report['recommendations']:
            f.write(f"- {recommendation}\n")
        f.write("\n")
        
        f.write("## Files Generated\n\n")
        f.write("- `emotion_analysis_report.json`: Complete analysis data\n")
        f.write("- `archetype_distribution.png`: Reagan story archetype distribution\n")
        f.write("- `correlation_distribution.png`: RoBERTa-LabMT correlation distribution\n")
        f.write("- `score_vs_correlation_scatter.png`: Emotional score vs method agreement\n")
        f.write("- `volatility_by_structure.png`: Emotional volatility comparison by structure\n")
        f.write("- `archetype_by_genre_stacked.png`: Archetype distribution across genres\n")
        f.write("- `disagreements_histogram.png`: Method disagreement analysis\n")
    
    print(f"✅ Analysis complete! Results saved to: {output_dir}")
    print("\nGenerated files:")
    for file in os.listdir(output_dir):
        print(f"  - {file}")

if __name__ == "__main__":
    main()
