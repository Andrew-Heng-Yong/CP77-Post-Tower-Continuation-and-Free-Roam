param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$root=Join-Path $WorkspaceRoot 'research/gig_restoration/gig_batch_u9'
if(Test-Path -LiteralPath (Join-Path $root 'install_receipt.json')){throw 'Installed U9 evidence pinned'}
$m=Get-Content -LiteralPath (Join-Path $root 'manifest.json') -Raw|ConvertFrom-Json
$installer=Join-Path $PSScriptRoot 'deploy_gig_batch_u9.ps1'
$refusals=[Collections.Generic.List[string]]::new();$fixtures=[Collections.Generic.List[string]]::new()
function NewFixtureU9([string]$name){
 $f=Join-Path $root ('fixture_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'_'+$name)
 $g=Join-Path $f 'game';$a=Join-Path $f 'audit';New-Item -ItemType Directory -Force $g,$a|Out-Null
 $p=Join-Path $g 'r6/scripts/PTFR_FixtureProtected/sentinel.reds';New-Item -ItemType Directory -Force (Split-Path -Parent $p)|Out-Null
 [IO.File]::WriteAllText($p,'// Protected fixture sentinel',[Text.UTF8Encoding]::new($false))
 $fixtures.Add($f);return @{root=$f;game=$g;audit=$a;protected=$p;hash=R5Hash $p}
}
function RefusedU9([string]$name,$f,[scriptblock]$action){
 $refused=$false;try{& $action|Out-Null}catch{$refused=$true}
 if(-not $refused){throw "Expected refusal: $name"};$refusals.Add($name);R5Match $f.protected $f.hash
}
function RecoverCheckedU9($f){
 & $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $f.game -AuditDirectory $f.audit -Mode ValidateRollback|Out-Null
 & $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $f.game -AuditDirectory $f.audit -Mode Rollback|Out-Null
 $r=Get-Content -LiteralPath (Join-Path $f.audit 'rollback_receipt.json') -Raw|ConvertFrom-Json
 foreach($x in $m.files){if(Test-Path -LiteralPath (Join-Path $f.game $x.relative)){throw 'Addition remained after recovery'}}
 foreach($x in $r.files){R5Match (R5Within (Join-Path $r.recoverable $x.relative) $r.recoverable) $x.sha256}
 R5Match $f.protected $f.hash;return $r
}
$f=NewFixtureU9 'normal';$game=$f.game;$audit=$f.audit
RefusedU9 'root outside canonical/fixture scope' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot (Join-Path $WorkspaceRoot 'wrong_game') -AuditDirectory $audit -Mode ValidateInstall}
RefusedU9 'fixture audit outside paired root' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $root -Mode ValidateInstall}
& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode ValidateInstall|Out-Null
$first=$m.files[0];$firstTarget=Join-Path $game $first.relative
New-Item -ItemType Directory -Force (Split-Path -Parent $firstTarget)|Out-Null
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot $first.source) -Destination $firstTarget
RefusedU9 'pre-existing additive target' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode Install}
Move-Item -LiteralPath (R5Within $firstTarget $game) -Destination (R5Within (Join-Path $f.root 'held-preexisting.archive') $f.root)
# A foreign XL registering the same depot must not be hidden as an own entry.
$foreign=Join-Path $game 'archive/pc/mod/Foreign_U9_SameDepot.archive.xl'
$xl=@($m.files|Where-Object relative -like '*.xl')[0]
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot $xl.source) -Destination $foreign
RefusedU9 'foreign XL exact-depot collision on install' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode ValidateInstall}
Move-Item -LiteralPath (R5Within $foreign $game) -Destination (R5Within (Join-Path $f.root 'held-foreign.xl') $f.root)
& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode Install|Out-Null
foreach($x in $m.files){R5Match (Join-Path $game $x.relative) $x.sha256}
RefusedU9 'duplicate install/receipt' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode Install}
& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback|Out-Null
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot $xl.source) -Destination $foreign
RefusedU9 'foreign XL exact-depot collision on rollback' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode ValidateRollback}
Move-Item -LiteralPath (R5Within $foreign $game) -Destination (R5Within (Join-Path $f.root 'held-foreign-afterinstall.xl') $f.root)
[IO.File]::WriteAllText($firstTarget,'fixture drift',[Text.UTF8Encoding]::new($false))
RefusedU9 'rollback refuses target drift' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode Rollback}
Copy-Item -LiteralPath (Join-Path $WorkspaceRoot $first.source) -Destination $firstTarget
# Interruption after two verified moves; the same recovery plan must resume.
RefusedU9 'injected partial rollback' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode Rollback -FixtureFailAfterMoves 2}
$recovery=RecoverCheckedU9 $f
RefusedU9 'repeated rollback' $f {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $game -AuditDirectory $audit -Mode Rollback}
# Partial install has no success receipt, but a pre-write transaction exists.
$partial=NewFixtureU9 'partial';$pg=$partial.game;$pa=$partial.audit
RefusedU9 'injected partial install' $partial {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $pg -AuditDirectory $pa -Mode Install -FixtureFailAfterCopies 3}
if(Test-Path -LiteralPath (Join-Path $pa 'install_receipt.json')){throw 'Partial install falsely successful'}
if(-not (Test-Path -LiteralPath (Join-Path $pa 'install_transaction.json'))){throw 'Missing partial recovery transaction'}
RefusedU9 'blind rerun after partial install' $partial {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $pg -AuditDirectory $pa -Mode Install}
RefusedU9 'injected partial-install recovery interruption' $partial {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $pg -AuditDirectory $pa -Mode Rollback -FixtureFailAfterMoves 1}
$partialRecovery=RecoverCheckedU9 $partial
if(@($partialRecovery.files).Count -ne 3 -or -not $partialRecovery.partial_install){throw 'Partial recovery scope wrong'}
# Harmless junction wholly in the disposable fixture remains as evidence.
$jf=NewFixtureU9 'reparse';$jg=$jf.game;$ja=$jf.audit
$redirect=Join-Path $jf.root 'redirect';New-Item -ItemType Directory -Force $redirect|Out-Null
$link=Join-Path $jg 'archive';New-Item -ItemType Junction -Path $link -Target $redirect|Out-Null
RefusedU9 'reparse target parent' $jf {& $installer -WorkspaceRoot $WorkspaceRoot -GameRoot $jg -AuditDirectory $ja -Mode ValidateInstall}
if(@(Get-ChildItem -LiteralPath $redirect -Recurse -File).Count){throw 'Reparse target was written'}
$helperPins=[ordered]@{}
foreach($name in @('shark_b7_2_helpers.ps1','gig_family_b7_1_xl.ps1','afterlife_faces_r5_deployment.ps1')){$helperPins['tools/'+$name]=R5Hash (Join-Path $PSScriptRoot $name)}
R5Json (Join-Path $root 'deployment_tests.json') ([ordered]@{
 status='PASS_U9_ADDITIVE_RECOVERABLE_FIXTURE';fixtures=$fixtures.ToArray()
 additions=$m.files.Count;replacements=0;recoverable=$recovery.recoverable;partial_recoverable=$partialRecovery.recoverable
 protected_sentinel_unchanged=$true;negative_cases=$refusals.ToArray();partial_install_recovery=$true;partial_rollback_resume=$true;exact_foreign_xl_collision_refused=$true;reparse_refusal=$true
 installer_sha256=R5Hash $installer;test_sha256=R5Hash $PSCommandPath;helper_pins=$helperPins
 tests_sha256=R5Hash (Join-Path $root 'tests.json');native_engine_proof=$false
})
'PASS_U9_ADDITIVE_RECOVERABLE_FIXTURE'
