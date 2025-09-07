import os
from src.utils.utils import generate_response, convert_json

def update_plot_from_dialogue(chapter_id, original_plot, dialogue, character_info, model="gpt-4.1"):
    """
    Automatically update the current chapter's plot based on dialogue and character information.
    Returns: dict, containing updated_plot / change_summary / changed
    """
    role_profiles = "\n".join([
        f"{char['name']} (Personality: {char['traits']}, Motivation: {char['motivation']})"
        for char in character_info
    ])
        
    # Defensive check to ensure dialogue is a list and compatible with different field names
    if isinstance(dialogue, str):
        dialogue_lines = dialogue  # If already a string, use directly
    elif isinstance(dialogue, list):
        dialogue_lines = "\n".join([
            f"{d['speaker']}: {d.get('dialogue', d.get('line', ''))}" for d in dialogue  # Priority 'dialogue', compatible with 'line'
        ])
    else:
        dialogue_lines = ""
    
    prompt = f"""
You are a narrative structure expert. Now there is a chapter plot summary and corresponding character dialogue. Please determine:

- Whether the current dialogue has deviated from the original plot (such as character motivation or stance changes)
- If so, please help me generate an **updated plot** that is consistent with the dialogue behavior
- Maintain character logic and natural connection with preceding and following plot

# Input information:

Chapter ID: {chapter_id}

Original plot:
{original_plot}

Character settings:
{role_profiles}

Chapter dialogue:
{dialogue_lines}

# Output format (strictly return JSON):
{{
  "updated_plot": "New plot (can be consistent with original plot if no changes needed)",
  "change_summary": "Explanation of this modification, e.g.: Carl betrays in dialogue, inconsistent with plot description, updated.",
  "changed": true or false
}}
""".strip()
    
    response = generate_response([{"role": "user", "content": prompt}], model=model)
    return convert_json(response)