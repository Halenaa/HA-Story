import json
from src.utils.utils import generate_response,convert_json

def expand_story_v1(chapters, characters, custom_instruction=None, performance_analyzer=None):
    import time
    character_json = json.dumps(characters, ensure_ascii=False, indent=2)
    story = []

    for ch in chapters:
#         msg_content = f"""
# Generate specific scenes, select character names and detailed descriptions based on the following content:
# Chapter number: {ch["chapter_id"]}
# Title: {ch["title"]}
# Character settings: {character_json}
# """
# Check if there are narrative instructions
        narrative_role = ch.get("narrative_role", None)
        narrative_instruction = ch.get("narrative_instruction", None)
        
        msg_content = f"""
Generate specific scenes, select character names and detailed descriptions based on the following content:
Chapter number: {ch["chapter_id"]}
Title: {ch["title"]}
Character settings: {character_json}
"""
        
        # If there are narrative instructions, add to prompt
        if narrative_role and narrative_instruction:
            msg_content += f"""
【Narrative Guidance】
Narrative role: {narrative_role}
Specific guidance: {narrative_instruction}

Please strictly organize content according to narrative guidance to ensure corresponding narrative techniques and style are reflected.
"""

        if custom_instruction:
            msg_content += f"\nSpecial Requirements: {custom_instruction}"

        msg_content += """

CORE REQUIREMENTS:
- Each scene must contain at least 2-3 specific actions
- Avoid pure emotional descriptions, focus on concrete character behaviors
- Every character appearance must have clear motivation and actions

SCENE DESCRIPTION REQUIREMENTS:
- Specify concrete environmental details (weather, location, time)
- Include sensory details (sounds, smells, textures)
- Each scene must have clear objectives and results
- Avoid abstract emotional landscape descriptions

CHARACTER REQUIREMENTS:
- Each character must have clear motivation for their actions
- Characters must take specific actions based on their motivations
- Character speech must fit their identity (animal thinking patterns)
- Show character decisions through concrete actions

DIALOGUE REQUIREMENTS:
- Character speech must fit their identity (animal thinking patterns)
- Dialogue must advance the plot, not just chat
- Show character conflicts and decisions through dialogue

MANDATORY ELEMENTS:
- At least 2-3 action verbs describing specific behaviors
- Concrete environmental details and sensory descriptions
- Character interactions or conflicts
- Clear scene objectives and outcomes
- Character motivations driving their actions

#OUTPUT FORMAT:
{
    "scene": "Specific time, location, and environmental details (include sensory descriptions)",
    "characters": ["Character name 1", "Character name 2"],
    "plot": "A paragraph focusing on SPECIFIC ACTIONS and EVENTS. Must include 2-3 clear actions, concrete environmental details, character interactions, and character motivations driving their behavior. Avoid pure emotional or psychological descriptions."
}
Do not add comments, explanations or other redundant content, only return JSON. Please ensure the returned result is valid JSON (can be correctly parsed by json.loads), and do not use unclosed double quotes in strings.
Note: Please strictly return a JSON object (starting with {), do not return JSON arrays or sentence list structures.
"""

        msg = [{"role": "user", "content": msg_content}]
        response = generate_response(msg, performance_analyzer=performance_analyzer, stage_name="story_expansion")

        print(f"Chapter {ch['chapter_id']} LLM response fragment:", response[:150].replace("\n", "\\n"))

        result = convert_json(response)
        print(f"Raw LLM response content:\n{response}")
        
        # If not dictionary or missing fields, report error and stop
        if not isinstance(result, dict):
            print(f"Chapter {ch['chapter_id']} parsing failed (not dict)")
            raise ValueError(f"Chapter {ch['chapter_id']} returned content format error!")

        if "plot" not in result:
            print(f"Chapter {ch['chapter_id']} missing 'plot' field")
            raise ValueError(f"Chapter {ch['chapter_id']} missing plot field, LLM may not output according to format")

        story.append(result)

        # Optional: Prevent rate limit
        time.sleep(1)

    return story
