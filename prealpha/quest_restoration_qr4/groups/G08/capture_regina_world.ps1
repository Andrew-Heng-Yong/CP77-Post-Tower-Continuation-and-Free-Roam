$ErrorActionPreference='Stop'
$ws=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'regina_world_01';if(Test-Path $out){throw 'Fresh output required'};New-Item -ItemType Directory $out|Out-Null
$prior=Join-Path $ws 'diagnostics/phone_expansion_ph3_20261029_01/native_04/providers_01.json'
$capture=Get-Content -Raw $prior|ConvertFrom-Json
$blocks=@($capture.hits|Where-Object{$_.depot.EndsWith('.streamingblock')})
$descriptors=@();$blockPins=@()
foreach($b in $blocks){
 if((Get-FileHash -LiteralPath $b.raw).Hash -ne $b.sha256){throw 'Prior block pin mismatch'}
 $r=Read-Cr2wFile $b.raw;$matches=@()
 foreach($desc in $r.RootChunk.Descriptors){
  $s=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($desc,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
  if($s -like '*mq007_pr_gun_return*'){$definition=$s|ConvertFrom-Json -Depth 95;$matches+=,$definition;$descriptors+=,@{archive=$b.archive;block=$b.depot;sha256=$b.sha256;definition=$definition}}
 }
 $blockPins+=,@{raw=$b.raw;sha256=$b.sha256;archive=$b.archive;block=$b.depot;matching_descriptors=$matches.Count}
}
$depots=@($descriptors|ForEach-Object{$_.definition.data.DepotPath.'$value'}|Sort-Object -Unique)
if($depots.Count -ne 1){throw 'Expected one scoped native world sector; inspect descriptor differences'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$queries=@{};foreach($d in $depots){$queries[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d}
$hits=@();$archives=0
foreach($p in Get-ChildItem 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Filter '*.archive' -Recurse -File){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive unreadable'};$archives++
 foreach($key in $queries.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue};$d=$queries[$key];$raw=Join-Path $out ($p.BaseName+'/'+$d);New-Item -ItemType Directory -Force(Split-Path $raw -Parent)|Out-Null
  $mem=[IO.MemoryStream]::new();$a.Files[[uint64]$key].Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray());$mem.Dispose();$decodeError=$null;$json=$null
  try{$resource=Read-Cr2wFile $raw;$json=$raw+'.json';Export-Cr2wJson $resource $json}catch{$decodeError=$_.Exception.Message}
  $hits+=,@{archive=$p.FullName;depot=$d;raw=$raw;sha256=(Get-FileHash $raw).Hash;json=$json;decode_error=$decodeError}
 }
}
@{status='READ_ONLY_PINNED_WORLD_CAPTURE';prior_provider_manifest=$prior;prior_manifest_sha256=(Get-FileHash $prior).Hash;blocks=$blockPins;descriptors=$descriptors;archives_scanned=$archives;sector_queries=$depots;hits=$hits;runtime_changes=@()}|ConvertTo-Json -Depth 100|Set-Content (Join-Path $out 'capture.json') -Encoding utf8NoBOM
@{descriptors=$descriptors.Count;sector_paths=$depots;providers=$hits.Count;decode_errors=@($hits|Where-Object{$_.decode_error}).Count;output=$out}|ConvertTo-Json -Depth 5
