from pathlib import Path

# 当前文件所在目录
current_dir = Path(__file__).parent.parent

# 根目录（在不同系统上的表现不同）
root_dir = Path("/")

# 构造一个子目录路径
output_dir = current_dir / "data" / "output"


