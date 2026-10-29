$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$rows=@()
foreach($name in @('ep1_1_nightcity.archive','ep1_2_gamedata.archive','basegame_4_gamedata.archive')){
 $path=Join-Path 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\content' $name
 if(!(Test-Path $path)){$path=Join-Path 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1' $name}
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$arc).ToString() -ne 'NoError'){throw $name}
 foreach($e in $arc.Files.Values){if($e.Name -match '^ep1\\.*\.questphase$' -and ($e.Name -match '(openworld|community|global|ep1\.questphase|ep1_main|q307)')){$rows+=@{depot=$e.Name;archive=$path;hash=$e.Key.ToString()}}}
}
$rows|ConvertTo-Json -Depth 4|Set-Content (Join-Path $PSScriptRoot 'ep1_resource_inventory_01.json')
@{count=$rows.Count;depots=@($rows|ForEach-Object{$_.depot}|Where-Object {$_ -match '(root|main|content|global|community|ep1\.questphase)'})}|ConvertTo-Json -Depth 3
