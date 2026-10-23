param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$AuditDirectory='',[switch]$Rollback,[switch]$ValidateOnly)
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
if($Rollback -and $ValidateOnly){throw 'Choose rollback OR validation'}
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\')
$audit=if($AuditDirectory){R5Within $AuditDirectory $workspace}else{Join-Path $workspace 'research\afterlife_world\faces_r5'}
$receipt=Get-Content -LiteralPath (Join-Path $audit 'install_receipt.json') -Raw|ConvertFrom-Json -Depth 12
if($receipt.status -ne 'INSTALLED_AFTERLIFE_FACES_R5_LIVE_PENDING' -or $receipt.files.Count -ne 2 -or $receipt.replacements -ne 0){throw 'Unexpected receipt'}
if(@(Compare-Object @(R5Scope) @($receipt.files.relative)).Count){throw 'Rollback scope changed'}
$game=[IO.Path]::GetFullPath($receipt.game_root).TrimEnd('\')
R5Closed
$targets=@($receipt.files|ForEach-Object {R5Within (Join-Path $game $_.relative) $game})
foreach($file in $receipt.files){R5Match (R5Within (Join-Path $game $file.relative) $game) $file.sha256}
$protected=R5Snapshot $game $targets
if(-not $Rollback){
 $result=@{status='R5_ROLLBACK_PREFLIGHT_ONLY';recoverable_removals=2;game_unchanged=$true;protected_files=$protected.Count}
 R5Json (Join-Path $audit 'rollback_preflight.json') $result
 $result|ConvertTo-Json;return
}
$stash=R5Within (Join-Path $audit ('removed_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))) $workspace
$moved=[Collections.Generic.List[object]]::new()
try{
 foreach($file in $receipt.files){
  R5Closed;$from=R5Within (Join-Path $game $file.relative) $game;$to=R5Within (Join-Path $stash $file.relative) $stash
  R5Match $from $file.sha256;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null
  Move-Item -LiteralPath $from -Destination $to;$moved.Add($file);R5Match $to $file.sha256
 }
 R5Unchanged $protected
}catch{
 $failure=$_.Exception.Message;R5Closed
 foreach($file in $moved){$from=R5Within (Join-Path $stash $file.relative) $stash;$to=R5Within (Join-Path $game $file.relative) $game;if(Test-Path -LiteralPath $to){throw 'Recovery destination appeared; inspect rollback stash'};R5Match $from $file.sha256;Move-Item -LiteralPath $from -Destination $to}
 throw $failure
}
$result=@{status='R5_REMOVED_RECOVERABLY';stash=$stash;removed=2;other_files_unchanged=$protected.Count}
R5Json (Join-Path $audit 'rollback_receipt.json') $result
$result|ConvertTo-Json
