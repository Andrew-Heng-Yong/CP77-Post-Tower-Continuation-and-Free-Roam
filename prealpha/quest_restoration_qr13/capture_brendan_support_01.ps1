Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'brendan_support_capture_01'
if(Test-Path -LiteralPath $out){throw 'Fresh provider output only'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$depots=@('base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock','base\worlds\03_night_city\_compiled\default\quest_5eaa50767f96451d.streamingsector','base\worlds\03_night_city\_compiled\default\quest_e8c7465a9bdb5654.streamingsector')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$queries=@{}
foreach($d in $depots){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d);if($queries.ContainsKey($key)){throw 'Query FNV collision'};$queries[$key]=$d}
$rows=@();$archives=@();$index=0
foreach($p in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -File -Filter '*.archive'|Sort-Object FullName){
 if($p.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked archive refused'}
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw "Unreadable archive $($p.FullName)"}
 $archives+=@{path=$p.FullName;bytes=$p.Length;mtime_utc=$p.LastWriteTimeUtc.ToString('o');members=$a.Files.Count};$index++
 foreach($key in $queries.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue}
  $depot=$queries[$key];$raw=Join-Path $out ('sources/'+$index.ToString('D3')+'/'+$depot);New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force|Out-Null
  $mem=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray())}finally{$mem.Dispose()}
  $json=$raw+'.json';$decodeError=$null
  try{Export-Cr2wJson (Read-Cr2wFile $raw) $json}catch{$decodeError=$_.Exception.Message}
  $rows+=@{archive=$p.FullName;depot=$depot;key=$key.ToString();raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$(if(Test-Path -LiteralPath $json){$json}else{$null});json_sha256=$(if(Test-Path -LiteralPath $json){(Get-FileHash -LiteralPath $json).Hash}else{$null});decode_error=$decodeError}
 }
}
$missing=@($depots|Where-Object {$_ -notin $rows.depot})
@{status='READ_ONLY_CURRENT_TARGET_PROVIDER_CAPTURE';archives=$archives;resources=$rows;missing=$missing;limits='All archive indexes are a conservative census including stored archives. Multiple providers require explicit precedence resolution; no automatic filename winner. Decode failures remain visible.';game_writes=0;save_writes=0}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
@{archives=$archives.Count;matching_payloads=$rows.Count;missing=$missing;decode_failures=@($rows|Where-Object {$null -ne $_.decode_error}).Count}|ConvertTo-Json -Depth 3
