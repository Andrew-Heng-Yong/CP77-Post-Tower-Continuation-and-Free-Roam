# Capture current providers into fresh workspace evidence. Never writes the game.
param([string]$Name='sources_01',[string]$QueryFile='')
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
$manifestPath=Join-Path $workspace 'prealpha/kold_mirage_gate_20261116_01/work/deployment_01/installed_manifest_01.json'
if((Get-FileHash -LiteralPath $manifestPath).Hash -cne 'D7D6EDC420052701621F9EE409075302E6AF5B1B931EABA5EF9A911526F2C7FF'){throw 'Core manifest drift'}
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
$identity=@(foreach($row in @($manifest.core_files)+@($manifest.required_files)){
 $path=Join-Path $manifest.game_root $row.path;Plain $path
 $hash=(Get-FileHash -LiteralPath $path).Hash
 if($hash -cne $row.sha256){throw "Installed baseline drift: $path"}
 @{path=$row.path;sha256=$hash}
})
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots=@(
 'base\worlds\03_night_city\_compiled\default\ep1\exterior_-1_0_0_5.streamingsector',
 'base\worlds\03_night_city\_compiled\default\ep1\exterior_-12_8_0_1.streamingsector',
 'base\worlds\03_night_city\_compiled\default\exterior_-1_0_0_5.streamingsector',
 'base\worlds\03_night_city\_compiled\default\exterior_-12_8_0_1.streamingsector',
 'base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock',
 'base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock',
 'ep1\quest\main_quests\q307\phases\q307_cleanup.questphase',
 'towercontinued\misty_viktor_world\shell_optin.questphase'
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
