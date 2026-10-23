param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$AuditDirectory='',
 [switch]$Install,
 [switch]$ValidateOnly
)
# Default is read-only game preflight. Exactly two additive script sources.
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
if($Install -and $ValidateOnly){throw 'Choose installation OR validation'}
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$sourceAudit=Join-Path $workspace 'research\afterlife_world\faces_r5'
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{$sourceAudit}
New-Item -ItemType Directory -Force $audit|Out-Null
$tests=Get-Content -LiteralPath (Join-Path $sourceAudit 'tests.json') -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_R5_OFFLINE_NOT_INSTALLED_NOT_LIVE' -or -not $tests.real_redscript_compilation){throw 'Missing R5 offline pass'}
R5Match (Join-Path $sourceAudit 'catalog.json') $tests.catalog_manifest_sha256
R5Match (Join-Path $workspace 'tools\build_afterlife_faces_r5.py') $tests.builder_sha256
R5Match (Join-Path $workspace 'tools\test_afterlife_faces_r5.py') $tests.validator_sha256
if(-not (Test-Path -LiteralPath (Join-Path $game 'r6\cache\final.redscripts') -PathType Leaf)){throw 'Unexpected game root'}
if(@(Compare-Object @(R5Scope) @($tests.files.relative)).Count -or $tests.files.Count -ne 2){throw 'Unexpected payload scope'}
$expected=[ordered]@{}
foreach($receipt in @('install_receipt.json','population_r2\install_receipt.json','idles_r3\install_receipt.json')){
 $prior=Get-Content -LiteralPath (Join-Path $workspace ('research\afterlife_world\'+$receipt)) -Raw|ConvertFrom-Json
 foreach($file in $prior.files){$expected[$file.relative]=$file.sha256}
}
R5Closed
foreach($path in $expected.Keys){R5Match (R5Within (Join-Path $game $path) $game) $expected[$path]}
$payloads=@($tests.files|ForEach-Object {
 $source=R5Within (Join-Path $workspace $_.source) $workspace
 $target=R5Within (Join-Path $game $_.relative) $game
 R5Match $source $_.sha256
 if(Test-Path -LiteralPath $target){throw "Additive destination exists: $target"}
 @{relative=$_.relative;source=$source;target=$target;sha256=$_.sha256}
})
$protected=R5Snapshot $game
R5Closed;R5Unchanged $protected
$preflight=@{status='R5_PREFLIGHT_ONLY_GAME_UNCHANGED';additions=2;replacements=0;protected_files=$protected.Count;game_running=$false;baseline_afterlife_files=$expected.Count}
R5Json (Join-Path $audit 'preflight.json') $preflight
if(-not $Install){$preflight|ConvertTo-Json;return}
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Receipt exists; reconcile before reinstalling'}
$written=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $payloads){
  R5Closed;R5Match $file.source $file.sha256
  if(Test-Path -LiteralPath $file.target){throw 'Destination appeared during installation'}
  New-Item -ItemType Directory -Force (Split-Path $file.target)|Out-Null
  [IO.File]::Copy($file.source,$file.target,$false)
  $written.Add($file);R5Match $file.target $file.sha256
 }
 R5Closed;R5Unchanged $protected
 $receipt=[ordered]@{status='INSTALLED_AFTERLIFE_FACES_R5_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');game_root=$game;additions=2;replacements=0;protected_files=$protected.Count;protected_hashes=$protected;files=@($payloads|ForEach-Object {@{relative=$_.relative;sha256=$_.sha256}});tests_sha256=(R5Hash (Join-Path $sourceAudit 'tests.json'));installer_sha256=(R5Hash $PSCommandPath);save_file_writes=0;story_writes=0;live_tested=$false}
 R5Json (Join-Path $audit 'install_receipt.json') $receipt
 [pscustomobject]$receipt|Select-Object status,utc,additions,replacements,protected_files|ConvertTo-Json
}catch{
 $failure=$_.Exception.Message;$errors=[Collections.Generic.List[string]]::new()
 $recovery=R5Within (Join-Path $audit ('failed_install_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
 if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){$errors.Add('Game started; recovery deferred')}
 else{foreach($file in $written){try{
  if(Test-Path -LiteralPath $file.target){R5Match $file.target $file.sha256;$dest=R5Within (Join-Path $recovery $file.relative) $recovery;New-Item -ItemType Directory -Force (Split-Path $dest)|Out-Null;Move-Item -LiteralPath $file.target -Destination $dest}
 }catch{$errors.Add($_.Exception.Message)}}}
 R5Json (Join-Path $audit 'install_failure.json') @{failure=$failure;recovery=$recovery;errors=@($errors)}
 throw ($failure+'; recovery errors: '+($errors -join '; '))
}
