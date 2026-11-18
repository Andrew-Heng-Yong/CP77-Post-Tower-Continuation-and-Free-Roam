# Capture current providers into fresh workspace evidence. Never writes the game.
param([string]$Name='native_01',[string]$QueryFile='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if($Name -cnotmatch '^[a-z][a-z0-9_]+$'){throw 'Invalid output name'}
$out=Join-Path $PSScriptRoot ('work/'+$Name)
if(Test-Path -LiteralPath $out){throw 'Fresh evidence required'}
function Plain([string]$path){
 for($item=Get-Item -LiteralPath $path -Force;$null -ne $item;){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked path refused: $path"}
  $item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}
 }
}
Plain $PSScriptRoot
$manifestPath=Join-Path $workspace 'prealpha/misty_rooftop_lift_20261117_01/installed_manifest.json'
if((Get-FileHash -LiteralPath $manifestPath).Hash -cne 'B738804793E5E669D71F72E9FB7755B2786D2B25E3B0A212681F10427C9EF5C0'){throw 'Core manifest drift'}
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$identity=@(foreach($row in @($manifest.core_files)+@($manifest.required_files)+@($manifest.archivexl_files)+@($manifest.ifp_files)){
 $path=Join-Path $manifest.game_root $row.path;Plain $path
 $hash=(Get-FileHash -LiteralPath $path).Hash
 if($hash -cne $row.sha256){throw "Installed baseline drift: $path"}
 @{path=$row.path;sha256=$hash}
})
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots=@(
 'base\quest\main_quests\part1\q115\scenes\q115_02b_ripperdoc_roof.scene',
 'ep1\quest\main_quests\q307\scenes\q307_00_pickup_holocall.scene',
 'base\quest\side_quests\sq028\scenes\kerry_villa\sq028_kerry_villa_sit.scene',
 'base\open_world\scenes\mirrors\mirror_scene_el_cojote.scene',
 'base\worlds\03_night_city\_compiled\default\quest_0eb702d8c8f8ee5b.streamingsector',
 'ep1\quest\ep1.quest',
 'towercontinued\streetkid_seat_auto\gate.questphase',
 'towercontinued\streetkid_seat_auto\seat_mirror.scene',
 'towercontinued\streetkid_seat_s1\seat.scene',
 'towercontinued\misty_rooftop_seat\gate.questphase',
 'towercontinued\misty_rooftop_seat\sit.scene'
)
if($QueryFile){$depots=@(Get-Content -LiteralPath $QueryFile -Raw|ConvertFrom-Json)}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$queries=@{}
foreach($depot in $depots){
 if($depot.StartsWith('\') -or $depot.Contains('..') -or $depot.Contains(':')){throw 'Unsafe depot'}
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString([string]$depot)
 if($queries.ContainsKey($key)){throw 'Depot collision'}
 $queries[$key]=[string]$depot
}
[void][IO.Directory]::CreateDirectory($out)
$hits=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
foreach($relative in @('archive/pc','mods')){
 $folder=Join-Path $manifest.game_root $relative
 if(-not(Test-Path -LiteralPath $folder)){continue}
 Plain $folder
 if(@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked archive tree'}
 foreach($file in Get-ChildItem -LiteralPath $folder -Filter '*.archive' -Recurse -File){
  Plain $file.FullName;$stamp=@($file.Length,$file.LastWriteTimeUtc.Ticks);$arc=$null
  if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw "Unreadable provider: $($file.FullName)"}
  $archives.Add(@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o')})
  foreach($key in $queries.Keys){
   if(-not $arc.Files.ContainsKey([uint64]$key)){continue}
   $depot=$queries[$key];$raw=Join-Path $out (([string]$archives.Count)+'/'+$depot)
   [void][IO.Directory]::CreateDirectory((Split-Path $raw -Parent))
   $memory=[IO.MemoryStream]::new()
   try{$arc.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
   $row=@{archive=$file.FullName;depot=$depot;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$null;json_sha256=$null;decode_error=$null}
   try{Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json');$row.json=$raw+'.json';$row.json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash}
   catch{$row.decode_error=$_.Exception.ToString()}
   $hits.Add($row)
  }
  $file.Refresh();if($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]){throw 'Archive changed during capture'}
 }
}
@{status='CURRENT_PROVIDER_CAPTURE';manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash;identity=$identity;queries=$depots;archives=$archives.ToArray();hits=$hits.ToArray();game_writes=0;save_writes=0}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output ("Verified {0} installed files; {1} providers captured across {2} archives; {3} decode failures retained" -f $identity.Count,$hits.Count,$archives.Count,@($hits|Where-Object {$_.decode_error}).Count)
