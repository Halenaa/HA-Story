# 阶段2：参数效应分析报告
## Parameter Effects Analysis Report

### 分析目标
检验参数组合（Structure, Temperature, Genre）如何影响各维度表现

### 分析方法
- 三因素方差分析 (Three-way ANOVA)
- Structure (2水平) × Temperature (3水平) × Genre (3水平)
- Bonferroni多重比较校正
- 效应量计算 (η²)

### 主要发现
#### 显著效应 (p < 0.05):
- **avg_semantic_continuity**: C(genre) (F=66.24, p=0.0000, η²=0.756, 大效应)
- **diversity_score_seed**: C(genre) (F=31.61, p=0.0000, η²=0.539, 大效应)
- **pseudo_ppl**: C(genre) (F=48.01, p=0.0000, η²=0.656, 大效应)
- **one_minus_self_bleu**: C(genre) (F=26.99, p=0.0000, η²=0.453, 大效应)
- **roberta_avg_score**: C(genre) (F=111.60, p=0.0000, η²=0.806, 大效应)

#### C(structure)
无显著影响

#### C(temperature)
无显著影响

#### C(genre)
显著影响的维度:
- avg_semantic_continuity: η²=0.756 (大)
- diversity_score_seed: η²=0.539 (大)
- pseudo_ppl: η²=0.656 (大)
- one_minus_self_bleu: η²=0.453 (大)
- roberta_avg_score: η²=0.806 (大)

#### C(structure):C(temperature)
无显著影响

#### C(structure):C(genre)
无显著影响

#### C(temperature):C(genre)
无显著影响

#### C(structure):C(temperature):C(genre)
无显著影响
