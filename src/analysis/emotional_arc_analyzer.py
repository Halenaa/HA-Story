"""
Dual-method emotional arc analyzer (updated version)
Primary method: RoBERTa (modern deep learning model)
Validation method: LabMT (classic method, consistent with Reagan's original work)
"""

import re
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import requests
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from scipy.stats import pearsonr, spearmanr

class DualMethodEmotionalAnalyzer:
    """
    Dual-method emotional analyzer (updated version)
    Primary: RoBERTa analysis
    Validation: LabMT analysis
    """
    
    def __init__(self, labmt_version='v1'):
        """
        Initialize dual-method analyzer
        
        Args:
            labmt_version: 'v1' (2011, consistent with Reagan) or 'v2' (2020, more modern)
        """
        print("Initializing dual-method emotional analyzer (RoBERTa version)...")
        
        self.labmt_version = labmt_version
        print(f"Selected LabMT version: {labmt_version} ({'consistent with Reagan original' if labmt_version == 'v1' else 'more modern version'})")
        
        # Initialize RoBERTa (primary method)
        self._init_roberta()
        
        # Initialize LabMT (validation method)
        self._init_labmt()
        
        print("Dual-method analyzer ready")
    
    def _init_roberta(self):
        """Initialize RoBERTa analyzer"""
        try:
            from transformers import pipeline
            
            print("Loading RoBERTa model...")
            # Using tested RoBERTa model
            self.roberta_classifier = pipeline(
                "sentiment-analysis", 
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                truncation=True,
                max_length=512
            )
            print("RoBERTa analyzer initialization successful (primary method)")
            
        except ImportError:
            print("RoBERTa initialization failed, please install transformers")
            raise ImportError("Please run: pip install transformers torch")
        except Exception as e:
            print(f"RoBERTa model loading failed: {e}")
            # Try alternative model
            try:
                print("Trying alternative model...")
                self.roberta_classifier = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    truncation=True,
                    max_length=512
                )
                print("Alternative DistilBERT model loaded successfully")
            except:
                raise ImportError("All models failed to load, please check network connection")
    
    def _init_labmt(self):
        """Initialize LabMT dictionary"""
        # Try to load local LabMT file
        possible_paths = [
            '/Users/haha/Story/data/Hedonometer.csv',
            './labMT.csv',
            './data/labMT.csv',
            '../data/labMT.csv'
        ]
        
        labmt_found = False
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found local LabMT dictionary file: {path}")
                self._load_labmt_local(path)
                labmt_found = True
                break
        
        if not labmt_found:
            print("Downloading LabMT dictionary...")


    
    def _load_labmt_local(self, file_path='/Users/haha/Story/data/Hedonometer.csv'):
        """Load local LabMT file - fixed version"""
        import pandas as pd
        
        try:
            print(f"Reading LabMT file: {file_path}")
            
            # Read using comma separator
            df = pd.read_csv(file_path, sep=',')
            print(f"Data shape: {df.shape}")
            
            # Use correct column names
            word_col = 'Word'
            happiness_col = 'Happiness Score'
            
            # Build dictionary
            self.labmt_dict = {}
            valid_count = 0
            
            for _, row in df.iterrows():
                try:
                    word = str(row[word_col]).lower().strip()
                    score = float(row[happiness_col])
                    
                    # Filter neutral words
                    if len(word) > 1 and 1.0 <= score <= 9.0 and not (4.0 <= score <= 6.0):
                        self.labmt_dict[word] = score
                        valid_count += 1
                except:
                    continue
            
            print(f"LabMT dictionary loaded successfully, valid words: {valid_count}")
            
        except Exception as e:
            print(f"File reading failed: {e}")
            self._init_simple_labmt()
        

    def analyze_with_roberta_correct(self, text: str) -> float:
        """RoBERTa emotional analysis (primary method) - fixed version"""
        if not text or not text.strip():
            return 0.0
        
        try:
            if len(text) <= 500:
                result = self.roberta_classifier(text)[0]
                return self.convert_roberta_score(result)
            else:
                # Sentence-by-sentence analysis (fixed version)
                sentences = [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 10]
                scores = []
                
                for sentence in sentences[:15]:  # Analyze first 15 sentences
                    try:
                        result = self.roberta_classifier(sentence)[0]
                        score = self.convert_roberta_score(result)
                        scores.append(score)
                    except:
                        continue
                
                return sum(scores) / len(scores) if scores else 0.0
                
        except Exception as e:
            print(f"RoBERTa analysis error: {e}")
            return 0.0
    
    def convert_roberta_score(self, result):
        """Correctly convert RoBERTa scores"""
        label = result['label'].lower()
        score = result['score']
        
        if label == 'positive':
            return score  # Positive value from 0 to 1
        elif label == 'negative':
            return -score  # Negative value from 0 to -1
        elif label == 'neutral':
            return 0.0  # Neutral is 0
        else:
            print(f"Unknown label: {label}")
            return 0.0
    
    def analyze_labmt(self, text: str) -> float:
        """LabMT emotional analysis (validation method)"""
        if not text or not text.strip():
            return 0.0  # Changed to 0.0 to be consistent with RoBERTa
        
        # Text preprocessing
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        if not words:
            return 0.0
        
        # Calculate sentiment score
        total_score = 0
        valid_words = 0
        
        for word in words:
            if word in self.labmt_dict:
                total_score += self.labmt_dict[word]
                valid_words += 1
        
        if valid_words == 0:
            return 0.0
        
        avg_score = total_score / valid_words
        
        # Convert to -1 to 1 range (for comparison with RoBERTa)
        # LabMT: 1-9 -> convert to -1 to 1
        normalized_score = (avg_score - 5.0) / 4.0  # (score-5)/4
        return max(-1, min(1, normalized_score))
    
    def parse_story(self, md_content: str) -> List[Dict]:
        """Parse story file"""
        chapters = []
        
        # Split by chapters
        chapter_pattern = r'# Chapter (\d+)[：:]([^\n]+)'
        splits = re.split(chapter_pattern, md_content)
        
        if len(splits) < 3:
            print("Standard chapter format not detected, trying to split by #")
            parts = md_content.split('\n# ')
            for i, part in enumerate(parts[1:], 1):
                lines = part.split('\n')
                title = lines[0].strip()
                content = '\n'.join(lines[1:]).strip()
                if content:
                    chapters.append({
                        'chapter_num': i,
                        'title': title,
                        'content': content
                    })
        else:
            for i in range(1, len(splits), 3):
                if i + 2 < len(splits):
                    chapter_num = int(splits[i])
                    title = splits[i + 1].strip()
                    content = splits[i + 2].strip()
                    
                    # Clean content
                    content = re.sub(r'-{20,}', '', content)
                    content = content.strip()
                    
                    chapters.append({
                        'chapter_num': chapter_num,
                        'title': title,
                        'content': content
                    })
        
        print(f"Parsed {len(chapters)} chapters")
        return chapters
    
    def analyze_story_dual_method(self, chapters: List[Dict]) -> Dict:
        """Dual-method analysis of story emotional arc (RoBERTa version)"""
        if not chapters:
            return {"error": "No chapter data"}
        
        print("Starting dual-method emotional analysis (RoBERTa + LabMT)...")
        
        # 1. Perform dual-method analysis on each chapter
        chapter_analysis = []
        roberta_scores = []
        labmt_scores = []
        
        for chapter in chapters:
            print(f"  Analyzing chapter {chapter['chapter_num']}: {chapter['title'][:30]}...")
            
            # RoBERTa analysis (primary)
            roberta_score = self.analyze_with_roberta_correct(chapter['content'])
            
            # LabMT analysis (validation)
            labmt_score = self.analyze_labmt(chapter['content'])
            
            chapter_analysis.append({
                'chapter_num': chapter['chapter_num'],
                'title': chapter['title'],
                'roberta_score': round(roberta_score, 4),
                'labmt_score': round(labmt_score, 4),
                'content_length': len(chapter['content'])
            })
            
            roberta_scores.append(roberta_score)
            labmt_scores.append(labmt_score)
        
        # 2. Calculate correlation between the two methods
        correlation_analysis = self._analyze_correlation(roberta_scores, labmt_scores)
        
        # 3. Reagan six-type classification (based on primary method RoBERTa)
        reagan_classification = self._classify_reagan_arc(roberta_scores, method="RoBERTa")
        
        # 4. Validation classification (based on LabMT)
        labmt_classification = self._classify_reagan_arc(labmt_scores, method="LabMT")
        
        # 5. Generate comparative analysis
        comparison_analysis = self._generate_comparison_analysis(
            roberta_scores, labmt_scores, reagan_classification, labmt_classification
        )
        
        # 6. Assemble results (standard format)
        result = {
            'metadata': {
                'total_chapters': len(chapters),
                'primary_method': 'RoBERTa',
                'validation_method': f'LabMT-en-{getattr(self, "actual_labmt_version", self.labmt_version)}',
                'analysis_timestamp': datetime.now().isoformat()
            },
            'chapter_analysis': chapter_analysis,
            'primary_analysis': {
                'method': 'RoBERTa',
                'scores': roberta_scores,
                'reagan_classification': reagan_classification
            },
            'validation_analysis': {
                'method': 'LabMT', 
                'scores': labmt_scores,
                'reagan_classification': labmt_classification
            },
            'correlation_analysis': correlation_analysis,
            'comparison_analysis': comparison_analysis,
            'final_conclusion': self._generate_final_conclusion(correlation_analysis, comparison_analysis)
        }
        
        print("Dual-method analysis completed!")
        print(f"Correlation coefficient: {correlation_analysis['pearson_correlation']['r']:.3f}")
        print(f"RoBERTa classification: {reagan_classification['best_match']} (confidence: {reagan_classification['confidence']:.3f})")
        print(f"LabMT classification: {labmt_classification['best_match']} (confidence: {labmt_classification['confidence']:.3f})")
        
        return result
    
    # Retain original other methods unchanged
    def _analyze_correlation(self, scores1: List[float], scores2: List[float]) -> Dict:
        """Analyze correlation between two methods"""
        if len(scores1) != len(scores2) or len(scores1) < 2:
            return {"error": "Insufficient data"}
        
        # Calculate correlation coefficients
        pearson_r, pearson_p = pearsonr(scores1, scores2)
        spearman_r, spearman_p = spearmanr(scores1, scores2)
        
        # Calculate directional consistency
        direction_agreement = 0
        for i in range(1, len(scores1)):
            roberta_direction = np.sign(scores1[i] - scores1[i-1])
            labmt_direction = np.sign(scores2[i] - scores2[i-1])
            if roberta_direction == labmt_direction:
                direction_agreement += 1
        
        direction_consistency = direction_agreement / max(1, len(scores1) - 1)
        
        return {
            'pearson_correlation': {
                'r': round(pearson_r, 4),
                'p_value': round(pearson_p, 4),
                'significance': 'Significant' if pearson_p < 0.05 else 'Not Significant'
            },
            'spearman_correlation': {
                'r': round(spearman_r, 4),
                'p_value': round(spearman_p, 4)
            },
            'direction_consistency': round(direction_consistency, 4),
            'consistency_level': 'High' if abs(pearson_r) > 0.7 else 'Medium' if abs(pearson_r) > 0.5 else 'Low',
            'interpretation': f"RoBERTa and LabMT correlation coefficient is {pearson_r:.3f}, belongs to {'strong correlation' if abs(pearson_r) > 0.7 else 'moderate correlation' if abs(pearson_r) > 0.5 else 'weak correlation'}"
        }
    
    def _classify_reagan_arc(self, scores: List[float], method: str) -> Dict:
        """Reagan six arc types classification"""
        if len(scores) < 3:
            return {
                'best_match': 'Unknown',
                'confidence': 0.0,
                'method': method,
                'all_similarities': {}
            }
        
        # Generate standard arc patterns
        standard_arcs = self._generate_standard_arcs(len(scores))
        
        # Calculate similarity
        similarities = {}
        for arc_name, arc_pattern in standard_arcs.items():
            similarity = self._cosine_similarity(scores, arc_pattern)
            similarities[arc_name] = round(max(0, similarity), 4)
        
        best_match = max(similarities, key=similarities.get)
        confidence = similarities[best_match]
        
        return {
            'method': method,
            'best_match': best_match,
            'confidence': confidence,
            'all_similarities': similarities,
            'reagan_category': self._get_reagan_category(best_match)
        }
    
    def _generate_standard_arcs(self, length: int) -> Dict[str, List[float]]:
        """Generate standard arc patterns"""
        x = np.linspace(0, 1, length)
        
        return {
            'Rags to riches': [0.8 * (t - 0.2) for t in x],
            'Tragedy': [0.8 * (0.8 - t) for t in x],
            'Man in a hole': [0.5 * np.sin(np.pi * t - np.pi/2) for t in x],
            'Icarus': [0.5 * np.sin(np.pi * t + np.pi/2) for t in x],
            'Cinderella': [0.5 * np.sin(2 * np.pi * t - np.pi/2) for t in x],
            'Oedipus': [0.5 * np.sin(2 * np.pi * t + np.pi/2) for t in x]
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        if len(vec1) != len(vec2):
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return max(0, dot_product / (norm1 * norm2))
    
    def _get_reagan_category(self, arc_type: str) -> str:
        """Get Reagan original text classification codes"""
        categories = {
            "Rags to riches": "RR",
            "Tragedy": "TR", 
            "Man in a hole": "MH",
            "Icarus": "IC",
            "Cinderella": "CN",
            "Oedipus": "OE"
        }
        return categories.get(arc_type, "UK")
    
    def _generate_comparison_analysis(self, roberta_scores, labmt_scores, 
                                    roberta_class, labmt_class) -> Dict:
        """Generate comparative analysis"""
        
        # Analyze disagreement points
        disagreement_points = []
        for i, (r_score, l_score) in enumerate(zip(roberta_scores, labmt_scores)):
            diff = abs(r_score - l_score)
            if diff > 0.3:  # Disagreement threshold
                disagreement_points.append({
                    'chapter': i + 1,
                    'roberta_score': r_score,
                    'labmt_score': l_score,
                    'difference': round(diff, 4)
                })
        
        # Method advantages analysis
        method_advantages = {
            'RoBERTa': {
                'strengths': [
                    "Deep learning model with better contextual understanding",
                    "Suitable for modern text and dialogue",
                    "High sensitivity to sci-fi and technical texts"
                ],
                'classification': roberta_class['best_match'],
                'confidence': roberta_class['confidence']
            },
            'LabMT': {
                'strengths': [
                    "Fully consistent with Reagan's original method",
                    "Based on large-scale human annotation",
                    "Suitable for traditional literary analysis"
                ],
                'classification': labmt_class['best_match'],
                'confidence': labmt_class['confidence']
            }
        }
        
        # Consistency assessment
        consistency_assessment = {
            'classification_agreement': roberta_class['best_match'] == labmt_class['best_match'],
            'major_disagreements': len(disagreement_points),
            'recommendation': self._generate_recommendation(roberta_class, labmt_class, disagreement_points)
        }
        
        return {
            'disagreement_points': disagreement_points,
            'method_advantages': method_advantages,
            'consistency_assessment': consistency_assessment
        }
    
    def _generate_recommendation(self, roberta_class, labmt_class, disagreements) -> str:
        """Generate usage recommendations"""
        if roberta_class['best_match'] == labmt_class['best_match']:
            return f"Both methods identify as {roberta_class['best_match']}, results are highly consistent, recommend using RoBERTa as the primary analysis result"
        elif len(disagreements) <= 2:
            return f"Classification differs slightly but overall consistent, recommend using RoBERTa as primary and LabMT for validation, demonstrating the advantages of modern deep learning models"
        else:
            return f"Two methods differ significantly, recommend detailed analysis of difference causes, may need more in-depth text feature analysis"
    
    def _generate_final_conclusion(self, correlation_analysis, comparison_analysis) -> str:
        """Generate final conclusion"""
        pearson_r = correlation_analysis['pearson_correlation']['r']
        consistency_level = correlation_analysis['consistency_level']
        
        conclusion = f"""
RoBERTa + LabMT Dual-Method Analysis Conclusion:

Correlation Analysis:
- Pearson correlation coefficient: r = {pearson_r:.3f} ({consistency_level})
- Consistency level: {correlation_analysis['interpretation']}

Classification Results:
- RoBERTa (primary): {comparison_analysis['method_advantages']['RoBERTa']['classification']}
- LabMT (validation): {comparison_analysis['method_advantages']['LabMT']['classification']}

Methodological Notes:
This study uses RoBERTa as the primary analysis method (modern deep learning model),
with LabMT for cross-validation (consistent with Reagan et al. 2016).
The correlation coefficient is {pearson_r:.3f}, showing {consistency_level.lower()} consistency between the two methods.

Recommendation: Use RoBERTa results as primary, with LabMT as academic benchmark validation.
        """.strip()
        
        return conclusion
    
    def save_results(self, result: Dict, output_dir: str = "./output/") -> str:
        """Save analysis results"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"roberta_labmt_analysis_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Analysis results saved to: {filepath}")
        return filepath


def analyze_story_dual_method(file_path: str, output_dir: str = "./output/") -> Dict:
    """
    RoBERTa + LabMT dual-method story analysis complete workflow
    
    Args:
        file_path: Story file path
        output_dir: Output directory
    
    Returns:
        Complete analysis results in standard format
    """
    print("Starting RoBERTa + LabMT dual-method emotional arc analysis...")
    print(f"Primary method: RoBERTa (deep learning)")
    print(f"Validation method: LabMT (consistent with Reagan's original)")
    
    # 1. Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Successfully read file: {file_path}")
    except Exception as e:
        return {"error": f"File reading failed: {e}"}
    
    # 2. Initialize analyzer
    analyzer = DualMethodEmotionalAnalyzer()
    
    # 3. Parse story
    chapters = analyzer.parse_story(content)
    if not chapters:
        return {"error": "Unable to parse chapter content"}
    
    # 4. Dual-method analysis
    result = analyzer.analyze_story_dual_method(chapters)
    if "error" in result:
        return result
    
    # 5. Save results
    try:
        json_path = analyzer.save_results(result, output_dir)
        result['output_files'] = {'analysis_json': json_path}
    except Exception as e:
        print(f"Failed to save results: {e}")
        result['output_files'] = {}
    
    # 6. Print result summary
    print("\n" + "="*60)
    print("RoBERTa + LabMT dual-method analysis completed!")
    print("="*60)
    
    # Print main results
    primary = result['primary_analysis']
    validation = result['validation_analysis']
    correlation = result['correlation_analysis']
    
    print(f"Primary analysis (RoBERTa): {primary['reagan_classification']['best_match']}")
    print(f"Validation analysis (LabMT): {validation['reagan_classification']['best_match']}")
    print(f"Correlation coefficient: r={correlation['pearson_correlation']['r']:.3f} ({correlation['consistency_level']})")
    
    print(f"\nChapter score comparison:")
    for ch in result['chapter_analysis']:
        print(f"  Chapter {ch['chapter_num']}: RoBERTa={ch['roberta_score']:.3f}, LabMT={ch['labmt_score']:.3f}")
    
    print(f"\n{result['final_conclusion']}")
    
    return result


# Direct run example
if __name__ == "__main__":
    print("RoBERTa + LabMT dual-method emotional arc analyzer")
    print("Primary method: RoBERTa (modern deep learning model)")
    print("Validation method: LabMT (consistent with Reagan's original)")
    
    # Check if there are story files
    possible_files = [
        '/Users/haha/Story/data/output/小红帽_科幻_linear_T0.7_s1/enhance.md',  # User's specific file
        'enhanced_story_dialogue_updated.md',
        'data/enhanced_story_dialogue_updated.md',
        './output/小红帽_科幻_linear_T0.7_s1/enhance.md',
        './小红帽_科幻_linear_T0.7_s1/enhance.md'
    ]
    
    story_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            story_file = file_path
            break
    
    if story_file:
        print(f"\nFound story file: {story_file}")
        print("Starting analysis...")
        
        try:
            result = analyze_story_dual_method(story_file, "./output/")
            
            # Save result variable for later use
            print(f"\nResult variable generated, can be used for visualization:")
            print(f"   - Type: {type(result)}")
            print(f"   - Chapters: {result['metadata']['total_chapters']}")
            print(f"   - Correlation: {result['correlation_analysis']['pearson_correlation']['r']:.3f}")
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            print("\nPossible solutions:")
            print("1. Check if story file format is correct")
            print("2. Install missing dependencies: pip install transformers torch nltk pandas requests scipy")
            print("3. Check network connection (required for model download)")
    else:
        print("\nStory file not found")
        print("Please ensure file is in one of the following locations:")
        for fp in possible_files:
            print(f"   - {fp}")
        print("\nOr manually specify file path:")
        print("   from emotional_arc_analyzer import analyze_story_dual_method")
        print("   result = analyze_story_dual_method('your_file_path.md')")