Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$prepared=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/prepared.json') -Raw | ConvertFrom-Json -Depth 100
$out=Join-Path $PSScriptRoot 'evidence_02'
if(Test-Path -LiteralPath $out){throw 'Use a fresh capture directory'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$cache=@{}
foreach($r in $prepared.cached_exports){$cache[$r.sha256]=$r}
$archives=@(Get-ChildItem -LiteralPath (Join-Path $prepared.game_root 'archive/pc') -Recurse -File -Filter '*.archive' | Sort-Object FullName)
$redmods=Join-Path $prepared.game_root 'mods'
if(Test-Path -LiteralPath $redmods){$archives+=@(Get-ChildItem -LiteralPath $redmods -Recurse -File -Filter '*.archive' | Sort-Object FullName)}
New-Item -ItemType Directory -Path $out | Out-Null
New-Item -ItemType Directory -Path (Join-Path $out 'exports') | Out-Null
$archiveRows=[Collections.Generic.List[object]]::new()
$writer=[IO.StreamWriter]::new((Join-Path $out 'resources.jsonl'),$false,[Text.UTF8Encoding]::new($false))
$count=0;$reused=0;$decoded=0;$opaque=0
try{
 foreach($file in $archives){
  if($file.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse archive refused'}
  $index=$archiveRows.Count
  $role=if($file.FullName -match '\\archive\\pc\\(content|ep1)\\'){'STOCK'}elseif($file.Name -ceq 'zzzz_PTFR_Combined.archive'){'PTFR'}else{'OTHER_MOD'}
  $archive=$null
  $code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive)
  if($code.ToString() -cne 'NoError'){throw "Archive unreadable: $($file.FullName)"}
  $archiveRows.Add(@{path=$file.FullName;bytes=$file.Length;mtime_ticks=$file.LastWriteTimeUtc.Ticks;index=$index;role=$role;members=$archive.Files.Count})
  foreach($entry in $archive.Files.Values){
   if($entry.Extension -notin @('.quest','.questphase','.scene','.journal','.gamedef')){continue}
   $row=[ordered]@{archive=$file.FullName;archive_index=$index;role=$role;depot=$entry.Name;key=$entry.Key.ToString();extension=$entry.Extension;sha256=$null;json=$null;json_sha256=$null;root_type=$null;status='PENDING';error=$null;imports=@()}
   try{
    $memory=[IO.MemoryStream]::new()
    try{$entry.Extract($memory);$bytes=$memory.ToArray()}finally{$memory.Dispose()}
    $row.sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    $memory=[IO.MemoryStream]::new($bytes,$false)
    try{
     $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory);$info=$null
     $code=$reader.ReadFileInfo([ref]$info,$null)
     if($code.ToString() -cne 'NoError'){throw "CR2W tables: $code"}
     $names=@($info.NameInfo | ForEach-Object {$info.StringDict[$_.offset]})
     $row.root_type=$names[$info.ExportInfo[0].className]
     $row.imports=@($info.ImportInfo | ForEach-Object {$info.StringDict[$_.offset]} | Sort-Object -Unique)
    }finally{$memory.Dispose()}
    if($cache.ContainsKey($row.sha256)){
     $prior=$cache[$row.sha256]
     if((Get-FileHash -LiteralPath $prior.json -Algorithm SHA256).Hash -cne $prior.json_sha256){throw 'Cached export changed'}
     $row.json=$prior.json;$row.json_sha256=$prior.json_sha256;$row.status='CURRENT_BYTES_MATCH_CACHED_EXPORT';$reused++
    }else{
     $memory=[IO.MemoryStream]::new($bytes,$false)
     try{
      $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory);$resource=$null
      $code=$reader.ReadFile([ref]$resource,$true)
      if($code.ToString() -cne 'NoError'){throw "CR2W decode: $code"}
      $jsonPath=Join-Path $out ('exports/'+$index+'_'+$entry.Key.ToString()+$entry.Extension+'.json')
      Export-Cr2wJson $resource $jsonPath
      $row.json=$jsonPath;$row.json_sha256=(Get-FileHash -LiteralPath $jsonPath).Hash;$row.status='EXPORTED_CURRENT';$decoded++
     }finally{$memory.Dispose()}
    }
   }catch{$row.status='OPAQUE';$row.error=$_.Exception.Message;$opaque++}
   $writer.WriteLine(($row | ConvertTo-Json -Depth 12 -Compress));$writer.Flush();$count++
  }
  if($role -eq 'STOCK' -or $role -eq 'PTFR'){Write-Output "$($file.Name): $count graph/journal providers, $reused reused, $decoded decoded, $opaque opaque"}
 }
}finally{$writer.Dispose()}
$changed=@(foreach($r in $archiveRows){$f=Get-Item -LiteralPath $r.path;if($f.Length -ne $r.bytes -or $f.LastWriteTimeUtc.Ticks -ne $r.mtime_ticks){$r.path}})
@{archives=$archiveRows.ToArray();changed=$changed;providers=$count;reused=$reused;decoded=$decoded;opaque=$opaque;game_writes=0;save_writes=0} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $out 'capture.json') -Encoding utf8NoBOM
if($changed.Count){throw 'Archives changed during capture'}
