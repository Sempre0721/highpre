@echo off
setlocal

REM 设置端口号（请确保与config.json中的端口一致）
set PORT=5839

REM 启动Flask应用
echo 正在启动highpre智能AI剪辑系统...
echo 请稍候，应用启动后将自动打开浏览器...

REM 在后台启动Python应用
start "highpre backend" /min python main.py

REM 等待应用启动（可以根据需要调整等待时间）
echo 等待应用启动...
timeout /t 5 /nobreak >nul

REM 打开浏览器访问应用
echo 正在打开浏览器...
start "" http://localhost:%PORT%

echo.
echo 应用已在后台运行，可以通过 http://localhost:%PORT% 访问
echo 关闭此窗口不会停止应用运行
echo 若要停止应用，请在任务管理器中结束python进程
echo.

REM 保持窗口开启，让用户看到提示信息
pause