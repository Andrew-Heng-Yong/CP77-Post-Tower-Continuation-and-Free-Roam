param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\activity_state_r3'
$definition=Get-Content (Join-Path $audit 'definition.json') -Raw|ConvertFrom-Json
$prefixes=@($definition.jobs|Where-Object category -eq 'side_job'|ForEach-Object {
 if($_.id -match '^(mq\d+|sq\d+|wst_ep1_\d+)(?:_|c\d)'){ $Matches[1] }
}|Select-Object -Unique)
$special=@('q304_splinter_stash','q304_car_retrieval','sq_q001_wilson','sq_q001_wakako','sts_ep1_08_steven_meeting_night_city')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$chosen=@{}
foreach($path in @(
 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive',
 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_2_gamedata.archive')){
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
 foreach($entry in $archive.Files.Values){
  if($entry.Extension -notin @('.quest','.questphase')){continue}
  $match=$false
  foreach($prefix in $prefixes+$special){
   if($entry.Name -match ('\\'+[regex]::Escape($prefix)+'(?:[\\_.]|c\d)')){$match=$true;break}
  }
  if($match){$chosen[$entry.Name]=@{entry=$entry;archive=$path}}
 }
}
$root=Join-Path $audit 'native_sources';$inventory=@()
foreach($name in @($chosen.Keys|Sort-Object)){
 $item=$chosen[$name];$memory=[IO.MemoryStream]::new()
 try{
  $item.entry.Extract($memory);$bytes=$memory.ToArray()
  $raw=Join-Path $root ('raw\'+$name);$json=Join-Path $root ('json\'+$name+'.json')
  New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
  if(Test-Path -LiteralPath $raw){
   if((Get-FileHash $raw).Hash -ne [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))){throw 'Native source changed; preserve extraction'}
  }else{[IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json}
  $inventory+=,[ordered]@{resource=$name;archive=$item.archive;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
 }finally{$memory.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $root 'inventory.json'),($inventory|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[ordered]@{status='NATIVE_SOURCE_EXTRACTION_ONLY';resources=$inventory.Count;game_writes=0;save_writes=0}|ConvertTo-Json
