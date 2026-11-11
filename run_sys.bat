@echo off
chcp 65001 >nul
echo ========================================================
echo   VNXBOX ENTERPRISE - LIVE WAR ROOM (ASGI / WEBSOCKET)
echo ========================================================

call env\Scripts\activate.bat
echo [+] Đã kích hoạt môi trường ảo, đang khởi động Daphne Server...

daphne -b 127.0.0.1 -p 8000 vnxbox_core.asgi:application

pause