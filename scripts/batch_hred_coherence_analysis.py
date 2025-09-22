"""
批量HRED连贯性分析脚本
遍历regression_test文件夹中的所有Markdown文件，运行HRED连贯性评估
将结果汇总到CSV表格中
"""

import os
import json
import pandas as pd
import re
from datetime import datetime
import sys

# 添加路径以便导入分析模块
sys.path.append('.')

# 导入HRED连贯性评估器
try:
    from src.analysis.hred_coherence_evaluator import HREDCoherenceEvaluator
    print("✅ 成功导入HRED连贯性评估器")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保src/analysis/hred_coherence_evaluator.py存在")
    sys.exit(1)

def parse_folder_name(folder_name):
    """
    解析文件夹名称，提取实验参数
    例：thelittleredridinghood_sciencefictionrewrite_linear_T0.7_s2
    """
    parts = folder_name.split('_')
    
    # 查找模式标识
    mode_part = None
    temp_part = None
    seed_part = None
    
    for part in parts:
        if part in ['linear', 'nonlinear']:
            mode_part = part
        elif part.startswith('T') and '.' in part:
            temp_part = part
        elif part.startswith('s') and part[1:].isdigit():
            seed_part = part
    
    # 构建结果
    result = {
        'folder_name': folder_name,
        'topic': 'Little Red Riding Hood',  # 从文件夹名推断
        'style': 'Science Fiction Rewrite',  # 从文件夹名推断
        'mode': mode_part if mode_part else 'unknown',
        'temperature': float(temp_part[1:]) if temp_part else 0.0,
        'seed': int(seed_part[1:]) if seed_part else 0
    }
    
    return result

def parse_markdown_to_story_data(markdown_content):
    """
    将Markdown内容解析为类似JSON story的格式
    """
    chapters = []
    
    # 按章节分割
    chapter_sections = re.split(r'\n# ', markdown_content)
    
    # 处理第一个章节（可能没有前导换行符）
    if chapter_sections[0].startswith('# '):
        chapter_sections[0] = chapter_sections[0][2:]  # 移除开头的'# '
    
    for i, section in enumerate(chapter_sections):
        if not section.strip():
            continue
            
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # 第一行是标题
        title = lines[0].strip()
        
        # 其余部分是内容
        content_lines = lines[1:]
        content = '\n'.join(content_lines).strip()
        
        # 移除markdown语法标记（简单处理）
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # 粗体
        content = re.sub(r'\*([^*]+)\*', r'\1', content)      # 斜体  
        content = re.sub(r'`([^`]+)`', r'\1', content)        # 代码
        content = re.sub(r'---+', '', content)               # 分隔线
        
        # 创建类似JSON的结构
        chapter = {
            'chapter_id': f"Chapter {i+1}",
            'title': title,
            'plot': content
        }
        chapters.append(chapter)
    
    return chapters

def run_batch_hred_analysis(base_dir="/Users/haha/Story/data/output/regression_test"):
    """
    批量运行HRED连贯性分析
    """
    print("🚀 开始批量HRED连贯性分析...")
    print(f"扫描目录: {base_dir}")
    
    # 扫描所有文件夹
    if not os.path.exists(base_dir):
        print(f"❌ 目录不存在: {base_dir}")
        return None
    
    folders = [f for f in os.listdir(base_dir) 
              if os.path.isdir(os.path.join(base_dir, f)) and not f.startswith('.')]
    
    print(f"📁 发现 {len(folders)} 个实验文件夹")
    
    # 存储所有结果
    all_results = []
    success_count = 0
    failed_files = []
    
    # 初始化HRED评估器（只初始化一次，提高效率）
    print("🔄 初始化HRED连贯性评估器...")
    try:
        evaluator = HREDCoherenceEvaluator(model_name="all-mpnet-base-v2")
        print("✅ HRED评估器初始化成功")
    except Exception as e:
        print(f"❌ HRED评估器初始化失败: {e}")
        return None
    
    # 遍历每个文件夹
    for i, folder in enumerate(folders, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(folders)}] 处理文件夹: {folder}")
        
        # 解析文件夹参数
        folder_params = parse_folder_name(folder)
        print(f"参数: {folder_params['mode']} | T{folder_params['temperature']} | s{folder_params['seed']}")
        
        # 构建MD文件路径
        md_file_path = os.path.join(base_dir, folder, "enhanced_story_dialogue_updated.md")
        
        if not os.path.exists(md_file_path):
            print(f"⚠️ MD文件不存在: {md_file_path}")
            failed_files.append({
                'folder': folder,
                'reason': 'MD文件不存在',
                'path': md_file_path
            })
            continue
        
        try:
            # 读取Markdown文件
            print("📖 读取Markdown文件...")
            with open(md_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 解析为story格式
            print("🔄 解析Markdown为故事格式...")
            story_data = parse_markdown_to_story_data(markdown_content)
            
            if not story_data:
                print("❌ Markdown解析失败，没有找到章节")
                failed_files.append({
                    'folder': folder,
                    'reason': 'Markdown解析失败',
                    'path': md_file_path
                })
                continue
            
            print(f"✅ 解析到 {len(story_data)} 个章节")
            
            # 运行HRED连贯性分析
            print("🔄 运行HRED连贯性分析...")
            coherence_result = evaluator.evaluate_story_coherence(story_data, include_details=True)
            
            if 'HRED连贯性评价' not in coherence_result:
                print("❌ HRED分析失败")
                failed_files.append({
                    'folder': folder,
                    'reason': 'HRED分析返回格式错误',
                    'path': md_file_path
                })
                continue
            
            # 提取关键指标
            hred_main = coherence_result['HRED连贯性评价']
            detailed = coherence_result.get('详细分析', {})
            stats = detailed.get('基本统计', {})
            
            # 构建结果记录
            result_record = {
                # 实验参数
                'folder_name': folder,
                'topic': folder_params['topic'],
                'style': folder_params['style'],
                'mode': folder_params['mode'],
                'temperature': folder_params['temperature'],
                'seed': folder_params['seed'],
                
                # HRED连贯性分析结果
                'model_name': hred_main['模型名称'],
                'sentence_count': hred_main['句子总数'],
                'adjacent_pairs': hred_main['相邻对数'],
                'avg_coherence': hred_main['平均连贯性'],
                
                # 详细统计
                'coherence_std': stats.get('连贯性标准差', None),
                'max_coherence': stats.get('最高连贯性', None),
                'min_coherence': stats.get('最低连贯性', None),
                'median_coherence': stats.get('连贯性中位数', None),
                
                # 连贯性断点和高连贯段落
                'low_coherence_points': len(detailed.get('连贯性断点', [])),
                'high_coherence_segments': len(detailed.get('高连贯性段落', [])),
                
                # 文件路径
                'source_file': md_file_path,
                
                # 分析时间
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            all_results.append(result_record)
            success_count += 1
            
            print(f"✅ 成功完成分析")
            print(f"   平均连贯性: {result_record['avg_coherence']:.4f}")
            print(f"   句子数量: {result_record['sentence_count']}")
            print(f"   相邻对数: {result_record['adjacent_pairs']}")
            
        except Exception as e:
            print(f"❌ 分析异常: {str(e)}")
            failed_files.append({
                'folder': folder,
                'reason': f'异常: {str(e)}',
                'path': md_file_path
            })
    
    # 生成汇总报告
    print(f"\n{'='*60}")
    print("📊 批量HRED分析完成汇总:")
    print(f"✅ 成功分析: {success_count}/{len(folders)} 个文件")
    print(f"❌ 失败文件: {len(failed_files)} 个")
    
    if failed_files:
        print("\n失败文件列表:")
        for failure in failed_files:
            print(f"  - {failure['folder']}: {failure['reason']}")
    
    if all_results:
        # 保存结果到CSV
        df = pd.DataFrame(all_results)
        
        # 确保输出目录存在
        os.makedirs('output/batch_hred_results', exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f'output/batch_hred_results/batch_hred_coherence_analysis_{timestamp}.csv'
        json_filename = f'output/batch_hred_results/batch_hred_coherence_analysis_{timestamp}.json'
        
        # 保存为CSV
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"📊 CSV结果已保存: {csv_filename}")
        
        # 保存为JSON（包含完整数据）
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'total_experiments': len(folders),
                    'successful_analyses': success_count,
                    'failed_analyses': len(failed_files),
                    'failed_files': failed_files,
                    'hred_model': 'all-mpnet-base-v2'
                },
                'results': all_results
            }, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON结果已保存: {json_filename}")
        
        # 显示基本统计
        print(f"\n📈 HRED连贯性统计:")
        print(f"温度分布: {df['temperature'].value_counts().to_dict()}")
        print(f"模式分布: {df['mode'].value_counts().to_dict()}")
        print(f"平均连贯性范围: {df['avg_coherence'].min():.4f} - {df['avg_coherence'].max():.4f}")
        print(f"整体平均连贯性: {df['avg_coherence'].mean():.4f}")
        print(f"平均句子数量: {df['sentence_count'].mean():.1f}")
        
        # 找出最连贯和最不连贯的故事
        best_coherence = df.loc[df['avg_coherence'].idxmax()]
        worst_coherence = df.loc[df['avg_coherence'].idxmin()]
        
        print(f"\n🏆 最连贯的故事:")
        print(f"   {best_coherence['mode']} T{best_coherence['temperature']} s{best_coherence['seed']}: {best_coherence['avg_coherence']:.4f}")
        
        print(f"🔻 最不连贯的故事:")
        print(f"   {worst_coherence['mode']} T{worst_coherence['temperature']} s{worst_coherence['seed']}: {worst_coherence['avg_coherence']:.4f}")
        
        return {
            'csv_file': csv_filename,
            'json_file': json_filename,
            'dataframe': df,
            'success_count': success_count,
            'failed_count': len(failed_files),
            'failed_files': failed_files
        }
    
    return None

if __name__ == "__main__":
    print("🎯 批量HRED连贯性分析工具")
    print("将分析所有regression_test实验结果的Markdown文件")
    
    result_summary = run_batch_hred_analysis()
    
    if result_summary:
        print(f"\n🎉 批量HRED分析完成！")
        print(f"📊 CSV文件: {result_summary['csv_file']}")
        print(f"📄 JSON文件: {result_summary['json_file']}")
        print(f"✅ 成功: {result_summary['success_count']} 个")
        print(f"❌ 失败: {result_summary['failed_count']} 个")
        
        print(f"\n💡 结果解读:")
        print(f"HRED连贯性分数范围0-1，越接近1表示相邻句子语义越相似")
        print(f"这个指标能够衡量故事的语义流畅度和逻辑连贯性")
    else:
        print(f"\n❌ 批量HRED分析未产生结果")
