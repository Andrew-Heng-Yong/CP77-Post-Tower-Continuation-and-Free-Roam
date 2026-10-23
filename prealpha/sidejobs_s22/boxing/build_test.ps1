param([string]$Revision='audit_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
. (Join-Path $PSScriptRoot 'build.ps1')
if($Revision -cnotmatch '^audit_\d{2}$'){throw 'Invalid audit revision'}
$out=Join-Path $WorkspaceRoot ('research/sidejobs_s22/boxing/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable audit exists'}
New-Item -ItemType Directory -Path $out|Out-Null
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$result=New-S22BoxingGraph $WorkspaceRoot $common
$resource=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $resource Graph $result.graph
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$resource
$raw=Join-Path $out 'mq025_progress.questphase';Write-Cr2wFile $file $raw
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out 'mq025_progress.json')
$pins=[ordered]@{}
foreach($p in @('prealpha/sidejobs_s22/boxing/build.ps1','prealpha/sidejobs_s22/boxing/build_test.ps1','prealpha/sidejobs_s22/boxing/contract.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1',$result.spec.native_source,($result.spec.native_source.Replace('/raw/','/json/')+'.json'))){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),(@{status='WORKSPACE_GRAPH_ONLY_NOT_PACKED_OR_INSTALLED';source_pins=$pins;common=$common;guard_equal=$result.guard_equal;depot=$result.depot;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash}|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status='WORKSPACE_GRAPH_EXPORTED';output=$out}|ConvertTo-Json
