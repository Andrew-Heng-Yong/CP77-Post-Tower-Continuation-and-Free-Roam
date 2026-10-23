param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$root=Join-Path $WorkspaceRoot 'research\side_job_pilot_s1\sources'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=$null
$path='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Native archive read failed'}
$entries=@($archive.Files.Values|Where-Object {
 ($_.Name -match '\\mq005\\' -and $_.Extension -in @('.scene','.community','.questphase')) -or
 ($_.Extension -eq '.questphase' -and $_.Name -match '\\(minor_quests|heywood|vista_del_rey)\.questphase$')
})
$inventory=@()
foreach($entry in $entries){
 $raw=Join-Path $root ('raw\'+$entry.Name);$json=Join-Path $root ('json\'+$entry.Name+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new()
 try{
  $entry.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  if(Test-Path $raw){if((Get-FileHash $raw).Hash -ne $hash){throw 'Changed source; preserve evidence'}}
  else{[IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json}
  $inventory+=,[ordered]@{resource=$entry.Name;sha256=$hash;json_sha256=(Get-FileHash $json).Hash}
 }finally{$m.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $root 'inventory.json'),($inventory|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$inventory|Select-Object resource,sha256|ConvertTo-Json
