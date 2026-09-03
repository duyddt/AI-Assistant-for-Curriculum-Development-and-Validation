[CmdletBinding()]
param(
    [string]$InputFile,
    [switch]$Local
)

$ErrorActionPreference = "Stop"
$scriptPath = $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($scriptPath)) {
    throw "Khong xac dinh duoc duong dan run_demo_sv5.ps1. Hay chay script bang -File."
}
$projectDirectory = Split-Path -Parent $scriptPath
if ([string]::IsNullOrWhiteSpace($InputFile)) {
    $InputFile = Join-Path $projectDirectory "input_clos_demo.json"
}
$pythonCommand = Get-Command python -ErrorAction Stop
$exitCode = 0

# Preserve the caller's environment so this script does not permanently alter
# keys or model settings in an existing PowerShell session.
$previousSv5Key = $env:SV5_LLM_API_KEY
$previousModel = $env:SV5_LLM_MODEL
$previousTemperature = $env:SV5_LLM_TEMPERATURE
$previousPythonUtf8 = $env:PYTHONUTF8
$temporaryGeminiKey = $false

Push-Location -LiteralPath $projectDirectory
try {
    $env:PYTHONUTF8 = "1"

    if ($Local) {
        Write-Host "Chay SV5 o che do local: khong goi Gemini API." -ForegroundColor Yellow
        & $pythonCommand.Source "demo_clo_schedule.py" --input $InputFile
        $exitCode = $LASTEXITCODE
    }
    else {
        if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
            $secureKey = Read-Host "Nhap Gemini API key (ky tu se duoc an)" -AsSecureString
            $keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
            try {
                $env:GEMINI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
            }
            finally {
                [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
            }
            $temporaryGeminiKey = $true
        }

        if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
            throw "Gemini API key khong duoc de trong."
        }

        $env:SV5_LLM_API_KEY = $env:GEMINI_API_KEY
        $env:SV5_LLM_MODEL = "gemini/gemini-3.5-flash-lite"
        $env:SV5_LLM_TEMPERATURE = "0"

        Write-Host "Chay SV5 live voi Gemini 3.5 Flash-Lite..." -ForegroundColor Cyan
        & $pythonCommand.Source "demo_clo_schedule.py" --input $InputFile --live
        $exitCode = $LASTEXITCODE
    }
}
finally {
    if ($temporaryGeminiKey) {
        Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
    }

    if ($null -eq $previousSv5Key) {
        Remove-Item Env:SV5_LLM_API_KEY -ErrorAction SilentlyContinue
    }
    else {
        $env:SV5_LLM_API_KEY = $previousSv5Key
    }

    if ($null -eq $previousModel) {
        Remove-Item Env:SV5_LLM_MODEL -ErrorAction SilentlyContinue
    }
    else {
        $env:SV5_LLM_MODEL = $previousModel
    }

    if ($null -eq $previousTemperature) {
        Remove-Item Env:SV5_LLM_TEMPERATURE -ErrorAction SilentlyContinue
    }
    else {
        $env:SV5_LLM_TEMPERATURE = $previousTemperature
    }

    if ($null -eq $previousPythonUtf8) {
        Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONUTF8 = $previousPythonUtf8
    }

    Pop-Location
}

if ($exitCode -ne 0) {
    throw "Demo SV5 ket thuc voi ma loi $exitCode."
}
