@echo off
echo 正在停止所有 Python 进程...
taskkill /F /IM python.exe 2>nul

echo 正在清理缓存...
cd /d d:\Ai\code\course\project1
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul

echo 正在启动服务器...
python server.py

pause
