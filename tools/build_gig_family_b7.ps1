param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/family_b7';$out=Join-Path $WorkspaceRoot 'build/GigFamilyB7';$source=Join-Path $out 'source'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed B7 evidence pinned'}
$plan=Get-Content (Join-Path $audit 'build_plan.json') -Raw|ConvertFrom-Json
foreach($p in $plan.pins.PSObject.Properties){if((Get-FileHash (Join-Path $WorkspaceRoot $p.Name)).Hash -ne $p.Value){throw "Source changed: $($p.Name)"}}
New-Item -ItemType Directory -Force $source|Out-Null
$helperPath=Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1';$helper=Get-Content $helperPath -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};');if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
function ReadRootB7($raw,$embedded){$f=Read-Cr2wFile (Join-Path $WorkspaceRoot $raw);if($null -ne $embedded){return $f.EmbeddedFiles[[int]$embedded].Content};return $f.RootChunk}
function GraphB7($g,$path){if($path -ne 'root'){foreach($i in $path.Substring(5).Split('/')){$g=(Get-QuestNode $g ([int]$i)).PhaseGraph.Chunk}};return $g}
function TowerB7 {return [ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0}}
function WriteRootB7($root,$depot){
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 Write-Cr2wFile $file (Join-Path $source $depot)
 $json=Join-Path (Join-Path $audit 'built') ($depot+'.json');New-Item -ItemType Directory -Force (Split-Path -Parent $json)|Out-Null
 Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) $json
 $script:resources.Add($depot)
}
# Separate claim/ack for each actual native payout or achievement node. Native
# branch selection remains responsible for normal/bonus/failure routing.
function OnceB7($g,$id,$key,$fault){
 $base=30000+$id*6;if($base+4 -gt 65535){throw 'Node ID overflow'}
 foreach($h in $g.Nodes){if([int]$h.Chunk.Id.ToString() -ge $base -and [int]$h.Chunk.Id.ToString() -le $base+4){throw 'Node ID collision'}}
 $edges=@(EdgesB5 $g|ForEach-Object {$_});$old=@($edges|Where-Object {$_[0] -eq $id})
 foreach($n in @((New-ConditionNode $base (AllB5 ([ordered]@{($key+'_Claim')=0;($key+'_Ack')=0;$fault=0}))), (New-SetFactNode ($base+1) ($key+'_Claim') 1),(New-SetFactNode ($base+2) ($key+'_Ack') 1),(New-SetFactNode ($base+3) $fault 1))){AddNodeB5 $g $n}
 foreach($e in $edges){if($e[2] -eq $id -and $e[3] -eq 'In'){$e[2]=$base}}
 $edges=@($edges|Where-Object {$_[0] -ne $id})
 foreach($e in @(@($base,'True',($base+1),'In'),@(($base+1),'Out',$id,'In'),@($id,'Out',($base+2),'In'),@($base,'False',($base+3),'In'))){$edges+=,$e}
 foreach($e in $old){$edges+=,@(($base+2),'Out',$e[2],$e[3])};RebuildB5 $g $edges
}
$prefix='towercontinued\family_b7\';$resources=[Collections.Generic.List[string]]::new();$boots=[Collections.Generic.List[string]]::new()
foreach($job in $plan.jobs){
 $tag=$job.tag;$map=@{};$roots=@{};$jobPrefix=$prefix+$job.id+'\'
 foreach($res in $job.resources){
  $original=ReadRootB7 $res.raw $res.binding.embedded_index;$copy=$original.DeepCopy();RewireB5 $copy.Graph.Chunk $original.Graph.Chunk
  $roots[$res.depot]=$copy;$map[$res.depot]=$jobPrefix+$res.key+'.questphase'
 }
 foreach($root in $roots.Values){
  $queue=[Collections.Generic.Queue[object]]::new();$queue.Enqueue($root.Graph.Chunk)
  while($queue.Count){$g=$queue.Dequeue();foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition'){
   if($null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){$queue.Enqueue($n.PhaseGraph.Chunk)}
   $dep=$n.PhaseResource.DepotPath.ToString();if($null -ne $dep -and $map.ContainsKey($dep)){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($map[$dep])}
  }}}
 }
 foreach($call in $job.calls){
  if($call.incoming.Count -eq 0){continue};if($call.alternative.Count -eq 0){throw 'No authored text route'}
  $g=GraphB7 $roots[$call.depot].Graph.Chunk $call.graph;$edges=@(EdgesB5 $g|ForEach-Object {$_});$result=@()
  foreach($e in $edges){if($e[2] -eq $call.node -and $e[3] -ne 'CutDestination'){foreach($a in $call.alternative){$result+=,@($e[0],$e[1],$a[0],$a[1])}}else{$result+=,$e}}
  RebuildB5 $g $result
 }
 foreach($m in $job.mutations){OnceB7 (GraphB7 $roots[$m.depot].Graph.Chunk $m.graph) $m.node ($tag+'_'+$m.key) ($tag+'_Fault')}
 foreach($res in $job.resources){WriteRootB7 $roots[$res.depot] $map[$res.depot]}
 # Copy only the original one-gig parent prelude: native tiers, POI and outside
 # triggers. Never restart the district/fixer root or copy sibling branches.
 $p=$job.parent;$parent=ReadRootB7 $p.raw $p.binding.binding.embedded_index;$pg=GraphB7 $parent.Graph.Chunk $p.binding.graph
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $root Graph $g
 foreach($spec in @($p.ancestors)+@($p.child)){
  $n=(Get-QuestNode $pg $spec.id).DeepCopy();ClearB5 $n
  if($spec.id -eq $p.input_node){$n.SocketName='In1'}
  if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk (Get-QuestNode $pg $spec.id).PhaseGraph.Chunk}
  if($spec.id -eq $p.child.id){$dep=$n.PhaseResource.DepotPath.ToString();$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($map[$dep])}
  AddNodeB5 $g $n
 }
 foreach($edit in $p.edits){
  $eg=GraphB7 $g $edit.graph;$ee=@(EdgesB5 $eg|ForEach-Object {$_});$remove=$edit.remove
  $ee=@($ee|Where-Object {-not ($_[0] -eq $remove[0] -and $_[1] -eq $remove[1] -and $_[2] -eq $remove[2] -and $_[3] -eq $remove[3])})
  if($null -ne $edit.add){$ee+=,@($edit.add)};RebuildB5 $eg $ee
 }
 $guard=TowerB7;$guard[$tag+'_Request']=1;$guard[$tag+'_Permit']=1;$guard[$tag+'_Started']=0;$guard[$tag+'_Fault']=0
 foreach($fact in @($job.start)+@($job.terminal)){$guard[$fact]=0}
 foreach($n in @((New-SetFactNode 65000 ($tag+'_Ready') 1),(PauseB5 65001 (AllB5 $guard)),(New-ConditionNode 65002 (AllB5 $guard)),(New-SetFactNode 65003 ($tag+'_Started') 1),(New-SetFactNode 65004 ($tag+'_OwnerFinished') 1),(New-OutputNode 65005 'Out1'),(New-SetFactNode 65006 ($tag+'_Revision') 1))){AddNodeB5 $g $n}
 $edges=@();foreach($e0 in $p.edges){$e=@($e0);if($e[0] -eq $p.input_node){$e[0]=65001};if($e[2] -eq $p.child.id){$e[2]=65002;$e[3]='In'};$edges+=,$e}
 foreach($e in @(@($p.input_node,'Out',65000,'In'),@(65000,'Out',65006,'In'),@(65006,'Out',65001,'In'),@(65002,'True',65003,'In'),@(65003,'Out',$p.child.id,$p.child_input),@(65004,'Out',65005,'In'))){$edges+=,$e}
 foreach($port in $job.outputs){$edges+=,@($p.child.id,$port,65004,'In')}
 RebuildB5 $g $edges;$boot=$jobPrefix+'boot.questphase';WriteRootB7 $root $boot;$boots.Add($boot)
 Write-Output ('Built '+$job.id)
}
# Independently earned native tier fragments; no welcome/counter/final-reward
# owners. Original delays/content locks and authored messages are retained.
foreach($tier in $plan.tiers){
 $original=ReadRootB7 $tier.raw $null;$og=$original.Graph.Chunk;$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $root Graph $g
 $tag='PTFRB7_'+$tier.region+'_Tier'+$tier.threshold
 foreach($spec in $tier.nodes){$n=(Get-QuestNode $og $spec.id).DeepCopy();ClearB5 $n;AddNodeB5 $g $n}
 $guard=TowerB7;$guard['PTFRB7_'+$tier.region+'_TierRequest']=1;$guard[$tag+'_Claim']=0;$guard[$tag+'_Ack']=0
 foreach($n in @((New-InputNode 65000 'In1'),(PauseB5 65001 (AllB5 $guard)),(New-SetFactNode 65002 ($tag+'_Claim') 1),(New-SetFactNode 65003 ($tag+'_Ack') 1))){AddNodeB5 $g $n}
 $edges=@($tier.edges);$edges+=,@(65000,'Out',65001,'In');$edges+=,@(65001,'Out',65002,'In');$edges+=,@(65002,'Out',$tier.start,'In')
 foreach($target in $tier.targets){if(@($edges|Where-Object {$_[0] -eq $target}).Count -eq 0){$edges+=,@($target,'Out',65003,'In')}}
 foreach($spec in $tier.nodes){
  $id=$spec.id;$n=Get-QuestNode $g $id
  if($spec.'$type' -eq 'questFactsDBManagerNodeDefinition'){
   $n.Type.Chunk.SetExactValue=[WolvenKit.RED4.Types.CBool]::op_Implicit($true)
   $c=New-FactCondition $n.Type.Chunk.FactName.ToString() 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
  }elseif($spec.'$type' -eq 'questPhoneManagerNodeDefinition'){
   $v=[WolvenKit.RED4.Types.questJournalEntry_ConditionType]::new();$v.Path=$n.Type.Chunk.Msg.DeepCopy();$v.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryUserState]::Inactive
   $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $v
  }else{continue}
  $gate=30000+$id;AddNodeB5 $g (New-ConditionNode $gate $c);$old=@($edges|Where-Object {$_[0] -eq $id})
  foreach($e in $edges){if($e[2] -eq $id){$e[2]=$gate}};$edges+=,@($gate,'True',$id,'In')
  foreach($e in $old){$edges+=,@($gate,'False',$e[2],$e[3])}
 }
 RebuildB5 $g $edges;$depot=$prefix+'tiers\'+$tier.region+'_'+$tier.threshold+'.questphase';WriteRootB7 $root $depot;$boots.Add($depot)
}
$xl=@('quest:','  phases:');foreach($boot in $boots){$xl+=@('    - path: '+$boot,'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')}
[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_FamilyB7.archive.xl'),(($xl -join "`n")+"`n"),[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_FamilyB7.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope changed'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Packed mismatch'}}finally{$m.Dispose()}}
$result=[ordered]@{status='BUILT_B7_NATIVE_FRESH_FAMILY_LIVE_PENDING';owners=$plan.jobs.Count;archive_sha256=(Get-FileHash $archive).Hash;plan_sha256=(Get-FileHash (Join-Path $audit 'build_plan.json')).Hash;helper_sha256=(Get-FileHash $helperPath).Hash;resources=$resources.ToArray();boots=$boots.ToArray();packed_readback=$true;vanilla_replacements=@();completed_replay=$false}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));$result.status
