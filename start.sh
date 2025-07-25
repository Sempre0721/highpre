#!/bin/bash

# 检查是否已存在虚拟环境，如果不存在则创建
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "Activating virtual environment..."
source venv/bin/activate

# 安装依赖包
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 检查FFmpeg可用性
echo "Checking FFmpeg availability..."
python3 -c "
import os
import platform
import shutil
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_exe = 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg'
local_ffmpeg = os.path.join(script_dir, ffmpeg_exe)

if os.path.exists(local_ffmpeg):
    print(f'✓ 找到本地 FFmpeg: {local_ffmpeg}')
    sys.exit(0)

system_ffmpeg = shutil.which('ffmpeg')
if system_ffmpeg:
    print(f'✓ 找到系统 FFmpeg: {system_ffmpeg}')
    sys.exit(0)

print('❌ 未找到 FFmpeg')
print('')
print('💡 解决方案:')
print('   请下载并安装 FFmpeg:')
print('   - 官方网站: https://ffmpeg.org/download.html')
print('   - Ubuntu/Debian 用户可使用 apt 安装:')
print('     sudo apt update && sudo apt install ffmpeg')
print('   - CentOS/RHEL 用户可使用 yum 安装:')
print('     sudo yum install ffmpeg')
print('   - macOS 用户可使用 Homebrew 安装:')
print('     brew install ffmpeg')
print('')
print('📌 安装完成后请确保:')
print('   1. 将 FFmpeg 放在本程序同目录下，或')
print('   2. 将 FFmpeg 添加到系统 PATH 环境变量中')
sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "FFmpeg检查失败，请根据上面的提示安装FFmpeg后再运行程序。"
    exit 1
fi

echo "FFmpeg检查通过，继续启动应用程序..."

# 启动项目
echo "Starting the application..."
python3 main.py