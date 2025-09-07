import os
import re
import json
import ast
import time
from openai import OpenAI
import anthropic
from src.constant import output_dir
from dotenv import load_dotenv
load_dotenv()



client = OpenAI(api_key=os.getenv("OPENAI_KEY"), base_url=os.getenv("OPENAI_API_BASE"),
)




def generate_response(msg, model="gpt-4.1", temperature=0.7, performance_analyzer=None, stage_name=None):     
    """
    Generate LLM response and record API cost and token consumption
    
    Args:
        msg: Message list
        model: Model name
        temperature: Temperature parameter
        performance_analyzer: Performance analyzer instance (optional)
        stage_name: Current stage name (for API cost statistics)
    """
    # Estimate input token count
    input_text = ""
    for message in msg:
        input_text += message.get("content", "")
    
    # Call API and record response time
    api_start_time = time.time()
    response = client.chat.completions.create(
        model=model,                                 
        messages=msg,
        temperature=temperature,
        max_tokens=9000  # Fix: Add sufficient token limit to prevent response truncation
    )
    api_response_time = time.time() - api_start_time
    
    # Extract response content
    response_content = response.choices[0].message.content
    
    # Record API usage statistics
    if hasattr(response, 'usage') and response.usage:
        # Use actual token count returned by API
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
    else:
        # If no usage information, estimate token count
        from src.utils.api_cost_calculator import APICostCalculator
        input_tokens = APICostCalculator.estimate_tokens_from_text(input_text)
        output_tokens = APICostCalculator.estimate_tokens_from_text(response_content)
        total_tokens = input_tokens + output_tokens
    
    # Calculate API cost
    from src.utils.api_cost_calculator import APICostCalculator
    cost = APICostCalculator.calculate_cost(model, input_tokens, output_tokens)
    
    # Record to performance analyzer
    if performance_analyzer and stage_name:
        performance_analyzer.add_api_cost(
            stage_name=stage_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            api_call_type="completion",
            response_time=api_response_time
        )
    
    # Print API call statistics (for debugging)
    print(f"API call - Model: {model}, Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost:.6f}")
    
    return response_content

def convert_dialogue_dict_to_list(dialogue_dict):
    """
    Convert dict format dialogue ({character_name: [dialogue_strings]}) to list[dict] format
    Modified: Use "dialogue" field to maintain consistency with dialogue_inserter.py core module
    """
    result = []
    for speaker, lines in dialogue_dict.items():
        for line in lines:
            # Remove "character_name: ..." prefix (if any)
            if line.startswith(speaker + ":"):
                line = line[len(speaker)+1:].strip()
            result.append({"speaker": speaker, "dialogue": line})  # Use "dialogue" field
    return result

def extract_behavior_llm(dialogue_block, model="gpt-4.1", confirm=False):
    from src.utils.utils import generate_response

    # Organize dialogue into string (whether list or dict)
    if isinstance(dialogue_block, dict):
        dialogue_items = []
        for speaker, lines in dialogue_block.items():
            for line in lines:
                dialogue_items.append(f"{speaker}: {line}")
    else:
        # Fix: Compatible with two field names: 'dialogue' and 'line'
        dialogue_items = []
        for d in dialogue_block:
            speaker = d.get('speaker', '')
            # Key fix: Try 'dialogue' first, then try 'line'
            content = d.get('dialogue', d.get('line', ''))
            dialogue_items.append(f"{speaker}: {content}")

    dialogue_text = "\n".join(dialogue_items)

    # Prompt: Let LLM return dict[str: list[str]] format
    prompt = f"""
You are a narrative behavior analyzer. Please read the following multi-turn character dialogues, extract each character's current key behavioral states (such as: angry, betrayed, calm, villain, withdrawn, etc.), and output in JSON format.

Output format:
{{
  "Character A": ["State 1", "State 2"],
  "Character B": ["State 3"]
}}

Note: States should match each character's language style and behavioral hints, no explanations needed, only return JSON.

Dialogue as follows:
{dialogue_text}
"""

    response = generate_response([{"role": "user", "content": prompt}], model=model)

    # Structured parsing
    from src.utils.utils import convert_json
    result = convert_json(response)

    # If parsing fails, return empty dictionary rather than crash the program
    if not isinstance(result, dict):
        print(f"extract_behavior_llm parsing failed, returning empty result")
        return {}

    # Manual confirmation mechanism
    if confirm:
        print("\n System extracted character behaviors:")
        for role, states in result.items():
            print(f"- {role}: {', '.join(states)}")
        fix = input("Do you want to manually modify any character states? (y/n): ").strip().lower()
        if fix == 'y':
            for role in result:
                manual = input(f"Please re-enter states for {role} (separated by commas, leave empty to skip): ").strip()
                if manual:
                    result[role] = [s.strip() for s in manual.split(",")]

    return result

def fix_plot_illegal_quotes(content):
    """
    Fix illegal unescaped quotes in plot string, e.g.: "plot": "...grandma"...
    Will replace "character" → 『character』 in plot
    """
    pattern = r'"plot"\s*:\s*"(.*?)"'
    matches = re.findall(pattern, content, re.DOTALL)
    if matches:
        plot_text = matches[0]
        fixed_plot = plot_text.replace('"', '\u201c')  # Replace illegal quotes with Chinese quotes
        content = re.sub(pattern, f'"plot": "{fixed_plot}"', content, count=1)
    return content

def convert_json(content):
    print(f"Original content: {content}...")  # Print first 100 characters for debugging
    content = content.replace("，", ",").replace("。", ".")

    try:
        # Remove Markdown wrapping
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        # Fix concatenated JSON objects {..}{..} to [{..},{..}]
        if re.search(r"}\s*{", content):
            content = "[" + re.sub(r"}\s*{", "},{", content) + "]"
        
        # Added: Fix concatenated JSON arrays [...][...]
        if re.search(r"\]\s*\[", content):
            # Find the first complete JSON array
            # Use smarter method: calculate bracket balance
            bracket_count = 0
            end_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i
                            break
            
            if end_pos > 0:
                # Only take the first complete JSON array
                content = content[:end_pos + 1]
        
        # Extract first JSON structure (improved version)
        content = content.strip()
        if content.startswith("["):
            # For arrays, use bracket balance method
            bracket_count = 0
            end_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '[':
                        bracket_count += 1
                    elif char == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_pos = i
                            break
            
            if end_pos > 0:
                json_text = content[:end_pos + 1]
                return json.loads(json_text)
        
        elif content.startswith("{"):
            # For objects, similar processing
            brace_count = 0
            end_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(content):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i
                            break
            
            if end_pos > 0:
                json_text = content[:end_pos + 1]
                return json.loads(json_text)

        # Try direct parsing
        print(f"Attempting direct JSON parsing: {content}...")
        return json.loads(content)

    except Exception as e:
        print(f"convert_json error: {e}")
        print(f"Content fragment (first 200 chars): {content[:200]}")
            
        # Determine return type based on content format
        content_stripped = content.strip()
        if content_stripped.startswith("{"):
            return {}  # If object format, return empty dict
        elif content_stripped.startswith("["):
            return []  # If array format, return empty list
        else:
            # Default case, infer from context
            return {}  # Most story expansion scenarios expect dict
       
def save_json(obj, folder,file_name):
    folder_path = os.path.join(output_dir,folder)
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def save_json_absolute(obj, full_path):
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def extract_plot_list(chapter_json_list):
    return [ch.get("plot", "") for ch in chapter_json_list]

def split_plot_into_sentences(plot_text, min_length=2):
    """
    Best practice version: combines advantages of various methods
    """
    if not plot_text: 
        return []
    
    text = plot_text.strip()
    
    # Replace ellipsis
    text = text.replace("...", "〈ELLIPSIS〉")
    text = text.replace("……", "〈ELLIPSIS_CN〉")
    
    # Use regular expression to find all sentences
    # Greedy match until punctuation marks
    pattern = r'.+?[.。!！?？;；]+'
    
    # Find all matching sentences
    sentences = re.findall(pattern, text)
    
    # Check if there's remaining text (without punctuation ending)
    last_pos = 0
    for match in re.finditer(pattern, text):
        last_pos = match.end()
    
    if last_pos < len(text):
        remaining = text[last_pos:].strip()
        if remaining:
            sentences.append(remaining)
    
    # Process results
    result = []
    for sentence in sentences:
        # Restore ellipsis
        sentence = sentence.replace("〈ELLIPSIS〉", "...")
        sentence = sentence.replace("〈ELLIPSIS_CN〉", "……")
        sentence = sentence.strip()
        
        # Only filter truly too short ones (like single characters)
        if sentence and len(sentence) >= min_length:
            result.append(sentence)
    
    return result

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_md(text, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def convert_json_safe(content):
    """
    JSON parser compatible with true/false/null (for LLM returns)
    """
    import json
    content = content.replace("，", ",").replace("。", ".")
    # Fix common spelling errors
    content = content.replace('"peaker"', '"speaker"')

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        return json.loads(content)
    except Exception as e:
        print("convert_json_safe error:", e)
        return {}
