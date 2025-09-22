# C. Correlation Analysis Report

**Analysis Date**: September 14, 2025  
**Sample Size**: 57 samples (54 Multi-Agent + 3 Baseline)  
**Method**: pandas.corr() + seaborn.heatmap()  
**Correlation Methods**: Pearson (linear) + Spearman (rank-order)

---

## C.1 Five-Dimension Correlation Matrix

### Table C1: Spearman Correlation Matrix (ρ)

| Dimension | Diversity | Semantic Continuity | Fluency (PPL) | Fluency (Error) | Emotion |
|-----------|-----------|-------------------|---------------|----------------|----------|
| **Diversity** | 1.000 | -0.733 | 0.682 | 0.334 | 0.109 |
| **Semantic Continuity** | -0.733 | 1.000 | -0.529 | -0.373 | -0.038 |
| **Fluency (PPL)** | 0.682 | -0.529 | 1.000 | 0.257 | -0.071 |
| **Fluency (Error Rate)** | 0.334 | -0.373 | 0.257 | 1.000 | 0.057 |
| **Emotion** | 0.109 | -0.038 | -0.071 | 0.057 | 1.000 |

### Table C2: Pearson Correlation Matrix (r)

| Dimension | Diversity | Semantic Continuity | Fluency (PPL) | Fluency (Error) | Emotion |
|-----------|-----------|-------------------|---------------|----------------|----------|
| **Diversity** | 1.000 | -0.766 | 0.737 | 0.273 | -0.004 |
| **Semantic Continuity** | -0.766 | 1.000 | -0.583 | -0.637 | -0.010 |
| **Fluency (PPL)** | 0.737 | -0.583 | 1.000 | -0.058 | -0.104 |
| **Fluency (Error Rate)** | 0.273 | -0.637 | -0.058 | 1.000 | 0.118 |
| **Emotion** | -0.004 | -0.010 | -0.104 | 0.118 | 1.000 |

---

## C.2 Key Correlation Findings

### 🔍 Strong Correlations (|ρ| > 0.5)

#### 1. **Diversity vs Semantic Continuity**: ρ = -0.733
- **Relationship**: Strong negative correlation
- **Interpretation**: Higher lexical diversity tends to sacrifice semantic coherence, revealing the classic diversity-quality tradeoff

#### 2. **Diversity vs Fluency (PPL)**: ρ = 0.682
- **Relationship**: Strong positive correlation
- **Interpretation**: More diverse vocabulary usage leads to higher perplexity (reduced fluency)

### 📊 Moderate Correlations (0.3 ≤ |ρ| ≤ 0.5)

#### 3. **Semantic Continuity vs Error Rate**: ρ = -0.373
- **Relationship**: Moderate negative correlation
- **Interpretation**: More semantically coherent texts tend to have fewer grammatical errors

#### 4. **Diversity vs Error Rate**: ρ = 0.334
- **Relationship**: Moderate positive correlation
- **Interpretation**: More diverse expressions may introduce more grammatical errors

### 🤷 Weak Correlations (|ρ| < 0.3)

#### 5. **Emotion Dimension Correlations**
- Emotion vs Diversity: ρ = 0.109 (weak positive)
- Emotion vs Semantic Continuity: ρ = -0.038 (weak negative)
- **Interpretation**: Emotion dimension is relatively independent of other quality dimensions

---

## C.3 Correlation Patterns & Implications

### 📊 Core Discovery Patterns

1. **Diversity-Quality Tradeoff**: Clear negative correlation between diversity and semantic continuity
2. **Fluency Duality**: PPL and error rate represent different aspects of fluency with weak correlation
3. **Emotion Independence**: Emotion dimension operates relatively independently of other quality metrics
4. **Quality Consistency**: Semantic continuity positively correlates with lower error rates, indicating overall quality consistency

### 🎯 Practical Applications

#### System Design Tradeoffs
- **Creativity vs Quality**: Need to balance lexical diversity with semantic coherence
- **Fluency Optimization**: PPL and error rates require separate optimization strategies
- **Emotion Control**: Emotional expression can be adjusted independently without significantly affecting other dimensions

#### Multi-Agent System Advantage Explanation
- **Balanced Optimization**: Multi-Agent maintains reasonable diversity while significantly improving semantic continuity
- **Quality-Oriented**: Negative correlation patterns explain why Multi-Agent shows moderate diversity reduction
- **Comprehensive Improvement**: Coordinated improvements across multiple correlated dimensions demonstrate systematic optimization

---

## C.4 Conclusion Examples (Based on Real Data)

### ✅ **Primary Correlation Findings**

**"Diversity and semantic continuity show strong negative correlation (ρ=-0.73), indicating that diversity enhancement often sacrifices coherence."**

**"Diversity and perplexity show strong positive correlation (ρ=0.68), suggesting that lexical diversity reduces language fluency."**

**"Semantic continuity and error rate show negative correlation (ρ=-0.37), where coherent texts tend to be more grammatically accurate."**

### 📈 **System Performance Explanation**

**"Correlation analysis reveals the Multi-Agent system's design advantages: by moderately reducing lexical diversity, it achieves significant improvements in semantic continuity and language accuracy, demonstrating an intelligent quality-creativity tradeoff strategy."**

---

## C.5 Generated Files

- `figure_4_correlation_heatmap.png`: Main single-panel Spearman correlation heatmap
- `figure_4_correlation_heatmap_dual.png`: Dual-panel correlation heatmap (Pearson + Spearman)
- `section_C_correlation_report_en.md`: This correlation analysis report

---

*Based on complete correlation analysis of 57 samples*  
*Using robust Spearman rank correlation and Pearson linear correlation*
