#!/usr/bin/env python3
"""
Length-Controlled Coherence Analysis System (English Version)
Controls for text length effects on coherence, providing fairer baseline vs AI comparison

Author: AI Assistant
Created: 2025-09-13
Version: 1.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import json
import warnings
warnings.filterwarnings('ignore')

plt.style.use('default')
sns.set_palette("husl")

class LengthControlledCoherenceAnalyzer:
    """Length-controlled coherence analyzer"""
    
    def __init__(self, csv_path):
        """Initialize analyzer"""
        self.csv_path = csv_path
        self.data = pd.read_csv(csv_path)
        
        # Separate baseline and AI story data
        self.baseline_data = self.data[self.data['is_baseline'] == 1].copy()
        self.ai_data = self.data[self.data['is_baseline'] == 0].copy()
        
        print(f"📊 Data loading completed:")
        print(f"   Baseline samples: {len(self.baseline_data)}")
        print(f"   AI story samples: {len(self.ai_data)}")
        
        # Initialize result storage
        self.results = {
            "analysis_info": {
                "timestamp": pd.Timestamp.now().isoformat(),
                "data_source": csv_path,
                "analyzer_version": "1.0",
                "control_methods": ["raw", "normalized", "residual", "matched", "stratified"]
            }
        }
        
    def analyze_length_coherence_relationship(self):
        """Analyze relationship between length and coherence"""
        print("\n🔍 Analyzing length-coherence relationship...")
        
        # Overall correlation
        all_words = pd.concat([self.baseline_data['total_words'], self.ai_data['total_words']])
        all_coherence = pd.concat([self.baseline_data['avg_coherence'], self.ai_data['avg_coherence']])
        
        overall_corr, overall_p = stats.pearsonr(all_words, all_coherence)
        
        # Group-wise correlation
        ai_corr, ai_p = stats.pearsonr(self.ai_data['total_words'], self.ai_data['avg_coherence'])
        
        # Baseline data too small for reliable correlation
        baseline_corr = np.nan
        baseline_p = np.nan
        
        relationship = {
            "overall": {
                "correlation": float(overall_corr),
                "p_value": float(overall_p),
                "significant": bool(overall_p < 0.05),
                "interpretation": self._interpret_correlation(overall_corr)
            },
            "ai_stories": {
                "correlation": float(ai_corr),
                "p_value": float(ai_p),
                "significant": bool(ai_p < 0.05),
                "interpretation": self._interpret_correlation(ai_corr)
            },
            "baseline": {
                "correlation": baseline_corr,
                "p_value": baseline_p,
                "note": "Too few samples for reliable correlation estimation"
            }
        }
        
        self.results["length_coherence_relationship"] = relationship
        return relationship
    
    def _interpret_correlation(self, r):
        """Interpret correlation coefficient"""
        if abs(r) < 0.1:
            return "negligible"
        elif abs(r) < 0.3:
            return "weak"
        elif abs(r) < 0.5:
            return "moderate"
        elif abs(r) < 0.7:
            return "strong"
        else:
            return "very strong"
    
    def raw_comparison(self):
        """Raw coherence comparison (no length control)"""
        print("\n📏 Raw coherence comparison (no length control)...")
        
        baseline_coh = self.baseline_data['avg_coherence'].mean()
        baseline_std = self.baseline_data['avg_coherence'].std()
        ai_coh = self.ai_data['avg_coherence'].mean()
        ai_std = self.ai_data['avg_coherence'].std()
        
        improvement = ai_coh - baseline_coh
        improvement_pct = (improvement / baseline_coh) * 100
        
        # Statistical test
        t_stat, p_val = stats.ttest_ind(
            self.ai_data['avg_coherence'],
            self.baseline_data['avg_coherence']
        )
        
        raw = {
            "baseline": {
                "mean_coherence": float(baseline_coh),
                "std_coherence": float(baseline_std),
                "count": int(len(self.baseline_data)),
                "mean_length": float(self.baseline_data['total_words'].mean())
            },
            "ai_stories": {
                "mean_coherence": float(ai_coh),
                "std_coherence": float(ai_std),
                "count": int(len(self.ai_data)),
                "mean_length": float(self.ai_data['total_words'].mean())
            },
            "comparison": {
                "absolute_improvement": float(improvement),
                "relative_improvement_pct": float(improvement_pct),
                "t_statistic": float(t_stat),
                "p_value": float(p_val),
                "significant": bool(p_val < 0.05)
            }
        }
        
        self.results["raw_comparison"] = raw
        return raw
    
    def normalized_coherence_analysis(self):
        """Normalized coherence analysis"""
        print("\n📐 Normalized coherence analysis...")
        
        # Method 1: coherence / log(length) 
        self.ai_data['normalized_coh_log'] = self.ai_data['avg_coherence'] / np.log(self.ai_data['total_words'])
        self.baseline_data['normalized_coh_log'] = self.baseline_data['avg_coherence'] / np.log(self.baseline_data['total_words'])
        
        # Method 2: coherence / sqrt(length)
        self.ai_data['normalized_coh_sqrt'] = self.ai_data['avg_coherence'] / np.sqrt(self.ai_data['total_words'])
        self.baseline_data['normalized_coh_sqrt'] = self.baseline_data['avg_coherence'] / np.sqrt(self.baseline_data['total_words'])
        
        normalized = {}
        
        for method, column in [("log", "normalized_coh_log"), ("sqrt", "normalized_coh_sqrt")]:
            baseline_norm = self.baseline_data[column].mean()
            ai_norm = self.ai_data[column].mean()
            improvement = ai_norm - baseline_norm
            improvement_pct = (improvement / baseline_norm) * 100
            
            # Statistical test
            t_stat, p_val = stats.ttest_ind(
                self.ai_data[column],
                self.baseline_data[column]
            )
            
            normalized[method] = {
                "baseline_mean": float(baseline_norm),
                "ai_mean": float(ai_norm),
                "improvement": float(improvement),
                "improvement_pct": float(improvement_pct),
                "t_statistic": float(t_stat),
                "p_value": float(p_val),
                "significant": bool(p_val < 0.05)
            }
        
        self.results["normalized_analysis"] = normalized
        return normalized
    
    def residual_coherence_analysis(self):
        """Residual coherence analysis (regression control for length)"""
        print("\n📈 Residual coherence analysis (regression control for length)...")
        
        # Use AI data to fit length-coherence relationship
        X = self.ai_data[['total_words']].values
        y = self.ai_data['avg_coherence'].values
        
        # Fit regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate predicted values and residuals for all data
        all_words = pd.concat([self.baseline_data['total_words'], self.ai_data['total_words']]).values.reshape(-1, 1)
        all_coherence = pd.concat([self.baseline_data['avg_coherence'], self.ai_data['avg_coherence']]).values
        
        predicted = model.predict(all_words)
        residuals = all_coherence - predicted
        
        # Assign residuals
        baseline_residuals = residuals[:len(self.baseline_data)]
        ai_residuals = residuals[len(self.baseline_data):]
        
        self.baseline_data['coherence_residual'] = baseline_residuals
        self.ai_data['coherence_residual'] = ai_residuals
        
        # Compare residuals
        baseline_res_mean = baseline_residuals.mean()
        ai_res_mean = ai_residuals.mean()
        improvement = ai_res_mean - baseline_res_mean
        
        # Statistical test
        t_stat, p_val = stats.ttest_ind(ai_residuals, baseline_residuals)
        
        residual = {
            "regression_model": {
                "slope": float(model.coef_[0]),
                "intercept": float(model.intercept_),
                "r_squared": float(model.score(X, y))
            },
            "baseline_residual_mean": float(baseline_res_mean),
            "ai_residual_mean": float(ai_res_mean),
            "residual_improvement": float(improvement),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "significant": bool(p_val < 0.05)
        }
        
        self.results["residual_analysis"] = residual
        return residual
    
    def matched_sample_analysis(self):
        """Matched sample analysis (select samples with similar lengths)"""
        print("\n🎯 Matched sample analysis...")
        
        # Find length overlap range
        baseline_min = self.baseline_data['total_words'].min()
        baseline_max = self.baseline_data['total_words'].max()
        
        # Select AI stories with lengths within baseline range
        matched_ai = self.ai_data[
            (self.ai_data['total_words'] >= baseline_min) & 
            (self.ai_data['total_words'] <= baseline_max)
        ].copy()
        
        if len(matched_ai) == 0:
            return {"note": "No AI stories within baseline length range"}
        
        # Further matching: find closest AI story for each baseline
        matched_pairs = []
        for _, baseline_row in self.baseline_data.iterrows():
            baseline_length = baseline_row['total_words']
            # Find AI story with closest length
            distances = np.abs(matched_ai['total_words'] - baseline_length)
            closest_idx = distances.idxmin()
            matched_pairs.append({
                'baseline_id': baseline_row['story_id'],
                'baseline_length': baseline_length,
                'baseline_coherence': baseline_row['avg_coherence'],
                'ai_id': matched_ai.loc[closest_idx, 'story_id'],
                'ai_length': matched_ai.loc[closest_idx, 'total_words'],
                'ai_coherence': matched_ai.loc[closest_idx, 'avg_coherence']
            })
        
        matched_df = pd.DataFrame(matched_pairs)
        
        # Statistical comparison
        baseline_matched_coh = matched_df['baseline_coherence'].mean()
        ai_matched_coh = matched_df['ai_coherence'].mean()
        improvement = ai_matched_coh - baseline_matched_coh
        improvement_pct = (improvement / baseline_matched_coh) * 100
        
        # Paired t-test
        t_stat, p_val = stats.ttest_rel(
            matched_df['ai_coherence'],
            matched_df['baseline_coherence']
        )
        
        matched = {
            "matched_pairs_count": len(matched_pairs),
            "length_range": {
                "min": float(baseline_min),
                "max": float(baseline_max)
            },
            "baseline_matched_coherence": float(baseline_matched_coh),
            "ai_matched_coherence": float(ai_matched_coh),
            "improvement": float(improvement),
            "improvement_pct": float(improvement_pct),
            "paired_t_statistic": float(t_stat),
            "p_value": float(p_val),
            "significant": bool(p_val < 0.05),
            "matched_pairs": matched_pairs
        }
        
        self.results["matched_analysis"] = matched
        return matched
    
    def stratified_analysis(self):
        """Stratified analysis (analyze by length intervals)"""
        print("\n📊 Stratified analysis (by length intervals)...")
        
        # Stratify all data by length
        all_data = pd.concat([self.baseline_data, self.ai_data])
        
        # Create length strata (based on quartiles)
        quartiles = all_data['total_words'].quantile([0.25, 0.5, 0.75]).values
        
        def get_stratum(length):
            if length <= quartiles[0]:
                return "Q1_Short"
            elif length <= quartiles[1]:
                return "Q2_Medium_Short"
            elif length <= quartiles[2]:
                return "Q3_Medium_Long"
            else:
                return "Q4_Long"
        
        self.baseline_data['length_stratum'] = self.baseline_data['total_words'].apply(get_stratum)
        self.ai_data['length_stratum'] = self.ai_data['total_words'].apply(get_stratum)
        
        strata_results = {}
        
        for stratum in ["Q1_Short", "Q2_Medium_Short", "Q3_Medium_Long", "Q4_Long"]:
            baseline_stratum = self.baseline_data[self.baseline_data['length_stratum'] == stratum]
            ai_stratum = self.ai_data[self.ai_data['length_stratum'] == stratum]
            
            if len(baseline_stratum) == 0 or len(ai_stratum) == 0:
                strata_results[stratum] = {"note": "Missing baseline or AI samples in this stratum"}
                continue
                
            baseline_coh = baseline_stratum['avg_coherence'].mean()
            ai_coh = ai_stratum['avg_coherence'].mean()
            improvement = ai_coh - baseline_coh if not np.isnan(baseline_coh) else np.nan
            improvement_pct = (improvement / baseline_coh) * 100 if not np.isnan(baseline_coh) and baseline_coh != 0 else np.nan
            
            # Statistical test (if sufficient samples)
            if len(baseline_stratum) >= 2 and len(ai_stratum) >= 2:
                t_stat, p_val = stats.ttest_ind(
                    ai_stratum['avg_coherence'],
                    baseline_stratum['avg_coherence']
                )
            else:
                t_stat, p_val = np.nan, np.nan
            
            strata_results[stratum] = {
                "baseline_count": int(len(baseline_stratum)),
                "ai_count": int(len(ai_stratum)),
                "baseline_coherence": float(baseline_coh) if not np.isnan(baseline_coh) else None,
                "ai_coherence": float(ai_coh) if not np.isnan(ai_coh) else None,
                "improvement": float(improvement) if not np.isnan(improvement) else None,
                "improvement_pct": float(improvement_pct) if not np.isnan(improvement_pct) else None,
                "t_statistic": float(t_stat) if not np.isnan(t_stat) else None,
                "p_value": float(p_val) if not np.isnan(p_val) else None,
                "significant": bool(p_val < 0.05) if not np.isnan(p_val) else None
            }
        
        self.results["stratified_analysis"] = strata_results
        return strata_results
    
    def create_visualizations(self):
        """Create visualizations"""
        print("\n🎨 Generating length control analysis visualizations...")
        
        fig = plt.figure(figsize=(16, 12))
        
        # 1. Length vs Coherence scatter plot
        plt.subplot(2, 3, 1)
        plt.scatter(self.baseline_data['total_words'], self.baseline_data['avg_coherence'], 
                   color='red', alpha=0.8, s=100, label='Baseline', marker='o')
        plt.scatter(self.ai_data['total_words'], self.ai_data['avg_coherence'], 
                   color='blue', alpha=0.6, s=50, label='AI Stories')
        
        # Add trend line
        z = np.polyfit(self.ai_data['total_words'], self.ai_data['avg_coherence'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(self.ai_data['total_words'].min(), self.ai_data['total_words'].max(), 100)
        plt.plot(x_trend, p(x_trend), "r--", alpha=0.8, label=f'Trend (r={stats.pearsonr(self.ai_data["total_words"], self.ai_data["avg_coherence"])[0]:.3f})')
        
        plt.xlabel('Text Length (words)')
        plt.ylabel('Coherence')
        plt.title('Text Length vs Coherence')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 2. Effect comparison of different control methods
        plt.subplot(2, 3, 2)
        methods = ['Original', 'Log Normalized', 'Sqrt Normalized', 'Residual Analysis']
        baseline_means = [
            self.results['raw_comparison']['baseline']['mean_coherence'],
            self.results['normalized_analysis']['log']['baseline_mean'],
            self.results['normalized_analysis']['sqrt']['baseline_mean'],
            self.results['residual_analysis']['baseline_residual_mean']
        ]
        ai_means = [
            self.results['raw_comparison']['ai_stories']['mean_coherence'],
            self.results['normalized_analysis']['log']['ai_mean'],
            self.results['normalized_analysis']['sqrt']['ai_mean'],
            self.results['residual_analysis']['ai_residual_mean']
        ]
        
        x = np.arange(len(methods))
        width = 0.35
        
        plt.bar(x - width/2, baseline_means, width, label='Baseline', color='red', alpha=0.7)
        plt.bar(x + width/2, ai_means, width, label='AI Stories', color='blue', alpha=0.7)
        
        plt.xlabel('Control Method')
        plt.ylabel('Coherence Value')
        plt.title('Effects of Different Length Control Methods')
        plt.xticks(x, methods, rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 3. Improvement comparison
        plt.subplot(2, 3, 3)
        improvements = [
            self.results['raw_comparison']['comparison']['relative_improvement_pct'],
            self.results['normalized_analysis']['log']['improvement_pct'],
            self.results['normalized_analysis']['sqrt']['improvement_pct'],
            self.results['residual_analysis']['residual_improvement'] * 100  # Convert to percentage for display
        ]
        
        if 'matched_analysis' in self.results and 'improvement_pct' in self.results['matched_analysis']:
            methods.append('Matched Sample')
            improvements.append(self.results['matched_analysis']['improvement_pct'])
        
        colors = ['red', 'orange', 'yellow', 'green', 'blue'][:len(methods)]
        bars = plt.bar(methods, improvements, color=colors, alpha=0.7)
        
        plt.xlabel('Control Method')
        plt.ylabel('Relative Improvement (%)')
        plt.title('AI Improvement vs Baseline')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, imp in zip(bars, improvements):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{imp:.1f}%', ha='center', va='bottom')
        
        # 4. Length distribution comparison
        plt.subplot(2, 3, 4)
        plt.hist(self.ai_data['total_words'], bins=20, alpha=0.7, label='AI Stories', color='blue')
        plt.hist(self.baseline_data['total_words'], bins=10, alpha=0.9, label='Baseline', color='red')
        plt.xlabel('Text Length (words)')
        plt.ylabel('Frequency')
        plt.title('Text Length Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 5. Residual distribution
        plt.subplot(2, 3, 5)
        if hasattr(self.ai_data, 'coherence_residual'):
            plt.hist(self.ai_data['coherence_residual'], bins=15, alpha=0.7, label='AI Residuals', color='blue')
            plt.hist(self.baseline_data['coherence_residual'], bins=8, alpha=0.9, label='Baseline Residuals', color='red')
            plt.xlabel('Coherence Residual')
            plt.ylabel('Frequency')
            plt.title('Coherence Residuals After Length Control')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        # 6. Stratified analysis results
        plt.subplot(2, 3, 6)
        if 'stratified_analysis' in self.results:
            strata_names = []
            baseline_strata = []
            ai_strata = []
            
            for stratum, data in self.results['stratified_analysis'].items():
                if 'baseline_coherence' in data and data['baseline_coherence'] is not None:
                    strata_names.append(stratum.replace('_', '\n'))
                    baseline_strata.append(data['baseline_coherence'])
                    ai_strata.append(data['ai_coherence'])
            
            x = np.arange(len(strata_names))
            width = 0.35
            
            if baseline_strata:
                plt.bar(x - width/2, baseline_strata, width, label='Baseline', color='red', alpha=0.7)
                plt.bar(x + width/2, ai_strata, width, label='AI Stories', color='blue', alpha=0.7)
                
                plt.xlabel('Length Stratum')
                plt.ylabel('Coherence')
                plt.title('Stratified Coherence Comparison')
                plt.xticks(x, strata_names)
                plt.legend()
                plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/Users/haha/Story/AAA/coherence_analysis/length_controlled_analysis_en.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print("   ✅ Length control analysis visualization saved")
    
    def generate_summary(self):
        """Generate analysis summary"""
        print("\n📋 Generating length control analysis summary...")
        
        summary = {
            "key_findings": [],
            "method_comparison": {},
            "recommendations": []
        }
        
        # Key findings
        raw_improvement = self.results['raw_comparison']['comparison']['relative_improvement_pct']
        length_correlation = self.results['length_coherence_relationship']['overall']['correlation']
        
        summary['key_findings'].append(f"Original analysis shows AI has {raw_improvement:.1f}% coherence improvement vs baseline")
        summary['key_findings'].append(f"Text length has {length_correlation:.3f} correlation with coherence")
        
        if abs(length_correlation) > 0.3:
            summary['key_findings'].append("Length has significant impact on coherence, requiring length control")
        
        # Method comparison
        for method in ['normalized_analysis', 'residual_analysis', 'matched_analysis']:
            if method in self.results:
                if method == 'normalized_analysis':
                    log_imp = self.results[method]['log']['improvement_pct']
                    sqrt_imp = self.results[method]['sqrt']['improvement_pct']
                    summary['method_comparison']['Normalization methods'] = {
                        'log_normalization': f"{log_imp:.1f}%",
                        'sqrt_normalization': f"{sqrt_imp:.1f}%"
                    }
                elif method == 'residual_analysis':
                    res_imp = self.results[method]['residual_improvement']
                    summary['method_comparison']['Residual analysis'] = f"Residual improvement: {res_imp:.4f}"
                elif method == 'matched_analysis':
                    if 'improvement_pct' in self.results[method]:
                        matched_imp = self.results[method]['improvement_pct']
                        summary['method_comparison']['Matched sample analysis'] = f"{matched_imp:.1f}%"
        
        # Recommendations
        summary['recommendations'].append("Keep original coherence analysis for overall performance assessment")
        summary['recommendations'].append("Use length-controlled analysis for true AI algorithm improvement evaluation")
        
        if abs(length_correlation) > 0.3:
            summary['recommendations'].append("Prioritize length-controlled results for algorithm evaluation")
        
        self.results['summary'] = summary
        return summary
    
    def run_complete_analysis(self):
        """Run complete length control analysis"""
        print("🚀 Starting length-controlled Coherence analysis...")
        print("=" * 60)
        
        # Execute various analyses
        self.analyze_length_coherence_relationship()
        self.raw_comparison()
        self.normalized_coherence_analysis()
        self.residual_coherence_analysis()
        self.matched_sample_analysis()
        self.stratified_analysis()
        
        # Generate visualizations and summary
        self.create_visualizations()
        self.generate_summary()
        
        # Save results
        output_path = '/Users/haha/Story/AAA/coherence_analysis/length_controlled_analysis_report_en.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("✅ Length-controlled Coherence analysis completed!")
        print(f"📊 Results saved to: {output_path}")
        print(f"📈 Visualizations saved to: length_controlled_analysis_en.png")
        
        return self.results

if __name__ == "__main__":
    # Run analysis
    analyzer = LengthControlledCoherenceAnalyzer('/Users/haha/Story/metrics_master_clean.csv')
    results = analyzer.run_complete_analysis()
    
    # Display key results
    print("\n" + "🏆" * 20 + " Key Results " + "🏆" * 20)
    
    raw_imp = results['raw_comparison']['comparison']['relative_improvement_pct']
    print(f"\n📊 Original analysis: AI improvement {raw_imp:.1f}%")
    
    if 'normalized_analysis' in results:
        log_imp = results['normalized_analysis']['log']['improvement_pct']
        sqrt_imp = results['normalized_analysis']['sqrt']['improvement_pct']
        print(f"📏 Normalized analysis: Log={log_imp:.1f}%, Sqrt={sqrt_imp:.1f}%")
    
    if 'residual_analysis' in results:
        res_imp = results['residual_analysis']['residual_improvement']
        print(f"📈 Residual analysis: Residual improvement {res_imp:.4f}")
    
    if 'matched_analysis' in results and 'improvement_pct' in results['matched_analysis']:
        matched_imp = results['matched_analysis']['improvement_pct']
        print(f"🎯 Matched sample: AI improvement {matched_imp:.1f}%")
    
    print(f"\n🔍 Length correlation: r = {results['length_coherence_relationship']['overall']['correlation']:.3f}")
