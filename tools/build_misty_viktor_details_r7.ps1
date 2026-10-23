param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[switch]$IncludeTrucks)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$prior=Get-Content (Join-Path $audit 'repair_r6_manifest.json') -Raw|ConvertFrom-Json
$out=Join-Path $WorkspaceRoot 'build\MistyViktorDetailsR7'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $source|Out-Null
$resources=[Collections.Generic.List[string]]::new()
foreach($depot in $prior.resources){
 $src=Join-Path $WorkspaceRoot ('build\MistyViktorRepairR6\source\'+$depot)
 $dst=Join-Path $source $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
 Copy-Item -LiteralPath $src -Destination $dst -Force
 $resources.Add($depot)
}
$manifestNames=@('r7_construction_manifest.json')
if($IncludeTrucks){$manifestNames+='r7_trucks_manifest.json'}
$supplements=[Collections.Generic.List[object]]::new()
$blocks=[Collections.Generic.List[string]]::new()
foreach($name in $manifestNames){
 $m=Get-Content (Join-Path $audit $name) -Raw|ConvertFrom-Json
 if($m.status -notin @('BUILT_R7_CONSTRUCTION_SOURCE_NOT_INSTALLED_OR_LIVE','BUILT_R7_TRUCK_SOURCE_NOT_INSTALLED_OR_LIVE')){throw "Unreviewed supplement: $name"}
 if($m.resources.Count -ne 2 -or $m.block_depot -notin $m.resources){throw 'Unexpected supplemental scope'}
 foreach($depot in $m.resources){
  if(-not $depot.StartsWith('towercontinued\misty_viktor_world\') -or $depot.Contains('..') -or $depot -in $resources){throw 'Invalid supplemental resource path'}
  $src=Join-Path $m.source_root $depot
  $expected=if($depot.EndsWith('.streamingsector')){$m.sector_sha256}else{$m.block_sha256}
  if((Get-FileHash -LiteralPath $src).Hash -ne $expected){throw "Supplement hash mismatch: $depot"}
  Copy-Item -LiteralPath $src -Destination (Join-Path $source $depot) -Force
  $resources.Add($depot)
 }
 $blocks.Add($m.block_depot)
 $supplements.Add([pscustomobject]@{manifest=$name;sha256=(Get-FileHash (Join-Path $audit $name)).Hash;resources=$m.resources;source_root=$m.source_root})
}
$phaseDepot='towercontinued\misty_viktor_world\shell_optin.questphase'
$phase=Read-Cr2wFile (Join-Path $source $phaseDepot)
if($phase.RootChunk.Graph.Chunk.Nodes.Count -ne 30){throw 'R6 controller changed'}
$revision=(Get-QuestNode $phase.RootChunk.Graph.Chunk 18).Type.Chunk
if($revision.FactName.ToString() -ne 'PTFRMV_Revision' -or $revision.Value.ToString() -ne '6'){throw 'R6 revision changed'}
$revision.Value=[int32]7
Write-Cr2wFile $phase (Join-Path $source $phaseDepot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $phaseDepot)) (Join-Path $audit 'details_r7_phase.json')

# Only additive private controlled blocks. Do not switch WLC_03_Default or
# WLC_03_Q307: their full scope includes remote geometry and ending FX.
$xl=Get-Content ($prior.archive+'.xl')
$anchor='    - towercontinued\misty_viktor_world\crowd_alley_r6.streamingblock'
if(@($xl|Where-Object {$_ -eq $anchor}).Count -ne 1){throw 'R6 registration changed'}
$xl=@($xl|ForEach-Object {$_;if($_ -eq $anchor){foreach($b in $blocks){'    - '+$b}}})
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$archive=Join-Path $out 'TowerContinued_MistyViktorShellOptIn.archive'
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hash,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'R7 pack failed'}}finally{$stream.Dispose()}
[IO.File]::WriteAllLines(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hash,[ref]$packed).ToString() -ne 'NoError'){throw 'R7 reopen failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'R7 resource scope mismatch'}
$manifest=[ordered]@{
 status='BUILT_R7_DETAILS_NOT_INSTALLED_OR_LIVE';archive=$archive
 sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash ($archive+'.xl')).Hash
 resources=@($resources);supplements=@($supplements);guards=$prior.guards;edges=$prior.edges
 construction_mesh_instances=18;truck_spawners=$(if($IncludeTrucks){2}else{0})
 private_sector_count=15+$supplements.Count;private_block_count=3+$supplements.Count
 crowd_ref=$prior.crowd_ref;terminal_retained_on_stop=$prior.terminal_retained_on_stop
 original_lighting_changes=0;original_world_resource_overrides=0
 native_scene_starts=0;story_fact_writes=0;live_tested=$false
 unresolved=@('Cyan hotel neon and residual police glow: exact narrow addressing not established','Original wall-gap surface not independently identified','New props/vehicles lifecycle and cold reload live-unverified')
}
[IO.File]::WriteAllText((Join-Path $audit 'details_r7_manifest.json'),($manifest|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
[pscustomobject]$manifest|Select-Object status,sha256,construction_mesh_instances,truck_spawners,private_sector_count,private_block_count|ConvertTo-Json
