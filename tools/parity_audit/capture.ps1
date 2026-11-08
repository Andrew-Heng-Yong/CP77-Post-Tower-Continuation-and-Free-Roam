param([Parameter(Mandatory=$true)][string]$OutputRoot,[string]$WorkspaceRoot=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),[int]$MaxRounds=12,[string]$ResumeCapture='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=[IO.Path]::GetFullPath($WorkspaceRoot);$o=[IO.Path]::GetFullPath($OutputRoot)
if(-not $o.StartsWith((Join-Path $w 'diagnostics')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Output escaped diagnostic root'}
if(Test-Path (Join-Path $o 'capture.json')){throw 'Fresh capture required'}
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$q=Get-Content (Join-Path $o 'queries.json') -Raw|ConvertFrom-Json -Depth 100;$prep=Get-Content (Join-Path $o 'prepared.json') -Raw|ConvertFrom-Json
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$cache=@{};$wanted=@{};$done=@{};$rows=[Collections.Generic.List[object]]::new();$archives=@();$privateChecks=@();$missing=@();$errors=@()
if($ResumeCapture){
 $prior=Get-Content -LiteralPath $ResumeCapture -Raw|ConvertFrom-Json -Depth 100
 foreach($r in $prior.resources){$rows.Add($r);$done[$r.depot]=$true}
 foreach($d in $prior.missing){$done[$d]=$true}
 $privateChecks=@($prior.private_readback);$missing=@($prior.missing);$errors=@($prior.decode_errors)
}
foreach($r in $q.cache){if(-not $cache.ContainsKey($r.depot)){$cache[$r.depot]=[Collections.Generic.List[object]]::new()};$cache[$r.depot].Add($r)}
function Want([string]$d){if($d -and $d -notin @('0','None')){$wanted[$d]=if($d -match '^[0-9]+$'){[uint64]$d}else{[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)}}}
foreach($d in $q.wanted){Want $d};foreach($r in $q.private){Want $r.depot}
$regex=[regex]'(?:base|ep1|towercontinued|dlc)\\[A-Za-z0-9_\\.-]+\.(?:questphase|scene|quest|ent|app|workspot|mesh|effect|anim|streamingsector|streamingblock|journal|xbm)(?![A-Za-z0-9_.\\])'
$parseExt=@('.questphase','.scene','.quest')
function BytesHash($bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
for($round=0;$round -lt $MaxRounds;$round++){
 $pending=@($wanted.Keys|Where-Object {-not $done.ContainsKey($_)});if($pending.Count -eq 0){break}
 $keys=@{};foreach($d in $pending){$keys[$wanted[$d]]=$d};$hits=@{};foreach($d in $pending){$hits[$d]=0}
 foreach($f in Get-ChildItem (Join-Path $prep.game 'archive/pc') -Filter '*.archive' -Recurse -File){
  $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw "Unreadable archive $($f.FullName)"}
  if($round -eq 0){$archives+=,@{path=$f.FullName;bytes=$f.Length;mtime_utc=$f.LastWriteTimeUtc.ToString('o');members=$a.Files.Count;stock=$f.DirectoryName -notlike '*\mod*'}}
  $owned=$f.Name -ceq 'zzzz_PTFR_Combined.archive'
  foreach($key in $keys.Keys){if(-not $a.Files.ContainsKey([uint64]$key)){continue};$d=$keys[$key];$hits[$d]++
   $parse=[IO.Path]::GetExtension($d) -in $parseExt
   # Presence-only assets: no geometry, gameplay or full asset closure claim.
   if(-not $parse -and -not $owned){$rows.Add(@{depot=$d;key=$key.ToString();archive=$f.FullName;stock=$f.DirectoryName -notlike '*\mod*';sha256=$null;raw=$null;json=$null;status='PRESENCE_ONLY';round=$round});continue}
   $m=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($m);$b=$m.ToArray()}finally{$m.Dispose()};$hash=BytesHash $b
   if($owned){$expected=@($q.private|Where-Object depot -CEQ $d);if($expected.Count -ne 1 -or $expected[0].sha256 -cne $hash){throw "Installed/source mismatch $d"};$privateChecks+=,@{depot=$d;sha256=$hash;key=$key.ToString()}}
   $reuse=$null
   if($cache.ContainsKey($d)){foreach($r in $cache[$d]){if($r.sha256 -ceq $hash -and (Test-Path -LiteralPath $r.json) -and (Get-FileHash -LiteralPath $r.json).Hash -ceq $r.json_sha256){$reuse=$r;break}}}
   $raw=Join-Path $o ('raw/'+$f.BaseName+'/'+$d);$json=$null;$errorText=$null;$status='PRESENCE_ONLY'
   if($null -ne $reuse){$raw=$reuse.raw;$json=$reuse.json;$status='DECODED_CACHE_HASH_MATCH'}else{
    New-Item -ItemType Directory -Force (Split-Path $raw -Parent)|Out-Null;[IO.File]::WriteAllBytes($raw,$b)
    if($parse){try{$resource=Read-Cr2wFile $raw;$json=$raw+'.json';Export-Cr2wJson $resource $json;$status='DECODED'}catch{$errorText=$_.Exception.Message;$status='OPAQUE';$errors+=,@{depot=$d;archive=$f.FullName;error=$errorText}}}
   }
   if($parse){foreach($match in $regex.Matches([Text.Encoding]::UTF8.GetString($b))){Want $match.Value}}
   $rows.Add(@{depot=$d;key=$key.ToString();archive=$f.FullName;stock=$f.DirectoryName -notlike '*\mod*';sha256=$hash;raw=$raw;json=$json;json_sha256=$(if($json){(Get-FileHash -LiteralPath $json).Hash}else{$null});status=$status;error=$errorText;round=$round})
  }
 }
 foreach($d in $pending){$done[$d]=$true;if($hits[$d] -eq 0){$missing+=,$d}}
 @{round=$round;queries=$pending.Count;providers=$rows.Count;new_pending=@($wanted.Keys|Where-Object {-not $done.ContainsKey($_)}).Count;decode_errors=$errors.Count}|ConvertTo-Json -Compress|Write-Output
}
$truncated=@($wanted.Keys|Where-Object {-not $done.ContainsKey($_)})
@{schema=1;archives=$archives;resources=$rows.ToArray();private_readback=$privateChecks;missing=$missing;truncated=$truncated;decode_errors=$errors;resumed_from=$ResumeCapture;dependency_scope='Recursive phase/scene/quest binary-reference closure; non-graph assets checked for presence only; unresolved dynamic/hashed refs remain audit limits';game_writes=0;save_writes=0}|ConvertTo-Json -Depth 20|Set-Content (Join-Path $o 'capture.json') -Encoding utf8NoBOM
@{status='CAPTURE_COMPLETE';providers=$rows.Count;missing=$missing.Count;truncated=$truncated.Count;private_readback=$privateChecks.Count}|ConvertTo-Json
