#!/usr/bin/env python3
"""
故事大纲生成器运行脚本
运行命令：python run_outline_app.py
"""

import subprocess
import sys
import os

def main():
    """运行Streamlit应用"""
    print("🚀 启动故事大纲生成器...")
    print("📚 应用将在浏览器中打开")
    print("🔗 默认地址：http://localhost:8501")
    print("-" * 50)
    
    # 检查streamlit是否安装
    try:
        import streamlit
        print(f"✅ Streamlit版本: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit未安装，请运行: pip install streamlit")
        return
    
    # 检查应用文件是否存在
    app_file = "outline_generator_app.py"
    if not os.path.exists(app_file):
        print(f"❌ 应用文件不存在: {app_file}")
        return
    
    print(f"✅ 应用文件: {app_file}")
    
    # 运行streamlit应用
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", app_file]
        print(f"🔄 执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
    except KeyboardInterrupt:
        print("\n👋 应用已停止")

if __name__ == "__main__":
    main()
