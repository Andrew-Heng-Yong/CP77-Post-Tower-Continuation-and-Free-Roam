param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$root=Join-Path $WorkspaceRoot 'research\activity_batches_b1\native_sources'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=$null
$archivePath='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archivePath,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
# Read official resources into this new audit only. No game/cache/save writes.
# Include scenes/community to audit casts and scene-only facts; test .quest and
# debug phases are deliberately excluded from this production-source selection.
$entries=@($archive.Files.Values|Where-Object {
 $_.Name -match '^base\\quest\\minor_quests\\mq(011|013|030)\\' -and
 $_.Extension -in @('.scene','.community','.questphase') -and
 $_.Name -notmatch '\\test\\'
}|Sort-Object Name)
if($entries.Count -lt 6){throw 'Missing expected production scene/owner resources'}
$inventory=@()
foreach($entry in $entries){
 $raw=Join-Path $root ('raw\'+$entry.Name);$json=Join-Path $root ('json\'+$entry.Name+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new()
 try{
  $entry.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  if(Test-Path -LiteralPath $raw){
   if((Get-FileHash -LiteralPath $raw).Hash -ne $hash){throw 'Changed source; preserve prior B1 evidence'}
   if(-not (Test-Path -LiteralPath $json)){throw 'Existing source has missing JSON'}
  }else{[IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json}
  $inventory+=,[ordered]@{resource=$entry.Name;archive=$archivePath;raw_sha256=$hash;json_sha256=(Get-FileHash -LiteralPath $json).Hash}
 }finally{$m.Dispose()}
}
$inventoryPath=Join-Path $root 'inventory.json'
$data=($inventory|ConvertTo-Json -Depth 6)
if(Test-Path -LiteralPath $inventoryPath){
 if([IO.File]::ReadAllText($inventoryPath) -ne $data){throw 'Changed inventory; preserve B1 evidence'}
}else{[IO.File]::WriteAllText($inventoryPath,$data,[Text.UTF8Encoding]::new($false))}
[ordered]@{extracted=$entries.Count;game_writes=0;save_writes=0;inventory=$inventoryPath}|ConvertTo-Json
