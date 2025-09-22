# Comprehensive Fluency Analysis Report

Generated on: 2025-09-12 23:38:31

## Preprocessing & Robustness Settings

- Winsorize limits for err_per_100w: [2%, 98%]
- log1p transform on err_per_100w: applied
- Normalization range for [0,1] scores: P5–P95
- Length penalty threshold (P20 words): 6405.0

## Summary Statistics

### Pseudo-PPL Statistics
- Count: 56
- Mean: 2.355
- Median: 2.218
- Std: 0.417
- Range: 1.858 - 3.937

### Error Rate per 100 Words Statistics
- Count: 56
- Mean: 0.287
- Median: 0.188
- Std: 0.348
- Range: 0.043 - 2.034

## Quality Analysis

### Pseudo-PPL Quality Levels
- good: 48 (85.7%)
- excellent: 8 (14.3%)

### Error Rate Quality Levels
- high_quality: 30 (53.6%)
- medium_quality: 20 (35.7%)
- poor_quality: 6 (10.7%)

### Combined Fluency Quality
- high: 32 (57.1%)
- medium: 24 (42.9%)

## Key Correlations (Robust Analysis)

### Pseudo-PPL Relationships (Spearman ρ, |ρ| > 0.1)
- distinct_avg: ρ=0.747 (Pearson r=0.800)
- roberta_avg_score: ρ=-0.690 (Pearson r=-0.637)
- avg_coherence: ρ=-0.629 (Pearson r=-0.840)
- total_words: ρ=-0.386 (Pearson r=-0.422)
- err_per_100w_winz: ρ=0.366 (Pearson r=0.369)
- err_per_100w: ρ=0.365 (Pearson r=0.309)
- err_per_100w_log1p: ρ=0.365 (Pearson r=0.339)
- distinct_score: ρ=0.303 (Pearson r=0.320)
- total_sentences: ρ=-0.274 (Pearson r=-0.209)

### Error Rate Relationships (Spearman ρ, |ρ| > 0.1)
- err_per_100w: ρ=1.000 (Pearson r=0.976)
- err_per_100w_log1p: ρ=1.000 (Pearson r=0.991)
- pseudo_ppl: ρ=0.366 (Pearson r=0.369)
- roberta_avg_score: ρ=-0.363 (Pearson r=-0.404)
- avg_coherence: ρ=-0.354 (Pearson r=-0.505)
- distinct_avg: ρ=0.348 (Pearson r=0.489)
- total_words: ρ=-0.185 (Pearson r=-0.225)
- diversity_group_score: ρ=0.178 (Pearson r=0.122)
- total_sentences: ρ=-0.132 (Pearson r=-0.088)

### Length-Controlled Relationships (Partial Correlations)
- Diversity ↔ Coherence (length-controlled): ρ=-0.714 (p=6.29e-10), r=-0.690 (p=4.12e-09)
  ✓ Trade-off remains significant even after controlling for text length.

## Outliers

Found 8 outliers:
- pseudo_ppl: sciencefiction_baseline_Tbaseline_sbaseline (value: 3.637)
- pseudo_ppl: baseline_baseline_Tbaseline_sbaseline (value: 3.937)
- err_per_100w: sciencefiction_linear_T0.9_s2 (value: 0.791)
- err_per_100w: sciencefiction_linear_T0.7_s3 (value: 1.375)
- err_per_100w: sciencefiction_linear_T0.3_s3 (value: 2.034)
- err_per_100w: sciencefiction_nonlinear_T0.9_s1 (value: 0.700)
- err_per_100w: sciencefiction_nonlinear_T0.7_s1 (value: 0.818)
- err_per_100w: sciencefiction_baseline_Tbaseline_sbaseline (value: 1.168)

## Quality Thresholds & Sensitivity Analysis

### Pseudo-PPL Thresholds
**Standard thresholds:**
- < 2.0: Excellent fluency
- 2.0 - 5.0: Good fluency
- > 5.0: Poor fluency

**Percentile-based thresholds (robust):**
- P50 (median): 2.218 - half of samples perform better
- P20: 2.054 - top 20% performance threshold
- P80: 2.660 - bottom 20% performance threshold

### Error Rate per 100 Words
**Standard thresholds:**
- < 0.2: High quality
- 0.2 - 0.5: Medium quality
- > 0.5: Poor quality

**Percentile-based thresholds (robust):**
- P50 (median): 0.188 - recommended for heavy-tailed distributions
- P20: 0.111 - top 20% performance (lowest error rates)
- P80: 0.281 - bottom 20% threshold (highest error rates)

**Note:** Given error rate heavy tails (skewness=3.37, kurtosis=12.85), percentile-based thresholds provide more robust quality assessment than fixed cutoffs.

## Files Generated

### Visualizations
- `fluency_boxplots_by_groups.png`: Boxplots by genre and structure
- `fluency_tradeoff_scatter.png`: Pseudo-PPL vs Error rate scatter plot
- `fluency_distributions.png`: Distribution histograms
- `fluency_correlation_heatmap_robust.png`: Dual correlation heatmap (Spearman + Pearson)
- `scored_metrics_correlation_heatmap.png`: Scored metrics correlations (all positive)
- `fluency_quality_distributions.png`: Quality level pie charts
- `temperature_effects_on_fluency.png`: Temperature effect analysis

### Data Tables
- `metrics_master_scored.csv`: Normalized [0,1] scores for all metrics
- `grouped_3d_scores.csv`: 3D grouping (genre × structure × temperature)
- `config_overall_scores.csv`: Overall scores by configuration

### Reports
- `fluency_analysis_results.json`: Complete numerical results with robust measures
- `ROBUST_ANALYSIS_FINDINGS.md`: Statistical robustness analysis summary
