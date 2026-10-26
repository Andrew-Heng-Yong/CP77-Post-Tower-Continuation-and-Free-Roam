param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $ws ('research/sidejobs_s29/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable extraction exists'}
New-Item -ItemType Directory $out|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc'
$files=@(Get-ChildItem -LiteralPath (Join-Path $game 'content') -File -Filter '*.archive')+@(Get-ChildItem -LiteralPath (Join-Path $game 'ep1') -File -Filter '*.archive')
$rows=@();$parentCandidates=@();$archives=@()
foreach($file in $files){
 $arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable archive '+$file.FullName)}
 $used=$false
 foreach($entry in $arc.Files.Values){
  $dep=$entry.Name
  if($dep -match '(?i)(minorquests|sidequests|phone|default_dialogs|q003\.quest|q305\.quest|world_stories|street_stories).*\.quest(phase)?$' -and $dep -notmatch '(?i)\\(bugfixing|scenes)\\'){$parentCandidates+=,@{depot=$dep;archive=$file.BaseName}}
  $selected=$dep -match '^base\\quest\\minor_quests\\mq(016|017|018|028|036|040|042|058|059|060)\\.+\.(questphase|scene)$' -or $dep -match '^base\\quest\\side_quests\\sq(023|025)\\.+\.(questphase|scene)$' -or $dep -match '^base\\quest\\main_quests\\prologue\\q003\\(q003\.questphase|phases\\q003_stout\.questphase|scenes\\q003_08_stout\.scene)$' -or $dep -match '^ep1\\quest\\main_quests\\q305\\(q305\.questphase|phases\\q305_12_haunted_weapon\.questphase)$' -or $dep -match '^ep1\\openworld\\(world_stories\\wst_ep1_09|street_stories\\sts_ep1_12)\\.+\.(questphase|scene)$' -or $dep -match '^(base\\quest\\(minorquests|sidequests|default_dialogs)|ep1\\quest\\ep1)\.quest(phase)?$'
  if(!$selected){continue};$used=$true
  $raw=Join-Path $out ($file.BaseName+'/raw/'+$dep);$json=Join-Path $out ($file.BaseName+'/json/'+$dep+'.json')
  New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null
  $stream=[IO.File]::Create($raw);try{$entry.Extract($stream)}finally{$stream.Dispose()}
  Export-Cr2wJson (Read-Cr2wFile $raw) $json
  $rows+=,@{depot=$dep;archive=$file.FullName;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');sha256=(Get-FileHash -LiteralPath $raw).Hash;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
 }
 if($used){$archives+=,@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o')}}
}
$result=[ordered]@{status='CURRENT_OFFICIAL_SOURCE_EXTRACTION';rows=$rows;archives=$archives;parent_candidates=$parentCandidates;tool_sha256=(Get-FileHash (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/WolvenKit.RED4.dll')).Hash;script_sha256=(Get-FileHash $PSCommandPath).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{resources=$rows.Count;unique=@($rows.depot|Sort-Object -Unique).Count;output=$out}|ConvertTo-Json
