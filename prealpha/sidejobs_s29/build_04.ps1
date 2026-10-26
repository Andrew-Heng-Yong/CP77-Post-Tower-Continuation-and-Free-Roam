param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $WorkspaceRoot 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision);if(Test-Path $out){throw 'Use successor directory'}
$source=Join-Path $out 'source';$readback=Join-Path $out 'readback';New-Item -ItemType Directory $source,$readback -Force|Out-Null
$preparedRel='prealpha/sidejobs_s29/prepared_04/prepared.json';$p=Get-Content (Join-Path $WorkspaceRoot $preparedRel) -Raw|ConvertFrom-Json -Depth 100
$pins=[ordered]@{};$resources=[ordered]@{};$boots=[Collections.Generic.List[string]]::new();$transforms=[Collections.Generic.List[object]]::new();$recipes=[Collections.Generic.List[object]]::new()
function Pin($path){$pins[$path]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $path)).Hash}
foreach($v in $p.source_pins.PSObject.Properties){Pin $v.Name;if($pins[$v.Name] -cne $v.Value){throw ('Source changed '+$v.Name)}}
foreach($f in @($preparedRel,'prealpha/sidejobs_s29/build_04.ps1','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1')){Pin $f}
function GraphAt($g,[string]$path){if($path -ne 'root'){foreach($id in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$id)).PhaseGraph.Chunk}};return $g}
function Native($dep){return (Read-Cr2wFile (Join-Path $WorkspaceRoot $p.index.$dep.raw)).RootChunk}
function CopyNode($g,$og,[int]$id,[int]$newid=-1){$o=Get-QuestNode $og $id;$n=$o.DeepCopy();ClearB5 $n;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk};if($newid -ge 0){$n.Id=[uint16]$newid};AddNodeB5 $g $n}
function Ref($n,$dep){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($dep)}
function Child($id,$dep,$inputName='In1'){$n=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$n.Id=[uint16]$id;Ref $n $dep;[void](New-QuestSocket $n $inputName 'Input');[void](New-QuestSocket $n 'Out1' 'Output');return $n}
function SaveRoot($root,$depot){$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root;$raw=Join-Path $source $depot;Write-Cr2wFile $f $raw;$rb=Join-Path $readback ($depot+'.json');New-Item -ItemType Directory (Split-Path $rb -Parent) -Force|Out-Null;Export-Cr2wJson (Read-Cr2wFile $raw) $rb;$resources[$depot]=(Get-FileHash $raw).Hash}
function SaveGraph($g,$dep){$r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g;SaveRoot $r $dep}
function JournalCondition($spec){$path=[WolvenKit.RED4.Types.gameJournalPath]::new();$path.RealPath=$spec.path;$path.ClassName=$spec.class;$path.FileEntryIndex=2;$t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $path;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]([int]$spec.states[0]);$t.Inverted=$false;$c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c}
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new();$count=0
foreach($item in $p.inputs){
 Pin $item.expected;$json=Get-Content (Join-Path $WorkspaceRoot $item.expected) -Raw
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],$json,$options)
 SaveRoot $dto.Data.RootChunk $item.depot;$count++;if($count%25 -eq 0){Write-Output "Serialized $count resource copies"}
}
# Remove unrelated roots from the three scoped native owners. Embedded graphs,
# prefabs and all retained node payloads remain native.
foreach($job in $p.jobs){if($null -eq $job.subset){continue}
 $root=(Read-Cr2wFile (Join-Path $source $job.private_native)).RootChunk;$og=$root.Graph.Chunk;$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $job.subset){CopyNode $g $og ([int]$id)}
 AddNodeB5 $g (New-InputNode 65000 'In1');$edges=@($job.selected_edges|ForEach-Object {,@($_)})
 $edges+=,@(65000,'Out',[int]$job.start_node,$job.start_socket);RebuildB5 $g $edges;Set-RedHandleProperty $root Graph $g;SaveRoot $root $job.private_native
 $transforms.Add(@{kind='subset';id=$job.id;depot=$job.private_native;ids=$job.subset;edges=$edges})
}
# Native service release handoffs. Never reset or terminate the shared owner.
$nix=($p.jobs|Where-Object id -eq 'mq016_bartmoss').private_native;$root=(Read-Cr2wFile (Join-Path $source $nix)).RootChunk;$g=$root.Graph.Chunk
$edges=@(EdgesB5 $g|ForEach-Object {$_});$changed=0
foreach($e in $edges){if($e[0] -eq 6 -and $e[2] -eq 3){$e[2]=64000;$e[3]='In';$changed++}}
if($changed -ne 1){throw 'Nix handoff boundary changed'}
AddNodeB5 $g (New-SetFactNode 64000 'nix_default_on' 0);AddNodeB5 $g (PauseB5 64001 (AllB5 ([ordered]@{nix_default_on=0;PTFRB0S4NIX_OwnerActive=0})))
$edges+=,@(64000,'Out',64001,'In');$edges+=,@(64001,'Out',3,'In1');RebuildB5 $g $edges;SaveRoot $root $nix
$transforms.Add(@{kind='nix_release';depot=$nix;graph='root';edge=@(6,'Out',3,'In1');nodes=@(64000,64001)})
$pepe=($p.jobs|Where-Object id -eq 'mq040_biosculpt').private_native;$root=(Read-Cr2wFile (Join-Path $source $pepe)).RootChunk;$g=GraphAt $root.Graph.Chunk 'root/3'
$edges=@(EdgesB5 $g|ForEach-Object {$_});$changed=0
foreach($e in $edges){if($e[0] -eq 11 -and $e[2] -eq 2){$e[2]=64000;$e[3]='In';$changed++}}
if($changed -ne 1){throw 'Pepe handoff boundary changed'}
AddNodeB5 $g (PauseB5 64000 (AllB5 ([ordered]@{elcoyote_barman_default_on=0;PTFRB0STPEPE_OwnerActive=0})))
$edges+=,@(64000,'Out',2,'In');RebuildB5 $g $edges;SaveRoot $root $pepe
$transforms.Add(@{kind='pepe_release';depot=$pepe;graph='root/3';edge=@(11,'Out',2,'In');nodes=@(64000)})
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
function PhoneIssued($name){if($name -ceq 'delamain'){return 'PTFRS22_SQ025_SupportIssued'};return 'PTFRS29_PHONE_'+$name+'_Issued'}
foreach($job in $p.jobs){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$tag=$job.tag;$child=64000;$edges=@()
 if($null -ne $job.parent){
  $parent=$job.parent;$og=(Native $parent.depot).Graph.Chunk;$child=[int]$parent.child
  foreach($id in $parent.ids){CopyNode $g $og ([int]$id)};Ref (Get-QuestNode $g $child) $job.private_native
  foreach($e0 in $parent.edges){$e=@($e0);if($e[0] -eq $parent.input_node){$e[0]=65005};if($e[2] -eq $child){$e[2]=65006;$e[3]='In'};$edges+=,$e}
 }else{AddNodeB5 $g (Child $child $job.private_native $job.input);$edges+=,@(65005,'Out',65006,'In')}
 $pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]};foreach($f in $job.facts_equal.PSObject.Properties){$pairs[$f.Name]=[int]$f.Value}
 foreach($s in @('Issued','Entered','Finished','Fault')){$pairs[$tag+'_'+$s]=0};$pairs[$tag+'_Permit']=1
 foreach($name in $job.phones){$pairs[(PhoneIssued $name)]=1}
 $c=AllB5 $pairs;foreach($j in $job.journals){Add-RedHandle $c.Conditions (JournalCondition $j)}
 foreach($f in $job.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $f.Name ([int]$f.Value.min) 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $f.Name ([int]$f.Value.max) 'LessOrEqual')}
 if($job.id -ceq 'sq025b_delamain_insurgence'){
  $o=[WolvenKit.RED4.Types.questLogicalCondition]::new();$o.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
  Add-RedHandle $o.Conditions (New-FactCondition 'PTFRS22_SQ025_Issued' 0 'Equal');Add-RedHandle $o.Conditions (New-FactCondition 'PTFRS22_SQ025_Finished' 1 'Equal');Add-RedHandle $c.Conditions $o
 }
 foreach($n in @((New-InputNode 65000 'In1'),(New-SetFactNode 65001 ($tag+'_Ready') 1),(New-SetFactNode 65002 ($tag+'_Revision') 1),(PauseB5 65003 $c),(New-ConditionNode 65004 $c.DeepCopy()),(New-SetFactNode 65005 ($tag+'_Issued') 1),(New-SetFactNode 65006 ($tag+'_Entered') 1),(New-SetFactNode 65007 ($tag+'_Finished') 1))){AddNodeB5 $g $n}
 $edges+=,@(65000,'Out',65001,'In');$edges+=,@(65001,'Out',65002,'In');$edges+=,@(65002,'Out',65003,'In');$edges+=,@(65003,'Out',65004,'In');$edges+=,@(65004,'False',65003,'In');$edges+=,@(65004,'True',65005,'In');$edges+=,@(65006,'Out',$child,$job.input)
 $node=Get-QuestNode $g $child
 if(@($node.Sockets|Where-Object {$_.Chunk.Name.ToString() -ceq 'Out1'}).Count -eq 1){$edges+=,@($child,'Out1',65007,'In')}
 if($job.PSObject.Properties.Name -contains 'native_entry_condition'){
  $spec=$job.native_entry_condition;$og=GraphAt (Native $spec.depot).Graph.Chunk $spec.graph
  AddNodeB5 $g (PauseB5 64001 (Get-QuestNode $og ([int]$spec.node)).Condition.Chunk.DeepCopy())
  foreach($e in $edges){if($e[0] -eq 65005 -and $e[2] -eq 65006){$e[2]=64001}}
  $edges+=,@(64001,'Out',65006,'In')
 }
 RebuildB5 $g $edges;$dep='towercontinued\sidejobs_s29\entries\'+$job.id+'.questphase';SaveGraph $g $dep;$boots.Add($dep)
 $recipes.Add(@{id=$job.id;depot=$dep;child=$child;guard=$pairs;edges=$edges})
}
$init=(Native 'base\quest\holocalls\holocall_initializers.questphase').Graph.Chunk
$globalIdle=@('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance')
foreach($contact in $p.contacts){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new();CopyNode $g $init ([int]$contact.init)
 $pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]};foreach($f in @($globalIdle)+@($contact.idle)){$pairs[$f]=0}
 $issued=PhoneIssued $contact.name;$pairs[$issued]=0;$pairs['PTFRS29_'+$contact.consumer+'_Permit']=1;$pairs['PTFRS29_'+$contact.consumer+'_Issued']=0
 if($contact.name -ceq 'delamain'){foreach($n in @('delamain','delamain_angry','delamain_sad','delamain_mean','delamain_manic','delamain_scared','delamain_deep','delamain_suicidal')){foreach($dir in @(($n+'_calls_v'),('v_calls_'+$n))){foreach($s in @('start_activate','end_activate','active')){$pairs['holo_'+$dir+'_'+$s]=0}}}}
 foreach($n in @((New-InputNode 1000 'In1'),(PauseB5 1002 (AllB5 $pairs)),(New-ConditionNode 1003 (AllB5 $pairs)),(New-SetFactNode 1004 $issued 1))){AddNodeB5 $g $n}
 RebuildB5 $g @(@(1000,'Out',1002,'In'),@(1002,'Out',1003,'In'),@(1003,'False',1002,'In'),@(1003,'True',1004,'In'),@(1004,'Out',[int]$contact.init,'In1'))
 $dep='towercontinued\sidejobs_s29\phone\'+$contact.name+'.questphase';SaveGraph $g $dep;$boots.Add($dep)
}
# Extend only the current PTFR cleanup resource. Keep all old contact payloads.
$oldRel='prealpha/sidejobs_s27/build/s27_03/source/towercontinued/gig_phone_u9/fixer_cleanup.questphase';Pin $oldRel
$old=(Read-Cr2wFile (Join-Path $WorkspaceRoot $oldRel)).RootChunk;$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($n in $old.Graph.Chunk.Nodes){CopyNode $g $old.Graph.Chunk ([int]$n.Chunk.Id.ToString())}
$edges=@(EdgesB5 $old.Graph.Chunk|ForEach-Object {$_});$changed=0
foreach($e in $edges){if($e[0] -in @(1011,1002,1003) -and $e[2] -eq 6){$e[2]=1210;$e[3]='In';$changed++}}
if($changed -ne 3){throw 'Cleanup boundary changed'}
$native=(Native 'base\quest\holocalls\holocall_cleanup.questphase').Graph.Chunk;$contacts=@($p.contacts|Where-Object name -ne 'delamain')
for($i=0;$i -lt $contacts.Count;$i++){
 $c=$contacts[$i];$cid=1200+2*$i;$phase=$cid+1;$gate=1250+$i
 if($i -eq 0){$gate=1210}
 # Gate IDs are disjoint from original and copied condition/phase IDs.
 if($i -eq 0){$gate=1240;foreach($e in $edges){if($e[2] -eq 1210){$e[2]=$gate}}}
 CopyNode $g $native ([int]$c.condition) $cid;CopyNode $g $native ([int]$c.cleanup) $phase
 AddNodeB5 $g (New-ConditionNode $gate (AllB5 ([ordered]@{(PhoneIssued $c.name)=1})))
 $next=if($i -lt $contacts.Count-1){1250+$i+1}else{6};$input=if($next -eq 6){'In2'}else{'In'}
 $edges+=,@($gate,'True',$cid,'In');$edges+=,@($gate,'False',$next,$input);$edges+=,@($cid,'True',$phase,$c.input);$edges+=,@($cid,'False',$next,$input);$edges+=,@($phase,$c.output,$next,$input)
}
RebuildB5 $g $edges;Set-RedHandleProperty $old Graph $g;SaveRoot $old 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
foreach($f in $pins.Keys){if((Get-FileHash (Join-Path $WorkspaceRoot $f)).Hash -cne $pins[$f]){throw 'Source drift'}}
$m=[ordered]@{status='BUILT_NOT_INSTALLED';resources=$resources;boots=$boots.ToArray();recipes=$recipes.ToArray();transforms=$transforms.ToArray();source_pins=$pins;prepared=$preparedRel;cleanup_donor=$oldRel;official_overrides=@();mod_overrides=@('towercontinued\gig_phone_u9\fixer_cleanup.questphase')}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($m|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
@{status=$m.status;resources=$resources.Count;boots=$boots.Count;out=$out}|ConvertTo-Json
