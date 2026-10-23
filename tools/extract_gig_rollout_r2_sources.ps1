param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\rollout_r2'
$catalogue=Get-Content (Join-Path $audit 'catalogue.json') -Raw|ConvertFrom-Json
$ids=@($catalogue.jobs|Where-Object {-not $_.native_resources.Count}|ForEach-Object {$_.id})
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$chosen=@{}
foreach($path in @(
 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive',
 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_2_gamedata.archive')){
 $archive=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
 foreach($entry in $archive.Files.Values){
  if($entry.Extension -notin @('.quest','.questphase')){continue}
  $match=$entry.Name -in @('base\open_world\street_stories\street_stories_dlc.questphase','ep1\openworld\street_stories\ep1_street_stories.questphase')
  foreach($id in $ids){if($entry.Name.Contains('\'+$id+'\') -or $entry.Name.Contains('\'+$id+'_')){$match=$true;break}}
  # EP1's later official override wins when it supplies the same resource.
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
   if((Get-FileHash $raw).Hash -ne [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))){throw 'Native source changed; preserve existing extraction'}
  }else{[IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json}
  $inventory+=,[ordered]@{resource=$name;archive=$item.archive;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash;raw_bytes=$bytes.Length}
 }finally{$memory.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $root 'inventory.json'),($inventory|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[ordered]@{status='NATIVE_EXTRACTION_ONLY';resources=$inventory.Count;game_writes=0;save_writes=0}|ConvertTo-Json
