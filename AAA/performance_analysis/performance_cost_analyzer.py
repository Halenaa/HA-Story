#!/usr/bin/env python3
"""
Performance and Cost Analysis System

This module analyzes performance metrics including:
- Execution time (wall_time_sec)
- Memory usage (peak_mem_mb)  
- Token consumption (tokens_total)
- Cost efficiency (cost_usd)
- Cost-effectiveness ratios
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class PerformanceCostAnalyzer:
    """Comprehensive performance and cost analysis system."""
    
    def __init__(self, csv_path: str, output_dir: str = "/Users/haha/Story/AAA/performance_analysis"):
        """Initialize the analyzer with data path and output directory."""
        self.csv_path = csv_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and prepare data
        self.df = pd.read_csv(csv_path)
        self.prepare_data()
        
        # Results storage
        self.results = {}
        
    def prepare_data(self):
        """Prepare and clean the data for analysis."""
        print("Preparing data for performance analysis...")
        
        # Remove baseline entries for comparison analysis
        self.df_experiments = self.df[self.df['is_baseline'] == 0].copy()
        self.df_baselines = self.df[self.df['is_baseline'] == 1].copy()
        
        # Calculate composite quality scores
        self.df_experiments['quality_composite'] = (
            self.df_experiments['one_minus_self_bleu'] * 0.3 +
            self.df_experiments['avg_coherence'] * 0.3 +
            self.df_experiments['distinct_score'] * 0.2 +
            self.df_experiments['diversity_group_score'] * 0.2
        )
        
        # Calculate cost-effectiveness metrics
        self.df_experiments['cost_per_1k_tokens'] = (
            self.df_experiments['cost_usd'] / (self.df_experiments['tokens_total'] / 1000)
        )
        self.df_experiments['cost_effectiveness'] = (
            self.df_experiments['quality_composite'] / self.df_experiments['cost_usd']
        )
        self.df_experiments['time_per_1k_tokens'] = (
            self.df_experiments['wall_time_sec'] / (self.df_experiments['tokens_total'] / 1000)
        )
        
        print(f"Prepared {len(self.df_experiments)} experimental entries for analysis")
        
    def analyze_performance_distributions(self):
        """Analyze distribution of performance metrics."""
        print("Analyzing performance metric distributions...")
        
        performance_metrics = ['wall_time_sec', 'peak_mem_mb', 'tokens_total', 'cost_usd']
        
        # Basic statistics
        perf_stats = {}
        for metric in performance_metrics:
            stats = {
                'mean': float(self.df_experiments[metric].mean()),
                'median': float(self.df_experiments[metric].median()),
                'std': float(self.df_experiments[metric].std()),
                'min': float(self.df_experiments[metric].min()),
                'max': float(self.df_experiments[metric].max()),
                'q25': float(self.df_experiments[metric].quantile(0.25)),
                'q75': float(self.df_experiments[metric].quantile(0.75))
            }
            perf_stats[metric] = stats
        
        self.results['performance_distributions'] = perf_stats
        
        # Create box plots for performance metrics
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Performance Metrics Distribution', fontsize=16, fontweight='bold')
        
        for idx, metric in enumerate(performance_metrics):
            row, col = idx // 2, idx % 2
            ax = axes[row, col]
            
            # Box plot by structure type
            sns.boxplot(data=self.df_experiments, x='structure', y=metric, ax=ax)
            ax.set_title(f'{metric.replace("_", " ").title()}')
            ax.tick_params(axis='x', rotation=45)
            
        plt.tight_layout()
        plt.savefig(self.output_dir / 'performance_distributions_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Performance distribution analysis completed")
        
    def analyze_cost_effectiveness(self):
        """Analyze cost-effectiveness relationships."""
        print("Analyzing cost-effectiveness metrics...")
        
        # Cost vs Quality scatter plot (Pareto frontier)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Cost-Effectiveness Analysis', fontsize=16, fontweight='bold')
        
        # 1. Cost vs Composite Quality
        ax1 = axes[0, 0]
        scatter = ax1.scatter(self.df_experiments['cost_usd'], 
                            self.df_experiments['quality_composite'],
                            c=self.df_experiments['temperature'], 
                            cmap='viridis', alpha=0.7)
        ax1.set_xlabel('Cost (USD)')
        ax1.set_ylabel('Composite Quality Score')
        ax1.set_title('Cost vs Quality (colored by temperature)')
        plt.colorbar(scatter, ax=ax1, label='Temperature')
        
        # Add trend line
        z = np.polyfit(self.df_experiments['cost_usd'], self.df_experiments['quality_composite'], 1)
        p = np.poly1d(z)
        ax1.plot(self.df_experiments['cost_usd'], p(self.df_experiments['cost_usd']), "r--", alpha=0.5)
        
        # 2. Cost per 1K tokens by structure
        ax2 = axes[0, 1]
        sns.boxplot(data=self.df_experiments, x='structure', y='cost_per_1k_tokens', ax=ax2)
        ax2.set_title('Cost per 1K Tokens by Structure')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Time vs Quality
        ax3 = axes[1, 0]
        scatter2 = ax3.scatter(self.df_experiments['wall_time_sec'], 
                              self.df_experiments['quality_composite'],
                              c=self.df_experiments['temperature'], 
                              cmap='plasma', alpha=0.7)
        ax3.set_xlabel('Execution Time (sec)')
        ax3.set_ylabel('Composite Quality Score')
        ax3.set_title('Time vs Quality (colored by temperature)')
        plt.colorbar(scatter2, ax=ax3, label='Temperature')
        
        # 4. Cost effectiveness by genre
        ax4 = axes[1, 1]
        sns.boxplot(data=self.df_experiments, x='genre', y='cost_effectiveness', ax=ax4)
        ax4.set_title('Cost Effectiveness by Genre')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'cost_effectiveness_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Calculate Pareto frontier for cost vs quality
        pareto_points = self._find_pareto_frontier(
            self.df_experiments['cost_usd'].values,
            self.df_experiments['quality_composite'].values
        )
        
        # Cost effectiveness statistics
        cost_effectiveness_stats = {
            'mean_cost_per_1k_tokens': float(self.df_experiments['cost_per_1k_tokens'].mean()),
            'median_cost_per_1k_tokens': float(self.df_experiments['cost_per_1k_tokens'].median()),
            'best_cost_effectiveness': {
                'story_id': self.df_experiments.loc[self.df_experiments['cost_effectiveness'].idxmax(), 'story_id'],
                'value': float(self.df_experiments['cost_effectiveness'].max())
            },
            'pareto_frontier_points': len(pareto_points)
        }
        
        self.results['cost_effectiveness'] = cost_effectiveness_stats
        
        print("Cost-effectiveness analysis completed")
        
    def analyze_structure_temperature_costs(self):
        """Analyze relationship between structure, temperature and costs."""
        print("Analyzing structure and temperature impact on costs...")
        
        # Group analysis
        structure_temp_analysis = self.df_experiments.groupby(['structure', 'temperature']).agg({
            'cost_usd': ['mean', 'std', 'count'],
            'wall_time_sec': ['mean', 'std'],
            'tokens_total': ['mean', 'std'],
            'quality_composite': ['mean', 'std']
        }).round(4)
        
        # Create heatmaps
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Structure & Temperature Impact on Performance', fontsize=16, fontweight='bold')
        
        # Cost heatmap
        cost_pivot = self.df_experiments.pivot_table(
            values='cost_usd', index='structure', columns='temperature', aggfunc='mean'
        )
        sns.heatmap(cost_pivot, annot=True, fmt='.3f', ax=axes[0,0], cmap='Reds')
        axes[0,0].set_title('Mean Cost (USD) by Structure & Temperature')
        
        # Time heatmap  
        time_pivot = self.df_experiments.pivot_table(
            values='wall_time_sec', index='structure', columns='temperature', aggfunc='mean'
        )
        sns.heatmap(time_pivot, annot=True, fmt='.1f', ax=axes[0,1], cmap='Oranges')
        axes[0,1].set_title('Mean Execution Time (sec) by Structure & Temperature')
        
        # Tokens heatmap
        tokens_pivot = self.df_experiments.pivot_table(
            values='tokens_total', index='structure', columns='temperature', aggfunc='mean'
        )
        sns.heatmap(tokens_pivot, annot=True, fmt='.0f', ax=axes[1,0], cmap='Blues')
        axes[1,0].set_title('Mean Token Count by Structure & Temperature')
        
        # Cost effectiveness heatmap
        cost_eff_pivot = self.df_experiments.pivot_table(
            values='cost_effectiveness', index='structure', columns='temperature', aggfunc='mean'
        )
        sns.heatmap(cost_eff_pivot, annot=True, fmt='.2f', ax=axes[1,1], cmap='Greens')
        axes[1,1].set_title('Mean Cost Effectiveness by Structure & Temperature')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'structure_temperature_cost_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Statistical analysis
        structure_impact = {
            'linear_vs_nonlinear_cost': {
                'linear_mean': float(self.df_experiments[self.df_experiments['structure'] == 'linear']['cost_usd'].mean()),
                'nonlinear_mean': float(self.df_experiments[self.df_experiments['structure'] == 'nonlinear']['cost_usd'].mean()),
                'difference': float(
                    self.df_experiments[self.df_experiments['structure'] == 'nonlinear']['cost_usd'].mean() -
                    self.df_experiments[self.df_experiments['structure'] == 'linear']['cost_usd'].mean()
                )
            },
            'temperature_correlation': {
                'cost_correlation': float(self.df_experiments[['temperature', 'cost_usd']].corr().iloc[0,1]),
                'time_correlation': float(self.df_experiments[['temperature', 'wall_time_sec']].corr().iloc[0,1]),
                'tokens_correlation': float(self.df_experiments[['temperature', 'tokens_total']].corr().iloc[0,1])
            }
        }
        
        self.results['structure_temperature_impact'] = structure_impact
        
        print("Structure and temperature cost analysis completed")
        
    def analyze_quality_performance_tradeoffs(self):
        """Analyze trade-offs between quality and performance metrics."""
        print("Analyzing quality vs performance trade-offs...")
        
        # Correlation analysis
        quality_metrics = ['one_minus_self_bleu', 'avg_coherence', 'distinct_score', 'quality_composite']
        performance_metrics = ['wall_time_sec', 'peak_mem_mb', 'tokens_total', 'cost_usd']
        
        # Calculate correlations
        correlations = {}
        for quality_metric in quality_metrics:
            correlations[quality_metric] = {}
            for perf_metric in performance_metrics:
                corr = self.df_experiments[[quality_metric, perf_metric]].corr().iloc[0,1]
                correlations[quality_metric][perf_metric] = float(corr)
        
        # Create correlation heatmap
        corr_df = pd.DataFrame(correlations).T
        
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        sns.heatmap(corr_df, annot=True, fmt='.3f', ax=ax, cmap='RdBu_r', center=0)
        ax.set_title('Quality vs Performance Correlations')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'quality_performance_correlations.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Trade-off analysis - find optimal balance points
        trade_off_analysis = {
            'quality_performance_correlations': correlations,
            'optimal_configurations': self._find_optimal_configurations()
        }
        
        self.results['quality_performance_tradeoffs'] = trade_off_analysis
        
        print("Quality vs performance trade-off analysis completed")
        
    def generate_performance_report(self):
        """Generate comprehensive performance analysis report."""
        print("Generating comprehensive performance report...")
        
        # Calculate summary statistics
        summary_stats = {
            'total_experiments': len(self.df_experiments),
            'total_cost_usd': float(self.df_experiments['cost_usd'].sum()),
            'total_runtime_hours': float(self.df_experiments['wall_time_sec'].sum() / 3600),
            'total_tokens_millions': float(self.df_experiments['tokens_total'].sum() / 1000000),
            'average_cost_per_experiment': float(self.df_experiments['cost_usd'].mean()),
            'average_runtime_minutes': float(self.df_experiments['wall_time_sec'].mean() / 60),
            'cost_range': {
                'min': float(self.df_experiments['cost_usd'].min()),
                'max': float(self.df_experiments['cost_usd'].max()),
                'std': float(self.df_experiments['cost_usd'].std())
            }
        }
        
        # Performance efficiency rankings
        efficiency_rankings = {
            'most_cost_effective': self.df_experiments.nlargest(5, 'cost_effectiveness')[
                ['story_id', 'cost_effectiveness', 'cost_usd', 'quality_composite']
            ].to_dict('records'),
            'fastest_execution': self.df_experiments.nsmallest(5, 'wall_time_sec')[
                ['story_id', 'wall_time_sec', 'quality_composite']
            ].to_dict('records'),
            'lowest_cost': self.df_experiments.nsmallest(5, 'cost_usd')[
                ['story_id', 'cost_usd', 'quality_composite']
            ].to_dict('records')
        }
        
        # Compile final results
        final_report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'summary_statistics': summary_stats,
            'efficiency_rankings': efficiency_rankings,
            **self.results
        }
        
        # Save comprehensive report
        with open(self.output_dir / 'performance_analysis_report.json', 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        # Generate markdown report
        self._generate_markdown_report(final_report)
        
        print(f"Performance analysis report saved to {self.output_dir}")
        return final_report
        
    def _find_pareto_frontier(self, costs, qualities):
        """Find Pareto frontier points for cost vs quality."""
        # For cost minimization and quality maximization
        # A point is Pareto optimal if no other point has both lower cost and higher quality
        pareto_points = []
        
        for i in range(len(costs)):
            is_pareto = True
            for j in range(len(costs)):
                if i != j and costs[j] <= costs[i] and qualities[j] >= qualities[i]:
                    if costs[j] < costs[i] or qualities[j] > qualities[i]:
                        is_pareto = False
                        break
            if is_pareto:
                pareto_points.append(i)
                
        return pareto_points
        
    def _find_optimal_configurations(self):
        """Find configurations with optimal quality-performance balance."""
        # Define efficiency score combining quality and inverse cost
        self.df_experiments['efficiency_score'] = (
            self.df_experiments['quality_composite'] / 
            (self.df_experiments['cost_usd'] * self.df_experiments['wall_time_sec'] / 3600)
        )
        
        top_configs = self.df_experiments.nlargest(10, 'efficiency_score')[
            ['story_id', 'structure', 'temperature', 'genre', 'quality_composite', 
             'cost_usd', 'wall_time_sec', 'efficiency_score']
        ].to_dict('records')
        
        return top_configs
        
    def _generate_markdown_report(self, report):
        """Generate a markdown summary report."""
        md_content = f"""# Performance and Cost Analysis Report

Generated on: {report['analysis_timestamp']}

## Executive Summary

- **Total Experiments**: {report['summary_statistics']['total_experiments']}
- **Total Cost**: ${report['summary_statistics']['total_cost_usd']:.2f}
- **Total Runtime**: {report['summary_statistics']['total_runtime_hours']:.2f} hours
- **Total Tokens**: {report['summary_statistics']['total_tokens_millions']:.2f} million
- **Average Cost per Experiment**: ${report['summary_statistics']['average_cost_per_experiment']:.3f}
- **Average Runtime**: {report['summary_statistics']['average_runtime_minutes']:.1f} minutes

## Key Performance Metrics

### Cost Distribution
- **Mean Cost per 1K Tokens**: ${report['cost_effectiveness']['mean_cost_per_1k_tokens']:.4f}
- **Median Cost per 1K Tokens**: ${report['cost_effectiveness']['median_cost_per_1k_tokens']:.4f}

### Structure Impact on Costs
- **Linear Structure Average Cost**: ${report['structure_temperature_impact']['linear_vs_nonlinear_cost']['linear_mean']:.3f}
- **Nonlinear Structure Average Cost**: ${report['structure_temperature_impact']['linear_vs_nonlinear_cost']['nonlinear_mean']:.3f}
- **Difference**: ${report['structure_temperature_impact']['linear_vs_nonlinear_cost']['difference']:.3f}

### Temperature Correlations
- **Cost Correlation**: {report['structure_temperature_impact']['temperature_correlation']['cost_correlation']:.3f}
- **Time Correlation**: {report['structure_temperature_impact']['temperature_correlation']['time_correlation']:.3f}
- **Token Correlation**: {report['structure_temperature_impact']['temperature_correlation']['tokens_correlation']:.3f}

## Top Performing Configurations

### Most Cost-Effective
"""
        for idx, config in enumerate(report['efficiency_rankings']['most_cost_effective'][:3], 1):
            md_content += f"""
{idx}. **{config['story_id']}**
   - Cost Effectiveness: {config['cost_effectiveness']:.3f}
   - Cost: ${config['cost_usd']:.3f}
   - Quality Score: {config['quality_composite']:.3f}
"""

        md_content += """
## Recommendations

1. **Cost Optimization**: Consider using linear structures and lower temperatures for cost-sensitive applications
2. **Quality-Cost Balance**: Monitor cost-effectiveness ratios when optimizing for both quality and budget
3. **Performance Monitoring**: Track cost per 1K tokens as a key efficiency metric

## Visualizations Generated

- `performance_distributions_boxplot.png`: Distribution of performance metrics
- `cost_effectiveness_analysis.png`: Cost vs quality analysis with Pareto frontier
- `structure_temperature_cost_analysis.png`: Impact of structural parameters on costs
- `quality_performance_correlations.png`: Correlation matrix between quality and performance metrics

"""
        
        with open(self.output_dir / 'performance_analysis_summary.md', 'w') as f:
            f.write(md_content)

def main():
    """Main execution function."""
    csv_path = "/Users/haha/Story/metrics_master_clean.csv"
    
    print("Starting Performance and Cost Analysis...")
    analyzer = PerformanceCostAnalyzer(csv_path)
    
    # Run all analyses
    analyzer.analyze_performance_distributions()
    analyzer.analyze_cost_effectiveness()
    analyzer.analyze_structure_temperature_costs()
    analyzer.analyze_quality_performance_tradeoffs()
    
    # Generate comprehensive report
    final_report = analyzer.generate_performance_report()
    
    print("Performance and Cost Analysis completed successfully!")
    print(f"Results saved in: {analyzer.output_dir}")
    
    return final_report

if __name__ == "__main__":
    main()
