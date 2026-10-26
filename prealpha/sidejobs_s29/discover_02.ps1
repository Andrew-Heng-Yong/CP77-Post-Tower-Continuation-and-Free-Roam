Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $ws 'research/sidejobs_s29/discovery_02';if(Test-Path -LiteralPath $out){throw 'Immutable discovery exists'}
New-Item -ItemType Directory $out|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$rows=@();$count=0
$needles=@('sts_ep1_12_pickup','mq059.quest','mq058.quest','mq060.quest')
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc'
foreach($relative in @('content/basegame_4_gamedata.archive','ep1/ep1_2_gamedata.archive')){
 $file=Join-Path $game $relative;$arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file,$hs,[ref]$arc).ToString() -cne 'NoError'){throw 'Unreadable archive'}
 foreach($entry in $arc.Files.Values){
  if($entry.Name -notmatch '\.quest(phase)?$' -or $entry.Name -match '\\versions\\'){continue}
  $count++;$m=[IO.MemoryStream]::new();try{$entry.Extract($m);$bytes=$m.ToArray()}finally{$m.Dispose()}
  $text=[Text.Encoding]::UTF8.GetString($bytes);$hits=@($needles|Where-Object {$text.Contains($_)});if(!$hits.Count){continue}
  $raw=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($file)+'/raw/'+$entry.Name)
  $json=Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($file)+'/json/'+$entry.Name+'.json')
  New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null
  [IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json
  $rows+=,@{depot=$entry.Name;archive=$file;hits=$hits;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
 }
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),(@{status='NATIVE_PARENT_REFERENCE_DISCOVERY';rows=$rows;scanned=$count;needles=$needles;script_sha256=(Get-FileHash $PSCommandPath).Hash;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{scanned=$count;hits=$rows.Count;depots=$rows.depot}|ConvertTo-Json
