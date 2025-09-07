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
    Build unified version naming format for subsequent log management and version differentiation.
    
    Example output:
    hongmao_sci_Structure_Role_T0.7_s42
    """
    name_parts = [
        topic.replace(" ", "").lower(),
        style.replace("rewrite", "").replace(" ", "").lower(),
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
