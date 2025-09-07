import os
import sys
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

try:
    from src.utils.utils import load_json, save_json
except ImportError:
    print("⚠️ 无法导入项目工具函数，使用简化版本")
    
    def load_json(file_path):
        """简化版load_json"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_json(data, version, filename):
        """简化版save_json"""
        # 尝试推断output目录
        possible_output_dirs = [
            os.path.join(project_root, "output"),
            os.path.join(project_root, "outputs"),
            os.path.join(project_root, "data", "output"),
            os.path.join(project_root, "results")
        ]
        
        output_dir = None
        for dir_path in possible_output_dirs:
            version_path = os.path.join(dir_path, version)
            if os.path.exists(version_path):
                output_dir = dir_path
                break
        
        if not output_dir:
            # 如果找不到，使用第一个作为默认
            output_dir = possible_output_dirs[0]
            os.makedirs(os.path.join(output_dir, version), exist_ok=True)
        
        file_path = os.path.join(output_dir, version, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class HREDCoherenceEvaluator:
    """
    基于HRED思想的语义连贯性评价器
    专注于原文句子的语义连贯性分析
    """
    
    def __init__(self, model_name="all-mpnet-base-v2"):
        """
        初始化向量模型
        
        Args:
            model_name: sentence-transformers模型名称
                      - "all-mpnet-base-v2": 推荐，性能最好
                      - "all-MiniLM-L6-v2": 更快，稍低精度
                      - "paraphrase-multilingual-mpnet-base-v2": 多语言
        """
        print(f"🔄 加载sentence-transformers模型: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f"✅ 模型加载完成")
    
    def extract_sentences_from_story(self, story_data):
        """
        从原文故事中提取所有句子
        
        Args:
            story_data: 故事数据，包含chapters的list
        
        Returns:
            List[str]: 原文句子列表
        """
        try:
            from src.utils.utils import split_plot_into_sentences
        except ImportError:
            # 简化版句子分割函数
            def split_plot_into_sentences(text):
                """简化版句子分割"""
                # 按句号、问号、感叹号分割
                import re
                sentences = re.split(r'[。！？.!?]+', text)
                return [s.strip() for s in sentences if s.strip()]
            
        all_sentences = []
        
        for chapter in story_data:
            plot = chapter.get('plot', '')
            if plot.strip():
                try:
                    sentences = split_plot_into_sentences(plot)
                except:
                    # 如果分割函数失败，使用简单分割
                    import re
                    sentences = re.split(r'[。！？.!?]+', plot)
                    sentences = [s.strip() for s in sentences if s.strip()]
                
                all_sentences.extend([s.strip() for s in sentences if s.strip()])
        
        return all_sentences
    
    def compute_embeddings(self, sentences):
        """
        计算句子的向量表示
        
        Args:
            sentences: 句子列表
        
        Returns:
            np.ndarray: 句子向量矩阵 (n_sentences, embedding_dim)
        """
        print(f"🧮 计算 {len(sentences)} 个句子的向量表示...")
        
        # 使用sentence-transformers计算嵌入
        embeddings = self.model.encode(sentences, convert_to_numpy=True)
        
        print(f"✅ 向量计算完成，维度: {embeddings.shape}")
        return embeddings
    
    def compute_adjacent_similarities(self, embeddings):
        """
        计算相邻句子之间的余弦相似度
        
        Args:
            embeddings: 句子向量矩阵
        
        Returns:
            List[float]: 相邻句子相似度列表
        """
        if len(embeddings) < 2:
            print("⚠️ 句子数量不足2个，无法计算相邻相似度")
            return []
        
        similarities = []
        
        for i in range(len(embeddings) - 1):
            # 计算第i个和第i+1个句子的余弦相似度
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            similarities.append(float(sim))
        
        return similarities
    
    def analyze_coherence_patterns(self, similarities, sentences):
        """
        分析连贯性模式
        
        Args:
            similarities: 相邻句子相似度列表
            sentences: 句子列表
        
        Returns:
            dict: 详细的连贯性分析结果
        """
        if not similarities:
            return {
                "error": "无法计算连贯性模式",
                "reason": "相似度列表为空"
            }
        
        similarities_array = np.array(similarities)
        
        # 基本统计
        stats = {
            "平均连贯性": float(np.mean(similarities_array)),
            "连贯性标准差": float(np.std(similarities_array)),
            "最高连贯性": float(np.max(similarities_array)),
            "最低连贯性": float(np.min(similarities_array)),
            "连贯性中位数": float(np.median(similarities_array))
        }
        
        # 识别连贯性断点（相似度显著下降的位置）
        threshold = np.mean(similarities_array) - np.std(similarities_array)
        low_coherence_points = []
        
        for i, sim in enumerate(similarities):
            if sim < threshold:
                low_coherence_points.append({
                    "位置": i + 1,
                    "句子对": f"{sentences[i][:30]}... → {sentences[i+1][:30]}...",
                    "相似度": round(sim, 3)
                })
        
        # 识别高连贯性段落
        high_threshold = np.mean(similarities_array) + 0.5 * np.std(similarities_array)
        high_coherence_segments = []
        
        current_segment = []
        for i, sim in enumerate(similarities):
            if sim > high_threshold:
                current_segment.append(i)
            else:
                if len(current_segment) >= 2:  # 至少3个连续句子
                    high_coherence_segments.append({
                        "起始句子": current_segment[0] + 1,
                        "结束句子": current_segment[-1] + 2,
                        "长度": len(current_segment) + 1,
                        "平均相似度": round(np.mean([similarities[j] for j in current_segment]), 3)
                    })
                current_segment = []
        
        # 检查最后一个段落
        if len(current_segment) >= 2:
            high_coherence_segments.append({
                "起始句子": current_segment[0] + 1,
                "结束句子": current_segment[-1] + 2,
                "长度": len(current_segment) + 1,
                "平均相似度": round(np.mean([similarities[j] for j in current_segment]), 3)
            })
        
        return {
            "基本统计": stats,
            "连贯性断点": low_coherence_points,
            "高连贯性段落": high_coherence_segments,
            "客观描述": self._describe_coherence_objectively(stats["平均连贯性"])
        }
    
    def _describe_coherence_objectively(self, avg_coherence):
        """
        客观描述连贯性，不给主观评级
        
        Args:
            avg_coherence: 平均连贯性分数
        
        Returns:
            dict: 客观描述
        """
        return {
            "分数": round(avg_coherence, 4),
            "范围": "0-1（1为完全相似）",
            "解释": "基于sentence-transformers模型计算的相邻句子语义相似度均值",
            "参考": "建议与其他文本对比，而非绝对评级"
        }
    
    def evaluate_story_coherence(self, story_data, include_details=True):
        """
        完整的故事连贯性评价
        
        Args:
            story_data: 原文故事数据
            include_details: 是否包含详细分析
        
        Returns:
            dict: 连贯性评价结果
        """
        print(f"\n🔍 开始HRED语义连贯性分析...")
        print(f"📊 使用模型: {self.model_name}")
        print(f"📋 分析方式: 原文句子连贯性")
        
        # Step 1: 提取原文句子
        sentences = self.extract_sentences_from_story(story_data)
        print(f"📝 提取到 {len(sentences)} 个有效句子")
        
        if len(sentences) < 2:
            return {
                "错误": "句子数量不足",
                "详情": f"需要至少2个句子，当前有{len(sentences)}个",
                "建议": "请确保输入包含足够的句子"
            }
        
        # Step 2: 计算向量表示
        embeddings = self.compute_embeddings(sentences)
        
        # Step 3: 计算相邻相似度
        similarities = self.compute_adjacent_similarities(embeddings)
        print(f"🔗 计算了 {len(similarities)} 个相邻句子对的相似度")
        
        # Step 4: 基本评价结果
        avg_coherence = np.mean(similarities) if similarities else 0
        
        result = {
            "HRED连贯性评价": {
                "模型名称": self.model_name,
                "分析方式": "原文句子连贯性",
                "句子总数": len(sentences),
                "相邻对数": len(similarities),
                "平均连贯性": round(avg_coherence, 4),
                "客观描述": self._describe_coherence_objectively(avg_coherence)
            }
        }
        
        # Step 5: 详细分析（可选）
        if include_details:
            print("🔍 进行详细连贯性模式分析...")
            detailed_analysis = self.analyze_coherence_patterns(similarities, sentences)
            result["详细分析"] = detailed_analysis
            
            # 添加逐对相似度（只显示前20对，避免过长）
            result["逐对相似度示例"] = []
            max_pairs = min(20, len(similarities))
            for i in range(max_pairs):
                result["逐对相似度示例"].append({
                    "句子对": f"句子{i+1} → 句子{i+2}",
                    "句子1": sentences[i][:50] + "..." if len(sentences[i]) > 50 else sentences[i],
                    "句子2": sentences[i+1][:50] + "..." if len(sentences[i+1]) > 50 else sentences[i+1],
                    "相似度": round(similarities[i], 4)
                })
            
            if len(similarities) > 20:
                result["逐对相似度示例"].append({
                    "说明": f"仅显示前20对，总共有{len(similarities)}对相邻句子"
                })
        
        print(f"✅ HRED连贯性分析完成")
        print(f"📊 平均连贯性: {avg_coherence:.4f} (0-1范围，越接近1越连贯)")
        
        return result


def evaluate_story_coherence_from_file(version, story_file="story_updated.json", model_name="all-mpnet-base-v2"):
    """
    从原文故事文件评价语义连贯性
    
    Args:
        version: 版本文件夹名
        story_file: 原文故事文件名
        model_name: sentence-transformers模型名
    
    Returns:
        dict: 连贯性评价结果
    """
    # 尝试导入output_dir，如果失败则使用默认路径
    try:
        from src.constant import output_dir
    except ImportError:
        # 推断output目录
        possible_dirs = ["output", "outputs", "data/output", "results"]
        output_dir = None
        for dir_name in possible_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if os.path.exists(dir_path):
                output_dir = dir_path
                break
        
        if not output_dir:
            output_dir = os.path.join(project_root, "output")
            print(f"⚠️ 使用默认输出目录: {output_dir}")
    
    print(f"\n🔍 开始原文语义连贯性评价：{version}")
    
    # 读取原文故事数据
    story_path = os.path.join(output_dir, version, story_file)
    if not os.path.exists(story_path):
        print(f"⚠️ 故事文件不存在：{story_path}")
        print(f"📁 查找的路径：{story_path}")
        return None
    
    story_data = load_json(story_path)
    
    # 创建评价器并分析
    evaluator = HREDCoherenceEvaluator(model_name=model_name)
    coherence_result = evaluator.evaluate_story_coherence(story_data, include_details=True)
    
    # 保存结果
    output_filename = f"hred_coherence_analysis_{model_name.replace('/', '_')}.json"
    save_json(coherence_result, version, output_filename)
    
    print(f"💾 结果已保存到: {output_filename}")
    
    return coherence_result


def compare_coherence_models(version, story_file="story_updated.json"):
    """
    使用多个模型比较连贯性评价结果
    
    Args:
        version: 版本文件夹名
        story_file: 原文故事文件名
    
    Returns:
        dict: 多模型比较结果
    """
    models_to_test = [
        "all-mpnet-base-v2",           # 推荐：性能最好
        "all-MiniLM-L6-v2",           # 快速：速度优先
        "paraphrase-mpnet-base-v2"     # 释义：理解相似表达
    ]
    
    print(f"\n🔍 多模型连贯性评价比较：{version}")
    
    # 尝试导入output_dir
    try:
        from src.constant import output_dir
    except ImportError:
        possible_dirs = ["output", "outputs", "data/output", "results"]
        output_dir = None
        for dir_name in possible_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if os.path.exists(dir_path):
                output_dir = dir_path
                break
        if not output_dir:
            output_dir = os.path.join(project_root, "output")
    
    story_path = os.path.join(output_dir, version, story_file)
    if not os.path.exists(story_path):
        print(f"⚠️ 故事文件不存在：{story_path}")
        return None
    
    story_data = load_json(story_path)
    
    # 预计算句子数量用于显示
    try:
        # 尝试使用项目的split函数
        try:
            from src.utils.utils import split_plot_into_sentences
        except ImportError:
            def split_plot_into_sentences(text):
                import re
                return re.split(r'[。！？.!?]+', text)
        
        sentence_count = len([s for ch in story_data for s in split_plot_into_sentences(ch.get('plot', '')) if s.strip()])
    except:
        sentence_count = "未知"
    
    comparison_results = {
        "版本": version,
        "分析方式": "原文句子连贯性",
        "句子总数": sentence_count,
        "模型比较": {}
    }
    
    for model_name in models_to_test:
        print(f"\n{'='*50}")
        print(f"🧮 测试模型: {model_name}")
        
        try:
            evaluator = HREDCoherenceEvaluator(model_name=model_name)
            result = evaluator.evaluate_story_coherence(story_data, include_details=False)
            
            comparison_results["模型比较"][model_name] = {
                "平均连贯性": result["HRED连贯性评价"]["平均连贯性"],
                "客观描述": result["HRED连贯性评价"]["客观描述"],
                "句子总数": result["HRED连贯性评价"]["句子总数"],
                "状态": "成功"
            }
            
        except Exception as e:
            print(f"⚠️ 模型 {model_name} 测试失败: {e}")
            comparison_results["模型比较"][model_name] = {
                "状态": "失败",
                "错误": str(e)
            }
    
    # 保存比较结果
    save_json(comparison_results, version, "hred_model_comparison.json")
    
    # 打印比较摘要
    print(f"\n{'='*60}")
    print("📊 原文句子连贯性模型比较摘要:")
    print("━" * 60)
    print(f"{'模型名称':<30} | {'连贯性':<8} | {'状态':<10}")
    print("━" * 60)
    
    for model_name, result in comparison_results["模型比较"].items():
        if result["状态"] == "成功":
            coherence = result["平均连贯性"]
            print(f"{model_name:<30} | {coherence:<8.4f} | {'成功':<10}")
        else:
            print(f"{model_name:<30} | {'--':<8} | {'失败':<10}")
    
    print("━" * 60)
    print("注：连贯性分数范围0-1，越接近1表示相邻句子语义越相似")
    print("━" * 60)
    
    return comparison_results


def add_coherence_to_story_evaluation(version, story_file="story_updated.json", model_name="all-mpnet-base-v2"):
    """
    将连贯性分析集成到现有的故事评价中
    
    Args:
        version: 版本文件夹名
        story_file: 原文故事文件名
        model_name: sentence-transformers模型名
    
    Returns:
        dict: 包含连贯性的完整评价结果
    """
    # 尝试导入output_dir
    try:
        from src.constant import output_dir
    except ImportError:
        possible_dirs = ["output", "outputs", "data/output", "results"]
        output_dir = None
        for dir_name in possible_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if os.path.exists(dir_path):
                output_dir = dir_path
                break
        if not output_dir:
            output_dir = os.path.join(project_root, "output")
    
    print(f"\n🔍 集成连贯性分析到故事评价：{version}")
    
    # 1. 检查是否有现有的结构分析结果
    existing_files = [
        "story_structure_analysis_statistical.json",
        "story_structure_analysis_default.json", 
        "story_structure_analysis_fixed.json"
    ]
    
    structure_result = None
    for filename in existing_files:
        file_path = os.path.join(output_dir, version, filename)
        if os.path.exists(file_path):
            structure_result = load_json(file_path)
            print(f"📂 找到现有结构分析: {filename}")
            break
    
    # 2. 进行连贯性分析
    coherence_result = evaluate_story_coherence_from_file(version, story_file, model_name)
    
    if not coherence_result:
        print("⚠️ 连贯性分析失败")
        return None
    
    # 3. 合并结果
    combined_result = {
        "版本": version,
        "评价时间": None,
        "连贯性分析": coherence_result
    }
    
    if structure_result:
        combined_result["结构分析"] = structure_result
        combined_result["评价模式"] = structure_result.get("评价模式", "未知")
    
    # 4. 生成综合摘要
    coherence_score = coherence_result["HRED连贯性评价"]["平均连贯性"]
    coherence_desc = coherence_result["HRED连贯性评价"]["客观描述"]
    
    summary = {
        "语义连贯性": {
            "分数": coherence_score,
            "描述": coherence_desc
        }
    }
    
    if structure_result and "结构分析" in structure_result:
        struct_analysis = structure_result["结构分析"]
        summary["结构完整性"] = {
            "Papalampidi": struct_analysis.get("Papalampidi结构分析", {}).get("转折点完整性", {}).get("TP覆盖率", "未知"),
            "Li功能": struct_analysis.get("Li功能分析", {}).get("功能多样性", "未知")
        }
    
    combined_result["综合摘要"] = summary
    
    # 5. 保存合并结果
    save_json(combined_result, version, "complete_story_evaluation.json")
    
    # 6. 打印综合摘要
    print(f"\n{'='*50}")
    print("📊 完整故事评价摘要:")
    print("━" * 50)
    print(f"语义连贯性: {coherence_score:.4f} (0-1范围)")
    if "结构完整性" in summary:
        print(f"结构完整性: TP覆盖率{summary['结构完整性']['Papalampidi']}, 功能多样性{summary['结构完整性']['Li功能']}种")
    print("━" * 50)
    print(f"💾 完整结果已保存到: complete_story_evaluation.json")
    
    return combined_result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HRED原文句子连贯性评价工具")
    parser.add_argument("--version", type=str, required=True, help="版本文件夹名")
    parser.add_argument("--story-file", type=str, default="story_updated.json", 
                       help="原文故事文件名")
    parser.add_argument("--model", type=str, default="all-mpnet-base-v2", 
                       help="sentence-transformers模型名")
    parser.add_argument("--compare-models", action="store_true", 
                       help="是否比较多个模型效果")
    parser.add_argument("--integrate", action="store_true",
                       help="是否集成到现有的故事评价中")
    
    args = parser.parse_args()
    
    if args.compare_models:
        compare_coherence_models(args.version, args.story_file)
    elif args.integrate:
        add_coherence_to_story_evaluation(args.version, args.story_file, args.model)
    else:
        evaluate_story_coherence_from_file(args.version, args.story_file, args.model)