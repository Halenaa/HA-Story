from src.utils.utils import convert_json, generate_response

def generate_outline(topic="小红帽", style="科幻改写", custom_instruction=None, 
                    generation_mode="traditional", user_description=None, file_content=None, performance_analyzer=None):
    """
    生成故事大纲的函数，支持两种模式：
    1. traditional: 基于题材和风格生成（原有模式）
    2. description_based: 基于用户描述和可选文件内容生成
    
    Args:
        topic: 故事题材（traditional模式使用）
        style: 故事风格（traditional模式使用）
        custom_instruction: 自定义指令
        generation_mode: 生成模式，'traditional' 或 'description_based'
        user_description: 用户对故事的描述（description_based模式使用）
        file_content: 上传文件的内容（可选）
    """
    
    if generation_mode == "traditional":
        # 原有的传统模式
        base_prompt = f"""
你是一个编剧，现在要创作一个名为《{topic}》的故事，请你为这个故事生成一个线性的大纲章节列表（不需要分支）。

请根据以下要求返回一个标准 JSON 格式的列表，每个元素表示一章，包括：
- chapter_id：章节编号（如 "Chapter 1"）
- title：章节标题
- summary：该章内容的简要介绍（1~2句话）

故事风格为：{style}
不要加入冒号、解释或其他多余格式，只返回 JSON 格式的内容。
"""
        
        # 如果用户提供了自定义指令，就加入进来
        if custom_instruction:
            base_prompt += f"\n请特别注意以下风格或内容提示：{custom_instruction}"

        base_prompt += "\n只返回标准 JSON 列表，不需要返回其他多余解释。"
    
    elif generation_mode == "description_based":
        # 新的基于描述的模式
        if not user_description:
            raise ValueError("description_based 模式需要提供 user_description 参数")
            
        base_prompt = f"""
你是一个专业的编剧和故事创作者。用户想要基于以下描述创作一个故事的大纲章节列表。

用户的故事描述：
{user_description}

请根据用户描述，为这个故事生成一个线性的大纲章节列表（不需要分支）。

请返回一个标准 JSON 格式的列表，每个元素表示一章，包括：
- chapter_id：章节编号（如 "Chapter 1"）
- title：章节标题
- summary：该章内容的简要介绍（1~2句话）

"""
        
        # 如果有文件内容，根据文件内容判断处理方式
        if file_content:
            if len(file_content.strip()) > 100:  # 如果文件内容较长，可能是现有故事
                base_prompt += f"""
用户还提供了以下相关内容作为参考：
{file_content[:2000]}...  # 截取前2000字符避免过长

请根据用户描述和提供的内容，判断用户的意图：
- 如果是续写：基于现有内容继续创作后续章节
- 如果是改写：对现有内容进行风格或情节改造
- 如果是联想：受现有内容启发创作新故事
- 如果是其他：按用户描述的具体要求处理

"""
            else:  # 如果文件内容较短，可能是简要参考
                base_prompt += f"""
用户还提供了以下参考信息：
{file_content}

请结合用户描述和这些参考信息来创作故事大纲。
"""
        
        # 如果用户提供了自定义指令，加入进来
        if custom_instruction:
            base_prompt += f"\n请特别注意以下创作要求：{custom_instruction}"

        base_prompt += "\n\n请创作出符合用户意图的故事大纲。只返回标准 JSON 列表格式，不需要其他解释。"
    
    else:
        raise ValueError("generation_mode 必须为 'traditional' 或 'description_based'")

    msg = [{"role": "user", "content": base_prompt}]
    raw = generate_response(msg, performance_analyzer=performance_analyzer, stage_name="outline_generation")
    print(f"[{generation_mode} mode] LLM 原始响应:", raw[:200] + "..." if len(raw) > 200 else raw)
    return convert_json(raw)
