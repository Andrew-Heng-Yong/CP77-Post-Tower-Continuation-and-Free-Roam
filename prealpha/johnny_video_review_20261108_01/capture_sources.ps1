Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$queryPath=Join-Path $PSScriptRoot 'source_queries_01.json'
$queries=Get-Content -LiteralPath $queryPath -Raw|ConvertFrom-Json -Depth 30
$out=Join-Path $PSScriptRoot 'source_01'
if(Test-Path -LiteralPath $out){throw 'Fresh capture required'}
if((Get-FileHash -LiteralPath $queries.installed_manifest).Hash -cne $queries.installed_manifest_sha256 -or (Get-FileHash -LiteralPath $queries.package_manifest).Hash -cne $queries.package_manifest_sha256){throw 'Selected baseline drift'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$hashes=[WolvenKit.Common.Services.HashService]::new();$hashes.Load();$lookup=@{}
foreach($q in $queries.queries){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($q.depot);if($lookup.ContainsKey($key)){throw 'Duplicate depot key'};$lookup[$key]=$q}
$rows=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
foreach($path in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -File -Filter '*.archive'){
 if($path.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked archive refused'}
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hashes,[ref]$archive).ToString() -cne 'NoError'){throw 'Unreadable archive'}
 $archives.Add(@{path=$path.FullName;bytes=$path.Length;mtime_utc=$path.LastWriteTimeUtc.ToString('o')})
 foreach($key in $lookup.Keys){
  if(-not $archive.Files.ContainsKey([uint64]$key)){continue}
  $q=$lookup[$key];$memory=[IO.MemoryStream]::new()
  try{[void]$archive.Files[[uint64]$key].Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
  $raw=Join-Path $out ($path.BaseName+'/'+$q.depot)
  New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent)|Out-Null
  [IO.File]::WriteAllBytes($raw,$bytes)
  Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
  $rows.Add(@{depot=$q.depot;scope=$q.scope;archive=$path.FullName;key=$key.ToString();sha256=(Get-FileHash -LiteralPath $raw).Hash;raw=$raw;json=$raw+'.json';json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash})
 }
}
$issues=@(foreach($q in $queries.queries){$found=@($rows|Where-Object{$_.depot -ceq $q.depot});if($found.Count -ne 1 -or @($found|Where-Object{$_.sha256 -cne $q.expected_sha256}).Count){@{depot=$q.depot;providers=$found;expected=$q.expected_sha256}}})
@{status=$(if($issues.Count){'REVIEW_REQUIRED'}else{'PASS_BATCH2_CURRENT_PRIVATE_PROVIDERS'});query_sha256=(Get-FileHash -LiteralPath $queryPath).Hash;archives=@($archives);resources=@($rows);issues=$issues;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
if($issues.Count){throw 'Provider/source drift; preserve capture'}
Write-Output "Captured $($rows.Count) batch-two quest resources across $($archives.Count) archive indices."
