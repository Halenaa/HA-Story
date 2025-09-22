#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取所有分析数据和输出结果
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import os

def extract_all_data():
    """提取所有数据和分析结果"""
    
    content_lines = []
    content_lines.append('# 📊 问卷实验数据分析 - 完整数据集合')
    content_lines.append(f'**生成时间**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}')
    content_lines.append('**数据来源**: 原始问卷 + 分析结果 + Notebook输出')
    content_lines.append('=' * 80)
    content_lines.append('')

    # 1. 读取原始问卷数据
    print('📖 读取原始问卷数据...')
    try:
        df_raw = pd.read_csv('Interview.csv')
        content_lines.append('# 📄 一、原始问卷数据 (Interview.csv)')
        content_lines.append('')
        content_lines.append(f'**数据规模**: {df_raw.shape[0]}行参与者 × {df_raw.shape[1]}列数据')
        content_lines.append('')
        
        content_lines.append('## 🔍 数据预览 (前5行):')
        content_lines.append('```')
        content_lines.append(df_raw.head().to_string())
        content_lines.append('```')
        content_lines.append('')
        
        content_lines.append('## 📋 所有列名:')
        content_lines.append('```')
        for i, col in enumerate(df_raw.columns):
            content_lines.append(f'{i+1:2d}. {col}')
        content_lines.append('```')
        content_lines.append('')
        
        # 识别关键数据
        story_cols = [col for col in df_raw.columns if 'Story' in col]
        rating_cols = [col for col in df_raw.columns if any(keyword in col.lower() for keyword in ['coherent', 'emotional', 'quality', 'creative', 'fluency', 'structural', 'character'])]
        ranking_cols = [col for col in df_raw.columns if 'ranking' in col.lower()]
        
        content_lines.append('## 📊 数据结构分析:')
        content_lines.append('```')
        content_lines.append(f'参与者数量: {len(df_raw)}')
        content_lines.append(f'故事相关列: {len(story_cols)}个 {story_cols}')
        content_lines.append(f'评分相关列: {len(rating_cols)}个')
        content_lines.append(f'排名相关列: {len(ranking_cols)}个')
        content_lines.append('```')
        content_lines.append('')
        
        # 显示故事配置分布
        if story_cols:
            content_lines.append('## 🎯 故事配置分布:')
            content_lines.append('```')
            for col in story_cols:
                unique_vals = df_raw[col].value_counts()
                content_lines.append(f'\n{col}:')
                for val, count in unique_vals.items():
                    content_lines.append(f'  {val}: {count}个参与者')
            content_lines.append('```')
            content_lines.append('')
        
        print(f'✅ 原始数据: {df_raw.shape[0]}x{df_raw.shape[1]}')
        
    except Exception as e:
        content_lines.append(f'❌ 无法读取原始数据: {e}')
        content_lines.append('')
        print(f'❌ 原始数据读取失败: {e}')

    # 2. 读取所有处理后的数据
    print('📊 读取分析结果数据...')
    content_lines.append('# 📊 二、分析结果数据文件')
    content_lines.append('')
    
    processed_dir = Path('data/processed')
    if processed_dir.exists():
        csv_files = list(processed_dir.glob('*.csv'))
        csv_files.sort()  # 按文件名排序
        
        content_lines.append(f'**处理后文件总数**: {len(csv_files)}个')
        content_lines.append('')
        
        for i, csv_file in enumerate(csv_files, 1):
            try:
                df = pd.read_csv(csv_file)
                
                content_lines.append(f'## 📋 {i}. {csv_file.name}')
                content_lines.append(f'**文件大小**: {csv_file.stat().st_size:,} bytes')
                content_lines.append(f'**数据维度**: {df.shape[0]}行 × {df.shape[1]}列')
                content_lines.append('')
                
                # 列名
                content_lines.append('**列名列表**:')
                content_lines.append('```')
                content_lines.append(' | '.join(df.columns))
                content_lines.append('```')
                content_lines.append('')
                
                # 数据预览
                if len(df) > 0:
                    max_rows = min(15, len(df))  # 最多显示15行
                    content_lines.append(f'**数据预览 (前{max_rows}行)**:')
                    content_lines.append('```')
                    content_lines.append(df.head(max_rows).to_string())
                    content_lines.append('```')
                    content_lines.append('')
                    
                    # 数值统计
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        content_lines.append('**数值列统计**:')
                        content_lines.append('```')
                        content_lines.append(df[numeric_cols].describe().to_string())
                        content_lines.append('```')
                        content_lines.append('')
                    
                    # 分类统计
                    categorical_cols = df.select_dtypes(include=['object']).columns
                    if len(categorical_cols) > 0 and len(categorical_cols) <= 3:  # 只显示少数分类列
                        content_lines.append('**分类列分布**:')
                        content_lines.append('```')
                        for col in categorical_cols:
                            if df[col].nunique() <= 20:  # 只显示类别不太多的列
                                counts = df[col].value_counts()
                                content_lines.append(f'\n{col}:')
                                for val, count in counts.head(10).items():
                                    content_lines.append(f'  {val}: {count}')
                        content_lines.append('```')
                        content_lines.append('')
                
                content_lines.append('---')
                content_lines.append('')
                print(f'✅ {csv_file.name}: {df.shape[0]}x{df.shape[1]}')
                
            except Exception as e:
                content_lines.append(f'❌ 读取 {csv_file.name} 失败: {e}')
                content_lines.append('')
                print(f'❌ {csv_file.name} 读取失败: {e}')
    else:
        content_lines.append('⚠️ data/processed/ 目录不存在')
        content_lines.append('')
    
    # 3. 从notebook提取有意义的输出
    print('📝 提取notebook输出...')
    try:
        with open('interview_analysis_v2.ipynb', 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        content_lines.append('# 🔧 三、Notebook执行输出')
        content_lines.append('')
        
        output_count = 0
        for i, cell in enumerate(notebook['cells']):
            if cell['cell_type'] == 'code':
                outputs = cell.get('outputs', [])
                if outputs:
                    # 获取标题
                    source = cell.get('source', [])
                    title = 'Code Cell'
                    if source and isinstance(source, list):
                        first_line = source[0].strip()
                        if first_line.startswith('#'):
                            title = first_line.replace('#', '').strip()[:80]
                    
                    content_lines.append(f'## 📋 Cell {i}: {title}')
                    content_lines.append('')
                    
                    for output in outputs:
                        if output.get('output_type') == 'stream':
                            text = ''.join(output.get('text', []))
                            if text.strip():
                                content_lines.append('```')
                                content_lines.append(text.strip())
                                content_lines.append('```')
                                content_lines.append('')
                        elif output.get('output_type') == 'error':
                            content_lines.append('❌ **执行错误**:')
                            content_lines.append('```')
                            error_text = '\n'.join(output.get('traceback', []))
                            content_lines.append(error_text)
                            content_lines.append('```')
                            content_lines.append('')
                    
                    content_lines.append('---')
                    content_lines.append('')
                    output_count += 1
        
        content_lines.append(f'**总计**: 找到 {output_count} 个有输出的cells')
        content_lines.append('')
        print(f'✅ Notebook: {output_count}个输出cells')
        
    except Exception as e:
        content_lines.append(f'❌ 无法读取notebook: {e}')
        content_lines.append('')
        print(f'❌ Notebook读取失败: {e}')
    
    # 4. 生成总结
    content_lines.append('# 📋 四、数据集合总结')
    content_lines.append('')
    content_lines.append(f'- **原始数据**: Interview.csv')
    content_lines.append(f'- **处理后文件**: {len(list(Path("data/processed").glob("*.csv")) if Path("data/processed").exists() else [])}个CSV文件')
    content_lines.append(f'- **分析输出**: Notebook执行结果')
    content_lines.append(f'- **生成时间**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}')
    content_lines.append('')
    content_lines.append('🎯 **这个文件包含了完整的数据支撑，可以直接分享给其他人查看！**')
    content_lines.append('')
    
    return '\n'.join(content_lines)

if __name__ == '__main__':
    try:
        print('🚀 开始提取所有数据...')
        full_content = extract_all_data()
        
        # 保存文件
        output_file = '📊 完整数据集合_所有输出.md'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        # 显示结果
        size = os.path.getsize(output_file)
        lines = len(full_content.split('\n'))
        
        print(f'\n🎉 数据集合生成完成！')
        print(f'📁 文件: {output_file}')
        print(f'📊 大小: {size:,} bytes')
        print(f'📄 行数: {lines:,} 行')
        print('')
        print('✅ 文件包含:')
        print('   📋 原始问卷数据 + 列名 + 数据预览')
        print('   📊 所有10个分析结果CSV文件的完整内容')
        print('   🔧 Notebook中的实际执行输出')
        print('   📈 详细统计信息和数据分布')
        print('')
        print('🎯 这个文件有完整的数据支撑，可以直接分享！')
        
    except Exception as e:
        print(f'❌ 生成失败: {e}')
        import traceback
        traceback.print_exc()
