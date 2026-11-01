<#
.SYNOPSIS
    Script de Firma Digital (Code Signing) para ejecutables e instaladores de AutoRod.

.DESCRIPTION
    Firma ejecutables (.exe) utilizando un certificado digital comercial (.pfx) si está disponible,
    o genera y utiliza un certificado autofirmado para desarrollo y distribución de confianza local.
    Aplica timestamp RFC 3161 para que la firma permanezca válida tras expirar el certificado.

.PARAMETER TargetPath
    Ruta del archivo .exe a firmar.

.PARAMETER PfxPath
    (Opcional) Ruta al archivo de certificado comercial PKCS#12 (.pfx).

.PARAMETER PfxPassword
    (Opcional) Contraseña del certificado .pfx.

.PARAMETER CreateDevCert
    Si es $true y no se pasa un .pfx, genera un certificado autofirmado para pruebas locales.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,

    [Parameter(Mandatory = $false)]
    [string]$PfxPath = "",

    [Parameter(Mandatory = $false)]
    [string]$PfxPassword = "",

    [Parameter(Mandatory = $false)]
    [switch]$CreateDevCert
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TargetPath)) {
    Write-Error "El archivo objetivo no existe: $TargetPath"
    exit 1
}

$TimestampServer = "http://timestamp.digicert.com"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   AutoRod Code Signing Tool" -ForegroundColor Cyan
Write-Host "   Objetivo: $TargetPath" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$Cert = $null

# 1. Intentar usar certificado PFX comercial si fue provisto
if ($PfxPath -and (Test-Path $PfxPath)) {
    Write-Host "[1/3] Cargando certificado comercial desde $PfxPath..." -ForegroundColor Green
    $SecurePass = ConvertTo-SecureString $PfxPassword -AsPlainText -Force
    $Cert = Get-PfxCertificate -FilePath $PfxPath
} elseif ($CreateDevCert) {
    # 2. Generar certificado autofirmado de desarrollo si se solicitó
    Write-Host "[1/3] Generando certificado autofirmado para AutoRod..." -ForegroundColor Yellow
    $CertSubject = "CN=AutoRod Open Source Project, O=AutoRod, OU=Software Distribution"
    
    # Buscar si ya existe uno previo en el almacén del usuario
    $Existing = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $CertSubject } | Select-Object -First 1
    if ($Existing) {
        Write-Host "  Usando certificado de desarrollo existente en el almacén del usuario." -ForegroundColor Green
        $Cert = $Existing
    } else {
        try {
            $Cert = New-SelfSignedCertificate `
                -Type CodeSigningCert `
                -Subject $CertSubject `
                -CertStoreLocation Cert:\CurrentUser\My `
                -NotAfter (Get-Date).AddYears(5) `
                -KeySpec Signature `
                -FriendlyName "AutoRod Dev Code Signing"
            Write-Host "  Nuevo certificado de desarrollo creado con éxito." -ForegroundColor Green
        } catch {
            Write-Warning "No se pudo generar el certificado autofirmado en el almacén del sistema: $_"
            Write-Host "Sugerencia: Ejecuta este script directamente en una consola de PowerShell con permisos estándar o usa un archivo .pfx comercial con el parámetro -PfxPath." -ForegroundColor Yellow
            exit 0
        }
    }

    # Exportar copia pública .cer para que los usuarios puedan confiar en él
    $ExportDir = Split-Path -Parent $TargetPath
    $CerPath = Join-Path $ExportDir "AutoRod-Dev-Certificate.cer"
    Export-Certificate -Cert $Cert -FilePath $CerPath -Force | Out-Null
    Write-Host "  Certificado público exportado a: $CerPath" -ForegroundColor Cyan
} else {
    Write-Host "[!] No se especificó certificado comercial ni el switch -CreateDevCert." -ForegroundColor Yellow
    Write-Host "    Usa: .\scripts\sign_binary.ps1 -TargetPath '$TargetPath' -CreateDevCert" -ForegroundColor Yellow
    exit 0
}

if ($Cert) {
    Write-Host "[2/3] Aplicando firma digital con Authenticode y Timestamp..." -ForegroundColor Green
    try {
        $SigResult = Set-AuthenticodeSignature `
            -FilePath $TargetPath `
            -Certificate $Cert `
            -TimestampServer $TimestampServer `
            -HashAlgorithm SHA256

        if ($SigResult.Status -eq "Valid") {
            Write-Host "[3/3] ¡Firma digital válida aplicada correctamente!" -ForegroundColor Green
        } else {
            Write-Host "[3/3] Firma aplicada con estado: $($SigResult.Status) ($($SigResult.StatusMessage))" -ForegroundColor Yellow
        }
    } catch {
        Write-Warning "Fallo al aplicar firma con Timestamp: $_"
        Write-Host "Reintentando firma sin servidor de Timestamp..." -ForegroundColor Yellow
        Set-AuthenticodeSignature -FilePath $TargetPath -Certificate $Cert -HashAlgorithm SHA256 | Out-Null
    }

    # Verificar estado de firma
    $FinalSig = Get-AuthenticodeSignature -FilePath $TargetPath
    Write-Host "----------------------------------------------------------"
    Write-Host "Resumen de Firma:"
    Write-Host "  Estado: $($FinalSig.Status)"
    Write-Host "  Firma: $($FinalSig.SignerCertificate.Subject)"
    Write-Host "  Algoritmo: $($FinalSig.SignerCertificate.SignatureAlgorithm.FriendlyName)"
    Write-Host "----------------------------------------------------------"
}
