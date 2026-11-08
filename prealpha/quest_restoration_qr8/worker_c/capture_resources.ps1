param([string]$Targets='baseline_01/new_targets.json',[string]$Output='capture_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$O=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Output))
if(-not $O.StartsWith($PSScriptRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Worker output containment'}
if(Test-Path -LiteralPath $O){throw 'Fresh worker output required'}
$targetPath=Join-Path $PSScriptRoot $Targets;$inputPin=(Get-FileHash -LiteralPath $targetPath).Hash
$data=Get-Content -Raw -LiteralPath $targetPath|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names=@{}
foreach($d in $data.targets){$names[[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString([string]$d)]=[string]$d}
$archives=@(Get-ChildItem -LiteralPath 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc' -Filter '*.archive' -Recurse -File|Sort-Object FullName)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$inventory=@();$rows=@();$i=0
[IO.Directory]::CreateDirectory($O)|Out-Null
foreach($file in $archives){
 $meta=@($file.Length,$file.LastWriteTimeUtc.Ticks);$arc=$null
 $result=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc)
 if($result.ToString() -ne 'NoError'){throw ('Cannot index '+$file.FullName)}
 $matches=@()
 foreach($key in $names.Keys){
  if(-not $arc.Files.ContainsKey([uint64]$key)){continue}
  $depot=$names[$key];$matches+=,$depot;$i++
  $raw=Join-Path $O ('resource_'+$i+[IO.Path]::GetExtension($depot));$json=$raw+'.json'
  $s=[IO.MemoryStream]::new()
  try{$arc.Files[[uint64]$key].Extract($s);[IO.File]::WriteAllBytes($raw,$s.ToArray())}finally{$s.Dispose()}
  $r=@{depot=$depot;provider=$file.FullName;provider_metadata=$meta;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash}
  try{
   $resource=Read-Cr2wFile $raw;Export-Cr2wJson $resource $json;$r.json=$json;$r.json_sha256=(Get-FileHash -LiteralPath $json).Hash;$r.status='EXPORTED'
   if($resource.RootChunk.GetType().Name -eq 'worldStreamingSector'){
    $buffer=Join-Path $O ('resource_'+$i+'.nodes.bin');[IO.File]::WriteAllBytes($buffer,$resource.RootChunk.NodeData.Buffer.GetBytes());$r.node_buffer=$buffer;$r.node_buffer_sha256=(Get-FileHash -LiteralPath $buffer).Hash
   }
  }catch{$r.status='OPAQUE';$r.error=$_.Exception.Message}
  $rows+=,$r
 }
 $file.Refresh();if($file.Length -ne $meta[0] -or $file.LastWriteTimeUtc.Ticks -ne $meta[1]){throw 'Provider changed during capture'}
 $inventory+=,@{path=$file.FullName;metadata=$meta;matches=$matches;index_entries=$arc.Files.Count}
}
if((Get-FileHash -LiteralPath $targetPath).Hash -cne $inputPin){throw 'Capture target list changed'}
@{status='READ_ONLY_TARGETED_CURRENT_PROVIDERS';input=@{path=$targetPath;sha256=$inputPin};resources=$rows;archive_index_inventory=$inventory;code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;large_archive_sha_operations=0;limits=@('Full archive hashes are not recomputed. Exact extracted payload SHA and stable provider metadata are recorded.','Index order is not asserted as precedence; differing collisions must be adjudicated.','No serialization, candidate, game, save, fact, build or package write.')}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $O 'manifest.json') -Encoding utf8NoBOM
@{targets=$names.Count;found=$rows.Count;opaque=@($rows|Where-Object status -eq 'OPAQUE').Count;indexes=$inventory.Count;output=$O}|ConvertTo-Json -Compress
