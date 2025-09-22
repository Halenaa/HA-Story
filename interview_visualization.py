#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问卷调查数据可视化工具
创建交互式表格和图表来分析问卷调查结果
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_and_clean_data(file_path):
    """
    加载和清理数据
    """
    # 读取数据，跳过第一行标题
    df = pd.read_csv(file_path, skiprows=1)
    
    # 创建简化的列名映射
    column_mapping = {
        'Timestamp': '提交时间',
        'Parameter': '实验参数',
        'What is your gender?': '性别',
        'Age Group': '年龄组',
        'Educational Background': '教育背景',
        'Fiction Reading Frequency': '小说阅读频率',
        'What is your English proficiency level?': '英语水平',
        'How familiar are you with science fiction as a genre?': '科幻熟悉度'
    }
    
    # 为评分列创建简化名称
    story_metrics = ['连贯性', '情感发展', '角色一致性', '创意原创性', '语言流畅性', '结构完整性', '整体质量']
    story_numbers = [1, 2, 3, 4]
    
    for i, story_num in enumerate(story_numbers):
        for j, metric in enumerate(story_metrics):
            # 找到对应的原始列名
            original_cols = [col for col in df.columns if any(word in col.lower() for word in 
                           ['coherence', 'emotional', 'character', 'creativity', 'fluency', 'structural', 'quality'])]
            if i * len(story_metrics) + j < len(original_cols):
                old_col = original_cols[i * len(story_metrics) + j]
                new_col = f'故事{story_num}_{metric}'
                column_mapping[old_col] = new_col
    
    # 偏好类列名
    preference_mapping = {
        'Favorite Story Among the 4 stories you just read, which one do you like most?': '最喜欢的故事',
        'Most Coherent Story Which story do you think is the most coherent?': '最连贯的故事',
        'Most Creative Story Which story do you think is the most creative?': '最有创意的故事',
        'Most Engaging Story Which story most motivated you to continue reading?': '最吸引人的故事'
    }
    
    # 排名类列名
    ranking_mapping = {}
    for i in range(1, 5):
        old_col = f'Quality Ranking Please rank the 4 stories by overall quality from best to worst (1=best, 4=worst) [Story {i}]'
        if i < 4:
            ranking_mapping[old_col] = f'故事{i}_质量排名'
        else:
            # 处理Story 4的特殊情况
            old_col_alt = f'Quality Ranking Please rank the 4 stories by overall quality from best to worst (1=best, 4=worst) [Story {i}:]'
            ranking_mapping[old_col_alt] = f'故事{i}_质量排名'
    
    # 合并所有映射
    all_mappings = {**column_mapping, **preference_mapping, **ranking_mapping}
    
    # 重命名列
    df_clean = df.rename(columns=all_mappings)
    
    # 处理缺失值
    df_clean = df_clean.fillna('未填写')
    
    return df_clean

def create_basic_info_table(df):
    """
    创建基本信息统计表
    """
    basic_cols = ['性别', '年龄组', '教育背景', '小说阅读频率', '英语水平', '科幻熟悉度']
    
    basic_stats = {}
    for col in basic_cols:
        if col in df.columns:
            value_counts = df[col].value_counts()
            basic_stats[col] = value_counts.to_dict()
    
    return basic_stats

def create_story_ratings_analysis(df):
    """
    分析故事评分数据
    """
    story_metrics = ['连贯性', '情感发展', '角色一致性', '创意原创性', '语言流畅性', '结构完整性', '整体质量']
    story_numbers = [1, 2, 3, 4]
    
    ratings_data = {}
    
    for story_num in story_numbers:
        story_data = {}
        for metric in story_metrics:
            col_name = f'故事{story_num}_{metric}'
            if col_name in df.columns:
                ratings = pd.to_numeric(df[col_name], errors='coerce')
                story_data[metric] = {
                    '平均分': round(ratings.mean(), 2),
                    '标准差': round(ratings.std(), 2),
                    '中位数': ratings.median(),
                    '最小值': ratings.min(),
                    '最大值': ratings.max(),
                    '数据': ratings.tolist()
                }
        ratings_data[f'故事{story_num}'] = story_data
    
    return ratings_data

def create_preference_analysis(df):
    """
    分析偏好数据
    """
    preference_cols = ['最喜欢的故事', '最连贯的故事', '最有创意的故事', '最吸引人的故事']
    preference_stats = {}
    
    for col in preference_cols:
        if col in df.columns:
            value_counts = df[col].value_counts()
            preference_stats[col] = value_counts.to_dict()
    
    return preference_stats

def create_ranking_analysis(df):
    """
    分析排名数据
    """
    ranking_cols = [f'故事{i}_质量排名' for i in range(1, 5)]
    ranking_data = {}
    
    for i, col in enumerate(ranking_cols, 1):
        if col in df.columns:
            rankings = pd.to_numeric(df[col], errors='coerce')
            ranking_data[f'故事{i}'] = {
                '平均排名': round(rankings.mean(), 2),
                '排名分布': rankings.value_counts().sort_index().to_dict(),
                '获得第一名次数': (rankings == 1).sum(),
                '获得最后一名次数': (rankings == 4).sum()
            }
    
    return ranking_data

def create_streamlit_app():
    """
    创建Streamlit应用
    """
    st.set_page_config(page_title="问卷调查数据可视化", layout="wide")
    
    st.title("📊 问卷调查数据可视化分析")
    st.markdown("---")
    
    # 加载数据
    try:
        df = load_and_clean_data('Interview.csv')
        st.success(f"✅ 成功加载数据：{df.shape[0]} 个受试者，{df.shape[1]} 个字段")
    except Exception as e:
        st.error(f"❌ 数据加载失败：{str(e)}")
        return
    
    # 侧边栏
    st.sidebar.title("🔧 分析选项")
    analysis_type = st.sidebar.selectbox(
        "选择分析类型",
        ["基本信息概览", "故事评分分析", "偏好分析", "排名分析", "原始数据查看"]
    )
    
    if analysis_type == "基本信息概览":
        st.header("👥 受试者基本信息")
        
        basic_stats = create_basic_info_table(df)
        
        # 创建图表
        cols = st.columns(2)
        
        for i, (category, data) in enumerate(basic_stats.items()):
            with cols[i % 2]:
                fig = px.pie(
                    values=list(data.values()),
                    names=list(data.keys()),
                    title=category
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "故事评分分析":
        st.header("📚 故事评分分析")
        
        ratings_data = create_story_ratings_analysis(df)
        
        # 创建评分对比图
        metrics = ['连贯性', '情感发展', '角色一致性', '创意原创性', '语言流畅性', '结构完整性', '整体质量']
        stories = ['故事1', '故事2', '故事3', '故事4']
        
        # 平均分对比
        avg_scores = []
        for story in stories:
            if story in ratings_data:
                story_avgs = [ratings_data[story].get(metric, {}).get('平均分', 0) for metric in metrics]
                avg_scores.append(story_avgs)
        
        if avg_scores:
            fig = go.Figure()
            
            for i, story in enumerate(stories):
                fig.add_trace(go.Radar(
                    r=avg_scores[i],
                    theta=metrics,
                    fill='toself',
                    name=story,
                    line_color=px.colors.qualitative.Set1[i % len(px.colors.qualitative.Set1)]
                ))
            
            fig.update_layout(
                radar=dict(
                    radialaxis=dict(visible=True, range=[0, 10])
                ),
                showlegend=True,
                title="故事评分雷达图对比"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 详细统计表
        st.subheader("📈 详细评分统计")
        for story, data in ratings_data.items():
            with st.expander(f"📖 {story} 详细数据"):
                stats_df = pd.DataFrame.from_dict(
                    {metric: {k: v for k, v in stats.items() if k != '数据'} 
                     for metric, stats in data.items()}, 
                    orient='index'
                )
                st.dataframe(stats_df, use_container_width=True)
    
    elif analysis_type == "偏好分析":
        st.header("❤️ 故事偏好分析")
        
        preference_stats = create_preference_analysis(df)
        
        cols = st.columns(2)
        
        for i, (category, data) in enumerate(preference_stats.items()):
            with cols[i % 2]:
                fig = px.bar(
                    x=list(data.keys()),
                    y=list(data.values()),
                    title=category,
                    labels={'x': '故事', 'y': '选择次数'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "排名分析":
        st.header("🏆 故事质量排名分析")
        
        ranking_data = create_ranking_analysis(df)
        
        # 平均排名条形图
        stories = list(ranking_data.keys())
        avg_rankings = [data['平均排名'] for data in ranking_data.values()]
        
        fig = px.bar(
            x=stories,
            y=avg_rankings,
            title="故事平均排名 (数值越小排名越高)",
            labels={'x': '故事', 'y': '平均排名'},
            color=avg_rankings,
            color_continuous_scale='RdYlBu_r'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 排名分布热图
        st.subheader("🔥 排名分布热图")
        
        ranking_matrix = []
        for story in stories:
            distribution = ranking_data[story]['排名分布']
            row = [distribution.get(i, 0) for i in range(1, 5)]
            ranking_matrix.append(row)
        
        ranking_df = pd.DataFrame(
            ranking_matrix,
            index=stories,
            columns=['第1名', '第2名', '第3名', '第4名']
        )
        
        fig = px.imshow(
            ranking_df.values,
            labels=dict(x="排名", y="故事", color="获得次数"),
            x=['第1名', '第2名', '第3名', '第4名'],
            y=stories,
            color_continuous_scale='Blues',
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 详细排名统计
        st.subheader("📊 排名详细统计")
        ranking_summary_df = pd.DataFrame.from_dict(
            {story: {k: v for k, v in data.items() if k != '排名分布'} 
             for story, data in ranking_data.items()}, 
            orient='index'
        )
        st.dataframe(ranking_summary_df, use_container_width=True)
    
    else:  # 原始数据查看
        st.header("🔍 原始数据查看")
        
        # 数据筛选
        st.subheader("🎛️ 数据筛选")
        
        # 性别筛选
        gender_options = ['全部'] + df['性别'].unique().tolist()
        selected_gender = st.selectbox("选择性别", gender_options)
        
        # 年龄组筛选
        age_options = ['全部'] + df['年龄组'].unique().tolist()
        selected_age = st.selectbox("选择年龄组", age_options)
        
        # 应用筛选
        filtered_df = df.copy()
        if selected_gender != '全部':
            filtered_df = filtered_df[filtered_df['性别'] == selected_gender]
        if selected_age != '全部':
            filtered_df = filtered_df[filtered_df['年龄组'] == selected_age]
        
        st.info(f"筛选后数据：{filtered_df.shape[0]} 行，{filtered_df.shape[1]} 列")
        
        # 显示数据
        st.dataframe(filtered_df, use_container_width=True, height=600)
        
        # 下载按钮
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载筛选后的数据",
            data=csv,
            file_name=f"filtered_interview_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def create_static_report():
    """
    创建静态分析报告
    """
    df = load_and_clean_data('Interview.csv')
    
    print("=" * 60)
    print("📊 问卷调查数据分析报告")
    print("=" * 60)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据规模：{df.shape[0]} 个受试者，{df.shape[1]} 个字段")
    print()
    
    # 基本信息统计
    print("👥 受试者基本信息统计")
    print("-" * 40)
    basic_stats = create_basic_info_table(df)
    for category, data in basic_stats.items():
        print(f"\n{category}:")
        for item, count in data.items():
            percentage = (count / df.shape[0]) * 100
            print(f"  {item}: {count} 人 ({percentage:.1f}%)")
    
    # 故事评分分析
    print("\n\n📚 故事评分分析")
    print("-" * 40)
    ratings_data = create_story_ratings_analysis(df)
    
    for story, data in ratings_data.items():
        print(f"\n{story}:")
        for metric, stats in data.items():
            print(f"  {metric}: 平均 {stats['平均分']:.2f}，标准差 {stats['标准差']:.2f}")
    
    # 偏好分析
    print("\n\n❤️ 故事偏好分析")
    print("-" * 40)
    preference_stats = create_preference_analysis(df)
    
    for category, data in preference_stats.items():
        print(f"\n{category}:")
        total_responses = sum(data.values())
        for story, count in data.items():
            percentage = (count / total_responses) * 100
            print(f"  {story}: {count} 次 ({percentage:.1f}%)")
    
    # 排名分析
    print("\n\n🏆 故事质量排名分析")
    print("-" * 40)
    ranking_data = create_ranking_analysis(df)
    
    print("平均排名 (数值越小排名越高):")
    for story, data in ranking_data.items():
        print(f"  {story}: {data['平均排名']:.2f}")
    
    print("\n获得第一名次数:")
    first_place_counts = [(story, data['获得第一名次数']) for story, data in ranking_data.items()]
    first_place_counts.sort(key=lambda x: x[1], reverse=True)
    for story, count in first_place_counts:
        print(f"  {story}: {count} 次")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "streamlit":
        create_streamlit_app()
    else:
        create_static_report()