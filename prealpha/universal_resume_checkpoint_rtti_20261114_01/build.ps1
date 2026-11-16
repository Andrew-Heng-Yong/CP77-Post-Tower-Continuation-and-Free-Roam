param([ValidateRange(1, 99)][int]$Attempt = 1)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh build directory required' }
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sdk = Join-Path $workspace 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include'
$source = Join-Path $PSScriptRoot 'source_01/NativeCheckpoint.cpp'
$checkpointFixture = Join-Path $PSScriptRoot 'source_01/CheckpointChecks.cpp'
$registrationFixture = Join-Path $PSScriptRoot 'RegistrationChecks.cpp'
foreach ($path in @($vcvars, (Join-Path $sdk 'RED4ext/Api/v1/Sdk.hpp'), $source, $checkpointFixture, $registrationFixture)) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required build input missing $path" }
}
[void][IO.Directory]::CreateDirectory($out)
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /LD /external:I"$sdk" /external:W0 "$source" /link /OUT:PTFR_ExecutionCheckpoint.dll bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
dumpbin.exe /nologo /exports PTFR_ExecutionCheckpoint.dll > exports.txt
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /external:I"$sdk" /external:W0 "$checkpointFixture" /link /OUT:CheckpointChecks.exe bcrypt.lib user32.lib
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /external:I"$sdk" /external:W0 "$registrationFixture" /link /OUT:RegistrationChecks.exe user32.lib
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Native compilation failed' }
    $exports = Get-Content -LiteralPath 'exports.txt' -Raw
    foreach ($name in 'Main','Query','Supports') {
        if ($exports -cnotmatch "(?m)\b$name\s*$") { throw "Missing RED4ext export $name" }
    }
    @(
        $source, (Join-Path $PSScriptRoot 'source_01/Checkpoint.hpp'), $checkpointFixture, $registrationFixture,
        (Join-Path $PSScriptRoot 'CheckpointRegistration.hpp'), (Join-Path $PSScriptRoot 'RegisterReader.inc'),
        (Join-Path $PSScriptRoot '../universal_resume_boundary_20261114_01/TimerRecord.hpp'),
        (Join-Path $PSScriptRoot '../universal_resume_eagles_20261114_01/GameTimeWait.hpp'),
        (Join-Path $out 'PTFR_ExecutionCheckpoint.dll'), (Join-Path $out 'CheckpointChecks.exe'),
        (Join-Path $out 'RegistrationChecks.exe')
    ) | ForEach-Object {
        [pscustomobject]@{name = (Split-Path $_ -Leaf); sha256 = (Get-FileHash -LiteralPath $_).Hash}
    } | ConvertTo-Json | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
} finally {
    Pop-Location
}
