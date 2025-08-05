@echo off
REM Переходим в корень проекта
cd /d "%~dp0"

REM Активируем виртуальное окружение
call .venv\Scripts\activate

REM Запускаем OPC UA сервер в НОВОМ КОНСОЛЬНОМ ОКНЕ
start "BKNS OPC Server" cmd /c "python .\opc_server\my_server.py & pause"

REM Ждем 3 секунды для инициализации OPC-сервера
timeout /t 3 /nobreak >nul

REM Запускаем FastAPI приложение в ТЕКУЩЕМ окне
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

pause