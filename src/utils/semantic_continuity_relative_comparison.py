"""
语义连续性相对比较系统
用于替代主观阈值的相对评价方法
"""

import numpy as np
from typing import List, Dict, Tuple, Optional


class SemanticContinuityRelativeComparison:
    """
    语义连续性相对比较系统
    
    注意：此系统仅基于相邻句子的语义相似度进行比较，
    不评价完整的故事连贯性、逻辑连贯性或因果关系。
    """
    
    def __init__(self):
        """初始化比较系统"""
        self.baseline_scores = []
        self.reference_data = {}
    
    def add_baseline_data(self, scores: List[float], dataset_name: str = "baseline"):
        """
        添加基准数据用于比较
        
        Args:
            scores: 语义连续性分数列表
            dataset_name: 数据集名称
        """
        if not scores:
            return
            
        self.baseline_scores.extend(scores)
        self.reference_data[dataset_name] = {
            "scores": scores,
            "mean": np.mean(scores),
            "std": np.std(scores),
            "percentiles": {
                "p25": np.percentile(scores, 25),
                "p50": np.percentile(scores, 50),  # 中位数
                "p75": np.percentile(scores, 75),
                "p90": np.percentile(scores, 90),
                "p95": np.percentile(scores, 95)
            }
        }
    
    def compare_to_baseline(self, score: float, dataset_name: str = "baseline") -> Dict:
        """
        与基准数据比较，返回相对位置
        
        Args:
            score: 待比较的语义连续性分数
            dataset_name: 参考数据集名称
        
        Returns:
            dict: 相对比较结果
        """
        if dataset_name not in self.reference_data:
            return {
                "error": f"Reference dataset '{dataset_name}' not found",
                "available_datasets": list(self.reference_data.keys())
            }
        
        ref_data = self.reference_data[dataset_name]
        ref_scores = ref_data["scores"]
        
        # 计算百分位排名
        percentile_rank = (np.sum(np.array(ref_scores) <= score) / len(ref_scores)) * 100
        
        # 计算超越的样本比例
        better_than_count = np.sum(np.array(ref_scores) < score)
        better_than_percentage = (better_than_count / len(ref_scores)) * 100
        
        # 确定相对位置描述
        if percentile_rank >= 95:
            position_desc = "极高水平"
            comparison_desc = f"高于{better_than_percentage:.1f}%的样本"
        elif percentile_rank >= 90:
            position_desc = "很高水平"
            comparison_desc = f"高于{better_than_percentage:.1f}%的样本"
        elif percentile_rank >= 75:
            position_desc = "较高水平"
            comparison_desc = f"高于{better_than_percentage:.1f}%的样本"
        elif percentile_rank >= 50:
            position_desc = "中等水平"
            comparison_desc = f"高于{better_than_percentage:.1f}%的样本"
        elif percentile_rank >= 25:
            position_desc = "较低水平"
            comparison_desc = f"高于{better_than_percentage:.1f}%的样本"
        else:
            position_desc = "很低水平"
            comparison_desc = f"高于{better_than_percentage:.1f}%的样本"
        
        return {
            "score": score,
            "dataset": dataset_name,
            "percentile_rank": round(percentile_rank, 1),
            "better_than_percentage": round(better_than_percentage, 1),
            "position_description": position_desc,
            "comparison_description": comparison_desc,
            "reference_statistics": {
                "sample_count": len(ref_scores),
                "mean": round(ref_data["mean"], 4),
                "std": round(ref_data["std"], 4),
                "median": round(ref_data["percentiles"]["p50"], 4)
            },
            "measurement_note": "仅基于相邻句子语义相似度，不代表完整连贯性"
        }
    
    def batch_compare(self, scores: List[float], dataset_name: str = "baseline") -> List[Dict]:
        """
        批量比较多个分数
        
        Args:
            scores: 语义连续性分数列表
            dataset_name: 参考数据集名称
        
        Returns:
            List[dict]: 批量比较结果
        """
        return [self.compare_to_baseline(score, dataset_name) for score in scores]
    
    def generate_distribution_summary(self, dataset_name: str = "baseline") -> Dict:
        """
        生成参考数据集的分布总结
        
        Args:
            dataset_name: 数据集名称
        
        Returns:
            dict: 分布总结
        """
        if dataset_name not in self.reference_data:
            return {"error": f"Dataset '{dataset_name}' not found"}
        
        ref_data = self.reference_data[dataset_name]
        
        return {
            "dataset": dataset_name,
            "sample_count": len(ref_data["scores"]),
            "distribution_summary": {
                "mean": round(ref_data["mean"], 4),
                "std": round(ref_data["std"], 4),
                "min": round(min(ref_data["scores"]), 4),
                "max": round(max(ref_data["scores"]), 4),
                "range": round(max(ref_data["scores"]) - min(ref_data["scores"]), 4)
            },
            "percentile_thresholds": {
                "25th percentile": round(ref_data["percentiles"]["p25"], 4),
                "50th percentile (median)": round(ref_data["percentiles"]["p50"], 4),
                "75th percentile": round(ref_data["percentiles"]["p75"], 4),
                "90th percentile": round(ref_data["percentiles"]["p90"], 4),
                "95th percentile": round(ref_data["percentiles"]["p95"], 4)
            },
            "interpretation_guide": {
                "95th+ percentile": "极高水平（前5%）",
                "90th-95th percentile": "很高水平（前10%）",
                "75th-90th percentile": "较高水平（前25%）",
                "50th-75th percentile": "中等偏上水平",
                "25th-50th percentile": "中等偏下水平",
                "25th- percentile": "较低水平（后25%）"
            },
            "measurement_limitation": "仅测量相邻句子语义相似度，不代表完整故事连贯性"
        }


def load_baseline_scores_from_csv(csv_file: str, score_column: str = "semantic_continuity") -> List[float]:
    """
    从CSV文件加载基准分数
    
    Args:
        csv_file: CSV文件路径
        score_column: 分数列名
    
    Returns:
        List[float]: 分数列表
    """
    try:
        import pandas as pd
        df = pd.read_csv(csv_file)
        
        if score_column not in df.columns:
            # 尝试查找可能的列名
            possible_columns = [col for col in df.columns if 'coherence' in col.lower() or 'continuity' in col.lower()]
            if possible_columns:
                print(f"Warning: Column '{score_column}' not found. Available columns: {possible_columns}")
                return []
            else:
                print(f"Warning: No semantic continuity related columns found in {csv_file}")
                return []
        
        scores = df[score_column].dropna().tolist()
        return [float(score) for score in scores if isinstance(score, (int, float))]
        
    except ImportError:
        print("Warning: pandas not available, cannot load CSV data")
        return []
    except Exception as e:
        print(f"Warning: Failed to load baseline scores from {csv_file}: {e}")
        return []


def create_comparison_system_from_existing_data(csv_files: List[str]) -> SemanticContinuityRelativeComparison:
    """
    从现有数据创建比较系统
    
    Args:
        csv_files: CSV文件路径列表
    
    Returns:
        SemanticContinuityRelativeComparison: 配置好的比较系统
    """
    comparison_system = SemanticContinuityRelativeComparison()
    
    for csv_file in csv_files:
        try:
            scores = load_baseline_scores_from_csv(csv_file)
            if scores:
                dataset_name = csv_file.split('/')[-1].replace('.csv', '')
                comparison_system.add_baseline_data(scores, dataset_name)
                print(f"Loaded {len(scores)} baseline scores from {dataset_name}")
        except Exception as e:
            print(f"Warning: Failed to load data from {csv_file}: {e}")
    
    return comparison_system


# 使用示例
if __name__ == "__main__":
    # 创建比较系统
    comparison_system = SemanticContinuityRelativeComparison()
    
    # 添加一些示例基准数据（实际使用时应从真实数据加载）
    example_baseline = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
    comparison_system.add_baseline_data(example_baseline, "example_baseline")
    
    # 测试分数
    test_score = 0.55
    result = comparison_system.compare_to_baseline(test_score, "example_baseline")
    
    print("相对比较结果:")
    print(f"分数: {result['score']}")
    print(f"百分位排名: {result['percentile_rank']}%")
    print(f"比较描述: {result['comparison_description']}")
    print(f"水平评价: {result['position_description']}")
    print(f"测量说明: {result['measurement_note']}")
