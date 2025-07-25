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

REM 启动项目并在后台运行
echo Starting the application...
start "" http://localhost:5839
python main.py

REM 保持窗口开启
pause