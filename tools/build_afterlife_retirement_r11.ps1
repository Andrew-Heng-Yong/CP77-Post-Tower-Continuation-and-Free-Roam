param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$OutputPath=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r11\retirement'
New-Item -ItemType Directory -Force $audit|Out-Null
$old=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r10\manifest.json') -Raw|ConvertFrom-Json
$spec=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\afterlife_world\dancers_manifest.json') -Raw|ConvertFrom-Json
$depot='towercontinued\afterlife_r1\dancers.questphase'
$inputPath=Join-Path $old.source_root $depot
if((Get-FileHash -LiteralPath $inputPath).Hash -ne $spec.sha256){throw 'Installed-generation dancer source differs from R1 audit'}
if(-not $OutputPath){$OutputPath=Join-Path $WorkspaceRoot ('build\AfterlifeRetirementR11\source\'+$depot)}
$file=Read-Cr2wFile $inputPath
$g=$file.RootChunk.Graph.Chunk
if($g.Nodes.Count -ne 112 -or $file.EmbeddedFiles.Count -ne 0 -or $file.RootChunk.PhasePrefabs.Count -ne 0){throw 'Dancer phase scope changed'}
$rows=[Collections.Generic.List[object]]::new()
foreach($entry in $spec.entries){
 $i=[int]$entry.start;$name=[string]$entry.entry;$prefix='PTFRAL1_Dancer'+$name.Substring(7)
 $retired='PTFRAL11_Dancer'+$name.Substring(7)+'Retired'
 $acquire=(Get-QuestNode $g ($i+3)).Actions[0].Type.Chunk
 $release=(Get-QuestNode $g ($i+8)).Actions[0].Type.Chunk
 foreach($p in @($acquire,$release)){
  if($p.CommunityEntryName.ToString() -ne $name -or $p.CommunityEntryPhaseName.ToString() -ne 'default' -or $p.SpawnerReference.ToString() -ne $spec.spawner){throw 'Non-dancer or changed-spawner target'}
 }
 if($acquire.Action.ToString() -ne 'Reactivate' -or $release.Action.ToString() -ne 'Deactivate'){throw 'Dancer action predecessor changed'}
 $acquire.Action=[WolvenKit.RED4.Types.Enums+populationSpawnerObjectCtrlAction]::Deactivate
 # Staggering existed for animation-start variation. Retirement has no start;
 # zero delay uses the existing dancer_01 precedent and avoids holding an old
 # saved dancer up to30 seconds. Node/socket identities are unchanged.
 (Get-QuestNode $g ($i+1)).Condition.Chunk.Type.Chunk.Seconds=[uint32]0
 $ready=(Get-QuestNode $g ($i+4)).Type.Chunk
 if($ready.FactName -ne ($prefix+'Requests')){throw 'Expected legacy request counter'}
 $ready.FactName=$prefix+'Ready';$ready.Value=0;$ready.SetExactValue=$true
 $ready2=(Get-QuestNode $g ($i+5)).Type.Chunk
 if($ready2.FactName -ne ($prefix+'Ready') -or $ready2.Value -ne 1){throw 'Expected legacy Ready1 setter'}
 $ready2.Value=0
 # New identity: an old saved +4/+5 continuation must NOT falsely mark retired
 # merely because its prior R1 action was Reactivate. Only the new edge after
 # actual Deactivate(+3) reaches this revision setter.
 Add-RedHandle $g.Nodes (New-SetFactNode ($i+11) $retired 11)
 $wait=(Get-QuestNode $g ($i+6)).Condition.Chunk
 if($wait.GetType().Name -ne 'questLogicalCondition' -or $wait.Operation.ToString() -ne 'OR' -or $wait.Conditions.Count -ne 2){throw 'Expected legacy owned wait'}
 # A saved R1..R10 active wait must wake even if the player never streams out.
 # It still passes the original full Guard before its exact Deactivate action.
 Add-RedHandle $wait.Conditions (New-FactCondition $retired 11 ([WolvenKit.RED4.Types.Enums+EComparisonType]::NotEqual))
 $rows.Add([ordered]@{entry=$name;phase='default';ref=$entry.ref;start=$i;retired_fact=$retired;retired_node=$i+11;previous_delay=$entry.delay;ready_fact=$prefix+'Ready'})
}
if($rows.Count -ne 10){throw 'Wrong retirement entry count'}
$edges=[Collections.Generic.List[object]]::new()
foreach($edge in $spec.edges){
 $split=@($rows|Where-Object {([int]$edge[0]) -eq ($_.start+3) -and $edge[1] -eq 'Out' -and ([int]$edge[2]) -eq ($_.start+4)})
 if($split.Count -eq 1){
  $edges.Add(@([int]$edge[0],'Out',[int]$split[0].retired_node))
  $edges.Add(@([int]$split[0].retired_node,'Out',[int]$edge[2]))
 }elseif($split.Count -eq 0){$edges.Add(@($edge))}else{throw 'Ambiguous edge split'}
}
foreach($handle in $g.Nodes){foreach($socket in $handle.Chunk.Sockets){$socket.Chunk.Connections.Clear()}}
foreach($edge in $edges){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g ([int]$edge[0])) ([string]$edge[1])) (Get-QuestSocket (Get-QuestNode $g ([int]$edge[2])) 'In'))
}
if($g.Nodes.Count -ne 122 -or $edges.Count -ne ($spec.edges.Count+10)){throw 'Retirement graph size changed'}
New-Item -ItemType Directory -Force (Split-Path $OutputPath)|Out-Null
Write-Cr2wFile $file $OutputPath
Export-Cr2wJson (Read-Cr2wFile $OutputPath) (Join-Path $audit 'dancers.questphase.json')
$manifest=[ordered]@{
 status='DANCER_RETIREMENT_R11_BUILT_NOT_LIVE';artifact=$OutputPath;depot=$depot
 sha256=(Get-FileHash -LiteralPath $OutputPath).Hash;source=$inputPath;source_sha256=$spec.sha256
 entries=@($rows);guards=$spec.guards;spawner=$spec.spawner;nodes=122;legacy_node_identities=112;edges=@($edges)
 registration_unchanged=$true;no_acquisition_actions=$true;no_original_resource_override=$true
 exact_entry_count=10;ordinary_population_unchanged=$true;live_retirement_unproven=$true
}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,artifact,sha256
