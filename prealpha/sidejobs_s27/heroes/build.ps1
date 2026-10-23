param([string]$Revision='heroes_01',[string]$Contract='prealpha/sidejobs_s27/heroes/contract05.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Definition helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^heroes_\d{2}$'){throw 'Invalid immutable revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Component already exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$spec=Get-Content (Join-Path $ws $Contract) -Raw|ConvertFrom-Json
$pins=[ordered]@{};$copies=[Collections.Generic.List[object]]::new();$resources=[Collections.Generic.List[object]]::new()
function Pin($rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $ws $rel)).Hash}
function ReadGraph($rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return (Read-Cr2wFile (Join-Path $ws $rel)).RootChunk.Graph.Chunk}
function NewGraph{return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function GraphAt($g,$path){foreach($id in ($path -split '/'|Select-Object -Skip 1)){$g=(Get-QuestNode $g ([int]$id)).PhaseGraph.Chunk};return $g}
function CopyNode($dest,$src,$id,$rel,$gp,$target,$newid=$id){
 $old=Get-QuestNode $src $id;$n=$old.DeepCopy();ClearB5 $n;$n.Id=[uint16]$newid
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $old.PhaseGraph.Chunk}
 AddNodeB5 $dest $n;$copies.Add([ordered]@{source=$rel;source_graph=$gp;source_id=$id;target_graph=$target;target_id=$newid})
}
function SaveGraph($g,$depot,$key){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 $json=Join-Path $out ('readback/'+$key+'.json');Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $resources.Add([ordered]@{depot=$depot;relative=('source/'+$depot.Replace('\','/'));sha256=(Get-FileHash $raw).Hash;readback=('readback/'+$key+'.json');readback_sha256=(Get-FileHash $json).Hash})
}
function JournalCondition($j){
 if(@($j.states).Count -ne 1 -or $j.states[0] -ne 1){throw 'Only Inactive fresh entry'}
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$j.path;$p.ClassName=$j.class;$p.FileEntryIndex=if($j.path.StartsWith('contacts/')){1}else{2}
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
$o=$spec.owners[0]
$intro=ReadGraph $o.native_only_checks[0].source
$default=ReadGraph $o.service_source
$inventory=(Get-QuestNode (GraphAt $intro $o.native_only_checks[0].graph) ([int]$o.native_only_checks[0].node)).Condition.Chunk.DeepCopy()
$inventory.Type.Chunk.Quantity=[uint32]0
$distance=(Get-QuestNode (GraphAt $default $o.native_only_checks[1].graph) ([int]$o.native_only_checks[1].node)).Condition.Chunk.Conditions[0].Chunk.DeepCopy()
function Guard(){
 $pairs=[ordered]@{};foreach($s in @($spec.common_equal,$o.facts_equal)){foreach($p in $s.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 $pairs[$o.tag+'_Permit']=1;$pairs[$o.tag+'_Issued']=0;$pairs[$o.tag+'_Finished']=0;$pairs[$o.tag+'_Fault']=0
 $pairs['PTFRS27_PHONE_MAMA_Issued']=1
 $c=AllB5 $pairs
 foreach($p in $o.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.min) 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.max) 'LessOrEqual')}
 foreach($j in $o.journals){Add-RedHandle $c.Conditions (JournalCondition $j)}
 Add-RedHandle $c.Conditions ($inventory.DeepCopy());Add-RedHandle $c.Conditions ($distance.DeepCopy())
 return $c
}
$g=NewGraph
$parent=ReadGraph $o.parent_source
foreach($id in $o.parent_nodes){CopyNode $g $parent ([int]$id) $o.parent_source 'root' 'heroes_package/root'}
$entry=ReadGraph $o.entry_source
CopyNode $g $entry ([int]$o.entry_node) $o.entry_source 'root' 'heroes_package/root'
$phase=Get-QuestNode $g ([int]$o.entry_node)
if(@($phase.Sockets|Where-Object {$_.Chunk.Name.ToString() -eq 'Out2'}).Count -eq 0){[void](New-QuestSocket $phase 'Out2' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))}
$cc=$o.contact_copy
CopyNode $g (GraphAt $entry $cc.graph) ([int]$cc.id) $cc.source $cc.graph 'heroes_package/root' 1010
foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 ($o.tag+'_Ready') 1),(PauseB5 1002 (Guard)),(PauseB5 1003 (AllB5 ([ordered]@{PTFRS27_PHONE_MAMA_Issued=1}))),(New-ConditionNode 1004 (Guard)),(New-SetFactNode 1005 ($o.tag+'_Issued') 1),(New-SetFactNode 1006 ($o.tag+'_Entered') 1),(New-SetFactNode 1007 ($o.tag+'_Finished') 1),(New-SetFactNode 1008 ($o.tag+'_Fault') 1))){AddNodeB5 $g $n}
$e=@(@(1000,'Out',1001,'In'),@(1001,'Out',1002,'In'),@(1002,'Out',1003,'In'),@(1003,'Out',89,'In'),@(89,'Out',119,'In'),@(119,'Out',1004,'In'),@(1004,'False',1002,'In'),@(1004,'True',1005,'In'),@(1005,'Out',1006,'In'),@(1006,'Out',1010,'In'),@(1010,'Out',42,'In'),@(42,'Out2',1007,'In'),@(42,'Out1',1008,'In'))
RebuildB5 $g $e;SaveGraph $g $o.depot 'heroes_package'
# Copy only Mama's original post-quest default loop. No common default-dialog
# root, no other service NPC, and no custom spawn/default-state mutation.
$service=NewGraph;$serviceTag='PTFRS27_HEROES_MAMA';$serviceDepot='towercontinued\sidejobs_s27\heroes\mama_default.questphase'
$pairs=[ordered]@{};foreach($p in $spec.common_equal.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}
$pairs[$o.tag+'_Issued']=1;$pairs[$o.tag+'_Finished']=1;$pairs[$o.tag+'_Fault']=0;$pairs['PTFRS27_PHONE_MAMA_Issued']=1;$pairs[$serviceTag+'_Issued']=0
foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 ($serviceTag+'_Ready') 1),(PauseB5 1002 (AllB5 $pairs)),(New-SetFactNode 1003 ($serviceTag+'_Issued') 1))){AddNodeB5 $service $n}
$sg=GraphAt $default $o.service_graph
foreach($id in $o.service_nodes){CopyNode $service $sg ([int]$id) $o.service_source $o.service_graph 'mama_default/root'}
RebuildB5 $service @(@(1000,'Out',1001,'In'),@(1001,'Out',1002,'In'),@(1002,'Out',1003,'In'),@(1003,'Out',16,'In'),@(16,'Out',17,'In1'),@(17,'Out1',16,'In'))
SaveGraph $service $serviceDepot 'mama_default'
foreach($p in $spec.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw ('Changed contract source: '+$p.Name)}}
foreach($p in @($Contract,'prealpha/sidejobs_s27/heroes/build.ps1','prealpha/sidejobs_s27/heroes/test.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1')){Pin $p}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $ws $p)).Hash -cne $pins[$p]){throw 'Source changed during build'}}
$map=[ordered]@{};foreach($r in $resources){$map[$r.depot]=$r.sha256}
$m=[ordered]@{status='COMPONENT_BUILT_FRESH_HEROES_PACKAGE_LIVE_PENDING';revision=$Revision;resources=$map;resource_details=@($resources.ToArray());boots=@($o.depot,$serviceDepot);contract=$Contract;contract_sha256=$pins[$Contract];source_pins=$pins;native_copies=@($copies.ToArray());native_resources=$spec.native_resources;override_donors=@{};native_changes=@('Directly references original package/introduction questphase; original parent enable/token waits and Mama AddContact node copied','Two native admission checks copy stock key inventory condition with quantity0 and original Coyote offsite distance condition','Copies individual original Mama default loop after this owner completes; native quest does its original Mama spawn/default switch','Adds otherwise-unused original Out2 phase output socket to observe package completion');limitations=@('Fresh package-outcome branch only; no Failed/progressed restart, funeral route, or completed replay','No custom quest progress, item, outcome, native phone counter, or reward reset','Live Mama call/SMS, H10 package, bike/reward, post-completion Mama interaction, save/reload pending');native_progress_resets=$false;game_writes=$false}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($m|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))
[pscustomobject]$m|Select-Object status,revision,contract_sha256|ConvertTo-Json
