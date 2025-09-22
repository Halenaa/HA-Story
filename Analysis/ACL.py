import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import shapiro, normaltest
import warnings
warnings.filterwarnings('ignore')

# Load data
print("=== 4.1.1 METRIC ROBUSTNESS ANALYSIS ===")
data = pd.read_csv('clean.csv')
print(f"Total configurations: {len(data)}")
print(f"Baseline configurations: {len(data[data.is_baseline == 1])}")
print(f"System configurations: {len(data[data.is_baseline == 0])}")

# Define core metrics based on methodology Section 3.2
core_metrics = {
    'fluency': {
        'primary': ['pseudo_ppl', 'err_per_100w'],
        'auxiliary': ['error_count', 'fluency_word_count']
    },
    'diversity': {
        'primary': ['distinct_avg', 'self_bleu_group', 'one_minus_self_bleu'],
        'auxiliary': ['distinct_score', 'diversity_group_score']
    },
    'coherence': {
        'primary': ['avg_semantic_continuity'],
        'auxiliary': ['semantic_continuity_sentence_count', 'semantic_continuity_std', 
                     'semantic_continuity_median', 'low_continuity_points', 'high_continuity_segments']
    },
    'emotion': {
        'primary': ['roberta_avg_score', 'emotion_correlation'],
        'auxiliary': ['roberta_std', 'labmt_std', 'correlation_coefficient', 
                     'direction_consistency', 'major_disagreements']
    },
    'structure': {
        'primary': ['tp_completion_rate', 'li_function_diversity'],
        'auxiliary': ['tp_coverage', 'total_events', 'chapter_count']
    },
    'efficiency': {
        'primary': ['cost_usd', 'wall_time_sec', 'tokens_total'],
        'auxiliary': ['total_words', 'total_sentences', 'peak_mem_mb']
    }
}

# ===== Core Functions =====

def analyze_distribution_characteristics(series, metric_name):
    """Analyze distribution characteristics and statistical properties"""
    # Remove invalid values
    valid_data = series.dropna()
    valid_data = valid_data[np.isfinite(valid_data)]
    
    if len(valid_data) < 10:
        return {
            'metric': metric_name,
            'n': len(valid_data),
            'data_completeness_pct': len(valid_data) / len(series) * 100,
            'error': 'Insufficient data for reliable analysis'
        }
    
    # Basic descriptive statistics
    n = len(valid_data)
    mean = valid_data.mean()
    std = valid_data.std()
    median = valid_data.median()
    min_val = valid_data.min()
    max_val = valid_data.max()
    
    # Quantiles for robustness
    q1 = valid_data.quantile(0.25)
    q3 = valid_data.quantile(0.75)
    iqr = q3 - q1
    p5 = valid_data.quantile(0.05)
    p95 = valid_data.quantile(0.95)
    
    # Distribution shape indicators
    skewness = stats.skew(valid_data)
    kurtosis = stats.kurtosis(valid_data)
    
    # Normality tests (use different tests based on sample size)
    if n >= 20:
        # Shapiro-Wilk test for smaller samples
        if n <= 5000:
            shapiro_stat, shapiro_p = shapiro(valid_data)
        else:
            shapiro_stat, shapiro_p = np.nan, np.nan
        
        # D'Agostino's normality test for larger samples
        dagostino_stat, dagostino_p = normaltest(valid_data)
    else:
        shapiro_stat, shapiro_p = np.nan, np.nan
        dagostino_stat, dagostino_p = np.nan, np.nan
    
    return {
        'metric': metric_name,
        'n': n,
        'data_completeness_pct': round(len(valid_data) / len(series) * 100, 1),
        'mean': round(mean, 4),
        'std': round(std, 4),
        'median': round(median, 4),
        'min': round(min_val, 4),
        'max': round(max_val, 4),
        'range': round(max_val - min_val, 4),
        'q1': round(q1, 4),
        'q3': round(q3, 4),
        'iqr': round(iqr, 4),
        'p5': round(p5, 4),
        'p95': round(p95, 4),
        'skewness': round(skewness, 4),
        'kurtosis': round(kurtosis, 4),
        'shapiro_stat': round(shapiro_stat, 4) if not np.isnan(shapiro_stat) else None,
        'shapiro_p': round(shapiro_p, 4) if not np.isnan(shapiro_p) else None,
        'dagostino_p': round(dagostino_p, 4) if not np.isnan(dagostino_p) else None
    }

def detect_outliers_comprehensive(series, metric_name):
    """Comprehensive outlier detection and analysis"""
    valid_data = series.dropna()
    valid_data = valid_data[np.isfinite(valid_data)]
    
    if len(valid_data) < 10:
        return {
            'metric': metric_name,
            'outliers_count': 0,
            'outlier_rate_pct': 0,
            'note': 'Insufficient data for outlier detection'
        }
    
    # IQR method
    q1 = valid_data.quantile(0.25)
    q3 = valid_data.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    iqr_outliers = valid_data[(valid_data < lower_bound) | (valid_data > upper_bound)]
    
    # Z-score method (as supplementary)
    z_scores = np.abs(stats.zscore(valid_data))
    z_outliers = valid_data[z_scores > 2.5]
    
    return {
        'metric': metric_name,
        'total_values': len(valid_data),
        'iqr_outliers_count': len(iqr_outliers),
        'iqr_outlier_rate_pct': round(len(iqr_outliers) / len(valid_data) * 100, 2),
        'z_outliers_count': len(z_outliers),
        'z_outlier_rate_pct': round(len(z_outliers) / len(valid_data) * 100, 2),
        'lower_bound': round(lower_bound, 4),
        'upper_bound': round(upper_bound, 4),
        'outlier_values': [round(x, 4) for x in iqr_outliers.head(5)]
    }

def analyze_seed_stability(data_subset, metric_name):
    """Analyze stability across different seeds within same configuration"""
    # Group by configuration parameters (excluding seed)
    config_cols = ['genre', 'structure', 'temperature']
    available_cols = [col for col in config_cols if col in data_subset.columns]
    
    if not available_cols:
        return {
            'metric': metric_name,
            'note': 'Configuration columns not available'
        }
    
    # Create configuration identifier
    data_subset = data_subset.copy()
    data_subset['config_id'] = data_subset[available_cols].astype(str).agg('_'.join, axis=1)
    
    config_groups = data_subset.groupby('config_id')
    
    stability_stats = []
    unstable_configs = []
    
    for config_name, config_data in config_groups:
        values = config_data[metric_name].dropna()
        values = values[np.isfinite(values)]
        
        if len(values) < 2:
            continue
            
        mean_val = values.mean()
        std_val = values.std()
        cv = abs(std_val / mean_val) if mean_val != 0 else np.inf
        range_val = values.max() - values.min()
        
        stability_stats.append({
            'config': config_name,
            'n_seeds': len(values),
            'mean': round(mean_val, 4),
            'std': round(std_val, 4),
            'cv': round(cv, 4),
            'range': round(range_val, 4)
        })
        
        # Flag high variation configurations
        if cv > 0.2:
            unstable_configs.append({
                'config': config_name,
                'cv': round(cv, 4),
                'n_seeds': len(values)
            })
    
    if not stability_stats:
        return {
            'metric': metric_name,
            'note': 'No valid configuration groups for stability analysis'
        }
    
    # Summary statistics
    cv_values = [s['cv'] for s in stability_stats if s['cv'] != np.inf]
    
    return {
        'metric': metric_name,
        'n_configurations': len(stability_stats),
        'avg_cv': round(np.mean(cv_values), 4) if cv_values else None,
        'median_cv': round(np.median(cv_values), 4) if cv_values else None,
        'max_cv': round(np.max(cv_values), 4) if cv_values else None,
        'high_variation_configs': len(unstable_configs),
        'high_variation_rate_pct': round(len(unstable_configs) / len(stability_stats) * 100, 2),
        'unstable_configs': unstable_configs[:5]  # Show top 5 unstable configs
    }

# ===== Main Analysis =====

print("\n=== DISTRIBUTION CHARACTERISTICS ANALYSIS ===")

distribution_results = {}
outlier_results = {}
stability_results = {}

for dimension, metrics in core_metrics.items():
    print(f"\n--- {dimension.upper()} DIMENSION ---")
    distribution_results[dimension] = []
    outlier_results[dimension] = []
    stability_results[dimension] = []
    
    for metric in metrics['primary']:
        if metric not in data.columns:
            print(f"{metric}: Column not found in data")
            continue
            
        print(f"\n{metric}:")
        
        # 1. Distribution characteristics
        dist_analysis = analyze_distribution_characteristics(data[metric], metric)
        distribution_results[dimension].append(dist_analysis)
        
        if 'error' in dist_analysis:
            print(f"  {dist_analysis['error']}")
            continue
        
        print(f"  Sample: N={dist_analysis['n']}, Completeness={dist_analysis['data_completeness_pct']}%")
        print(f"  Central tendency: Mean={dist_analysis['mean']}, Median={dist_analysis['median']}")
        print(f"  Variability: SD={dist_analysis['std']}, Range={dist_analysis['range']}, IQR={dist_analysis['iqr']}")
        print(f"  Distribution shape: Skewness={dist_analysis['skewness']}, Kurtosis={dist_analysis['kurtosis']}")
        
        # Report normality test results
        if dist_analysis['shapiro_p'] is not None:
            normality_note = "Normal" if dist_analysis['shapiro_p'] > 0.05 else "Non-normal"
            print(f"  Normality: {normality_note} (Shapiro p={dist_analysis['shapiro_p']})")
        
        # 2. Outlier detection
        outlier_analysis = detect_outliers_comprehensive(data[metric], metric)
        outlier_results[dimension].append(outlier_analysis)
        
        if 'note' not in outlier_analysis:
            print(f"  Outliers (IQR): {outlier_analysis['iqr_outliers_count']}/{outlier_analysis['total_values']} ({outlier_analysis['iqr_outlier_rate_pct']}%)")
            print(f"  Outliers (Z-score): {outlier_analysis['z_outliers_count']}/{outlier_analysis['total_values']} ({outlier_analysis['z_outlier_rate_pct']}%)")
            
            if outlier_analysis['outlier_values']:
                print(f"  Extreme values: {outlier_analysis['outlier_values']}")
        
        # 3. Seed stability analysis (only for system configurations)
        system_data = data[data.is_baseline == 0]
        if len(system_data) > 0:
            stability_analysis = analyze_seed_stability(system_data, metric)
            stability_results[dimension].append(stability_analysis)
            
            if 'note' not in stability_analysis and stability_analysis['avg_cv'] is not None:
                print(f"  Seed stability: {stability_analysis['n_configurations']} configs, Avg CV={stability_analysis['avg_cv']}")
                print(f"  High variation configs: {stability_analysis['high_variation_configs']} ({stability_analysis['high_variation_rate_pct']}%)")
                
                if stability_analysis['unstable_configs']:
                    unstable_list = [f"{u['config']}(CV={u['cv']})" for u in stability_analysis['unstable_configs']]
                    print(f"  Most unstable: {', '.join(unstable_list[:3])}")

print("\n=== AUXILIARY INDICATORS DATA QUALITY ===")

for dimension, metrics in core_metrics.items():
    print(f"\n{dimension.upper()} auxiliary indicators:")
    for metric in metrics['auxiliary']:
        if metric in data.columns:
            valid_count = data[metric].notna().sum()
            completeness = round(valid_count / len(data) * 100, 1)
            
            if completeness < 100:
                print(f"  {metric}: {valid_count}/{len(data)} ({completeness}% complete)")
            else:
                print(f"  {metric}: Complete (100%)")

print("\n=== ROBUSTNESS ANALYSIS SUMMARY ===")

# Create comprehensive summary
def create_robustness_summary():
    """Create summary of robustness analysis"""
    summary_data = []
    
    for dimension, dist_results in distribution_results.items():
        for i, result in enumerate(dist_results):
            if 'error' in result:
                continue
                
            # Get corresponding outlier and stability results
            outlier_result = outlier_results[dimension][i] if i < len(outlier_results[dimension]) else {}
            stability_result = stability_results[dimension][i] if i < len(stability_results[dimension]) else {}
            
            summary_data.append({
                'dimension': dimension,
                'metric': result['metric'],
                'n': result['n'],
                'completeness_pct': result['data_completeness_pct'],
                'mean': result['mean'],
                'std': result['std'],
                'median': result['median'],
                'iqr': result['iqr'],
                'skewness': result['skewness'],
                'kurtosis': result['kurtosis'],
                'outlier_rate_pct': outlier_result.get('iqr_outlier_rate_pct', 0),
                'seed_stability_cv': stability_result.get('avg_cv'),
                'high_var_configs_pct': stability_result.get('high_variation_rate_pct')
            })
    
    return pd.DataFrame(summary_data)

# Generate summary
summary_df = create_robustness_summary()

print("\nROBUSTNESS SUMMARY BY DIMENSION:")
for dimension in core_metrics.keys():
    dim_data = summary_df[summary_df.dimension == dimension]
    if len(dim_data) > 0:
        avg_completeness = dim_data['completeness_pct'].mean()
        avg_outlier_rate = dim_data['outlier_rate_pct'].mean()
        avg_stability_cv = dim_data['seed_stability_cv'].dropna().mean()
        
        print(f"{dimension.upper()}:")
        print(f"  Data completeness: {avg_completeness:.1f}%")
        print(f"  Average outlier rate: {avg_outlier_rate:.2f}%")
        if not np.isnan(avg_stability_cv):
            print(f"  Average seed stability CV: {avg_stability_cv:.4f}")
        print(f"  Metrics analyzed: {len(dim_data)}")

# Identify metrics requiring attention
print("\nMETRICS REQUIRING ATTENTION:")

# High outlier rates
high_outlier_metrics = summary_df[summary_df.outlier_rate_pct > 10]
if len(high_outlier_metrics) > 0:
    print("High outlier rates (>10%):")
    for _, row in high_outlier_metrics.iterrows():
        print(f"  - {row['metric']}: {row['outlier_rate_pct']:.2f}%")

# Low data completeness
low_completeness_metrics = summary_df[summary_df.completeness_pct < 95]
if len(low_completeness_metrics) > 0:
    print("Low data completeness (<95%):")
    for _, row in low_completeness_metrics.iterrows():
        print(f"  - {row['metric']}: {row['completeness_pct']:.1f}%")

# High seed instability
high_instability_metrics = summary_df[summary_df.seed_stability_cv > 0.2]
high_instability_metrics = high_instability_metrics.dropna(subset=['seed_stability_cv'])
if len(high_instability_metrics) > 0:
    print("High seed instability (CV > 0.2):")
    for _, row in high_instability_metrics.iterrows():
        print(f"  - {row['metric']}: CV={row['seed_stability_cv']:.4f}")

# Most stable metrics
most_stable = summary_df.dropna(subset=['seed_stability_cv']).nsmallest(5, 'seed_stability_cv')
print("\nMOST STABLE METRICS (lowest seed CV):")
for _, row in most_stable.iterrows():
    print(f"  {row['metric']}: CV={row['seed_stability_cv']:.4f}")

# Save detailed results
summary_df.to_csv('robustness_analysis_detailed.csv', index=False)
print(f"\nDetailed results saved to 'robustness_analysis_detailed.csv'")

print("\n=== 4.1.1 ANALYSIS COMPLETE ===")
print("Results ready for Section 4.1.1 writeup")