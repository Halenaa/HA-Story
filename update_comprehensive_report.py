#!/usr/bin/env python3
"""
更新综合分析报告，包含normal_baseline数据
"""

import pandas as pd
import json
import numpy as np
from collections import Counter

def generate_comprehensive_report():
    """生成包含所有baseline的综合分析报告"""
    
    # 读取更新后的CSV数据
    df = pd.read_csv('/Users/haha/Story/data/core_metrics_analysis.csv')
    
    print(f"总配置数: {len(df)}")
    print(f"包含的类型: {df['genre'].unique()}")
    
    # 基础统计
    analysis_summary = {
        "total_configurations": len(df),
        "genres": dict(df['genre'].value_counts()),
        "structures": dict(df['structure'].value_counts()),
        "temperatures": dict(df['temperature'].value_counts()),
        "data_completeness": {
            "emotional_analysis": f"{df['roberta_avg_score'].notna().sum()}/{len(df)}",
            "coherence_analysis": f"{df['hred_avg_coherence'].notna().sum()}/{len(df)}",
            "structure_analysis": f"{df['tp_coverage'].notna().sum()}/{len(df)}",
            "text_features": f"{df['total_words'].notna().sum()}/{len(df)}"
        }
    }
    
    # 按类型分组分析
    def analyze_group(group):
        result = {
            "count": int(len(group)),
            "emotional_metrics": {
                "avg_roberta_score": float(group['roberta_avg_score'].mean()),
                "reagan_classifications": dict(group['reagan_classification'].value_counts())
            },
            "coherence_metrics": {
                "avg_hred_coherence": float(group['hred_avg_coherence'].mean())
            },
            "structure_metrics": {
                "avg_tp_coverage": dict(group['tp_coverage'].value_counts()),
                "avg_li_diversity": float(group['li_function_diversity'].mean())
            },
            "text_metrics": {
                "avg_words": float(group['total_words'].mean()),
                "avg_chapters": float(group['chapter_count'].mean()),
                "avg_sentences": float(group['sentence_count'].mean())
            }
        }
        
        # 转换value_counts结果中的numpy类型
        for key in ['reagan_classifications', 'avg_tp_coverage']:
            if key in result['emotional_metrics']:
                result['emotional_metrics'][key] = {str(k): int(v) for k, v in result['emotional_metrics'][key].items()}
            elif key in result['structure_metrics']:
                result['structure_metrics'][key] = {str(k): int(v) for k, v in result['structure_metrics'][key].items()}
        
        return result
    
    # 按类型分析
    genre_comparison = {}
    for genre in df['genre'].unique():
        genre_data = df[df['genre'] == genre]
        genre_comparison[genre] = analyze_group(genre_data)
        # 转换numpy类型为Python原生类型
        for key, value in genre_comparison[genre].items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if hasattr(subvalue, 'item'):  # numpy scalar
                        genre_comparison[genre][key][subkey] = subvalue.item()
                    elif isinstance(subvalue, dict):
                        for k, v in subvalue.items():
                            if hasattr(v, 'item'):
                                genre_comparison[genre][key][subkey][k] = v.item()
    
    # 按结构分析
    structure_comparison = {}
    for structure in df['structure'].unique():
        structure_data = df[df['structure'] == structure]
        structure_comparison[structure] = analyze_group(structure_data)
    
    # 按温度分析
    temperature_comparison = {}
    for temp in df['temperature'].unique():
        temp_key = f"T{temp}" if temp != 'baseline' else f"T{temp}"
        temp_data = df[df['temperature'] == temp]
        temperature_comparison[temp_key] = analyze_group(temp_data)
    
    # 详细指标统计
    detailed_metrics = {
        "emotional_arc": {
            "roberta_scores": {
                "mean": df['roberta_avg_score'].mean(),
                "std": df['roberta_avg_score'].std(),
                "min": df['roberta_avg_score'].min(),
                "max": df['roberta_avg_score'].max()
            },
            "reagan_classifications": dict(df['reagan_classification'].value_counts()),
            "correlation_coefficients": {
                "mean": df['correlation_coefficient'].mean(),
                "std": df['correlation_coefficient'].std()
            }
        },
        "coherence": {
            "hred_scores": {
                "mean": df['hred_avg_coherence'].mean(),
                "std": df['hred_avg_coherence'].std(),
                "min": df['hred_avg_coherence'].min(),
                "max": df['hred_avg_coherence'].max()
            }
        },
        "structure": {
            "tp_coverage_distribution": dict(df['tp_coverage'].value_counts()),
            "li_diversity": {
                "mean": df['li_function_diversity'].mean(),
                "std": df['li_function_diversity'].std(),
                "min": df['li_function_diversity'].min(),
                "max": df['li_function_diversity'].max()
            }
        },
        "text_features": {
            "word_counts": {
                "mean": df['total_words'].mean(),
                "std": df['total_words'].std(),
                "min": df['total_words'].min(),
                "max": df['total_words'].max()
            },
            "chapter_counts": {
                "mean": df['chapter_count'].mean(),
                "std": df['chapter_count'].std(),
                "min": df['chapter_count'].min(),
                "max": df['chapter_count'].max()
            },
            "sentence_counts": {
                "mean": df['sentence_count'].mean(),
                "std": df['sentence_count'].std(),
                "min": df['sentence_count'].min(),
                "max": df['sentence_count'].max()
            }
        }
    }
    
    # 组装完整报告
    comprehensive_report = {
        "analysis_summary": analysis_summary,
        "genre_comparison": genre_comparison,
        "structure_comparison": structure_comparison,
        "temperature_comparison": temperature_comparison,
        "detailed_metrics": detailed_metrics
    }
    
    return comprehensive_report

def generate_markdown_report(report_data):
    """生成Markdown格式报告"""
    
    md_content = """# 故事生成分析综合报告

## 📊 总体概览

- **总配置数**: {total_configs}
- **类型分布**: {genre_dist}
- **结构分布**: {structure_dist}
- **温度分布**: {temp_dist}

## 📈 数据完整性

- **情感分析**: {emotional_complete}
- **连贯性分析**: {coherence_complete}
- **结构分析**: {structure_complete}
- **文本特征**: {text_complete}

## 🎭 按类型比较

""".format(
        total_configs=report_data["analysis_summary"]["total_configurations"],
        genre_dist=report_data["analysis_summary"]["genres"],
        structure_dist=report_data["analysis_summary"]["structures"],
        temp_dist=report_data["analysis_summary"]["temperatures"],
        emotional_complete=report_data["analysis_summary"]["data_completeness"]["emotional_analysis"],
        coherence_complete=report_data["analysis_summary"]["data_completeness"]["coherence_analysis"],
        structure_complete=report_data["analysis_summary"]["data_completeness"]["structure_analysis"],
        text_complete=report_data["analysis_summary"]["data_completeness"]["text_features"]
    )
    
    # 添加各类型详细分析
    for genre, data in report_data["genre_comparison"].items():
        md_content += f"""
### {genre.title()}

- **配置数**: {data["count"]}
- **平均情感分数**: {data["emotional_metrics"]["avg_roberta_score"]:.4f}
- **平均连贯性**: {data["coherence_metrics"]["avg_hred_coherence"]:.4f}
- **平均Li功能多样性**: {data["structure_metrics"]["avg_li_diversity"]:.1f}
- **平均字数**: {data["text_metrics"]["avg_words"]:.0f}
- **平均章节数**: {data["text_metrics"]["avg_chapters"]:.1f}

**Reagan分类分布**:
"""
        for classification, count in data["emotional_metrics"]["reagan_classifications"].items():
            md_content += f"- {classification}: {count}个\n"
    
    return md_content

def main():
    print("="*80)
    print("更新综合分析报告（包含normal_baseline）")
    print("="*80)
    
    # 生成报告
    report = generate_comprehensive_report()
    
    # 保存JSON格式
    json_file = '/Users/haha/Story/data/comprehensive_analysis_report.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    md_content = generate_markdown_report(report)
    md_file = '/Users/haha/Story/data/comprehensive_analysis_report.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ JSON报告已更新: {json_file}")
    print(f"✅ Markdown报告已更新: {md_file}")
    
    # 打印关键统计
    print(f"\n📊 更新后的关键统计:")
    print(f"   总配置数: {report['analysis_summary']['total_configurations']}")
    print(f"   类型分布: {report['analysis_summary']['genres']}")
    print(f"   完整性检查: 情感分析 {report['analysis_summary']['data_completeness']['emotional_analysis']}")
    
    return True

if __name__ == "__main__":
    main()
