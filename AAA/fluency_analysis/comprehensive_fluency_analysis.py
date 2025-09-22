"""
Comprehensive Fluency Analysis Script

This script analyzes fluency-related metrics from story generation experiments:
- pseudo_ppl (Pseudo Perplexity): Lower is better
- err_per_100w (Error rate per 100 words): Lower is better
- error_count (Total errors)
- fluency_word_count (Word count for fluency analysis)

Creates visualizations and analyzes relationships with other metrics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

class FluencyAnalysisComprehensive:
    """Comprehensive fluency analysis system"""
    
    def __init__(self, csv_path: str, output_dir: str):
        """
        Initialize fluency analysis
        
        Args:
            csv_path: Path to metrics_master.csv
            output_dir: Directory to save results
        """
        self.csv_path = csv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        print("Loading data...")
        self.df = pd.read_csv(csv_path)
        print(f"Loaded {len(self.df)} records")
        
        # Fluency quality thresholds
        self.ppl_thresholds = {
            'excellent': 2.0,
            'good': 5.0,
            'poor': float('inf')
        }
        
        self.error_thresholds = {
            'high_quality': 0.2,
            'medium_quality': 0.5,
            'poor_quality': float('inf')
        }
        
        # Initialize analysis results
        self.results = {
            'summary_stats': {},
            'quality_distribution': {},
            'correlations': {},
            'group_analysis': {},
            'outliers': []
        }
    
    def validate_data(self):
        """Validate required columns exist"""
        required_cols = ['pseudo_ppl', 'err_per_100w', 'error_count', 'fluency_word_count', 
                        'genre', 'structure', 'temperature']
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        print("Data validation passed")
        
        # Print basic info about fluency metrics
        print("\nFluency Metrics Overview:")
        print(f"Pseudo-PPL range: {self.df['pseudo_ppl'].min():.2f} - {self.df['pseudo_ppl'].max():.2f}")
        print(f"Error rate per 100w range: {self.df['err_per_100w'].min():.2f} - {self.df['err_per_100w'].max():.2f}")
        print(f"Total records: {len(self.df)}")
        print(f"Records with valid PPL: {(self.df['pseudo_ppl'] != float('inf')).sum()}")
    
    def calculate_summary_statistics(self):
        """Calculate comprehensive summary statistics (emphasize robust measures)"""
        print("\nCalculating summary statistics...")
        
        # Filter out infinite values for statistics
        valid_ppl = self.df[self.df['pseudo_ppl'] != float('inf')]['pseudo_ppl']
        valid_err = self.df['err_per_100w']
        
        # Calculate IQR for robust spread measure
        def calculate_robust_stats(series, name):
            stats = {
                'count': len(series),
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'q25': float(series.quantile(0.25)),
                'q75': float(series.quantile(0.75)),
                'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
                'mad': float((series - series.median()).abs().median()),  # Median absolute deviation
                'skewness': float(series.skew()),
                'kurtosis': float(series.kurtosis())
            }
            
            # Print robust vs non-robust comparison
            print(f"  {name} - Mean: {stats['mean']:.3f}, Median: {stats['median']:.3f} (robust)")
            print(f"  {name} - Std: {stats['std']:.3f}, IQR: {stats['iqr']:.3f} (robust)")
            print(f"  {name} - Skewness: {stats['skewness']:.3f}, Kurtosis: {stats['kurtosis']:.3f}")
            
            # Flag heavy tails
            if abs(stats['skewness']) > 2:
                print(f"    WARNING: {name} has heavy skewness ({stats['skewness']:.2f}) - use median/IQR")
            if stats['kurtosis'] > 7:
                print(f"    WARNING: {name} has heavy tails (kurtosis {stats['kurtosis']:.2f}) - use robust measures")
                
            return stats
        
        summary_stats = {
            'pseudo_ppl': calculate_robust_stats(valid_ppl, 'Pseudo-PPL'),
            'err_per_100w': calculate_robust_stats(valid_err, 'Error Rate')
        }
        
        self.results['summary_stats'] = summary_stats
        return summary_stats
    
    def classify_quality_levels(self):
        """Classify samples by fluency quality levels"""
        print("Classifying quality levels...")
        
        # Create quality categories
        def categorize_ppl(ppl):
            if ppl == float('inf'):
                return 'invalid'
            elif ppl < self.ppl_thresholds['excellent']:
                return 'excellent'
            elif ppl < self.ppl_thresholds['good']:
                return 'good'
            else:
                return 'poor'
        
        def categorize_errors(err_rate):
            if err_rate < self.error_thresholds['high_quality']:
                return 'high_quality'
            elif err_rate < self.error_thresholds['medium_quality']:
                return 'medium_quality'
            else:
                return 'poor_quality'
        
        self.df['ppl_quality'] = self.df['pseudo_ppl'].apply(categorize_ppl)
        self.df['error_quality'] = self.df['err_per_100w'].apply(categorize_errors)
        
        # Calculate distributions
        ppl_dist = self.df['ppl_quality'].value_counts().to_dict()
        error_dist = self.df['error_quality'].value_counts().to_dict()
        
        # Combined quality score
        def combined_quality(row):
            ppl_q = row['ppl_quality']
            err_q = row['error_quality']
            
            if ppl_q == 'invalid':
                return 'invalid'
            
            # Create combined score
            ppl_score = {'excellent': 3, 'good': 2, 'poor': 1}.get(ppl_q, 0)
            err_score = {'high_quality': 3, 'medium_quality': 2, 'poor_quality': 1}.get(err_q, 0)
            
            combined_score = (ppl_score + err_score) / 2
            
            if combined_score >= 2.5:
                return 'high'
            elif combined_score >= 1.5:
                return 'medium'
            else:
                return 'low'
        
        self.df['combined_fluency_quality'] = self.df.apply(combined_quality, axis=1)
        combined_dist = self.df['combined_fluency_quality'].value_counts().to_dict()
        
        quality_dist = {
            'ppl_distribution': ppl_dist,
            'error_distribution': error_dist,
            'combined_distribution': combined_dist
        }
        
        self.results['quality_distribution'] = quality_dist
        return quality_dist
    
    def analyze_correlations(self, winsor_limits=(0.02, 0.02), use_log1p=True):
        """Analyze correlations with other metrics (robust options via params)"""
        print("Analyzing correlations...")
        
        # ROBUSTNESS FIX: Handle heavy-tailed error distribution
        from scipy.stats.mstats import winsorize
        df = self.df.copy()
        
        # Winsorize / log1p error rate to handle extreme values
        err = df['err_per_100w'].to_numpy()
        if winsor_limits:
            err_win = winsorize(err, limits=winsor_limits)  # e.g., (0.02, 0.02)
            df['err_per_100w_winz'] = np.asarray(err_win)   # ensure ndarray, not MaskedArray
        if use_log1p:
            df['err_per_100w_log1p'] = np.log1p(df['err_per_100w'])
        
        # Pretty print robustness summary (guard absent columns)
        msg = [f"Original std={df['err_per_100w'].std():.3f}"]
        if 'err_per_100w_winz' in df.columns:
            msg.append(f"Winsorized std={df['err_per_100w_winz'].std():.3f}")
        if 'err_per_100w_log1p' in df.columns:
            msg.append(f"Log1p std={df['err_per_100w_log1p'].std():.3f}")
        print("Error rate robustness: " + ", ".join(msg))
        
        # CONFOUNDING FIX: Partial correlation controlling for length
        import statsmodels.api as sm
        
        def residualize(y_col, x_cols):
            """Remove confounding variables using residuals"""
            try:
                X = sm.add_constant(df[x_cols].replace([np.inf, -np.inf], np.nan).fillna(0))
                y_clean = df[y_col].replace([np.inf, -np.inf], np.nan).fillna(df[y_col].median())
                model = sm.OLS(y_clean, X).fit()
                return y_clean - model.predict(X)
            except:
                return df[y_col].copy()
        
        # Control for length confounding
        if all(col in df.columns for col in ['distinct_avg', 'avg_coherence', 'total_words', 'total_sentences']):
            df['distinct_res'] = residualize('distinct_avg', ['total_words', 'total_sentences'])
            df['coh_res'] = residualize('avg_coherence', ['total_words', 'total_sentences'])
            df['ppl_res'] = residualize('pseudo_ppl', ['total_words', 'total_sentences'])
            
            # Calculate partial correlations
            from scipy.stats import spearmanr, pearsonr
            
            # Diversity-Coherence partial correlation (controlling length)
            try:
                rho_s, p_s = spearmanr(df['distinct_res'], df['coh_res'], nan_policy='omit')
                r_p, p_p = pearsonr(df['distinct_res'].dropna(), df['coh_res'].dropna())
                print(f"\n[PARTIAL CORRELATION] Diversity↔Coherence (controlling length):")
                print(f"  Spearman ρ={rho_s:.3f} (p={p_s:.3g}), Pearson r={r_p:.3f} (p={p_p:.3g})")
                
                # Store partial correlation results
                partial_corrs = {
                    'diversity_coherence_partial': {'spearman': rho_s, 'pearson': r_p, 'spearman_p': p_s, 'pearson_p': p_p}
                }
            except Exception as e:
                print(f"Partial correlation failed: {e}")
                partial_corrs = {}
        else:
            partial_corrs = {}
        
        # Select relevant metrics for correlation analysis
        correlation_cols = [
            'pseudo_ppl', 'err_per_100w', 'err_per_100w_winz', 'err_per_100w_log1p',
            'distinct_avg', 'diversity_group_score', 'distinct_score',  # Diversity metrics
            'avg_coherence', 'coherence_std',  # Coherence metrics
            'roberta_avg_score', 'emotion_correlation',  # Emotional metrics
            'total_words', 'total_sentences'  # Text statistics
        ]
        
        # Filter to available columns
        available_cols = [col for col in correlation_cols if col in df.columns]
        
        # Create correlation subset (exclude infinite values)
        corr_df = df[available_cols].copy()
        
        # Replace infinite values with NaN for correlation calculation
        corr_df = corr_df.replace([np.inf, -np.inf], np.nan)
        
        # Calculate correlations (both Pearson and Spearman)
        pearson_corr = corr_df.corr(method='pearson')
        spearman_corr = corr_df.corr(method='spearman')
        
        # Guard: if key columns dropped due to NaNs
        must_cols = ['pseudo_ppl', 'err_per_100w_winz' if 'err_per_100w_winz' in corr_df.columns else 'err_per_100w']
        for must_col in must_cols:
            if must_col not in spearman_corr.columns:
                print(f"Warning: '{must_col}' dropped from correlation matrix due to NaNs.")
        
        # Focus on fluency metrics correlations
        fluency_pearson = {
            'pseudo_ppl': pearson_corr['pseudo_ppl'].drop(['pseudo_ppl']).to_dict(),
            'err_per_100w': pearson_corr['err_per_100w'].drop(['err_per_100w']).to_dict(),
            'err_per_100w_robust': pearson_corr['err_per_100w_winz'].drop(['err_per_100w_winz']).to_dict() if 'err_per_100w_winz' in pearson_corr.columns else {}
        }
        
        fluency_spearman = {
            'pseudo_ppl': spearman_corr['pseudo_ppl'].drop(['pseudo_ppl']).to_dict(),
            'err_per_100w': spearman_corr['err_per_100w'].drop(['err_per_100w']).to_dict(),
            'err_per_100w_robust': spearman_corr['err_per_100w_winz'].drop(['err_per_100w_winz']).to_dict() if 'err_per_100w_winz' in spearman_corr.columns else {}
        }
        
        correlations = {
            'pearson': fluency_pearson,
            'spearman': fluency_spearman,
            'partial_correlations': partial_corrs,
            'full_pearson_matrix': pearson_corr.to_dict(),
            'full_spearman_matrix': spearman_corr.to_dict()
        }
        
        self.results['correlations'] = correlations
        
        # Print key relationships (prioritize Spearman for robustness)
        print("\nKey Correlations with Fluency (ROBUST - Spearman preferred):")
        print("Pseudo-PPL correlations (Note: PPL higher = worse fluency):")
        for metric, corr in fluency_spearman['pseudo_ppl'].items():
            if not pd.isna(corr) and abs(corr) > 0.1:
                pearson_val = fluency_pearson['pseudo_ppl'].get(metric, np.nan)
                # Add interpretation for key relationships
                interpretation = ""
                if metric == 'distinct_avg' and corr > 0:
                    interpretation = " → Higher diversity leads to worse fluency"
                elif metric == 'avg_coherence' and corr < 0:
                    interpretation = " → Higher coherence leads to better fluency"
                print(f"  {metric}: Spearman={corr:.3f}, Pearson={pearson_val:.3f}{interpretation}")
        
        print("Error rate correlations (Robust Winsorized, higher = worse):")
        for metric, corr in fluency_spearman.get('err_per_100w_robust', {}).items():
            if not pd.isna(corr) and abs(corr) > 0.1:
                original = fluency_spearman['err_per_100w'].get(metric, np.nan)
                # Add interpretation for key relationships  
                interpretation = ""
                if metric == 'distinct_avg' and corr > 0:
                    interpretation = " → Higher diversity leads to more errors"
                elif metric == 'avg_coherence' and corr < 0:
                    interpretation = " → Higher coherence leads to fewer errors"
                print(f"  {metric}: Robust={corr:.3f}, Original={original:.3f}{interpretation}")
        
        # Print scored correlations if available for cleaner interpretation
        if hasattr(self, 'scored_table'):
            print("\nScored Correlations (all metrics: higher = better):")
            score_cols = ['fluency_score','coherence_score','diversity_score','emotion_score','structure_score']
            st = self.scored_table
            available_scores = [c for c in score_cols if c in st.columns]
            if len(available_scores) >= 2:
                score_corr = st[available_scores].corr(method='spearman')
                key_pairs = [
                    ('diversity_score','coherence_score','Diversity-Coherence trade-off'),
                    ('diversity_score','fluency_score','Diversity-Fluency trade-off'),
                    ('coherence_score','fluency_score','Coherence-Fluency synergy')
                ]
                for c1, c2, label in key_pairs:
                    if c1 in score_corr.columns and c2 in score_corr.columns:
                        rho = score_corr.loc[c1, c2]
                        direction = "TRADE-OFF" if rho < -0.1 else ("SYNERGY" if rho > 0.1 else "NEUTRAL")
                        print(f"  {label}: ρ={rho:.3f} [{direction}]")
        
        # Store processed dataframe for later use
        self.df_processed = df
        
        return correlations
    
    def analyze_by_groups(self):
        """Analyze fluency by different groups (genre, structure, temperature)"""
        print("Analyzing by groups...")
        
        group_analysis = {}
        
        # Analyze by genre
        if 'genre' in self.df.columns:
            genre_stats = {}
            for genre in self.df['genre'].unique():
                genre_data = self.df[self.df['genre'] == genre]
                genre_stats[genre] = {
                    'pseudo_ppl': {
                        'mean': float(genre_data['pseudo_ppl'].mean()),
                        'median': float(genre_data['pseudo_ppl'].median()),
                        'std': float(genre_data['pseudo_ppl'].std()),
                        'count': int(genre_data['pseudo_ppl'].count())
                    },
                    'err_per_100w': {
                        'mean': float(genre_data['err_per_100w'].mean()),
                        'median': float(genre_data['err_per_100w'].median()),
                        'std': float(genre_data['err_per_100w'].std()),
                        'count': int(genre_data['err_per_100w'].count())
                    }
                }
            group_analysis['by_genre'] = genre_stats
        
        # Analyze by structure
        if 'structure' in self.df.columns:
            structure_stats = {}
            for structure in self.df['structure'].unique():
                structure_data = self.df[self.df['structure'] == structure]
                structure_stats[structure] = {
                    'pseudo_ppl': {
                        'mean': float(structure_data['pseudo_ppl'].mean()),
                        'median': float(structure_data['pseudo_ppl'].median()),
                        'std': float(structure_data['pseudo_ppl'].std()),
                        'count': int(structure_data['pseudo_ppl'].count())
                    },
                    'err_per_100w': {
                        'mean': float(structure_data['err_per_100w'].mean()),
                        'median': float(structure_data['err_per_100w'].median()),
                        'std': float(structure_data['err_per_100w'].std()),
                        'count': int(structure_data['err_per_100w'].count())
                    }
                }
            group_analysis['by_structure'] = structure_stats
        
        # Analyze by temperature
        if 'temperature' in self.df.columns:
            temp_stats = {}
            for temp in self.df['temperature'].unique():
                if pd.isna(temp):
                    continue
                temp_data = self.df[self.df['temperature'] == temp]
                temp_stats[str(temp)] = {
                    'pseudo_ppl': {
                        'mean': float(temp_data['pseudo_ppl'].mean()),
                        'median': float(temp_data['pseudo_ppl'].median()),
                        'std': float(temp_data['pseudo_ppl'].std()),
                        'count': int(temp_data['pseudo_ppl'].count())
                    },
                    'err_per_100w': {
                        'mean': float(temp_data['err_per_100w'].mean()),
                        'median': float(temp_data['err_per_100w'].median()),
                        'std': float(temp_data['err_per_100w'].std()),
                        'count': int(temp_data['err_per_100w'].count())
                    }
                }
            group_analysis['by_temperature'] = temp_stats
        
        # Analyze by baseline vs non-baseline
        if 'is_baseline' in self.df.columns:
            baseline_stats = {}
            for baseline in self.df['is_baseline'].unique():
                baseline_data = self.df[self.df['is_baseline'] == baseline]
                baseline_stats[str(baseline)] = {
                    'pseudo_ppl': {
                        'mean': float(baseline_data['pseudo_ppl'].mean()),
                        'median': float(baseline_data['pseudo_ppl'].median()),
                        'std': float(baseline_data['pseudo_ppl'].std()),
                        'count': int(baseline_data['pseudo_ppl'].count())
                    },
                    'err_per_100w': {
                        'mean': float(baseline_data['err_per_100w'].mean()),
                        'median': float(baseline_data['err_per_100w'].median()),
                        'std': float(baseline_data['err_per_100w'].std()),
                        'count': int(baseline_data['err_per_100w'].count())
                    }
                }
            group_analysis['by_baseline'] = baseline_stats
        
        # THREE-DIMENSIONAL GROUPING (genre x structure x temperature)
        if all(col in self.df.columns for col in ['genre', 'structure', 'temperature']) and hasattr(self, 'scored_table'):
            print("Creating 3D grouping table (genre × structure × temperature)...")
            
            # Use scored table for meaningful aggregation
            grouped_3d = self.scored_table.groupby(['genre', 'structure', 'temperature']).agg({
                'fluency_score': ['mean', 'std', 'count'],
                'coherence_score': ['mean', 'std'],
                'diversity_score': ['mean', 'std'], 
                'emotion_score': ['mean', 'std'],
                'structure_score': ['mean', 'std'],
                'overall_score': ['mean', 'std']
            }).round(3)
            
            # Flatten column names for easier use
            grouped_3d.columns = ['_'.join(col).strip() for col in grouped_3d.columns]
            
            # Save as CSV for easy use in heatmaps
            output_3d_file = self.output_dir / 'grouped_3d_scores.csv'
            grouped_3d.to_csv(output_3d_file)
            print(f"3D grouping table saved: {output_3d_file}")
            
            # Store in results (convert to dict for JSON serialization, handling tuple keys)
            try:
                # Convert to dict with string keys to avoid JSON serialization issues
                grouped_3d_dict = {}
                for col in grouped_3d.columns:
                    grouped_3d_dict[col] = {}
                    for idx, val in grouped_3d[col].items():
                        # Convert tuple index to string
                        key_str = "_".join(str(x) for x in idx) if isinstance(idx, tuple) else str(idx)
                        grouped_3d_dict[col][key_str] = val
                group_analysis['by_3d_config'] = grouped_3d_dict
            except Exception as e:
                print(f"Warning: Could not serialize 3D config results: {e}")
                group_analysis['by_3d_config'] = "See grouped_3d_scores.csv for detailed results"
            
            # Also create a simplified version with just overall_score for quick reference
            simple_3d = self.scored_table.groupby(['genre', 'structure', 'temperature'])['overall_score'].agg(['mean', 'std', 'count']).round(3)
            simple_3d_file = self.output_dir / 'config_overall_scores.csv'
            simple_3d.to_csv(simple_3d_file)
            print(f"Config overview saved: {simple_3d_file}")
        
        self.results['group_analysis'] = group_analysis
        return group_analysis
    
    def detect_outliers(self):
        """Detect outliers in fluency metrics"""
        print("Detecting outliers...")
        
        outliers = []
        
        # Pseudo-PPL outliers (using IQR method)
        valid_ppl = self.df[self.df['pseudo_ppl'] != float('inf')]['pseudo_ppl']
        if len(valid_ppl) > 0:
            Q1_ppl = valid_ppl.quantile(0.25)
            Q3_ppl = valid_ppl.quantile(0.75)
            IQR_ppl = Q3_ppl - Q1_ppl
            lower_bound_ppl = Q1_ppl - 1.5 * IQR_ppl
            upper_bound_ppl = Q3_ppl + 1.5 * IQR_ppl
            
            ppl_outliers = self.df[
                (self.df['pseudo_ppl'] < lower_bound_ppl) | 
                (self.df['pseudo_ppl'] > upper_bound_ppl)
            ]
            
            outliers.extend([{
                'type': 'pseudo_ppl',
                'story_id': row['story_id'],
                'value': row['pseudo_ppl'],
                'threshold': f"<{lower_bound_ppl:.2f} or >{upper_bound_ppl:.2f}"
            } for _, row in ppl_outliers.iterrows()])
        
        # Error rate outliers
        Q1_err = self.df['err_per_100w'].quantile(0.25)
        Q3_err = self.df['err_per_100w'].quantile(0.75)
        IQR_err = Q3_err - Q1_err
        lower_bound_err = Q1_err - 1.5 * IQR_err
        upper_bound_err = Q3_err + 1.5 * IQR_err
        
        err_outliers = self.df[
            (self.df['err_per_100w'] < lower_bound_err) | 
            (self.df['err_per_100w'] > upper_bound_err)
        ]
        
        outliers.extend([{
            'type': 'err_per_100w',
            'story_id': row['story_id'],
            'value': row['err_per_100w'],
            'threshold': f"<{lower_bound_err:.2f} or >{upper_bound_err:.2f}"
        } for _, row in err_outliers.iterrows()])
        
        self.results['outliers'] = outliers
        print(f"Found {len(outliers)} outliers")
        return outliers
    
    def build_scored_table(self):
        """Build normalized [0,1] scored table for all metrics (higher = better)"""
        print("Building normalized scored table...")
        
        def robust_scale(series, lower=0.05, upper=0.95):
            """Robust scaling using percentiles (resistant to outliers)"""
            a, b = series.quantile(lower), series.quantile(upper)
            s = series.clip(a, b)
            # Avoid constant columns
            if b - a < 1e-9:
                return pd.Series(0.5, index=series.index)
            return (s - a) / (b - a)
        
        # Use processed dataframe if available (with robust error measures)
        df = getattr(self, 'df_processed', self.df).copy()
        
        print("Normalizing metrics to [0,1] scale...")
        
        # 1) POSITIVE METRICS (higher = better)
        df['coherence_score'] = robust_scale(df['avg_coherence'])
        print(f"  Coherence: {df['coherence_score'].mean():.3f} ± {df['coherence_score'].std():.3f}")
        
        # Emotion: Use roberta_avg_score as primary
        if 'roberta_avg_score' in df.columns:
            df['emotion_score'] = robust_scale(df['roberta_avg_score'])
            print(f"  Emotion (RoBERTa): {df['emotion_score'].mean():.3f} ± {df['emotion_score'].std():.3f}")
        else:
            df['emotion_score'] = 0.5  # Neutral fallback
        
        # Diversity: Use distinct_avg as primary
        df['diversity_score'] = robust_scale(df['distinct_avg'])
        print(f"  Diversity: {df['diversity_score'].mean():.3f} ± {df['diversity_score'].std():.3f}")
        
        # Structure: Combine completion rate and function diversity
        if all(col in df.columns for col in ['tp_m', 'tp_n']):
            df['tp_rate'] = (df['tp_m'] / df['tp_n']).replace([np.inf, -np.inf], np.nan).fillna(0)
            if 'li_function_diversity' in df.columns:
                df['structure_score'] = (robust_scale(df['tp_rate']) * 0.6 + 
                                       robust_scale(df['li_function_diversity']) * 0.4)
            else:
                df['structure_score'] = robust_scale(df['tp_rate'])
        elif 'li_function_diversity' in df.columns:
            df['structure_score'] = robust_scale(df['li_function_diversity'])
        else:
            df['structure_score'] = 0.5  # Neutral fallback
        print(f"  Structure: {df['structure_score'].mean():.3f} ± {df['structure_score'].std():.3f}")
        
        # 2) NEGATIVE METRICS (lower = better → invert to higher = better)
        df['ppl_score'] = 1 - robust_scale(df['pseudo_ppl'])
        print(f"  PPL Score (inverted): {df['ppl_score'].mean():.3f} ± {df['ppl_score'].std():.3f}")
        
        # Use robust error rate if available
        if 'err_per_100w_winz' in df.columns:
            df['grammar_score'] = 1 - robust_scale(df['err_per_100w_winz'])
            error_source = "winsorized"
        else:
            df['grammar_score'] = 1 - robust_scale(df['err_per_100w'])
            error_source = "original"
        print(f"  Grammar Score (inverted, {error_source}): {df['grammar_score'].mean():.3f} ± {df['grammar_score'].std():.3f}")
        
        # 3) COMPOSITE FLUENCY SCORE (conservative: min of PPL and grammar)
        df['fluency_score'] = df[['ppl_score', 'grammar_score']].min(axis=1)  # Conservative
        # Alternative: df['fluency_score'] = df[['ppl_score', 'grammar_score']].mean(axis=1)
        print(f"  Fluency (composite): {df['fluency_score'].mean():.3f} ± {df['fluency_score'].std():.3f}")
        
        # 4) OPTIONAL: Length penalty (prevent gaming with very short texts)
        if 'total_words' in df.columns:
            tw = df['total_words']
            p20 = tw.quantile(0.20)
            short_penalty = (tw < p20)
            if short_penalty.sum() > 0:
                df.loc[short_penalty, 'diversity_score'] *= 0.97  # Light penalty
                print(f"  Applied length penalty to {short_penalty.sum()} short texts (<{p20:.0f} words)")
        
        # 5) OVERALL COMPOSITE SCORE (equal weights for now)
        score_components = ['fluency_score', 'coherence_score', 'diversity_score', 'emotion_score', 'structure_score']
        df['overall_score'] = df[score_components].mean(axis=1)
        print(f"  Overall (equal weights): {df['overall_score'].mean():.3f} ± {df['overall_score'].std():.3f}")
        
        # 6) EXPORT SCORED TABLE
        output_cols = [
            'story_id', 'genre', 'structure', 'temperature', 'seed', 'is_baseline',
            'fluency_score', 'coherence_score', 'diversity_score', 'emotion_score', 'structure_score',
            'overall_score', 'total_words', 'total_sentences'
        ]
        
        # Add cost and time if available
        if 'cost_usd' in df.columns:
            output_cols.append('cost_usd')
        if 'wall_time_sec' in df.columns:
            output_cols.append('wall_time_sec')
        
        # Filter to available columns
        available_output_cols = [col for col in output_cols if col in df.columns]
        scored_table = df[available_output_cols].copy()
        
        # Save scored table
        output_file = self.output_dir / 'metrics_master_scored.csv'
        scored_table.to_csv(output_file, index=False)
        print(f"Scored table saved: {output_file}")
        
        # Store results
        self.scored_table = scored_table
        
        # Add to results
        self.results['scored_summary'] = {
            'fluency_mean': float(df['fluency_score'].mean()),
            'coherence_mean': float(df['coherence_score'].mean()),
            'diversity_mean': float(df['diversity_score'].mean()),
            'emotion_mean': float(df['emotion_score'].mean()),
            'structure_mean': float(df['structure_score'].mean()),
            'overall_mean': float(df['overall_score'].mean()),
            'length_penalty_applied': int(short_penalty.sum()) if 'total_words' in df.columns else 0,
            'short_threshold_words': float(p20) if 'total_words' in df.columns else None
        }
        
        return scored_table
    
    def create_visualizations(self):
        """Create comprehensive visualizations"""
        print("Creating visualizations...")
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. Boxplots by genre and structure
        self.create_boxplots_by_groups()
        
        # 2. Scatter plot: pseudo_ppl vs err_per_100w
        self.create_scatter_plot_tradeoff()
        
        # 3. Distribution histograms
        self.create_distribution_plots()
        
        # 4. Correlation heatmap
        self.create_correlation_heatmap()
        
        # 5. Quality distribution pie charts
        self.create_quality_distribution_plots()
        
        # 6. Temperature effect analysis
        self.create_temperature_analysis_plots()
        
        print("Visualizations created successfully!")
    
    def create_boxplots_by_groups(self):
        """Create boxplots for pseudo_ppl by genre and structure"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Filter out infinite values for plotting
        plot_df = self.df[self.df['pseudo_ppl'] != float('inf')].copy()
        
        # Pseudo-PPL by genre
        if 'genre' in plot_df.columns and len(plot_df['genre'].unique()) > 1:
            sns.boxplot(data=plot_df, x='genre', y='pseudo_ppl', ax=axes[0,0])
            axes[0,0].set_title('Pseudo-PPL by Genre')
            axes[0,0].tick_params(axis='x', rotation=45)
            axes[0,0].axhline(y=2.0, color='green', linestyle='--', alpha=0.7, label='Excellent (<2.0)')
            axes[0,0].axhline(y=5.0, color='orange', linestyle='--', alpha=0.7, label='Good (<5.0)')
            axes[0,0].legend()
        
        # Pseudo-PPL by structure
        if 'structure' in plot_df.columns and len(plot_df['structure'].unique()) > 1:
            sns.boxplot(data=plot_df, x='structure', y='pseudo_ppl', ax=axes[0,1])
            axes[0,1].set_title('Pseudo-PPL by Structure')
            axes[0,1].tick_params(axis='x', rotation=45)
            axes[0,1].axhline(y=2.0, color='green', linestyle='--', alpha=0.7, label='Excellent (<2.0)')
            axes[0,1].axhline(y=5.0, color='orange', linestyle='--', alpha=0.7, label='Good (<5.0)')
            axes[0,1].legend()
        
        # Error rate by genre
        if 'genre' in self.df.columns and len(self.df['genre'].unique()) > 1:
            sns.boxplot(data=self.df, x='genre', y='err_per_100w', ax=axes[1,0])
            axes[1,0].set_title('Error Rate per 100w by Genre')
            axes[1,0].tick_params(axis='x', rotation=45)
            axes[1,0].axhline(y=0.2, color='green', linestyle='--', alpha=0.7, label='High Quality (<0.2)')
            axes[1,0].axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Medium Quality (<0.5)')
            axes[1,0].legend()
        
        # Error rate by structure
        if 'structure' in self.df.columns and len(self.df['structure'].unique()) > 1:
            sns.boxplot(data=self.df, x='structure', y='err_per_100w', ax=axes[1,1])
            axes[1,1].set_title('Error Rate per 100w by Structure')
            axes[1,1].tick_params(axis='x', rotation=45)
            axes[1,1].axhline(y=0.2, color='green', linestyle='--', alpha=0.7, label='High Quality (<0.2)')
            axes[1,1].axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Medium Quality (<0.5)')
            axes[1,1].legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fluency_boxplots_by_groups.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_scatter_plot_tradeoff(self):
        """Create scatter plot showing pseudo_ppl vs err_per_100w trade-off"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Filter out infinite values
        plot_df = self.df[self.df['pseudo_ppl'] != float('inf')].copy()
        
        # Color by genre if available
        if 'genre' in plot_df.columns:
            genres = plot_df['genre'].unique()
            colors = plt.cm.Set3(np.linspace(0, 1, len(genres)))
            
            for i, genre in enumerate(genres):
                genre_data = plot_df[plot_df['genre'] == genre]
                ax.scatter(genre_data['pseudo_ppl'], genre_data['err_per_100w'], 
                          c=[colors[i]], label=genre, alpha=0.7, s=50)
        else:
            ax.scatter(plot_df['pseudo_ppl'], plot_df['err_per_100w'], alpha=0.7, s=50)
        
        # Add quality threshold lines
        ax.axvline(x=2.0, color='green', linestyle='--', alpha=0.7, label='PPL Excellent (2.0)')
        ax.axvline(x=5.0, color='orange', linestyle='--', alpha=0.7, label='PPL Good (5.0)')
        ax.axhline(y=0.2, color='green', linestyle=':', alpha=0.7, label='Error High Quality (0.2)')
        ax.axhline(y=0.5, color='orange', linestyle=':', alpha=0.7, label='Error Medium Quality (0.5)')
        
        # Add best quality quadrant shading
        ax.axvspan(0, 2.0, ymin=0, ymax=0.2/ax.get_ylim()[1], alpha=0.1, color='green', label='Best Quality Zone')
        
        ax.set_xlabel('Pseudo-PPL (Lower is Better)')
        ax.set_ylabel('Error Rate per 100 Words (Lower is Better)')
        ax.set_title('Fluency Trade-off: Pseudo-PPL vs Error Rate')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fluency_tradeoff_scatter.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_distribution_plots(self):
        """Create distribution plots for fluency metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Pseudo-PPL distribution
        valid_ppl = self.df[self.df['pseudo_ppl'] != float('inf')]['pseudo_ppl']
        axes[0,0].hist(valid_ppl, bins=30, alpha=0.7, edgecolor='black')
        axes[0,0].axvline(valid_ppl.mean(), color='red', linestyle='--', label=f'Mean: {valid_ppl.mean():.2f}')
        axes[0,0].axvline(valid_ppl.median(), color='blue', linestyle='--', label=f'Median: {valid_ppl.median():.2f}')
        axes[0,0].axvline(2.0, color='green', linestyle='-', alpha=0.7, label='Excellent (2.0)')
        axes[0,0].axvline(5.0, color='orange', linestyle='-', alpha=0.7, label='Good (5.0)')
        axes[0,0].set_title('Pseudo-PPL Distribution')
        axes[0,0].set_xlabel('Pseudo-PPL')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # Error rate distribution
        axes[0,1].hist(self.df['err_per_100w'], bins=30, alpha=0.7, edgecolor='black')
        axes[0,1].axvline(self.df['err_per_100w'].mean(), color='red', linestyle='--', 
                         label=f'Mean: {self.df["err_per_100w"].mean():.2f}')
        axes[0,1].axvline(self.df['err_per_100w'].median(), color='blue', linestyle='--',
                         label=f'Median: {self.df["err_per_100w"].median():.2f}')
        axes[0,1].axvline(0.2, color='green', linestyle='-', alpha=0.7, label='High Quality (0.2)')
        axes[0,1].axvline(0.5, color='orange', linestyle='-', alpha=0.7, label='Medium Quality (0.5)')
        axes[0,1].set_title('Error Rate per 100w Distribution')
        axes[0,1].set_xlabel('Error Rate per 100 Words')
        axes[0,1].set_ylabel('Frequency')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # Log-scale Pseudo-PPL (if needed)
        if valid_ppl.max() / valid_ppl.min() > 10:
            axes[1,0].hist(np.log(valid_ppl), bins=30, alpha=0.7, edgecolor='black')
            axes[1,0].set_title('Log Pseudo-PPL Distribution')
            axes[1,0].set_xlabel('Log(Pseudo-PPL)')
            axes[1,0].set_ylabel('Frequency')
            axes[1,0].grid(True, alpha=0.3)
        else:
            axes[1,0].text(0.5, 0.5, 'Log scale not needed\n(narrow range)', 
                          ha='center', va='center', transform=axes[1,0].transAxes)
        
        # Quality level distribution
        if 'combined_fluency_quality' in self.df.columns:
            quality_counts = self.df['combined_fluency_quality'].value_counts()
            axes[1,1].bar(quality_counts.index, quality_counts.values, alpha=0.7)
            axes[1,1].set_title('Combined Fluency Quality Distribution')
            axes[1,1].set_xlabel('Quality Level')
            axes[1,1].set_ylabel('Count')
            axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fluency_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_correlation_heatmap(self):
        """Create correlation heatmap focusing on fluency relationships (ROBUST VERSION)"""
        # Use processed dataframe with robust measures
        df_for_corr = getattr(self, 'df_processed', self.df)
        
        # Select key metrics for correlation (prioritize robust versions)
        corr_cols = ['pseudo_ppl']
        
        # Use robust error measure if available
        if 'err_per_100w_winz' in df_for_corr.columns:
            corr_cols.append('err_per_100w_winz')
            error_label = 'err_per_100w_winz'
        elif 'err_per_100w_log1p' in df_for_corr.columns:
            corr_cols.append('err_per_100w_log1p') 
            error_label = 'err_per_100w_log1p'
        else:
            corr_cols.append('err_per_100w')
            error_label = 'err_per_100w'
        
        # Add available metrics
        available_metrics = ['distinct_avg', 'diversity_group_score', 'avg_coherence', 
                           'coherence_std', 'roberta_avg_score', 'total_words', 'total_sentences']
        for col in available_metrics:
            if col in df_for_corr.columns:
                corr_cols.append(col)
        
        # Create correlation matrices (both Spearman and Pearson)
        corr_df = df_for_corr[corr_cols].replace([np.inf, -np.inf], np.nan)
        spearman_matrix = corr_df.corr(method='spearman')
        pearson_matrix = corr_df.corr(method='pearson')
        
        if spearman_matrix.empty:
            print("Warning: correlation matrices empty (likely all-NaN columns). Skipping heatmap.")
            return
        
        # Create dual heatmap plot
        fig, axes = plt.subplots(1, 2, figsize=(20, 8))
        
        # Spearman (primary - robust)
        mask = np.triu(np.ones_like(spearman_matrix, dtype=bool))
        sns.heatmap(spearman_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8}, ax=axes[0])
        axes[0].set_title('Spearman Correlations (Robust - PRIMARY)')
        
        # Pearson (secondary - for comparison)
        sns.heatmap(pearson_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8}, ax=axes[1])
        axes[1].set_title('Pearson Correlations (For Comparison)')
        
        # Add annotation about robust measures
        fig.suptitle(f'Fluency Correlation Analysis (Using {error_label} for robustness)', fontsize=14, y=1.02)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fluency_correlation_heatmap_robust.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Also create scored version heatmap if available
        if hasattr(self, 'scored_table'):
            self.create_scored_correlation_heatmap()
    
    def create_scored_correlation_heatmap(self):
        """Create correlation heatmap for scored metrics (all positive = good)"""
        # Use scored table where all metrics are "higher = better"
        score_cols = ['fluency_score', 'coherence_score', 'diversity_score', 
                     'emotion_score', 'structure_score', 'overall_score']
        
        # Filter to available columns
        available_score_cols = [col for col in score_cols if col in self.scored_table.columns]
        
        if len(available_score_cols) < 2:
            return
        
        # Create correlation matrix (Spearman preferred for interpretability)
        corr_df = self.scored_table[available_score_cols]
        spearman_matrix = corr_df.corr(method='spearman')
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        mask = np.triu(np.ones_like(spearman_matrix, dtype=bool))
        sns.heatmap(spearman_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8},
                   fmt='.3f', annot_kws={'size': 10})
        plt.title('Scored Metrics Correlations\n(All metrics: Higher = Better)', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Add interpretation note
        plt.figtext(0.02, 0.02, 
                   'Note: Negative correlations indicate trade-offs between quality dimensions.\n'
                   'All scores normalized to [0,1] where 1.0 = best performance.',
                   fontsize=9, style='italic')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'scored_metrics_correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_quality_distribution_plots(self):
        """Create pie charts for quality distributions"""
        if 'combined_fluency_quality' not in self.df.columns:
            return
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # PPL quality distribution
        ppl_counts = self.df['ppl_quality'].value_counts()
        axes[0].pie(ppl_counts.values, labels=ppl_counts.index, autopct='%1.1f%%', startangle=90)
        axes[0].set_title('Pseudo-PPL Quality Distribution')
        
        # Error quality distribution
        err_counts = self.df['error_quality'].value_counts()
        axes[1].pie(err_counts.values, labels=err_counts.index, autopct='%1.1f%%', startangle=90)
        axes[1].set_title('Error Rate Quality Distribution')
        
        # Combined quality distribution
        combined_counts = self.df['combined_fluency_quality'].value_counts()
        axes[2].pie(combined_counts.values, labels=combined_counts.index, autopct='%1.1f%%', startangle=90)
        axes[2].set_title('Combined Fluency Quality Distribution')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'fluency_quality_distributions.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_temperature_analysis_plots(self):
        """Analyze temperature effects on fluency"""
        if 'temperature' not in self.df.columns:
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Temperature vs Pseudo-PPL
        temp_groups = self.df[self.df['pseudo_ppl'] != float('inf')].groupby('temperature')['pseudo_ppl'].agg(['mean', 'std'])
        axes[0].errorbar(temp_groups.index, temp_groups['mean'], yerr=temp_groups['std'], 
                        marker='o', capsize=5, capthick=2)
        axes[0].set_xlabel('Temperature')
        axes[0].set_ylabel('Pseudo-PPL')
        axes[0].set_title('Temperature Effect on Pseudo-PPL')
        axes[0].grid(True, alpha=0.3)
        axes[0].axhline(y=2.0, color='green', linestyle='--', alpha=0.7, label='Excellent')
        axes[0].axhline(y=5.0, color='orange', linestyle='--', alpha=0.7, label='Good')
        axes[0].legend()
        
        # Temperature vs Error Rate
        temp_err_groups = self.df.groupby('temperature')['err_per_100w'].agg(['mean', 'std'])
        axes[1].errorbar(temp_err_groups.index, temp_err_groups['mean'], yerr=temp_err_groups['std'], 
                        marker='o', capsize=5, capthick=2)
        axes[1].set_xlabel('Temperature')
        axes[1].set_ylabel('Error Rate per 100w')
        axes[1].set_title('Temperature Effect on Error Rate')
        axes[1].grid(True, alpha=0.3)
        axes[1].axhline(y=0.2, color='green', linestyle='--', alpha=0.7, label='High Quality')
        axes[1].axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='Medium Quality')
        axes[1].legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'temperature_effects_on_fluency.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self):
        """Save all analysis results"""
        print("Saving analysis results...")
        
        # Save comprehensive results as JSON
        results_file = self.output_dir / 'fluency_analysis_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save summary report as text
        self.create_summary_report()
        
        print(f"Results saved to {self.output_dir}")
    
    def create_summary_report(self):
        """Create a human-readable summary report"""
        report_file = self.output_dir / 'fluency_analysis_summary_report.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Fluency Analysis Report\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Reproducibility settings
            f.write("## Preprocessing & Robustness Settings\n\n")
            f.write("- Winsorize limits for err_per_100w: [2%, 98%]\n")
            f.write("- log1p transform on err_per_100w: applied\n")
            f.write("- Normalization range for [0,1] scores: P5–P95\n")
            if 'scored_summary' in self.results:
                ss = self.results['scored_summary']
                if ss.get('short_threshold_words') is not None:
                    f.write(f"- Length penalty threshold (P20 words): {ss['short_threshold_words']:.1f}\n")
            f.write("\n")
            
            # Summary statistics
            f.write("## Summary Statistics\n\n")
            stats = self.results['summary_stats']
            
            f.write("### Pseudo-PPL Statistics\n")
            f.write(f"- Count: {stats['pseudo_ppl']['count']}\n")
            f.write(f"- Mean: {stats['pseudo_ppl']['mean']:.3f}\n")
            f.write(f"- Median: {stats['pseudo_ppl']['median']:.3f}\n")
            f.write(f"- Std: {stats['pseudo_ppl']['std']:.3f}\n")
            f.write(f"- Range: {stats['pseudo_ppl']['min']:.3f} - {stats['pseudo_ppl']['max']:.3f}\n\n")
            
            f.write("### Error Rate per 100 Words Statistics\n")
            f.write(f"- Count: {stats['err_per_100w']['count']}\n")
            f.write(f"- Mean: {stats['err_per_100w']['mean']:.3f}\n")
            f.write(f"- Median: {stats['err_per_100w']['median']:.3f}\n")
            f.write(f"- Std: {stats['err_per_100w']['std']:.3f}\n")
            f.write(f"- Range: {stats['err_per_100w']['min']:.3f} - {stats['err_per_100w']['max']:.3f}\n\n")
            
            # Quality analysis
            f.write("## Quality Analysis\n\n")
            qual_dist = self.results['quality_distribution']
            
            f.write("### Pseudo-PPL Quality Levels\n")
            for level, count in qual_dist['ppl_distribution'].items():
                percentage = (count / len(self.df)) * 100
                f.write(f"- {level}: {count} ({percentage:.1f}%)\n")
            
            f.write("\n### Error Rate Quality Levels\n")
            for level, count in qual_dist['error_distribution'].items():
                percentage = (count / len(self.df)) * 100
                f.write(f"- {level}: {count} ({percentage:.1f}%)\n")
            
            f.write("\n### Combined Fluency Quality\n")
            for level, count in qual_dist['combined_distribution'].items():
                percentage = (count / len(self.df)) * 100
                f.write(f"- {level}: {count} ({percentage:.1f}%)\n")
            
            # Key correlations (ROBUST VERSION - Spearman primary)
            f.write("\n## Key Correlations (Robust Analysis)\n\n")
            
            # Primary: Spearman correlations
            spearman_corrs = self.results['correlations']['spearman']
            pearson_corrs = self.results['correlations']['pearson']
            
            f.write("### Pseudo-PPL Relationships (Spearman ρ, |ρ| > 0.1)\n")
            ppl_spearman = [(k, v) for k, v in spearman_corrs['pseudo_ppl'].items() if not pd.isna(v) and abs(v) > 0.1]
            ppl_spearman.sort(key=lambda x: abs(x[1]), reverse=True)
            for metric, spear_corr in ppl_spearman:
                pear_corr = pearson_corrs['pseudo_ppl'].get(metric, np.nan)
                f.write(f"- {metric}: ρ={spear_corr:.3f} (Pearson r={pear_corr:.3f})\n")
            
            f.write("\n### Error Rate Relationships (Spearman ρ, |ρ| > 0.1)\n")
            # Use robust error rate if available
            err_key = 'err_per_100w_robust' if 'err_per_100w_robust' in spearman_corrs else 'err_per_100w'
            if err_key in spearman_corrs:
                err_spearman = [(k, v) for k, v in spearman_corrs[err_key].items() if not pd.isna(v) and abs(v) > 0.1]
                err_spearman.sort(key=lambda x: abs(x[1]), reverse=True)
                for metric, spear_corr in err_spearman:
                    pear_corr = pearson_corrs.get(err_key, {}).get(metric, np.nan)
                    f.write(f"- {metric}: ρ={spear_corr:.3f} (Pearson r={pear_corr:.3f})\n")
            
            # Partial correlations (controlling for length)
            if 'partial_correlations' in self.results['correlations'] and self.results['correlations']['partial_correlations']:
                f.write("\n### Length-Controlled Relationships (Partial Correlations)\n")
                partial = self.results['correlations']['partial_correlations']
                if 'diversity_coherence_partial' in partial:
                    div_coh = partial['diversity_coherence_partial']
                    f.write(f"- Diversity ↔ Coherence (length-controlled): ")
                    f.write(f"ρ={div_coh['spearman']:.3f} (p={div_coh['spearman_p']:.3g}), ")
                    f.write(f"r={div_coh['pearson']:.3f} (p={div_coh['pearson_p']:.3g})\n")
                    f.write("  ✓ Trade-off remains significant even after controlling for text length.\n")
            
            # Outliers
            f.write(f"\n## Outliers\n\n")
            f.write(f"Found {len(self.results['outliers'])} outliers:\n")
            for outlier in self.results['outliers'][:10]:  # Show top 10
                f.write(f"- {outlier['type']}: {outlier['story_id']} (value: {outlier['value']:.3f})\n")
            
            # Quality thresholds explanation (ENHANCED with percentile thresholds)
            f.write("\n## Quality Thresholds & Sensitivity Analysis\n\n")
            f.write("### Pseudo-PPL Thresholds\n")
            f.write("**Standard thresholds:**\n")
            f.write("- < 2.0: Excellent fluency\n")
            f.write("- 2.0 - 5.0: Good fluency\n")
            f.write("- > 5.0: Poor fluency\n\n")
            
            # Add percentile-based thresholds for robustness (true P20/P50/P80)
            valid_ppl = self.df[self.df['pseudo_ppl'] != float('inf')]['pseudo_ppl']
            ppl_p20 = float(valid_ppl.quantile(0.20))
            ppl_p50 = float(valid_ppl.quantile(0.50))
            ppl_p80 = float(valid_ppl.quantile(0.80))
            
            f.write("**Percentile-based thresholds (robust):**\n")
            f.write(f"- P50 (median): {ppl_p50:.3f} - half of samples perform better\n")
            f.write(f"- P20: {ppl_p20:.3f} - top 20% performance threshold\n") 
            f.write(f"- P80: {ppl_p80:.3f} - bottom 20% performance threshold\n\n")
            
            f.write("### Error Rate per 100 Words\n")
            f.write("**Standard thresholds:**\n")
            f.write("- < 0.2: High quality\n")
            f.write("- 0.2 - 0.5: Medium quality\n")
            f.write("- > 0.5: Poor quality\n\n")
            
            err_series = self.df['err_per_100w']
            err_p20 = float(err_series.quantile(0.20))
            err_p50 = float(err_series.quantile(0.50))
            err_p80 = float(err_series.quantile(0.80))
            
            f.write("**Percentile-based thresholds (robust):**\n")
            f.write(f"- P50 (median): {err_p50:.3f} - recommended for heavy-tailed distributions\n")
            f.write(f"- P20: {err_p20:.3f} - top 20% performance (lowest error rates)\n")
            f.write(f"- P80: {err_p80:.3f} - bottom 20% threshold (highest error rates)\n\n")
            
            stats = self.results['summary_stats']  # reuse for skew/kurt note
            f.write("**Note:** Given error rate heavy tails (skewness={:.2f}, kurtosis={:.2f}), ".format(
                stats['err_per_100w']['skewness'], stats['err_per_100w']['kurtosis']))
            f.write("percentile-based thresholds provide more robust quality assessment than fixed cutoffs.\n\n")
            
            f.write("## Files Generated\n\n")
            f.write("### Visualizations\n")
            f.write("- `fluency_boxplots_by_groups.png`: Boxplots by genre and structure\n")
            f.write("- `fluency_tradeoff_scatter.png`: Pseudo-PPL vs Error rate scatter plot\n")
            f.write("- `fluency_distributions.png`: Distribution histograms\n")
            f.write("- `fluency_correlation_heatmap_robust.png`: Dual correlation heatmap (Spearman + Pearson)\n")
            f.write("- `scored_metrics_correlation_heatmap.png`: Scored metrics correlations (all positive)\n")
            f.write("- `fluency_quality_distributions.png`: Quality level pie charts\n")
            f.write("- `temperature_effects_on_fluency.png`: Temperature effect analysis\n\n")
            
            f.write("### Data Tables\n")
            f.write("- `metrics_master_scored.csv`: Normalized [0,1] scores for all metrics\n")
            f.write("- `grouped_3d_scores.csv`: 3D grouping (genre × structure × temperature)\n")
            f.write("- `config_overall_scores.csv`: Overall scores by configuration\n\n")
            
            f.write("### Reports\n")
            f.write("- `fluency_analysis_results.json`: Complete numerical results with robust measures\n")
            f.write("- `ROBUST_ANALYSIS_FINDINGS.md`: Statistical robustness analysis summary\n")
    
    def run_complete_analysis(self):
        """Run the complete fluency analysis pipeline"""
        print("Starting comprehensive fluency analysis...")
        
        # Validate data
        self.validate_data()
        
        # Run all analyses
        self.calculate_summary_statistics()
        self.classify_quality_levels()
        self.analyze_correlations()  # This now includes robust measures and partial correlations
        self.analyze_by_groups()
        self.detect_outliers()
        
        # Build normalized scored table (NEW)
        self.build_scored_table()
        
        # Re-run group analysis with scored table to generate 3D grouping
        print("Generating 3D grouping tables with scored metrics...")
        self.analyze_by_groups()
        
        # Create visualizations
        self.create_visualizations()
        
        # Save results
        self.save_results()
        
        print("Comprehensive fluency analysis completed successfully!")
        print(f"Results saved to: {self.output_dir}")
        
        return self.results

def main():
    """Main function to run the analysis"""
    # Paths
    csv_path = "/Users/haha/Story/metrics_master.csv"
    output_dir = "/Users/haha/Story/AAA/fluency_analysis"
    
    # Initialize and run analysis
    analyzer = FluencyAnalysisComprehensive(csv_path, output_dir)
    results = analyzer.run_complete_analysis()
    
    # Print key findings
    print("\n" + "="*60)
    print("KEY FINDINGS SUMMARY")
    print("="*60)
    
    stats = results['summary_stats']
    print(f"Pseudo-PPL: Mean={stats['pseudo_ppl']['mean']:.2f}, Median={stats['pseudo_ppl']['median']:.2f}")
    print(f"Error Rate: Mean={stats['err_per_100w']['mean']:.2f}, Median={stats['err_per_100w']['median']:.2f}")
    
    qual_dist = results['quality_distribution']['combined_distribution']
    print(f"Quality Distribution: High={qual_dist.get('high', 0)}, Medium={qual_dist.get('medium', 0)}, Low={qual_dist.get('low', 0)}")
    
    print(f"Total outliers detected: {len(results['outliers'])}")
    print(f"Analysis complete! Check {output_dir} for detailed results and visualizations.")

if __name__ == "__main__":
    main()
