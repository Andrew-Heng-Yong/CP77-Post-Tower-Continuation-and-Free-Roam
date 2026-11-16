param([ValidateRange(1,99)][int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
$sdk = Join-Path $root 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include'
if (!(Test-Path -LiteralPath $vcvars) -or !(Test-Path -LiteralPath $sdk)) { throw 'Missing local MSVC or SDK' }
$probe = Join-Path $PSScriptRoot 'ReplyProbe.cpp'
$checks = Join-Path $PSScriptRoot 'ReplyChecks.cpp'
$sources = [ordered]@{
    source = $probe
    checks = $checks
    header = Join-Path $PSScriptRoot 'ReplyHandoff.hpp'
    game_time = Join-Path $root 'prealpha/universal_resume_eagles_20261114_01/GameTimeWait.hpp'
    slots = Join-Path $root 'prealpha/universal_resume_retirement_20261114_01/RetiredQuestSlot.hpp'
    phase_address = Join-Path $root 'prealpha/universal_resume_owner_20261114_01/OwnerTrace.hpp'
}
$hashes = [ordered]@{}
foreach ($name in $sources.Keys) { $hashes[$name] = (Get-FileHash -LiteralPath $sources[$name]).Hash }
[void][IO.Directory]::CreateDirectory($out)
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /LD /external:I"$sdk" /external:W0 "$probe" /link /OUT:PTFR_ClaireReply.dll bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
dumpbin.exe /nologo /exports PTFR_ClaireReply.dll > exports.txt
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT "$checks" /link /OUT:ReplyChecks.exe
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
    $exports = Get-Content -LiteralPath exports.txt -Raw
    foreach ($name in 'Main','Query','Supports') {
        if ($exports -cnotmatch "(?m)\b$name\s*$") { throw "Missing RED4ext export $name" }
    }
    $result = & (Join-Path $out 'ReplyChecks.exe')
    if ($LASTEXITCODE -ne 0 -or $result[-1] -cne '15 passed, 0 failed') { throw "Fixture failed: $result" }
    $result | Set-Content -LiteralPath 'fixture_checks.txt' -Encoding utf8NoBOM
    foreach ($name in $sources.Keys) {
        if ((Get-FileHash -LiteralPath $sources[$name]).Hash -cne $hashes[$name]) {
            throw "Source changed during compile: $name"
        }
    }
    @{ dll_sha256 = (Get-FileHash -LiteralPath 'PTFR_ClaireReply.dll').Hash
       sources = $hashes
    } | ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
    $result[-1]
} finally { Pop-Location }
