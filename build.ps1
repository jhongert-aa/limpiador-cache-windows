# Compila la app a un .exe standalone (pide PyInstaller).
# Uso: abrir PowerShell en esta carpeta y ejecutar:  .\build.ps1

$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando PyInstaller..."
    python -m pip install --user pyinstaller
}

pyinstaller --noconfirm --onefile --windowed `
    --name "LimpiadorCache" `
    --uac-admin `
    main.py

Write-Host ""
Write-Host "Listo. El ejecutable esta en .\dist\LimpiadorCache.exe"
