param([string]$Candidate = (Join-Path $PSScriptRoot '../build/gd1_01'))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$deploy = Join-Path $PSScriptRoot 'deploy.ps1'
$candidateRoot = (Resolve-Path -LiteralPath $Candidate).Path
$runsRoot = Join-Path $ws 'prealpha/graphics_gd1/fixtures'
$run = Join-Path $runsRoot ('run_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ'))
New-Item -ItemType Directory -Path $run -ErrorAction Stop | Out-Null
$rows = [Collections.Generic.List[object]]::new()
$archiveName = 'TowerContinued_DizzyDiagnostic_GD1.archive'
$expectedSha = (Get-FileHash -LiteralPath (Join-Path $candidateRoot $archiveName) -Algorithm SHA256).Hash
$checks = 0
function Put([string]$path,[string]$value) {
    [void](New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force)
    [IO.File]::WriteAllText($path,$value,[Text.UTF8Encoding]::new($false))
}
function PutJson([string]$path,$obj) { Put $path ($obj | ConvertTo-Json -Depth 30) }
function Sha([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
function Check([bool]$ok,[string]$message) {
    $script:checks++
    if (!$ok) { throw $message }
}
function NewFixture([string]$name) {
    $base = Join-Path $run $name
    $game = Join-Path $base 'game'
    $saves = Join-Path $base 'saves'
    $build = Join-Path $base 'build'
    $recovery = Join-Path $base 'recovery'
    [void](New-Item -ItemType Directory -Path (Join-Path $game 'archive/pc/mod'),$saves,$build -Force)
    Put (Join-Path $game 'archive/pc/mod/Unrelated.archive') 'synthetic protected archive'
    Put (Join-Path $game 'r6/scripts/Unrelated.reds') 'synthetic protected script'
    Put (Join-Path $game 'r6/cache/final.redscripts') 'synthetic protected cache'
    Put (Join-Path $saves 'ManualSave-00/sav.dat') 'synthetic original save'
    Put (Join-Path $saves 'ManualSave-00/metadata.9.json') '{"synthetic":true}'
    foreach ($name in @($archiveName,'build.json','tests.json')) {
        Copy-Item -LiteralPath (Join-Path $candidateRoot $name) -Destination (Join-Path $build $name)
    }
    return @{base=$base;game=$game;saves=$saves;build=$build;recovery=$recovery;target=(Join-Path $game ('archive/pc/mod/'+$archiveName))}
}
function Args($f,[string]$mode) { return @{Mode=$mode;Build=$f.build;RecoveryRoot=$f.recovery;GameRoot=$f.game;SaveRoot=$f.saves;Fixture=$true} }
function Call($f,[string]$mode) { $p=Args $f $mode; return (& $deploy @p | Out-String) }
function Refuse($p,[string]$pattern) {
    try { $null = & $deploy @p; throw 'UNEXPECTED_ACCEPTANCE' }
    catch {
        if ($_.Exception.Message -eq 'UNEXPECTED_ACCEPTANCE') { throw }
        Check ($_.Exception.Message -match $pattern) ('Unexpected rejection: '+$_.Exception.Message+'; expected '+$pattern)
    }
}
function Protected($f) {
    $h=@{}
    foreach ($base in @($f.game,$f.saves)) {
        foreach ($x in Get-ChildItem -LiteralPath $base -Recurse -File) {
            if ($x.FullName -ne $f.target) { $h[$x.FullName]=Sha $x.FullName }
        }
    }
    return $h
}
function Unchanged($f,$before) {
    $after=Protected $f
    Check ($before.Count -eq $after.Count) 'Protected synthetic file set changed.'
    foreach ($k in $before.Keys) { Check ($after.ContainsKey($k) -and $after[$k] -ceq $before[$k]) ('Protected synthetic file changed: '+$k) }
}
function RelinkTests($f) {
    $t=Get-Content -LiteralPath (Join-Path $f.build 'tests.json') -Raw | ConvertFrom-Json
    $t.build_sha256=Sha (Join-Path $f.build 'build.json')
    PutJson (Join-Path $f.build 'tests.json') $t
}
function EditTxn($f,[scriptblock]$edit) {
    $p=Join-Path $f.recovery 'transaction.json'
    $t=Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
    & $edit $t
    PutJson $p $t
    Put (Join-Path $f.recovery 'transaction.sha256') (Sha $p)
}
function Case([string]$name,[scriptblock]$body) {
    $start=$script:checks
    try { & $body; $rows.Add(@{name=$name;status='PASS';checks=$script:checks-$start}) }
    catch { $rows.Add(@{name=$name;status='FAIL';checks=$script:checks-$start;error=$_.Exception.Message}) }
}

$normal=NewFixture 'normal'
$original=Protected $normal
Case 'Validate is read-only' {
    $result=(Call $normal 'Validate') | ConvertFrom-Json
    Check ($result.status -eq 'VALIDATED_GD1_ADD_ONLY') 'Validate status differs.'
    Check (!(Test-Path -LiteralPath $normal.target) -and !(Test-Path -LiteralPath $normal.recovery)) 'Validate mutated installation.'
    Unchanged $normal $original
}
Case 'Install adds exact sole diagnostic and retains originals' {
    $null=Call $normal 'Install'
    Check ((Sha $normal.target) -ceq $expectedSha) 'Installed bytes differ.'
    $receipt=Get-Content -LiteralPath (Join-Path $normal.recovery 'install_receipt.json') -Raw | ConvertFrom-Json
    Check ($receipt.additions -eq 1 -and $receipt.replacements -eq 0 -and $receipt.protected_save_files -eq 2 -and $receipt.protected_cache_files -eq 1) 'Receipt counts differ.'
    Unchanged $normal $original
}
Case 'ValidateRollback is read-only' {
    $result=(Call $normal 'ValidateRollback') | ConvertFrom-Json
    Check ($result.status -eq 'VALIDATED_GD1_ROLLBACK' -and $result.target_present) 'Rollback validation differs.'
    Check ((Sha $normal.target) -ceq $expectedSha -and !(Test-Path -LiteralPath (Join-Path $normal.recovery 'rollback_receipt.json'))) 'Rollback validation mutated installation.'
    Unchanged $normal $original
}
Case 'Rollback moves only diagnostic recoverably' {
    $null=Call $normal 'Rollback'
    Check (!(Test-Path -LiteralPath $normal.target)) 'Target remains after rollback.'
    Check ((Sha (Join-Path $normal.recovery ('removed_'+$archiveName))) -ceq $expectedSha) 'Recoverable removed bytes differ.'
    Check ((Sha (Join-Path $normal.recovery $archiveName)) -ceq $expectedSha) 'Recovery source changed.'
    Unchanged $normal $original
}
Case 'Second rollback refused' { Refuse (Args $normal 'Rollback') 'Already rolled back' }
Case 'Existing target refused without overwrite' {
    $f=NewFixture 'target_exists'; Put $f.target 'do not overwrite'
    Refuse (Args $f 'Install') 'already present'
    Check ((Get-Content -LiteralPath $f.target -Raw) -ceq 'do not overwrite') 'Existing target overwritten.'
    Check (!(Test-Path -LiteralPath $f.recovery)) 'Recovery created on refused install.'
}
Case 'Existing recovery refused' {
    $f=NewFixture 'recovery_exists'; [void](New-Item -ItemType Directory -Path $f.recovery)
    Refuse (Args $f 'Install') 'New recovery directory required'
    Check (!(Test-Path -LiteralPath $f.target)) 'Target created despite existing recovery.'
}
Case 'Bad archive hash refused' {
    $f=NewFixture 'bad_archive'; Put (Join-Path $f.build $archiveName) 'not archive'
    Refuse (Args $f 'Install') 'Hash mismatch'
    Check (!(Test-Path -LiteralPath $f.target)) 'Bad archive installed.'
}
Case 'Extra resource scope refused' {
    $f=NewFixture 'extra_resource'; $m=Get-Content -LiteralPath (Join-Path $f.build 'build.json') -Raw | ConvertFrom-Json
    $m.resource_count=2; PutJson (Join-Path $f.build 'build.json') $m; RelinkTests $f
    Refuse (Args $f 'Install') 'manifest scope mismatch'
}
Case 'Wrong target depot refused' {
    $f=NewFixture 'wrong_depot'; $m=Get-Content -LiteralPath (Join-Path $f.build 'build.json') -Raw | ConvertFrom-Json
    $m.resource_depot='ep1\fx\quest\q307\q307_dizzy_wakeup.effect'; PutJson (Join-Path $f.build 'build.json') $m; RelinkTests $f
    Refuse (Args $f 'Install') 'manifest scope mismatch'
}
Case 'Archive filename traversal refused' {
    $f=NewFixture 'wrong_archive'; $m=Get-Content -LiteralPath (Join-Path $f.build 'build.json') -Raw | ConvertFrom-Json
    $m.archive='../elsewhere.archive'; PutJson (Join-Path $f.build 'build.json') $m; RelinkTests $f
    Refuse (Args $f 'Install') 'manifest scope mismatch'
}
Case 'Unlinked tests refused' {
    $f=NewFixture 'bad_tests_link'; $t=Get-Content -LiteralPath (Join-Path $f.build 'tests.json') -Raw | ConvertFrom-Json
    $t.build_sha256=('0'*64); PutJson (Join-Path $f.build 'tests.json') $t
    Refuse (Args $f 'Install') 'Matching tests/readback required'
}
Case 'Failed tests status refused' {
    $f=NewFixture 'bad_tests_status'; $t=Get-Content -LiteralPath (Join-Path $f.build 'tests.json') -Raw | ConvertFrom-Json
    $t.status='FAIL'; PutJson (Join-Path $f.build 'tests.json') $t
    Refuse (Args $f 'Install') 'Matching tests/readback required'
}
Case 'Outside fixture game root refused' {
    $f=NewFixture 'outside_game'; $p=Args $f 'Validate'; $p.GameRoot=$ws
    Refuse $p 'Outside approved root'
}
Case 'Outside fixture saves root refused' {
    $f=NewFixture 'outside_saves'; $p=Args $f 'Validate'; $p.SaveRoot=$ws
    Refuse $p 'Outside approved root'
}
Case 'Outside fixture build refused' {
    $f=NewFixture 'outside_build'; $p=Args $f 'Validate'; $p.Build=$candidateRoot
    Refuse $p 'Outside approved root'
}
Case 'Outside fixture recovery refused' {
    $f=NewFixture 'outside_recovery'; $p=Args $f 'Install'; $p.RecoveryRoot=$ws
    Refuse $p 'Outside approved root'
}
Case 'Injected post-copy failure remains recoverable' {
    $f=NewFixture 'interrupted'; $before=Protected $f; $p=Args $f 'Install'; $p.FailAfterCopy=$true
    Refuse $p 'Injected fixture failure after copy'
    Check ((Sha $f.target) -ceq $expectedSha) 'Expected interrupted target absent/wrong.'
    Check ((Test-Path -LiteralPath (Join-Path $f.recovery 'failure.json')) -and !(Test-Path -LiteralPath (Join-Path $f.recovery 'install_receipt.json'))) 'Failure evidence incorrect.'
    $null=Call $f 'ValidateRollback'; $null=Call $f 'Rollback'
    Check (!(Test-Path -LiteralPath $f.target)) 'Interrupted target remains after recovery.'
    Unchanged $f $before
}
Case 'Absent target after interruption handled without recreation' {
    $f=NewFixture 'absent_target'; $before=Protected $f; $p=Args $f 'Install'; $p.FailAfterCopy=$true
    Refuse $p 'Injected fixture failure after copy'
    $saved=Join-Path $f.base 'observed_interrupted_target.archive'
    [IO.File]::Move($f.target,$saved,$false)
    $result=(Call $f 'ValidateRollback') | ConvertFrom-Json
    Check (!$result.target_present) 'Absent-target status wrong.'
    $null=Call $f 'Rollback'
    $receipt=Get-Content -LiteralPath (Join-Path $f.recovery 'rollback_receipt.json') -Raw | ConvertFrom-Json
    Check (!$receipt.diagnostic_moved_recoverably -and !(Test-Path -LiteralPath $f.target)) 'Absent target unnecessarily recreated/moved.'
    Check ((Sha $saved) -ceq $expectedSha) 'Interrupted target evidence lost.'
    Unchanged $f $before
}
Case 'Tampered target blocks rollback without moving it' {
    $f=NewFixture 'tampered_target'; $null=Call $f 'Install'; Put $f.target 'foreign replacement'
    Refuse (Args $f 'Rollback') 'Hash mismatch'
    Check ((Get-Content -LiteralPath $f.target -Raw) -ceq 'foreign replacement') 'Foreign replacement touched.'
    Check (!(Test-Path -LiteralPath (Join-Path $f.recovery ('removed_'+$archiveName)))) 'Tampered target moved.'
}
Case 'Tampered staged recovery blocks rollback' {
    $f=NewFixture 'tampered_staged'; $null=Call $f 'Install'; Put (Join-Path $f.recovery $archiveName) 'bad stage'
    Refuse (Args $f 'Rollback') 'Hash mismatch'
    Check ((Sha $f.target) -ceq $expectedSha) 'Installed target changed during rejected recovery.'
}
Case 'Tampered transaction digest blocks rollback' {
    $f=NewFixture 'tampered_transaction'; $null=Call $f 'Install'
    $p=Join-Path $f.recovery 'transaction.json'; Put $p ((Get-Content -LiteralPath $p -Raw)+' ')
    Refuse (Args $f 'Rollback') 'Hash mismatch'
    Check ((Sha $f.target) -ceq $expectedSha) 'Target moved despite bad transaction digest.'
}
Case 'Transaction game identity mismatch refused with updated digest' {
    $f=NewFixture 'identity_game'; $null=Call $f 'Install'
    EditTxn $f { param($t) $t.game_root='C:\not_the_game' }
    Refuse (Args $f 'Rollback') 'Recovery identity mismatch'
}
Case 'Transaction target traversal refused with updated digest' {
    $f=NewFixture 'identity_target'; $null=Call $f 'Install'
    EditTxn $f { param($t) $t.relative='../Unrelated.archive' }
    Refuse (Args $f 'Rollback') 'Recovery identity mismatch'
}
Case 'Existing recoverable destination prevents overwrite' {
    $f=NewFixture 'removed_exists'; $null=Call $f 'Install'
    $p=Join-Path $f.recovery ('removed_'+$archiveName); Put $p 'keep previous evidence'
    Refuse (Args $f 'Rollback') 'Recovery destination already exists'
    Check ((Get-Content -LiteralPath $p -Raw) -ceq 'keep previous evidence') 'Recovery evidence overwritten.'
}
$linkFixture=NewFixture 'reparse'
$junction=Join-Path $linkFixture.base 'game_link'
try {
    [void](New-Item -ItemType Junction -Path $junction -Target $linkFixture.game -ErrorAction Stop)
    Case 'Reparse game root refused' {
        $p=Args $linkFixture 'Validate'; $p.GameRoot=$junction
        Refuse $p 'Reparse path refused'
    }
} catch {
    $rows.Add(@{name='Reparse game root refused';status='SKIPPED_ENVIRONMENT';error=$_.Exception.Message})
}

$failed=@($rows | Where-Object status -eq 'FAIL')
$skipped=@($rows | Where-Object status -eq 'SKIPPED_ENVIRONMENT')
$report=@{
    status=if($failed.Count){'FAIL'}elseif($skipped.Count){'PASS_WITH_ENVIRONMENT_SKIP'}else{'PASS'}
    created_utc=[DateTime]::UtcNow.ToString('o'); fixture_root=$run
    fixture_only=$true; game_save_cache_settings_writes=$false
    deploy_sha256=Sha $deploy; test_sha256=Sha $PSCommandPath
    candidate_build_sha256=Sha (Join-Path $candidateRoot 'build.json')
    cases=$rows.Count; checks=$checks; skipped=$skipped.Count; failed=$failed.Count; results=@($rows)
    limitations=@('Synthetic protected files, not a game run.','Fixtures intentionally retained; no recursive deletion.','No code compilation needed for archive-only diagnostic.')
}
PutJson (Join-Path $run 'deployment_tests.json') $report
Write-Output ((@{status=$report.status;report=(Join-Path $run 'deployment_tests.json');cases=$rows.Count;checks=$checks;skipped=$skipped.Count;failed=$failed.Count}) | ConvertTo-Json)
if($failed.Count){throw 'Deployment fixture failures; inspect retained report.'}
