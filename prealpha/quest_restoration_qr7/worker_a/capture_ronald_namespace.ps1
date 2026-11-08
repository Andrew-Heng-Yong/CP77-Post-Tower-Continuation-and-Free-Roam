param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[void][Reflection.Assembly]::LoadFrom((Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll'))
$o=[IO.Path]::GetFullPath((Join-Path $w $Output))
if(Test-Path -LiteralPath $o){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $o|Out-Null
$planPath=Join-Path $w 'prealpha/quest_restoration_qr7/worker_b/registration_plan_01.json'
if((Get-FileHash -LiteralPath $planPath).Hash -ne '169C3FBDE2584DF2ED363A9C6601313FFCDBE73099B90F08054C89BEC803E4ED'){throw 'Registration declaration drift'}
$depots=@('towercontinued\quest_restoration_qr7\ronald_news_future.questphase','towercontinued\quest_restoration_qr7\ronald_news_markers.streamingsector','towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock','ep1\quest\ep1.quest')
$keys=@{};foreach($d in $depots){$keys[[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d)]=$d}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archives=@();$hits=@();$i=0
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -File -Filter '*.archive'|Sort-Object FullName){
 $before=@($f.Length,$f.LastWriteTimeUtc.Ticks);$a=$null
 $status=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString()
 if($status -ne 'NoError'){throw 'Archive index unreadable'}
 $found=@()
 foreach($key in $keys.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue}
  $d=$keys[$key];$found+=,$d;$row=@{depot=$d;fnv64=$key;provider=$f.FullName}
  if($d -eq 'ep1\quest\ep1.quest'){
   $raw=Join-Path $o ('parent_'+$i+'.quest');$i++;$memory=[IO.MemoryStream]::new()
   try{$a.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
   $json=$raw+'.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json;$row.raw=$raw;$row.raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;$row.json=$json;$row.json_sha256=(Get-FileHash -LiteralPath $json).Hash
  }
  $hits+=,$row
 }
 $f.Refresh();if($f.Length -ne $before[0] -or $f.LastWriteTimeUtc.Ticks -ne $before[1]){throw 'Provider changed during read'}
 $archives+=@{path=$f.FullName;bytes=$before[0];mtime_utc_ticks=$before[1];index_entries=$a.Files.Count;read_status=$status;matches=$found}
}
function Convert-YamlNode($n){
 if($n -is [YamlDotNet.RepresentationModel.YamlScalarNode]){return [ordered]@{kind='scalar';value=$n.Value;tag=[string]$n.Tag}}
 if($n -is [YamlDotNet.RepresentationModel.YamlSequenceNode]){return [ordered]@{kind='sequence';items=@($n.Children|ForEach-Object {Convert-YamlNode $_})}}
 if($n -is [YamlDotNet.RepresentationModel.YamlMappingNode]){return [ordered]@{kind='mapping';entries=@($n.Children.GetEnumerator()|ForEach-Object {[ordered]@{key=(Convert-YamlNode $_.Key);value=(Convert-YamlNode $_.Value)}})}}
 throw ('Unsupported YAML node '+$n.GetType().FullName)
}
$configs=@();$paths=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -File -Filter '*.xl'|ForEach-Object {$_.FullName})
$paths+=Join-Path $w 'prealpha/quest_restoration_qr7/candidate_01/package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
foreach($p in $paths){
 $row=@{path=$p;sha256=(Get-FileHash -LiteralPath $p).Hash;candidate=$p.StartsWith((Join-Path $w 'prealpha/quest_restoration_qr7/candidate_01'),[StringComparison]::OrdinalIgnoreCase)}
 $stream=[YamlDotNet.RepresentationModel.YamlStream]::new();$reader=[IO.StringReader]::new([IO.File]::ReadAllText($p))
 try{$stream.Load($reader);$row.parse_status='PARSED';$row.documents=@($stream.Documents|ForEach-Object {Convert-YamlNode $_.RootNode})}catch{$row.parse_status='BLOCKED';$row.error=$_.Exception.ToString()}finally{$reader.Dispose()}
 $configs+=,$row
}
@{scope='Read-only exact three new depot namespace plus fresh native parent and all installed XL ASTs/current candidate XL; no registration applied';registration_plan=$planPath;registration_plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;depots=$depots;archive_index_inventory=$archives;matching_providers=$hits;xl_configs=$configs;yaml_parser=[YamlDotNet.RepresentationModel.YamlStream].Assembly.FullName;yaml_parser_sha256=(Get-FileHash -LiteralPath (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll')).Hash;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;candidate_writes=0;game_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $o 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Captured '+$archives.Count+' archive indexes and '+$configs.Count+' XL configs')
