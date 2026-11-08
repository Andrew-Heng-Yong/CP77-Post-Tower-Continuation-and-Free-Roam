param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskRoot=(Get-Location).Path
. (Join-Path $taskRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $taskRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[void][Reflection.Assembly]::LoadFrom((Join-Path $taskRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll'))
$taskOut=[IO.Path]::GetFullPath((Join-Path $taskRoot $Output))
$allowed=[IO.Path]::GetFullPath((Join-Path $taskRoot 'prealpha/quest_restoration_qr8/worker_a'))+[IO.Path]::DirectorySeparatorChar
if(-not $taskOut.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Output outside worker scope'}
if(Test-Path -LiteralPath $taskOut){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $taskOut|Out-Null
$depots=@('towercontinued\quest_restoration_qr7\ronald_news_future.questphase','towercontinued\quest_restoration_qr7\ronald_news_markers.streamingsector','towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock','ep1\quest\ep1.quest')
$keys=@{};foreach($depot in $depots){$keys[[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)]=$depot}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$candidate=Join-Path $taskRoot 'prealpha/quest_restoration_qr7/candidate_01'
$taskArchives=@(Get-ChildItem -LiteralPath $game -Recurse -File -Filter '*.archive'|Sort-Object FullName)
$taskArchives+=Get-Item -LiteralPath (Join-Path $candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load();$archives=@();$hits=@();$ordinal=0
foreach($file in $taskArchives){
 $before=@($file.Length,$file.LastWriteTimeUtc.Ticks);$archive=$null
 $status=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive).ToString()
 if($status -ne 'NoError'){throw ('Archive index unreadable: '+$file.FullName)}
 $found=@();$staged=$file.FullName.StartsWith($candidate,[StringComparison]::OrdinalIgnoreCase)
 $location=if($staged){'QR7_STAGED_NOT_INSTALLED'}elseif($file.FullName -match '\\archive\\pc\\'){ 'NATIVE_OR_MOD_PC' }elseif($file.FullName -match '\\red4ext\\plugins\\'){ 'PLUGIN_ARCHIVE_SUPERSET' }else{'ON_DISK_STORAGE_LOAD_NOT_ASSERTED'}
 foreach($key in $keys.Keys){
  if(-not $archive.Files.ContainsKey([uint64]$key)){continue}
  $depot=$keys[$key];$found+=,$depot;$raw=Join-Path $taskOut ('provider_'+$ordinal+'.'+[IO.Path]::GetExtension($depot).TrimStart('.'));$ordinal++
  $memory=[IO.MemoryStream]::new()
  try{$archive.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
  $json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
  $hits+=,@{depot=$depot;fnv64=$key;provider=$file.FullName;classification=$location;candidate=$staged;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
 }
 $file.Refresh();if($file.Length -ne $before[0] -or $file.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'Provider changed during read'}
 $archives+=@{path=$file.FullName;classification=$location;bytes=$before[0];mtime_utc_ticks=$before[1];index_entries=$archive.Files.Count;read_status=$status;matches=$found;full_archive_sha='Not rehashed: targeted index+extracted payload verification; coordinator pins canonical candidate'}
}
function Convert-YamlNode($node){
 if($node -is [YamlDotNet.RepresentationModel.YamlScalarNode]){return [ordered]@{kind='scalar';value=$node.Value;tag=[string]$node.Tag}}
 if($node -is [YamlDotNet.RepresentationModel.YamlSequenceNode]){return [ordered]@{kind='sequence';items=@($node.Children|ForEach-Object {Convert-YamlNode $_})}}
 if($node -is [YamlDotNet.RepresentationModel.YamlMappingNode]){return [ordered]@{kind='mapping';entries=@($node.Children.GetEnumerator()|ForEach-Object {[ordered]@{key=(Convert-YamlNode $_.Key);value=(Convert-YamlNode $_.Value)}})}}
 throw ('Unsupported YAML node '+$node.GetType().FullName)
}
$configs=@();$paths=@(Get-ChildItem -LiteralPath $game -Recurse -File -Filter '*.xl'|Sort-Object FullName|ForEach-Object {$_.FullName})
$paths+=Join-Path $candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
foreach($path in $paths){
 $file=Get-Item -LiteralPath $path;$before=@($file.Length,$file.LastWriteTimeUtc.Ticks)
 $row=@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash;candidate=$path.StartsWith($candidate,[StringComparison]::OrdinalIgnoreCase);size=$before[0];mtime_utc_ticks=$before[1]}
 $stream=[YamlDotNet.RepresentationModel.YamlStream]::new();$reader=[IO.StringReader]::new([IO.File]::ReadAllText($path))
 try{$stream.Load($reader);$row.parse_status='PARSED';$row.documents=@($stream.Documents|ForEach-Object {Convert-YamlNode $_.RootNode})}catch{$row.parse_status='BLOCKED';$row.error=$_.Exception.ToString()}finally{$reader.Dispose()}
 $file.Refresh();if($file.Length -ne $before[0] -or $file.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'XL changed during read'}
 $configs+=,$row
}
@{scope='Bounded four-depot query: all on-disk game archives conservative superset plus staged QR7 archive; all on-disk XL ASTs includes ArchiveXL Bundle metadata and plugin registrations; no loader execution asserted';depots=$depots;archive_index_inventory=$archives;matching_providers=$hits;xl_configs=$configs;yaml_parser=[YamlDotNet.RepresentationModel.YamlStream].Assembly.FullName;yaml_parser_sha256=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll')).Hash;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;candidate_writes=0;game_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $taskOut 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Captured '+$archives.Count+' archive indexes, '+$configs.Count+' XL configs and '+$hits.Count+' matching providers')
