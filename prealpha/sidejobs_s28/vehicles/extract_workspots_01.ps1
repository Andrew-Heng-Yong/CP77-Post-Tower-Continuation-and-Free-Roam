Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$out=Join-Path $ws 'research/sidejobs_s28/vehicles/workspots_01'
if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out|Out-Null
$paths=@(
 'base\workspots\main_characters\johnny\johnny__stand_ground_glasses__stand_around__01.workspot',
 'base\workspots\main_characters\johnny\johnny__stand_chair_lean_front_gun__stand_around__01.workspot',
 'base\workspots\main_characters\johnny\johnny__stand_wall_lean_back_cigarette__stand_around__01.workspot',
 'base\workspots\main_characters\johnny\johnny__stand_ground__stand_around__01.workspot',
 'base\workspots\quest\side_quests\sq031\sq031_05_grave\sq_031__johnny__stand_ground__stand_around__01.workspot'
)
$rows=[Collections.Generic.List[object]]::new();$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc'
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'content') -Filter 'basegame_*.archive' -File)+@(Get-ChildItem -LiteralPath (Join-Path $game 'ep1') -Filter 'ep1_*.archive' -File)
foreach($archive in $archives){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive.FullName,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($entry in $arc.Files.Values){
  if($entry.Name -cnotin $paths){continue}
  $memory=[IO.MemoryStream]::new()
  try{
   $entry.Extract($memory);$raw=Join-Path $out ($archive.BaseName+'/raw/'+$entry.Name);$json=Join-Path $out ($archive.BaseName+'/json/'+$entry.Name+'.json')
   New-Item -ItemType Directory -Force (Split-Path $raw -Parent),(Split-Path $json -Parent)|Out-Null
   [IO.File]::WriteAllBytes($raw,$memory.ToArray());Export-Cr2wJson (Read-Cr2wFile $raw) $json
   $rows.Add(@{archive=$archive.FullName;archive_length=$archive.Length;archive_mtime=$archive.LastWriteTimeUtc.ToString('o');depot=$entry.Name;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash})
  }finally{$memory.Dispose()}
 }
}
foreach($p in $paths){if(@($rows|Where-Object {$_.depot -ceq $p}).Count -eq 0){throw ('Missing '+$p)}}
$result=@{status='EXTRACTED_CURRENT_OFFICIAL_VARIANTS';rows=$rows.ToArray();script_sha256=(Get-FileHash $PSCommandPath).Hash;tool_sha256=(Get-FileHash (Join-Path $wk 'WolvenKit.RED4.dll')).Hash}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($result|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
Write-Output ('EXTRACTED '+$rows.Count)
