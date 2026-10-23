param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$world=Get-Content (Join-Path $audit 'lighting_r8_world_manifest.json') -Raw|ConvertFrom-Json
$phase=Get-Content (Join-Path $audit 'lighting_r8_phase_manifest.json') -Raw|ConvertFrom-Json
if($world.status -ne 'BUILT_R8_WORLD_SOURCE_NOT_INSTALLED' -or $phase.status -ne 'BUILT_R8_AUTOMATIC_NATIVE_PHASES_NOT_INSTALLED'){throw 'R8 source status changed'}
$out=Join-Path $WorkspaceRoot 'build\MistyLightingR8';$source=Join-Path $out 'source'
$items=@(
 @($world.original_depot,$world.original_sha256),@($world.cold_sector_depot,$world.cold_sector_sha256),
 @($world.cold_block_depot,$world.cold_block_sha256),@($phase.neon.depot,$phase.neon.sha256),
 @($phase.police.depot,$phase.police.sha256)
)
foreach($item in $items){if((Get-FileHash -LiteralPath (Join-Path $source $item[0])).Hash -ne $item[1]){throw ('R8 source changed: '+$item[0])}}
$actual=@(Get-ChildItem -LiteralPath $source -File -Recurse|ForEach-Object {$_.FullName.Substring($source.Length+1)})
if(@(Compare-Object @($items|ForEach-Object {$_[0]}|Sort-Object) @($actual|Sort-Object)).Count){throw 'R8 source tree has unexpected resources'}
function Crc([string]$text){
 $value=65535
 foreach($byte in [Text.Encoding]::UTF8.GetBytes($text+':1')){
  $x=($value -shr 8) -bxor $byte;$x=$x -bxor ($x -shr 4)
  $value=(($value -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535
 }
 return $value
}
$neonId=Crc $phase.neon.depot;$policeId=Crc $phase.police.depot
if($neonId -eq $policeId){throw 'R8 parent registration collision'}
$parent=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\ep1\quest\ep1.quest')
foreach($id in @($neonId,$policeId)){if(@($parent.RootChunk.Graph.Chunk.Nodes|Where-Object {$_.Chunk.Id.ToString() -eq "$id"}).Count){throw ('Vanilla parent node ID collision: '+$id)}}
$xl=@('streaming:','  blocks:',('    - '+$world.cold_block_depot),'quest:','  phases:')
foreach($path in @($phase.neon.depot,$phase.police.depot)){
 $xl+=@("    - path: $path",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')
}
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archivePath=Join-Path $out 'TowerContinued_MistyLightingR8.archive'
$stream=[IO.File]::Create($archivePath)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R8 archive pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archivePath+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R8 archive reopen failed'}
if(@(Compare-Object @($items|ForEach-Object {$_[0]}|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R8 packed resource scope mismatch'}
foreach($entry in $packed.Files.Values){
 $memory=[IO.MemoryStream]::new()
 try{$entry.Extract($memory);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}
 $expect=@($items|Where-Object {$_[0] -eq $entry.Name})
 if($expect.Count -ne 1 -or $digest -ne $expect[0][1]){throw ('R8 packed bytes mismatch: '+$entry.Name)}
}
$driver=Join-Path $WorkspaceRoot 'redscript\PTFR_MistyViktor_Auto\MistyViktorAuto.reds'
$journalDriver=Join-Path $WorkspaceRoot 'redscript\PTFR_TowerJournal_Auto\TowerJournalAuto.reds'
$timeDriver=Join-Path $WorkspaceRoot 'redscript\PTFR_Time_Auto\TimeAuto.reds'
$manifest=[ordered]@{
 status='BUILT_R8_AUTOMATIC_PACKAGE_NOT_INSTALLED';archive=$archivePath;archive_sha256=(Get-FileHash $archivePath).Hash
 xl=$archivePath+'.xl';xl_sha256=(Get-FileHash ($archivePath+'.xl')).Hash
 driver=$driver;driver_sha256=(Get-FileHash $driver).Hash
 journal_driver=$journalDriver;journal_driver_sha256=(Get-FileHash $journalDriver).Hash
 time_driver=$timeDriver;time_driver_sha256=(Get-FileHash $timeDriver).Hash
 resources=@($items|ForEach-Object {@{path=$_[0];sha256=$_[1]}});neon_registration_id=$neonId;police_registration_id=$policeId
 original_sector_overrides=1;original_alias_changes=12;private_cold_nodes=5;automatic_neon=$true;automatic_police_after_r7=$true
 automatic_r7_driver=$true;automatic_journal_driver=$true;automatic_time_driver=$true;no_cet_required=$true;story_fact_writes=0;original_variant_writes=0;installed=$false;live_tested=$false
}
[IO.File]::WriteAllText((Join-Path $audit 'lighting_r8_package_manifest.json'),($manifest|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,archive_sha256,xl_sha256,driver_sha256,journal_driver_sha256,time_driver_sha256,neon_registration_id,police_registration_id|ConvertTo-Json
