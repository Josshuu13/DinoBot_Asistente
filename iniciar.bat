@echo off
chcp 65001 >nul
cd /d "%~dp0"
title DinoBot - Asistente Virtual IA

rem === 1. Crear el entorno virtual (solo la primera vez) ===
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creando entorno virtual .venv ...
    for %%V in (3.12 3.11 3.13 3) do (
        if not exist ".venv\Scripts\python.exe" py -%%V -m venv .venv >nul 2>&1
    )
    if not exist ".venv\Scripts\python.exe" python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo No se encontro Python. Instala Python 3.11 o 3.12 desde https://www.python.org/downloads/
    echo y marca la casilla "Add python.exe to PATH" durante la instalacion.
    pause
    exit /b 1
)

rem === 2. Instalar dependencias (solo la primera vez, tarda unos minutos) ===
if not exist ".venv\.instalado" (
    echo [2/4] Instalando librerias, esto tarda unos minutos ...
    ".venv\Scripts\python.exe" --version
    ".venv\Scripts\python.exe" -m pip install --upgrade pip > instalacion.log 2>&1
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt >> instalacion.log 2>&1 || goto error
    echo [3/4] Descargando modelo de espanol de spaCy ...
    ".venv\Scripts\python.exe" -m spacy download es_core_news_md >> instalacion.log 2>&1 || goto error
    echo [4/4] Descargando datos de NLTK ...
    ".venv\Scripts\python.exe" -c "import nltk; [nltk.download(x) for x in ('punkt','punkt_tab','stopwords')]" >> instalacion.log 2>&1 || goto error
    echo ok> ".venv\.instalado"
)

rem === 3. Ejecutar DinoBot ===
echo Iniciando DinoBot ...
".venv\Scripts\python.exe" main.py > ejecucion.log 2>&1
if errorlevel 1 (
    echo.
    echo DinoBot se cerro con un error. Revisa el archivo ejecucion.log
    pause
)
exit /b 0

:error
echo.
echo Hubo un error en la instalacion. Revisa el archivo instalacion.log
pause
exit /b 1
