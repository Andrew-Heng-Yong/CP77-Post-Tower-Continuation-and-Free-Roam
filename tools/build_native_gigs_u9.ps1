param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_gigs_u9';$out=Join-Path $WorkspaceRoot 'build/NativeGigsU9';$source=Join-Path $out ('source_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Installed U9 evidence pinned'}
New-Item -ItemType Directory -Force $audit,$source|Out-Null
$helper=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$planPath=Join-Path $audit 'build_plan.json';$plan=Get-Content -LiteralPath $planPath -Raw|ConvertFrom-Json
foreach($p in $plan.pins.PSObject.Properties){R5Match (Join-Path $WorkspaceRoot $p.Name) $p.Value}
function GraphU9($g,[string]$path){if($path -ne 'root'){foreach($i in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$i)).PhaseGraph.Chunk}};return $g}
function ReadU9([string]$raw,$embedded=$null){$f=Read-Cr2wFile (Join-Path $WorkspaceRoot $raw);if($null -ne $embedded){return $f.EmbeddedFiles[[int]$embedded].Content};return $f.RootChunk}
function EmptyU9 {return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function SliceU9($og,$ids){$g=EmptyU9;foreach($id in $ids){$n=(Get-QuestNode $og ([int]$id)).DeepCopy();ClearB5 $n;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk (Get-QuestNode $og ([int]$id)).PhaseGraph.Chunk};AddNodeB5 $g $n};return $g}
function OwnU9([string]$id,[string]$key){return 'PTFRU9_'+$id+'_'+$key}
function RefU9($n,[string]$depot){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($depot)}
function TowerU9 {return [ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRU7_Support_Request=0;PTFRU7_Support_Issued=0;PTFRU6_Padre_Request=0;PTFRU6_Padre_Issued=0}}
$resources=[ordered]@{};$boots=[Collections.Generic.List[string]]::new();$recipes=[Collections.Generic.List[object]]::new()
B71Parser|Out-Null;$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$inventory=@(B72Inventory $game)
$usedIDs=[Collections.Generic.HashSet[int]]::new();foreach($e in $inventory){[void]$usedIDs.Add([int]$e.id)}
$nativeRoot=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
foreach($id in @($nativeRoot.Data.RootChunk.graph.Data.nodes.Data.id)){[void]$usedIDs.Add([int]$id)}
foreach($pending in @('research/gig_restoration/gig_phone_u9/manifest.json','research/gig_restoration/special_gigs_u9/manifest_additions.json')){
 $pp=Join-Path $WorkspaceRoot $pending;if(Test-Path -LiteralPath $pp){$pm=Get-Content -LiteralPath $pp -Raw|ConvertFrom-Json
  if($pm.PSObject.Properties.Name -contains 'boots'){foreach($b in $pm.boots){[void]$usedIDs.Add([int](B72Id ($b+':1')))}}
  if($pm.PSObject.Properties.Name -contains 'depot'){[void]$usedIDs.Add([int](B72Id ($pm.depot+':1')))}
 }
}
function SaveU9($g,[string]$name){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $depot='towercontinued\native_gigs_u9\'+$name+'.questphase';$alias=0
 while($usedIDs.Contains([int](B72Id ($depot+':1')))){$alias+=1;if($alias -gt 100){throw 'Unable to allocate collision-free phase name'};$depot='towercontinued\native_gigs_u9\'+$name+'_alias'+$alias+'.questphase'}
 [void]$usedIDs.Add([int](B72Id ($depot+':1')));$raw=Join-Path $source $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw)|Out-Null;Write-Cr2wFile $file $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit ($name+'.json'))
 $resources[$depot]=R5Hash $raw;$boots.Add($depot);return $depot
}
foreach($job in $plan.jobs){
 $id=$job.id;$p=$job.parent;$root=ReadU9 $p.raw $p.binding.binding.embedded_index;$og=GraphU9 $root.Graph.Chunk $p.binding.graph
 $ids=@(@($p.ancestors|ForEach-Object id)+@($p.child.id)|Sort-Object -Unique);$g=SliceU9 $og $ids
 (Get-QuestNode $g $p.input_node).SocketName='In1';RefU9 (Get-QuestNode $g $p.child.id) $job.resources[0].depot
 foreach($edit in $p.edits){$eg=GraphU9 $g $edit.graph;$remove=$edit.remove;$ee=@(EdgesB5 $eg|ForEach-Object {$_}|Where-Object {-not ($_[0] -eq $remove[0] -and $_[1] -eq $remove[1] -and $_[2] -eq $remove[2] -and $_[3] -eq $remove[3])});if($null -ne $edit.add){$ee+=,@($edit.add)};RebuildB5 $eg $ee}
 if($job.PSObject.Properties.Name -contains 'shared_gate' -and $null -ne $job.shared_gate){
  if($job.shared_gate -ne 'ep1_tier3'){throw 'Unknown shared native gate'}
  $gate=Get-QuestNode $g 9;$ng=EmptyU9
  foreach($n in @((New-InputNode 0 'In1'),(PauseB5 2 (AllB5 ([ordered]@{PTFRU9_EP1Tier3_Ready=1}))))){AddNodeB5 $ng $n}
  $output=(Get-QuestNode $gate.PhaseGraph.Chunk 1).DeepCopy();ClearB5 $output;AddNodeB5 $ng $output
  RebuildB5 $ng @(@(0,'Out',2,'In'),@(2,'Out',1,'In'));Set-RedHandleProperty $gate PhaseGraph $ng
 }
 $guard=TowerU9;$guard[(OwnU9 $id 'Request')]=1;$guard[(OwnU9 $id 'Permit')]=1;$guard[(OwnU9 $id 'ParentEntered')]=0;$guard[(OwnU9 $id 'Fault')]=0
 if($job.retaliation_dependency){$guard['PTFRU9_Retaliation_Issued']=1;$guard['PTFRU9_Retaliation_Fault']=0;$guard['PTFRU9_Retaliation_'+$job.retaliation_gang+'_Issued']=1;$guard['PTFRU9_Retaliation_'+$job.retaliation_gang+'_Fault']=0}
 foreach($f in @($job.start)+@($job.terminal)){$guard[$f]=0}
 foreach($tag in $job.legacy_tags){foreach($key in @('Queued','Request','Started','CounterClaim','CounterAck','RewardClaim','AccountClaim')){$guard[$tag+'_'+$key]=0}}
 foreach($n in @((New-SetFactNode 65000 (OwnU9 $id 'Ready') 1),(New-SetFactNode 65001 (OwnU9 $id 'Revision') 1),(PauseB5 65002 (AllB5 $guard)),(New-SetFactNode 65003 (OwnU9 $id 'ParentEntered') 1),(New-SetFactNode 65004 (OwnU9 $id 'Started') 1),(New-SetFactNode 65005 (OwnU9 $id 'MainFinished') 1),(New-SetFactNode 65006 (OwnU9 $id 'OwnerFinished') 1))){AddNodeB5 $g $n}
 $edges=@();$mainInputs=@($p.edges|Where-Object {$_[2] -eq $p.child.id}|ForEach-Object {$_[3]}|Sort-Object -Unique)
 $mainInput=if($mainInputs -contains 'STS_started'){'STS_started'}elseif($mainInputs.Count -eq 1){$mainInputs[0]}else{throw ('Multiple main lifecycle inputs require explicit rule: '+$id)}
 foreach($e0 in $p.edges){$e=@($e0);if($e[0] -eq $p.input_node){$e[0]=65003};if($e[2] -eq $p.child.id -and $e[3] -eq $mainInput){$e[2]=65004;$e[3]='In'};$edges+=,$e}
 foreach($e in @(@($p.input_node,'Out',65000,'In'),@(65000,'Out',65001,'In'),@(65001,'Out',65002,'In'),@(65002,'Out',65003,'In'),@(65004,'Out',$p.child.id,$mainInput))){$edges+=,$e}
 $companions=@();if($job.PSObject.Properties.Name -contains 'companions'){$companions=@($job.companions)}
 $cleanupNodes=@();$afterNodes=@();$cn=64000;$companionIDs=@{}
 foreach($c in $companions){
  $key=$c.source_raw+'|'+$c.source_graph+'|'+$c.source_node+'|'+$c.depot
  if(-not $companionIDs.ContainsKey($key)){
   $cr=ReadU9 $c.source_raw;$cg=GraphU9 $cr.Graph.Chunk $c.source_graph;$n=(Get-QuestNode $cg $c.source_node).DeepCopy();$n.Id=[uint16]$cn;ClearB5 $n;RefU9 $n $c.depot;AddNodeB5 $g $n;$companionIDs[$key]=$cn;$cn+=1
  };$nodeID=$companionIDs[$key]
  if($c.kind -in @('parallel_bugfix','parallel_prestate')){$edges+=,@(65003,'Out',$nodeID,$c.input)}
  elseif($c.kind -eq 'cleanup'){$edges+=,@($p.child.id,$c.from_output,$nodeID,$c.input);$cleanupNodes+=,@{id=$nodeID;spec=$c}}
  elseif($c.kind -eq 'after_cleanup'){$afterNodes+=,@{id=$nodeID;spec=$c}}
  else{throw 'Unknown native companion kind'}
 }
 $exposed=@((Get-QuestNode $g $p.child.id).Sockets|ForEach-Object {$_.Chunk.Name.ToString()})
 foreach($port in $job.outputs){if($port -in $exposed -and ($companions.Count -eq 0 -or $port -eq 'Out1')){$edges+=,@($p.child.id,$port,65005,'In')}}
 if($cleanupNodes.Count -eq 0){$edges+=,@(65005,'Out',65006,'In')}else{
  foreach($c in $cleanupNodes){foreach($port in $c.spec.outputs){$edges+=,@($c.id,$port,65006,'In');foreach($a in $afterNodes){if($a.spec.from_output -eq $port){$edges+=,@($c.id,$port,$a.id,$a.spec.input)}}}}
 }
 # No terminating wrapper output: native parallel bugfix/post-gig community
 # owners retain their authored lifetime. Observation never cuts a stock phase.
 RebuildB5 $g $edges
 $compiledGraph='root'
 if($p.binding.graph -ne 'root'){
  $parts=@($p.binding.graph.Substring(5).Split('/'));$prefix='root';$containers=@()
  foreach($part in $parts){$containers+=,@{graph=$prefix;id=[int]$part};$prefix+='/'+$part}
  for($wi=$containers.Count-1;$wi -ge 0;$wi--){$spec=$containers[$wi];$cg=GraphU9 $root.Graph.Chunk $spec.graph;$container=(Get-QuestNode $cg $spec.id).DeepCopy();ClearB5 $container;Set-RedHandleProperty $container PhaseGraph $g
   $outer=EmptyU9;AddNodeB5 $outer (New-InputNode 0 'In1');AddNodeB5 $outer (New-SetFactNode 65000 (OwnU9 $id 'Ready') 1);AddNodeB5 $outer (New-SetFactNode 65001 (OwnU9 $id 'Revision') 1);AddNodeB5 $outer $container
   RebuildB5 $outer @(@(0,'Out',65000,'In'),@(65000,'Out',65001,'In'),@(65001,'Out',$spec.id,'In1'));$g=$outer
  };$compiledGraph=$p.binding.graph
 }
 $depot=SaveU9 $g ($id+'_entry')
 $recipes.Add(@{kind='entry';id=$id;depot=$depot;raw=$p.raw;graph=$p.binding.graph;compiled_graph=$compiledGraph;ids=$ids;edges=$edges;main_input=$mainInput;native=$job.resources[0].depot;companions=$companions})
 Write-Output ('Built original '+$id)
}
foreach($c in $plan.credits){
 $og=GraphU9 (ReadU9 $c.raw).Graph.Chunk $c.graph;$g=SliceU9 $og $c.ids
 $guard=[ordered]@{(OwnU9 $c.id 'Started')=1;(OwnU9 $c.id 'CreditEntered')=0;(OwnU9 $c.id 'CreditDone')=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
 foreach($n in @((PauseB5 65000 (AllB5 $guard)),(New-SetFactNode 65001 (OwnU9 $c.id 'CreditEntered') 1),(New-SetFactNode 65002 (OwnU9 $c.id 'CreditDone') 1))){AddNodeB5 $g $n}
 $edges=@();foreach($e0 in $c.edges){$e=@($e0);if($e[0] -eq 0){$e[0]=65001};$edges+=,$e};$edges+=,@(0,'Out',65000,'In');$edges+=,@(65000,'Out',65001,'In');$edges+=,@($c.end,'Out',65002,'In');RebuildB5 $g $edges
 $depot=SaveU9 $g ($c.id+'_credit');$recipes.Add(@{kind='credit';id=$c.id;depot=$depot;raw=$c.raw;graph=$c.graph;ids=$c.ids;edges=$edges})
}
foreach($t in $plan.tiers){
 $og=(ReadU9 $t.raw).Graph.Chunk;$g=SliceU9 $og $t.ids;$id=$t.region+'_Tier'+$t.threshold
 $guard=[ordered]@{(OwnU9 $t.region 'TierRequest')=1;(OwnU9 $id 'Permit')=1;(OwnU9 $id 'Entered')=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
 foreach($n in @((New-InputNode 65000 'In1'),(PauseB5 65001 (AllB5 $guard)),(New-SetFactNode 65002 (OwnU9 $id 'Entered') 1),(New-SetFactNode 65003 (OwnU9 $id 'Done') 1))){AddNodeB5 $g $n}
 $edges=@($t.edges);$edges+=,@(65000,'Out',65001,'In');$edges+=,@(65001,'Out',65002,'In');$edges+=,@(65002,'Out',$t.start,'In');$edges+=,@($t.end,'Out',65003,'In');RebuildB5 $g $edges
 $depot=SaveU9 $g ($id+'_native');$recipes.Add(@{kind='tier';id=$id;depot=$depot;raw=$t.raw;graph='root';ids=$t.ids;edges=$edges})
}
$mi=@{}
foreach($m in $plan.maps){
 if(-not $mi.ContainsKey($m.id)){$mi[$m.id]=0};$index=$mi[$m.id];$mi[$m.id]+=1
 $og=GraphU9 (ReadU9 $m.raw).Graph.Chunk $m.graph;$g=SliceU9 $og $m.ids
 $guard=[ordered]@{(OwnU9 $m.id 'Started')=1;(OwnU9 $m.id 'MapPermit')=1;(OwnU9 $m.id ('Map'+$index+'Entered'))=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
 AddNodeB5 $g (PauseB5 65000 (AllB5 $guard));AddNodeB5 $g (New-SetFactNode 65001 (OwnU9 $m.id ('Map'+$index+'Entered')) 1)
 $edges=@();foreach($e0 in $m.edges){$e=@($e0);if($e[0] -eq $m.input){$e[0]=65001};$edges+=,$e};$edges+=,@($m.input,'Out',65000,'In');$edges+=,@(65000,'Out',65001,'In');RebuildB5 $g $edges
 $depot=SaveU9 $g ($m.id+'_map'+$index);$recipes.Add(@{kind='map';id=$m.id;index=$index;depot=$depot;raw=$m.raw;graph=$m.graph;ids=$m.ids;edges=$edges;foreign_poi_contraction=$m.foreign_poi_contraction})
}
$collisions=@()
foreach($depot in $boots){$c=B72CollisionCheck $inventory $WorkspaceRoot $depot;if($c.new_id -in $inventory.id){throw ('U9 batch node collision: '+$depot)};$collisions+=@{depot=$depot;node_id=$c.new_id};$inventory+=@{path=$depot;id=$c.new_id;source='U9_batch'}}
$xl=B71Render @($boots);B71Parse $xl|Out-Null;[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_NativeGigsU9.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_NativeGigsU9.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Pack scope mismatch'}
foreach($e in $packed.Files.Values){if(-not $resources.Contains($e.Name)){throw 'Unexpected resource'};$mem=[IO.MemoryStream]::new();try{$e.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne $resources[$e.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}}
$files=@(@{source='build/NativeGigsU9/TowerContinued_NativeGigsU9.archive';relative='archive/pc/mod/TowerContinued_NativeGigsU9.archive';predecessor=$null},@{source='build/NativeGigsU9/TowerContinued_NativeGigsU9.archive.xl';relative='archive/pc/mod/TowerContinued_NativeGigsU9.archive.xl';predecessor=$null})
foreach($name in @('NativeGigsU9.reds','NativeGigDataU9.generated.reds')){$files+=@{source='redscript/PTFR_NativeGigsU9/'+$name;relative='r6/scripts/PTFR_NativeGigsU9/'+$name;predecessor=$null}}
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U9_ENGINE_PENDING';files=$files;recipes=$recipes.ToArray();boots=$boots.ToArray();resources=$resources;source_dir=$source;source_pins=$plan.pins;collisions=$collisions;packed_readback=$true;builder_sha256=R5Hash $PSCommandPath;plan_sha256=R5Hash $planPath;original_gameplay_resources_packed=0;production_auto=$false;final_fixer_reward=$false;coverage=$plan.coverage;warnings=$plan.warnings})
'BUILT_U9_ENGINE_PENDING'
