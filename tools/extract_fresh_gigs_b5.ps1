param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b5'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed B5 evidence pinned'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive',$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Official archive read failed'}
$rows=@()
foreach($name in @('base\open_world\fixers\wakako\phases\wakako.questphase','base\open_world\street_stories\westbrook\sts_westbrook.questphase')){
 $entry=@($ar.Files.Values|Where-Object {$_.Name -eq $name});if($entry.Count -ne 1){throw "Missing exact official source $name"}
 $raw=Join-Path $audit ('sources\raw\'+$name);$json=Join-Path $audit ('sources\json\'+$name+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new();try{$entry[0].Extract($m);$bytes=$m.ToArray()}finally{$m.Dispose()}
 if(Test-Path $raw){throw 'Preserve previous extraction'}
 [IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=,[ordered]@{depot=$name;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $audit 'sources\inventory.json'),($rows|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$rows|ConvertTo-Json -Depth 8
