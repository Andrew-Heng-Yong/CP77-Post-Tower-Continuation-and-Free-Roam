param([string]$Revision='resume_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};');if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'};. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
. (Join-Path $PSScriptRoot 'build.ps1')
if($Revision -cnotmatch '^resume_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $WorkspaceRoot ('research/sidejobs_s23/base_a_v2/'+$Revision);if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
$spec=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw|ConvertFrom-Json
$oldPath=Join-Path $WorkspaceRoot $spec.reused_manifest
if((Get-FileHash -LiteralPath $oldPath).Hash -cne $spec.reused_manifest_sha256){throw 'Reused manifest drift'}
$old=Get-Content -LiteralPath $oldPath -Raw|ConvertFrom-Json
foreach($p in $old.source_pins.PSObject.Properties){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p.Name)).Hash -cne $p.Value){throw ('Reused source drift: '+$p.Name)}}
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@();$resources=[ordered]@{};$pins=[ordered]@{};$common=[ordered]@{}
foreach($p in $old.common.PSObject.Properties){$common[$p.Name]=$p.Value}
foreach($p in $old.source_pins.PSObject.Properties){$pins[$p.Name]=$p.Value}
# Reuse frozen native wrappers, never rerun their pinned builders.
foreach($r in $old.rows){
 if((Get-FileHash -LiteralPath $r.raw).Hash -cne $r.sha256){throw 'Reused payload drift'}
 $raw=Join-Path (Join-Path $out 'source') $r.depot;New-Item -ItemType Directory -Path (Split-Path -Parent $raw) -Force|Out-Null;Copy-Item -LiteralPath $r.raw -Destination $raw
 $json=Join-Path $out ($r.id+'.json');Copy-Item -LiteralPath $r.json -Destination $json
 $rows+=,@{id=$r.id;depot=$r.depot;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;readback_sha256=(Get-FileHash -LiteralPath $json).Hash;reused=$true}
 $resources[$r.depot]=$r.sha256
 $pins[[IO.Path]::GetRelativePath($WorkspaceRoot,$r.raw).Replace('\','/')]=(Get-FileHash -LiteralPath $r.raw).Hash
 $pins[[IO.Path]::GetRelativePath($WorkspaceRoot,$r.json).Replace('\','/')]=(Get-FileHash -LiteralPath $r.json).Hash
}
$s=@($spec.owners|Where-Object tag -EQ 'PTFRS23_MQ007_RESUME')[0]
$native=(Read-Cr2wFile (Join-Path $WorkspaceRoot $s.resume_source)).RootChunk.Graph.Chunk
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($id in $s.resume_nodes){$oldNode=Get-QuestNode $native $id;$n=$oldNode.DeepCopy();ClearB5 $n;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $oldNode.PhaseGraph.Chunk};AddNodeB5 $g $n}
$edges=@();foreach($e in $s.resume_edges){$edges+=,@($e[0],$e[1],$e[2],$e[3])};RebuildB5 $g $edges
$boot=New-S23BaseAResumeGraph $WorkspaceRoot $common $s.tag
foreach($entry in @(@{graph=$g;depot=$s.resume_depot;name='mq007_resume_owner'},@{graph=$boot.graph;depot=$s.depot;name='mq007_resume_boot'})){
 $res=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $res Graph $entry.graph;$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$res
 $raw=Join-Path (Join-Path $out 'source') $entry.depot;New-Item -ItemType Directory -Path (Split-Path -Parent $raw) -Force|Out-Null;Write-Cr2wFile $file $raw
 $json=Join-Path $out ($entry.name+'.json');Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $h=(Get-FileHash -LiteralPath $raw).Hash;$resources[$entry.depot]=$h
 $rows+=,@{id=$entry.name;depot=$entry.depot;raw=$raw;sha256=$h;json=$json;readback_sha256=(Get-FileHash -LiteralPath $json).Hash;reused=$false}
}
foreach($p in @($spec.reused_manifest,'research/sidejobs_s23/base_a/audit_03/tests.json','prealpha/sidejobs_s23/base_a_v2/prepare.py','prealpha/sidejobs_s23/base_a_v2/contract.json','prealpha/sidejobs_s23/base_a_v2/build.ps1','prealpha/sidejobs_s23/base_a_v2/build_component.ps1','prealpha/sidejobs_s23/base_a_v2/test.py')){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
$manifest=@{status='WORKSPACE_COMPONENTS_NOT_INSTALLED';source_pins=$pins;common=$common;resources=$resources;rows=$rows;boots=@($spec.owners|ForEach-Object {$_.depot});contract='prealpha/sidejobs_s23/base_a_v2/contract.json';reused_manifest=$spec.reused_manifest;native_progress_resets=$false;history_confirmation_fact=$s.history_confirmation_fact}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($manifest|ConvertTo-Json -Depth 35),[Text.UTF8Encoding]::new($false))
@{status='EXPORTED';output=$out;resources=$rows.Count;boots=$spec.owners.Count}|ConvertTo-Json
