#!/usr/bin/env python3
"""
Comprehensive Coherence Analysis System (English Version)
Analyzes coherence patterns in AI-generated stories vs baseline

Author: AI Assistant  
Created: 2025-09-13
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json
import warnings
warnings.filterwarnings('ignore')

plt.style.use('default')
sns.set_palette("husl")

class CoherenceAnalyzer:
    """Comprehensive coherence analyzer"""
    
    def __init__(self, csv_path):
        """Initialize with data from CSV file"""
        self.data = pd.read_csv(csv_path)
        
        # Filter out baseline entries for main analysis
        self.experiment_data = self.data[self.data['is_baseline'] == 0].copy()
        self.baseline_data = self.data[self.data['is_baseline'] == 1].copy()
        
        # Coherence evaluation criteria
        self.COHERENT_THRESHOLD = 0.35
        self.STABLE_STD_THRESHOLD = 0.18
        
        print(f"Loaded {len(self.data)} total entries")
        print(f"- {len(self.experiment_data)} experimental entries")
        print(f"- {len(self.baseline_data)} baseline entries")
        
    def basic_statistics(self):
        """Calculate basic coherence statistics"""
        print("\n📊 Calculating basic coherence statistics...")
        
        coherence_data = self.experiment_data['avg_coherence'].dropna()
        std_data = self.experiment_data['coherence_std'].dropna()
        
        # Overall statistics
        stats_dict = {
            'overall': {
                'count': len(coherence_data),
                'mean_coherence': float(coherence_data.mean()),
                'std_coherence': float(coherence_data.std()),
                'median_coherence': float(coherence_data.median()),
                'min_coherence': float(coherence_data.min()),
                'max_coherence': float(coherence_data.max()),
                'mean_std': float(std_data.mean()),
                'coherent_stories': len(coherence_data[coherence_data > self.COHERENT_THRESHOLD]),
                'coherent_percentage': len(coherence_data[coherence_data > self.COHERENT_THRESHOLD]) / len(coherence_data) * 100,
                'stable_stories': len(std_data[std_data < self.STABLE_STD_THRESHOLD]),
                'stable_percentage': len(std_data[std_data < self.STABLE_STD_THRESHOLD]) / len(std_data) * 100
                }
        }
        
        # Structure-wise analysis  
        for structure in ['linear', 'nonlinear']:
            struct_data = self.experiment_data[self.experiment_data['structure'] == structure]
            struct_coherence = struct_data['avg_coherence'].dropna()
            struct_std = struct_data['coherence_std'].dropna()
            
            if len(struct_coherence) > 0:
                stats_dict[f'{structure}_structure'] = {
                    'count': len(struct_coherence),
                    'mean_coherence': float(struct_coherence.mean()),
                    'std_coherence': float(struct_coherence.std()),
                    'median_coherence': float(struct_coherence.median()),
                    'coherent_percentage': len(struct_coherence[struct_coherence > self.COHERENT_THRESHOLD]) / len(struct_coherence) * 100,
                    'stable_percentage': len(struct_std[struct_std < self.STABLE_STD_THRESHOLD]) / len(struct_std) * 100
                }
        
        # Genre-wise analysis
        for genre in ['sciencefiction', 'horror', 'romantic']:
            genre_data = self.experiment_data[self.experiment_data['genre'] == genre]
            genre_coherence = genre_data['avg_coherence'].dropna()
            genre_std = genre_data['coherence_std'].dropna()
            
            if len(genre_coherence) > 0:
                stats_dict[f'{genre}_genre'] = {
                    'count': len(genre_coherence),
                    'mean_coherence': float(genre_coherence.mean()),
                    'std_coherence': float(genre_coherence.std()),
                    'median_coherence': float(genre_coherence.median()),
                    'coherent_percentage': len(genre_coherence[genre_coherence > self.COHERENT_THRESHOLD]) / len(genre_coherence) * 100,
                    'stable_percentage': len(genre_std[genre_std < self.STABLE_STD_THRESHOLD]) / len(genre_std) * 100
                }
        
        # Compare with baseline
        if len(self.baseline_data) > 0:
            baseline_coh = self.baseline_data['avg_coherence'].dropna()
            if len(baseline_coh) > 0:
                stats_dict['baseline_comparison'] = {
                    'baseline_mean': baseline_coh.mean(),
                    'experiment_mean': coherence_data.mean(),
                    'improvement': coherence_data.mean() - baseline_coh.mean(),
                    'improvement_percentage': ((coherence_data.mean() - baseline_coh.mean()) / baseline_coh.mean()) * 100
                }
        
        return stats_dict
    
    def structure_analysis(self):
        """Analyze coherence differences between structures"""
        print("\n🏗️ Analyzing structure effects...")
        
        linear_data = self.experiment_data[self.experiment_data['structure'] == 'linear']['avg_coherence'].dropna()
        nonlinear_data = self.experiment_data[self.experiment_data['structure'] == 'nonlinear']['avg_coherence'].dropna()
        
        if len(linear_data) > 0 and len(nonlinear_data) > 0:
            # Statistical test
            t_stat, p_value = stats.ttest_ind(linear_data, nonlinear_data)
            
            # Effect size (Cohen's d)
            pooled_std = np.sqrt(((len(linear_data) - 1) * linear_data.var() + (len(nonlinear_data) - 1) * nonlinear_data.var()) / (len(linear_data) + len(nonlinear_data) - 2))
            cohens_d = (linear_data.mean() - nonlinear_data.mean()) / pooled_std
            
            return {
                'statistical_test': {
                    'linear_mean': float(linear_data.mean()),
                    'nonlinear_mean': float(nonlinear_data.mean()),
                    'linear_count': len(linear_data),
                    'nonlinear_count': len(nonlinear_data),
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'significant': bool(p_value < 0.05),
                    'effect_size': float(cohens_d)
                },
                'practical_significance': {
                    'linear_higher': bool(linear_data.mean() > nonlinear_data.mean()),
                    'difference_magnitude': float(abs(linear_data.mean() - nonlinear_data.mean())),
                    'relative_difference_pct': float(abs(linear_data.mean() - nonlinear_data.mean()) / min(linear_data.mean(), nonlinear_data.mean()) * 100)
                }
            }
        else:
            return {'error': 'Insufficient data for structure analysis'}
    
    def coherence_diversity_interaction(self):
        """Analyze coherence-diversity trade-off"""
        print("\n🔗 Analyzing coherence-diversity interaction...")
        
        # Filter data with both coherence and diversity metrics
        analysis_data = self.experiment_data.dropna(subset=['avg_coherence', 'diversity_group_score'])
        
        if len(analysis_data) < 10:
            return {'error': 'Insufficient data for coherence-diversity analysis'}
        
        coherence = analysis_data['avg_coherence']
        diversity = analysis_data['diversity_group_score']
        
        # Correlation analysis
        corr_coef, p_value = stats.pearsonr(coherence, diversity)
        
        # Categorize into quadrants
        coh_median = coherence.median()
        div_median = diversity.median()
        
        high_coh_high_div = analysis_data[(coherence >= coh_median) & (diversity >= div_median)]
        high_coh_low_div = analysis_data[(coherence >= coh_median) & (diversity < div_median)]
        low_coh_high_div = analysis_data[(coherence < coh_median) & (diversity >= div_median)]
        low_coh_low_div = analysis_data[(coherence < coh_median) & (diversity < div_median)]
        
        return {
            'correlation': {
                'pearson_r': float(corr_coef),
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05),
                'strength': self._interpret_correlation_strength(abs(corr_coef)),
                'direction': 'positive' if corr_coef > 0 else 'negative'
            },
            'segments': {
                'high_coh_high_div': {
                    'count': len(high_coh_high_div),
                    'percentage': len(high_coh_high_div) / len(analysis_data) * 100,
                    'avg_coherence': float(high_coh_high_div['avg_coherence'].mean()),
                    'avg_diversity': float(high_coh_high_div['diversity_group_score'].mean())
                },
                'high_coh_low_div': {
                    'count': len(high_coh_low_div),
                    'percentage': len(high_coh_low_div) / len(analysis_data) * 100,
                    'avg_coherence': float(high_coh_low_div['avg_coherence'].mean()),
                    'avg_diversity': float(high_coh_low_div['diversity_group_score'].mean())
                },
                'low_coh_high_div': {
                    'count': len(low_coh_high_div),
                    'percentage': len(low_coh_high_div) / len(analysis_data) * 100,
                    'avg_coherence': float(low_coh_high_div['avg_coherence'].mean()),
                    'avg_diversity': float(low_coh_high_div['diversity_group_score'].mean())
                },
                'low_coh_low_div': {
                    'count': len(low_coh_low_div),
                    'percentage': len(low_coh_low_div) / len(analysis_data) * 100,
                    'avg_coherence': float(low_coh_low_div['avg_coherence'].mean()),
                    'avg_diversity': float(low_coh_low_div['diversity_group_score'].mean())
                }
            }
        }
    
    def _interpret_correlation_strength(self, r):
        """Interpret correlation strength"""
        if r < 0.1:
            return "negligible"
        elif r < 0.3:
            return "weak"
        elif r < 0.5:
            return "moderate"
        elif r < 0.7:
            return "strong"
        else:
            return "very strong"
    
    def create_visualizations(self):
        """Create coherence analysis visualizations"""
        print("\n📈 Creating visualizations...")
        
        # 1. Coherence by structure
        plt.figure(figsize=(10, 6))
        structure_data = []
        structure_labels = []
        for structure in ['linear', 'nonlinear']:
            data = self.experiment_data[self.experiment_data['structure'] == structure]['avg_coherence'].dropna()
            structure_data.append(data)
            structure_labels.append(structure.title())
        
        plt.boxplot(structure_data, tick_labels=structure_labels)
        plt.title('Coherence Distribution by Story Structure')
        plt.xlabel('Story Structure')
        plt.ylabel('Average Coherence')
        plt.grid(True, alpha=0.3)
        plt.savefig('/Users/haha/Story/AAA/coherence_analysis/coherence_by_structure_boxplot_en.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Coherence by genre
        plt.figure(figsize=(10, 6))
        genre_data = []
        genre_labels = []
        for genre in ['sciencefiction', 'horror', 'romantic']:
            data = self.experiment_data[self.experiment_data['genre'] == genre]['avg_coherence'].dropna()
            if len(data) > 0:
                genre_data.append(data)
                genre_labels.append(genre.title())
        
        plt.boxplot(genre_data, tick_labels=genre_labels)
        plt.title('Coherence Distribution by Story Genre')
        plt.xlabel('Story Genre')
        plt.ylabel('Average Coherence')
        plt.grid(True, alpha=0.3)
        plt.savefig('/Users/haha/Story/AAA/coherence_analysis/coherence_by_genre_boxplot_en.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Coherence vs Diversity scatter plot
        analysis_data = self.experiment_data.dropna(subset=['avg_coherence', 'diversity_group_score'])
        if len(analysis_data) > 0:
            plt.figure(figsize=(10, 8))
            
            # Color by genre
            genres = analysis_data['genre'].unique()
            colors = plt.cm.Set3(np.linspace(0, 1, len(genres)))
            
            for i, genre in enumerate(genres):
                genre_data = analysis_data[analysis_data['genre'] == genre]
                plt.scatter(genre_data['avg_coherence'], genre_data['diversity_group_score'], 
                           c=[colors[i]], label=genre.title(), alpha=0.7, s=50)
            
            # Add trend line
            z = np.polyfit(analysis_data['avg_coherence'], analysis_data['diversity_group_score'], 1)
            p = np.poly1d(z)
            plt.plot(analysis_data['avg_coherence'].sort_values(), 
                     p(analysis_data['avg_coherence'].sort_values()), "r--", alpha=0.8)
            
            plt.xlabel('Average Coherence')
            plt.ylabel('Diversity Group Score')
            plt.title('Coherence vs Diversity Trade-off Analysis')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig('/Users/haha/Story/AAA/coherence_analysis/coherence_vs_diversity_scatter_en.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 4. Coherence distribution histogram
        plt.figure(figsize=(10, 6))
        coherence_data = self.experiment_data['avg_coherence'].dropna()
        plt.hist(coherence_data, bins=20, alpha=0.7, edgecolor='black')
        plt.axvline(self.COHERENT_THRESHOLD, color='red', linestyle='--', label=f'Coherent threshold ({self.COHERENT_THRESHOLD})')
        plt.axvline(coherence_data.mean(), color='green', linestyle='-', label=f'Mean ({coherence_data.mean():.3f})')
        plt.xlabel('Average Coherence')
        plt.ylabel('Frequency')
        plt.title('Distribution of Coherence Scores')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('/Users/haha/Story/AAA/coherence_analysis/coherence_distribution_histogram_en.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 5. Coherence stability histogram  
        plt.figure(figsize=(10, 6))
        std_data = self.experiment_data['coherence_std'].dropna()
        plt.hist(std_data, bins=20, alpha=0.7, edgecolor='black')
        plt.axvline(self.STABLE_STD_THRESHOLD, color='red', linestyle='--', label=f'Stable threshold ({self.STABLE_STD_THRESHOLD})')
        plt.axvline(std_data.mean(), color='green', linestyle='-', label=f'Mean ({std_data.mean():.3f})')
        plt.xlabel('Coherence Standard Deviation')
        plt.ylabel('Frequency')
        plt.title('Distribution of Coherence Stability')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('/Users/haha/Story/AAA/coherence_analysis/coherence_stability_histogram_en.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 6. Temperature effect on coherence
        temp_data = self.experiment_data.dropna(subset=['temperature', 'avg_coherence'])
        if len(temp_data) > 0:
            plt.figure(figsize=(10, 6))
            
            # Group by temperature
            temp_groups = temp_data.groupby('temperature')['avg_coherence'].agg(['mean', 'std'])
            temp_values = temp_groups.index
            mean_coherence = temp_groups['mean']
            std_coherence = temp_groups['std']
            
            plt.errorbar(temp_values, mean_coherence, yerr=std_coherence, 
                        marker='o', capsize=5, capthick=2, elinewidth=2)
            plt.xlabel('Temperature Parameter')
            plt.ylabel('Average Coherence')
            plt.title('Effect of Temperature on Coherence')
            plt.grid(True, alpha=0.3)
            plt.savefig('/Users/haha/Story/AAA/coherence_analysis/temperature_effect_coherence_en.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print("Created 6 visualization plots in /Users/haha/Story/AAA/coherence_analysis")
    
    def generate_interpretations(self, stats_dict, structure_results, interaction_results):
        """Generate human-readable interpretations"""
        interpretations = []
        
        # Overall coherence quality
        coherent_pct = stats_dict['overall']['coherent_percentage']
        if coherent_pct >= 90:
            interpretations.append(f"✅ EXCELLENT: {coherent_pct:.1f}% of stories are coherent (above {self.COHERENT_THRESHOLD})")
        elif coherent_pct >= 70:
            interpretations.append(f"✅ GOOD: {coherent_pct:.1f}% of stories are coherent (above {self.COHERENT_THRESHOLD})")
        else:
            interpretations.append(f"⚠️ NEEDS IMPROVEMENT: Only {coherent_pct:.1f}% of stories are coherent (above {self.COHERENT_THRESHOLD})")
        
        # Stability
        stable_pct = stats_dict['overall']['stable_percentage']
        if stable_pct >= 80:
            interpretations.append(f"✅ STABLE: {stable_pct:.1f}% of stories have stable coherence (std < {self.STABLE_STD_THRESHOLD})")
        else:
            interpretations.append(f"⚠️ UNSTABLE: Only {stable_pct:.1f}% of stories have stable coherence (std < {self.STABLE_STD_THRESHOLD})")
        
        # Interaction analysis
        if 'correlation' in interaction_results:
            corr_strength = interaction_results['correlation']['strength']
            corr_direction = interaction_results['correlation']['direction']
            corr_value = interaction_results['correlation']['pearson_r']
            interpretations.append(f"🔗 DIVERSITY INTERACTION: {corr_strength.title()} {corr_direction} correlation between coherence and diversity (r={corr_value:.3f})")
        
        return interpretations
    
    def generate_recommendations(self, stats_dict, structure_results):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Structure-based recommendations
        if 'statistical_test' in structure_results:
            linear_mean = structure_results['statistical_test']['linear_mean']
            nonlinear_mean = structure_results['statistical_test']['nonlinear_mean']
            
            if linear_mean > nonlinear_mean and structure_results['statistical_test']['significant']:
                recommendations.append("STRUCTURE FOCUS: Nonlinear stories show lower coherence - may need specialized coherence techniques")
            elif nonlinear_mean > linear_mean and structure_results['statistical_test']['significant']:
                recommendations.append("STRUCTURE FOCUS: Linear stories show lower coherence - consider improving linear narrative flow")
        
        # Genre-based recommendations
        genre_means = {}
        for genre in ['sciencefiction', 'horror', 'romantic']:
            genre_key = f'{genre}_genre'
            if genre_key in stats_dict:
                genre_means[genre] = stats_dict[genre_key]['mean_coherence']
        
        if genre_means:
            lowest_genre = min(genre_means.keys(), key=lambda x: genre_means[x])
            recommendations.append(f"GENRE OPTIMIZATION: {lowest_genre.title()} stories have lowest coherence - focus improvement efforts here")
        
        return recommendations
    
    def run_complete_analysis(self):
        """Run complete coherence analysis"""
        print("🔍 Starting Comprehensive Coherence Analysis")
        print("=" * 60)
        
        # Run all analyses
        stats_dict = self.basic_statistics()
        structure_results = self.structure_analysis()
        interaction_results = self.coherence_diversity_interaction()
        
        # Generate interpretations and recommendations
        interpretations = self.generate_interpretations(stats_dict, structure_results, interaction_results)
        recommendations = self.generate_recommendations(stats_dict, structure_results)
        
        # Create visualizations
        self.create_visualizations()
        
        # Compile results
        results = {
            'analysis_info': {
                'timestamp': pd.Timestamp.now().isoformat(),
                'data_source': 'metrics_master_clean.csv',
                'analyzer_version': '1.0',
                'evaluation_criteria': {
                    'coherent_threshold': self.COHERENT_THRESHOLD,
                    'stable_std_threshold': self.STABLE_STD_THRESHOLD
                }
            },
            'basic_statistics': stats_dict,
            'structure_analysis': structure_results,
            'coherence_diversity_interaction': interaction_results,
            'validation': self.validate_results(),
            'interpretations': interpretations,
            'recommendations': recommendations
        }
        
        # Save results
        output_path = '/Users/haha/Story/AAA/coherence_analysis/coherence_analysis_report_en.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Generate summary
        self.generate_summary(results)
        
        print("\n✅ Analysis complete! Results saved to:", output_path)
        return results
    
    def validate_results(self):
        """Validate analysis results for sanity checks"""
        coherence_data = self.experiment_data['avg_coherence'].dropna()
        
        validation = {
            'value_range': {
                'min_value': float(coherence_data.min()),
                'max_value': float(coherence_data.max()),
                'within_expected_range': bool(coherence_data.min() >= 0 and coherence_data.max() <= 1),
                'realistic_range': bool(coherence_data.min() > 0.1 and coherence_data.max() < 1.0)
            },
            'consistency_checks': {},
            'total_consistency_issues': 0,
            'structure_health': {
                'total_stories': len(self.experiment_data),
                'healthy_structure_count': 0,
                'healthy_percentage': 0.0
            }
        }
        
        return validation
    
    def generate_summary(self, results):
        """Generate markdown summary"""
        summary_path = '/Users/haha/Story/AAA/coherence_analysis/coherence_analysis_summary_en.md'
        
        with open(summary_path, 'w') as f:
            f.write("# Coherence Analysis Summary\n\n")
            f.write(f"**Generated:** {results['analysis_info']['timestamp'][:19]}\n\n")
            
            f.write("## Key Findings\n\n")
            overall = results['basic_statistics']['overall']
            f.write(f"- **Total Stories Analyzed:** {overall['count']}\n")
            f.write(f"- **Average Coherence:** {overall['mean_coherence']:.4f}\n") 
            f.write(f"- **Coherent Stories:** {overall['coherent_stories']}/{overall['count']} ({overall['coherent_percentage']:.1f}%)\n")
            f.write(f"- **Stable Stories:** {overall['stable_stories']}/{overall['count']} ({overall['stable_percentage']:.1f}%)\n\n")
            
            f.write("## Interpretations\n\n")
            for interpretation in results['interpretations']:
                f.write(f"- {interpretation}\n")
            f.write("\n")
            
            if results['recommendations']:
                f.write("## Recommendations\n\n")
                for rec in results['recommendations']:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            f.write("## Files Generated\n\n")
            f.write("- `coherence_analysis_report_en.json`: Complete analysis data\n")
            f.write("- `coherence_by_structure_boxplot_en.png`: Coherence comparison by story structure\n")
            f.write("- `coherence_by_genre_boxplot_en.png`: Coherence comparison by genre\n")
            f.write("- `coherence_vs_diversity_scatter_en.png`: Coherence-diversity trade-off analysis\n")
            f.write("- `coherence_distribution_histogram_en.png`: Distribution of coherence scores\n")
            f.write("- `coherence_stability_histogram_en.png`: Coherence stability analysis\n")
            f.write("- `temperature_effect_coherence_en.png`: Temperature parameter effect on coherence\n")
        
        print(f"Summary saved to: {summary_path}")

if __name__ == "__main__":
    analyzer = CoherenceAnalyzer('/Users/haha/Story/metrics_master_clean.csv')
    results = analyzer.run_complete_analysis()
    
    print(f"\nGenerated files:")
    print(f"  - coherence_analysis_report_en.json")
    print(f"  - coherence_analysis_summary_en.md") 
    print(f"  - coherence_by_structure_boxplot_en.png")
    print(f"  - coherence_by_genre_boxplot_en.png")
    print(f"  - coherence_vs_diversity_scatter_en.png")
    print(f"  - coherence_distribution_histogram_en.png")
    print(f"  - coherence_stability_histogram_en.png")
    print(f"  - temperature_effect_coherence_en.png")
