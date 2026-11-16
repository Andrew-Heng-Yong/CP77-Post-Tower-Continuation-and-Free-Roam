param([ValidateRange(1, 99)][int]$Attempt = 1)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$out = Join-Path $PSScriptRoot ('build_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh build directory required' }

$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if (!(Test-Path -LiteralPath $vcvars)) { throw 'Missing local MSVC' }

$prior = Join-Path (Split-Path -Parent $PSScriptRoot) 'universal_resume_handoff_20261114_01'
$source = Join-Path $prior 'NativeDelayChecks.cpp'
$expectedSource = '23A67BBCC1AEEB31453D98B9B6BEB3B5864B738D85FC4BD520BD9463A9145125'
if ((Get-FileHash -LiteralPath $source).Hash -cne $expectedSource) { throw 'Fixture source changed' }
$files = [ordered]@{
    source = $source
    handoff = Join-Path $prior 'RealTimeHandoff.hpp'
    delay = Join-Path $prior 'DelayHold.hpp'
    observation = Join-Path $prior 'CutoffObservation.hpp'
    timer_record = Join-Path $prior '../universal_resume_boundary_20261114_01/TimerRecord.hpp'
    owner = Join-Path $prior '../universal_resume_owner_20261114_01/OwnerTrace.hpp'
    retirement = Join-Path $PSScriptRoot 'RetiredQuestSlot.hpp'
    checks = Join-Path $PSScriptRoot 'RetiredQuestSlotChecks.cpp'
}
$sourceHashes = [ordered]@{}
foreach ($key in $files.Keys) { $sourceHashes[$key] = (Get-FileHash -LiteralPath $files[$key]).Hash }

# Extend the pinned stand-alone harness in a fresh directory. The extra native
# slices and checks use the same scratch heap and exception reporter.
$text = [IO.File]::ReadAllText($source)
$patches = [ordered]@{
    'slices != 73' = 'slices != 76'
    'void* sliceBaseForDiagnostics;' = "void* sliceBaseForDiagnostics;`nstd::uint8_t** ObserveQuestLock(std::uint8_t** observed, std::uint8_t* lock);"
    '        PutJump(0x1CEF5C, &FreeQuestBatch);' = "        PutJump(0x1CEF5C, &FreeQuestBatch);`n        PutJump(0x1FFAD60, &ObserveQuestLock);"
    '        Checks checks(native);' = "        InitQuestLockObserver(native);`n        Checks checks(native);"
    'int main(int argc, char** argv)' = '#include "../RetiredQuestSlotChecks.cpp"' + "`n`nint main(int argc, char** argv)"
    '        CutoffAndRebuiltHandler(checks, native);' = "        CutoffAndRebuiltHandler(checks, native);`n        CheckRetiredSlots(checks, native);"
}
foreach ($original in $patches.Keys) {
    if ($text.IndexOf($original, [StringComparison]::Ordinal) -lt 0 -or
        $text.IndexOf($original, [StringComparison]::Ordinal) -ne $text.LastIndexOf($original, [StringComparison]::Ordinal)) {
        throw "Unexpected fixture source anchor: $original"
    }
    $text = $text.Replace($original, $patches[$original])
}
[void][IO.Directory]::CreateDirectory($out)
$staged = Join-Path $out 'NativeDelayChecks.cpp'
Set-Content -LiteralPath $staged -Value $text -Encoding utf8NoBOM
$batch = @"
@echo off
call "$vcvars" >nul
if errorlevel 1 exit /b 1
cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"$prior" NativeDelayChecks.cpp /link /OUT:NativeDelayChecks.exe
"@
Set-Content -LiteralPath (Join-Path $out 'build.cmd') -Value $batch -Encoding ascii
Push-Location -LiteralPath $out
try {
    & cmd.exe /d /c build.cmd
    if ($LASTEXITCODE -ne 0) { throw 'Compilation failed' }
    foreach ($key in $files.Keys) {
        if ((Get-FileHash -LiteralPath $files[$key]).Hash -cne $sourceHashes[$key]) {
            throw "Fixture source changed during build: $key"
        }
    }
    @{
        sources = $sourceHashes
        staged_sha256 = (Get-FileHash -LiteralPath $staged).Hash
        exe_sha256 = (Get-FileHash -LiteralPath 'NativeDelayChecks.exe').Hash
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'build.json' -Encoding utf8NoBOM
} finally {
    Pop-Location
}
