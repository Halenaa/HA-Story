#!/usr/bin/env python3
"""
整合所有 fluency 分析结果的脚本
将所有数据整合成一个包含 linear/nonlinear、Temperature、seeds 等标识的完整数据集
"""

import os
import json
import pandas as pd
import re
from datetime import datetime
from pathlib import Path


class FluencyDataIntegrator:
    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.all_data = []
        
    def extract_experiment_info(self, folder_name):
        """从文件夹名称提取实验信息"""
        # 模式: thelittleredridinghood_genre_method_temperature_seed
        pattern = r'thelittleredridinghood_([^_]+)(?:rewrite)?_([^_]+)_T([0-9.]+)_s([0-9]+)'
        match = re.match(pattern, folder_name)
        
        if match:
            genre, method, temperature, seed = match.groups()
            # 处理特殊情况
            if 'horror-suspense' in genre:
                genre = 'horror'
            elif 'romantic' in genre:
                genre = 'romantic'  
            elif 'sciencefiction' in genre:
                genre = 'sci-fi'
                
            return {
                'genre': genre,
                'method': method,  # linear or nonlinear
                'temperature': float(temperature),
                'seed': int(seed)
            }
        return None
    
    def process_experiment_results(self, subfolder):
        """处理实验结果文件夹"""
        print(f"处理实验文件夹: {subfolder.name}")
        
        # 遍历所有子文件夹（每个代表一个实验条件）
        for exp_folder in subfolder.iterdir():
            if not exp_folder.is_dir():
                continue
                
            fluency_file = exp_folder / 'fluency_analysis.json'
            if not fluency_file.exists():
                continue
                
            # 提取实验信息
            exp_info = self.extract_experiment_info(exp_folder.name)
            if not exp_info:
                print(f"无法解析文件夹名: {exp_folder.name}")
                continue
                
            # 读取fluency数据
            try:
                with open(fluency_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 整合数据
                integrated_data = {
                    'source_folder': subfolder.name,
                    'experiment_folder': exp_folder.name,
                    'data_type': 'experiment',
                    'genre': exp_info['genre'],
                    'method': exp_info['method'],
                    'temperature': exp_info['temperature'],
                    'seed': exp_info['seed'],
                    'pseudo_ppl': data.get('pseudo_ppl'),
                    'err_per_100w': data.get('err_per_100w'),
                    'error_count': data.get('error_count'),
                    'word_count': data.get('word_count'),
                    'char_count': data.get('char_count'),
                    'analysis_timestamp': data.get('analysis_timestamp'),
                    'model_name': data.get('model_name'),
                    'subsample_rate': data.get('subsample_rate')
                }
                
                self.all_data.append(integrated_data)
                print(f"  添加数据: {exp_info['genre']} {exp_info['method']} T{exp_info['temperature']} s{exp_info['seed']}")
                
            except Exception as e:
                print(f"处理文件 {fluency_file} 时出错: {e}")
    
    def process_baseline_results(self, subfolder):
        """处理基线结果文件夹"""
        print(f"处理基线文件夹: {subfolder.name}")
        
        # 查找所有 JSON 文件
        for json_file in subfolder.glob('*.json'):
            if 'summary' in json_file.name:
                continue  # 跳过summary文件
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 确定基线类型
                if 'normal' in json_file.name or 'normal' in subfolder.name:
                    baseline_type = 'normal_baseline'
                elif 'sci' in json_file.name or 'sci' in subfolder.name:
                    baseline_type = 'sci_baseline'
                else:
                    baseline_type = 'unknown_baseline'
                
                # 整合基线数据
                integrated_data = {
                    'source_folder': subfolder.name,
                    'experiment_folder': json_file.name,
                    'data_type': 'baseline',
                    'genre': baseline_type,
                    'method': 'baseline',
                    'temperature': None,
                    'seed': None,
                    'pseudo_ppl': data.get('pseudo_ppl'),
                    'err_per_100w': data.get('err_per_100w'),
                    'error_count': data.get('error_count'),
                    'word_count': data.get('word_count'),
                    'char_count': data.get('char_count'),
                    'analysis_timestamp': data.get('analysis_timestamp'),
                    'model_name': data.get('model_name'),
                    'subsample_rate': data.get('subsample_rate'),
                    'file_name': data.get('file_name'),
                    'description': data.get('description')
                }
                
                self.all_data.append(integrated_data)
                print(f"  添加基线数据: {baseline_type}")
                
            except Exception as e:
                print(f"处理文件 {json_file} 时出错: {e}")
    
    def integrate_all_data(self):
        """整合所有 fluency 数据"""
        print("开始整合 fluency 数据...")
        
        # 遍历所有结果文件夹
        for subfolder in self.results_dir.iterdir():
            if not subfolder.is_dir():
                continue
                
            folder_name = subfolder.name.lower()
            
            if 'baseline' in folder_name:
                self.process_baseline_results(subfolder)
            elif any(keyword in folder_name for keyword in ['test_results', 'horror', 'romantic', 'regression']):
                self.process_experiment_results(subfolder)
            else:
                print(f"跳过未识别的文件夹: {subfolder.name}")
        
        print(f"总共收集了 {len(self.all_data)} 条数据")
        
    def save_results(self, output_dir):
        """保存整合结果"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # 转换为DataFrame
        df = pd.DataFrame(self.all_data)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存为CSV
        csv_file = output_dir / f"integrated_fluency_data_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"CSV文件已保存到: {csv_file}")
        
        # 保存为JSON
        json_file = output_dir / f"integrated_fluency_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_data, f, indent=2, ensure_ascii=False)
        print(f"JSON文件已保存到: {json_file}")
        
        # 生成统计报告
        self.generate_summary_report(df, output_dir, timestamp)
        
        return df
    
    def generate_summary_report(self, df, output_dir, timestamp):
        """生成统计报告"""
        report = []
        report.append("# Fluency 数据整合报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"")
        
        # 数据总览
        report.append("## 数据总览")
        report.append(f"总数据条数: {len(df)}")
        report.append(f"")
        
        # 按数据类型分组
        report.append("### 按数据类型分组")
        type_counts = df['data_type'].value_counts()
        for data_type, count in type_counts.items():
            report.append(f"- {data_type}: {count} 条")
        report.append("")
        
        # 按流派分组（实验数据）
        experiment_df = df[df['data_type'] == 'experiment']
        if len(experiment_df) > 0:
            report.append("### 按流派分组（实验数据）")
            genre_counts = experiment_df['genre'].value_counts()
            for genre, count in genre_counts.items():
                report.append(f"- {genre}: {count} 条")
            report.append("")
            
            # 按方法分组
            report.append("### 按方法分组（实验数据）")
            method_counts = experiment_df['method'].value_counts()
            for method, count in method_counts.items():
                report.append(f"- {method}: {count} 条")
            report.append("")
            
            # 按温度分组
            report.append("### 按温度分组（实验数据）")
            temp_counts = experiment_df['temperature'].value_counts().sort_index()
            for temp, count in temp_counts.items():
                report.append(f"- T{temp}: {count} 条")
            report.append("")
        
        # 基线数据
        baseline_df = df[df['data_type'] == 'baseline']
        if len(baseline_df) > 0:
            report.append("### 基线数据")
            for _, row in baseline_df.iterrows():
                report.append(f"- {row['genre']}: PPL={row['pseudo_ppl']:.3f}, 错误率={row['err_per_100w']:.3f}")
            report.append("")
        
        # 关键指标统计
        if len(experiment_df) > 0:
            report.append("## 关键指标统计（实验数据）")
            report.append("### 伪困惑度 (Pseudo Perplexity)")
            report.append(f"- 平均值: {experiment_df['pseudo_ppl'].mean():.3f}")
            report.append(f"- 标准差: {experiment_df['pseudo_ppl'].std():.3f}")
            report.append(f"- 最小值: {experiment_df['pseudo_ppl'].min():.3f}")
            report.append(f"- 最大值: {experiment_df['pseudo_ppl'].max():.3f}")
            report.append("")
            
            report.append("### 错误率 (每100词)")
            report.append(f"- 平均值: {experiment_df['err_per_100w'].mean():.3f}")
            report.append(f"- 标准差: {experiment_df['err_per_100w'].std():.3f}")
            report.append(f"- 最小值: {experiment_df['err_per_100w'].min():.3f}")
            report.append(f"- 最大值: {experiment_df['err_per_100w'].max():.3f}")
            report.append("")
        
        # 保存报告
        report_file = output_dir / f"fluency_data_summary_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        print(f"统计报告已保存到: {report_file}")


def main():
    """主函数"""
    # 配置路径
    results_dir = "/Users/haha/Story/fluency_analysis_results"
    output_dir = "/Users/haha/Story/integrated_fluency_results"
    
    # 创建整合器
    integrator = FluencyDataIntegrator(results_dir)
    
    # 整合数据
    integrator.integrate_all_data()
    
    # 保存结果
    df = integrator.save_results(output_dir)
    
    print(f"\n整合完成！数据包含以下列:")
    for col in df.columns:
        print(f"  - {col}")
    
    print(f"\n数据预览:")
    print(df.head())


if __name__ == "__main__":
    main()
