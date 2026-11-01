<#
.SYNOPSIS
    Instala el certificado público de desarrollo de AutoRod en el almacén de confianza de Windows.

.DESCRIPTION
    Permite a los usuarios y desarrolladores confiar en el ejecutable en sus máquinas locales,
    eliminando las pantallas de advertencia de Microsoft Defender SmartScreen.
    
    Requiere ejecutarse en una ventana de PowerShell.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [string]$CerPath = "AutoRod-Dev-Certificate.cer"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CerPath)) {
    Write-Error "No se encontró el archivo de certificado: $CerPath"
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Instalador de Confianza para AutoRod" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

try {
    # Importar en el almacén de Entidades de Certificación Raíz de Confianza del usuario actual
    Import-Certificate -FilePath $CerPath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
    Write-Host "[OK] Certificado agregado con éxito al almacén de confianza del usuario actual." -ForegroundColor Green
    Write-Host "A partir de este momento, Windows reconocerá la firma del binario sin bloqueos de SmartScreen." -ForegroundColor Green
} catch {
    Write-Error "Fallo al importar el certificado: $_"
}
