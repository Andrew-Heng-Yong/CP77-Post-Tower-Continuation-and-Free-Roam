$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$source=Join-Path $ws 'prealpha/resume_dispatcher_rd1_20261112_01/archive_04/archive_source'
$out=Join-Path $PSScriptRoot 'graphs_01'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
[void](New-Item -ItemType Directory -Path $out)
foreach($depot in @('base/quest/main_quests/epilogue/final_boards.questphase','ep1/quest/main_quests/q307/phases/q307_ending_board.questphase','towercontinued/postending_pa5/camera/owner.questphase','towercontinued/postending_pa5/camera/optics_reset.scene')){
 $p=Join-Path $source $depot
 $f=Read-Cr2wFile $p
 Export-Cr2wJson $f (Join-Path $out ((Split-Path $depot -Leaf)+'.json'))
 Write-Output "$depot $((Get-FileHash -LiteralPath $p).Hash)"
}
