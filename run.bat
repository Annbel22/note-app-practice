@echo off
call venv\Scripts\activate
set QT_QPA_PLATFORM_PLUGIN_PATH=
set QT_QPA_PLATFORM_PLUGIN_PATH=D:\Univer\Vumip\note_app\venv\Lib\site-packages\PyQt5\Qt5\plugins
python main.py
pause