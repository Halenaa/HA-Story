from src.utils.utils import generate_response, convert_json_safe

def regenerate_dialogue_from_plot(chapter_id, plot, character_info, style_hint=None, model="gpt-4.1"):
    """
    Generate natural dialogue between characters based on plot and character settings.
    Returns: List[Dict]
    """
    role_profiles = "\n".join([
        f"{char['name']} (Personality: {char['traits']}, Motivation: {char['motivation']})"
        for char in character_info
    ])

    style_instruction = f"\nStyle hint: {style_hint}" if style_hint else ""

    prompt = f"""
You are an excellent novel screenplay writer.

Please generate natural dialogue that "advances the plot and reflects character personalities" based on the following plot:
- Output in json array format
- Include all characters taking turns to speak
- Each character speaks 1~2 sentences, pay attention to language style reflecting personality
- No need to restate the plot, only write dialogue

【Chapter ID】: {chapter_id}

【Plot Summary】:
{plot}

【Character Settings】:
{role_profiles}
{style_instruction}

【Output Format】 (strictly json):
[
  {{"speaker": "character_name", "line": "dialogue_content"}},
  ...
]
""".strip()

    response = generate_response([{"role": "user", "content": prompt}], model=model)
    return convert_json_safe(response)
