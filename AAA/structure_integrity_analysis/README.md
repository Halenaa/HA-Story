# Structure Integrity Analysis - Hybrid Approach

## 📁 核心文件说明

### 🔧 **主要实现**
- **`structure_analysis.py`** - Hybrid结构完整性分析器核心实现
  - TP Coverage硬门槛机制 (≥1.0)
  - 3组件复杂度评分 (Chapter + Li + Event)
  - 理论baseline + 数据驱动微调 (±15%)

### 📊 **分析结果** (`structure_analysis_results/`)
- **`comprehensive_structure_report.json`** - 完整分析数据 (机器可读)
- **`structure_analysis_report.md`** - 详细分析报告 (人类可读)
- **`hybrid_weight_comparison.png`** - 权重演化可视化 ⭐
- **`structure_integrity_dashboard.png`** - 综合评估面板 ⭐
- **`*_analysis.png`** - 各维度专项分析图表

### 📋 **文档说明**
- **`hybrid_weight_implementation_summary.md`** - Hybrid方案实现总结 ⭐
- **`honest_weight_analysis_conclusion.md`** - 诚实的科学分析结论 ⭐

## 🚀 快速使用

```python
from structure_analysis import StructureIntegrityAnalyzer

# 初始化分析器
analyzer = StructureIntegrityAnalyzer('/path/to/metrics_master_clean.csv')

# 运行完整分析
results = analyzer.generate_comprehensive_report()

# 查看权重配置
print("Final Weights:", analyzer.selected_weights)
print("TP Gate Stats:", analyzer.tp_gate_stats)
```

## 🎯 核心特性

✅ **TP硬门槛**: 结构完整性必要条件 (≥1.0)  
✅ **3组件评分**: Chapter(49.6%) + Li(29.4%) + Event(21.0%)  
✅ **理论-经验结合**: 科学理论 + 数据驱动微调  
✅ **完整追踪**: 权重演化的透明过程  
✅ **可扩展性**: 支持多种配置和自定义权重

## 📈 分析结果亮点

- **TP Gate通过率**: 100% (54/54主样本，另有3个baseline对照)
- **章节结构优异**: 96.3%在最优范围(5-8章)
- **情节多样性丰富**: 平均8.6分，59.3%高多样性
- **事件密度平衡**: 7.3事件/千词，相关性良好

---

*精简后的核心文件，专注于Hybrid方案的科学实现和分析结果*
