Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$inventory=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inventory_archives_01.json') -Raw|ConvertFrom-Json
$keys=@{};foreach($a in $inventory.archives){foreach($m in $a.members){$keys[$m.key]=$m.depot}}
$mods='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod'
$files=[string[]]@(Get-ChildItem -LiteralPath $mods -Filter '*.archive' -File | Where-Object {$_.Name -notlike '*TowerContinued*'} | ForEach-Object FullName)
[Array]::Sort($files,[StringComparer]::OrdinalIgnoreCase)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$hits=[Collections.Generic.List[object]]::new()
foreach($path in $files){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Archive unreadable '+$path)}
 foreach($e in $a.Files.Values){if(!$keys.ContainsKey($e.Key.ToString())){continue};$hits.Add(@{archive=$path;depot=$keys[$e.Key.ToString()];key=$e.Key.ToString();name=$e.Name})}
}
$result=[ordered]@{status='EXTERNAL_MOD_COLLISION_SCAN_READ_ONLY';external_archives=$files.Count;ptfr_unique_keys=$keys.Count;collisions=$hits.ToArray();game_writes=0;save_writes=0}
$out=Join-Path $PSScriptRoot 'external_collisions_01.json';if(Test-Path -LiteralPath $out){throw 'Collision proof exists'}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
@{status=$result.status;external_archives=$result.external_archives;collisions=$hits.Count}|ConvertTo-Json
