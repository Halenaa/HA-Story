"""
Performance data visualization and trend analysis tool
Used to generate charts, trend analysis and complexity curve fitting for performance reports
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import datetime
from pathlib import Path

# Set Chinese font (for Chinese systems)
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PerformanceVisualizer:
    """Performance data visualizer"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.reports = []
        
    def load_performance_reports(self, data_dir: str = "data/output") -> int:
        """Load all performance reports"""
        self.reports = []
        
        if not os.path.exists(data_dir):
            print(f" Data directory does not exist: {data_dir}")
            return 0
            
        report_count = 0
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.startswith("performance_analysis_") and file.endswith(".json"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            report = json.load(f)
                        self.reports.append({
                            'data': report,
                            'filepath': filepath,
                            'filename': file
                        })
                        report_count += 1
                    except Exception as e:
                        print(f" Failed to load report {file}: {e}")
        
        print(f" Successfully loaded {report_count} performance reports")
        return report_count
    
    def extract_data_for_analysis(self) -> pd.DataFrame:
        """Extract structured data for analysis"""
        data_rows = []
        
        for report in self.reports:
            report_data = report['data']
            
            # Basic information
            metadata = report_data.get('metadata', {})
            text_features = report_data.get('text_features', {})
            complexity = report_data.get('complexity_analysis', {})
            stage_performance = report_data.get('stage_performance', {})
            
            row = {
                'task_name': metadata.get('task_name', ''),
                'timestamp': metadata.get('analysis_timestamp', ''),
                'total_time': metadata.get('total_execution_time', 0),
                
                # Text features
                'word_count': text_features.get('total_word_count', 0),
                'char_count': text_features.get('total_char_count', 0),
                'sentence_count': text_features.get('total_sentence_count', 0),
                'chapter_count': text_features.get('chapter_count', 0),
                'avg_chapter_length': text_features.get('avg_chapter_length', 0),
                'avg_sentence_length': text_features.get('avg_sentence_length', 0),
                
                # Efficiency metrics
                'words_per_second': complexity.get('efficiency_metrics', {}).get('words_per_second', 0),
                'chars_per_second': complexity.get('efficiency_metrics', {}).get('chars_per_second', 0),
                'time_per_word': complexity.get('time_per_word', 0),
                'time_per_char': complexity.get('time_per_char', 0),
                
                # Complexity metrics
                'linear_indicator': complexity.get('complexity_indicators', {}).get('linear_indicator', 0),
                'sqrt_indicator': complexity.get('complexity_indicators', {}).get('sqrt_n_indicator', 0),
                'quadratic_indicator': complexity.get('complexity_indicators', {}).get('quadratic_indicator', 0),
                
                # Memory-related metrics
                'peak_memory_mb': metadata.get('peak_memory_usage_mb', 0),
                'memory_per_character': 0,
                
                # API cost-related metrics
                'total_api_cost': metadata.get('total_api_cost', 0),
                'total_tokens': metadata.get('total_tokens', 0),
                'cost_per_word': 0,
                'cost_per_token': 0,
                
                # Character-related metrics
                'character_count': text_features.get('character_features', {}).get('character_count', 0),
                'character_complexity_score': text_features.get('character_features', {}).get('character_complexity_score', 0),
                
                # Stage times
                **{f'{stage}_time': duration for stage, duration in stage_performance.get('stage_times', {}).items()}
            }
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # 计算派生指标
        if not df.empty:
            # 计算每角色内存开销
            df['memory_per_character'] = df.apply(
                lambda r: r['peak_memory_mb'] / r['character_count'] if r['character_count'] > 0 else 0, 
                axis=1
            )
            
            # 计算成本效率指标
            df['cost_per_word'] = df.apply(
                lambda r: r['total_api_cost'] / r['word_count'] if r['word_count'] > 0 else 0,
                axis=1
            )
            
            df['cost_per_token'] = df.apply(
                lambda r: r['total_api_cost'] / r['total_tokens'] if r['total_tokens'] > 0 else 0,
                axis=1
            )
        
        return df
    
    def plot_time_complexity_analysis(self, save_path: str = None) -> str:
        """Plot time complexity analysis chart"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            print(" No available data for complexity analysis")
            return None
            
        # Filter valid data
        df = df[(df['word_count'] > 0) & (df['total_time'] > 0)].copy()
        
        if len(df) < 2:
            print(" Insufficient data points for complexity analysis")
            return None
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Total time vs word count
        x = df['word_count'].values
        y = df['total_time'].values
        
        ax1.scatter(x, y, alpha=0.6, s=60)
        ax1.set_xlabel('Word Count')
        ax1.set_ylabel('Total Time (seconds)')
        ax1.set_title('Time Complexity Analysis: Total Time vs Word Count')
        
        # Try fitting different complexity models
        if len(x) >= 3:
            self._fit_complexity_curves(ax1, x, y)
        
        # 2. Efficiency trends
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            ax2.plot(range(len(df_sorted)), df_sorted['words_per_second'], marker='o')
            ax2.set_xlabel('Execution Order')
            ax2.set_ylabel('Generation Efficiency (words/sec)')
            ax2.set_title('Efficiency Trend Analysis')
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Stage time distribution
        stage_columns = [col for col in df.columns if col.endswith('_time')]
        if stage_columns:
            stage_data = df[stage_columns].mean()
            stage_names = [col.replace('_time', '').replace('_', ' ').title() for col in stage_columns]
            
            ax3.pie(stage_data.values, labels=stage_names, autopct='%1.1f%%')
            ax3.set_title('Average Stage Time Distribution')
        
        # 4. Complexity metrics comparison
        indicators = ['linear_indicator', 'sqrt_indicator', 'quadratic_indicator']
        available_indicators = [ind for ind in indicators if ind in df.columns and df[ind].sum() > 0]
        
        if available_indicators:
            indicator_data = df[available_indicators].mean()
            indicator_names = [ind.replace('_indicator', '').replace('_', ' ').title() for ind in available_indicators]
            
            ax4.bar(indicator_names, indicator_data.values)
            ax4.set_ylabel('Metric Value')
            ax4.set_title('Complexity Metrics Comparison')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save chart
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/complexity_analysis_{timestamp}.png"
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Complexity analysis chart saved: {save_path}")
        return save_path
    
    def _fit_complexity_curves(self, ax, x, y):
        """Fit different complexity curves"""
        x_fit = np.linspace(min(x), max(x), 100)
        
        # Linear fitting: T(n) = an + b
        try:
            linear_coeffs = np.polyfit(x, y, 1)
            linear_fit = np.poly1d(linear_coeffs)
            ax.plot(x_fit, linear_fit(x_fit), '--', label=f'Linear: T(n)={linear_coeffs[0]:.2e}n+{linear_coeffs[1]:.2f}', alpha=0.7)
        except:
            pass
        
        # N-log-N fitting: T(n) = a*n*log(n) + b
        try:
            def nlogn_func(x_val, a, b):
                return a * x_val * np.log(x_val + 1) + b
            
            popt, _ = curve_fit(nlogn_func, x, y, maxfev=1000)
            y_fit = nlogn_func(x_fit, *popt)
            ax.plot(x_fit, y_fit, ':', label=f'N*Log(N): T(n)={popt[0]:.2e}*n*log(n)+{popt[1]:.2f}', alpha=0.7)
        except:
            pass
        
        # Quadratic fitting: T(n) = an² + bn + c
        try:
            if len(x) >= 3:
                quad_coeffs = np.polyfit(x, y, 2)
                quad_fit = np.poly1d(quad_coeffs)
                ax.plot(x_fit, quad_fit(x_fit), '-.', label=f'Quadratic: T(n)={quad_coeffs[0]:.2e}n²+...', alpha=0.7)
        except:
            pass
        
        ax.legend()
    
    def plot_performance_trends(self, save_path: str = None) -> str:
        """Plot performance trends chart"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            print(" No available data")
            return None
            
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Execution time trend
        ax1.plot(df.index, df['total_time'], marker='o', linewidth=2, markersize=6)
        ax1.set_xlabel('Execution Order')
        ax1.set_ylabel('Total Time (seconds)')
        ax1.set_title('Execution Time Trend')
        ax1.grid(True, alpha=0.3)
        
        # Add trend line
        if len(df) >= 2:
            z = np.polyfit(df.index, df['total_time'], 1)
            p = np.poly1d(z)
            ax1.plot(df.index, p(df.index), "--", alpha=0.7, color='red', 
                    label=f'Trend: {"Rising" if z[0] > 0 else "Declining"}')
            ax1.legend()
        
        # 2. Generation efficiency trend
        ax2.plot(df.index, df['words_per_second'], marker='s', linewidth=2, markersize=6, color='green')
        ax2.set_xlabel('Execution Order')
        ax2.set_ylabel('Efficiency (words/sec)')
        ax2.set_title('Generation Efficiency Trend')
        ax2.grid(True, alpha=0.3)
        
        # 3. Word count vs time scatter plot
        scatter = ax3.scatter(df['word_count'], df['total_time'], 
                            c=df.index, cmap='viridis', s=80, alpha=0.7)
        ax3.set_xlabel('Word Count')
        ax3.set_ylabel('Total Time (seconds)')
        ax3.set_title('Word Count vs Time (Color indicates execution order)')
        plt.colorbar(scatter, ax=ax3, label='Execution Order')
        
        # 4. Stage time box plot
        stage_columns = [col for col in df.columns if col.endswith('_time') and df[col].sum() > 0]
        if stage_columns:
            stage_data = [df[col].dropna() for col in stage_columns]
            stage_names = [col.replace('_time', '').replace('_', '\n') for col in stage_columns]
            
            box_plot = ax4.boxplot(stage_data, labels=stage_names, patch_artist=True)
            ax4.set_ylabel('Time (seconds)')
            ax4.set_title('Stage Time Distribution')
            
            # Beautify box plot
            colors = plt.cm.Set3(np.linspace(0, 1, len(box_plot['boxes'])))
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
        
        plt.tight_layout()
        
        # Save chart
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/performance_trends_{timestamp}.png"
            
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f" Performance trends chart saved: {save_path}")
        return save_path
    
    def plot_memory_complexity_analysis(self, save_path: str = None) -> str:
        """Plot memory complexity analysis chart"""
        df = self.extract_data_for_analysis()
        
        if df.empty or df['peak_memory_mb'].sum() == 0:
            print(" No memory data for analysis")
            return None
            
        # Filter valid data
        df = df[(df['character_count'] > 0) & (df['peak_memory_mb'] > 0)].copy()
        
        if len(df) < 2:
            print(" Insufficient memory data points")
            return None
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Memory usage vs character count
        x = df['character_count'].values
        y = df['peak_memory_mb'].values
        
        ax1.scatter(x, y, alpha=0.6, s=60, c='red')
        ax1.set_xlabel('Character Count')
        ax1.set_ylabel('Peak Memory (MB)')
        ax1.set_title('Memory Complexity Analysis: Memory Usage vs Character Count')
        
        # Fit linear relationship
        if len(x) >= 2:
            try:
                linear_coeffs = np.polyfit(x, y, 1)
                x_fit = np.linspace(min(x), max(x), 100)
                linear_fit = np.poly1d(linear_coeffs)
                ax1.plot(x_fit, linear_fit(x_fit), '--', 
                        label=f'Linear fit: M = {linear_coeffs[0]:.2f}*C + {linear_coeffs[1]:.2f}',
                        color='darkred', alpha=0.8)
                ax1.legend()
            except:
                pass
        
        # 2. Memory overhead per character trend
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            ax2.plot(range(len(df_sorted)), df_sorted['memory_per_character'], 
                    marker='o', color='orange')
            ax2.set_xlabel('Execution Order')
            ax2.set_ylabel('Memory/Character (MB)')
            ax2.set_title('Memory Overhead per Character Trend')
        
        # 3. Memory vs character complexity
        if 'character_complexity_score' in df.columns and df['character_complexity_score'].sum() > 0:
            scatter = ax3.scatter(df['character_complexity_score'], df['peak_memory_mb'], 
                                c=df['character_count'], cmap='plasma', s=80, alpha=0.7)
            ax3.set_xlabel('Character Complexity Score')
            ax3.set_ylabel('Peak Memory (MB)')
            ax3.set_title('Memory vs Character Complexity (Color indicates character count)')
            plt.colorbar(scatter, ax=ax3, label='Character Count')
        
        # 4. Memory efficiency distribution
        if len(df['memory_per_character']) > 1:
            ax4.hist(df['memory_per_character'], bins=max(len(df)//3, 3), 
                    alpha=0.7, color='lightcoral', edgecolor='black')
            ax4.set_xlabel('Memory/Character (MB)')
            ax4.set_ylabel('Frequency')
            ax4.set_title('Memory Overhead per Character Distribution')
            ax4.axvline(df['memory_per_character'].mean(), color='red', linestyle='--',
                       label=f'Average: {df["memory_per_character"].mean():.2f} MB')
            ax4.legend()
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/memory_complexity_{timestamp}.png"
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f" Memory complexity analysis chart saved: {save_path}")
        return save_path
    
    def plot_api_cost_analysis(self, save_path: str = None) -> str:
        """Plot API cost analysis chart"""
        df = self.extract_data_for_analysis()
        
        if df.empty or df['total_api_cost'].sum() == 0:
            print(" No API cost data for analysis")
            return None
            
        # Filter valid data
        df = df[df['total_api_cost'] > 0].copy()
        
        if len(df) < 2:
            print(" Insufficient API cost data points")
            return None
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. API cost vs text length
        x = df['word_count'].values
        y = df['total_api_cost'].values
        
        ax1.scatter(x, y, alpha=0.6, s=60, c='green')
        ax1.set_xlabel('Generated Word Count')
        ax1.set_ylabel('API Cost ($)')
        ax1.set_title('API Cost vs Text Length')
        
        # 拟合线性关系
        if len(x) >= 2:
            try:
                linear_coeffs = np.polyfit(x, y, 1)
                x_fit = np.linspace(min(x), max(x), 100)
                linear_fit = np.poly1d(linear_coeffs)
                ax1.plot(x_fit, linear_fit(x_fit), '--', 
                        label=f'Linear fit: Cost = {linear_coeffs[0]:.6f}*Words + {linear_coeffs[1]:.6f}',
                        color='darkgreen', alpha=0.8)
                ax1.legend()
            except:
                pass
        
        # 2. Cost efficiency trend
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            ax2.plot(range(len(df_sorted)), df_sorted['cost_per_word'], 
                    marker='s', color='blue')
            ax2.set_xlabel('Execution Order')
            ax2.set_ylabel('Cost/Word ($)')
            ax2.set_title('Cost Efficiency Trend')
        
        # 3. Token usage vs cost
        if 'total_tokens' in df.columns:
            scatter = ax3.scatter(df['total_tokens'], df['total_api_cost'],
                                c=df['word_count'], cmap='viridis', s=80, alpha=0.7)
            ax3.set_xlabel('Total Tokens')
            ax3.set_ylabel('API Cost ($)')
            ax3.set_title('Token Usage vs Cost (Color indicates word count)')
            plt.colorbar(scatter, ax=ax3, label='Generated Word Count')
        
        # 4. Cost efficiency distribution
        if len(df['cost_per_word']) > 1:
            ax4.hist(df['cost_per_word'], bins=max(len(df)//3, 3), 
                    alpha=0.7, color='lightblue', edgecolor='black')
            ax4.set_xlabel('Cost/Word ($)')
            ax4.set_ylabel('Frequency')
            ax4.set_title('Cost per Word Distribution')
            ax4.axvline(df['cost_per_word'].mean(), color='blue', linestyle='--',
                       label=f'Average: ${df["cost_per_word"].mean():.6f}')
            ax4.legend()
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/api_cost_analysis_{timestamp}.png"
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"💰 API cost analysis chart saved: {save_path}")
        return save_path
    
    def generate_performance_heatmap(self, save_path: str = None) -> str:
        """Generate performance heatmap"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            print(" No available data")
            return None
            
        # Select numeric columns for heatmap analysis
        numeric_cols = ['total_time', 'word_count', 'char_count', 'sentence_count', 
                       'words_per_second', 'chars_per_second', 'time_per_word']
        
        # Include stage time columns
        stage_cols = [col for col in df.columns if col.endswith('_time')]
        numeric_cols.extend(stage_cols)
        
        # Filter existing columns
        available_cols = [col for col in numeric_cols if col in df.columns and df[col].sum() != 0]
        
        if len(available_cols) < 2:
            print(" Insufficient available numeric columns")
            return None
            
        # Create correlation heatmap
        correlation_data = df[available_cols].corr()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # 1. Correlation heatmap
        sns.heatmap(correlation_data, annot=True, cmap='coolwarm', center=0,
                   square=True, ax=ax1, cbar_kws={"shrink": .8})
        ax1.set_title('Performance Metrics Correlation Heatmap')
        
        # 2. Normalized performance metrics heatmap
        normalized_df = df[available_cols].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
        
        sns.heatmap(normalized_df.T, cmap='viridis', ax=ax2, 
                   cbar_kws={"shrink": .8}, yticklabels=True)
        ax2.set_title('Normalized Performance Metrics Heatmap')
        ax2.set_xlabel('Execution Instance')
        ax2.set_ylabel('Performance Metrics')
        
        plt.tight_layout()
        
        # Save chart
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/performance_heatmap_{timestamp}.png"
            
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f" Performance heatmap saved: {save_path}")
        return save_path
    
    def generate_comprehensive_report(self, save_dir: str = None) -> Dict[str, str]:
        """Generate comprehensive performance analysis report"""
        if save_dir is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = f"{self.output_dir}/comprehensive_report_{timestamp}"
        
        os.makedirs(save_dir, exist_ok=True)
        
        report_files = {}
        
        # 1. Time complexity analysis
        complexity_chart = self.plot_time_complexity_analysis(
            os.path.join(save_dir, "complexity_analysis.png")
        )
        if complexity_chart:
            report_files['complexity_analysis'] = complexity_chart
        
        # 2. Performance trends analysis
        trends_chart = self.plot_performance_trends(
            os.path.join(save_dir, "performance_trends.png")
        )
        if trends_chart:
            report_files['performance_trends'] = trends_chart
        
        # 3. Performance heatmap
        heatmap_chart = self.generate_performance_heatmap(
            os.path.join(save_dir, "performance_heatmap.png")
        )
        if heatmap_chart:
            report_files['performance_heatmap'] = heatmap_chart
        
        # 4. Memory complexity analysis
        memory_chart = self.plot_memory_complexity_analysis(
            os.path.join(save_dir, "memory_complexity.png")
        )
        if memory_chart:
            report_files['memory_complexity'] = memory_chart
        
        # 5. API cost analysis
        cost_chart = self.plot_api_cost_analysis(
            os.path.join(save_dir, "api_cost_analysis.png")
        )
        if cost_chart:
            report_files['api_cost_analysis'] = cost_chart
        
        # 6. Generate statistical summary
        summary_file = self.generate_statistical_summary(
            os.path.join(save_dir, "statistical_summary.json")
        )
        if summary_file:
            report_files['statistical_summary'] = summary_file
        
        # 7. Generate HTML report
        html_report = self.generate_html_report(save_dir, report_files)
        if html_report:
            report_files['html_report'] = html_report
        
        print(f" Comprehensive performance analysis report generated: {save_dir}")
        return report_files
    
    def generate_statistical_summary(self, save_path: str) -> str:
        """Generate statistical summary"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            return None
            
        summary = {
            'report_metadata': {
                'generated_at': datetime.datetime.now().isoformat(),
                'total_reports_analyzed': len(df),
                'analysis_period': {
                    'start': df['timestamp'].min() if 'timestamp' in df.columns else 'unknown',
                    'end': df['timestamp'].max() if 'timestamp' in df.columns else 'unknown'
                }
            },
            'performance_statistics': {
                'execution_time': {
                    'mean': float(df['total_time'].mean()),
                    'std': float(df['total_time'].std()),
                    'min': float(df['total_time'].min()),
                    'max': float(df['total_time'].max()),
                    'median': float(df['total_time'].median())
                },
                'efficiency': {
                    'mean_words_per_second': float(df['words_per_second'].mean()),
                    'std_words_per_second': float(df['words_per_second'].std()),
                    'best_efficiency': float(df['words_per_second'].max()),
                    'worst_efficiency': float(df['words_per_second'].min())
                },
                'text_characteristics': {
                    'avg_word_count': float(df['word_count'].mean()),
                    'avg_chapter_count': float(df['chapter_count'].mean()),
                    'avg_sentence_count': float(df['sentence_count'].mean())
                }
            },
            'complexity_analysis': self._analyze_complexity_trends(df),
            'recommendations': self._generate_performance_recommendations(df)
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Statistical summary saved: {save_path}")
        return save_path
    
    def _analyze_complexity_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze complexity trends"""
        if len(df) < 3:
            return {'status': 'insufficient_data'}
        
        # Try fitting linear relationship
        try:
            correlation, p_value = pearsonr(df['word_count'], df['total_time'])
            
            # Calculate average complexity indicators
            avg_linear = df['linear_indicator'].mean() if 'linear_indicator' in df.columns else 0
            avg_sqrt = df['sqrt_indicator'].mean() if 'sqrt_indicator' in df.columns else 0
            
            return {
                'time_vs_wordcount_correlation': {
                    'correlation_coefficient': float(correlation),
                    'p_value': float(p_value),
                    'strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak'
                },
                'complexity_indicators': {
                    'avg_linear_indicator': float(avg_linear),
                    'avg_sqrt_indicator': float(avg_sqrt),
                    'estimated_complexity': 'linear' if avg_linear > 0 and avg_sqrt > avg_linear * 10 else 'unknown'
                }
            }
        except:
            return {'status': 'analysis_failed'}
    
    def _generate_performance_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        if df.empty:
            return recommendations
        
        # Efficiency analysis
        avg_efficiency = df['words_per_second'].mean()
        if avg_efficiency < 10:
            recommendations.append("Low generation efficiency (<10 words/sec), recommend optimizing LLM calls or upgrading hardware performance")
        elif avg_efficiency > 50:
            recommendations.append("Excellent generation efficiency (>50 words/sec), good performance")
        
        # Time analysis
        if df['total_time'].std() / df['total_time'].mean() > 0.5:
            recommendations.append("Large execution time fluctuations, recommend checking network stability and cache strategy")
        
        # Stage analysis
        stage_cols = [col for col in df.columns if col.endswith('_time')]
        if stage_cols:
            stage_means = df[stage_cols].mean()
            slowest_stage = stage_means.idxmax()
            recommendations.append(f"Most time-consuming stage is {slowest_stage.replace('_time', '')}, can focus on optimizing this stage")
        
        return recommendations
    
    def generate_html_report(self, save_dir: str, report_files: Dict[str, str]) -> str:
        """Generate comprehensive report in HTML format"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Story Generation Performance Analysis Report</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ text-align: center; color: #2c3e50; margin-bottom: 40px; }}
                .section {{ margin: 30px 0; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                .chart img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
                .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
                .recommendation {{ background: #e8f5e8; padding: 15px; border-left: 4px solid #28a745; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1> Story Generation System Performance Analysis Report</h1>
                <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2> Time Complexity Analysis</h2>
                <div class="chart">
                    <img src="complexity_analysis.png" alt="Time Complexity Analysis Chart">
                </div>
                <p>This chart shows the relationship between generation time and text length, as well as fitting results of different complexity models.</p>
            </div>
            
            <div class="section">
                <h2> Performance Trends Analysis</h2>
                <div class="chart">
                    <img src="performance_trends.png" alt="Performance Trends Chart">
                </div>
                <p>This chart shows the change trends of key metrics such as execution time and generation efficiency.</p>
            </div>
            
            <div class="section">
                <h2> Performance Heatmap</h2>
                <div class="chart">
                    <img src="performance_heatmap.png" alt="Performance Heatmap">
                </div>
                <p>This chart shows the correlations and distribution characteristics between various performance metrics.</p>
            </div>
            
            <div class="section">
                <h2> Memory Complexity Analysis</h2>
                <div class="chart">
                    <img src="memory_complexity.png" alt="Memory Complexity Analysis Chart">
                </div>
                <p>This chart analyzes the relationship between memory usage and character count, as well as memory overhead at each stage.</p>
            </div>
            
            <div class="section">
                <h2> API Cost Analysis</h2>
                <div class="chart">
                    <img src="api_cost_analysis.png" alt="API Cost Analysis Chart">
                </div>
                <p>This chart shows the relationship between API call costs and text length, as well as cost efficiency analysis.</p>
            </div>
            
            <div class="section summary">
                <h2> Analysis Summary</h2>
                <p>For detailed statistical data and analysis results, please see the <a href="statistical_summary.json">statistical_summary.json</a> file.</p>
                
                <h3> Performance Improvement Recommendations</h3>
                <div class="recommendation">
                    <strong> Recommendation:</strong> Based on current data analysis, recommend focusing on the most time-consuming generation stages and optimizing LLM call strategies.
                </div>
                <div class="recommendation">
                    <strong>⚡ Efficiency Improvement:</strong> Consider implementing better caching mechanisms to reduce redundant computations.
                </div>
                <div class="recommendation">
                    <strong> Continuous Monitoring:</strong> Recommend running this analysis regularly to track performance change trends.
                </div>
            </div>
            
            <div class="section">
                <h2> Technical Notes</h2>
                <ul>
                    <li><strong>Time Complexity Analysis:</strong> Estimate algorithm time complexity by fitting different mathematical models</li>
                    <li><strong>Efficiency Metrics:</strong> Measure generation efficiency in "words/second"</li>
                    <li><strong>Stage Analysis:</strong> Break down the time consumption ratio of each generation step</li>
                    <li><strong>Correlation Analysis:</strong> Identify key factors affecting performance</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        html_path = os.path.join(save_dir, "performance_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f" HTML report generated: {html_path}")
        return html_path


def main():
    """Main function - demonstration of usage"""
    print(" Starting performance data visualization tool")
    
    # Create visualizer
    visualizer = PerformanceVisualizer()
    
    # Load data
    report_count = visualizer.load_performance_reports()
    
    if report_count == 0:
        print("No performance report data found")
        print("Please run story generation process first to generate performance data")
        return
    
    # Generate comprehensive report
    print("\nGenerating comprehensive performance analysis report...")
    report_files = visualizer.generate_comprehensive_report()
    
    print(f"\nAnalysis completed! Generated the following files:")
    for report_type, file_path in report_files.items():
        print(f"   {report_type}: {file_path}")
    
    print(f"\n Open {report_files.get('html_report', 'report file')} to view complete analysis results")


if __name__ == "__main__":
    main()
