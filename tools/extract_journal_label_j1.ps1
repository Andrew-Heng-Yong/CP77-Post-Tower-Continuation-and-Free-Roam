param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$root=Join-Path $WorkspaceRoot 'research\journal_label_j1\native_widget'
New-Item -ItemType Directory -Force $root|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=$null
$path='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_1_engine.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Read failed'}
$inventory=@()
foreach($entry in @($archive.Files.Values|Where-Object {$_.Extension -eq '.inkwidget' -and $_.Name -match '(quest.?log|journal)'})){
 $raw=Join-Path $root ('raw\'+$entry.Name);$json=Join-Path $root ('json\'+$entry.Name+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new()
 try{
  $entry.Extract($m);$bytes=$m.ToArray();$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  if(Test-Path $raw){if((Get-FileHash $raw).Hash -ne $hash){throw 'Changed source'}}else{[IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json}
  $inventory+=,[ordered]@{resource=$entry.Name;sha256=$hash;json_sha256=(Get-FileHash $json).Hash}
 }finally{$m.Dispose()}
}
[IO.File]::WriteAllText((Join-Path $root 'inventory.json'),($inventory|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$inventory | ConvertTo-Json
