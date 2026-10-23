param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$PreflightOnly,[switch]$Rollback)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$out=Join-Path $WorkspaceRoot 'build\RestorationBaseline_R1'
$receiptPath=Join-Path $out 'install_receipt.json'
$root=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
if(-not (Test-Path -LiteralPath (Join-Path $root 'archive\pc\content') -PathType Container)){throw 'Unexpected game root'}
function AssertClosed(){if(@(Get-Process -Name Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk must be fully closed'}}
function Target([string]$relative){
 $p=[IO.Path]::GetFullPath((Join-Path $root $relative))
 if(-not $p.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Target escapes game root'}
 return $p
}
AssertClosed
if($Rollback){
 $receipt=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json
 if($receipt.status -ne 'INSTALLED_UNVERIFIED'){throw 'No active installation receipt'}
 foreach($f in $receipt.changed){
  $dst=Target $f.path
  if((Get-FileHash -LiteralPath $dst).Hash -ne $f.sha256){throw "Changed since install; refuse rollback: $dst"}
  if($f.before -and (Get-FileHash -LiteralPath (Join-Path $receipt.backup $f.path)).Hash -ne $f.before){throw 'Rollback backup mismatch'}
 }
 if($PreflightOnly){'ROLLBACK_PREFLIGHT_OK';return}
 AssertClosed
 foreach($f in $receipt.changed){
  $dst=Target $f.path
  if($f.before){Copy-Item -LiteralPath (Join-Path $receipt.backup $f.path) -Destination $dst}
  else{Remove-Item -LiteralPath $dst} # Only the two exact new files, never a directory.
 }
 $receipt.status='ROLLED_BACK';$receipt|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $receiptPath
 'Rollback restored 12 previous files and removed only the 2 Baseline-R1 additions. Backups retained.';return
}
$manifestPath=Join-Path $out 'manifest.json'
$m=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$tests=Get-Content -LiteralPath (Join-Path $out 'tests.json') -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS' -or $tests.manifestSha256 -ne (Get-FileHash -LiteralPath $manifestPath).Hash -or $m.version -ne 'Baseline-R1'){throw 'Validation does not match package'}
$changed=@($m.files|Where-Object action -ne 'preserved')
if($changed.Count -ne 14){throw 'Unexpected integration scope'}
foreach($f in $m.files){
 $src=Join-Path (Join-Path $out 'game') $f.path;$dst=Target $f.path
 if((Get-FileHash -LiteralPath $src).Hash -ne $f.sha256){throw 'Package changed after tests'}
 if($f.before){if((Get-FileHash -LiteralPath $dst).Hash -ne $f.before){throw "Installed baseline differs: $dst"}}
 elseif(Test-Path -LiteralPath $dst){throw "New target already exists: $dst"}
}
if($PreflightOnly){'PREFLIGHT_OK: 12 exact backed-up replacements, 2 additions; all 25 archives preserved';return}
AssertClosed
$backup=Join-Path $out ('rollback_'+(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ'))
New-Item -ItemType Directory -Path $backup|Out-Null
foreach($f in $changed){if($f.before){
 $dst=Join-Path $backup $f.path;New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath (Target $f.path) -Destination $dst
 if((Get-FileHash -LiteralPath $dst).Hash -ne $f.before){throw 'Backup verification failed'}
}}
$done=[Collections.Generic.List[object]]::new()
try{
 AssertClosed
 foreach($f in $changed){
  $dst=Target $f.path;New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst)|Out-Null
  $done.Add($f)
  Copy-Item -LiteralPath (Join-Path (Join-Path $out 'game') $f.path) -Destination $dst
  if((Get-FileHash -LiteralPath $dst).Hash -ne $f.sha256){throw 'Installed hash mismatch'}
 }
 foreach($f in $m.files){if((Get-FileHash -LiteralPath (Target $f.path)).Hash -ne $f.sha256){throw 'Final verification failed'}}
}catch{
 foreach($f in $done){$dst=Target $f.path;if($f.before){Copy-Item -LiteralPath (Join-Path $backup $f.path) -Destination $dst}elseif(Test-Path -LiteralPath $dst){Remove-Item -LiteralPath $dst}}
 throw
}
$receipt=[ordered]@{status='INSTALLED_UNVERIFIED';version='Baseline-R1';timeUtc=(Get-Date).ToUniversalTime().ToString('o');backup=$backup;changed=$changed;verifiedFiles=$m.files.Count;preservedArchives=25;savesModified=$false;newNativeOwners=0;manifestSha256=(Get-FileHash -LiteralPath $manifestPath).Hash;live='PENDING_COMBINED_SMOKE_CHECK'}
[IO.File]::WriteAllText($receiptPath,($receipt|ConvertTo-Json -Depth 8))
[pscustomobject]@{status=$receipt.status;changed=$changed.Count;verifiedFiles=$m.files.Count;backup=$backup;savesModified=$false}
