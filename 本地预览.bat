@echo off
rem 一键预览笔记网站：后台起 HTTP 服务 -> 打开浏览器
rem 关闭方法：直接关掉标题为 "gongkao-notes-server" 的窗口，或任务管理器结束 python
cd /d "%~dp0"
start "gongkao-notes-server" /min cmd /c "python -m http.server 8000"
timeout /t 1 /nobreak >nul
start "" "http://localhost:8000"
echo 网站已启动：http://localhost:8000
echo （关闭此窗口不影响网站；停止网站请关掉 gongkao-notes-server 窗口）
pause
