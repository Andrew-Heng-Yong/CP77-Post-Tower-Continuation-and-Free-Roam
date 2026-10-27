Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $ws 'tools/shark_b7_2_helpers.ps1')
$h=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$b=$h.IndexOf('function ClearB5(');$e=$h.IndexOf('$allRoots=@{};')
. ([scriptblock]::Create($h.Substring($b,$e-$b)))
$files=@{
 pony='research/whitelist_outside_review_20261026/shape_pony_native_01/raw/base/open_world/mini_world_stories/badlands/se5/mws_se5_07/mws_se5_07.questphase'
 career='research/whitelist_outside_review_20261026/career_native_01/raw/base/open_world/mini_world_stories/watson/mws_wat_08/mws_wat_08.questphase'
 coaster='research/b0_world_interactions/extended/raw/base/quest/minor_quests/mq006/mq006.questphase'
}
foreach($name in $files.Keys){
 $g=(Read-Cr2wFile (Join-Path $ws $files[$name])).RootChunk.Graph.Chunk
 Write-Output ("`n"+$name+' root')
 $edges=EdgesB5 $g
 foreach($v in $edges){Write-Output ($v -join ' | ')}
 if($name -eq 'coaster'){
  foreach($id in @(15,50,51,52,53,55)){
   Write-Output ('coaster embedded '+$id)
   $sub=(Get-QuestNode $g $id).PhaseGraph.Chunk
   $nested=EdgesB5 $sub
   foreach($v in $nested){Write-Output ($v -join ' | ')}
  }
 }
}
