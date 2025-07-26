# version_namer.py

def build_version_name(
    topic: str,
    style: str,
    prompt_type: str = None,
    prompt_style: str = None,
    temperature: float = None,
    seed: int = None,
    order_mode: str = None
) -> str:
    """
    构建统一版本命名格式，便于后续日志管理和版本区分。
    
    示例输出：
    hongmao_sci_Structure_Role_T0.7_s42
    """
    name_parts = [
        topic.replace(" ", "").lower(),
        style.replace("改写", "").replace(" ", "").lower(),
    ]

    if order_mode:
        name_parts.append(order_mode.lower())

    if prompt_type:
        name_parts.append(prompt_type)
    if prompt_style:
        name_parts.append(prompt_style)
    if temperature is not None:
        name_parts.append(f"T{temperature}")
    if seed is not None:
        name_parts.append(f"s{seed}")

    return "_".join(name_parts)
