param([string]$Revision='services_01',[string]$Contract='contract01.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^services_\d{2}$' -or $Contract -cnotmatch '^contract\d{2}\.json$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback'),(Join-Path $out 'native_readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$copies=@();$transforms=@();$overrides=@();$nativeReadbacks=[ordered]@{}
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function ReadPinned($p){Pin $p;$f=Read-Cr2wFile (Join-Path $WorkspaceRoot $p);if(-not $nativeReadbacks.Contains($p)){$relative='native_readback/'+$pins[$p]+'.json';Export-Cr2wJson $f (Join-Path $out $relative);$nativeReadbacks[$p]=$relative};return $f}
$contractPath='prealpha/sidejobs_s25/services/'+$Contract
foreach($p in @('prealpha/sidejobs_s25/services/build.ps1','prealpha/sidejobs_s25/services/prepare.py','prealpha/sidejobs_s25/services/test.py','prealpha/sidejobs_s25/services/inspect.py',$contractPath,'tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','prealpha/ncpd_scanner_n1/native_inspect.py','tools/audit_activity_batches_b1.py','tools/catalog_gig_rollout_r2.py','tools/inspect_story_services.py','prealpha/sidejobs_s22/delamain_v2/test.py')){Pin $p}
$contractData=Get-Content -LiteralPath (Join-Path $PSScriptRoot $Contract) -Raw|ConvertFrom-Json
Pin $contractData.capture
if($pins[$contractData.capture] -cne $contractData.capture_sha256){throw 'Capture changed'}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
function Eq($f,$v){return New-FactCondition $f $v ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function JournalCondition($j,[string]$State='Inactive'){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$j.path;$p.ClassName=$j.class;$p.FileEntryIndex=$(if($j.path.StartsWith('contacts/')){1}else{2})
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],$State);$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function Guard($s){
 $pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]};foreach($f in $s.facts_equal.PSObject.Properties){$pairs[$f.Name]=[int]$f.Value}
 $pairs[$s.tag+'_Permit']=1;$pairs[$s.tag+'_Issued']=0;$pairs[$s.tag+'_Finished']=0;$pairs[$s.tag+'_Fault']=0
 $c=AllB5 $pairs
 foreach($r in $s.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $r.Name ([int]$r.Value.min) ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual));Add-RedHandle $c.Conditions (New-FactCondition $r.Name ([int]$r.Value.max) ([WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual))}
 foreach($j in $s.journals){Add-RedHandle $c.Conditions (JournalCondition $j)}
 if($s.key -eq 'GUN'){$inv=(SceneNode (ReadPinned $s.scene_native) 281).QuestNode.Chunk.Condition.Chunk.DeepCopy();$inv.Type.Chunk.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Less;Add-RedHandle $c.Conditions $inv}
 return $c
}
function GraphAt($file,$route){$g=$file.RootChunk.Graph.Chunk;foreach($id in $route.Split('/')|Select-Object -Skip 1){$g=(Get-QuestNode $g ([int]$id)).PhaseGraph.Chunk};return $g}
function SaveFile($f,$depot,$label){$p=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $p;Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $out ('readback/'+$label+'.json'));$resources[$depot]=(Get-FileHash -LiteralPath $p).Hash}
function SceneNode($f,[int]$id){$n=@($f.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq "$id"});if($n.Count -ne 1){throw "Bad scene node $id"};return $n[0].Chunk}
function SceneEdges($n,$outs){
 for($k=0;$k -lt $outs.Count;$k++){
  $n.OutputSockets[$k].Destinations.Clear()
  foreach($pair in $outs[$k]){$d=[WolvenKit.RED4.Types.scnInputSocketId]::new();$d.NodeId.Id=[uint32]$pair[0];$d.IsockStamp.Ordinal=[uint16]$pair[1];$d.IsockStamp.Name=[uint16]0;$n.OutputSockets[$k].Destinations.Add($d)}
 }
}
foreach($s in $contractData.owners){
 $native=GraphAt (ReadPinned $s.native_source) $s.source_graph
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $s.native_ids){$n=(Get-QuestNode $native ([int]$id)).DeepCopy();ClearB5 $n;AddNodeB5 $g $n;$copies+=,@{depot=$s.depot;source=$s.native_source;source_graph=$s.source_graph;source_id=[int]$id;target_id=[int]$id}}
 foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 ($s.tag+'_Ready') 1),(PauseB5 1002 (Guard $s)),(New-ConditionNode 1003 (Guard $s)),(New-SetFactNode 1004 ($s.tag+'_Issued') 1),(New-SetFactNode 1005 ($s.tag+'_Entered') 1),(New-SetFactNode 1007 ($s.tag+'_Finished') 1))){AddNodeB5 $g $n}
 $edges=@($s.native_edges|ForEach-Object {,@([int]$_[0],[string]$_[1],[int]$_[2],[string]$_[3])})
 $edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In');$edges+=,@(1002,'Out',1003,'In');$edges+=,@(1003,'False',1002,'In');$edges+=,@(1003,'True',1004,'In')
 if($s.key -eq 'GUN'){
  $contact=(Get-QuestNode (ReadPinned $s.contact_source).RootChunk.Graph.Chunk 168).DeepCopy();ClearB5 $contact;$contact.Id=[uint16]1006
  if($contact.Type.Chunk.Params[0].Contact.Chunk.RealPath.ToString() -cne 'contacts/dex'){throw 'Native contact changed'}
  $contact.Type.Chunk.Params[0].Contact.Chunk.RealPath=$s.contact_target;AddNodeB5 $g $contact
  AddNodeB5 $g (PauseB5 1008 (JournalCondition $s.journals[0] 'Succeeded'))
  $edges+=,@(1004,'Out',1006,'In');$edges+=,@(1006,'Out',1005,'In');$edges+=,@(1005,'Out',51,'Active');$edges+=,@(1005,'Out',52,'In');$edges+=,@(1005,'Out',1008,'In');$edges+=,@(1008,'Out',1007,'In')
  $transforms+=,@{depot=$s.depot;source=$s.contact_source;source_id=168;target_id=1006;field='type.params[0].contact.realPath';before='contacts/dex';after='contacts/wilson'}
 }else{$edges+=,@(1004,'Out',1005,'In');$edges+=,@(1005,'Out',[int]$s.native_start,$s.native_start_socket);$edges+=,@([int]$s.native_finish,'Out',1007,'In')}
 RebuildB5 $g $edges
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$r.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $r Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r;SaveFile $f $s.depot $s.key.ToLower();$boots+=,$s.depot
 if($s.key -eq 'PAID'){
  $scene=ReadPinned $s.scene_current;$original=ReadPinned $s.scene_native
  foreach($choice in $s.scene_options){
   $id=[int]$choice[0];$option=[int]$choice[1];$target=SceneNode $scene $id;$donor=SceneNode $original $id
   if($donor.Options[$option].Caption.ToString() -cne 'q001_debt'){throw 'Debt choice identity changed'}
   $target.Options[$option]=$donor.Options[$option].DeepCopy();$target.OutputSockets[$option]=$donor.OutputSockets[$option].DeepCopy()
   $gate=AllB5 ([ordered]@{($s.tag+'_Issued')=1;($s.tag+'_Finished')=0;($s.tag+'_Fault')=0})
   Add-RedHandle $gate.Conditions $target.Options[$option].QuestCondition.Chunk.DeepCopy()
   Add-RedHandle $gate.Conditions (JournalCondition $s.journals[0] 'Active')
   Set-RedHandleProperty $target.Options[$option] QuestCondition $gate
  }
  SaveFile $scene $s.scene_depot 'viktor_scene';$overrides+=,$s.scene_depot
  $transforms+=,@{depot=$s.scene_depot;before_source=$s.scene_current;native_donor=$s.scene_native;nodes=@(351,840);restored_options=@(1,1);operation='Only native debt options/output restored, with additional owned-issued and Active-root condition. All other B0 scene data exact.'}
 }
 if($s.key -eq 'GUN'){
  $scene=ReadPinned $s.scene_native;$shop=ReadPinned $s.shop_current
  $retained=@();foreach($id in $s.scene_ids){
   $n=$(if([int]$id -in @(0,678,224)){(SceneNode $shop ([int]$id)).DeepCopy()}else{(SceneNode $scene ([int]$id)).DeepCopy()})
   SceneEdges $n $s.scene_edges.PSObject.Properties[[string]$id].Value
   if([int]$id -eq 177){$n.Options.RemoveAt(1)}
   if([int]$id -eq 512){$n.QuestNode.Chunk.Condition.Chunk.Type.Chunk.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.scnSceneResource]]::new($s.scene_depot)}
   $retained+=,$n
  }
  $scene.RootChunk.SceneGraph.Chunk.Graph.Clear();foreach($n in $retained){Add-RedHandle $scene.RootChunk.SceneGraph.Chunk.Graph $n}
  $scene.RootChunk.Props.Clear()
  $entry=$scene.RootChunk.EntryPoints[0].DeepCopy();if($entry.NodeId.Id.ToString() -cne '0'){throw 'Scene entry changed'}
  $scene.RootChunk.EntryPoints.Clear();$scene.RootChunk.EntryPoints.Add($entry)
  $start=$shop.RootChunk.SceneGraph.Chunk.StartNodes[0].DeepCopy();$scene.RootChunk.SceneGraph.Chunk.StartNodes.Clear();$scene.RootChunk.SceneGraph.Chunk.StartNodes.Add($start)
  $scene.RootChunk.SceneGraph.Chunk.EndNodes.Clear()
  SaveFile $scene $s.scene_depot 'gun_scene'
  $body=ReadPinned $s.body_current;$bg=$body.RootChunk.Graph.Chunk
  $be=@(EdgesB5 $bg|ForEach-Object {$_}|Where-Object { -not ($_[0] -eq 4 -and $_[2] -eq 5)})
  $gate=AllB5 ([ordered]@{($s.tag+'_Issued')=1;($s.tag+'_Finished')=0;($s.tag+'_Fault')=0})
  $states=[WolvenKit.RED4.Types.questLogicalCondition]::new();$states.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
  Add-RedHandle $states.Conditions (JournalCondition $s.journals[0] 'Inactive');Add-RedHandle $states.Conditions (JournalCondition $s.journals[0] 'Active');Add-RedHandle $gate.Conditions $states
  AddNodeB5 $bg (New-ConditionNode 100 $gate)
  $request=(Get-QuestNode $bg 5).DeepCopy();ClearB5 $request;$request.Id=[uint16]101;$request.SceneFile=[WolvenKit.RED4.Types.CResourceAsyncReference[WolvenKit.RED4.Types.scnSceneResource]]::new($s.scene_depot);AddNodeB5 $bg $request
  $be+=,@(4,'Out',100,'In');$be+=,@(100,'False',5,'wilson_default_in');$be+=,@(100,'True',101,'wilson_default_in');$be+=,@(12,'CutSource',101,'CutDestination');RebuildB5 $bg $be
  SaveFile $body $s.body_depot 'wilson_body';$overrides+=,$s.body_depot
  $transforms+=,@{depot=$s.scene_depot;source=$s.scene_native;operation='Bounded stock order/vendor/inventory/reward route; omit first-meet greeting/prop/attention and unrelated DLC shop/main-quest tracking. Scene graph exact listed edge plan.'}
  $transforms+=,@{depot=$s.body_depot;before_source=$s.body_current;operation='Only owned Inactive/Active Gun selector and copied scene request; old false path and all actor/distance/wanted payloads unchanged.'}
 }
 foreach($p in $s.sourcepins.PSObject.Properties){if(-not $pins.Contains($p.Name)){Pin $p.Name}}
 foreach($p in $s.sourcepins.PSObject.Properties){if($pins[$p.Name] -cne $p.Value){throw "Source changed: $($p.Name)"}}
}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw 'Pinned source changed during build'}}
$manifest=[ordered]@{schema=1;status='BUILT_NOT_INSTALLED';revision=$Revision;resources=$resources;boots=$boots;source_pins=$pins;native_copies=$copies;native_readbacks=$nativeReadbacks;transforms=$transforms;mod_overrides=$overrides;override_donors=$contractData.override_donors;contract=$contractPath;common_equal=$common;live='NOT_TESTED'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($manifest|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
[ordered]@{revision=$Revision;resources=$resources.Count;boots=$boots.Count;overrides=$overrides.Count;build=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
