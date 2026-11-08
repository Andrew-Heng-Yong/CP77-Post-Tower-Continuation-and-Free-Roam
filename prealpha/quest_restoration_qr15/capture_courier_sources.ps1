Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'courier_providers_01'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
function Assert-NoLink([string]$path){
 $item=Get-Item -LiteralPath $path
 while($null -ne $item){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked input refused: $($item.FullName)"}
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory}
 }
}
Assert-NoLink $PSScriptRoot
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots=@(
 'ep1\openworld\sandbox_activities\courier_spot\loop_phases\sa_ep1_pacifica_zone.questphase',
 'ep1\openworld\sandbox_activities\courier_spot\sa_ep1_114\sa_ep1_114.questphase'
)
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$queries=@{}
foreach($d in $depots){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d);if($queries.ContainsKey($key)){throw 'Query collision'};$queries[$key]=$d}
$rows=@();$archives=@();$index=0
$dirs=[Collections.Generic.Stack[string]]::new();$dirs.Push((Join-Path $game 'archive/pc'))
$files=[Collections.Generic.List[IO.FileInfo]]::new()
while($dirs.Count -gt 0){
 $dir=$dirs.Pop();Assert-NoLink $dir
 foreach($item in Get-ChildItem -LiteralPath $dir){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Archive census link: $($item.FullName)"}
  if($item -is [IO.DirectoryInfo]){$dirs.Push($item.FullName)}elseif($item.Extension -ceq '.archive'){$files.Add($item)}
 }
}
foreach($p in $files|Sort-Object FullName){
 Assert-NoLink $p.FullName
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw "Unreadable archive: $($p.FullName)"}
 $archives+=@{path=$p.FullName;bytes=$p.Length;mtime_utc=$p.LastWriteTimeUtc.ToString('o');members=$a.Files.Count};$index++
 foreach($key in $queries.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue}
  $depot=$queries[$key];$raw=Join-Path $out ('sources/'+$index.ToString('D3')+'/'+$depot)
  New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force|Out-Null
  $mem=[IO.MemoryStream]::new()
  try{$a.Files[[uint64]$key].Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray())}finally{$mem.Dispose()}
  $json=$raw+'.json';$err=$null
  try{Export-Cr2wJson (Read-Cr2wFile $raw) $json}catch{$err=$_.Exception.Message}
  $rows+=@{archive=$p.FullName;depot=$depot;key=$key.ToString();raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$(if(Test-Path -LiteralPath $json){$json}else{$null});json_sha256=$(if(Test-Path -LiteralPath $json){(Get-FileHash -LiteralPath $json).Hash}else{$null});decode_error=$err}
 }
}
$missing=@($depots|Where-Object {$_ -notin $rows.depot})
@{status='READ_ONLY_TARGET_PROVIDER_CAPTURE';queries=$depots;archives=$archives;resources=$rows;missing=$missing;game_writes=0;save_writes=0;limits='Conservative archive/pc index census; multiple providers must be resolved explicitly. Extraction and export only, no compile/build/install.'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
@{archives=$archives.Count;payloads=$rows.Count;missing=$missing;decode_failures=@($rows|Where-Object {$null -ne $_.decode_error}).Count}|ConvertTo-Json -Depth 3
