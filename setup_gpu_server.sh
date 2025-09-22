#!/bin/bash

# GPU服务器环境配置脚本
# 用于配置流畅度分析所需的环境

echo "🚀 开始配置GPU服务器环境..."

# 检查当前目录
echo "📍 当前工作目录: $(pwd)"

# 进入Story项目目录
cd /root/Story || {
    echo "❌ 错误：找不到Story目录"
    exit 1
}

echo "📂 进入项目目录: $(pwd)"

# 检查Python版本
echo "🐍 检查Python版本..."
python3 --version
python3 -m pip --version

# 检查GPU是否可用
echo "🔍 检查GPU状态..."
nvidia-smi

# 检查PyTorch和GPU支持
echo "🔍 检查PyTorch GPU支持..."
python3 -c "
import torch
print(f'PyTorch版本: {torch.__version__}')
print(f'CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA版本: {torch.version.cuda}')
    print(f'GPU数量: {torch.cuda.device_count()}')
    print(f'当前GPU: {torch.cuda.get_device_name(0)}')
else:
    print('⚠️  CUDA不可用，需要安装PyTorch GPU版本')
"

# 安装requirements.txt中的依赖
echo "📦 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    echo "找到requirements.txt，开始安装依赖..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ 找不到requirements.txt文件"
    exit 1
fi

# 如果PyTorch不支持CUDA，安装GPU版本
echo "🔧 检查并安装PyTorch GPU版本..."
python3 -c "
import torch
if not torch.cuda.is_available():
    print('需要安装PyTorch GPU版本')
    import subprocess
    subprocess.run(['pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cu118'])
else:
    print('PyTorch GPU支持已就绪')
"

# 验证GPU环境
echo "✅ 最终验证GPU环境..."
python3 -c "
import torch
print('=' * 50)
print('GPU环境验证结果:')
print(f'PyTorch版本: {torch.__version__}')
print(f'CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA版本: {torch.version.cuda}')
    print(f'GPU数量: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
    print(f'当前设备: {torch.cuda.current_device()}')
print('=' * 50)
"

# 检查关键依赖
echo "🔍 验证关键依赖包..."
python3 -c "
try:
    import transformers
    print(f'✅ transformers: {transformers.__version__}')
except ImportError:
    print('❌ transformers 未安装')

try:
    import language_tool_python
    print('✅ language-tool-python: 已安装')
except ImportError:
    print('❌ language-tool-python 未安装')

try:
    import pandas
    print(f'✅ pandas: {pandas.__version__}')
except ImportError:
    print('❌ pandas 未安装')

try:
    import numpy
    print(f'✅ numpy: {numpy.__version__}')
except ImportError:
    print('❌ numpy 未安装')
"

echo "🎉 GPU服务器环境配置完成！"
echo ""
echo "📋 接下来可以执行的操作："
echo "1. 测试单文件流畅度分析: python3 test_fluency_single.py"
echo "2. 运行批量流畅度分析: python3 batch_analyze_fluency.py"
echo ""
echo "💡 建议先运行测试脚本验证环境是否正常工作"
