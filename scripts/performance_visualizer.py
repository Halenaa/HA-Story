"""
性能数据可视化和趋势分析工具
用于生成性能报告的图表、趋势分析和复杂度曲线拟合
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

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class PerformanceVisualizer:
    """性能数据可视化器"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.reports = []
        
    def load_performance_reports(self, data_dir: str = "data/output") -> int:
        """加载所有性能报告"""
        self.reports = []
        
        if not os.path.exists(data_dir):
            print(f"⚠️ 数据目录不存在: {data_dir}")
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
                        print(f"❌ 加载报告失败 {file}: {e}")
        
        print(f"✅ 成功加载 {report_count} 个性能报告")
        return report_count
    
    def extract_data_for_analysis(self) -> pd.DataFrame:
        """提取用于分析的结构化数据"""
        data_rows = []
        
        for report in self.reports:
            report_data = report['data']
            
            # 基本信息
            metadata = report_data.get('metadata', {})
            text_features = report_data.get('text_features', {})
            complexity = report_data.get('complexity_analysis', {})
            stage_performance = report_data.get('stage_performance', {})
            
            row = {
                'task_name': metadata.get('task_name', ''),
                'timestamp': metadata.get('analysis_timestamp', ''),
                'total_time': metadata.get('total_execution_time', 0),
                
                # 文本特征
                'word_count': text_features.get('total_word_count', 0),
                'char_count': text_features.get('total_char_count', 0),
                'sentence_count': text_features.get('total_sentence_count', 0),
                'chapter_count': text_features.get('chapter_count', 0),
                'avg_chapter_length': text_features.get('avg_chapter_length', 0),
                'avg_sentence_length': text_features.get('avg_sentence_length', 0),
                
                # 效率指标
                'words_per_second': complexity.get('efficiency_metrics', {}).get('words_per_second', 0),
                'chars_per_second': complexity.get('efficiency_metrics', {}).get('chars_per_second', 0),
                'time_per_word': complexity.get('time_per_word', 0),
                'time_per_char': complexity.get('time_per_char', 0),
                
                # 复杂度指标
                'linear_indicator': complexity.get('complexity_indicators', {}).get('linear_indicator', 0),
                'sqrt_indicator': complexity.get('complexity_indicators', {}).get('sqrt_n_indicator', 0),
                'quadratic_indicator': complexity.get('complexity_indicators', {}).get('quadratic_indicator', 0),
                
                # 内存相关指标
                'peak_memory_mb': metadata.get('peak_memory_usage_mb', 0),
                'memory_per_character': 0,
                
                # API成本相关指标
                'total_api_cost': metadata.get('total_api_cost', 0),
                'total_tokens': metadata.get('total_tokens', 0),
                'cost_per_word': 0,
                'cost_per_token': 0,
                
                # 角色相关指标
                'character_count': text_features.get('character_features', {}).get('character_count', 0),
                'character_complexity_score': text_features.get('character_features', {}).get('character_complexity_score', 0),
                
                # 各阶段时间
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
        """绘制时间复杂度分析图"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            print("⚠️ 没有可用数据进行复杂度分析")
            return None
            
        # 过滤有效数据
        df = df[(df['word_count'] > 0) & (df['total_time'] > 0)].copy()
        
        if len(df) < 2:
            print("⚠️ 数据点不足，无法进行复杂度分析")
            return None
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 总时间 vs 字数
        x = df['word_count'].values
        y = df['total_time'].values
        
        ax1.scatter(x, y, alpha=0.6, s=60)
        ax1.set_xlabel('字数')
        ax1.set_ylabel('总时间 (秒)')
        ax1.set_title('时间复杂度分析: 总时间 vs 字数')
        
        # 尝试拟合不同复杂度模型
        if len(x) >= 3:
            self._fit_complexity_curves(ax1, x, y)
        
        # 2. 效率趋势
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            ax2.plot(range(len(df_sorted)), df_sorted['words_per_second'], marker='o')
            ax2.set_xlabel('执行顺序')
            ax2.set_ylabel('生成效率 (字/秒)')
            ax2.set_title('效率趋势分析')
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. 各阶段时间分布
        stage_columns = [col for col in df.columns if col.endswith('_time')]
        if stage_columns:
            stage_data = df[stage_columns].mean()
            stage_names = [col.replace('_time', '').replace('_', ' ').title() for col in stage_columns]
            
            ax3.pie(stage_data.values, labels=stage_names, autopct='%1.1f%%')
            ax3.set_title('平均各阶段时间分布')
        
        # 4. 复杂度指标对比
        indicators = ['linear_indicator', 'sqrt_indicator', 'quadratic_indicator']
        available_indicators = [ind for ind in indicators if ind in df.columns and df[ind].sum() > 0]
        
        if available_indicators:
            indicator_data = df[available_indicators].mean()
            indicator_names = [ind.replace('_indicator', '').replace('_', ' ').title() for ind in available_indicators]
            
            ax4.bar(indicator_names, indicator_data.values)
            ax4.set_ylabel('指标值')
            ax4.set_title('复杂度指标对比')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # 保存图表
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/complexity_analysis_{timestamp}.png"
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 复杂度分析图已保存: {save_path}")
        return save_path
    
    def _fit_complexity_curves(self, ax, x, y):
        """拟合不同复杂度曲线"""
        x_fit = np.linspace(min(x), max(x), 100)
        
        # 线性拟合: T(n) = an + b
        try:
            linear_coeffs = np.polyfit(x, y, 1)
            linear_fit = np.poly1d(linear_coeffs)
            ax.plot(x_fit, linear_fit(x_fit), '--', label=f'线性: T(n)={linear_coeffs[0]:.2e}n+{linear_coeffs[1]:.2f}', alpha=0.7)
        except:
            pass
        
        # 对数线性拟合: T(n) = a*n*log(n) + b
        try:
            def nlogn_func(x_val, a, b):
                return a * x_val * np.log(x_val + 1) + b
            
            popt, _ = curve_fit(nlogn_func, x, y, maxfev=1000)
            y_fit = nlogn_func(x_fit, *popt)
            ax.plot(x_fit, y_fit, ':', label=f'N*Log(N): T(n)={popt[0]:.2e}*n*log(n)+{popt[1]:.2f}', alpha=0.7)
        except:
            pass
        
        # 二次拟合: T(n) = an² + bn + c
        try:
            if len(x) >= 3:
                quad_coeffs = np.polyfit(x, y, 2)
                quad_fit = np.poly1d(quad_coeffs)
                ax.plot(x_fit, quad_fit(x_fit), '-.', label=f'二次: T(n)={quad_coeffs[0]:.2e}n²+...', alpha=0.7)
        except:
            pass
        
        ax.legend()
    
    def plot_performance_trends(self, save_path: str = None) -> str:
        """绘制性能趋势图"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            print("⚠️ 没有可用数据")
            return None
            
        # 按时间排序
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 执行时间趋势
        ax1.plot(df.index, df['total_time'], marker='o', linewidth=2, markersize=6)
        ax1.set_xlabel('执行顺序')
        ax1.set_ylabel('总时间 (秒)')
        ax1.set_title('执行时间趋势')
        ax1.grid(True, alpha=0.3)
        
        # 添加趋势线
        if len(df) >= 2:
            z = np.polyfit(df.index, df['total_time'], 1)
            p = np.poly1d(z)
            ax1.plot(df.index, p(df.index), "--", alpha=0.7, color='red', 
                    label=f'趋势: {"上升" if z[0] > 0 else "下降"}')
            ax1.legend()
        
        # 2. 生成效率趋势
        ax2.plot(df.index, df['words_per_second'], marker='s', linewidth=2, markersize=6, color='green')
        ax2.set_xlabel('执行顺序')
        ax2.set_ylabel('效率 (字/秒)')
        ax2.set_title('生成效率趋势')
        ax2.grid(True, alpha=0.3)
        
        # 3. 字数 vs 时间散点图
        scatter = ax3.scatter(df['word_count'], df['total_time'], 
                            c=df.index, cmap='viridis', s=80, alpha=0.7)
        ax3.set_xlabel('字数')
        ax3.set_ylabel('总时间 (秒)')
        ax3.set_title('字数 vs 时间 (颜色表示时间顺序)')
        plt.colorbar(scatter, ax=ax3, label='执行顺序')
        
        # 4. 各阶段时间箱线图
        stage_columns = [col for col in df.columns if col.endswith('_time') and df[col].sum() > 0]
        if stage_columns:
            stage_data = [df[col].dropna() for col in stage_columns]
            stage_names = [col.replace('_time', '').replace('_', '\n') for col in stage_columns]
            
            box_plot = ax4.boxplot(stage_data, labels=stage_names, patch_artist=True)
            ax4.set_ylabel('时间 (秒)')
            ax4.set_title('各阶段时间分布')
            
            # 美化箱线图
            colors = plt.cm.Set3(np.linspace(0, 1, len(box_plot['boxes'])))
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
        
        plt.tight_layout()
        
        # 保存图表
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/performance_trends_{timestamp}.png"
            
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 性能趋势图已保存: {save_path}")
        return save_path
    
    def plot_memory_complexity_analysis(self, save_path: str = None) -> str:
        """绘制内存复杂度分析图"""
        df = self.extract_data_for_analysis()
        
        if df.empty or df['peak_memory_mb'].sum() == 0:
            print("⚠️ 没有内存数据进行分析")
            return None
            
        # 过滤有效数据
        df = df[(df['character_count'] > 0) & (df['peak_memory_mb'] > 0)].copy()
        
        if len(df) < 2:
            print("⚠️ 内存数据点不足")
            return None
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 内存使用 vs 角色数量
        x = df['character_count'].values
        y = df['peak_memory_mb'].values
        
        ax1.scatter(x, y, alpha=0.6, s=60, c='red')
        ax1.set_xlabel('角色数量')
        ax1.set_ylabel('峰值内存 (MB)')
        ax1.set_title('内存复杂度分析: 内存使用 vs 角色数量')
        
        # 拟合线性关系
        if len(x) >= 2:
            try:
                linear_coeffs = np.polyfit(x, y, 1)
                x_fit = np.linspace(min(x), max(x), 100)
                linear_fit = np.poly1d(linear_coeffs)
                ax1.plot(x_fit, linear_fit(x_fit), '--', 
                        label=f'线性拟合: M = {linear_coeffs[0]:.2f}*C + {linear_coeffs[1]:.2f}',
                        color='darkred', alpha=0.8)
                ax1.legend()
            except:
                pass
        
        # 2. 每角色内存开销趋势
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            ax2.plot(range(len(df_sorted)), df_sorted['memory_per_character'], 
                    marker='o', color='orange')
            ax2.set_xlabel('执行顺序')
            ax2.set_ylabel('内存/角色 (MB)')
            ax2.set_title('每角色内存开销趋势')
        
        # 3. 内存 vs 角色复杂度
        if 'character_complexity_score' in df.columns and df['character_complexity_score'].sum() > 0:
            scatter = ax3.scatter(df['character_complexity_score'], df['peak_memory_mb'], 
                                c=df['character_count'], cmap='plasma', s=80, alpha=0.7)
            ax3.set_xlabel('角色复杂度评分')
            ax3.set_ylabel('峰值内存 (MB)')
            ax3.set_title('内存 vs 角色复杂度 (颜色表示角色数量)')
            plt.colorbar(scatter, ax=ax3, label='角色数量')
        
        # 4. 内存效率分布
        if len(df['memory_per_character']) > 1:
            ax4.hist(df['memory_per_character'], bins=max(len(df)//3, 3), 
                    alpha=0.7, color='lightcoral', edgecolor='black')
            ax4.set_xlabel('内存/角色 (MB)')
            ax4.set_ylabel('频次')
            ax4.set_title('每角色内存开销分布')
            ax4.axvline(df['memory_per_character'].mean(), color='red', linestyle='--',
                       label=f'平均值: {df["memory_per_character"].mean():.2f} MB')
            ax4.legend()
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/memory_complexity_{timestamp}.png"
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"🧠 内存复杂度分析图已保存: {save_path}")
        return save_path
    
    def plot_api_cost_analysis(self, save_path: str = None) -> str:
        """绘制API成本分析图"""
        df = self.extract_data_for_analysis()
        
        if df.empty or df['total_api_cost'].sum() == 0:
            print("⚠️ 没有API成本数据进行分析")
            return None
            
        # 过滤有效数据
        df = df[df['total_api_cost'] > 0].copy()
        
        if len(df) < 2:
            print("⚠️ API成本数据点不足")
            return None
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. API成本 vs 文本长度
        x = df['word_count'].values
        y = df['total_api_cost'].values
        
        ax1.scatter(x, y, alpha=0.6, s=60, c='green')
        ax1.set_xlabel('生成字数')
        ax1.set_ylabel('API成本 ($)')
        ax1.set_title('API成本 vs 文本长度')
        
        # 拟合线性关系
        if len(x) >= 2:
            try:
                linear_coeffs = np.polyfit(x, y, 1)
                x_fit = np.linspace(min(x), max(x), 100)
                linear_fit = np.poly1d(linear_coeffs)
                ax1.plot(x_fit, linear_fit(x_fit), '--', 
                        label=f'线性拟合: Cost = {linear_coeffs[0]:.6f}*Words + {linear_coeffs[1]:.6f}',
                        color='darkgreen', alpha=0.8)
                ax1.legend()
            except:
                pass
        
        # 2. 成本效率趋势
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            ax2.plot(range(len(df_sorted)), df_sorted['cost_per_word'], 
                    marker='s', color='blue')
            ax2.set_xlabel('执行顺序')
            ax2.set_ylabel('成本/字 ($)')
            ax2.set_title('成本效率趋势')
        
        # 3. Token使用 vs 成本
        if 'total_tokens' in df.columns:
            scatter = ax3.scatter(df['total_tokens'], df['total_api_cost'],
                                c=df['word_count'], cmap='viridis', s=80, alpha=0.7)
            ax3.set_xlabel('总Tokens')
            ax3.set_ylabel('API成本 ($)')
            ax3.set_title('Token使用 vs 成本 (颜色表示字数)')
            plt.colorbar(scatter, ax=ax3, label='生成字数')
        
        # 4. 成本效率分布
        if len(df['cost_per_word']) > 1:
            ax4.hist(df['cost_per_word'], bins=max(len(df)//3, 3), 
                    alpha=0.7, color='lightblue', edgecolor='black')
            ax4.set_xlabel('成本/字 ($)')
            ax4.set_ylabel('频次')
            ax4.set_title('单字成本分布')
            ax4.axvline(df['cost_per_word'].mean(), color='blue', linestyle='--',
                       label=f'平均值: ${df["cost_per_word"].mean():.6f}')
            ax4.legend()
        
        plt.tight_layout()
        
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/api_cost_analysis_{timestamp}.png"
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"💰 API成本分析图已保存: {save_path}")
        return save_path
    
    def generate_performance_heatmap(self, save_path: str = None) -> str:
        """生成性能热力图"""
        df = self.extract_data_for_analysis()
        
        if df.empty:
            print("⚠️ 没有可用数据")
            return None
            
        # 选择数值列进行热力图分析
        numeric_cols = ['total_time', 'word_count', 'char_count', 'sentence_count', 
                       'words_per_second', 'chars_per_second', 'time_per_word']
        
        # 加入阶段时间列
        stage_cols = [col for col in df.columns if col.endswith('_time')]
        numeric_cols.extend(stage_cols)
        
        # 过滤存在的列
        available_cols = [col for col in numeric_cols if col in df.columns and df[col].sum() != 0]
        
        if len(available_cols) < 2:
            print("⚠️ 可用数值列不足")
            return None
            
        # 创建相关性热力图
        correlation_data = df[available_cols].corr()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # 1. 相关性热力图
        sns.heatmap(correlation_data, annot=True, cmap='coolwarm', center=0,
                   square=True, ax=ax1, cbar_kws={"shrink": .8})
        ax1.set_title('性能指标相关性热力图')
        
        # 2. 标准化后的性能指标热力图
        normalized_df = df[available_cols].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
        
        sns.heatmap(normalized_df.T, cmap='viridis', ax=ax2, 
                   cbar_kws={"shrink": .8}, yticklabels=True)
        ax2.set_title('标准化性能指标热力图')
        ax2.set_xlabel('执行实例')
        ax2.set_ylabel('性能指标')
        
        plt.tight_layout()
        
        # 保存图表
        if save_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.output_dir}/performance_heatmap_{timestamp}.png"
            
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"🔥 性能热力图已保存: {save_path}")
        return save_path
    
    def generate_comprehensive_report(self, save_dir: str = None) -> Dict[str, str]:
        """生成综合性能分析报告"""
        if save_dir is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = f"{self.output_dir}/comprehensive_report_{timestamp}"
        
        os.makedirs(save_dir, exist_ok=True)
        
        report_files = {}
        
        # 1. 时间复杂度分析
        complexity_chart = self.plot_time_complexity_analysis(
            os.path.join(save_dir, "complexity_analysis.png")
        )
        if complexity_chart:
            report_files['complexity_analysis'] = complexity_chart
        
        # 2. 性能趋势分析
        trends_chart = self.plot_performance_trends(
            os.path.join(save_dir, "performance_trends.png")
        )
        if trends_chart:
            report_files['performance_trends'] = trends_chart
        
        # 3. 性能热力图
        heatmap_chart = self.generate_performance_heatmap(
            os.path.join(save_dir, "performance_heatmap.png")
        )
        if heatmap_chart:
            report_files['performance_heatmap'] = heatmap_chart
        
        # 4. 内存复杂度分析
        memory_chart = self.plot_memory_complexity_analysis(
            os.path.join(save_dir, "memory_complexity.png")
        )
        if memory_chart:
            report_files['memory_complexity'] = memory_chart
        
        # 5. API成本分析
        cost_chart = self.plot_api_cost_analysis(
            os.path.join(save_dir, "api_cost_analysis.png")
        )
        if cost_chart:
            report_files['api_cost_analysis'] = cost_chart
        
        # 4. 生成统计摘要
        summary_file = self.generate_statistical_summary(
            os.path.join(save_dir, "statistical_summary.json")
        )
        if summary_file:
            report_files['statistical_summary'] = summary_file
        
        # 5. 生成HTML报告
        html_report = self.generate_html_report(save_dir, report_files)
        if html_report:
            report_files['html_report'] = html_report
        
        print(f"📊 综合性能分析报告已生成: {save_dir}")
        return report_files
    
    def generate_statistical_summary(self, save_path: str) -> str:
        """生成统计摘要"""
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
        
        print(f"📋 统计摘要已保存: {save_path}")
        return save_path
    
    def _analyze_complexity_trends(self, df: pd.DataFrame) -> Dict:
        """分析复杂度趋势"""
        if len(df) < 3:
            return {'status': 'insufficient_data'}
        
        # 尝试拟合线性关系
        try:
            correlation, p_value = pearsonr(df['word_count'], df['total_time'])
            
            # 计算平均复杂度指标
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
        """生成性能优化建议"""
        recommendations = []
        
        if df.empty:
            return recommendations
        
        # 效率分析
        avg_efficiency = df['words_per_second'].mean()
        if avg_efficiency < 10:
            recommendations.append("生成效率较低（<10字/秒），建议优化LLM调用或提升硬件性能")
        elif avg_efficiency > 50:
            recommendations.append("生成效率优秀（>50字/秒），性能表现良好")
        
        # 时间分析
        if df['total_time'].std() / df['total_time'].mean() > 0.5:
            recommendations.append("执行时间波动较大，建议检查网络稳定性和缓存策略")
        
        # 阶段分析
        stage_cols = [col for col in df.columns if col.endswith('_time')]
        if stage_cols:
            stage_means = df[stage_cols].mean()
            slowest_stage = stage_means.idxmax()
            recommendations.append(f"最耗时阶段是{slowest_stage.replace('_time', '')}，可重点优化此阶段")
        
        return recommendations
    
    def generate_html_report(self, save_dir: str, report_files: Dict[str, str]) -> str:
        """生成HTML格式的综合报告"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>故事生成性能分析报告</title>
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
                <h1>📊 故事生成系统性能分析报告</h1>
                <p>生成时间: {datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>🎯 时间复杂度分析</h2>
                <div class="chart">
                    <img src="complexity_analysis.png" alt="时间复杂度分析图">
                </div>
                <p>该图展示了生成时间与文本长度的关系，以及不同复杂度模型的拟合结果。</p>
            </div>
            
            <div class="section">
                <h2>📈 性能趋势分析</h2>
                <div class="chart">
                    <img src="performance_trends.png" alt="性能趋势图">
                </div>
                <p>该图展示了执行时间、生成效率等关键指标的变化趋势。</p>
            </div>
            
            <div class="section">
                <h2>🔥 性能热力图</h2>
                <div class="chart">
                    <img src="performance_heatmap.png" alt="性能热力图">
                </div>
                <p>该图展示了各性能指标之间的相关性和分布特征。</p>
            </div>
            
            <div class="section">
                <h2>🧠 内存复杂度分析</h2>
                <div class="chart">
                    <img src="memory_complexity.png" alt="内存复杂度分析图">
                </div>
                <p>该图分析了内存使用量与角色数量的关系，以及各阶段的内存开销。</p>
            </div>
            
            <div class="section">
                <h2>💰 API成本分析</h2>
                <div class="chart">
                    <img src="api_cost_analysis.png" alt="API成本分析图">
                </div>
                <p>该图展示了API调用成本与文本长度的关系，以及成本效率分析。</p>
            </div>
            
            <div class="section summary">
                <h2>📋 分析总结</h2>
                <p>详细的统计数据和分析结果请查看 <a href="statistical_summary.json">statistical_summary.json</a> 文件。</p>
                
                <h3>🎯 性能改进建议</h3>
                <div class="recommendation">
                    <strong>💡 建议:</strong> 基于当前数据分析，建议重点关注最耗时的生成阶段，优化LLM调用策略。
                </div>
                <div class="recommendation">
                    <strong>⚡ 效率提升:</strong> 可以考虑实现更好的缓存机制来减少重复计算。
                </div>
                <div class="recommendation">
                    <strong>📊 持续监控:</strong> 建议定期运行此分析以跟踪性能变化趋势。
                </div>
            </div>
            
            <div class="section">
                <h2>🛠️ 技术说明</h2>
                <ul>
                    <li><strong>时间复杂度分析:</strong> 通过拟合不同数学模型来估算算法的时间复杂度</li>
                    <li><strong>效率指标:</strong> 以"字/秒"为单位衡量生成效率</li>
                    <li><strong>阶段分析:</strong> 分解各个生成步骤的耗时占比</li>
                    <li><strong>相关性分析:</strong> 识别影响性能的关键因素</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        html_path = os.path.join(save_dir, "performance_report.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML报告已生成: {html_path}")
        return html_path


def main():
    """主函数 - 演示使用方法"""
    print("🚀 启动性能数据可视化工具")
    
    # 创建可视化器
    visualizer = PerformanceVisualizer()
    
    # 加载数据
    report_count = visualizer.load_performance_reports()
    
    if report_count == 0:
        print("❌ 没有找到性能报告数据")
        print("💡 请先运行故事生成流程以产生性能数据")
        return
    
    # 生成综合报告
    print("\n📊 正在生成综合性能分析报告...")
    report_files = visualizer.generate_comprehensive_report()
    
    print(f"\n✅ 分析完成！生成了以下文件:")
    for report_type, file_path in report_files.items():
        print(f"   {report_type}: {file_path}")
    
    print(f"\n🎯 打开 {report_files.get('html_report', '报告文件')} 查看完整分析结果")


if __name__ == "__main__":
    main()
