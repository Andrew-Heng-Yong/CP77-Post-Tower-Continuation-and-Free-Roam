param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output=Join-Path $PSScriptRoot 'source_01'
if(Test-Path -LiteralPath $output){throw 'Fresh capture output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$native=@(
 'base\quest\cyberpunk2077.quest',
 'base\quest\cyberpunk2077.questphase',
 'base\quest\minor_quests\minorquests.questphase',
 'base\quest\minor_quests\mq016\mq016_bartmoss.questphase',
 'base\quest\minor_quests\mq016\phases\mq016_00_shard.questphase',
 'base\quest\minor_quests\mq016\phases\mq016_01_freezer.questphase',
 'base\quest\minor_quests\mq016\phases\mq016_02_afterlife.questphase'
)
$private=@('towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase')
$private+=@($native|Where-Object{$_ -like '*\mq016\*'}|ForEach-Object{'towercontinued\sidejobs_s29\native\'+$_})
$depots=@($native)+@($private)
$hashes=[WolvenKit.Common.Services.HashService]::new();$hashes.Load()
$queries=@{}
foreach($depot in $depots){$queries[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)]=$depot}
New-Item -ItemType Directory -Path $output|Out-Null
$rows=@();$archives=@()
foreach($path in Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Filter '*.archive' -Recurse -File){
 $archive=$null
 $status=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hashes,[ref]$archive).ToString()
 if($status -cne 'NoError'){throw "Unreadable archive index: $($path.FullName)"}
 $archives+=,@{path=$path.FullName;bytes=$path.Length;mtime_utc=$path.LastWriteTimeUtc.ToString('o')}
 foreach($key in $queries.Keys){
  if(-not $archive.Files.ContainsKey([uint64]$key)){continue}
  $depot=$queries[$key]
  $raw=Join-Path $output ($path.BaseName+'/'+$depot)
  New-Item -ItemType Directory -Force -Path (Split-Path $raw -Parent)|Out-Null
  $memory=[IO.MemoryStream]::new()
  try{$archive.Files[[uint64]$key].Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
  $resource=Read-Cr2wFile $raw
  Export-Cr2wJson $resource ($raw+'.json')
  $rows+=,@{archive=$path.FullName;depot=$depot;key=$key.ToString();raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=($raw+'.json');json_sha256=(Get-FileHash -LiteralPath ($raw+'.json')).Hash}
 }
}
$missing=@($depots|Where-Object{$depot=$_;-not @($rows|Where-Object{$_.depot -ceq $depot}).Count})
@{schema=1;status='READ_ONLY_PROVIDER_CAPTURE';archives=$archives;queries=$depots;resources=$rows;missing=$missing;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $output 'providers.json') -Encoding utf8NoBOM
if($missing.Count){throw ('Missing depots: '+($missing -join ', '))}
Write-Output "Captured $($rows.Count) resources for $($depots.Count) depots from $($archives.Count) archive indices; no game/save writes."
