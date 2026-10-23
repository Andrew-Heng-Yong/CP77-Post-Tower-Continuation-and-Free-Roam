param([string]$Revision='native_04',[string]$PresentationManifest='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$toolsRoot=Join-Path $WorkspaceRoot 'tools'
. (Join-Path $toolsRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $toolsRoot 'shark_b7_2_helpers.ps1')
$helper=Get-Content -LiteralPath (Join-Path $toolsRoot 'build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision);if(Test-Path -LiteralPath $out){throw 'Use successor build directory'}
$source=Join-Path $out 'source';$readback=Join-Path $out 'readback'
New-Item -ItemType Directory -Force $source,$readback|Out-Null
$planRel='research/gigs_u10/native/build_plan_01.json';$contractRel='research/gigs_u10/native/contracts_02.json'
$plan=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $planRel) -Raw|ConvertFrom-Json
$contracts=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $contractRel) -Raw|ConvertFrom-Json
$pins=[ordered]@{};foreach($p in $contracts.source_pins.PSObject.Properties){$pins[$p.Name]=$p.Value;R5Match (Join-Path $WorkspaceRoot $p.Name) $p.Value};foreach($p in $plan.pins.PSObject.Properties){$pins[$p.Name]=$p.Value;R5Match (Join-Path $WorkspaceRoot $p.Name) $p.Value}
function Pin([string]$rel){$pins[$rel]=R5Hash (Join-Path $WorkspaceRoot $rel)}
foreach($rel in @($planRel,$contractRel,'prealpha/gigs_u10/native/prepare_01.py','prealpha/gigs_u10/native/build_02.ps1','prealpha/gigs_u10/native/test_03.py','prealpha/gigs_u10/native/inventory_contract_02.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json')){Pin $rel}
$mapping=@{}
if($PresentationManifest){$pm=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $PresentationManifest) -Raw|ConvertFrom-Json;Pin $PresentationManifest;foreach($p in $pm.main_replacement.PSObject.Properties){$mapping[$p.Name]=$p.Value}}
function GraphU10($g,[string]$path){if($path -ne 'root'){foreach($i in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$i)).PhaseGraph.Chunk}};return $g}
function ReadU10([string]$raw,$embedded=$null){$f=Read-Cr2wFile (Join-Path $WorkspaceRoot $raw);if($null -ne $embedded){return $f.EmbeddedFiles[[int]$embedded].Content};return $f.RootChunk}
function EmptyU10 {return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function SliceU10($og,$ids){$g=EmptyU10;foreach($id in $ids){$original=Get-QuestNode $og ([int]$id);$n=$original.DeepCopy();ClearB5 $n;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk};AddNodeB5 $g $n};return $g}
function OwnU10([string]$id,[string]$key){return 'PTFRU10_'+$id+'_'+$key}
function RefU10($n,[string]$depot){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($depot)}
function TowerU10 {return [ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRU7_Support_Request=0;PTFRU7_Support_Issued=0;PTFRU6_Padre_Request=0;PTFRU6_Padre_Issued=0}}
function JournalCondition($path,$class,[int]$state=1){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=2
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]$state;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function InventoryCondition($spec){
 $root=ReadU10 $spec.raw $spec.embedded_index;$g=GraphU10 $root.Graph.Chunk $spec.graph
 $c=(Get-QuestNode $g $spec.node).Condition.Chunk.DeepCopy()
 if($c.GetType().Name -ne 'questObjectCondition' -or $c.Type.Chunk.GetType().Name -ne 'questInventory_ConditionType'){throw 'Unexpected inventory source condition'}
 if(!$c.Type.Chunk.IsPlayer -or [int]$c.Type.Chunk.Quantity.ToString() -ne 1){throw 'Unexpected inventory source semantics'}
 $c.Type.Chunk.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal;$c.Type.Chunk.Quantity=[uint32]0
 return $c
}
$resources=[ordered]@{};$boots=[Collections.Generic.List[string]]::new();$recipes=[Collections.Generic.List[object]]::new()
function SaveU10($g,[string]$name){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $depot='towercontinued\gigs_u10\native\'+$name+'.questphase';$raw=Join-Path $source $depot
 Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $readback ($name+'.json'))
 $resources[$depot]=R5Hash $raw;$boots.Add($depot);return $depot
}
foreach($job in $plan.jobs){
 $id=$job.id;$p=$job.parent;$root=ReadU10 $p.raw $p.binding.binding.embedded_index;$og=GraphU10 $root.Graph.Chunk $p.binding.graph
 $ids=@(@($p.ancestors|ForEach-Object id)+@($p.child.id)|Sort-Object -Unique);$g=SliceU10 $og $ids
 if($p.binding.graph -ne 'root'){throw 'Unexpected nested district parent'}
 (Get-QuestNode $g $p.input_node).SocketName='In1';$mainDepot=$job.resources[0].depot
 if($mapping.ContainsKey($mainDepot)){$mainDepot=$mapping[$mainDepot]}
 if($id -eq 'sts_hey_gle_03' -and -not $mapping.ContainsKey($job.resources[0].depot)){throw 'Psychofan presentation dependency required'}
 RefU10 (Get-QuestNode $g $p.child.id) $mainDepot
 $guard=TowerU10;$guard[(OwnU10 $id 'Permit')]=1;$guard[(OwnU10 $id 'Issued')]=0;$guard[(OwnU10 $id 'Fault')]=0
 if($job.retaliation_dependency){$guard['PTFRU9_Retaliation_Issued']=1;$guard['PTFRU9_Retaliation_Fault']=0;$guard['PTFRU9_Retaliation_'+$job.retaliation_gang+'_Issued']=1;$guard['PTFRU9_Retaliation_'+$job.retaliation_gang+'_Fault']=0}
 $contract=@($contracts.owners|Where-Object {$_.id -ceq $id})[0]
 foreach($f in $contract.facts_equal.PSObject.Properties){$guard[$f.Name]=[int]$f.Value}
 $condition=AllB5 $guard;foreach($j in $contract.journals){Add-RedHandle $condition.Conditions (JournalCondition $j.path $j.class ([int]$j.states[0]))};foreach($item in $contract.inventory_native){Add-RedHandle $condition.Conditions (InventoryCondition $item)}
 foreach($f in $contract.fact_ranges.PSObject.Properties){Add-RedHandle $condition.Conditions (New-FactCondition $f.Name ([int]$f.Value.min) 'GreaterOrEqual');Add-RedHandle $condition.Conditions (New-FactCondition $f.Name ([int]$f.Value.max) 'LessOrEqual')}
 foreach($n in @((New-SetFactNode 65000 (OwnU10 $id 'Ready') 1),(New-SetFactNode 65001 (OwnU10 $id 'Revision') 1),(PauseB5 65002 $condition),(New-SetFactNode 65003 (OwnU10 $id 'Issued') 1),(New-SetFactNode 65004 (OwnU10 $id 'Started') 1),(New-SetFactNode 65005 (OwnU10 $id 'MainFinished') 1),(New-SetFactNode 65006 (OwnU10 $id 'OwnerFinished') 1),(New-SetFactNode 65007 ('PTFRU9_'+$job.region+'_TierRequest') 1),(New-ConditionNode 65008 $condition.DeepCopy()))){AddNodeB5 $g $n}
 $edges=@();$mainInputs=@($p.edges|Where-Object {$_[2] -eq $p.child.id}|ForEach-Object {$_[3]}|Sort-Object -Unique)
 $mainInput=if($mainInputs -contains 'STS_started'){'STS_started'}elseif($mainInputs.Count -eq 1){$mainInputs[0]}else{throw ('Multiple main lifecycle inputs '+$id)}
 foreach($e0 in $p.edges){$e=@($e0);if($e[0] -eq $p.input_node){$e[0]=65007};if($e[2] -eq $p.child.id -and $e[3] -eq $mainInput){$e[2]=65004;$e[3]='In'};$edges+=,$e}
 foreach($e in @(@($p.input_node,'Out',65000,'In'),@(65000,'Out',65001,'In'),@(65001,'Out',65002,'In'),@(65002,'Out',65008,'In'),@(65008,'False',65002,'In'),@(65008,'True',65003,'In'),@(65003,'Out',65007,'In'),@(65004,'Out',$p.child.id,$mainInput))){$edges+=,$e}
 $cn=64000;$cleanup=@()
 foreach($c in $job.companions){
  $cr=ReadU10 $c.source_raw;$cg=GraphU10 $cr.Graph.Chunk $c.source_graph;$original=Get-QuestNode $cg $c.source_node;$n=$original.DeepCopy();$n.Id=[uint16]$cn;ClearB5 $n
  if($null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
  if($c.depot){RefU10 $n $c.depot};AddNodeB5 $g $n
  if($c.kind -eq 'parallel_prestate'){$edges+=,@(65003,'Out',$cn,$c.input)}
  elseif($c.kind -eq 'cleanup'){$edges+=,@($p.child.id,$c.from_output,$cn,$c.input);$cleanup+=,@{id=$cn;spec=$c}}
  else{throw 'Unknown companion kind'}
  $cn++
 }
 foreach($port in $job.outputs){$edges+=,@($p.child.id,$port,65005,'In')}
 if($cleanup.Count -eq 0){$edges+=,@(65005,'Out',65006,'In')}
 else{foreach($c in $cleanup){foreach($port in $c.spec.outputs){$edges+=,@($c.id,$port,65006,'In')}}}
 RebuildB5 $g $edges;$depot=SaveU10 $g ($id+'_entry')
 $recipes.Add(@{kind='entry';id=$id;depot=$depot;raw=$p.raw;graph=$p.binding.graph;ids=$ids;edges=$edges;main_input=$mainInput;native=$mainDepot;companions=$job.companions;guard=$guard;guard_journals=$contract.journals})
}
foreach($job in @($plan.jobs|Where-Object retaliation_dependency)){
 $id=$job.id;$contract=@($contracts.owners|Where-Object {$_.id -ceq $id})[0];$g=EmptyU10
 $guard=TowerU10;$guard[(OwnU10 $id 'PreparePermit')]=1;$guard[(OwnU10 $id 'Issued')]=0;$guard[(OwnU10 $id 'Fault')]=0;$guard[(OwnU10 $id 'ServiceRequested')]=0
 foreach($f in $contract.facts_equal.PSObject.Properties){$guard[$f.Name]=[int]$f.Value}
 $guard['PTFRU9_Retaliation_Ready']=1;$guard['PTFRU9_Retaliation_Fault']=0;$guard['PTFRU9_Retaliation_'+$job.retaliation_gang+'_Fault']=0
 $condition=AllB5 $guard;foreach($j in $contract.journals){Add-RedHandle $condition.Conditions (JournalCondition $j.path $j.class ([int]$j.states[0]))};foreach($item in $contract.inventory_native){Add-RedHandle $condition.Conditions (InventoryCondition $item)}
 foreach($fact in @('PTFRU9_Retaliation_Issued',('PTFRU9_Retaliation_'+$job.retaliation_gang+'_Issued'))){Add-RedHandle $condition.Conditions (New-FactCondition $fact 0 'GreaterOrEqual');Add-RedHandle $condition.Conditions (New-FactCondition $fact 1 'LessOrEqual')}
 foreach($n in @((New-InputNode 0 'In1'),(PauseB5 1 $condition),(New-ConditionNode 2 $condition.DeepCopy()),(New-SetFactNode 3 (OwnU10 $id 'ServiceRequested') 1),(New-SetFactNode 4 'PTFRU9_Retaliation_Request' 1),(New-SetFactNode 5 ('PTFRU9_Retaliation_'+$job.retaliation_gang+'_Request') 1))){AddNodeB5 $g $n}
 $edges=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'False',1,'In'),@(2,'True',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,'In'));RebuildB5 $g $edges
 $depot=SaveU10 $g ($id+'_service_request');$recipes.Add(@{kind='service_request';id=$id;depot=$depot;guard=$guard;guard_journals=$contract.journals;edges=$edges;gang=$job.retaliation_gang})
}
foreach($c in $plan.credits){
 $og=GraphU10 (ReadU10 $c.raw).Graph.Chunk $c.graph;$g=SliceU10 $og $c.ids
 $guard=[ordered]@{(OwnU10 $c.id 'Started')=1;(OwnU10 $c.id 'CreditEntered')=0;(OwnU10 $c.id 'CreditDone')=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
 foreach($n in @((PauseB5 65000 (AllB5 $guard)),(New-SetFactNode 65001 (OwnU10 $c.id 'CreditEntered') 1),(New-SetFactNode 65002 (OwnU10 $c.id 'CreditDone') 1))){AddNodeB5 $g $n}
 $edges=@();foreach($e0 in $c.edges){$e=@($e0);if($e[0] -eq 0){$e[0]=65001};$edges+=,$e};$edges+=,@(0,'Out',65000,'In');$edges+=,@(65000,'Out',65001,'In');$edges+=,@($c.end,'Out',65002,'In');RebuildB5 $g $edges
 $depot=SaveU10 $g ($c.id+'_credit');$recipes.Add(@{kind='credit';id=$c.id;depot=$depot;raw=$c.raw;graph=$c.graph;ids=$c.ids;edges=$edges})
}
$mi=@{}
foreach($m in $plan.maps){
 if(-not $mi.ContainsKey($m.id)){$mi[$m.id]=0};$index=$mi[$m.id];$mi[$m.id]++
 $og=GraphU10 (ReadU10 $m.raw).Graph.Chunk $m.graph;$g=SliceU10 $og $m.ids
 $guard=[ordered]@{(OwnU10 $m.id 'Started')=1;(OwnU10 $m.id 'MapPermit')=1;(OwnU10 $m.id ('Map'+$index+'Entered'))=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
 $job=@($plan.jobs|Where-Object {$_.id -ceq $m.id})[0];foreach($f in $job.terminal){$guard[$f]=0}
 $condition=AllB5 $guard;Add-RedHandle $condition.Conditions (JournalCondition $job.entries[0].path 'gameJournalQuest')
 AddNodeB5 $g (PauseB5 65000 $condition);AddNodeB5 $g (New-SetFactNode 65001 (OwnU10 $m.id ('Map'+$index+'Entered')) 1)
 $edges=@();foreach($e0 in $m.edges){$e=@($e0);if($e[0] -eq $m.input){$e[0]=65001};$edges+=,$e};$edges+=,@($m.input,'Out',65000,'In');$edges+=,@(65000,'Out',65001,'In');RebuildB5 $g $edges
 $depot=SaveU10 $g ($m.id+'_map'+$index);$recipes.Add(@{kind='map';id=$m.id;index=$index;depot=$depot;raw=$m.raw;graph=$m.graph;ids=$m.ids;edges=$edges;foreign_poi_contraction=$m.foreign_poi_contraction})
}
# Preserve the existing mod-owned retaliation instance. The predecessor has the
# complete new-gig branches, but their exact selector startup edges were cut.
$overlayDepot='towercontinued\special_gigs_u9\gang_retaliation.questphase'
$donorArchive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_PreAlpha.archive'
$donorArchiveHash=R5Hash $donorArchive
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($donorArchive,$hs,[ref]$arc).ToString() -ne 'NoError'){throw 'Cannot read installed donor'}
$entry=@($arc.Files.Values|Where-Object {$_.Name -ceq $overlayDepot});if($entry.Count -ne 1){throw 'Missing/ambiguous installed overlay donor'}
$donorDir=Join-Path $out 'donor';New-Item -ItemType Directory -Force $donorDir|Out-Null
$donorRaw=Join-Path $donorDir 'gang_retaliation.questphase';$stream=[IO.File]::Create($donorRaw);try{$entry[0].Extract($stream)}finally{$stream.Dispose()}
R5Match $donorRaw '7B45FC9F27DB1EE48A018AB9A407845168E99AFD5D166491AC77503261DDBBA0'
$donor=Read-Cr2wFile $donorRaw;Export-Cr2wJson $donor (Join-Path $donorDir 'gang_retaliation.json');$overlay=$donor.RootChunk.DeepCopy();RewireB5 $overlay.Graph.Chunk $donor.RootChunk.Graph.Chunk
$selectorEdits=@(@{graph='root/22/33/227';entry=38;selector=37;id='sts_hey_rey_02'},@{graph='root/22/37/298';entry=81;selector=79;id='sts_wbr_jpn_12'})
foreach($s in $selectorEdits){
 $g=GraphU10 $overlay.Graph.Chunk $s.graph;$n=Get-QuestNode $g $s.selector;$condition=AllB5 ([ordered]@{(OwnU10 $s.id 'Started')=1});Add-RedHandle $condition.Conditions $n.Condition.Chunk.DeepCopy();Set-RedHandleProperty $n Condition $condition
 $edges=@(EdgesB5 $g|ForEach-Object {$_});if(@($edges|Where-Object {$_[0] -eq 0 -and $_[2] -eq $s.entry}).Count){throw 'Selector already connected in donor'}
 $edges+=,@(0,'Out',$s.entry,'In');RebuildB5 $g $edges
}
$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$overlay;$overlayRaw=Join-Path $source $overlayDepot;Write-Cr2wFile $f $overlayRaw;Export-Cr2wJson (Read-Cr2wFile $overlayRaw) (Join-Path $readback 'retaliation_overlay.json');$resources[$overlayDepot]=R5Hash $overlayRaw
Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,$donorRaw).Replace('\','/'));Pin ([IO.Path]::GetRelativePath($WorkspaceRoot,(Join-Path $donorDir 'gang_retaliation.json')).Replace('\','/'))
$oldRawRel='build/SpecialGigsU9/source/towercontinued/special_gigs_u9/gang_retaliation.questphase';Pin $oldRawRel;R5Match (Join-Path $WorkspaceRoot $oldRawRel) (R5Hash $donorRaw)
foreach($p in @('research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_gang_retaliation.questphase','research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_gang_retaliation.questphase.json')){Pin $p}
foreach($p in $pins.Keys){R5Match (Join-Path $WorkspaceRoot $p) $pins[$p]}
$component=[ordered]@{status='BUILT_U10_NATIVE_ENGINE_PENDING';resources=$resources;boots=$boots.ToArray();source_pins=$pins;contract=$contractRel;recipes=$recipes.ToArray();source_dir=$source;readback_dir=$readback;original_gameplay_resources_packed=0;official_overrides=0;warnings=$plan.warnings;builder_sha256=R5Hash $PSCommandPath;mod_overrides=@($overlayDepot);override_donors=@{$overlayDepot=@{source=$oldRawRel;sha256=R5Hash $donorRaw}};overlay=@{depot=$overlayDepot;installed_donor_archive=$donorArchive;installed_donor_archive_sha256=$donorArchiveHash;donor_resource_sha256=R5Hash $donorRaw;selector_edits=$selectorEdits;saved_owner_loading_live_pending=$true;restart=$false}}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($component|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
Write-Output ('BUILT '+$out)
