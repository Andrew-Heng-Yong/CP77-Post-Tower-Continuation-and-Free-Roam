param([string]$Revision='native_01')
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$out=Join-Path $ws ('research/sidejobs_s22/ep1_jobs/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable extraction exists'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$resources=@()
foreach($ap in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter '*.archive'){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($e in $a.Files.Values){
  if($e.Name -match '^ep1\\quest\\minor_quests\\mq306\\.*\.(quest|questphase|scene)$' -or $e.Name -match '^ep1\\quest\\main_quests\\q304\\phases\\.*q304_car_retrieval.*\.questphase$' -or $e.Name -in @('ep1\quest\main_quests\q304\q304.quest','ep1\quest\minor_quests\minorquests.questphase','ep1\quest\main_quests\q304\scenes\q304_car_retrieval_purge_data.scene','ep1\quest\main_quests\q304\scenes\q304_car_retrieval_truck_stop.scene','ep1\quest\main_quests\q304\scenes\q304_09d_reed_escape_combat.scene')){
   $resources+=,$e.Name
  }
 }
}
if(!$resources.Count){throw 'No mq306 resources found'}
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths ($resources|Sort-Object -Unique) -OutputRoot $out -ArchivePaths @((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter '*.archive').FullName)
