param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$OutputPath=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r11\emmerick'
New-Item -ItemType Directory -Force $audit|Out-Null
if(-not $OutputPath){$OutputPath=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR11\source\towercontinued\afterlife_interactions_r8\emmerick.scene'}
$sourcePath=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR10\source\towercontinued\afterlife_interactions_r8\emmerick.scene'
$sourceHash=(Get-FileHash -LiteralPath $sourcePath).Hash
$file=Read-Cr2wFile $sourcePath
$root=$file.RootChunk
$g=$root.SceneGraph.Chunk
if($root.Actors.Count -ne 1 -or $root.PlayerActors.Count -ne 1 -or $root.Actors[0].ActorId.Id.ToString() -ne '0' -or $root.PlayerActors[0].ActorId.Id.ToString() -ne '1'){throw 'Unexpected source cast'}
if($g.Graph.Count -ne 5){throw 'Expected the five-node Emmerick-only movement branch'}
$section=@($g.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '441'})[0].Chunk
if($section.ActorBehaviors.Count -ne 2 -or $section.ActorBehaviors[0].ActorId.Id.ToString() -ne '1' -or $section.ActorBehaviors[1].ActorId.Id.ToString() -ne '0'){throw 'Unexpected section ownership'}
if($section.Events.Count -ne 2 -or $section.Events[0].Chunk.GetType().Name -ne 'scnPlaySkAnimEvent' -or $section.Events[0].Chunk.Performer.Id.ToString() -ne '1' -or $section.Events[1].Chunk.GetType().Name -ne 'scneventsSocket'){throw 'Expected only Emmerick animation plus socket event'}
# This branch has no player action or dialogue. Keeping the unused player in
# the cast needlessly acquires V while Claire's ambient service scene owns V.
# Remove unused player references, never remap them onto the NPC.
$root.PlayerActors.Clear()
$section.ActorBehaviors.RemoveAt(0)
$symbols=$root.DebugSymbols.PerformersDebugSymbols
if($symbols.Count -ne 2 -or $symbols[1].PerformerId.Id.ToString() -ne '257'){throw 'Unexpected player debug performer'}
$symbols.RemoveAt(1)
if($root.ScreenplayStore.Lines.Count -ne 9 -or $root.ScreenplayStore.Options.Count -ne 2){throw 'Unexpected inherited unused screenplay'}
$root.ScreenplayStore.Lines.Clear()
$root.ScreenplayStore.Options.Clear()
Write-Cr2wFile $file $OutputPath
Export-Cr2wJson (Read-Cr2wFile $OutputPath) (Join-Path $audit 'emmerick.scene.json')
if((Get-FileHash -LiteralPath $sourcePath).Hash -ne $sourceHash){throw 'Historical source changed'}
$m=[ordered]@{status='BUILT_NPC_ONLY_EMMERICK_R11_NOT_LIVE';source=$sourcePath;source_sha256=$sourceHash;path=$OutputPath;sha256=(Get-FileHash -LiteralPath $OutputPath).Hash;ordinary_actor_ids=@(0);player_actors=0;nodes=5;animation_and_root_motion_unchanged=$true;removed=@('playerActors[0]','section441.actorBehaviors[0]','debugSymbols.performersDebugSymbols[1]','screenplayStore.lines[0..8]','screenplayStore.options[0..1]');no_player_acquisition=$true}
[IO.File]::WriteAllText((Join-Path $audit 'scene_manifest.json'),($m|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
[pscustomobject]$m
