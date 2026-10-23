param([Parameter(Mandatory)][string]$RecoveryRoot)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$receipt=Get-Content (Join-Path $RecoveryRoot 'install_receipt.json') -Raw|ConvertFrom-Json
$txn=Get-Content (Join-Path $RecoveryRoot 'transaction.json') -Raw|ConvertFrom-Json
$m=Get-Content -LiteralPath $txn.manifest -Raw|ConvertFrom-Json
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Match([string]$p,[string]$h){if((Hash $p) -cne $h){throw "Post-install hash drift: $p"}}
Match $txn.manifest $receipt.manifest_sha256
foreach($f in $m.package){Match (Join-Path $txn.game_root $f.relative) $f.sha256}
foreach($f in $m.protected){$root=if($f.kind -eq 'save'){$txn.save_root}else{$txn.game_root};Match (Join-Path $root $f.relative) $f.sha256}
$backups=0
foreach($u in $m.units){
 $root=if($u.kind -eq 'save'){$txn.save_root}else{$txn.game_root}
 if(Test-Path -LiteralPath (Join-Path $root $u.relative)){throw 'Original cleanup target still active'}
 $base=Join-Path $RecoveryRoot ($u.kind+'/'+$u.relative)
 foreach($f in $u.files){$p=if($f.path -ceq '.'){$base}else{Join-Path $base $f.path};Match $p $f.sha256;$backups++}
}
foreach($f in $txn.keep_files){Match (Join-Path $RecoveryRoot ('retained_source/'+$txn.keep_save+'/'+$f.path)) $f.sha256}
$slots=@(Get-ChildItem -LiteralPath $txn.save_root -Directory|ForEach-Object {$_.Name})
if($slots.Count -ne 1 -or $slots[0] -cne 'ManualSave-10'){throw 'Unexpected active save set'}
$scripts=@(Get-ChildItem -LiteralPath (Join-Path $txn.game_root 'r6/scripts') -Directory -Filter 'PTFR*'|ForEach-Object {$_.Name})
$cets=@(Get-ChildItem -LiteralPath (Join-Path $txn.game_root 'bin/x64/plugins/cyber_engine_tweaks/mods') -Directory -Filter 'PTFR*'|ForEach-Object {$_.Name})
$archives=@(Get-ChildItem -LiteralPath (Join-Path $txn.game_root 'archive/pc/mod') -File -Filter 'TowerContinued*'|ForEach-Object {$_.Name})
if($scripts.Count -ne 1 -or $scripts[0] -cne 'PTFR_PreAlpha' -or $cets.Count -ne 1 -or $cets[0] -cne 'PTFR_PreAlpha' -or $archives.Count -ne 2){throw 'Consolidated installation shape mismatch'}
$result=[ordered]@{status='PASS_INSTALLED_AND_RECOVERY_HASH_AUDIT_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');recovery=$RecoveryRoot;package_files_verified=@($m.package).Count;protected_files_verified=@($m.protected).Count;archived_original_files_verified=$backups;archived_game_units=@($m.units|Where-Object kind -eq 'game').Count;archived_save_folders=@($m.units|Where-Object kind -eq 'save').Count;active_save=$slots[0];active_scripts=$scripts;active_cet=$cets;active_archive=$archives;manifest=$txn.manifest;manifest_sha256=(Hash $txn.manifest);installer_sha256=(Hash (Join-Path $PSScriptRoot 'deploy.ps1'));save_bytes_modified=$false;cache_modified=$false;live_test='PENDING'}
[IO.File]::WriteAllText((Join-Path $ws 'research/pre_alpha_clean/install_audit.json'),($result|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
