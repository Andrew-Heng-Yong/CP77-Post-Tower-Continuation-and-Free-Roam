param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research/gig_restoration/family_b7'
if(Test-Path (Join-Path $out 'install_receipt.json')){throw 'Installed evidence pinned'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive',$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Official archive read failed'}
$rows=@()
foreach($entry in $ar.Files.Values){
 if($entry.Name -notmatch '^base\\open_world\\fixers\\[^\\]+\\phases\\[^\\]+\.questphase$'){continue}
 $raw=Join-Path $out ('fixers/raw/'+$entry.Name);$json=Join-Path $out ('fixers/json/'+$entry.Name+'.json')
 if(Test-Path $raw){throw 'Preserve previous extraction'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new();try{$entry.Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=,[ordered]@{depot=$entry.Name;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $out 'fixers/inventory.json'),($rows|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$rows.depot
