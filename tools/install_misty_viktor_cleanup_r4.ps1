param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',[switch]$ValidateOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$game=[IO.Path]::GetFullPath($GameRoot).TrimEnd('\')
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$r3=Get-Content (Join-Path $audit 'street_r3_install_receipt.json') -Raw|ConvertFrom-Json
$m=Get-Content (Join-Path $audit 'cleanup_r4_manifest.json') -Raw|ConvertFrom-Json
$tests=Get-Content (Join-Path $audit 'cleanup_r4_tests.json') -Raw|ConvertFrom-Json
if($tests.status -ne 'PASS_R4_OFFLINE_NOT_INSTALLED_OR_LIVE' -or $tests.archive_sha256 -ne $m.sha256 -or $tests.xl_sha256 -ne $m.xl_sha256){throw 'R4 offline tests missing/stale'}
if($r3.status -ne 'INSTALLED_R3_PASSIVE_STREET_IDLE_OPTIN_LIVE_PENDING'){throw 'R3 installation receipt changed'}
$files=@(
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive';source=$m.archive;hash=$m.sha256},
 [pscustomobject]@{relative='archive\pc\mod\TowerContinued_MistyViktorShellOptIn.archive.xl';source=($m.archive+'.xl');hash=$m.xl_sha256},
 [pscustomobject]@{relative='bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_MistyViktor_World\init.lua';source=(Join-Path $WorkspaceRoot 'diagnostics\PTFR_MistyViktor_World\init.lua');hash=$tests.probe_sha256}
)
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Cyberpunk running; installation deferred'}
$targetHashes=[ordered]@{}
for($i=0;$i -lt $files.Count;$i++){
 $f=$files[$i];$target=[IO.Path]::GetFullPath((Join-Path $game $f.relative))
 if(-not $target.StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Game target escaped root'}
 if($target -ne [IO.Path]::GetFullPath((Join-Path $game $r3.files[$i].relative))){throw 'R3 target receipt mismatch'}
 if((Get-FileHash -LiteralPath $target).Hash -ne $r3.files[$i].sha256){throw "Installed R3 changed: $target"}
 if((Get-FileHash -LiteralPath $f.source).Hash -ne $f.hash){throw "R4 source changed: $($f.source)"}
 $targetHashes[$target]=$r3.files[$i].sha256
}
$protected=[ordered]@{}
$archiveDir=Join-Path $game 'archive\pc\mod'
foreach($p in (Get-ChildItem -LiteralPath $archiveDir -File -Filter 'TowerContinued*')){if(-not $targetHashes.Contains($p.FullName)){$protected[$p.FullName]=(Get-FileHash -LiteralPath $p.FullName).Hash}}
foreach($root in @((Join-Path $game 'r6\scripts'),(Join-Path $game 'bin\x64\plugins\cyber_engine_tweaks\mods'))){
 foreach($dir in (Get-ChildItem -LiteralPath $root -Directory -Filter 'PTFR_*')){
  foreach($p in (Get-ChildItem -LiteralPath $dir.FullName -Recurse -File)){if(-not $targetHashes.Contains($p.FullName)){$protected[$p.FullName]=(Get-FileHash -LiteralPath $p.FullName).Hash}}
 }
}
if($ValidateOnly){[pscustomobject]@{status='VALIDATED_ONLY_NOT_INSTALLED';r3_targets=$files.Count;protected_files=$protected.Count;game_running=$false}|ConvertTo-Json;return}
$backup=Join-Path $audit ('rollback_r3_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Force -Path $backup|Out-Null
for($i=0;$i -lt $files.Count;$i++){
 $target=Join-Path $game $files[$i].relative
 $saved=Join-Path $backup $files[$i].relative
 New-Item -ItemType Directory -Force (Split-Path -Parent $saved)|Out-Null
 Copy-Item -LiteralPath $target -Destination $saved
 if((Get-FileHash -LiteralPath $saved).Hash -ne $r3.files[$i].sha256){throw 'R3 rollback hash mismatch'}
}
if(@(Get-Process Cyberpunk2077 -ErrorAction SilentlyContinue).Count){throw 'Game started before install; deferred'}
for($i=0;$i -lt $files.Count;$i++){
 $target=Join-Path $game $files[$i].relative
 Copy-Item -LiteralPath $files[$i].source -Destination $target -Force
 if((Get-FileHash -LiteralPath $target).Hash -ne $files[$i].hash){throw "R4 installed hash mismatch: $target"}
}
foreach($path in $protected.Keys){if((Get-FileHash -LiteralPath $path).Hash -ne $protected[$path]){throw "Protected installed file changed: $path"}}
$receipt=[ordered]@{status='INSTALLED_R4_CLEANUP_IDLE_OPTIN_LIVE_PENDING';utc=[DateTime]::UtcNow.ToString('o');files=@($files|ForEach-Object {@{relative=$_.relative;sha256=$_.hash}});rollback_directory=$backup;protected_files=$protected.Count;passive_street_placements=$m.passive_placements;police_specific_placements_removed=$m.police_removed_count;native_original_interior_hide=$true;actors_added=0;native_scene_starts=0;story_fact_writes=0;save_files_modified=$false;gameplay_commands_executed=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'cleanup_r4_install_receipt.json'),($receipt|ConvertTo-Json -Depth 5))
$receipt|ConvertTo-Json -Depth 4
