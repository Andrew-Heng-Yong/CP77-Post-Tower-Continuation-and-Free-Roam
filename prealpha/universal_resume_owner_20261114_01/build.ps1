param([ValidateRange(1, 99)][int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh build directory required' }

$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sdk = Join-Path $workspace 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include'
if (!(Test-Path -LiteralPath $vcvars) -or !(Test-Path -LiteralPath (Join-Path $sdk 'RED4ext/Api/v1/Sdk.hpp'))) {
    throw 'Missing local MSVC or SDK headers'
}
[void][IO.Directory]::CreateDirectory($out)
$source = Join-Path $PSScriptRoot 'OwnerTraceChecks.cpp'
$probe = Join-Path $PSScriptRoot 'CutoffProbe.cpp'
$prior = Join-Path $PSScriptRoot '../universal_resume_handoff_20261114_01'
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /LD /external:I"$sdk" /external:W0 "$probe" /link /OUT:PTFR_QuestTimerProbe.dll bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
dumpbin.exe /nologo /exports PTFR_QuestTimerProbe.dll > exports.txt
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT "$source" /link /OUT:OwnerTraceChecks.exe
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    $exports = Get-Content -LiteralPath 'exports.txt' -Raw
    foreach ($name in 'Main','Query','Supports') {
        if ($exports -cnotmatch "(?m)\b$name\s*$") { throw "Missing RED4ext export $name" }
    }
    @{
        exe_sha256 = (Get-FileHash -LiteralPath 'OwnerTraceChecks.exe').Hash
        source_sha256 = (Get-FileHash -LiteralPath $source).Hash
        header_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'OwnerTrace.hpp')).Hash
        hold_sha256 = (Get-FileHash -LiteralPath (Join-Path $prior 'DelayHold.hpp')).Hash
        handoff_sha256 = (Get-FileHash -LiteralPath (Join-Path $prior 'RealTimeHandoff.hpp')).Hash
        cutoff_sha256 = (Get-FileHash -LiteralPath (Join-Path $prior 'CutoffObservation.hpp')).Hash
        record_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot '../universal_resume_boundary_20261114_01/TimerRecord.hpp')).Hash
        probe_sha256 = (Get-FileHash -LiteralPath $probe).Hash
        dll_sha256 = (Get-FileHash -LiteralPath 'PTFR_QuestTimerProbe.dll').Hash
    } | ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
} finally { Pop-Location }
