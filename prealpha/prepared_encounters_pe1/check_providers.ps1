Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$queries=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'provider_queries_01.json') -Raw|ConvertFrom-Json -Depth 20
$out=Join-Path $PSScriptRoot 'providers_01'
if(Test-Path -LiteralPath $out){throw 'Fresh provider output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $out|Out-Null
$hashes=[WolvenKit.Common.Services.HashService]::new();$hashes.Load();$lookup=@{}
foreach($q in $queries.queries){$lookup[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($q.depot)]=$q}
$rows=[Collections.Generic.List[object]]::new();$archives=[Collections.Generic.List[object]]::new()
foreach($path in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -File -Filter '*.archive'){
 if($path.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked archive refused'}
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hashes,[ref]$archive).ToString() -cne 'NoError'){throw 'Unreadable archive index'}
 $archives.Add(@{path=$path.FullName;bytes=$path.Length;mtime_utc=$path.LastWriteTimeUtc.ToString('o')})
 foreach($key in $lookup.Keys){
  if(-not $archive.Files.ContainsKey([uint64]$key)){continue}
  $q=$lookup[$key];$memory=[IO.MemoryStream]::new()
  try{[void]$archive.Files[[uint64]$key].Extract($memory);$bytes=$memory.ToArray();$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}finally{$memory.Dispose()}
  $row=@{depot=$q.depot;key=$key.ToString();archive=$path.FullName;sha256=$digest;scope=$q.scope;raw=$null;json=$null;json_sha256=$null}
  if($q.scope -cne 'INSTALLED_SOURCE'){
   $raw=Join-Path $out ($path.BaseName+'/'+$q.depot)
   New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent)|Out-Null
   [IO.File]::WriteAllBytes($raw,$bytes)
   Export-Cr2wJson (Read-Cr2wFile $raw) ($raw+'.json')
   $row.raw=$raw;$row.json=$raw+'.json';$row.json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash
  }
  $rows.Add($row)
 }
}
$issues=[Collections.Generic.List[object]]::new()
foreach($q in $queries.queries){
 $found=@($rows|Where-Object{$_.depot -ceq $q.depot})
 if($q.scope -ceq 'INSTALLED_SOURCE'){
  $core=@($found|Where-Object{[IO.Path]::GetFileName($_.archive) -ceq 'zzzz_PTFR_Combined.archive'})
  $otherMods=@($found|Where-Object{$_.archive -like '*\archive\pc\mod\*' -and [IO.Path]::GetFileName($_.archive) -cne 'zzzz_PTFR_Combined.archive'})
  if($core.Count -ne 1 -or $core[0].sha256 -cne $q.expected_sha256 -or $otherMods.Count){$issues.Add(@{depot=$q.depot;reason='CURRENT_PRIVATE_PROVIDER_DRIFT_OR_COLLISION';providers=$found})}
 }else{
  if(-not $found.Count -or @($found|Where-Object{$_.sha256 -cne $q.expected_sha256}).Count){$issues.Add(@{depot=$q.depot;reason='NATIVE_SOURCE_HASH_OR_PRECEDENCE_DRIFT';providers=$found})}
 }
}
@{status=$(if($issues.Count){'PROVIDER_REVIEW_REQUIRED'}else{'PASS_CURRENT_PHASE_AND_NATIVE_PREFIX_PROVIDERS'});archives=@($archives);resources=@($rows);issues=@($issues);queries=$queries.queries.Count;current_phases=$queries.current_phase_count;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
if($issues.Count){throw "Provider/source review needed for $($issues.Count) depots; preserve evidence"}
Write-Output "Verified all $($queries.queries.Count) phase/prefix queries across $($archives.Count) archives."
