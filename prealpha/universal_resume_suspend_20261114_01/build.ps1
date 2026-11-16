param([ValidateRange(1, 99)][int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh build directory required' }

$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if (!(Test-Path -LiteralPath $vcvars)) { throw 'Missing local MSVC' }
[void][IO.Directory]::CreateDirectory($out)
$source = Join-Path $PSScriptRoot 'NativeDelayChecks.cpp'
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT "$source" /link /OUT:NativeDelayChecks.exe
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    @{
        exe_sha256 = (Get-FileHash -LiteralPath 'NativeDelayChecks.exe').Hash
        source_sha256 = (Get-FileHash -LiteralPath $source).Hash
        header_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'DelayHold.hpp')).Hash
    } | ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
} finally { Pop-Location }
