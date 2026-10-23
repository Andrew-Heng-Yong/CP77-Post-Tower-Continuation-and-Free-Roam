param([string]$Revision='base_b_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^base_b_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$copies=@();$changes=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function ReadPinned($p){Pin $p;return Read-Cr2wFile (Join-Path $WorkspaceRoot $p)}
foreach($p in @('prealpha/sidejobs_s23/base_b/build.ps1','prealpha/sidejobs_s23/base_b/contract.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/sidejobs_s23/live_20261016_01/capture.json')){Pin $p}
function CopyNode($g,$source,$id,$newid=-1){
 $o=Get-QuestNode $source $id;$n=$o.DeepCopy();ClearB5 $n
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk}
 if($newid -ge 0){$n.Id=[uint16]$newid};AddNodeB5 $g $n
}
function SaveGraph($g,$depot,$label,$inject=$false){
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$r.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $r Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r;$p=Join-Path (Join-Path $out 'source') $depot
 Write-Cr2wFile $f $p;Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $out ('readback/'+$label+'.json'))
 $resources[$depot]=(Get-FileHash -LiteralPath $p).Hash;if($inject){$script:boots+=,$depot}
}
function Eq($f,$v){return New-FactCondition $f $v ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function Any($conditions){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR;foreach($x in $conditions){Add-RedHandle $c.Conditions $x};return $c}
function JournalCondition($j){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$j.path;$p.ClassName=$j.class;$p.FileEntryIndex=2
 $conditions=@();foreach($state in $j.states){$t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p.DeepCopy();$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],@('','Inactive','Active','Succeeded','Failed')[[int]$state]);$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;$conditions+=,$c};return Any $conditions
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$contract=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw|ConvertFrom-Json
if($pins[$contract.capture] -cne $contract.capture_sha256){throw 'Capture pin mismatch'}
function Guard($s){
 $p=[ordered]@{};foreach($k in $common.Keys){$p[$k]=$common[$k]};foreach($f in $s.facts_equal.PSObject.Properties){$p[$f.Name]=[int]$f.Value}
 $p[$s.tag+'_Permit']=1;$p[$s.tag+'_Issued']=0;$p[$s.tag+'_Finished']=0;$p[$s.tag+'_Fault']=0
 $c=AllB5 $p;foreach($j in $s.journals){Add-RedHandle $c.Conditions (JournalCondition $j)};return $c
}
function Dependency($s){$p=[ordered]@{};foreach($contact in $s.phone_dependencies){$p['PTFRS23_PHONE_'+$contact+'_Issued']=1};if(!$p.Count){$p['PTFRPA2_Finished']=1};return AllB5 $p}
$parentSource='research/sidejobs_s2/sacrum_audit/native_01/raw/base/quest/minor_quests/minorquests.questphase'
$parent=(ReadPinned $parentSource).RootChunk.Graph.Chunk
$bugSource='research/races_r1/parents_01/raw/base/quest/bugfixing/quest_bugfixing.questphase'
$bug=(Get-QuestNode (ReadPinned $bugSource).RootChunk.Graph.Chunk 3).PhaseGraph.Chunk
$vendorSource='research/phase2b_p4/vendor_owner/raw/base/quest/default_dialogs.questphase'
$vendor=(Get-QuestNode (ReadPinned $vendorSource).RootChunk.Graph.Chunk 7).PhaseGraph.Chunk

# The old Wilson body (spawn/scene/native departure) is left byte-for-byte alone.
# Preserve every old node ID, including the saved waiting node3 and active body4.
# Both new and persisted owners encounter the cooperative lease gate at node3.
$wvSource='archive/b0_wilson_vendor/source/towercontinued/b0_wilson_vendor/owner.questphase'
$wv=(ReadPinned $wvSource).RootChunk.Graph.Chunk;$wg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($h in $wv.Nodes){CopyNode $wg $wv ([int]$h.Chunk.Id.ToString())}
$wake=Any @((Eq 'PTFRB0WV_Near' 1),(Eq 'PTFRB0WV_QuestOwns' 1))
Set-RedHandleProperty (Get-QuestNode $wg 3) Condition $wake
foreach($n in @((New-ConditionNode 100 (Eq 'PTFRB0WV_QuestOwns' 1)),(New-SetFactNode 101 'PTFRB0WV_Released' 1),(PauseB5 102 (Eq 'PTFRB0WV_QuestOwns' 0)),(New-SetFactNode 103 'PTFRB0WV_Released' 0))){AddNodeB5 $wg $n}
$we=@(EdgesB5 $wv|ForEach-Object {$_}|Where-Object {$_[0] -ne 3})
$we+=,@(3,'Out',100,'In');$we+=,@(100,'True',101,'In');$we+=,@(101,'Out',102,'In');$we+=,@(102,'Out',3,'In');$we+=,@(100,'False',103,'In');$we+=,@(103,'Out',4,'In1')
RebuildB5 $wg $we
SaveGraph $wg 'towercontinued\b0_wilson_vendor\owner.questphase' 'wilson_owner'
$changes+=,@{depot='towercontinued\b0_wilson_vendor\owner.questphase';source=$wvSource;modified_nodes=@(3);added_nodes=@(100,101,102,103);before_sha256=$pins[$wvSource];reason='Existing pending node3 now releases lease only with no active body; body4 returns after native despawn. No cut, no actor/fact reset.'}

foreach($s in $contract.owners){
 Pin $s.native_source;foreach($p in $s.sourcepins.PSObject.Properties){if($pins[$p.Name] -cne $p.Value){throw 'Native source changed'}}
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$edges=@();$nativeIds=@()
 if($s.key -eq 'MQ049'){$source=$bug;$nativeIds=@(63,64);$start=63;$edges+=,@(63,'Out',64,'In') ;$edges[-1][3]='In1'}
 elseif($s.key -eq 'MQ026'){$source=$parent;$nativeIds=@(39);$start=39}
 else{$source=$parent;$nativeIds=@(54,80,55,[int]$s.parent_node);$start=54;$edges+=,@(54,'Out',80,'In');$edges+=,@(80,'Out',55,'In')
  if($s.key -eq 'MQ011'){$nativeIds+=@(184,93);$edges+=,@(55,'Out',184,'In');$edges+=,@(184,'True',93,'In');$edges+=,@(93,'Out',15,'In1');$edges+=,@(184,'False',15,'EP1_Standalone')}
  else{$edges+=,@(55,'Out',[int]$s.parent_node,'In1')}
 }
 foreach($id in $nativeIds){CopyNode $g $source $id}
 # Add a native child output socket solely to observe cleanup completion. No
 # child payload/edge or gameplay phase is rewritten and no parent output ends it.
 $child=Get-QuestNode $g ([int]$s.parent_node)
 if(@($child.Sockets|Where-Object {$_.Chunk.Name.ToString() -eq 'Out1'}).Count -eq 0){[void](New-QuestSocket $child 'Out1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))}
 foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 ($s.tag+'_Ready') 1),(PauseB5 1002 (Guard $s)),(PauseB5 1003 (Dependency $s)),(New-ConditionNode 1004 (Guard $s)),(New-SetFactNode 1005 ($s.tag+'_Issued') 1),(New-SetFactNode 1006 ($s.tag+'_Entered') 1),(New-SetFactNode 1007 ($s.tag+'_Finished') 1),(New-SetFactNode 1008 ($s.tag+'_Refused') 1))){AddNodeB5 $g $n}
 # Recheck AFTER all original parent waits, immediately before native entry.
 foreach($e in $edges){if($e[2] -eq [int]$s.parent_node){$e[2]=1004;$e[3]='In'}}
 $entryStart=if($start -eq [int]$s.parent_node){1004}else{$start}
 $edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In');$edges+=,@(1002,'Out',1003,'In');$edges+=,@(1003,'Out',$entryStart,'In');$edges+=,@(1004,'False',1002,'In');$edges+=,@(1004,'True',1005,'In');$edges+=,@(1005,'Out',1006,'In');$edges+=,@(1006,'Out',[int]$s.parent_node,'In1');$edges+=,@([int]$s.parent_node,'Out1',1007,'In')
 if($s.key -eq 'MQ011'){
  # Preserve the stock EP1-standalone port as a separate guarded entry.
  foreach($e in $edges){if($e[0] -eq 184 -and $e[1] -eq 'False'){$e[2]=1104}}
  foreach($n in @((New-ConditionNode 1104 (Guard $s)),(New-SetFactNode 1105 ($s.tag+'_Issued') 1),(New-SetFactNode 1106 ($s.tag+'_Entered') 1))){AddNodeB5 $g $n}
  $edges+=,@(1104,'True',1105,'In');$edges+=,@(1104,'False',1002,'In');$edges+=,@(1105,'Out',1106,'In');$edges+=,@(1106,'Out',15,'EP1_Standalone')
 }
 if($s.service_lease){
  $prefix='PTFRB0'+$s.service_lease+'_';$release=[ordered]@{($prefix+'Released')=1}
  if($s.service_lease -eq 'ZAN'){$release[$prefix+'OwnerActive']=0;$release[$prefix+'Inside']=0}
  else{$release[$prefix+'Near']=0;$release[$prefix+'SpawnActionOut']=0;$release[$prefix+'ActorDistanceGate']=0}
  $released=AllB5 $release
  if($s.service_lease -eq 'ZAN'){$released=Any @($released,(AllB5 ([ordered]@{PTFRB0ZAN_OwnerActive=0;PTFRB0ZAN_Enabled=0;PTFRB0ZAN_Inside=0})))}
  foreach($n in @((New-SetFactNode 1010 ($prefix+'QuestOwns') 1),(PauseB5 1011 $released),(New-SetFactNode 1012 ($prefix+'QuestOwns') 0),(New-SetFactNode 1013 ($prefix+'QuestOwns') 0))){AddNodeB5 $g $n}
  # Lease acquisition precedes final guard+Issued. Saved preparation never resets
  # native quest progress; no support guard is placed before Ready/Permit.
  foreach($e in $edges){if($e[0] -eq 1003){$e[2]=1010;$e[3]='In'};if($e[0] -in @(1004,1104) -and $e[1] -eq 'False'){$e[2]=1013};if($e[0] -eq 1007){throw 'Unexpected finish edge'}}
  $edges+=,@(1010,'Out',1011,'In');$edges+=,@(1011,'Out',$entryStart,'In');$edges+=,@(1007,'Out',1012,'In');$edges+=,@(1013,'Out',1002,'In')
  if($s.service_lease -eq 'ZAN'){
   CopyNode $g $vendor 25 1020
   $edges+=,@(1006,'Out',1020,'In1')
   $copies+=,@{depot=$s.depot;source=$vendorSource;source_graph='root/7';source_id=25;target_id=1020}
  }
 }
 RebuildB5 $g $edges;SaveGraph $g $s.depot $s.key.ToLower() $true
 foreach($id in $nativeIds){$copies+=,@{depot=$s.depot;source=$(if($s.key -eq 'MQ049'){$bugSource}else{$parentSource});source_graph=$(if($s.key -eq 'MQ049'){'root/3'}else{'root'});source_id=$id;target_id=$id}}
}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw 'Pinned source changed during build'}}
$manifest=[ordered]@{schema=1;status='BUILT_NOT_INSTALLED';revision=$Revision;resources=$resources;boots=$boots;source_pins=$pins;native_copies=$copies;transforms=$changes;mod_overrides=@('towercontinued\b0_wilson_vendor\owner.questphase');contract='prealpha/sidejobs_s23/base_b/contract.json';live='NOT_TESTED'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 4
