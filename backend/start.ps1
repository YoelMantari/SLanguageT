# Script para configurar e iniciar el backend de ConnectSigns

Write-Host "=== ConnectSigns Backend Setup ===" -ForegroundColor Cyan
Write-Host ""

# Verificar si existe el entorno virtual
$venvPath = "..\\.venv"
if (-Not (Test-Path $venvPath)) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Entorno virtual creado." -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& "$venvPath\Scripts\Activate.ps1"

# Instalar dependencias
Write-Host ""
Write-Host "Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt

# Verificar que el modelo existe
$modelPath = "..\modelo_senas.h5"
if (-Not (Test-Path $modelPath)) {
    Write-Host ""
    Write-Host "ADVERTENCIA: No se encontró el archivo modelo_senas.h5" -ForegroundColor Red
    Write-Host "Por favor, coloca tu modelo en: $modelPath" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Modelo encontrado: $modelPath" -ForegroundColor Green
}

# Iniciar servidor
Write-Host ""
Write-Host "=== Iniciando servidor FastAPI ===" -ForegroundColor Cyan
Write-Host "El servidor estará disponible en: http://localhost:8000" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""

python app.py
