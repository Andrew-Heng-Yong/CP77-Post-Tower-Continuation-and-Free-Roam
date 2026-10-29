Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$rows=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'ep1_prefab_candidates_01.json') -Raw|ConvertFrom-Json
$out=@();$resources=@()
foreach($row in $rows){foreach($ref in $row.resolved_candidates){
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($ref)
 $res='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
 $out+=@{id=$row.id;ref=$ref;hash=$hash.ToString();resource=$res};$resources+=$res
}}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'ep1_prefab_hashes_01.json'),($out|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllLines((Join-Path $PSScriptRoot 'ep1_prefab_resources_01.txt'),$resources,[Text.UTF8Encoding]::new($false))
