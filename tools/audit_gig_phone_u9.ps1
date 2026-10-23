param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research/gig_restoration/gig_phone_u9'
if(Test-Path (Join-Path $out 'inventory.json')){throw 'Source inventory exists; preserve it'}
$contacts=@('dakota','dino','mr_hands','muamar','padre','reggie','rogue','wakako')
$targets=@('base\quest\holocalls\holocall_initializers.questphase','base\quest\holocalls\holocall_cleanup.questphase','base\quest\holocalls\holocall_interrupts.questphase')
foreach($c in $contacts){$targets+=@("base\quest\holocalls\$c\${c}_holocall.questphase","base\quest\holocalls\$c\${c}_cleanup.questphase")}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$ar=$null
$archive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content\basegame_4_gamedata.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Official archive read failed'}
$rows=@()
foreach($depot in $targets){
 $entry=@($ar.Files.Values|Where-Object Name -ceq $depot);if($entry.Count -ne 1){throw "Missing official resource: $depot"}
 $raw=Join-Path $out ('sources/raw/'+$depot);$json=Join-Path $out ('sources/json/'+$depot+'.json')
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw),(Split-Path -Parent $json)|Out-Null
 $mem=[IO.MemoryStream]::new();try{$entry[0].Extract($mem);[IO.File]::WriteAllBytes($raw,$mem.ToArray())}finally{$mem.Dispose()}
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=,[ordered]@{depot=$depot;raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash;source_archive=$archive}
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($rows|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$rows.depot
