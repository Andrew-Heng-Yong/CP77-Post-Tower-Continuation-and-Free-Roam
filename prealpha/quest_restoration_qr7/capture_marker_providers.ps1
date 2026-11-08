param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$outputPath=[IO.Path]::GetFullPath((Join-Path $workspace $Output))
if(Test-Path -LiteralPath $outputPath){throw 'Fresh marker-provider output required'}
[IO.Directory]::CreateDirectory($outputPath)|Out-Null
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$depots=@('base\worlds\03_night_city\_compiled\default\ep1\always_loaded_0.streamingsector','base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock')
$keys=@{};foreach($depot in $depots){$keys[[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)]=$depot}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$matches=@();$archives=@();$idx=0
foreach($file in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -File -Filter '*.archive'){
 $archive=$null
 $status=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString()
 $archives+=@{path=$file.FullName;bytes=$file.Length;mtime_utc=$file.LastWriteTimeUtc.ToString('o');read_status=$status}
 if($status -ne 'NoError'){throw ('Provider archive unreadable: '+$file.FullName)}
 foreach($key in @($keys.Keys)){
  if(-not $archive.Files.ContainsKey([uint64]$key)){continue}
  $depot=$keys[$key];$raw=Join-Path $outputPath ('provider_'+$idx+[IO.Path]::GetExtension($depot));$memory=[IO.MemoryStream]::new()
  try{$archive.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
  $rawHash=(Get-FileHash -LiteralPath $raw).Hash
  $oldRaw=Join-Path $workspace ('research/phase2b_p4/staging_scan/'+$file.BaseName+'/raw/'+$depot.Replace('\','/'))
  $oldJson=Join-Path $workspace ('research/phase2b_p4/staging_scan/'+$file.BaseName+'/json/'+$depot.Replace('\','/')+'.json')
  $row=@{depot=$depot;fnv64=$key;provider=$file.FullName;raw=$raw;raw_sha256=$rawHash;old_raw=$oldRaw;old_raw_exists=(Test-Path -LiteralPath $oldRaw);old_json=$oldJson;old_json_exists=(Test-Path -LiteralPath $oldJson)}
  if($row.old_raw_exists){$row.old_raw_sha256=(Get-FileHash -LiteralPath $oldRaw).Hash;$row.old_raw_matches_current=($row.old_raw_sha256 -ceq $rawHash)}
  if($row.old_json_exists){$row.old_json_sha256=(Get-FileHash -LiteralPath $oldJson).Hash}
  try{
   $resource=Read-Cr2wFile $raw;$row.root_type=$resource.RootChunk.GetType().FullName
   $jp=$raw+'.json';Export-Cr2wJson $resource $jp;$row.json=$jp;$row.json_sha256=(Get-FileHash -LiteralPath $jp).Hash;$row.decode_status='FRESH_WOLVENKIT_9_1_EXPORT'
  }catch{$row.decode_status='BLOCKED';$row.decode_error=$_.Exception.ToString()}
  $matches+=,$row;$idx++
 }
}
@{scope='Fresh bounded actual-provider lookup plus payload hash and typed export. No game/runtime/build/save writes. Every matching archive retained; caller must reconcile staged candidate and provider precedence before declaring a winner.';depots=$depots;archive_inventory=$archives;providers=$matches;game_writes=0;save_writes=0;tool_script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $outputPath 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Captured '+$matches.Count+' exact provider payloads across '+$archives.Count+' archives')
