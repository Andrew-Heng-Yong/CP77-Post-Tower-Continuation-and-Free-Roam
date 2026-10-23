param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\pilot_r1'
$out=Join-Path $WorkspaceRoot 'build\GigPilotR1'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$raw=Join-Path $WorkspaceRoot 'research\gig_restoration\watson_sources\raw\base\open_world\street_stories\watson\northside_industrial_district\sts_wat_northside_industrial_district.questphase'
$index=Join-Path $WorkspaceRoot 'research\gig_restoration\watson_analysis\analysis.json'
if((Get-FileHash $index).Hash -ne '0E4D0E2BDCDB291B08970980896AE75301FA34740C26FDC9B51DD6DF1AF06B6E'){throw 'Native graph index changed'}
$rawHash=(Get-FileHash $raw).Hash
if($rawHash -ne '43D163168D0241F3B7E56C1D116575B65E0C488FDA14498F709828C943126DF5'){throw 'Native district source changed'}
$native=Read-Cr2wFile $raw
$a=Get-Content $index -Raw|ConvertFrom-Json
$nativePath='base\open_world\street_stories\watson\northside_industrial_district\sts_wat_northside_industrial_district.questphase'
$prefix='towercontinued\gig_pilot_r1\'
$names=@('native_owner','ow','gameplay')
$indices=@(1,7,17)
function ClearG1($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function Link($g,$from,$socket,$to,$dest='In'){
 [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $from) $socket) (Get-QuestSocket (Get-QuestNode $g $to) $dest))
}
# DeepCopy must not leave socket references pointing at separately copied nodes.
# Rebuild every connection from the original objects, including CutSource links
# omitted by the historical analysis index. Child graphs remain exactly paired.
function Rewire($g,$original){
 RebuildEdges $g @(Edges $original | ForEach-Object {$_})
 for($i=0;$i -lt $g.Nodes.Count;$i++){
  $n=$g.Nodes[$i].Chunk
  if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){Rewire $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}
 }
}
function RebuildEdges($g,$edges){foreach($h in $g.Nodes){ClearG1 $h.Chunk};foreach($e in $edges){Link $g $e[0] $e[1] $e[2] $e[3]}}
function Edges($g){
 $owners=@{};foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){
  if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){
   $rows.Add(@([int]$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),[int]$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))
  }
 }}}
 return ,$rows.ToArray()
}
$roots=@{}
for($i=0;$i -lt 3;$i++){
 $root=$native.EmbeddedFiles[$indices[$i]].Content.DeepCopy()
 Rewire $root.Graph.Chunk $native.EmbeddedFiles[$indices[$i]].Content.Graph.Chunk
 $roots[$names[$i]]=$root
}
# Resume only the audited pre-authorization journal stage. Do not repeat start,
# glossary, checkpoint/briefing, or worker_003 shard injection.
$play=(Get-QuestNode $roots.ow.Graph.Chunk 4).PhaseGraph.Chunk
$edges=@(Edges $play | ForEach-Object {$_})
$edges=@($edges|Where-Object {$_[0] -ne 3})
$edges+=,@(3,'Out',27,'Active');$edges+=,@(3,'Out',202,'In')
RebuildEdges $play $edges
# Preserve the continuation at the native cross-gig journal node, while removing
# its unrelated Pacifica journal side effect. No replacement local target guessed.
$chase=(Get-QuestNode $play 138).PhaseGraph.Chunk
$ce=@(Edges $chase | ForEach-Object {$_})
$replacement=New-XorNode 92 1
for($i=0;$i -lt $chase.Nodes.Count;$i++){if($chase.Nodes[$i].Chunk.Id.ToString() -eq '92'){$chase.Nodes[$i]=New-RedHandle ($chase.Nodes[$i].GetType()) $replacement;break}}
foreach($e in $ce){if($e[0] -eq 92){$e[1]='Out1'};if($e[2] -eq 92){$e[3]='In1'}}
RebuildEdges $chase $ce
# Use the gig's authored phone-muted/rejected text debrief. Its global phone
# transport died with the base root; this pilot never restarts that transport.
$cleanup=(Get-QuestNode $roots.ow.Graph.Chunk 5).PhaseGraph.Chunk
$fe=@(Edges $cleanup | ForEach-Object {$_})
foreach($e in $fe){if($e[0] -eq 93 -and $e[1] -eq 'False'){$e[2]=94;$e[3]='In'}}
# A native reward node remains the sole payout; claims prevent repeated entry.
$fe=@($fe|Where-Object { -not ($_[0] -eq 96 -and $_[2] -eq 69) -and -not ($_[0] -eq 69 -and $_[2] -eq 60) })
foreach($n in @((New-ConditionNode 400 (New-FactCondition 'PTFRG1_RewardClaim' 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))),
 (New-SetFactNode 401 'PTFRG1_RewardClaim' 1),(New-SetFactNode 402 'PTFRG1_RewardAck' 1),(New-SetFactNode 403 'PTFRG1_RewardReplayRefused' 1))){Add-RedHandle $cleanup.Nodes $n}
foreach($e in @(@(96,'Out1',400,'In'),@(400,'True',401,'In'),@(401,'Out',69,'In'),@(69,'Out',402,'In'),@(402,'Out',60,'In'),@(400,'False',403,'In'),@(403,'Out',60,'In'))){$fe+=,$e}
RebuildEdges $cleanup $fe
# Native parent preserves parallel gameplay/OW and cuts gameplay on OW exit.
$nativeOwner=$roots.native_owner.Graph.Chunk
foreach($id in @(8,9)){
 $node=Get-QuestNode $nativeOwner $id
 $rel=$prefix+$(if($id -eq 8){'gameplay'}else{'ow'})+'.questphase'
 $node.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($rel)
}
# The original owner binds #loc_sts_wat_nid_02_streetstory. Keep that binding in
# a separate child resource, entered ONLY after opt-in. The boot gate has none.
$roots.owner=[WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
Set-RedHandleProperty $roots.owner Graph $g
foreach($n in @((New-InputNode 0 'In1'),(New-OutputNode 1 'Out1'))){Add-RedHandle $g.Nodes $n}
$child=(Get-QuestNode $nativeOwner 8).DeepCopy();$child.Id=[uint16]405;ClearG1 $child
$child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+'native_owner.questphase')
Add-RedHandle $g.Nodes $child
$names+=,'owner'
$guard=[WolvenKit.RED4.Types.questLogicalCondition]::new();$guard.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
$guardFacts=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRG1_Request=1;PTFRG1_Started=0;PTFRG1_Fault=0;PTFRG1_RewardClaim=0;nid_02_start=1;nid_02_finished=0;sts_wat_nid_02_fail=0;sts_wat_nid_02_delivery_status=0}
foreach($k in $guardFacts.Keys){Add-RedHandle $guard.Conditions (New-FactCondition $k $guardFacts[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
$pause=(Get-QuestNode (Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')).RootChunk.Graph.Chunk 106).DeepCopy()
$pause.Id=[uint16]402;ClearG1 $pause;Set-RedHandleProperty $pause Condition $guard
foreach($n in @((New-SetFactNode 400 'PTFRG1_Ready' 1),(New-SetFactNode 401 'PTFRG1_NativeRevision' 1),$pause,
 (New-SetFactNode 403 'PTFRG1_Started' 1),(New-SetFactNode 404 'PTFRG1_OwnerFinished' 1))){Add-RedHandle $g.Nodes $n}
RebuildEdges $g @(@(0,'Out',400,'In'),@(400,'Out',401,'In'),@(401,'Out',402,'In'),@(402,'Out',403,'In'),@(403,'Out',405,'In1'),@(405,'Out1',404,'In'),@(404,'Out',1,'In'))
$resources=@()
foreach($name in $names){
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$roots[$name]
 $depot=$prefix+$name+'.questphase';$resources+=,$depot
 Write-Cr2wFile $file (Join-Path $source $depot)
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit ($name+'.questphase.json'))
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$archive=Join-Path $out 'TowerContinued_GigPilotR1.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object{$_.Name}|Sort-Object)).Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Archive readback mismatch'}}finally{$m.Dispose()}}
if((Get-FileHash $raw).Hash -ne $rawHash){throw 'Native source changed'}
$manifest=[ordered]@{status='BUILT_GIG_PILOT_R1_LIVE_PENDING';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$resources;source_sha256=$rawHash;index_sha256=(Get-FileHash $index).Hash;native_guard=$guardFacts;packed_readback=$true;vanilla_replacements=@();entry_stage='inside';initialization_omissions=@('start/glossary counters','initial briefing/checkpoint','worker shard reinjection');foreign_journal_isolated=$true;native_text_debrief=$true;native_reward='QuestRewards.sts_wat_nid_02_completion';game_writes=0;save_writes=0;live_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest|Select-Object status,sha256,packed_readback|ConvertTo-Json
