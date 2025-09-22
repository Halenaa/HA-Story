# 🧪 实验4A：离散参数敏感性分析报告
## Experiment 4A: Discrete Parameter Sensitivity Analysis
### （基于54组实验的3×2×3参数组合分析）

## 🎯 核心发现汇总

1. **Horror**: 最大改进 **298.4%** (效应大小: 0.420, 最优: nonlinear@0.7)
2. **Romantic**: 最大改进 **178.5%** (效应大小: 0.264, 最优: nonlinear@0.3)
3. **Sciencefiction**: 最大改进 **166.2%** (效应大小: 0.310, 最优: linear@0.7)

## 📚 Sciencefiction Genre 详细分析

### 🏗️ Nonlinear Structure

- **Temperature Effect Size**: 0.3620
- **Optimal Configuration**: Temperature = 0.7 (Score: -0.016)
- **Performance Improvement**: 95.8%
- **Sample Size**: 9
- **Statistical Test**: Not Significant (F=0.57, p=0.5951)

**Temperature Settings Performance**:
- 🥈 Temperature 0.3: -0.048 ± 0.199 (n=3)
- 🥇 Temperature 0.7: -0.016 ± 0.732 (n=3)
- 🥉 Temperature 0.9: -0.378 ± 0.248 (n=3)

### 🏗️ Linear Structure

- **Temperature Effect Size**: 0.3097
- **Optimal Configuration**: Temperature = 0.7 (Score: 0.123)
- **Performance Improvement**: 166.2%
- **Sample Size**: 9
- **Statistical Test**: Not Significant (F=1.22, p=0.3605)

**Temperature Settings Performance**:
- 🥈 Temperature 0.3: 0.009 ± 0.207 (n=3)
- 🥇 Temperature 0.7: 0.123 ± 0.181 (n=3)
- 🥉 Temperature 0.9: -0.186 ± 0.326 (n=3)

## 📚 Horror Genre 详细分析

### 🏗️ Nonlinear Structure

- **Temperature Effect Size**: 0.4196
- **Optimal Configuration**: Temperature = 0.7 (Score: 0.279)
- **Performance Improvement**: 298.4%
- **Sample Size**: 9
- **Statistical Test**: Not Significant (F=1.30, p=0.3389)

**Temperature Settings Performance**:
- 🥉 Temperature 0.3: -0.141 ± 0.248 (n=3)
- 🥇 Temperature 0.7: 0.279 ± 0.468 (n=3)
- 🥈 Temperature 0.9: 0.007 ± 0.180 (n=3)

### 🏗️ Linear Structure

- **Temperature Effect Size**: 0.4276
- **Optimal Configuration**: Temperature = 0.7 (Score: 0.172)
- **Performance Improvement**: 167.5%
- **Sample Size**: 9
- **Statistical Test**: Not Significant (F=1.17, p=0.3736)

**Temperature Settings Performance**:
- 🥉 Temperature 0.3: -0.255 ± 0.280 (n=3)
- 🥇 Temperature 0.7: 0.172 ± 0.542 (n=3)
- 🥈 Temperature 0.9: -0.220 ± 0.251 (n=3)

## 📚 Romantic Genre 详细分析

### 🏗️ Nonlinear Structure

- **Temperature Effect Size**: 0.2636
- **Optimal Configuration**: Temperature = 0.3 (Score: 0.411)
- **Performance Improvement**: 178.5%
- **Sample Size**: 9
- **Statistical Test**: Not Significant (F=0.97, p=0.4329)

**Temperature Settings Performance**:
- 🥇 Temperature 0.3: 0.411 ± 0.085 (n=3)
- 🥉 Temperature 0.7: 0.148 ± 0.161 (n=3)
- 🥈 Temperature 0.9: 0.169 ± 0.408 (n=3)

### 🏗️ Linear Structure

- **Temperature Effect Size**: 1.0246
- **Optimal Configuration**: Temperature = 0.9 (Score: 0.437)
- **Performance Improvement**: 174.3%
- **Sample Size**: 9
- **Statistical Test**: Statistically Significant (F=10.00, p=0.0123)

**Temperature Settings Performance**:
- 🥈 Temperature 0.3: 0.076 ± 0.178 (n=3)
- 🥉 Temperature 0.7: -0.588 ± 0.263 (n=3)
- 🥇 Temperature 0.9: 0.437 ± 0.377 (n=3)

## 🔍 Cross-Genre Comparison

- **Most Parameter-Sensitive Configuration**: romantic-linear (Effect Size: 1.0246)
- **Statistical Significance Rate**: 1/6 configurations show significant temperature effects

## 📊 Methodology
This analysis is based on 54 experiments with discrete parameter settings:
- **Temperature**: [0.3, 0.7, 0.9]
- **Structure**: ['nonlinear', 'linear']
- **Genre**: ['sciencefiction', 'horror', 'romantic']
- **Analysis Method**: ANOVA and effect size calculation for parameter sensitivity quantification
- **Comprehensive Score**: Normalized average of Semantic Continuity, Diversity, Novelty, and Emotional Consistency

## 🎯 Practical Recommendations

### Horror Genre
- **Recommended Configuration**: nonlinear@0.7
- **Expected Improvement**: 298.4%
- **Implementation Priority**: High

### Romantic Genre
- **Recommended Configuration**: nonlinear@0.3
- **Expected Improvement**: 178.5%
- **Implementation Priority**: Medium

### Sciencefiction Genre
- **Recommended Configuration**: linear@0.7
- **Expected Improvement**: 166.2%
- **Implementation Priority**: Medium
