param([string]$Revision='audit_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};');if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'};. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
. (Join-Path $PSScriptRoot 'build.ps1')
if($Revision -cnotmatch '^audit_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $WorkspaceRoot ('research/sidejobs_s23/base_a/'+$Revision);if(Test-Path -LiteralPath $out){throw 'Immutable output exists'};New-Item -ItemType Directory -Path $out|Out-Null
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$rows=@();$spec=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw|ConvertFrom-Json
foreach($j in $spec.owners){
 $r=New-S23BaseAGraph $WorkspaceRoot $common $j.id
 $resource=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $resource Graph $r.graph;$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$resource
 $raw=Join-Path (Join-Path $out 'source') $j.depot;New-Item -ItemType Directory -Path (Split-Path -Parent $raw) -Force|Out-Null;Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ($j.id+'.json'))
 $rows+=,@{id=$j.id;depot=$j.depot;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=(Join-Path $out ($j.id+'.json'))}
}
$pins=[ordered]@{}
foreach($p in @('prealpha/sidejobs_s23/base_a/build.ps1','prealpha/sidejobs_s23/base_a/build_test.ps1','prealpha/sidejobs_s23/base_a/contract.json','prealpha/sidejobs_s23/base_a/prepare.py','prealpha/sidejobs_s23/base_a/audit.py','prealpha/sidejobs_s23/base_a/scene_audit.py','prealpha/sidejobs_s23/base_a/test.py','prealpha/sidejobs_s23/base_a/extract_audit.ps1','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','research/sidejobs_s23/live_20261016_01/capture.json',$spec.owners[0].native_source,($spec.owners[0].native_source.Replace('/raw/','/json/')+'.json'))){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
foreach($family in @('mq024','mq007','mq035','mq012','mq002','mq021','mq041','mq044')){
 foreach($kind in @('raw','json')){foreach($f in Get-ChildItem -LiteralPath (Join-Path $WorkspaceRoot ('research/activity_state_r3/native_sources/'+$kind+'/base/quest/minor_quests/'+$family)) -File -Recurse){$pins[[IO.Path]::GetRelativePath($WorkspaceRoot,$f.FullName).Replace('\','/')]=(Get-FileHash -LiteralPath $f.FullName).Hash}}
}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $WorkspaceRoot 'research/sidejobs_s23/base_a/native_02') -File -Recurse){$pins[[IO.Path]::GetRelativePath($WorkspaceRoot,$f.FullName).Replace('\','/')]=(Get-FileHash -LiteralPath $f.FullName).Hash}
$resources=[ordered]@{};foreach($r in $rows){$resources[$r.depot]=$r.sha256}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),(@{status='WORKSPACE_COMPONENTS_NOT_INSTALLED';source_pins=$pins;common=$common;resources=$resources;rows=$rows;boots=@($rows|ForEach-Object {$_.depot});contract='prealpha/sidejobs_s23/base_a/contract.json'}|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status='EXPORTED';output=$out;resources=$rows.Count}|ConvertTo-Json
