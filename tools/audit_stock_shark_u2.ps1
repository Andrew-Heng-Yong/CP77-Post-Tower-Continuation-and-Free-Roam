param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research/gig_restoration/stock_shark_u2'
if(Test-Path (Join-Path $out 'install_receipt.json')){throw 'Installed evidence pinned'}
$targets=@('base\quest\holocalls\reggie\reggie_holocall.questphase','base\quest\holocalls\reggie\reggie_cleanup.questphase','base\quest\holocalls\reggie\reggie_holocall.scene','base\quest\holocalls\holocall_initializers.questphase','base\quest\holocalls\holocall_interrupts.questphase','base\quest\holocalls\holocall_cleanup.questphase','base\quest\cyberpunk2077.quest','base\quest\persistent_content.questphase')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive('C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive',$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Official archive read failed'}
$rows=@()
foreach($depot in $targets){
 $entry=@($ar.Files.Values|Where-Object Name -ceq $depot);if($entry.Count -ne 1){throw "Missing official resource: $depot"}
 $raw=Join-Path $out ('sources/raw/'+$depot);$json=Join-Path $out ('sources/json/'+$depot+'.json')
 if(Test-Path $raw){throw 'Preserve previous extraction'}
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $m=[IO.MemoryStream]::new();try{$entry[0].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=,[ordered]@{depot=$depot;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash}
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($rows|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$rows.depot
