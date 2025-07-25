@echo off
REM 检查是否已存在虚拟环境，如果不存在则创建
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM 激活虚拟环境
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM 安装依赖包
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

REM 检查FFmpeg可用性
echo Checking FFmpeg availability...
python -c "import shutil; import sys; ffmpeg_path = shutil.which('ffmpeg'); print('✓ FFmpeg found:', ffmpeg_path) if ffmpeg_path else print('❌ FFmpeg not found'); sys.exit(0 if ffmpeg_path else 1)"

if errorlevel 1 (
    echo.
    echo FFmpeg check failed. Please install FFmpeg and ensure it's in your PATH.
    echo Visit: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

echo FFmpeg check passed, continuing to start application...

REM 启动项目并在后台运行
echo Starting the application...
start "" http://localhost:5839
python main.py

REM 保持窗口开启
pause