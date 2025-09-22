#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix correlation heatmap with clear annotations and proper design
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Set high-quality defaults
plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300
sns.set_style("whitegrid")

def create_improved_correlation_heatmaps():
    """Create improved correlation heatmaps with clear annotations"""
    
    # Load data
    df = pd.read_csv('/Users/haha/Story/metrics_master_clean.csv')
    
    # Select core metrics for five dimensions
    metrics = {
        'Diversity': 'distinct_avg',
        'Semantic\nContinuity': 'avg_semantic_continuity', 
        'Fluency\n(PPL)': 'pseudo_ppl',
        'Fluency\n(Error Rate)': 'err_per_100w',
        'Emotion': 'correlation_coefficient'
    }
    
    # Create correlation dataframe
    corr_data = pd.DataFrame()
    for dim_name, metric in metrics.items():
        if metric in df.columns:
            corr_data[dim_name] = df[metric]
    
    # Calculate correlations
    pearson_corr = corr_data.corr(method='pearson')
    spearman_corr = corr_data.corr(method='spearman')
    
    output_dir = Path("/Users/haha/Story/AAA/stage1_statistical_rigor_analysis/")
    
    # Method 1: Side-by-side comparison with full matrices
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    
    # Pearson correlation (left panel)
    sns.heatmap(pearson_corr, annot=True, cmap='RdBu_r', center=0,
                square=True, ax=ax1, fmt='.3f', 
                cbar_kws={"shrink": .8, "label": "Pearson r"},
                linewidths=0.5, annot_kws={'size': 11, 'weight': 'bold'})
    ax1.set_title('Pearson Linear Correlations (r)', fontweight='bold', fontsize=14)
    ax1.tick_params(axis='x', rotation=45, labelsize=10)
    ax1.tick_params(axis='y', rotation=0, labelsize=10)
    
    # Spearman correlation (right panel)
    sns.heatmap(spearman_corr, annot=True, cmap='RdBu_r', center=0,
                square=True, ax=ax2, fmt='.3f',
                cbar_kws={"shrink": .8, "label": "Spearman ρ"},
                linewidths=0.5, annot_kws={'size': 11, 'weight': 'bold'})
    ax2.set_title('Spearman Rank Correlations (ρ)', fontweight='bold', fontsize=14)
    ax2.tick_params(axis='x', rotation=45, labelsize=10)
    ax2.tick_params(axis='y', rotation=0, labelsize=10)
    
    plt.suptitle('Figure 4: Five-Dimension Correlation Analysis', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    # Save side-by-side version
    output_file_side = output_dir / 'figure_4_correlation_heatmap_sidebyside.png'
    plt.savefig(output_file_side, dpi=300, bbox_inches='tight')
    print(f"✅ Side-by-side heatmap saved: {output_file_side}")
    
    plt.close()
    
    # Method 2: Combined triangular matrix (upper = Pearson, lower = Spearman)
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Create combined matrix
    combined_corr = spearman_corr.copy()
    
    # Fill upper triangle with Pearson correlations
    for i in range(len(combined_corr)):
        for j in range(i+1, len(combined_corr)):
            combined_corr.iloc[i, j] = pearson_corr.iloc[i, j]
    
    # Create annotations matrix
    annot_matrix = combined_corr.copy()
    for i in range(len(annot_matrix)):
        for j in range(len(annot_matrix)):
            if i < j:  # Upper triangle (Pearson)
                annot_matrix.iloc[i, j] = f"{pearson_corr.iloc[i, j]:.3f}"
            elif i > j:  # Lower triangle (Spearman)
                annot_matrix.iloc[i, j] = f"{spearman_corr.iloc[i, j]:.3f}"
            else:  # Diagonal
                annot_matrix.iloc[i, j] = "1.000"
    
    # Plot combined heatmap
    sns.heatmap(combined_corr, annot=annot_matrix, cmap='RdBu_r', center=0,
                square=True, ax=ax, fmt='',
                cbar_kws={"shrink": .8, "label": "Correlation Coefficient"},
                linewidths=1.0, annot_kws={'size': 12, 'weight': 'bold'})
    
    ax.set_title('Figure 4: Five-Dimension Correlation Matrix\\n(Upper Triangle: Pearson r, Lower Triangle: Spearman ρ)', 
                 fontweight='bold', fontsize=14, pad=20)
    
    # Add legend
    ax.text(0.02, 0.98, 'Upper Triangle: Pearson (r)\\nLower Triangle: Spearman (ρ)', 
            transform=ax.transAxes, fontsize=10, fontweight='bold',
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Save triangular version
    output_file_tri = output_dir / 'figure_4_correlation_heatmap_triangular.png'
    plt.savefig(output_file_tri, dpi=300, bbox_inches='tight')
    print(f"✅ Triangular heatmap saved: {output_file_tri}")
    
    plt.close()
    
    # Method 3: Create interpretation guide
    create_interpretation_guide(pearson_corr, spearman_corr, output_dir)
    
    return pearson_corr, spearman_corr

def create_interpretation_guide(pearson_corr, spearman_corr, output_dir):
    """Create a visual interpretation guide for the correlation matrices"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Spearman correlation with interpretation
    sns.heatmap(spearman_corr, annot=True, cmap='RdBu_r', center=0,
                square=True, ax=ax1, fmt='.3f',
                cbar_kws={"shrink": .8}, linewidths=0.5,
                annot_kws={'size': 10, 'weight': 'bold'})
    ax1.set_title('A) Spearman Rank Correlations (ρ)\\nRobust to outliers, captures monotonic relationships', 
                  fontweight='bold', fontsize=12)
    
    # 2. Pearson correlation
    sns.heatmap(pearson_corr, annot=True, cmap='RdBu_r', center=0,
                square=True, ax=ax2, fmt='.3f',
                cbar_kws={"shrink": .8}, linewidths=0.5,
                annot_kws={'size': 10, 'weight': 'bold'})
    ax2.set_title('B) Pearson Linear Correlations (r)\\nMeasures linear relationships, sensitive to outliers', 
                  fontweight='bold', fontsize=12)
    
    # 3. Difference matrix
    diff_matrix = pearson_corr - spearman_corr
    sns.heatmap(diff_matrix, annot=True, cmap='RdBu_r', center=0,
                square=True, ax=ax3, fmt='.3f',
                cbar_kws={"shrink": .8}, linewidths=0.5,
                annot_kws={'size': 10, 'weight': 'bold'})
    ax3.set_title('C) Difference (Pearson - Spearman)\\nLarge differences suggest non-linear relationships', 
                  fontweight='bold', fontsize=12)
    
    # 4. Correlation strength interpretation
    # Create a dummy matrix for interpretation legend
    interp_matrix = np.array([[1.0, 0.8, 0.5, 0.3, 0.1],
                             [0.8, 1.0, 0.0, -0.3, -0.5],
                             [0.5, 0.0, 1.0, -0.8, -1.0],
                             [0.3, -0.3, -0.8, 1.0, 0.0],
                             [0.1, -0.5, -1.0, 0.0, 1.0]])
    
    labels = ['Perfect\\n(±1.0)', 'Strong\\n(±0.8)', 'Moderate\\n(±0.5)', 'Weak\\n(±0.3)', 'Negligible\\n(±0.1)']
    
    sns.heatmap(interp_matrix, annot=True, cmap='RdBu_r', center=0,
                square=True, ax=ax4, fmt='.1f',
                xticklabels=labels, yticklabels=labels,
                cbar_kws={"shrink": .8}, linewidths=0.5,
                annot_kws={'size': 10, 'weight': 'bold'})
    ax4.set_title('D) Correlation Strength Guide\\nInterpretation of correlation magnitudes', 
                  fontweight='bold', fontsize=12)
    
    plt.suptitle('Figure 4: Complete Correlation Analysis with Interpretation Guide', 
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save interpretation guide
    output_file_guide = output_dir / 'figure_4_correlation_interpretation_guide.png'
    plt.savefig(output_file_guide, dpi=300, bbox_inches='tight')
    print(f"✅ Interpretation guide saved: {output_file_guide}")
    
    plt.close()

def print_correlation_summary(pearson_corr, spearman_corr):
    """Print detailed correlation summary"""
    
    print("\n📊 DETAILED CORRELATION SUMMARY")
    print("="*50)
    
    dimensions = ['Diversity', 'Semantic\\nContinuity', 'Fluency\\n(PPL)', 'Fluency\\n(Error Rate)', 'Emotion']
    
    print("\n🔍 KEY RELATIONSHIPS:")
    
    key_pairs = [
        (0, 1, 'Diversity ↔ Semantic Continuity'),
        (0, 2, 'Diversity ↔ Fluency (PPL)'),
        (0, 3, 'Diversity ↔ Error Rate'),
        (1, 3, 'Semantic Continuity ↔ Error Rate'),
        (2, 3, 'PPL ↔ Error Rate')
    ]
    
    for i, j, name in key_pairs:
        pearson_val = pearson_corr.iloc[i, j]
        spearman_val = spearman_corr.iloc[i, j]
        
        # Determine strength
        strength_p = "Strong" if abs(pearson_val) > 0.5 else "Moderate" if abs(pearson_val) > 0.3 else "Weak"
        strength_s = "Strong" if abs(spearman_val) > 0.5 else "Moderate" if abs(spearman_val) > 0.3 else "Weak"
        
        print(f"\n{name}:")
        print(f"  Pearson r:  {pearson_val:+.3f} ({strength_p})")
        print(f"  Spearman ρ: {spearman_val:+.3f} ({strength_s})")
        
        # Interpretation
        if abs(pearson_val - spearman_val) > 0.1:
            print(f"  ⚠️  Large difference suggests non-linear relationship")
        
        if abs(spearman_val) > 0.5:
            direction = "negative" if spearman_val < 0 else "positive"
            print(f"  📈 Strong {direction} correlation detected!")

if __name__ == "__main__":
    print("🔧 Fixing correlation heatmaps with improved design...")
    
    # Create improved correlation heatmaps
    pearson_corr, spearman_corr = create_improved_correlation_heatmaps()
    
    # Print detailed summary
    print_correlation_summary(pearson_corr, spearman_corr)
    
    print("\n🎉 Improved correlation visualizations complete!")
    print("\n📋 Generated Files:")
    print("- figure_4_correlation_heatmap_sidebyside.png: Clear side-by-side comparison")
    print("- figure_4_correlation_heatmap_triangular.png: Combined triangular matrix")
    print("- figure_4_correlation_interpretation_guide.png: Complete interpretation guide")
