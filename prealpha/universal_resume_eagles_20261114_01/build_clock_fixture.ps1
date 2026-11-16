param([ValidateRange(1,99)][int]$Attempt = 1)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh build directory required' }
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if (!(Test-Path -LiteralPath $vcvars)) { throw 'Missing local MSVC' }
$source = Join-Path $PSScriptRoot 'GameTimeChecks.cpp'
$header = Join-Path $PSScriptRoot 'GameTimeWait.hpp'
$sourceHash = (Get-FileHash -LiteralPath $source).Hash
$headerHash = (Get-FileHash -LiteralPath $header).Hash
[void][IO.Directory]::CreateDirectory($out)
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT "$source" /link /OUT:GameTimeChecks.exe
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Clock fixture build failed' }
    if ((Get-FileHash -LiteralPath $source).Hash -cne $sourceHash -or
        (Get-FileHash -LiteralPath $header).Hash -cne $headerHash) { throw 'Source changed during build' }
    @{
        source_sha256 = $sourceHash
        header_sha256 = $headerHash
        exe_sha256 = (Get-FileHash -LiteralPath 'GameTimeChecks.exe').Hash
    } | ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
} finally {
    Pop-Location
}
