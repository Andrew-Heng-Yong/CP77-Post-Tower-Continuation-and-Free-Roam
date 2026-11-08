Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$O=Join-Path $PSScriptRoot 'owner_gap_readback_01'
if(Test-Path -LiteralPath $O){throw 'Fresh provider output required'}
$q=@(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'owner_gap_queries.json') -Raw|ConvertFrom-Json -Depth 50)
$g=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'prepared.json') -Raw|ConvertFrom-Json).game
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[IO.Directory]::CreateDirectory($O)|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$lookup=@{};foreach($r in $q){$k=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.depot);$lookup[$k]=$r}
$arcs=@();$rows=@();$errors=@()
foreach($f in Get-ChildItem -LiteralPath (Join-Path $g 'archive/pc') -File -Recurse -Filter '*.archive'){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw ('Unreadable archive: '+$f.FullName)}
 $stock=$f.DirectoryName -notlike '*\mod*'
 $arcs+=,@{path=$f.FullName;bytes=$f.Length;mtime_utc=$f.LastWriteTimeUtc.ToString('o');members=$a.Files.Count}
 foreach($k in $lookup.Keys){
  if(-not $a.Files.ContainsKey([uint64]$k)){continue};$r=$lookup[$k];$h=$null;$raw=$null;$json=$null;$status='PRESENCE_ONLY'
  if($r.hash_payload){
   $m=[IO.MemoryStream]::new()
   try{
    $a.Files[[uint64]$k].Extract($m);$bytes=$m.ToArray();$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));$status='HASHED'
    if($r.export){
     $raw=Join-Path (Join-Path $O $f.BaseName) $r.depot
     [IO.Directory]::CreateDirectory((Split-Path $raw -Parent))|Out-Null
     [IO.File]::WriteAllBytes($raw,$bytes)
     try{$res=Read-Cr2wFile $raw;$json=$raw+'.json';Export-Cr2wJson $res $json;$status='EXPORTED'}catch{$errors+=,@{depot=$r.depot;archive=$f.FullName;error=$_.Exception.Message};$status='DECODE_ERROR'}
    }
   }finally{$m.Dispose()}
  }
  $rows+=,@{depot=$r.depot;archive=$f.FullName;stock=$stock;key=$k.ToString();sha256=$h;status=$status;raw=$raw;json=$json;expected_sha256=$r.expected_sha256;matches_expected=if($h -and @($r.expected_sha256).Count){@($r.expected_sha256) -ccontains $h}else{$null}}
 }
}
$missing=@($q|Where-Object{$rows.depot -cnotcontains $_.depot}|ForEach-Object{$_.depot})
@{queries=$q;archives=$arcs;providers=$rows;missing=$missing;decode_errors=$errors;game_writes=0;save_writes=0;scope='Bounded QR2 quest and ancestor dependencies; presence-only binary assets do not prove decoded semantic/placement parity'}|ConvertTo-Json -Depth 60|Set-Content -LiteralPath (Join-Path $O 'capture.json') -Encoding utf8NoBOM
@{archives=$arcs.Count;queries=$q.Count;providers=$rows.Count;missing=$missing;decode_errors=$errors.Count}|ConvertTo-Json -Depth 10
