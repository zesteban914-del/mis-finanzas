@echo off
rem Arranca Mis Finanzas: enciende PostgreSQL (Docker) y la API con la interfaz.
rem Uso:  .\iniciar.bat          (puerto 8000)
rem       .\iniciar.bat 8080     (otro puerto)
rem No hace falta activar el entorno virtual: usa directamente .venv\Scripts\python.exe

cd /d "%~dp0"
set PUERTO=%1
if "%PUERTO%"=="" set PUERTO=8000

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No existe el entorno virtual .venv. Crealo con:
  echo     py -3.12 -m venv .venv
  echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)

echo Encendiendo la base de datos...
docker compose up -d --wait >nul 2>&1
if errorlevel 1 (
  echo [AVISO] No se pudo encender PostgreSQL con Docker. Abre Docker Desktop y vuelve a intentar.
)

echo Abre http://localhost:%PUERTO% en el navegador. Para detener: Ctrl+C
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --reload-dir app --port %PUERTO%
