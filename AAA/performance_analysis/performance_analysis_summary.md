# Performance and Cost Analysis Report

Generated on: 2025-09-13T16:57:20.186595

## Executive Summary

- **Total Experiments**: 54
- **Total Cost**: $66.33
- **Total Runtime**: 9.53 hours
- **Total Tokens**: 4.32 million
- **Average Cost per Experiment**: $1.228
- **Average Runtime**: 10.6 minutes

## Key Performance Metrics

### Cost Distribution
- **Mean Cost per 1K Tokens**: $0.0155
- **Median Cost per 1K Tokens**: $0.0154

### Structure Impact on Costs
- **Linear Structure Average Cost**: $1.172
- **Nonlinear Structure Average Cost**: $1.285
- **Difference**: $0.114

### Temperature Correlations
- **Cost Correlation**: 0.038
- **Time Correlation**: 0.163
- **Token Correlation**: 0.036

## Top Performing Configurations

### Most Cost-Effective

1. **sciencefiction_linear_T0.9_s1**
   - Cost Effectiveness: 1.591
   - Cost: $0.442
   - Quality Score: 0.704

2. **horror_nonlinear_T0.7_s2**
   - Cost Effectiveness: 1.559
   - Cost: $0.507
   - Quality Score: 0.790

3. **sciencefiction_linear_T0.7_s3**
   - Cost Effectiveness: 1.462
   - Cost: $0.497
   - Quality Score: 0.727

## Recommendations

1. **Cost Optimization**: Consider using linear structures and lower temperatures for cost-sensitive applications
2. **Quality-Cost Balance**: Monitor cost-effectiveness ratios when optimizing for both quality and budget
3. **Performance Monitoring**: Track cost per 1K tokens as a key efficiency metric

## Visualizations Generated

- `performance_distributions_boxplot.png`: Distribution of performance metrics
- `cost_effectiveness_analysis.png`: Cost vs quality analysis with Pareto frontier
- `structure_temperature_cost_analysis.png`: Impact of structural parameters on costs
- `quality_performance_correlations.png`: Correlation matrix between quality and performance metrics

