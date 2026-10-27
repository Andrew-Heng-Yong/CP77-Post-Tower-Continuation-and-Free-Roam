Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $ws 'tools/shark_b7_2_helpers.ps1')
$h=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$b=$h.IndexOf('function ClearB5(');$e=$h.IndexOf('$allRoots=@{};')
. ([scriptblock]::Create($h.Substring($b,$e-$b)))
$p='research/sidejobs_s29/native_03/basegame_4_gamedata/raw/base/quest/minor_quests/minorquests.questphase'
$g=(Read-Cr2wFile (Join-Path $ws $p)).RootChunk.Graph.Chunk
$ed=EdgesB5 $g
$want=[Collections.Generic.HashSet[int]]::new();[void]$want.Add(20)
for($pass=0;$pass -lt 7;$pass++){
 foreach($v in $ed){if($want.Contains([int]$v[2])){[void]$want.Add([int]$v[0])}}
}
foreach($v in $ed){if($want.Contains([int]$v[0]) -and $want.Contains([int]$v[2])){Write-Output ($v -join ' | ')}}
Write-Output ('IDS '+(($want|Sort-Object)-join ','))
