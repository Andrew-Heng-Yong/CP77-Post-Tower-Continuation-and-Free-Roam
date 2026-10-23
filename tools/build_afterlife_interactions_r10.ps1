param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r10'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeInteractionsR10'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$old=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\afterlife_world\interactions_r9\manifest.json') -Raw|ConvertFrom-Json
$hashes=[ordered]@{}
foreach($rel in $old.resources){
 $from=Join-Path $old.source_root $rel;$hashes[$from]=(Get-FileHash -LiteralPath $from).Hash
 $to=Join-Path $source $rel;New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null
 Copy-Item -LiteralPath $from -Destination $to
}
$rogueRel='towercontinued\afterlife_interactions_r8\rogue.scene'
$stub=& (Join-Path $PSScriptRoot 'build_afterlife_rogue_quarantine_r10.ps1') -WorkspaceRoot $WorkspaceRoot -OutputPath (Join-Path $source $rogueRel)
if($stub.status -ne 'ROGUE_SCENE_QUARANTINE_BUILT_NOT_LIVE'){throw 'Quarantine helper failed'}
$ownerRel='towercontinued\afterlife_interactions_r8\owner.questphase'
$owner=Read-Cr2wFile (Join-Path $old.source_root $ownerRel);$g=$owner.RootChunk.Graph.Chunk
$phase=(Get-QuestNode $g 104).PhaseGraph.Chunk
$near=New-FactCondition 'PTFRAL10_ENear' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
# Preserve native stages/inside recheck; use the exact runtime NPC for distance.
$replaced=0
foreach($id in @(3,9)){
 $conditions=(Get-QuestNode $phase $id).Condition.Chunk.Conditions
 for($i=0;$i -lt $conditions.Count;$i++){
  if($conditions[$i].Chunk.GetType().Name -eq 'questDistanceCondition'){
   $conditions[$i].Chunk=$near.DeepCopy();$replaced++
  }
 }
}
if($replaced -ne 2){throw 'Expected exactly two distance predicate replacements'}
(Get-QuestNode $g 2).Type.Chunk.Value=10
$rPhase=(Get-QuestNode $g 204).PhaseGraph.Chunk
# The actor-free same-path stub has no interruption scenario0. Keep socket/node
# identities for pending saved requests, without attempting actor acquisition.
(Get-QuestNode $rPhase 4).InterruptionOperations.Clear()
Write-Cr2wFile $owner (Join-Path $source $ownerRel)
Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $ownerRel)) (Join-Path $audit 'owner.questphase.json')
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($old.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected resources'}
foreach($p in $packed.Files.Values){
 $ms=[IO.MemoryStream]::new()
 try{$p.Extract($ms);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()}
 if($h -ne (Get-FileHash -LiteralPath (Join-Path $source $p.Name)).Hash){throw 'Readback byte mismatch'}
}
foreach($p in $hashes.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $hashes[$p]){throw "Source changed $p"}}
$m=@{status='BUILT_R10_SAFETY_NOT_INSTALLED_NOT_LIVE';source_root=$source;archive=$archive;sha256=(Get-FileHash -LiteralPath $archive).Hash;resources=$old.resources;source_hashes=$hashes;changed_payloads=@($rogueRel,$ownerRel);unchanged_r9_payloads=11;packed_readback=$true;rogue_quarantined=$true;xl_unchanged=$true;new_actor_identities=0;new_story_writes=0;crash_root_cause_unproven=$true;emmerick_root_cause_unproven=$true}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($m|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$m|Select-Object status,sha256,unchanged_r9_payloads,rogue_quarantined|ConvertTo-Json
