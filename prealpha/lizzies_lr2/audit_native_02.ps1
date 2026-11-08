$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'native_review_02';New-Item -ItemType Directory -Path $out -Force|Out-Null
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$depots=@('base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock','base\worlds\03_night_city\_compiled\default\quest_d9b1b5422f36a8fc.streamingsector','base\open_world\community\watson\kabuki\phases\wat_kab_lizzies_bar_phase.questphase','towercontinued\lizzies_lr1\club_owner.questphase','towercontinued\lizzies_lr2\club_support.questphase')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$queries=@{}
foreach($d in $depots){$queries[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d}
$hits=@();$descriptors=@();$count=0
foreach($p in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Filter '*.archive' -Recurse -File){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'};$count++
 foreach($key in $queries.Keys){if(!$a.Files.ContainsKey([uint64]$key)){continue};$depot=$queries[$key];$raw=Join-Path $out ('source/'+$p.BaseName+'/'+$depot)
  New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent)|Out-Null
  $ms=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($ms);[IO.File]::WriteAllBytes($raw,$ms.ToArray())}finally{$ms.Dispose()}
  $file=Read-Cr2wFile $raw
  if($depot.EndsWith('.streamingblock')){
   foreach($d in $file.RootChunk.Descriptors){if($d.Data.DepotPath.ToString() -eq $depots[1] -or $d.QuestPrefabNodeRef.ToString() -like '*loc_q004_lizzys_nightclub_openworld*'){
    $descriptors+=@{archive=$p.Name;sector=$d.Data.DepotPath.ToString();prefab=$d.QuestPrefabNodeRef.ToString();category=$d.Category.ToString();variants=$d.Variants.Count;definition=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($d,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 80)}
   }}
  }else{Export-Cr2wJson $file ($raw+'.json')}
  $hits+=@{archive=$p.FullName;depot=$depot;source=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash}
 }
}
@{archives=$count;hits=$hits;descriptors=$descriptors;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 90|Set-Content -LiteralPath (Join-Path $out 'providers_01.json') -Encoding utf8NoBOM
$logs=Join-Path $out 'logs';New-Item -ItemType Directory -Force -Path $logs|Out-Null
foreach($rel in @('bin/x64/plugins/cyber_engine_tweaks/scripting.log','red4ext/plugins/ArchiveXL/ArchiveXL-2026-10-29-15-00-44.log','red4ext/logs/red4ext-2026-10-29-15-00-43.log','r6/logs/redscript_rCURRENT.log')){Copy-Item -LiteralPath (Join-Path $game $rel) -Destination $logs}
@{archives=$count;resources=$hits.Count;descriptors=@($descriptors|Select-Object archive,sector,prefab,category,variants)}|ConvertTo-Json -Depth 7

