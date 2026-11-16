param([ValidateRange(1, 99)][int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh build directory required' }

$vs = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools'
$vcvars = Join-Path $vs 'VC\Auxiliary\Build\vcvars64.bat'
$sdk = Join-Path $workspace 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include'
if (!(Test-Path -LiteralPath $vcvars) -or !(Test-Path -LiteralPath (Join-Path $sdk 'RED4ext/Api/v1/Sdk.hpp'))) {
    throw 'Missing local MSVC or SDK headers'
}

[void][IO.Directory]::CreateDirectory($out)
$source = Join-Path $PSScriptRoot 'TimerProbe.cpp'
$fixtureTests = Join-Path $PSScriptRoot 'TimerRecordChecks.cpp'
$command = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /LD /I"$sdk" "$source" /link /OUT:PTFR_QuestTimerProbe.dll bcrypt.lib
if errorlevel 1 exit /b 1
dumpbin.exe /nologo /exports PTFR_QuestTimerProbe.dll > exports.txt
if errorlevel 1 exit /b 1
dumpbin.exe /nologo /dependents PTFR_QuestTimerProbe.dll > dependencies.txt
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT "$fixtureTests" /link /OUT:TimerRecordChecks.exe
"@
$batch = Join-Path $out 'build.cmd'
Set-Content -LiteralPath $batch -Value $command -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Compilation or DLL readback failed' }
    $exports = Get-Content -LiteralPath 'exports.txt' -Raw
    foreach ($name in 'Main','Query','Supports') {
        if ($exports -cnotmatch "(?m)\b$name\s*$") { throw "Missing RED4ext export $name" }
    }
    $digest = (Get-FileHash -LiteralPath 'PTFR_QuestTimerProbe.dll').Hash
    @{ status = 'WORKSPACE_PROBE_BUILT'; dll_sha256 = $digest; source_sha256 = (Get-FileHash -LiteralPath $source).Hash;
       checks_sha256 = (Get-FileHash -LiteralPath 'TimerRecordChecks.exe').Hash;
       checks_source_sha256 = (Get-FileHash -LiteralPath $fixtureTests).Hash;
       cutoff_observation_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'CutoffObservation.hpp')).Hash;
       timer_record_sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'TimerRecord.hpp')).Hash } |
        ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
    "Built $out\PTFR_QuestTimerProbe.dll"
} finally { Pop-Location }
