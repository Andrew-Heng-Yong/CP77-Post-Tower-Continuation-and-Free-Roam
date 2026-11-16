param([ValidateRange(1, 99)][int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$out = Join-Path $PSScriptRoot ('probe_build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh probe build directory required' }
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sdk = Join-Path $workspace 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include'
if (!(Test-Path -LiteralPath $vcvars) -or !(Test-Path -LiteralPath (Join-Path $sdk 'RED4ext/Api/v1/Sdk.hpp'))) {
    throw 'Missing local MSVC or RED4ext SDK headers'
}
[void][IO.Directory]::CreateDirectory($out)
$source = Join-Path $PSScriptRoot 'RttiProbe.cpp'
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /LD /external:I"$sdk" /external:W0 "$source" /link /OUT:PTFR_CheckpointRTTIProbe.dll user32.lib
if errorlevel 1 exit /b 1
dumpbin.exe /nologo /exports PTFR_CheckpointRTTIProbe.dll > exports.txt
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'RTTI probe compilation failed' }
    $exports = Get-Content -LiteralPath 'exports.txt' -Raw
    foreach ($name in 'Main', 'Query', 'Supports') {
        if ($exports -cnotmatch "(?m)\b$name\s*$") { throw "Missing RED4ext export $name" }
    }
    [pscustomobject]@{
        source_sha256 = (Get-FileHash -LiteralPath $source).Hash
        dll_sha256 = (Get-FileHash -LiteralPath 'PTFR_CheckpointRTTIProbe.dll').Hash
        dll_bytes = (Get-Item -LiteralPath 'PTFR_CheckpointRTTIProbe.dll').Length
    } | ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
} finally {
    Pop-Location
}
