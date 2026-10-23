param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research/gig_restoration/padre_phone_u5'
if(Test-Path (Join-Path $out 'inventory.json')){throw 'Existing source audit pinned'}
$targets=@('base\quest\holocalls\padre\padre_holocall.questphase','base\quest\holocalls\padre\padre_cleanup.questphase','base\quest\holocalls\padre\padre_holocall.scene')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive',$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Archive read failed'}
$rows=@()
foreach($depot in $targets){
 $entry=@($ar.Files.Values|Where-Object Name -ceq $depot);if($entry.Count -ne 1){throw "Missing official resource: $depot"}
 $raw=Join-Path $out ('sources/raw/'+$depot);$json=Join-Path $out ('sources/json/'+$depot+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $mem=[IO.MemoryStream]::new();try{$entry[0].Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray())}finally{$mem.Dispose()}
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=,[ordered]@{depot=$depot;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($rows|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$rows.depot
