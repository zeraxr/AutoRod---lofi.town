<#
.SYNOPSIS
    Añade la ruta de instalación de AutoRod a las exclusiones de Windows Defender.

.DESCRIPTION
    Los bots de juego y herramientas de automatización que envían eventos de ratón/teclado
    de baja latencia (SendInput / Interception) pueden ser catalogados por algunos antivirus
    como 'Riskware' o 'GameHack' debido a su naturaleza de automatización activa.
    
    Este script permite al usuario autorizar explícitamente la carpeta de AutoRod en Windows Defender,
    garantizando que el antivirus no interrumpa el bot sin comprometer la seguridad del resto del equipo.
    
    NOTA: Requiere ejecutarse como Administrador de Windows.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [string]$TargetFolder = "$env:LOCALAPPDATA\Programs\AutoRod"
)

# Verificar permisos de Administrador
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $IsAdmin) {
    Write-Warning "Este script requiere permisos de Administrador para modificar la lista de exclusiones de Windows Defender."
    Write-Host "Por favor, abre PowerShell como Administrador y vuelve a ejecutar:" -ForegroundColor Yellow
    Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\add_defender_exclusion.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Configuración de Exclusión de Seguridad para AutoRod" -ForegroundColor Cyan
Write-Host "   Ruta: $TargetFolder" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

try {
    Add-MpPreference -ExclusionPath $TargetFolder
    Write-Host "[OK] Carpeta añadida correctamente a las exclusiones de Windows Defender." -ForegroundColor Green
    Write-Host "Windows Defender ya no escaneará ni bloqueará los módulos de AutoRod en esta ruta." -ForegroundColor Green
} catch {
    Write-Error "Fallo al registrar la exclusión en Windows Defender: $_"
}
