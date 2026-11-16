Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $PSScriptRoot 'source_01'
if(Test-Path -LiteralPath $out){throw 'Fresh capture required'}
$baseline=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/prepared_encounters_pe1/candidate_02/package_manifest.json') -Raw|ConvertFrom-Json -AsHashtable -Depth 30
$queries=@{}
foreach($depot in $baseline.source_resources.Keys){
 if($depot.Contains('\mq016\') -or $depot.EndsWith('\entries\mq016_bartmoss.questphase')){$queries[$depot]=@{scope='CURRENT_PRIVATE';sha256=$baseline.source_resources[$depot]}}
}
$previous=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/kold_mirage_km1/source_01/providers.json') -Raw|ConvertFrom-Json -Depth 25
foreach($row in $previous.resources){if(-not $row.depot.StartsWith('towercontinued\')){$queries[$row.depot]=@{scope='NATIVE';sha256=$row.sha256}}}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$hashes=[WolvenKit.Common.Services.HashService]::new();$hashes.Load();$lookup=@{}
foreach($depot in $queries.Keys){$lookup[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)]=$depot}
$rows=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
foreach($path in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -File -Filter '*.archive'){
 if($path.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked archive refused'}
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hashes,[ref]$archive).ToString() -cne 'NoError'){throw 'Unreadable archive'}
 $archives.Add(@{path=$path.FullName;bytes=$path.Length;mtime_utc=$path.LastWriteTimeUtc.ToString('o')})
 foreach($key in $lookup.Keys){
  if(-not $archive.Files.ContainsKey([uint64]$key)){continue}
  $depot=$lookup[$key];$memory=[IO.MemoryStream]::new()
  try{[void]$archive.Files[[uint64]$key].Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
  $raw=Join-Path $out ($path.BaseName+'/'+$depot)
  New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent)|Out-Null
  [IO.File]::WriteAllBytes($raw,$bytes)
  Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
  $digest=(Get-FileHash -LiteralPath $raw).Hash
  $rows.Add(@{depot=$depot;scope=$queries[$depot].scope;archive=$path.FullName;key=$key.ToString();sha256=$digest;raw=$raw;json=$raw+'.json';json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash})
 }
}
$issues=@(foreach($depot in $queries.Keys){
 $found=@($rows|Where-Object{$_.depot -ceq $depot})
 if($found.Count -ne 1 -or @($found|Where-Object{$_.sha256 -cne $queries[$depot].sha256}).Count){@{depot=$depot;providers=$found;expected=$queries[$depot].sha256}}
})
@{status=$(if($issues.Count){'REVIEW_REQUIRED'}else{'PASS_EXACT_KM2_CURRENT_AND_NATIVE_PROVIDERS'});archives=@($archives);queries=$queries;resources=@($rows);issues=$issues;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
if($issues.Count){throw 'Provider/source drift; preserve capture'}
Write-Output "Captured $($rows.Count) pinned resources across $($archives.Count) archives."
