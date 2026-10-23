param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),[string]$WolvenKitRoot='C:\Users\Ayong\Documents\WolvenKit-8.20.0')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -WolvenKitRoot $WolvenKitRoot -HelpersOnly
$research=Join-Path $WorkspaceRoot 'research\b0_claire'
$audit=Get-Content (Join-Path $research 'audit.json') -Raw|ConvertFrom-Json
$source=Join-Path $WorkspaceRoot 'archive\b0_claire\source'
$out=Join-Path $WorkspaceRoot 'build\B0_Claire'
$val=Join-Path $research 'validation'
New-Item -ItemType Directory -Force -Path $source,$out,$val|Out-Null
if((Get-FileHash (Join-Path $WorkspaceRoot $audit.owner)).Hash -ne $audit.owner_sha256 -or (Get-FileHash (Join-Path $WorkspaceRoot $audit.scene)).Hash -ne $audit.scene_sha256){throw 'Audit source changed'}
$raw=Join-Path $WorkspaceRoot 'research\phase2b_p4\vendor_owner\raw\base\quest\default_dialogs.questphase'
$vendor=Read-Cr2wFile $raw
$base=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')
function ClearSockets($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,$from,$socket,$to,$dest='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $from) $socket) (Get-QuestSocket (Get-QuestNode $g $to) $dest))}
function Inc($id,$suffix){$n=New-SetFactNode $id ('PTFRB0CLA_'+$suffix) 1;$n.Type.Chunk.SetExactValue=$false;return $n}
function Rewire($g,$route){
  foreach($h in $g.Nodes){ClearSockets $h.Chunk}
  foreach($e in $audit.graphs.$route.edges){
    $to=$e.destination_node_id;$dest=$e.destination_socket
    if($route -eq 'root/node4/node19' -and $e.source_node_id -eq 21){$to=200;$dest='In'}
    if($route -eq 'root/node4/node19/node26'){
      if($e.source_node_id -eq 27){$to=200;$dest='In'}
      if($e.source_node_id -eq 29){$to=202;$dest='In'}
      if($e.destination_node_id -eq 17){$to=204;$dest='In'}
      if($e.destination_node_id -eq 41){$to=205;$dest='In'}
    }
    Link $g $e.source_node_id $e.source_socket $to $dest
  }
}
$phase=(Get-QuestNode (Get-QuestNode $vendor.RootChunk.Graph.Chunk 4).PhaseGraph.Chunk 19).DeepCopy()
$phase.Id=[uint16]5;ClearSockets $phase
$outer=$phase.PhaseGraph.Chunk
$inner=(Get-QuestNode $outer 26).PhaseGraph.Chunk
$empty=(Get-QuestNode $inner 7).PhaseGraph.Chunk
Add-RedHandle $outer.Nodes (Inc 200 'SpawnActionOut')
foreach($n in @((New-SetFactNode 200 'PTFRB0CLA_Inside' 1),(Inc 201 'Entries'),(New-SetFactNode 202 'PTFRB0CLA_Inside' 0),(Inc 203 'Exits'),(Inc 204 'NormalRequests'),(Inc 205 'AngryRequests'))){Add-RedHandle $inner.Nodes $n}
Rewire $outer 'root/node4/node19';Rewire $inner 'root/node4/node19/node26';Rewire $empty 'root/node4/node19/node26/node7'
Link $outer 200 Out 35
Link $inner 200 Out 201;Link $inner 201 Out 38
Link $inner 202 Out 203;Link $inner 203 Out 12
Link $inner 204 Out 17 'claire_default_start';Link $inner 205 Out 41 'claire_pissed'
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach($f in $audit.common_guards.PSObject.Properties){Add-RedHandle $guard.Conditions (New-FactCondition $f.Name $f.Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
foreach($f in @('PTFRB0CLA_Excluded','PTFRB0CLA_Suspended','PTFRBASE_Suspended')){Add-RedHandle $guard.Conditions (New-FactCondition $f 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
Add-RedHandle $guard.Conditions (New-FactCondition 'PTFRB0CLA_Enabled' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
Add-RedHandle $guard.Conditions (New-FactCondition 'claire_default_on' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Greater))
$pause=(Get-QuestNode $base.RootChunk.Graph.Chunk 106).DeepCopy();$pause.Id=[uint16]2;ClearSockets $pause;Set-RedHandleProperty $pause Condition $guard
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRB0CLA_Ready' 1),$pause,(New-SetFactNode 3 'PTFRB0CLA_OwnerActive' 1),(Inc 4 'OwnerStarts'),$phase,(New-SetFactNode 6 'PTFRB0CLA_OwnerActive' 0))){Add-RedHandle $g.Nodes $n}
foreach($e in @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,'In1'),@(5,'Out1',6,'In'),@(6,'Out',2,'In'))){Link $g $e[0] $e[1] $e[2] $e[3]}
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$root.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $root Graph $g
$resource=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$resource.RootChunk=$root
$depot='towercontinued\b0_claire\claire_service.questphase'
Write-Cr2wFile $resource (Join-Path $source $depot)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $val 'claire_service.questphase.json')
if(@(Get-ChildItem $source -Recurse -File).Count -ne 1){throw 'Package scope drift'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_B0_Claire.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 1){throw 'Archive readback failed'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);if($e.Name -ne $depot -or [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $depot)).Hash){throw 'Pack mismatch'}}finally{$m.Dispose()}}
$xl=@('quest:','  phases:',"    - path: $depot",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out') -join "`n"
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'archive\b0_claire\TowerContinued_B0_Claire.archive.xl'),$xl+"`n")
$report=[ordered]@{status='BUILT_NOT_LIVE_TESTED';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=@($depot);common_guards=$audit.common_guards;audit_sha256=(Get-FileHash (Join-Path $research 'audit.json')).Hash;owner_raw_sha256=(Get-FileHash $raw).Hash;vanilla_replacements=@();scene_replacements=@();scope='Claire prefab-owning service only; original conditions, scenes, actions, and prefab retained'}
[IO.File]::WriteAllText((Join-Path $val 'build_manifest.json'),($report|ConvertTo-Json -Depth 6))
'BUILT: one Claire service owner; no vanilla replacement'
