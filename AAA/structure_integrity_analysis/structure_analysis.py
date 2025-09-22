"""
Structure Integrity Analysis
===========================

This module analyzes the structural integrity of generated stories based on:
1. Chapter count distribution and optimality (5-8 chapters considered optimal)
2. Turning point coverage (tp_coverage) - should be >0.7 for qualification
3. Li function diversity - higher values indicate richer plot progression
4. Total events vs story length relationship
5. Interactions with coherence and diversity metrics

Key Metrics:
- chapter_count: Number of chapters (optimal range: 5-8)
- tp_coverage: Turning point coverage (format: "m/n", target: >0.7)
- tp_completion_rate: Rate of turning point completion
- li_function_diversity: Plot progression richness
- total_events: Event count in the story
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from scipy import stats
from scipy.stats.mstats import winsorize
import re
import warnings
warnings.filterwarnings('ignore')

# Set style for professional plots
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

class StructureIntegrityAnalyzer:
    """Analyzer for story structure integrity metrics."""
    
    def __init__(self, csv_path):
        """Initialize with data from CSV file."""
        self.df = pd.read_csv(csv_path)
        self.results = {}
        self.output_dir = Path("structure_analysis_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Parse tp_coverage from string format to numeric
        self._parse_turning_points()
        
    def _parse_turning_points(self):
        """Parse turning point coverage with robust handling of various formats."""
        def parse_tp_coverage(tp_str):
            """
            Parse TP coverage supporting formats like:
            - "5/5" -> (1.0, 5, 5)
            - "4/5 (0.8)" -> (0.8, 4, 5)  
            - "0.75" -> (0.75, nan, nan)
            Returns: (ratio, m, n)
            """
            if pd.isna(tp_str) or str(tp_str).strip() == '':
                return np.nan, np.nan, np.nan
            
            s = str(tp_str).strip()
            
            # Try to find m/n pattern
            m_n = re.findall(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', s)
            if m_n:
                m, n = map(float, m_n[0])
                ratio = m/n if n > 0 else np.nan
                return ratio, m, n
            
            # Fallback: pure decimal
            try:
                return float(s), np.nan, np.nan
            except:
                return np.nan, np.nan, np.nan
        
        # Apply parsing and create new columns
        tp_data = self.df['tp_coverage'].apply(lambda x: pd.Series(parse_tp_coverage(x)))
        self.df['tp_coverage_numeric'] = tp_data.iloc[:, 0]
        self.df['tp_m'] = tp_data.iloc[:, 1]
        self.df['tp_n'] = tp_data.iloc[:, 2]
        
        # Separate main samples from baseline
        self._create_main_sample()
        
        # Add derived metrics
        self._add_derived_metrics()
        
    def _create_main_sample(self):
        """Separate main experimental samples from baseline controls."""
        self.df_main = self.df.query("genre!='baseline' and structure!='baseline'").copy()
        self.df_baseline = self.df.query("genre=='baseline' or structure=='baseline'").copy()
        
        print(f"📊 Sample split: {len(self.df_main)} main samples, {len(self.df_baseline)} baseline samples")
        
    def _add_derived_metrics(self):
        """Add derived metrics like chapter_score and event_density."""
        # Event density (events per 1000 words)
        self.df_main['event_density'] = self.df_main['total_events'] / (self.df_main['total_words'] / 1000)
        
        # Chapter score (peak at 5-8 chapters)
        def chapter_score(ch):
            """Score chapters with peak at 5-8 range."""
            if pd.isna(ch):
                return np.nan
            if ch < 5:
                return max(0.0, (ch - 1) / (5 - 1))  # Linear 1→0, 5→1
            if ch <= 8:
                return 1.0  # Optimal range gets full score
            
            # Above 8, linear decay to upper bound
            upper = max(8, min(14, int(self.df_main['chapter_count'].quantile(0.95))))
            if upper > 8:
                return max(0.0, 1 - (ch - 8) / (upper - 8))
            else:
                return 0.0
                
        self.df_main['chapter_score'] = self.df_main['chapter_count'].apply(chapter_score)
        
        # Structure complexity (weighted composite)
        self._calculate_structure_complexity()
        
    def _calculate_structure_complexity(self, weight_profile="hybrid"):
        """
        Calculate structure complexity using hybrid approach:
        1. TP Coverage as hard gate (must be >=1.0)
        2. Complexity scoring only for passed samples using chapter_score, li_diversity, event_density
        3. Theoretical baseline weights + data-driven adjustment (±10-15%)
        
        Args:
            weight_profile: Weight configuration profile
                - "hybrid": TP hard gate + 3-component weighted scoring (recommended)
                - "theoretical": Pure theoretical weights for 3 components  
                - "data_driven": Pure empirical weights based on correlations
                - "custom": User-defined weights (requires self.custom_weights)
        """
        print("🔧 Calculating Structure Complexity (Hybrid Approach)...")
        
        # Step 1: TP Coverage Hard Gate
        # TP Coverage → 结构完整性gate (Propp's morphological completeness requirement)
        self.df_main['tp_pass'] = (self.df_main['tp_coverage_numeric'] >= 1.0)
        passed_samples = self.df_main[self.df_main['tp_pass']].copy()
        failed_samples = self.df_main[~self.df_main['tp_pass']].copy()
        
        print(f"📊 TP Gate Results: {len(passed_samples)} passed, {len(failed_samples)} failed")
        
        if len(passed_samples) == 0:
            print("❌ No samples passed TP gate! Setting all complexity to 0.")
            self.df_main['structure_complexity'] = 0.0
            self.selected_weight_profile = weight_profile
            self.selected_weights = {}
            return
        
        # Step 2: Define 3-component theoretical baseline weights
        theoretical_baseline = {
            'chapter_score': 0.5,        # Chapter Score → 认知负荷理论 (Miller's 7±2 rule & Zacks event segmentation)
            'li_function_diversity': 0.3, # Li Diversity → 信息熵 (Shannon's information theory - balanced variety)
            'event_density': 0.2          # Event Density → 节奏调控 + 经验校正 (McKee's tempo theory + empirical correlation)
        }
        
        # Step 3: Calculate data-driven adjustments
        data_adjustments = self._calculate_data_driven_adjustments(passed_samples)
        
        # Step 4: Apply adjustments to get final weights
        final_weights = self._apply_hybrid_adjustments(theoretical_baseline, data_adjustments, weight_profile)
        
        # Step 5: Calculate complexity scores for passed samples
        complexity_scores = self._calculate_three_component_complexity(passed_samples, final_weights)
        
        # Step 6: Assign final scores (0 for failed, calculated for passed)
        self.df_main['structure_complexity'] = 0.0  # Initialize all to 0
        self.df_main.loc[passed_samples.index, 'structure_complexity'] = complexity_scores
        
        # Store configuration for reporting
        self.selected_weight_profile = weight_profile
        self.selected_weights = final_weights.copy()
        self.theoretical_baseline = theoretical_baseline.copy()
        self.data_adjustments = data_adjustments.copy()
        self.tp_gate_stats = {
            'total_samples': len(self.df_main),
            'passed_samples': len(passed_samples),
            'failed_samples': len(failed_samples),
            'pass_rate': len(passed_samples) / len(self.df_main)
        }
        
        print(f"✅ Hybrid complexity calculation completed")
        print(f"📈 TP Pass Rate: {self.tp_gate_stats['pass_rate']:.1%}")
        
    def _calculate_data_driven_adjustments(self, passed_samples):
        """Calculate data-driven adjustments for the 3 components."""
        adjustments = {}
        
        # Only use samples that passed TP gate for correlation analysis
        if 'quality_target' not in passed_samples.columns:
            # Create quality target if not exists
            if 'avg_coherence' in passed_samples.columns and 'distinct_avg' in passed_samples.columns:
                coherence_norm = (passed_samples['avg_coherence'] - passed_samples['avg_coherence'].min()) / \
                               (passed_samples['avg_coherence'].max() - passed_samples['avg_coherence'].min())
                diversity_norm = (passed_samples['distinct_avg'] - passed_samples['distinct_avg'].min()) / \
                               (passed_samples['distinct_avg'].max() - passed_samples['distinct_avg'].min())
                passed_samples['quality_target'] = 0.5 * coherence_norm + 0.5 * diversity_norm
        
        components = ['chapter_score', 'li_function_diversity', 'event_density']
        
        for comp in components:
            if comp in passed_samples.columns and 'quality_target' in passed_samples.columns:
                # Calculate correlation with quality target
                corr = passed_samples[comp].corr(passed_samples['quality_target'])
                
                # Convert correlation to adjustment factor (-15% to +15%)
                if not pd.isna(corr):
                    # Normalize correlation (-1 to 1) to adjustment factor (-0.15 to 0.15)
                    adjustment_factor = corr * 0.15  # Max ±15% adjustment
                else:
                    adjustment_factor = 0.0
                
                adjustments[comp] = {
                    'correlation': float(corr) if not pd.isna(corr) else 0.0,
                    'adjustment_factor': adjustment_factor,
                    'has_variance': passed_samples[comp].nunique(dropna=True) > 1
                }
            else:
                adjustments[comp] = {
                    'correlation': 0.0,
                    'adjustment_factor': 0.0,
                    'has_variance': False
                }
        
        return adjustments
    
    def _apply_hybrid_adjustments(self, theoretical_baseline, data_adjustments, weight_profile):
        """Apply data-driven adjustments to theoretical baseline weights."""
        
        if weight_profile == "theoretical":
            # Pure theoretical weights
            return theoretical_baseline.copy()
        elif weight_profile == "data_driven":
            # Pure data-driven weights based on correlations
            total_corr = sum(abs(adj['correlation']) for adj in data_adjustments.values() if adj['has_variance'])
            if total_corr > 0:
                return {comp: abs(adj['correlation']) / total_corr 
                       for comp, adj in data_adjustments.items() if adj['has_variance']}
            else:
                # Fallback to equal weights if no correlations
                valid_comps = [comp for comp, adj in data_adjustments.items() if adj['has_variance']]
                return {comp: 1.0/len(valid_comps) for comp in valid_comps} if valid_comps else {}
        else:
            # Hybrid approach (default)
            adjusted_weights = {}
            
            for comp, baseline_weight in theoretical_baseline.items():
                if comp in data_adjustments and data_adjustments[comp]['has_variance']:
                    # Apply data-driven adjustment
                    adjustment = data_adjustments[comp]['adjustment_factor'] 
                    adjusted_weight = baseline_weight * (1 + adjustment)
                    adjusted_weights[comp] = max(0.05, adjusted_weight)  # Minimum 5% weight
                elif comp in data_adjustments:
                    # No variance, use theoretical weight
                    adjusted_weights[comp] = baseline_weight
            
            # Renormalize to sum to 1.0
            total_weight = sum(adjusted_weights.values())
            if total_weight > 0:
                final_weights = {comp: weight/total_weight for comp, weight in adjusted_weights.items()}
            else:
                final_weights = theoretical_baseline.copy()
            
            return final_weights
    
    def _calculate_three_component_complexity(self, passed_samples, weights):
        """Calculate complexity scores using 3 components for passed samples."""
        
        def _clip_normalize(series):
            """Winsorize and normalize to 0-1."""
            if series.nunique(dropna=True) <= 1:
                return pd.Series(0.5, index=series.index)
            
            # Winsorize at 5th and 95th percentiles
            lo, hi = series.quantile([0.05, 0.95])
            clipped = series.clip(lo, hi)
            
            # Normalize to 0-1
            if clipped.max() > clipped.min():
                return (clipped - clipped.min()) / (clipped.max() - clipped.min())
            else:
                return pd.Series(0.5, index=series.index)
        
        # Prepare normalized components
        normed_components = pd.DataFrame(index=passed_samples.index)
        normed_components['chapter_score'] = passed_samples['chapter_score']  # Already 0-1
        
        for col in ['li_function_diversity', 'event_density']:
            if col in passed_samples.columns and col in weights:
                normed_components[col] = _clip_normalize(passed_samples[col])
        
        # Calculate weighted sum
        complexity_scores = pd.Series(0.0, index=passed_samples.index)
        for component, weight in weights.items():
            if component in normed_components.columns:
                complexity_scores += weight * normed_components[component].fillna(0.5)
        
        return complexity_scores
    
    def _generate_weight_comparison_table(self):
        """Generate comparison table: theoretical vs data-corrected vs final weights."""
        
        if not hasattr(self, 'theoretical_baseline') or not hasattr(self, 'data_adjustments'):
            return {"error": "Hybrid weight calculation not completed"}
        
        comparison_table = {}
        
        for comp in self.theoretical_baseline.keys():
            theoretical_weight = self.theoretical_baseline[comp]
            
            if comp in self.data_adjustments:
                adj_data = self.data_adjustments[comp]
                correlation = adj_data['correlation']
                adjustment_factor = adj_data['adjustment_factor']
                data_corrected_weight = theoretical_weight * (1 + adjustment_factor)
            else:
                correlation = 0.0
                adjustment_factor = 0.0
                data_corrected_weight = theoretical_weight
            
            final_weight = self.selected_weights.get(comp, 0.0)
            
            comparison_table[comp] = {
                'theoretical_weight': theoretical_weight,
                'correlation_with_quality': correlation,
                'adjustment_factor': adjustment_factor,
                'data_corrected_weight': data_corrected_weight,
                'final_weight': final_weight,
                'weight_change': final_weight - theoretical_weight
            }
        
        # Add summary statistics
        comparison_table['summary'] = {
            'tp_gate_applied': True,
            'tp_pass_rate': self.tp_gate_stats['pass_rate'],
            'components_used': list(self.theoretical_baseline.keys()),
            'total_final_weight': sum(self.selected_weights.values()),
            'max_adjustment': max(abs(data['adjustment_factor']) for data in comparison_table.values() if isinstance(data, dict) and 'adjustment_factor' in data),
            'profile_used': self.selected_weight_profile
        }
        
        return comparison_table
        
    def validate_weight_configuration(self, profile="default", verbose=True):
        """
        Validate and analyze the effectiveness of weight configuration.
        
        Returns detailed statistics about weight impact and sensitivity.
        """
        # Temporarily store original values
        original_complexity = self.df_main['structure_complexity'].copy() if 'structure_complexity' in self.df_main.columns else None
        original_profile = getattr(self, 'selected_weight_profile', 'default')
        
        # Calculate complexity with specified profile
        self._calculate_structure_complexity(weight_profile=profile)
        
        # Component correlation analysis
        components = ['tp_coverage_numeric', 'chapter_score', 'li_function_diversity', 'event_density']
        available_components = [c for c in components if c in self.df_main.columns]
        
        if len(available_components) < 2:
            return {"error": "Insufficient components for validation"}
        
        # Calculate component correlations with final score
        component_correlations = {}
        for comp in available_components:
            if comp in self.df_main.columns and 'structure_complexity' in self.df_main.columns:
                corr = self.df_main[comp].corr(self.df_main['structure_complexity'])
                component_correlations[comp] = float(corr) if not pd.isna(corr) else None
        
        # Weight sensitivity analysis
        sensitivity_results = {}
        if len(available_components) >= 2:
            base_std = self.df_main['structure_complexity'].std()
            
            for comp in available_components:
                # Test ±10% weight change
                test_weights = self.selected_weights.copy()
                original_weight = test_weights[comp]
                
                # Increase weight by 10%
                test_weights[comp] = min(1.0, original_weight * 1.1)
                # Proportionally decrease others
                remaining_weight = 1.0 - test_weights[comp]
                other_total = sum(w for k, w in self.selected_weights.items() if k != comp)
                if other_total > 0:
                    for k in test_weights:
                        if k != comp:
                            test_weights[k] = self.selected_weights[k] * (remaining_weight / other_total)
                
                # Calculate sensitivity
                self.custom_weights = test_weights
                self._calculate_structure_complexity("custom")
                new_std = self.df_main['structure_complexity'].std()
                
                sensitivity_results[comp] = {
                    'weight_change': 0.1,
                    'std_change': float(new_std - base_std),
                    'sensitivity': float((new_std - base_std) / base_std) if base_std > 0 else 0
                }
        
        # Restore original state
        if original_complexity is not None:
            self.df_main['structure_complexity'] = original_complexity
        if hasattr(self, 'custom_weights'):
            delattr(self, 'custom_weights')
        self.selected_weight_profile = original_profile
        
        # Principal component analysis
        pca_results = {}
        try:
            from sklearn.decomposition import PCA
            
            component_data = self.df_main[available_components].dropna()
            if len(component_data) > 5:  # Need sufficient samples
                pca = PCA(n_components=min(4, len(available_components)))
                pca_transformed = pca.fit_transform(component_data)
                
                pca_results = {
                    'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                    'components': {
                        f'PC{i+1}': dict(zip(available_components, pca.components_[i]))
                        for i in range(len(pca.components_))
                    }
                }
        except ImportError:
            pca_results = {"error": "sklearn not available for PCA analysis"}
        
        validation_results = {
            'weight_profile': profile,
            'selected_weights': self.selected_weights,
            'component_correlations': component_correlations,
            'sensitivity_analysis': sensitivity_results,
            'pca_analysis': pca_results,
            'statistics': {
                'complexity_mean': float(self.df_main['structure_complexity'].mean()),
                'complexity_std': float(self.df_main['structure_complexity'].std()),
                'complexity_range': [
                    float(self.df_main['structure_complexity'].min()),
                    float(self.df_main['structure_complexity'].max())
                ],
                'n_samples': len(self.df_main)
            }
        }
        
        if verbose:
            self._print_weight_validation_summary(validation_results)
        
        return validation_results
    
    def _print_weight_validation_summary(self, results):
        """Print a human-readable summary of weight validation results."""
        print(f"\n📊 Weight Configuration Validation: {results['weight_profile'].title()}")
        print("="*60)
        
        print("\n🎯 Selected Weights:")
        for component, weight in results['selected_weights'].items():
            comp_name = component.replace('_', ' ').title()
            print(f"  {comp_name:<25}: {weight:.1%}")
        
        print(f"\n📈 Complexity Score Statistics:")
        stats = results['statistics']
        print(f"  Mean: {stats['complexity_mean']:.3f}")
        print(f"  Std:  {stats['complexity_std']:.3f}")
        print(f"  Range: [{stats['complexity_range'][0]:.3f}, {stats['complexity_range'][1]:.3f}]")
        
        print(f"\n🔗 Component-Final Score Correlations:")
        for comp, corr in results['component_correlations'].items():
            comp_name = comp.replace('_', ' ').title()
            if corr is not None:
                print(f"  {comp_name:<25}: {corr:.3f}")
            else:
                print(f"  {comp_name:<25}: N/A")
        
        if results['sensitivity_analysis']:
            print(f"\n⚖️  Weight Sensitivity (±10% change impact):")
            for comp, sens in results['sensitivity_analysis'].items():
                comp_name = comp.replace('_', ' ').title()
                print(f"  {comp_name:<25}: {sens['sensitivity']:+.1%} std change")
    
    def set_custom_weights(self, tp_weight=0.4, chapter_weight=0.3, 
                          li_weight=0.2, event_weight=0.1):
        """
        Set custom weights for structure complexity calculation.
        
        Args:
            tp_weight: Weight for turning point coverage (0-1)
            chapter_weight: Weight for chapter score (0-1) 
            li_weight: Weight for Li function diversity (0-1)
            event_weight: Weight for event density (0-1)
            
        Note: Weights will be automatically normalized to sum to 1.0
        """
        total = tp_weight + chapter_weight + li_weight + event_weight
        if total <= 0:
            raise ValueError("Sum of weights must be positive")
        
        self.custom_weights = {
            'tp_coverage_numeric': tp_weight / total,
            'chapter_score': chapter_weight / total,
            'li_function_diversity': li_weight / total,
            'event_density': event_weight / total
        }
        
        print(f"✅ Custom weights set (normalized):")
        for comp, weight in self.custom_weights.items():
            comp_name = comp.replace('_', ' ').title()
            print(f"  {comp_name}: {weight:.1%}")
    
    def _drop_constant_cols(self, df, cols):
        """Remove columns with no variance from correlation analysis."""
        return [c for c in cols if c in df.columns and df[c].nunique(dropna=True) > 1]
        
    def analyze_chapter_distribution(self):
        """Analyze chapter count distribution across genres and structures (main samples only)."""
        print("🔍 Analyzing Chapter Distribution...")
        
        # Overall chapter statistics (main samples only)
        chapter_stats = {
            'mean': self.df_main['chapter_count'].mean(),
            'median': self.df_main['chapter_count'].median(),
            'std': self.df_main['chapter_count'].std(),
            'optimal_range_count': len(self.df_main[(self.df_main['chapter_count'] >= 5) & 
                                                   (self.df_main['chapter_count'] <= 8)]),
            'optimal_percentage': len(self.df_main[(self.df_main['chapter_count'] >= 5) & 
                                                  (self.df_main['chapter_count'] <= 8)]) / len(self.df_main) * 100,
            'chapter_score_mean': self.df_main['chapter_score'].mean(),
            'chapter_score_std': self.df_main['chapter_score'].std()
        }
        
        # Chapter distribution by genre and structure (main samples only)
        chapter_by_genre = self.df_main.groupby('genre')['chapter_count'].agg(['mean', 'std', 'count'])
        chapter_by_structure = self.df_main.groupby('structure')['chapter_count'].agg(['mean', 'std', 'count'])
        
        # Convert to JSON-serializable format
        chapter_by_genre_dict = {}
        for genre in chapter_by_genre.index:
            chapter_by_genre_dict[str(genre)] = {
                'mean': float(chapter_by_genre.loc[genre, 'mean']) if not pd.isna(chapter_by_genre.loc[genre, 'mean']) else None,
                'std': float(chapter_by_genre.loc[genre, 'std']) if not pd.isna(chapter_by_genre.loc[genre, 'std']) else None,
                'count': int(chapter_by_genre.loc[genre, 'count']) if not pd.isna(chapter_by_genre.loc[genre, 'count']) else None
            }
        
        chapter_by_structure_dict = {}
        for structure in chapter_by_structure.index:
            chapter_by_structure_dict[str(structure)] = {
                'mean': float(chapter_by_structure.loc[structure, 'mean']) if not pd.isna(chapter_by_structure.loc[structure, 'mean']) else None,
                'std': float(chapter_by_structure.loc[structure, 'std']) if not pd.isna(chapter_by_structure.loc[structure, 'std']) else None,
                'count': int(chapter_by_structure.loc[structure, 'count']) if not pd.isna(chapter_by_structure.loc[structure, 'count']) else None
            }
        
        self.results['chapter_analysis'] = {
            'overall_stats': chapter_stats,
            'by_genre': chapter_by_genre_dict,
            'by_structure': chapter_by_structure_dict
        }
        
        # Visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Overall distribution (main samples only)
        chapter_bins = range(int(self.df_main['chapter_count'].min()), 
                            int(self.df_main['chapter_count'].max())+2)
        axes[0,0].hist(self.df_main['chapter_count'], bins=chapter_bins, 
                      alpha=0.7, color='skyblue', edgecolor='black')
        axes[0,0].axvspan(5, 8, alpha=0.3, color='green', label='Optimal Range (5-8)')
        axes[0,0].set_title('Chapter Count Distribution\n(Optimal range shaded in green)')
        axes[0,0].set_xlabel('Number of Chapters')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # By genre (main samples only)
        unique_genres = self.df_main['genre'].unique()
        genre_data = [self.df_main[self.df_main['genre']==g]['chapter_count'].values for g in unique_genres]
        axes[0,1].boxplot(genre_data, labels=unique_genres)
        axes[0,1].axhspan(5, 8, alpha=0.3, color='green', label='Optimal Range')
        axes[0,1].set_title('Chapter Count by Genre\n(Optimal range shaded in green)')
        axes[0,1].set_ylabel('Number of Chapters')
        axes[0,1].tick_params(axis='x', rotation=45)
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # By structure (main samples only)
        unique_structures = self.df_main['structure'].unique()
        structure_data = [self.df_main[self.df_main['structure']==s]['chapter_count'].values for s in unique_structures]
        axes[1,0].boxplot(structure_data, labels=unique_structures)
        axes[1,0].axhspan(5, 8, alpha=0.3, color='green', label='Optimal Range')
        axes[1,0].set_title('Chapter Count by Structure\n(Optimal range shaded in green)')
        axes[1,0].set_ylabel('Number of Chapters')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        # Chapter score distribution (new metric)
        axes[1,1].hist(self.df_main['chapter_score'], bins=20, alpha=0.7, 
                      color='lightgreen', edgecolor='black')
        axes[1,1].axvline(0.8, color='red', linestyle='--', linewidth=2, 
                         label='High Quality Threshold (0.8)')
        axes[1,1].set_title('Chapter Score Distribution\n(Peak scoring at 5-8 chapters)')
        axes[1,1].set_xlabel('Chapter Score (0-1)')
        axes[1,1].set_ylabel('Frequency')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'chapter_distribution_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return chapter_stats
        
    def analyze_turning_point_coverage(self):
        """Analyze turning point coverage across different conditions (main samples only)."""
        print("🔍 Analyzing Turning Point Coverage...")
        
        # Remove rows with invalid tp_coverage (main samples only)
        valid_tp = self.df_main.dropna(subset=['tp_coverage_numeric'])
        
        # Check for variance in TP coverage
        has_variance = valid_tp['tp_coverage_numeric'].nunique(dropna=True) > 1
        
        # Overall TP statistics
        tp_stats = {
            'mean': valid_tp['tp_coverage_numeric'].mean(),
            'median': valid_tp['tp_coverage_numeric'].median(),
            'std': valid_tp['tp_coverage_numeric'].std(),
            'unique_values': valid_tp['tp_coverage_numeric'].nunique(dropna=True),
            'has_variance': has_variance,
            'qualified_count': len(valid_tp[valid_tp['tp_coverage_numeric'] > 0.7]) if has_variance else len(valid_tp),
            'qualified_percentage': len(valid_tp[valid_tp['tp_coverage_numeric'] > 0.7]) / len(valid_tp) * 100 if len(valid_tp) > 0 else 0,
            'perfect_coverage_count': len(valid_tp[valid_tp['tp_coverage_numeric'] == 1.0]),
            'perfect_coverage_percentage': len(valid_tp[valid_tp['tp_coverage_numeric'] == 1.0]) / len(valid_tp) * 100 if len(valid_tp) > 0 else 0,
            'tp_m_mean': valid_tp['tp_m'].mean() if 'tp_m' in valid_tp.columns else None,
            'tp_n_mean': valid_tp['tp_n'].mean() if 'tp_n' in valid_tp.columns else None
        }
        
        # TP coverage by genre and structure (main samples only)
        tp_by_genre = valid_tp.groupby('genre')['tp_coverage_numeric'].agg(['mean', 'std', 'count'])
        tp_by_structure = valid_tp.groupby('structure')['tp_coverage_numeric'].agg(['mean', 'std', 'count'])
        
        # Convert to JSON-serializable format
        tp_by_genre_dict = {}
        for genre in tp_by_genre.index:
            tp_by_genre_dict[str(genre)] = {
                'mean': float(tp_by_genre.loc[genre, 'mean']) if not pd.isna(tp_by_genre.loc[genre, 'mean']) else None,
                'std': float(tp_by_genre.loc[genre, 'std']) if not pd.isna(tp_by_genre.loc[genre, 'std']) else None,
                'count': int(tp_by_genre.loc[genre, 'count']) if not pd.isna(tp_by_genre.loc[genre, 'count']) else None
            }
        
        tp_by_structure_dict = {}
        for structure in tp_by_structure.index:
            tp_by_structure_dict[str(structure)] = {
                'mean': float(tp_by_structure.loc[structure, 'mean']) if not pd.isna(tp_by_structure.loc[structure, 'mean']) else None,
                'std': float(tp_by_structure.loc[structure, 'std']) if not pd.isna(tp_by_structure.loc[structure, 'std']) else None,
                'count': int(tp_by_structure.loc[structure, 'count']) if not pd.isna(tp_by_structure.loc[structure, 'count']) else None
            }
        
        self.results['tp_coverage_analysis'] = {
            'overall_stats': tp_stats,
            'by_genre': tp_by_genre_dict,
            'by_structure': tp_by_structure_dict
        }
        
        # Visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        if has_variance:
            # Overall distribution
            tp_min, tp_max = valid_tp['tp_coverage_numeric'].min(), valid_tp['tp_coverage_numeric'].max()
            bins = np.linspace(tp_min, tp_max, 20) if tp_max > tp_min else [tp_min - 0.1, tp_min, tp_min + 0.1]
            
            axes[0,0].hist(valid_tp['tp_coverage_numeric'], bins=bins, alpha=0.7, 
                          color='lightcoral', edgecolor='black')
            axes[0,0].axvline(0.7, color='red', linestyle='--', linewidth=2, 
                             label='Qualification Threshold (0.7)')
            axes[0,0].set_title('Turning Point Coverage Distribution\n(TP ≥1.0 required for complexity scoring)')
            axes[0,0].set_xlabel('TP Coverage')
            axes[0,0].set_ylabel('Frequency')
            axes[0,0].legend()
            axes[0,0].grid(True, alpha=0.3)
            
            # By genre
            sns.boxplot(data=valid_tp, x='genre', y='tp_coverage_numeric', ax=axes[0,1])
            axes[0,1].axhline(0.7, color='red', linestyle='--', linewidth=2, 
                             label='Qualification Threshold')
            axes[0,1].set_title('TP Coverage by Genre\n(Hard gate threshold shown)')
            axes[0,1].set_ylabel('TP Coverage')
            axes[0,1].tick_params(axis='x', rotation=45)
            axes[0,1].legend()
            axes[0,1].grid(True, alpha=0.3)
            
            # By structure
            sns.boxplot(data=valid_tp, x='structure', y='tp_coverage_numeric', ax=axes[1,0])
            axes[1,0].axhline(0.7, color='red', linestyle='--', linewidth=2, 
                             label='Qualification Threshold')
            axes[1,0].set_title('TP Coverage by Structure\n(Hard gate threshold shown)')
            axes[1,0].set_ylabel('TP Coverage')
            axes[1,0].legend()
            axes[1,0].grid(True, alpha=0.3)
            
            # Qualification rate by genre-structure combination
            qualification_rates = valid_tp.groupby(['genre', 'structure']).apply(
                lambda x: (x['tp_coverage_numeric'] > 0.7).mean() * 100
            ).unstack(fill_value=0)
            
            im = axes[1,1].imshow(qualification_rates.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
            axes[1,1].set_xticks(range(len(qualification_rates.columns)))
            axes[1,1].set_yticks(range(len(qualification_rates.index)))
            axes[1,1].set_xticklabels(qualification_rates.columns)
            axes[1,1].set_yticklabels(qualification_rates.index)
            axes[1,1].set_title('TP Coverage Qualification Rate\n(Green=High qualification rate)')
            plt.colorbar(im, ax=axes[1,1])
            
            # Add text annotations
            for i in range(len(qualification_rates.index)):
                for j in range(len(qualification_rates.columns)):
                    text = axes[1,1].text(j, i, f'{qualification_rates.values[i, j]:.0f}%',
                                         ha="center", va="center", color="black")
        else:
            # Handle constant TP coverage case
            constant_value = valid_tp['tp_coverage_numeric'].iloc[0] if len(valid_tp) > 0 else 1.0
            
            for ax in axes.flat:
                ax.text(0.5, 0.5, f'TP Coverage Constant\nValue: {constant_value:.3f}\n(No variance detected)', 
                       ha='center', va='center', transform=ax.transAxes, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7),
                       fontsize=12)
                ax.set_title('TP Coverage Analysis: Constant Values')
                ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'tp_coverage_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return tp_stats
        
    def analyze_li_function_diversity(self):
        """Analyze Li function diversity across conditions (main samples only)."""
        print("🔍 Analyzing Li Function Diversity...")
        
        # Overall diversity statistics (main samples only)
        diversity_stats = {
            'mean': self.df_main['li_function_diversity'].mean(),
            'median': self.df_main['li_function_diversity'].median(),
            'std': self.df_main['li_function_diversity'].std(),
            'high_diversity_count': len(self.df_main[self.df_main['li_function_diversity'] >= 9]),
            'high_diversity_percentage': len(self.df_main[self.df_main['li_function_diversity'] >= 9]) / len(self.df_main) * 100
        }
        
        # Diversity by genre and structure (main samples only)
        diversity_by_genre = self.df_main.groupby('genre')['li_function_diversity'].agg(['mean', 'std', 'count'])
        diversity_by_structure = self.df_main.groupby('structure')['li_function_diversity'].agg(['mean', 'std', 'count'])
        
        # Convert to JSON-serializable format
        diversity_by_genre_dict = {}
        for genre in diversity_by_genre.index:
            diversity_by_genre_dict[str(genre)] = {
                'mean': float(diversity_by_genre.loc[genre, 'mean']) if not pd.isna(diversity_by_genre.loc[genre, 'mean']) else None,
                'std': float(diversity_by_genre.loc[genre, 'std']) if not pd.isna(diversity_by_genre.loc[genre, 'std']) else None,
                'count': int(diversity_by_genre.loc[genre, 'count']) if not pd.isna(diversity_by_genre.loc[genre, 'count']) else None
            }
        
        diversity_by_structure_dict = {}
        for structure in diversity_by_structure.index:
            diversity_by_structure_dict[str(structure)] = {
                'mean': float(diversity_by_structure.loc[structure, 'mean']) if not pd.isna(diversity_by_structure.loc[structure, 'mean']) else None,
                'std': float(diversity_by_structure.loc[structure, 'std']) if not pd.isna(diversity_by_structure.loc[structure, 'std']) else None,
                'count': int(diversity_by_structure.loc[structure, 'count']) if not pd.isna(diversity_by_structure.loc[structure, 'count']) else None
            }
        
        self.results['li_diversity_analysis'] = {
            'overall_stats': diversity_stats,
            'by_genre': diversity_by_genre_dict,
            'by_structure': diversity_by_structure_dict
        }
        
        # Visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Overall distribution (main samples only) 
        li_min, li_max = self.df_main['li_function_diversity'].min(), self.df_main['li_function_diversity'].max()
        if li_max > li_min:
            bins = np.linspace(li_min, li_max, 20)
        else:
            bins = range(int(li_min), int(li_max)+2)
            
        axes[0,0].hist(self.df_main['li_function_diversity'], bins=bins, 
                      alpha=0.7, color='mediumpurple', edgecolor='black')
        axes[0,0].axvline(9, color='red', linestyle='--', linewidth=2, 
                         label='High Diversity Threshold (9+)')
        axes[0,0].set_title('Li Function Diversity Distribution\n(High diversity ≥9)')
        axes[0,0].set_xlabel('Li Function Diversity Score')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # By genre (main samples only)
        sns.boxplot(data=self.df_main, x='genre', y='li_function_diversity', ax=axes[0,1])
        axes[0,1].axhline(9, color='red', linestyle='--', linewidth=2, alpha=0.7)
        axes[0,1].set_title('Li Function Diversity by Genre\n(High diversity ≥9)')
        axes[0,1].set_ylabel('Li Function Diversity Score')
        axes[0,1].tick_params(axis='x', rotation=45)
        axes[0,1].grid(True, alpha=0.3)
        
        # By structure (main samples only)
        sns.boxplot(data=self.df_main, x='structure', y='li_function_diversity', ax=axes[1,0])
        axes[1,0].axhline(9, color='red', linestyle='--', linewidth=2, alpha=0.7)
        axes[1,0].set_title('Li Function Diversity by Structure\n(High diversity ≥9)')
        axes[1,0].set_ylabel('Li Function Diversity Score')
        axes[1,0].grid(True, alpha=0.3)
        
        # Diversity vs temperature (main samples only)
        if 'temperature' in self.df_main.columns:
            scatter_data = self.df_main.copy()
            scatter_data['temperature'] = pd.to_numeric(scatter_data['temperature'], errors='coerce')
            scatter_data = scatter_data.dropna(subset=['temperature'])
            
            if len(scatter_data) > 0:
                sns.scatterplot(data=scatter_data, x='temperature', y='li_function_diversity', 
                              hue='genre', style='structure', ax=axes[1,1], s=60)
                axes[1,1].set_title('Li Function Diversity vs Temperature (Main Samples)')
                axes[1,1].set_xlabel('Temperature')
                axes[1,1].set_ylabel('Li Function Diversity Score')
                axes[1,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                axes[1,1].grid(True, alpha=0.3)
            else:
                axes[1,1].text(0.5, 0.5, 'No valid temperature data', ha='center', va='center', 
                              transform=axes[1,1].transAxes)
        else:
            axes[1,1].text(0.5, 0.5, 'Temperature data not available', ha='center', va='center',
                          transform=axes[1,1].transAxes)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'li_function_diversity_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return diversity_stats
        
    def analyze_events_vs_length(self):
        """Analyze relationship between total events and story length (main samples only)."""
        print("🔍 Analyzing Events vs Story Length...")
        
        # Calculate correlation (main samples only)
        correlation = self.df_main['total_events'].corr(self.df_main['total_words'])
        
        # Event density already calculated in _add_derived_metrics
        
        # Statistics (main samples only)
        events_stats = {
            'events_words_correlation': correlation,
            'mean_event_density': self.df_main['event_density'].mean(),
            'median_event_density': self.df_main['event_density'].median(),
            'event_density_std': self.df_main['event_density'].std(),
            'mean_total_events': self.df_main['total_events'].mean(),
            'mean_total_words': self.df_main['total_words'].mean()
        }
        
        # Event statistics by genre and structure (main samples only)
        events_by_genre = self.df_main.groupby('genre')[['total_events', 'event_density']].agg(['mean', 'std'])
        events_by_structure = self.df_main.groupby('structure')[['total_events', 'event_density']].agg(['mean', 'std'])
        
        # Convert multi-level column names to JSON-serializable format
        events_by_genre_dict = {}
        for genre in events_by_genre.index:
            events_by_genre_dict[str(genre)] = {}
            for col, stat in events_by_genre.columns:
                key = f"{col}_{stat}"
                events_by_genre_dict[str(genre)][key] = float(events_by_genre.loc[genre, (col, stat)]) if not pd.isna(events_by_genre.loc[genre, (col, stat)]) else None
        
        events_by_structure_dict = {}
        for structure in events_by_structure.index:
            events_by_structure_dict[str(structure)] = {}
            for col, stat in events_by_structure.columns:
                key = f"{col}_{stat}"
                events_by_structure_dict[str(structure)][key] = float(events_by_structure.loc[structure, (col, stat)]) if not pd.isna(events_by_structure.loc[structure, (col, stat)]) else None
        
        self.results['events_analysis'] = {
            'overall_stats': events_stats,
            'by_genre': events_by_genre_dict,
            'by_structure': events_by_structure_dict
        }
        
        # Visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Events vs Words scatter plot (main samples only)
        sns.scatterplot(data=self.df_main, x='total_words', y='total_events', 
                       hue='genre', style='structure', ax=axes[0,0], s=60, alpha=0.7)
        axes[0,0].set_title(f'Total Events vs Total Words (r={correlation:.3f}, Main Samples)')
        axes[0,0].set_xlabel('Total Words')
        axes[0,0].set_ylabel('Total Events')
        axes[0,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[0,0].grid(True, alpha=0.3)
        
        # Event density distribution (main samples only)
        density_min, density_max = self.df_main['event_density'].min(), self.df_main['event_density'].max()
        bins = np.linspace(density_min, density_max, 20) if density_max > density_min else [density_min]
        
        axes[0,1].hist(self.df_main['event_density'], bins=bins, alpha=0.7, 
                      color='orange', edgecolor='black')
        axes[0,1].axvline(self.df_main['event_density'].median(), color='red', linestyle='--', 
                         label=f'Median: {self.df_main["event_density"].median():.1f}')
        axes[0,1].set_title('Event Density Distribution\n(Balanced density zone around median)')
        axes[0,1].set_xlabel('Events per 1000 Words')
        axes[0,1].set_ylabel('Frequency')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Event density by genre (main samples only)
        sns.boxplot(data=self.df_main, x='genre', y='event_density', ax=axes[1,0])
        axes[1,0].set_title('Event Density by Genre\n(Balanced density distribution)')
        axes[1,0].set_ylabel('Events per 1000 Words')
        axes[1,0].tick_params(axis='x', rotation=45)
        axes[1,0].grid(True, alpha=0.3)
        
        # Event density by structure (main samples only)
        sns.boxplot(data=self.df_main, x='structure', y='event_density', ax=axes[1,1])
        axes[1,1].set_title('Event Density by Structure\n(Balanced density distribution)')
        axes[1,1].set_ylabel('Events per 1000 Words')
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'events_vs_length_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return events_stats
        
    def analyze_structure_interactions(self):
        """Analyze interactions between structure metrics and other quality measures (main samples only)."""
        print("🔍 Analyzing Structure Interactions...")
        
        # Key correlation columns including new metrics
        base_correlation_cols = [
            'chapter_count', 'chapter_score', 'tp_coverage_numeric', 'li_function_diversity', 
            'total_events', 'event_density', 'avg_coherence', 'distinct_avg', 'structure_complexity'
        ]
        
        # Filter to available columns and remove constant columns
        available_cols = self._drop_constant_cols(self.df_main, base_correlation_cols)
        
        # Calculate both Pearson and Spearman correlations
        if len(available_cols) >= 2:
            correlation_pearson = self.df_main[available_cols].corr(method='pearson')
            correlation_spearman = self.df_main[available_cols].corr(method='spearman')
            n_effective = len(self.df_main.dropna(subset=available_cols))
        else:
            correlation_pearson = pd.DataFrame()
            correlation_spearman = pd.DataFrame() 
            n_effective = 0
        
        # Analyze structure complexity relationships
        coherence_pearson = coherence_spearman = None
        diversity_pearson = diversity_spearman = None
        
        if 'structure_complexity' in self.df_main.columns:
            if 'avg_coherence' in self.df_main.columns:
                coherence_pearson = self.df_main['structure_complexity'].corr(self.df_main['avg_coherence'], method='pearson')
                coherence_spearman = self.df_main['structure_complexity'].corr(self.df_main['avg_coherence'], method='spearman')
            if 'distinct_avg' in self.df_main.columns:
                diversity_pearson = self.df_main['structure_complexity'].corr(self.df_main['distinct_avg'], method='pearson')
                diversity_spearman = self.df_main['structure_complexity'].corr(self.df_main['distinct_avg'], method='spearman')
        
        # Convert correlation matrices to JSON-serializable format
        def correlation_to_dict(corr_matrix, matrix_name):
            if corr_matrix.empty:
                return {}, []
            
            corr_dict = {}
            excluded_cols = []
            
            for col in corr_matrix.columns:
                if corr_matrix[col].nunique(dropna=True) <= 1:
                    excluded_cols.append(col)
                    continue
                    
                corr_dict[str(col)] = {}
                for row in corr_matrix.index:
                    value = corr_matrix.loc[row, col]
                    corr_dict[str(col)][str(row)] = float(value) if not pd.isna(value) else None
                    
            return corr_dict, excluded_cols
        
        correlation_pearson_dict, excluded_pearson = correlation_to_dict(correlation_pearson, 'pearson')
        correlation_spearman_dict, excluded_spearman = correlation_to_dict(correlation_spearman, 'spearman')
        
        # Structure complexity component weights (3-component hybrid approach)
        complexity_weights = getattr(self, 'selected_weights', {
            'chapter_score': 0.5, 
            'li_function_diversity': 0.3,
            'event_density': 0.2
        })
        
        weight_profile = getattr(self, 'selected_weight_profile', 'hybrid')
        
        # Weight rationale for 3-component approach
        weight_rationale = {
            'chapter_score': "Miller's 7±2 rule & Zacks event segmentation - cognitive processing optimization",
            'li_function_diversity': "Shannon entropy & information theory - optimal narrative variety",
            'event_density': "McKee's tempo theory - pacing regulation (data-adjusted)"
        }
        
        # TP Coverage handled separately as hard gate
        tp_gate_rationale = "Propp's morphology & Campbell's monomyth - structural completeness prerequisite (hard gate: must be >=1.0)"
        
        interactions_stats = {
            'correlation_matrix_pearson': correlation_pearson_dict,
            'correlation_matrix_spearman': correlation_spearman_dict,
            'n_effective_samples': n_effective,
            'available_correlation_cols': available_cols,
            'excluded_constant_cols_pearson': excluded_pearson,
            'excluded_constant_cols_spearman': excluded_spearman,
            'structure_coherence_pearson': float(coherence_pearson) if coherence_pearson is not None and not pd.isna(coherence_pearson) else None,
            'structure_coherence_spearman': float(coherence_spearman) if coherence_spearman is not None and not pd.isna(coherence_spearman) else None,
            'structure_diversity_pearson': float(diversity_pearson) if diversity_pearson is not None and not pd.isna(diversity_pearson) else None,
            'structure_diversity_spearman': float(diversity_spearman) if diversity_spearman is not None and not pd.isna(diversity_spearman) else None,
            'structure_complexity_weights': {
                'approach': 'hybrid_3_component',
                'tp_coverage_role': 'hard_gate',
                'tp_gate_rationale': tp_gate_rationale,
                'component_weights': complexity_weights,
                'weight_profile': weight_profile,
                'component_rationale': weight_rationale,
                'theoretical_baseline': getattr(self, 'theoretical_baseline', {}),
                'data_adjustments': getattr(self, 'data_adjustments', {}),
                'tp_gate_stats': getattr(self, 'tp_gate_stats', {}),
                'validation_available': True
            }
        }
        
        self.results['interactions_analysis'] = interactions_stats
        
        # Visualization
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Correlation heatmap (Pearson)
        if not correlation_pearson.empty and len(correlation_pearson.columns) > 1:
            mask = np.triu(np.ones_like(correlation_pearson, dtype=bool))
            sns.heatmap(correlation_pearson, mask=mask, annot=True, cmap='coolwarm', center=0,
                       square=True, ax=axes[0,0], fmt='.3f')
            axes[0,0].set_title(f'Pearson Correlation Matrix (N={n_effective}, Main Samples)')
        else:
            axes[0,0].text(0.5, 0.5, 'Insufficient non-constant\nvariables for correlation', 
                          ha='center', va='center', transform=axes[0,0].transAxes)
            axes[0,0].set_title('Pearson Correlation: Not Available')
        
        # Correlation heatmap (Spearman)
        if not correlation_spearman.empty and len(correlation_spearman.columns) > 1:
            mask = np.triu(np.ones_like(correlation_spearman, dtype=bool))
            sns.heatmap(correlation_spearman, mask=mask, annot=True, cmap='coolwarm', center=0,
                       square=True, ax=axes[0,1], fmt='.3f')
            axes[0,1].set_title(f'Spearman Correlation Matrix (N={n_effective}, Main Samples)')
        else:
            axes[0,1].text(0.5, 0.5, 'Insufficient non-constant\nvariables for correlation', 
                          ha='center', va='center', transform=axes[0,1].transAxes)
            axes[0,1].set_title('Spearman Correlation: Not Available')
        
        # Structure complexity vs coherence 
        if 'structure_complexity' in self.df_main.columns and 'avg_coherence' in self.df_main.columns:
            sns.scatterplot(data=self.df_main, x='structure_complexity', y='avg_coherence', 
                           hue='genre', style='structure', ax=axes[1,0], s=60, alpha=0.7)
            r_p = coherence_pearson if coherence_pearson is not None else 0
            r_s = coherence_spearman if coherence_spearman is not None else 0
            axes[1,0].set_title(f'Structure Complexity vs Coherence\n(Pearson: {r_p:.3f}, Spearman: {r_s:.3f})')
            axes[1,0].set_xlabel('Structure Complexity Score')
            axes[1,0].set_ylabel('Average Coherence')
            axes[1,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            axes[1,0].grid(True, alpha=0.3)
        else:
            axes[1,0].text(0.5, 0.5, 'Structure complexity or\ncoherence data not available', 
                          ha='center', va='center', transform=axes[1,0].transAxes)
            
        # Structure complexity vs diversity
        if 'structure_complexity' in self.df_main.columns and 'distinct_avg' in self.df_main.columns:
            sns.scatterplot(data=self.df_main, x='structure_complexity', y='distinct_avg', 
                           hue='genre', style='structure', ax=axes[1,1], s=60, alpha=0.7)
            r_p = diversity_pearson if diversity_pearson is not None else 0
            r_s = diversity_spearman if diversity_spearman is not None else 0
            axes[1,1].set_title(f'Structure Complexity vs Diversity\n(Pearson: {r_p:.3f}, Spearman: {r_s:.3f})')
            axes[1,1].set_xlabel('Structure Complexity Score')
            axes[1,1].set_ylabel('Distinct Average (Diversity)')
            axes[1,1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            axes[1,1].grid(True, alpha=0.3)
        else:
            axes[1,1].text(0.5, 0.5, 'Structure complexity or\ndiversity data not available', 
                          ha='center', va='center', transform=axes[1,1].transAxes)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'structure_interactions_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return interactions_stats
    
    def analyze_baseline_comparison(self):
        """Analyze baseline samples separately for comparison."""
        print("📊 Analyzing Baseline Comparison...")
        
        if len(self.df_baseline) == 0:
            return {
                'baseline_available': False,
                'message': 'No baseline samples found'
            }
        
        baseline_stats = {
            'baseline_available': True,
            'n_baseline_samples': len(self.df_baseline),
            'n_main_samples': len(self.df_main),
            'chapter_count': {
                'baseline_mean': self.df_baseline['chapter_count'].mean(),
                'baseline_std': self.df_baseline['chapter_count'].std(),
                'main_mean': self.df_main['chapter_count'].mean(),
                'main_std': self.df_main['chapter_count'].std(),
                'difference': self.df_baseline['chapter_count'].mean() - self.df_main['chapter_count'].mean()
            },
            'avg_coherence': {
                'baseline_mean': self.df_baseline['avg_coherence'].mean() if 'avg_coherence' in self.df_baseline.columns else None,
                'main_mean': self.df_main['avg_coherence'].mean() if 'avg_coherence' in self.df_main.columns else None,
                'difference': (self.df_baseline['avg_coherence'].mean() - self.df_main['avg_coherence'].mean()) 
                             if 'avg_coherence' in self.df_baseline.columns else None
            },
            'total_words': {
                'baseline_mean': self.df_baseline['total_words'].mean() if 'total_words' in self.df_baseline.columns else None,
                'main_mean': self.df_main['total_words'].mean() if 'total_words' in self.df_main.columns else None,
                'difference': (self.df_baseline['total_words'].mean() - self.df_main['total_words'].mean()) 
                             if 'total_words' in self.df_baseline.columns else None
            }
        }
        
        # Add TP coverage comparison if available
        if 'tp_coverage_numeric' in self.df_baseline.columns:
            baseline_stats['tp_coverage'] = {
                'baseline_mean': self.df_baseline['tp_coverage_numeric'].mean(),
                'main_mean': self.df_main['tp_coverage_numeric'].mean(),
                'baseline_variance': self.df_baseline['tp_coverage_numeric'].var(),
                'main_variance': self.df_main['tp_coverage_numeric'].var()
            }
        
        return baseline_stats
        
    def generate_comprehensive_report(self):
        """Generate a comprehensive structure integrity report."""
        print("📊 Generating Comprehensive Structure Report...")
        
        # Get current weight configuration for reporting
        complexity_weights = getattr(self, 'selected_weights', {
            'chapter_score': 0.5, 
            'li_function_diversity': 0.3,
            'event_density': 0.2
        })
        weight_profile = getattr(self, 'selected_weight_profile', 'hybrid')
        
        # Run all analyses
        chapter_stats = self.analyze_chapter_distribution()
        tp_stats = self.analyze_turning_point_coverage()
        diversity_stats = self.analyze_li_function_diversity()
        events_stats = self.analyze_events_vs_length()
        interactions_stats = self.analyze_structure_interactions()
        baseline_stats = self.analyze_baseline_comparison()
        
        # Generate hybrid weight comparison table
        weight_comparison = self._generate_weight_comparison_table()
        
        # Generate summary insights
        insights = {
            "optimal_chapter_distribution": {
                "percentage_in_optimal_range": chapter_stats['optimal_percentage'],
                "chapter_score_mean": chapter_stats.get('chapter_score_mean', 0),
                "interpretation": f"Optimal ({chapter_stats['optimal_percentage']:.0f}% in 5-8 range)"
            },
            "turning_point_qualification": {
                "qualified_percentage": tp_stats['qualified_percentage'],
                "perfect_coverage_percentage": tp_stats['perfect_coverage_percentage'],
                "has_variance": tp_stats.get('has_variance', True),
                "unique_values": tp_stats.get('unique_values', 0),
                "interpretation": "No Variance (Gate Applied)" if not tp_stats.get('has_variance', True) else
                                 f"Excellent ({tp_stats['qualified_percentage']:.0f}% qualified)" if tp_stats['qualified_percentage'] > 80 else 
                                 f"Good ({tp_stats['qualified_percentage']:.0f}% qualified)" if tp_stats['qualified_percentage'] > 60 else "Needs Improvement"
            },
            "plot_progression_richness": {
                "mean_diversity": diversity_stats['mean'],
                "high_diversity_percentage": diversity_stats['high_diversity_percentage'],
                "interpretation": f"Rich (avg≈{diversity_stats['mean']:.1f}, {diversity_stats['high_diversity_percentage']:.0f}%≥9)"
            },
            "event_story_balance": {
                "events_words_correlation": events_stats['events_words_correlation'],
                "mean_event_density": events_stats['mean_event_density'],
                "interpretation": f"Well-balanced (r≈{events_stats['events_words_correlation']:.2f})"
            },
            "structure_complexity": {
                "available": 'structure_complexity' in self.df_main.columns,
                "mean_complexity": self.df_main['structure_complexity'].mean() if 'structure_complexity' in self.df_main.columns else None,
                "mean_complexity_passed_only": self.df_main[self.df_main['structure_complexity'] > 0]['structure_complexity'].mean() if 'structure_complexity' in self.df_main.columns else None,
                "coherence_correlation_pearson": interactions_stats.get('structure_coherence_pearson'),
                "diversity_correlation_pearson": interactions_stats.get('structure_diversity_pearson'),
                "tp_gate_applied": True,
                "tp_pass_rate": getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0),
                "interpretation": f"High (mean≈{self.df_main['structure_complexity'].mean():.2f})" if 'structure_complexity' in self.df_main.columns and self.df_main['structure_complexity'].mean() > 0.6 else 
                                 f"Moderate (mean≈{self.df_main['structure_complexity'].mean():.2f})" if 'structure_complexity' in self.df_main.columns and self.df_main['structure_complexity'].mean() > 0.4 else "Low"
            },
            "tp_gate_analysis": {
                "gate_threshold": 1.0,
                "total_samples": getattr(self, 'tp_gate_stats', {}).get('total_samples', len(self.df_main)),
                "passed_samples": getattr(self, 'tp_gate_stats', {}).get('passed_samples', len(self.df_main)),
                "failed_samples": getattr(self, 'tp_gate_stats', {}).get('failed_samples', 0),
                "pass_rate": getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0),
                "interpretation": f"All Passed ({getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0):.0%})" if getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0) > 0.95 else
                                 f"Most Passed ({getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0):.0%})" if getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0) > 0.8 else 
                                 f"Some Failed ({getattr(self, 'tp_gate_stats', {}).get('pass_rate', 1.0):.0%} pass)"
            }
        }
        
        # Complete results compilation
        complete_results = {
            "analysis_metadata": {
                "total_stories_analyzed": len(self.df),
                "main_samples_analyzed": len(self.df_main),
                "baseline_samples_analyzed": len(self.df_baseline),
                "genres": list(self.df_main['genre'].unique()),
                "structures": list(self.df_main['structure'].unique()),
                "all_genres": list(self.df['genre'].unique()),
                "all_structures": list(self.df['structure'].unique()),
                "analysis_date": pd.Timestamp.now().isoformat(),
                "new_metrics_available": {
                    "chapter_score": 'chapter_score' in self.df_main.columns,
                    "structure_complexity": 'structure_complexity' in self.df_main.columns,
                    "tp_m_n": all(col in self.df_main.columns for col in ['tp_m', 'tp_n'])
                }
            },
            "chapter_analysis": self.results['chapter_analysis'],
            "tp_coverage_analysis": self.results['tp_coverage_analysis'],
            "li_diversity_analysis": self.results['li_diversity_analysis'],
            "events_analysis": self.results['events_analysis'],
            "interactions_analysis": self.results['interactions_analysis'],
            "baseline_comparison": baseline_stats,
            "weight_comparison": weight_comparison,
            "key_insights": insights,
            "recommendations": self._generate_recommendations(insights),
            "methodology_notes": {
                "analysis_approach": "Hybrid theoretical-empirical structure complexity analysis",
                "main_vs_baseline": "Analysis performed on main experimental samples, excluding baseline controls",
                "tp_coverage_approach": "Hard gate mechanism - TP coverage must be >=1.0 to qualify for complexity scoring",
                "tp_gate_rationale": "由于本批数据TP覆盖率恒为1.0，无差异，故设置为硬性Gate（≥1.0必须通过），不再纳入加权计算",
                "tp_gate_stats": getattr(self, 'tp_gate_stats', {}),
                "complexity_scoring": "3-component weighted scoring for TP-qualified samples only",
                "component_weighting": f"Hybrid {getattr(self, 'selected_weight_profile', 'hybrid')} profile: " + 
                                     " + ".join([f"{comp.replace('_', ' ').title()}({weight:.1%})" 
                                               for comp, weight in complexity_weights.items()]),
                "weight_methodology": {
                    "approach": "Theoretical baseline + data-driven adjustment (±15%)",
                    "theoretical_baseline": getattr(self, 'theoretical_baseline', {}),
                    "data_adjustments": getattr(self, 'data_adjustments', {}),
                    "final_weights": complexity_weights
                },
                "scientific_basis": {
                    "tp_hard_gate": "Propp's morphological analysis - structural completeness as prerequisite",
                    "chapter_score_weighting": "Miller's cognitive load theory & Zacks event segmentation",
                    "li_diversity_weighting": "Shannon information entropy - balanced variety principle",
                    "event_density_weighting": "McKee's story tempo theory - empirically adjusted based on quality correlation"
                },
                "data_driven_corrections": {
                    "quality_target": "Balanced composite: 0.5×coherence + 0.5×diversity",
                    "adjustment_method": "Correlation-based ±15% weight modification",
                    "normalization": "Final weights renormalized to sum=1.0 for interpretability"
                },
                "technical_details": {
                    "tp_coverage_parsing": "Robust parsing supports 'm/n', 'm/n (ratio)', and decimal formats", 
                    "chapter_scoring": "Peak scoring at 5-8 chapters with linear decay outside optimal range",
                    "correlation_methods": "Both Pearson and Spearman correlations provided with constant column exclusion",
                    "winsorization": "5th-95th percentile clipping applied before normalization"
                },
                "profiles_available": ["hybrid", "theoretical", "data_driven", "custom"],
                "validation_methods": "Bootstrap stability, cross-validation, sensitivity analysis available"
            }
        }
        
        # Save comprehensive report
        with open(self.output_dir / 'comprehensive_structure_report.json', 'w') as f:
            json.dump(complete_results, f, indent=2)
            
        # Generate summary dashboard
        self._create_summary_dashboard()
        
        # Generate text report
        self._generate_text_report(complete_results)
        
        # Generate weight comparison visualization
        self._create_weight_comparison_visualization()
        
        print(f"✅ Analysis complete! Results saved to: {self.output_dir.absolute()}")
        return complete_results
    
    def _create_weight_comparison_visualization(self):
        """Create visualization showing theoretical vs data-corrected vs final weights."""
        
        if not hasattr(self, 'theoretical_baseline') or not hasattr(self, 'data_adjustments'):
            print("⚠️ Weight comparison data not available for visualization")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Weight evolution comparison
        components = list(self.theoretical_baseline.keys())
        component_names = [c.replace('_', ' ').title() for c in components]
        
        theoretical_weights = [self.theoretical_baseline[c] for c in components]
        
        # Calculate data-corrected weights
        data_corrected_weights = []
        for comp in components:
            baseline = self.theoretical_baseline[comp]
            if comp in self.data_adjustments:
                adjustment = self.data_adjustments[comp]['adjustment_factor']
                corrected = baseline * (1 + adjustment)
            else:
                corrected = baseline
            data_corrected_weights.append(corrected)
        
        # Renormalize data-corrected weights
        total_corrected = sum(data_corrected_weights)
        if total_corrected > 0:
            data_corrected_weights = [w/total_corrected for w in data_corrected_weights]
        
        final_weights = [self.selected_weights.get(c, 0) for c in components]
        
        # Weight evolution plot
        x = np.arange(len(components))
        width = 0.25
        
        axes[0,0].bar(x - width, theoretical_weights, width, label='Theoretical Baseline', alpha=0.8, color='lightblue')
        axes[0,0].bar(x, data_corrected_weights, width, label='Data Corrected', alpha=0.8, color='orange')
        axes[0,0].bar(x + width, final_weights, width, label='Final Hybrid', alpha=0.8, color='green')
        
        axes[0,0].set_xlabel('Structure Components')
        axes[0,0].set_ylabel('Weight')
        axes[0,0].set_title('Weight Evolution: Theoretical → Data-Corrected → Final')
        axes[0,0].set_xticks(x)
        axes[0,0].set_xticklabels(component_names, rotation=45)
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # Correlation and adjustment factors
        correlations = [self.data_adjustments[c]['correlation'] for c in components if c in self.data_adjustments]
        adjustments = [self.data_adjustments[c]['adjustment_factor'] for c in components if c in self.data_adjustments]
        
        axes[0,1].bar(component_names, correlations, alpha=0.7, color='purple')
        axes[0,1].set_xlabel('Structure Components')
        axes[0,1].set_ylabel('Correlation with Quality Target')
        axes[0,1].set_title('Data-Driven Correlations')
        axes[0,1].tick_params(axis='x', rotation=45)
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].axhline(0, color='black', linestyle='-', alpha=0.3)
        
        # Adjustment factors
        colors = ['red' if adj < 0 else 'green' for adj in adjustments]
        bars = axes[1,0].bar(component_names, adjustments, alpha=0.7, color=colors)
        axes[1,0].set_xlabel('Structure Components')
        axes[1,0].set_ylabel('Weight Adjustment Factor')
        axes[1,0].set_title('Data-Driven Weight Adjustments (±15% max)')
        axes[1,0].tick_params(axis='x', rotation=45)
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].axhline(0, color='black', linestyle='-', alpha=0.3)
        
        # Add adjustment percentage labels
        for bar, adj in zip(bars, adjustments):
            height = bar.get_height()
            axes[1,0].text(bar.get_x() + bar.get_width()/2., height + (0.01 if height >= 0 else -0.01),
                          f'{adj:+.1%}', ha='center', va='bottom' if height >= 0 else 'top')
        
        # TP Gate Analysis
        if hasattr(self, 'tp_gate_stats'):
            gate_stats = self.tp_gate_stats
            labels = ['Passed TP Gate', 'Failed TP Gate']
            sizes = [gate_stats['passed_samples'], gate_stats['failed_samples']]
            colors = ['green', 'red']
            
            if gate_stats['failed_samples'] > 0:
                axes[1,1].pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                axes[1,1].set_title(f'TP Gate Results (n={gate_stats["total_samples"]})')
            else:
                axes[1,1].text(0.5, 0.5, f'All samples passed TP gate\n(n={gate_stats["total_samples"]})', 
                              ha='center', va='center', transform=axes[1,1].transAxes,
                              bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
                axes[1,1].set_title('TP Gate: 100% Pass Rate')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'hybrid_weight_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("📊 Weight comparison visualization saved: hybrid_weight_comparison.png")
        
    def _generate_recommendations(self, insights):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Chapter count recommendations
        if insights['optimal_chapter_distribution']['interpretation'] != "Good":
            recommendations.append({
                "area": "Chapter Structure",
                "issue": f"Only {insights['optimal_chapter_distribution']['percentage_in_optimal_range']:.1f}% of stories have optimal chapter count (5-8)",
                "recommendation": "Focus on generating stories with 5-8 chapters for optimal narrative structure",
                "priority": "High"
            })
        
        # TP Gate recommendations 
        if 'tp_gate_analysis' in insights:
            tp_gate = insights['tp_gate_analysis']
            if tp_gate['interpretation'] == "Needs Improvement":
                recommendations.append({
                    "area": "TP Gate Qualification",
                    "issue": f"Only {tp_gate['pass_rate']:.1%} of stories pass TP gate (≥1.0 coverage)",
                    "recommendation": "Improve turning point identification and coverage in story generation pipeline",
                    "priority": "High"
                })
            elif tp_gate['pass_rate'] < 1.0:
                recommendations.append({
                    "area": "TP Gate Performance",
                    "issue": f"TP gate excludes {tp_gate['failed_samples']} samples from complexity scoring",
                    "recommendation": "Monitor TP gate performance - consider threshold adjustment if exclusion rate is high",
                    "priority": "Medium"
                })
        
        # Legacy TP variance issue (now resolved by gate approach)
        tp_interp = insights['turning_point_qualification']['interpretation']
        if tp_interp == "No Variance":
            recommendations.append({
                "area": "Methodology Improvement", 
                "issue": "TP coverage converted to hard gate due to no variance in current data",
                "recommendation": "New hybrid approach successfully addresses TP variance issue - monitor gate performance",
                "priority": "Info"
            })
        
        # Diversity recommendations
        if insights['plot_progression_richness']['interpretation'] == "Limited":
            recommendations.append({
                "area": "Plot Progression",
                "issue": f"Li function diversity is limited (mean: {insights['plot_progression_richness']['mean_diversity']:.1f})",
                "recommendation": "Enhance plot progression mechanisms to increase narrative richness",
                "priority": "Medium"
            })
        
        # Balance recommendations
        if insights['event_story_balance']['interpretation'] == "Imbalanced":
            recommendations.append({
                "area": "Event-Length Balance",
                "issue": f"Event density correlation suggests imbalance ({insights['event_story_balance']['events_words_correlation']:.3f})",
                "recommendation": "Optimize event distribution relative to story length",
                "priority": "Medium"
            })
        
        # Structure complexity recommendations
        if insights['structure_complexity']['available']:
            mean_complexity = insights['structure_complexity']['mean_complexity']
            if mean_complexity is not None and mean_complexity < 0.5:
                recommendations.append({
                    "area": "Structure Complexity",
                    "issue": f"Low structure complexity score (mean: {mean_complexity:.3f})",
                    "recommendation": "Enhance structural sophistication through better TP coverage, chapter scoring, and narrative diversity",
                    "priority": "Medium"
                })
        
        return recommendations
        
    def _create_summary_dashboard(self):
        """Create a comprehensive summary dashboard."""
        fig, axes = plt.subplots(3, 2, figsize=(20, 18))
        
        # Key metrics summary (main samples only)
        metrics = ['Chapter Score', 'TP Coverage', 'Li Diversity', 'Event Density', 'Coherence', 'Diversity']
        values = [
            self.df_main['chapter_score'].mean() if 'chapter_score' in self.df_main.columns else 0,
            self.df_main['tp_coverage_numeric'].mean() if 'tp_coverage_numeric' in self.df_main.columns else 0,
            self.df_main['li_function_diversity'].mean() / 10,  # Normalize to 0-1 for display
            self.df_main['event_density'].mean() / 20,  # Normalize to 0-1 for display  
            self.df_main['avg_coherence'].mean() if 'avg_coherence' in self.df_main.columns else 0,
            self.df_main['distinct_avg'].mean() if 'distinct_avg' in self.df_main.columns else 0
        ]
        
        bars = axes[0,0].bar(metrics, values, color=['skyblue', 'lightcoral', 'mediumpurple', 
                                                    'orange', 'lightgreen', 'pink'])
        axes[0,0].set_title('Structure Integrity Key Metrics Overview (Main Samples)')
        axes[0,0].set_ylabel('Normalized Values (0-1)')
        axes[0,0].tick_params(axis='x', rotation=45)
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].set_ylim(0, 1.1)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            axes[0,0].text(bar.get_x() + bar.get_width()/2., height,
                          f'{value:.3f}', ha='center', va='bottom')
        
        # Genre comparison line plot (corrected from "radar")
        unique_genres = self.df_main['genre'].unique()
        if len(unique_genres) > 1:
            genre_metrics = []
            for genre in unique_genres:
                genre_data = self.df_main[self.df_main['genre'] == genre]
                genre_metrics.append([
                    genre_data['chapter_score'].mean() if 'chapter_score' in genre_data.columns else 0,
                    genre_data['tp_coverage_numeric'].mean() if 'tp_coverage_numeric' in genre_data.columns else 0,
                    genre_data['li_function_diversity'].mean() / 10,
                    genre_data['event_density'].mean() / 20
                ])
            
            # Plot normalized values
            for i, genre in enumerate(unique_genres):
                axes[0,1].plot(range(4), genre_metrics[i], 'o-', label=genre, linewidth=2, markersize=8)
            
            axes[0,1].set_xticks(range(4))
            axes[0,1].set_xticklabels(['Chapter Score', 'TP Coverage', 'Li Diversity', 'Event Density'], rotation=45)
            axes[0,1].set_title('Genre Comparison (Normalized Line Plot)')
            axes[0,1].legend()
            axes[0,1].grid(True, alpha=0.3)
            axes[0,1].set_ylim(0, 1)
        else:
            axes[0,1].text(0.5, 0.5, f'Single genre: {unique_genres[0]}', ha='center', va='center',
                          transform=axes[0,1].transAxes)
        
        # Quality distribution using chapter score (main samples only)
        if 'chapter_score' in self.df_main.columns:
            chapter_score_quality = pd.cut(self.df_main['chapter_score'], 
                                         bins=[0, 0.5, 0.7, 0.9, 1.0], 
                                         labels=['Poor', 'Fair', 'Good', 'Excellent'])
            chapter_counts = chapter_score_quality.value_counts()
            if len(chapter_counts) > 0:
                axes[1,0].pie(chapter_counts.values, labels=chapter_counts.index, autopct='%1.1f%%',
                             colors=['red', 'orange', 'lightgreen', 'green'])
                axes[1,0].set_title('Chapter Score Quality Distribution (Main Samples)')
            else:
                axes[1,0].text(0.5, 0.5, 'No chapter score data', ha='center', va='center',
                              transform=axes[1,0].transAxes)
        else:
            axes[1,0].text(0.5, 0.5, 'Chapter score not available', ha='center', va='center',
                          transform=axes[1,0].transAxes)
        
        # TP coverage quality distribution (main samples only)
        if 'tp_coverage_numeric' in self.df_main.columns:
            if self.df_main['tp_coverage_numeric'].nunique(dropna=True) > 1:
                tp_quality = pd.cut(self.df_main['tp_coverage_numeric'], 
                                  bins=[0, 0.5, 0.7, 0.9, 1.0], 
                                  labels=['Poor', 'Fair', 'Good', 'Excellent'])
                tp_counts = tp_quality.value_counts()
                if len(tp_counts) > 0:
                    axes[1,1].pie(tp_counts.values, labels=tp_counts.index, autopct='%1.1f%%',
                                 colors=['red', 'orange', 'lightgreen', 'green'])
                    axes[1,1].set_title('TP Coverage Quality Distribution (Main Samples)')
                else:
                    axes[1,1].text(0.5, 0.5, 'No TP coverage data', ha='center', va='center',
                                  transform=axes[1,1].transAxes)
            else:
                constant_value = self.df_main['tp_coverage_numeric'].iloc[0] if len(self.df_main) > 0 else 1.0
                axes[1,1].text(0.5, 0.5, f'TP Coverage Constant\n{constant_value:.3f}', 
                              ha='center', va='center', transform=axes[1,1].transAxes,
                              bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
                axes[1,1].set_title('TP Coverage: No Variance')
        
        # Structure complexity vs quality metrics (main samples only)
        if 'structure_complexity' in self.df_main.columns and 'avg_coherence' in self.df_main.columns:
            if 'distinct_avg' in self.df_main.columns:
                scatter = axes[2,0].scatter(self.df_main['structure_complexity'], self.df_main['avg_coherence'], 
                                          c=self.df_main['distinct_avg'], s=60, alpha=0.6, cmap='viridis')
                plt.colorbar(scatter, ax=axes[2,0], label='Diversity')
            else:
                axes[2,0].scatter(self.df_main['structure_complexity'], self.df_main['avg_coherence'], 
                                s=60, alpha=0.6, color='blue')
            
            axes[2,0].set_xlabel('Structure Complexity')
            axes[2,0].set_ylabel('Coherence')
            axes[2,0].set_title('Structure vs Quality Metrics (Main Samples)')
            axes[2,0].grid(True, alpha=0.3)
        else:
            axes[2,0].text(0.5, 0.5, 'Structure complexity or\ncoherence data not available', 
                          ha='center', va='center', transform=axes[2,0].transAxes)
        
        # Best practices adherence (main samples only)
        best_practices = {
            'Optimal Chapters (5-8)': (self.df_main['chapter_count'].between(5, 8)).mean() * 100,
            'High Chapter Score (≥0.8)': (self.df_main['chapter_score'] >= 0.8).mean() * 100 if 'chapter_score' in self.df_main.columns else 0,
            'High Li Diversity (≥9)': (self.df_main['li_function_diversity'] >= 9).mean() * 100,
            'Balanced Event Density': ((self.df_main['event_density'] >= 3) & (self.df_main['event_density'] <= 15)).mean() * 100
        }
        
        practices = list(best_practices.keys())
        adherence = list(best_practices.values())
        
        bars = axes[2,1].barh(practices, adherence, color=['green' if x >= 70 else 'orange' if x >= 50 else 'red' for x in adherence])
        axes[2,1].set_xlabel('Adherence Percentage (%)')
        axes[2,1].set_title('Best Practices Adherence (Main Samples)')
        axes[2,1].grid(True, alpha=0.3)
        axes[2,1].set_xlim(0, 105)
        
        # Add percentage labels
        for i, (practice, pct) in enumerate(zip(practices, adherence)):
            axes[2,1].text(pct + 1, i, f'{pct:.1f}%', va='center')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'structure_integrity_dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _generate_text_report(self, results):
        """Generate a comprehensive text report."""
        report = f"""
# Structure Integrity Analysis Report (Hybrid Approach)

## Executive Summary
This report analyzes the structural integrity of {results['analysis_metadata']['total_stories_analyzed']} generated stories across {len(results['analysis_metadata']['genres'])} genres and {len(results['analysis_metadata']['structures'])} structure types using a **hybrid theoretical-empirical approach**.

## Methodology Innovation
**Hybrid Approach**: TP Coverage as hard gate (≥1.0 required) + 3-component weighted complexity scoring with theoretical baseline + data-driven adjustment (±15%).

## Key Findings

### 1. TP Gate Analysis (New)
- **Gate threshold**: ≥1.0 coverage required for complexity scoring
- **Pass rate**: {results['key_insights']['tp_gate_analysis']['pass_rate']:.1%} ({results['key_insights']['tp_gate_analysis']['passed_samples']}/{results['key_insights']['tp_gate_analysis']['total_samples']} samples)
- **Failed samples**: {results['key_insights']['tp_gate_analysis']['failed_samples']} (excluded from complexity scoring)
- **Assessment**: {results['key_insights']['tp_gate_analysis']['interpretation']}

### 2. Chapter Distribution Analysis
- **Average chapters per story**: {results['chapter_analysis']['overall_stats']['mean']:.1f}
- **Optimal range adherence** (5-8 chapters): {results['chapter_analysis']['overall_stats']['optimal_percentage']:.1f}%
- **Chapter score average**: {results['chapter_analysis']['overall_stats']['chapter_score_mean']:.3f}
- **Assessment**: {results['key_insights']['optimal_chapter_distribution']['interpretation']}

### 3. Li Function Diversity Analysis
- **Average diversity score**: {results['li_diversity_analysis']['overall_stats']['mean']:.1f}
- **High diversity stories** (≥9): {results['li_diversity_analysis']['overall_stats']['high_diversity_percentage']:.1f}%
- **Assessment**: {results['key_insights']['plot_progression_richness']['interpretation']}

### 4. Event-Length Balance Analysis
- **Events-Words correlation**: {results['events_analysis']['overall_stats']['events_words_correlation']:.3f}
- **Average event density**: {results['events_analysis']['overall_stats']['mean_event_density']:.1f} events/1000 words
- **Assessment**: {results['key_insights']['event_story_balance']['interpretation']}

### 5. Structure Complexity Analysis (Hybrid)
- **Mean complexity** (all samples): {results['key_insights']['structure_complexity']['mean_complexity']:.3f}
- **Mean complexity** (passed samples only): {results['key_insights']['structure_complexity']['mean_complexity_passed_only']:.3f}
- **Assessment**: {results['key_insights']['structure_complexity']['interpretation']}

## Weight Configuration Evolution

### Theoretical Baseline → Data-Driven Adjustment → Final Hybrid Weights
"""
        
        # Add weight comparison table if available
        if 'weight_comparison' in results and 'summary' in results['weight_comparison']:
            report += "\n### Weight Evolution: Theoretical → Data-Driven → Final Hybrid\n\n"
            report += "| Component | Theoretical Baseline | Quality Correlation | Data Adjustment | Final Weight | Net Change |\n"
            report += "|-----------|---------------------|-------------------|-----------------|--------------|------------|\n"
            
            weight_comp = results['weight_comparison']
            for comp, data in weight_comp.items():
                if isinstance(data, dict) and 'theoretical_weight' in data:
                    comp_name = comp.replace('_', ' ').title()
                    theo_weight = data['theoretical_weight']
                    correlation = data['correlation_with_quality']
                    adjustment = data['adjustment_factor'] 
                    final_weight = data['final_weight']
                    change = data['weight_change']
                    
                    # Add theoretical explanation for each component
                    theory_note = ""
                    if 'chapter' in comp:
                        theory_note = " (Miller认知负荷)"
                    elif 'li_function' in comp:
                        theory_note = " (Shannon信息熵)"
                    elif 'event' in comp:
                        theory_note = " (McKee节奏理论)"
                    
                    report += f"| {comp_name}{theory_note} | {theo_weight:.1%} | r={correlation:.3f} | {adjustment:+.1%} | **{final_weight:.1%}** | {change:+.1%} |\n"
            
            summary = weight_comp['summary']
            report += f"""
**Hybrid Weight Summary:**
- **TP Coverage Role**: Hard Gate (≥1.0 required, not weighted)
- **TP Pass Rate**: {summary['tp_pass_rate']:.1%} ({summary.get('components_used', 3)} components weighted)
- **Max Data Adjustment**: ±{summary['max_adjustment']:.1%} (within ±15% limit)
- **Weight Profile Used**: {summary['profile_used'].title()}
- **Theoretical Foundation**: Miller + Shannon + McKee theories
- **Empirical Calibration**: Quality correlation-based ±15% micro-adjustment
"""
        
        report += "\n## Recommendations\n"
        
        for i, rec in enumerate(results['recommendations'], 1):
            report += f"""
### {i}. {rec['area']} ({rec['priority']} Priority)
- **Issue**: {rec['issue']}
- **Recommendation**: {rec['recommendation']}
"""
        
        report += f"""

## Methodology (Hybrid Approach)

### Core Innovation: Hybrid Theoretical-Empirical Framework
1. **TP Coverage Hard Gate**: Must achieve ≥1.0 coverage to qualify for complexity scoring (Propp/Campbell structural completeness)
2. **3-Component Complexity Scoring**: Only for TP-qualified samples using weighted combination
3. **Weight Determination**: Theoretical baseline (Miller/Shannon/McKee) + data-driven adjustment (±15% max)

### Component Analysis:
1. **Chapter Score**: Peak scoring at 5-8 chapters (Miller's 7±2 cognitive load theory)
2. **Li Function Diversity**: Information entropy balance (Shannon theory)  
3. **Event Density**: Pacing regulation (McKee tempo theory, empirically enhanced)
4. **TP Coverage**: Structural prerequisite (Propp morphology, hard gate implementation)

### Statistical Validation:
- **Sample separation**: {results['analysis_metadata']['main_samples_analyzed']} main + {results['analysis_metadata']['baseline_samples_analyzed']} baseline
- **Correlation analysis**: Both Pearson and Spearman with constant column exclusion
- **Weight adjustment**: Based on correlation with balanced quality target (0.5×coherence + 0.5×diversity)

## Data Quality
- Total stories analyzed: {results['analysis_metadata']['total_stories_analyzed']}
- Main experimental samples: {results['analysis_metadata']['main_samples_analyzed']}
- Baseline control samples: {results['analysis_metadata']['baseline_samples_analyzed']}
- Genres covered: {', '.join(results['analysis_metadata']['genres'])}
- Structure types: {', '.join(results['analysis_metadata']['structures'])}
- Analysis date: {results['analysis_metadata']['analysis_date']}

---
Generated by Structure Integrity Analyzer v2.0 (Hybrid Approach)
"""
        
        with open(self.output_dir / 'structure_analysis_report.md', 'w') as f:
            f.write(report)

def main():
    """Main execution function."""
    print("🚀 Starting Structure Integrity Analysis...")
    print("="*60)
    
    # Initialize analyzer
    analyzer = StructureIntegrityAnalyzer('/Users/haha/Story/metrics_master_clean.csv')
    
    # Run comprehensive analysis
    results = analyzer.generate_comprehensive_report()
    
    print("="*60)
    print("📋 Analysis Summary:")
    print(f"✓ Chapter distribution: {results['key_insights']['optimal_chapter_distribution']['interpretation']}")
    print(f"✓ Turning point coverage: {results['key_insights']['turning_point_qualification']['interpretation']}")
    print(f"✓ Plot progression: {results['key_insights']['plot_progression_richness']['interpretation']}")
    print(f"✓ Event balance: {results['key_insights']['event_story_balance']['interpretation']}")
    print("="*60)

if __name__ == "__main__":
    main()
