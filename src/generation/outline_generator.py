from src.utils.utils import convert_json, generate_response

def generate_outline(topic="Little Red Riding Hood", style="Sci-fi rewrite", custom_instruction=None, 
                    generation_mode="traditional", user_description=None, file_content=None, performance_analyzer=None):
    """
    Function to generate story outline, supporting two modes:
    1. traditional: Generate based on topic and style (original mode)
    2. description_based: Generate based on user description and optional file content
    
    Args:
        topic: Story topic (used in traditional mode)
        style: Story style (used in traditional mode)
        custom_instruction: Custom instructions
        generation_mode: Generation mode, 'traditional' or 'description_based'
        user_description: User's description of the story (used in description_based mode)
        file_content: Content of uploaded file (optional)
    """
    
    if generation_mode == "traditional":
        # Original traditional mode
        base_prompt = f"""
You are a professional screenwriter. Create a story titled "{topic}" with a linear outline that focuses on CONCRETE EVENTS and ACTION-DRIVEN chapters.

CRITICAL REQUIREMENTS:
- Each chapter must contain SPECIFIC EVENTS, not just emotions or descriptions
- Focus on CONFLICTS, DECISIONS, and ACTIONS that drive the plot forward
- Include character interactions, dialogue, and character decisions
- Every chapter should have clear CAUSE and EFFECT
- Each character must have clear motivations for their actions

STORY STYLE: {style}

CHAPTER STRUCTURE REQUIREMENTS:
Each chapter must include:
- chapter_id: Chapter number (e.g. "Chapter 1")  
- title: Action-focused chapter title (avoid vague emotional titles)
- summary: 2-3 sentences describing WHAT HAPPENS (specific events, actions, conflicts, decisions, character motivations). Avoid pure emotional descriptions.

EXAMPLE of GOOD summary: "Character A discovers a hidden letter and confronts Character B about the secret. They argue over past betrayals, and Character B storms out after revealing their true motivation. Character A must decide whether to pursue or let them go."

EXAMPLE of BAD summary: "Character A feels confused and uncertain about their relationships. The atmosphere becomes tense as emotions run high and past memories surface."

Return only a JSON list with concrete, event-driven chapter outlines focusing on character actions and motivations.
"""
        
        # If user provided custom instructions, add them
        if custom_instruction:
            base_prompt += f"\nPlease pay special attention to the following style or content suggestions: {custom_instruction}"

        base_prompt += "\nOnly return standard JSON list, no need to return other redundant explanations."
    
    elif generation_mode == "description_based":
        # New description-based mode
        if not user_description:
            raise ValueError("description_based mode requires user_description parameter")
            
        base_prompt = f"""
You are a professional screenwriter and story creator. The user wants to create a story outline chapter list based on the following description.

User's story description:
{user_description}

Please generate a linear outline chapter list for this story based on the user description (no branching required).

Please return a standard JSON formatted list, each element represents a chapter, including:
- chapter_id: Chapter number (e.g. "Chapter 1")
- title: Chapter title
- summary: Brief introduction of the chapter content (1-2 sentences)

"""
        
        # If there is file content, determine processing method based on file content
        if file_content:
            if len(file_content.strip()) > 100:  # If file content is long, it may be an existing story
                base_prompt += f"""
The user also provided the following related content as reference:
{file_content[:2000]}...  # Truncate first 2000 characters to avoid being too long

Please judge the user's intention based on the user description and provided content:
- If it's continuation: Continue creating subsequent chapters based on existing content
- If it's rewriting: Modify existing content for style or plot transformation
- If it's inspiration: Create new stories inspired by existing content
- If it's other: Handle according to specific requirements described by user

"""
            else:  # If file content is short, it may be brief reference
                base_prompt += f"""
The user also provided the following reference information:
{file_content}

Please combine the user description and this reference information to create the story outline.
"""
        
        # If user provided custom instructions, add them
        if custom_instruction:
            base_prompt += f"\nPlease pay special attention to the following creation requirements: {custom_instruction}"

        base_prompt += "\n\nPlease create a story outline that meets the user's intentions. Only return standard JSON list format, no other explanations needed."
    
    else:
        raise ValueError("generation_mode must be 'traditional' or 'description_based'")

    msg = [{"role": "user", "content": base_prompt}]
    raw = generate_response(msg, performance_analyzer=performance_analyzer, stage_name="outline_generation")
    print(f"[{generation_mode} mode] LLM raw response:", raw[:200] + "..." if len(raw) > 200 else raw)
    return convert_json(raw)
