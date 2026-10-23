param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$OutputPath=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r11\rogue'
$allowed=[IO.Path]::GetFullPath((Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR11\source'))+[IO.Path]::DirectorySeparatorChar
if(-not $OutputPath){$OutputPath=Join-Path $allowed 'towercontinued\afterlife_interactions_r8\rogue.scene'}
$OutputPath=[IO.Path]::GetFullPath($OutputPath)
if(-not $OutputPath.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'R11 Rogue output must stay inside its candidate source directory'}
$sourcePath=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR9\source\towercontinued\afterlife_interactions_r8\rogue.scene'
$expected='E408759C3B9B501D28AE397C485D739E665BEC5273E2DE54CF7FA7B6A2BD586D'
if((Get-FileHash -LiteralPath $sourcePath).Hash -ne $expected){throw 'Reviewed dense-cast R9 Rogue scene changed'}
$prior=Read-Cr2wFile $sourcePath
$root=$prior.RootChunk
if($root.Actors.Count -ne 1 -or $root.PlayerActors.Count -ne 1 -or $root.Actors[0].ActorId.Id.ToString() -ne '0' -or $root.PlayerActors[0].ActorId.Id.ToString() -ne '1'){throw 'Invalid Rogue cast'}
if($root.SceneGraph.Chunk.Graph.Count -ne 47 -or $root.EntryPoints[0].Name.ToString() -ne 'in' -or $root.ExitPoints[0].Name.ToString() -ne 'local_out'){throw 'Rogue local scene scope drift'}
New-Item -ItemType Directory -Force $audit,(Split-Path $OutputPath)|Out-Null
# Copy the reviewed fixed resource, not the crashing R8 sparse cast, and not a
# reserialization that could mask an unrelated delta. Restore only this scene.
Copy-Item -LiteralPath $sourcePath -Destination $OutputPath -Force
if((Get-FileHash -LiteralPath $OutputPath).Hash -ne $expected){throw 'Rogue byte-copy failed'}
Export-Cr2wJson (Read-Cr2wFile $OutputPath) (Join-Path $audit 'rogue.scene.json')
$result=[ordered]@{
 status='ROGUE_R11_CANDIDATE_BUILT_NOT_INSTALLED_NOT_LIVE';path=$OutputPath
 source=$sourcePath;sha256=$expected;source_sha256=$expected
 actor_ids=@(0,1);nodes=47;entry='in';exit='local_out'
 scope='R9 dense-cast local-only scene restored byte-exact; live face policy remains removed independently'
 crash_root_cause_unproven=$true;new_actor_identities=0;new_story_fact_writes=0
}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($result|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
[pscustomobject]$result
