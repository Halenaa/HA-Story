import json
import os
from src.utils.utils import generate_response, convert_json
from src.constant import output_dir

# Legacy commented code removed - outdated implementation

def analyze_narrative_structure(reordered_chapters, original_chapters, topic="Unknown", style="Unknown", performance_analyzer=None):
    """
    Improved version: Analyze narrative structure of reordered chapters, add narrative guidance for each chapter
    
    Args:
        reordered_chapters: Output result from chapter_reorder.py
        original_chapters: Original linear chapters
        topic: Story topic
        style: Story style
    
    Returns:
        analyzed_chapters: Chapter list containing narrative analysis
    """
    
    chapter_analysis = []
    for new_pos, ch in enumerate(reordered_chapters):
        original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
                           if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
        # Calculate position change
        position_change = new_pos - original_pos if original_pos >= 0 else 0
        
        # Time relationship analysis
        if position_change > 0:
            time_relation = "Time forward"
            narrative_hint = "Sequential development, can be directly connected"
        elif position_change < 0:
            time_relation = "Time backward" 
            narrative_hint = "Needs flashback/interpolation handling"
        else:
            time_relation = "Position unchanged"
            narrative_hint = "Maintain original rhythm"
        
        # Character relationship context analysis
        if new_pos == 0:
            character_context = "First reader contact, need to establish character recognition"
        elif original_pos == 0 and new_pos > 0:
            character_context = "Original opening chapter, now needs background supplement"
        elif abs(position_change) > 2:
            character_context = "Large position change, needs careful handling of character relationships"
        else:
            character_context = "Normal connection, maintain character relationship continuity"
            
        chapter_analysis.append({
            "Chapter ID": ch["chapter_id"],
            "Title": ch["title"], 
            "Summary": next((orig["summary"] for orig in original_chapters 
                         if orig["chapter_id"] == ch["chapter_id"]), ""),
            "New position": new_pos + 1,
            "Original position": original_pos + 1 if original_pos >= 0 else "Unknown",
            "Position change": position_change,
            "Time relationship": time_relation,
            "Narrative hint": narrative_hint,
            "Character relationship context": character_context,
            "Position span": abs(position_change)
        })
    
    info_text = json.dumps(chapter_analysis, ensure_ascii=False, indent=2)
    
    prompt = f"""You are a professional narrative structure expert. Please design precise narrative strategies for the following non-linear novel chapter arrangement.

【Story Background】
Topic: {topic}
Style: {style}

【Detailed Chapter Timeline Analysis】
{info_text}

【Key Requirements】
1. Unified narrative perspective: The entire text must use the same narrative perspective, no arbitrary switching
2. Timeline logic: For "time backward" chapters, must clearly use flashback or interpolation techniques
3. Character relationship consistency: Ensure character familiarity matches the story's internal timeline
4. Natural transitions: Chapter transitions should be smooth, avoid abruptness

【Special Notes】
- When "position change" is negative, this is time backward, requiring special handling
- When "character relationship context" shows first contact, characters cannot appear already familiar
- Avoid using different narrative persons in different chapters (first person/third person mixing)

【Output Format】
Return JSON array, each chapter contains the following fields:
- chapter_id: Chapter number
- narrative_role: Narrative role (3-6 words)
- narrative_instruction: Detailed guidance (must include specific perspective type, tense handling, character relationship handling)
- transition_hint: Specific transition method (how to naturally transition from previous chapter to this chapter)
- timeline_method: Timeline handling (sequential/flashback/interpolation/parallel narrative)
- pov_requirement: Perspective requirement (must be unified: third person omniscient/third person limited/first person)
- character_consistency_note: Character relationship notes

Please ensure all chapters' pov_requirement fields are completely consistent. Only return JSON array, no other content."""
    
    try:
        response = generate_response([{"role": "user", "content": prompt}], performance_analyzer=performance_analyzer, stage_name="chapter_reorder")
        analysis_result = convert_json(response)
        
        if not isinstance(analysis_result, list):
            print("LLM analysis format error, using basic mode")
            return add_basic_analysis(reordered_chapters, original_chapters)
        
        # Validate result completeness
        chapter_ids = [ch["chapter_id"] for ch in reordered_chapters]
        analysis_ids = [item.get("chapter_id") for item in analysis_result]
        
        if set(chapter_ids) != set(analysis_ids):
            print("LLM analysis incomplete, using basic mode")
            return add_basic_analysis(reordered_chapters, original_chapters)
        
        print("LLM narrative analysis successful")
        return merge_analysis_with_chapters(reordered_chapters, analysis_result)
        
    except Exception as e:
        print(f"LLM analysis failed: {e}, using basic mode")
        return add_basic_analysis(reordered_chapters, original_chapters)

# def add_basic_analysis(reordered_chapters, original_chapters):
#     """Basic narrative analysis (fallback solution)"""
#     analyzed_chapters = []
    
#     for idx, ch in enumerate(reordered_chapters):
#         original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
#                            if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
#         # Simple logical judgment
#         if idx == 0:  # First position
#             if original_pos > len(original_chapters) // 2:
#                 role = "Opening suspense"
#                 instruction = "Open with later plot to create suspense, no explanation of causes and consequences"
#             else:
#                 role = "Normal opening"
#                 instruction = "Open according to original logic, lay groundwork for subsequent development"
#         elif original_pos < idx:  # Timeline backward
#             role = "Flashback narrative"
#             instruction = "Use flashback form for narration, add transition language like 'let us go back to...'" 
#         else:  # Timeline forward
#             role = "Sequential development"
#             instruction = "Connect to previous text, advance story in chronological order"
        
#         analyzed_ch = dict(ch)  # Copy original information
#         analyzed_ch.update({
#             "narrative_role": role,
#             "narrative_instruction": instruction,
#             "transition_hint": "Standard transition"
#         })
        
#         analyzed_chapters.append(analyzed_ch)
    
#     return analyzed_chapters

def add_basic_analysis(reordered_chapters, original_chapters):
    """Improved version of basic narrative analysis (fallback solution)"""
    analyzed_chapters = []
    
    for idx, ch in enumerate(reordered_chapters):
        original_pos = next((i for i, orig_ch in enumerate(original_chapters) 
                           if orig_ch["chapter_id"] == ch["chapter_id"]), -1)
        
        # Simple logical judgment
        if idx == 0:
            if original_pos > len(original_chapters) // 2:
                role = "Suspense opening"
                instruction = "Third person limited perspective, open with later plot to create suspense, no explanation of causes and consequences"
                timeline_method = "Jump opening"
            else:
                role = "Normal opening"
                instruction = "Third person limited perspective, open according to original logic, lay groundwork for subsequent development"
                timeline_method = "Sequential"
        elif original_pos < idx:
            role = "Flashback narrative"
            instruction = "Third person limited perspective, use flashback form for narration, add transition language like 'let us go back to...'"
            timeline_method = "Flashback"
        else:
            role = "Sequential development"
            instruction = "Third person limited perspective, connect to previous text, advance story in chronological order"
            timeline_method = "Sequential"
        
        analyzed_ch = dict(ch)  # Copy original information
        analyzed_ch.update({
            "narrative_role": role,
            "narrative_instruction": instruction,
            "transition_hint": "Standard transition",
            "timeline_method": timeline_method,
            "pov_requirement": "Third person limited",  # Force unified perspective
            "character_consistency_note": "Maintain character relationship logic"
        })
        
        analyzed_chapters.append(analyzed_ch)
    
    return analyzed_chapters

def merge_analysis_with_chapters(reordered_chapters, analysis_result):
    """Merge LLM analysis results with chapter information"""
    analyzed_chapters = []
    
    for ch in reordered_chapters:
        # Find corresponding analysis
        analysis = next((item for item in analysis_result 
                        if item["chapter_id"] == ch["chapter_id"]), {})
        
        analyzed_ch = dict(ch)  # Copy original information
        analyzed_ch.update({
            "narrative_role": analysis.get("narrative_role", "Standard narrative"),
            "narrative_instruction": analysis.get("narrative_instruction", "Expand in conventional way"),
            "transition_hint": analysis.get("transition_hint", "Standard transition")
        })
        
        analyzed_chapters.append(analyzed_ch)
    
    return analyzed_chapters

def enhance_summaries_with_narrative(analyzed_chapters):
    """
    Enhance summary field based on narrative analysis
    """
    enhanced_chapters = []
    
    for idx, ch in enumerate(analyzed_chapters):
        original_summary = ch.get("summary", "No summary")
        narrative_role = ch.get("narrative_role", "Standard narrative")
        narrative_instruction = ch.get("narrative_instruction", "")
        
        # Generate enhanced summary
        enhanced_summary = f"【{narrative_role}】{original_summary}. {narrative_instruction}"
        
        enhanced_ch = dict(ch)
        enhanced_ch["narrative_summary"] = enhanced_summary
        
        enhanced_chapters.append(enhanced_ch)
    
    return enhanced_chapters

if __name__ == "__main__":
    # Independent test module
    print("Testing narrative analysis module")
    
    # Simulate output from chapter_reorder.py
    original_chapters = [
        {"chapter_id": "Chapter 1", "title": "Red Hood Journey", "summary": "Robot Little Red Hood receives mission"},
        {"chapter_id": "Chapter 2", "title": "Data Forest", "summary": "Enter virtual forest environment"},
        {"chapter_id": "Chapter 3", "title": "AI Wolf Appears", "summary": "Encounter malicious AI program"},
        {"chapter_id": "Chapter 4", "title": "Final Battle", "summary": "Decisive battle with AI wolf"}
    ]
    
    # Simulate reordering result
    reordered_chapters = [
        {"chapter_id": "Chapter 4", "title": "Final Battle", "new_order": 1},
        {"chapter_id": "Chapter 1", "title": "Red Hood Journey", "new_order": 2},
        {"chapter_id": "Chapter 2", "title": "Data Forest", "new_order": 3},
        {"chapter_id": "Chapter 3", "title": "AI Wolf Appears", "new_order": 4}
    ]
    
    # Test analysis
    print("Original chapters:", [ch["chapter_id"] for ch in original_chapters])
    print("Reordered sequence:", [ch["chapter_id"] for ch in reordered_chapters])
    print()
    
    # Execute analysis (will call basic mode here, because there's no real LLM)
    analyzed = analyze_narrative_structure(
        reordered_chapters, original_chapters, 
        topic="Little Red Hood", style="Sci-fi rewrite"
    )
    
    print("Analysis results:")
    for ch in analyzed:
        print(f"  {ch['chapter_id']}: {ch['narrative_role']}")
        print(f"    Guidance: {ch['narrative_instruction']}")
    
    # Test summary enhancement
    enhanced = enhance_summaries_with_narrative(analyzed)
    print("\nEnhanced summary:")
    for ch in enhanced:
        print(f"  {ch['chapter_id']}: {ch['narrative_summary']}")