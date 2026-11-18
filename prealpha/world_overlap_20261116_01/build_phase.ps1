# New private phase uses the final authored native cleanup state; no world copies.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pins=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'work/inputs.json') -Raw|ConvertFrom-Json
$out=Join-Path $PSScriptRoot 'work/graph_01'
if(Test-Path -LiteralPath $out){throw 'Fresh graph output required'}
foreach($p in @($pins.shell,$pins.native_cleanup)){if((Get-FileHash -LiteralPath $p.raw).Hash -cne $p.sha256){throw 'Source drift'}}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$shell=Read-Cr2wFile $pins.shell.raw
$native=Read-Cr2wFile $pins.native_cleanup.raw
if($shell.RootChunk.PhasePrefabs.Count -ne 0 -or $shell.RootChunk.InplacePhases.Count -ne 0){throw 'Unexpected foundation support'}
$params=@((Get-QuestNode $native.RootChunk.Graph.Chunk 22).Type.Chunk.Params|Where-Object {$_.PrefabNodeRef.ToString() -ceq $pins.native_cleanup_owner})
if($params.Count -ne 1 -or $params[0].VariantStates.Count -ne 2){throw 'Native final cleanup pair is not unique'}
$pair=$params[0]
if($pair.VariantStates[0].Name.ToString() -cne 'q307_final_scene' -or $pair.VariantStates[0].Show.ToString() -cne 'False' -or $pair.VariantStates[1].Name.ToString() -cne 'q307_final_scene_hide' -or $pair.VariantStates[1].Show.ToString() -cne 'True'){throw 'Native final state changed'}
$condition=(Get-QuestNode $shell.RootChunk.Graph.Chunk 2).Condition.Chunk.DeepCopy()
foreach($fact in @(@('PTFRMV_Applied',1),@('PTFRWO1_CleanupPermit',1),@('PTFRWO1_CleanupDone',0))){Add-RedHandle $condition.Conditions (New-FactCondition $fact[0] $fact[1] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$pause=(Get-QuestNode $shell.RootChunk.Graph.Chunk 2).DeepCopy()
$pause.Id=[uint16]2
foreach($socket in $pause.Sockets){$socket.Chunk.Connections.Clear()}
Set-RedHandleProperty $pause Condition ($condition.DeepCopy())
$toggle=(Get-QuestNode $native.RootChunk.Graph.Chunk 22).DeepCopy()
$toggle.Id=[uint16]4
foreach($socket in $toggle.Sockets){$socket.Chunk.Connections.Clear()}
$toggle.Type.Chunk.Params.Clear()
$exact=$pair.DeepCopy();$exact.PrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit([string]$pins.owner)
[void]$toggle.Type.Chunk.Params.Add($exact)
$file=$shell;$g=$file.RootChunk.Graph.Chunk;$g.Nodes.Clear()
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRWO1_CleanupRegistered' 1),$pause,(New-ConditionNode 3 ($condition.DeepCopy())),$toggle,(New-SetFactNode 5 'PTFRWO1_CleanupDone' 1),(New-SetFactNode 6 'PTFRWO1_CleanupPermit' 0),(New-OutputNode 7 'Out1'))){Add-RedHandle $g.Nodes $n}
$edges=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'True',4,'In'),@(3,'False',2,'In'),@(4,'Out',5,'In'),@(5,'Out',6,'In'),@(6,'Out',7,'In'))
foreach($edge in $edges){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $edge[0]) $edge[1]) (Get-QuestSocket (Get-QuestNode $g $edge[2]) $edge[3]))}
$raw=Join-Path $out ('source/'+$pins.depot)
Write-Cr2wFile $file $raw
Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out 'readback.json')
@{depot=$pins.depot;path=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash;json=(Join-Path $out 'readback.json');json_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'readback.json')).Hash;nodes=8;game_writes=0}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
Write-Output 'Built and read back an eight-node native cleanup phase with no acquired prefabs.'
