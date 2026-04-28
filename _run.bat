@echo off
chcp 65001 > nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -X utf8 manage.py runserver 127.0.0.1:8000 --noreload
