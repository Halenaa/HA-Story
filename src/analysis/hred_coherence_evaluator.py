import os
import sys
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

try:
    from src.utils.utils import load_json, save_json
except ImportError:
    print("WARNING: Unable to import project utility functions, using simplified version")
    
    def load_json(file_path):
        """Simplified version of load_json"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_json(data, version, filename):
        """Simplified version of save_json"""
        # Try to infer output directory
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
            # If not found, use the first one as default
            output_dir = possible_output_dirs[0]
            os.makedirs(os.path.join(output_dir, version), exist_ok=True)
        
        file_path = os.path.join(output_dir, version, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class HREDSemanticContinuityEvaluator:
    """
    Semantic continuity evaluator based on HRED concept
    Focuses on semantic continuity analysis of original story sentences
    
    注意：此评估器仅测量相邻句子间的语义相似度，不评价完整的故事连贯性。
    语义连续性 ≠ 逻辑连贯性或因果关系的完整性。
    """
    
    def __init__(self, model_name="all-mpnet-base-v2"):
        """
        Initialize vector model
        
        Args:
            model_name: sentence-transformers model name
                      - "all-mpnet-base-v2": Recommended, best performance
                      - "all-MiniLM-L6-v2": Faster, slightly lower accuracy
                      - "paraphrase-multilingual-mpnet-base-v2": Multilingual
        """
        print(f" Loading sentence-transformers model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f" Model loading completed")
    
    def extract_sentences_from_story(self, story_data):
        """
        Extract all sentences from original story
        
        Args:
            story_data: Story data containing list of chapters
        
        Returns:
            List[str]: List of original story sentences
        """
        try:
            from src.utils.utils import split_plot_into_sentences
        except ImportError:
            # Simplified sentence splitting function
            def split_plot_into_sentences(text):
                """Simplified sentence splitting"""
                # Split by periods, question marks, exclamation marks
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
                    # If splitting function fails, use simple splitting
                    import re
                    sentences = re.split(r'[。！？.!?]+', plot)
                    sentences = [s.strip() for s in sentences if s.strip()]
                
                all_sentences.extend([s.strip() for s in sentences if s.strip()])
        
        return all_sentences
    
    def compute_embeddings(self, sentences):
        """
        Compute vector representations of sentences
        
        Args:
            sentences: List of sentences
        
        Returns:
            np.ndarray: Sentence vector matrix (n_sentences, embedding_dim)
        """
        print(f" Computing vector representations for {len(sentences)} sentences...")
        
        # Use sentence-transformers to compute embeddings
        embeddings = self.model.encode(sentences, convert_to_numpy=True)
        
        print(f" Vector computation completed, dimension: {embeddings.shape}")
        return embeddings
    
    def compute_adjacent_similarities(self, embeddings):
        """
        Compute cosine similarity between adjacent sentences
        
        Args:
            embeddings: Sentence vector matrix
        
        Returns:
            List[float]: List of adjacent sentence similarities
        """
        if len(embeddings) < 2:
            print("WARNING: Insufficient sentences (less than 2), cannot compute adjacent similarities")
            return []
        
        similarities = []
        
        for i in range(len(embeddings) - 1):
            # Compute cosine similarity between i-th and (i+1)-th sentences
            sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            similarities.append(float(sim))
        
        return similarities
    
    def analyze_semantic_continuity_patterns(self, similarities, sentences):
        """
        Analyze semantic continuity patterns
        
        Args:
            similarities: List of adjacent sentence similarities
            sentences: List of sentences
        
        Returns:
            dict: Detailed semantic continuity analysis results
        """
        if not similarities:
            return {
                "error": "Cannot compute semantic continuity patterns",
                "reason": "Similarity list is empty"
            }
        
        similarities_array = np.array(similarities)
        
        # Basic statistics
        stats = {
            "average_semantic_continuity": float(np.mean(similarities_array)),
            "semantic_continuity_std": float(np.std(similarities_array)),
            "max_semantic_continuity": float(np.max(similarities_array)),
            "min_semantic_continuity": float(np.min(similarities_array)),
            "semantic_continuity_median": float(np.median(similarities_array))
        }
        
        # Identify semantic continuity breakpoints (positions where similarity drops significantly)
        threshold = np.mean(similarities_array) - np.std(similarities_array)
        low_continuity_points = []
        
        for i, sim in enumerate(similarities):
            if sim < threshold:
                low_continuity_points.append({
                    "position": i + 1,
                    "sentence_pair": f"{sentences[i][:30]}... → {sentences[i+1][:30]}...",
                    "similarity": round(sim, 3)
                })
        
        # Identify high semantic continuity segments
        high_threshold = np.mean(similarities_array) + 0.5 * np.std(similarities_array)
        high_continuity_segments = []
        
        current_segment = []
        for i, sim in enumerate(similarities):
            if sim > high_threshold:
                current_segment.append(i)
            else:
                if len(current_segment) >= 2:  # At least 3 consecutive sentences
                    high_continuity_segments.append({
                        "start_sentence": current_segment[0] + 1,
                        "end_sentence": current_segment[-1] + 2,
                        "length": len(current_segment) + 1,
                        "average_similarity": round(np.mean([similarities[j] for j in current_segment]), 3)
                    })
                current_segment = []
        
        # Check the last segment
        if len(current_segment) >= 2:
            high_continuity_segments.append({
                "start_sentence": current_segment[0] + 1,
                "end_sentence": current_segment[-1] + 2,
                "length": len(current_segment) + 1,
                "average_similarity": round(np.mean([similarities[j] for j in current_segment]), 3)
            })
        
        return {
            "basic_statistics": stats,
            "semantic_continuity_breakpoints": low_continuity_points,
            "high_continuity_segments": high_continuity_segments,
            "objective_description": self._describe_continuity_objectively(stats["average_semantic_continuity"])
        }
    
    def _describe_continuity_objectively(self, avg_continuity):
        """
        Objectively describe semantic continuity without subjective rating
        
        Args:
            avg_continuity: Average semantic continuity score
        
        Returns:
            dict: Objective description
        """
        return {
            "score": round(avg_continuity, 4),
            "range": "0-1 (1 means completely similar)",
            "measurement_scope": "Adjacent sentence semantic similarity only",
            "explanation": "Mean semantic similarity of adjacent sentences computed by sentence-transformers model",
            "limitation": "Does not measure logical coherence, causal relationships, or complete narrative coherence",
            "reference": "Recommend comparing with other texts rather than absolute rating"
        }
    
    def evaluate_story_semantic_continuity(self, story_data, include_details=True):
        """
        Complete story semantic continuity evaluation
        
        注意：此方法仅测量相邻句子间的语义相似度，不评价完整连贯性。
        
        Args:
            story_data: Original story data
            include_details: Whether to include detailed analysis
        
        Returns:
            dict: Semantic continuity evaluation results
        """
        print(f"\n Starting HRED semantic continuity analysis...")
        print(f" Using model: {self.model_name}")
        print(f" Analysis method: Original sentence semantic continuity")
        
        # Step 1: Extract original sentences
        sentences = self.extract_sentences_from_story(story_data)
        print(f" Extracted {len(sentences)} valid sentences")
        
        if len(sentences) < 2:
            return {
                "error": "Insufficient sentences",
                "details": f"Need at least 2 sentences, currently have {len(sentences)}",
                "suggestion": "Please ensure input contains enough sentences"
            }
        
        # Step 2: Compute vector representations
        embeddings = self.compute_embeddings(sentences)
        
        # Step 3: Compute adjacent similarities
        similarities = self.compute_adjacent_similarities(embeddings)
        print(f" Computed similarities for {len(similarities)} adjacent sentence pairs")
        
        # Step 4: Basic evaluation results
        avg_coherence = np.mean(similarities) if similarities else 0
        
        result = {
            "HRED_semantic_continuity_evaluation": {
                "model_name": self.model_name,
                "analysis_method": "Original sentence semantic continuity",
                "measurement_scope": "Adjacent sentence similarity only, not complete coherence",
                "total_sentences": len(sentences),
                "adjacent_pairs": len(similarities),
                "average_semantic_continuity": round(avg_coherence, 4),
                "objective_description": self._describe_continuity_objectively(avg_coherence)
            }
        }
        
        # Step 5: Detailed analysis (optional)
        if include_details:
            print(" Performing detailed semantic continuity pattern analysis...")
            detailed_analysis = self.analyze_semantic_continuity_patterns(similarities, sentences)
            result["detailed_analysis"] = detailed_analysis
            
            # Add pairwise similarities (only show first 20 pairs to avoid excessive length)
            result["pairwise_similarity_examples"] = []
            max_pairs = min(20, len(similarities))
            for i in range(max_pairs):
                result["pairwise_similarity_examples"].append({
                    "sentence_pair": f"Sentence {i+1} → Sentence {i+2}",
                    "sentence_1": sentences[i][:50] + "..." if len(sentences[i]) > 50 else sentences[i],
                    "sentence_2": sentences[i+1][:50] + "..." if len(sentences[i+1]) > 50 else sentences[i+1],
                    "similarity": round(similarities[i], 4)
                })
            
            if len(similarities) > 20:
                result["pairwise_similarity_examples"].append({
                    "note": f"Only showing first 20 pairs, total of {len(similarities)} adjacent sentence pairs"
                })
        
        print(f" HRED semantic continuity analysis completed")
        print(f" Average semantic continuity: {avg_coherence:.4f} (0-1 range, closer to 1 means more similar adjacent sentences)")
        
        return result


def evaluate_story_semantic_continuity_from_file(version, story_file="story_updated.json", model_name="all-mpnet-base-v2"):
    """
    Evaluate semantic continuity from original story file
    
    Args:
        version: Version folder name
        story_file: Original story file name
        model_name: sentence-transformers model name
    
    Returns:
        dict: Semantic continuity evaluation results
    """
    # Try to import output_dir, use default path if failed
    try:
        from src.constant import output_dir
    except ImportError:
        # Infer output directory
        possible_dirs = ["output", "outputs", "data/output", "results"]
        output_dir = None
        for dir_name in possible_dirs:
            dir_path = os.path.join(project_root, dir_name)
            if os.path.exists(dir_path):
                output_dir = dir_path
                break
        
        if not output_dir:
            output_dir = os.path.join(project_root, "output")
            print(f"WARNING: Using default output directory: {output_dir}")
    
    print(f"\n Starting original text semantic continuity evaluation: {version}")
    
    # Read original story data
    story_path = os.path.join(output_dir, version, story_file)
    if not os.path.exists(story_path):
        print(f"WARNING: Story file does not exist: {story_path}")
        print(f" Searched path: {story_path}")
        return None
    
    story_data = load_json(story_path)
    
    # Create evaluator and analyze
    evaluator = HREDSemanticContinuityEvaluator(model_name=model_name)
    continuity_result = evaluator.evaluate_story_semantic_continuity(story_data, include_details=True)
    
    # Save results
    output_filename = f"hred_semantic_continuity_analysis_{model_name.replace('/', '_')}.json"
    save_json(continuity_result, version, output_filename)
    
    print(f" Results saved to: {output_filename}")
    
    return continuity_result


def compare_semantic_continuity_models(version, story_file="story_updated.json"):
    """
    Compare semantic continuity evaluation results using multiple models
    
    Args:
        version: Version folder name
        story_file: Original story file name
    
    Returns:
        dict: Multi-model comparison results
    """
    models_to_test = [
        "all-mpnet-base-v2",           # Recommended: best performance
        "all-MiniLM-L6-v2",           # Fast: speed priority
        "paraphrase-mpnet-base-v2"     # Paraphrase: understand similar expressions
    ]
    
    print(f"\n Multi-model semantic continuity evaluation comparison: {version}")
    
    # Try to import output_dir
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
        print(f"WARNING: Story file does not exist: {story_path}")
        return None
    
    story_data = load_json(story_path)
    
    # Pre-compute sentence count for display
    try:
        # Try to use project's split function
        try:
            from src.utils.utils import split_plot_into_sentences
        except ImportError:
            def split_plot_into_sentences(text):
                import re
                return re.split(r'[。！？.!?]+', text)
        
        sentence_count = len([s for ch in story_data for s in split_plot_into_sentences(ch.get('plot', '')) if s.strip()])
    except:
        sentence_count = "unknown"
    
    comparison_results = {
        "version": version,
        "analysis_method": "Original sentence semantic continuity",
        "measurement_scope": "Adjacent sentence similarity only, not complete coherence",
        "total_sentences": sentence_count,
        "model_comparison": {}
    }
    
    for model_name in models_to_test:
        print(f"\n{'='*50}")
        print(f" Testing model: {model_name}")
        
        try:
            evaluator = HREDSemanticContinuityEvaluator(model_name=model_name)
            result = evaluator.evaluate_story_semantic_continuity(story_data, include_details=False)
            
            comparison_results["model_comparison"][model_name] = {
                "average_semantic_continuity": result["HRED_semantic_continuity_evaluation"]["average_semantic_continuity"],
                "objective_description": result["HRED_semantic_continuity_evaluation"]["objective_description"],
                "total_sentences": result["HRED_semantic_continuity_evaluation"]["total_sentences"],
                "status": "success"
            }
            
        except Exception as e:
            print(f"WARNING: Model {model_name} test failed: {e}")
            comparison_results["model_comparison"][model_name] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Save comparison results
    save_json(comparison_results, version, "hred_semantic_continuity_model_comparison.json")
    
    # Print comparison summary
    print(f"\n{'='*60}")
    print(" Original sentence semantic continuity model comparison summary:")
    print("━" * 60)
    print(f"{'Model Name':<30} | {'Continuity':<10} | {'Status':<10}")
    print("━" * 60)
    
    for model_name, result in comparison_results["model_comparison"].items():
        if result["status"] == "success":
            continuity = result["average_semantic_continuity"]
            print(f"{model_name:<30} | {continuity:<10.4f} | {'Success':<10}")
        else:
            print(f"{model_name:<30} | {'--':<10} | {'Failed':<10}")
    
    print("━" * 60)
    print("Note: Semantic continuity score range 0-1, closer to 1 means more similar adjacent sentences")
    print("Note: This measures adjacent sentence similarity only, NOT complete narrative coherence")
    print("━" * 60)
    
    return comparison_results


def add_semantic_continuity_to_story_evaluation(version, story_file="story_updated.json", model_name="all-mpnet-base-v2"):
    """
    Integrate semantic continuity analysis into existing story evaluation
    
    Args:
        version: Version folder name
        story_file: Original story file name
        model_name: sentence-transformers model name
    
    Returns:
        dict: Complete evaluation results including semantic continuity
    """
    # Try to import output_dir
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
    
    print(f"\n Integrating semantic continuity analysis into story evaluation: {version}")
    
    # 1. Check if there are existing structure analysis results
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
            print(f" Found existing structure analysis: {filename}")
            break
    
    # 2. Perform semantic continuity analysis
    continuity_result = evaluate_story_semantic_continuity_from_file(version, story_file, model_name)
    
    if not continuity_result:
        print("WARNING: Semantic continuity analysis failed")
        return None
    
    # 3. Merge results
    combined_result = {
        "version": version,
        "evaluation_time": None,
        "semantic_continuity_analysis": continuity_result
    }
    
    if structure_result:
        combined_result["structure_analysis"] = structure_result
        combined_result["evaluation_mode"] = structure_result.get("evaluation_mode", "unknown")
    
    # 4. Generate comprehensive summary
    continuity_score = continuity_result["HRED_semantic_continuity_evaluation"]["average_semantic_continuity"]
    continuity_desc = continuity_result["HRED_semantic_continuity_evaluation"]["objective_description"]
    
    summary = {
        "semantic_continuity": {
            "score": continuity_score,
            "description": continuity_desc,
            "measurement_scope": "Adjacent sentence similarity only, not complete coherence"
        }
    }
    
    if structure_result and "structure_analysis" in structure_result:
        struct_analysis = structure_result["structure_analysis"]
        summary["structural_integrity"] = {
            "Papalampidi": struct_analysis.get("Papalampidi_structure_analysis", {}).get("turning_point_integrity", {}).get("TP_coverage", "unknown"),
            "Li_function": struct_analysis.get("Li_function_analysis", {}).get("function_diversity", "unknown")
        }
    
    combined_result["comprehensive_summary"] = summary
    
    # 5. Save merged results
    save_json(combined_result, version, "complete_story_evaluation.json")
    
    # 6. Print comprehensive summary
    print(f"\n{'='*50}")
    print(" Complete story evaluation summary:")
    print("━" * 50)
    print(f"Semantic continuity: {continuity_score:.4f} (0-1 range, adjacent sentences only)")
    if "structural_integrity" in summary:
        print(f"Structural integrity: TP coverage {summary['structural_integrity']['Papalampidi']}, function diversity {summary['structural_integrity']['Li_function']} types")
    print("━" * 50)
    print(f" Complete results saved to: complete_story_evaluation.json")
    
    return combined_result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HRED original sentence semantic continuity evaluation tool")
    parser.add_argument("--version", type=str, required=True, help="Version folder name")
    parser.add_argument("--story-file", type=str, default="story_updated.json", 
                       help="Original story file name")
    parser.add_argument("--model", type=str, default="all-mpnet-base-v2", 
                       help="sentence-transformers model name")
    parser.add_argument("--compare-models", action="store_true", 
                       help="Whether to compare multiple model effects")
    parser.add_argument("--integrate", action="store_true",
                       help="Whether to integrate into existing story evaluation")
    
    args = parser.parse_args()
    
    if args.compare_models:
        compare_semantic_continuity_models(args.version, args.story_file)
    elif args.integrate:
        add_semantic_continuity_to_story_evaluation(args.version, args.story_file, args.model)
    else:
        evaluate_story_semantic_continuity_from_file(args.version, args.story_file, args.model)