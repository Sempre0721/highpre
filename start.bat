@echo off
setlocal

REM ���ö˿ںţ���ȷ����config.json�еĶ˿�һ�£�
set PORT=5839

REM ����FlaskӦ��
echo ��������highpre����AI����ϵͳ...
echo ���Ժ�Ӧ���������Զ��������...

REM �ں�̨����PythonӦ��
start "highpre backend" /min python main.py

REM �ȴ�Ӧ�����������Ը�����Ҫ�����ȴ�ʱ�䣩
echo �ȴ�Ӧ������...
timeout /t 5 /nobreak >nul

REM �����������Ӧ��
echo ���ڴ������...
start "" http://localhost:%PORT%

echo.
echo Ӧ�����ں�̨���У�����ͨ�� http://localhost:%PORT% ����
echo �رմ˴��ڲ���ֹͣӦ������
echo ��ҪֹͣӦ�ã���������������н���python����
echo.

REM ���ִ��ڿ��������û�������ʾ��Ϣ
pause