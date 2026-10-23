param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b5';$out=Join-Path $WorkspaceRoot 'build\FreshGigsB5';$source=Join-Path $out 'source_r1'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed evidence pinned'}
$review=Get-Content (Join-Path $audit 'source_review.json') -Raw|ConvertFrom-Json
foreach($p in $review.pins.PSObject.Properties){if((Get-FileHash (Join-Path $WorkspaceRoot $p.Name)).Hash -ne $p.Value){throw 'Changed source audit'}}
New-Item -ItemType Directory -Force $source|Out-Null
$prefix='towercontinued\fresh_b5\'
function ClearB5($n){foreach($s in $n.Sockets){$s.Chunk.Connections.Clear()}}
function LinkB5($g,$f,$s,$t,$d='In'){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $g $f) $s) (Get-QuestSocket (Get-QuestNode $g $t) $d))}
function EdgesB5($g){
 $owners=@{};foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)]=[int]$h.Chunk.Id.ToString()}}
 $rows=[Collections.Generic.List[object]]::new()
 foreach($h in $g.Nodes){foreach($s in $h.Chunk.Sockets){foreach($c in $s.Chunk.Connections){if([object]::ReferenceEquals($c.Chunk.Source.Chunk,$s.Chunk)){$rows.Add(@($owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($s.Chunk)],$s.Chunk.Name.ToString(),$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Chunk.Destination.Chunk)],$c.Chunk.Destination.Chunk.Name.ToString()))}}}}
 return ,$rows.ToArray()
}
function RebuildB5($g,$edges){foreach($h in $g.Nodes){ClearB5 $h.Chunk};foreach($e in $edges){LinkB5 $g $e[0] $e[1] $e[2] $e[3]}}
function RewireB5($g,$original){
 RebuildB5 $g @(EdgesB5 $original|ForEach-Object {$_})
 foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk (Get-QuestNode $original ([int]$n.Id.ToString())).PhaseGraph.Chunk}}
}
function AllB5($pairs){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND;foreach($k in $pairs.Keys){Add-RedHandle $c.Conditions (New-FactCondition $k $pairs[$k] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))};return $c}
function EqB5($a,$b){$v=[WolvenKit.RED4.Types.questVarVsVarComparison_ConditionType]::new();$v.FactName1=$a;$v.FactName2=$b;$v.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal;$c=[WolvenKit.RED4.Types.questFactsDBCondition]::new();Set-RedHandleProperty $c Type $v;return $c}
function AddNodeB5($g,$n){Add-RedHandle $g.Nodes $n}
function NestedB5($g,$ids){foreach($id in $ids){$g=(Get-QuestNode $g $id).PhaseGraph.Chunk};return $g}
$pauseTemplate=(Get-QuestNode (Read-Cr2wFile (Join-Path $WorkspaceRoot 'research\q307_extracted\raw\base\quest\cyberpunk2077.questphase')).RootChunk.Graph.Chunk 106)
function PauseB5($id,$condition){$n=$pauseTemplate.DeepCopy();$n.Id=[uint16]$id;ClearB5 $n;Set-RedHandleProperty $n Condition $condition;return $n}
function RedirectB5($g,$from,$socket,$to,$dest){$e=@(EdgesB5 $g|ForEach-Object {$_});foreach($x in $e){if($x[2] -eq $from -and $x[3] -eq $socket){$x[2]=$to;$x[3]=$dest}};RebuildB5 $g $e}
function RewardB5($g,$id,$tag){
 $base=4000+$id*4;$edges=@(EdgesB5 $g|ForEach-Object {$_});$old=@($edges|Where-Object {$_[0] -eq $id})
 foreach($n in @((New-ConditionNode $base (AllB5 ([ordered]@{($tag+'_RewardClaim')=0;($tag+'_RewardAck')=0;($tag+'_Fault')=0}))), (New-SetFactNode ($base+1) ($tag+'_RewardClaim') 1),(New-SetFactNode ($base+2) ($tag+'_RewardAck') 1),(New-SetFactNode ($base+3) ($tag+'_Fault') 1))){AddNodeB5 $g $n}
 foreach($e in $edges){if($e[2] -eq $id){$e[2]=$base}}
 $edges=@($edges|Where-Object {$_[0] -ne $id});$edges+=,@($base,'True',($base+1),'In');$edges+=,@(($base+1),'Out',$id,'In');$edges+=,@($id,'Out',($base+2),'In');$edges+=,@($base,'False',($base+3),'In')
 foreach($e in $old){$edges+=,@(($base+2),'Out',$e[2],$e[3])};RebuildB5 $g $edges
}
function AccountB5($g,$id,$tag){
 $edges=@(EdgesB5 $g|ForEach-Object {$_});$old=@($edges|Where-Object {$_[0] -eq $id})
 $guard=AllB5 ([ordered]@{($tag+'_AccountClaim')=0;($tag+'_AccountAck')=0;($tag+'_Fault')=0})
 Add-RedHandle $guard.Conditions (EqB5 ($tag+'_CountBase') 'wbr_sts_counter');Add-RedHandle $guard.Conditions (EqB5 ($tag+'_AchBase') 'wbr_achievement')
 foreach($n in @((New-SetFactNode 6000 ($tag+'_AccountRequest') 1),(PauseB5 6001 (New-FactCondition ($tag+'_AccountReady') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))), (New-ConditionNode 6002 $guard),(New-SetFactNode 6003 ($tag+'_AccountClaim') 1),(New-SetFactNode 6004 ($tag+'_AccountAck') 1),(New-SetFactNode 6005 ($tag+'_Fault') 1))){AddNodeB5 $g $n}
 foreach($e in $edges){if($e[2] -eq $id){$e[2]=6000}}
 $edges=@($edges|Where-Object {$_[0] -ne $id})
 foreach($e in @(@(6000,'Out',6001,'In'),@(6001,'Out',6002,'In'),@(6002,'True',6003,'In'),@(6003,'Out',$id,'In'),@($id,'Out',6004,'In'),@(6002,'False',6005,'In'))){$edges+=,$e}
 foreach($e in $old){$edges+=,@(6004,'Out',$e[2],$e[3])};RebuildB5 $g $edges
}
$allRoots=@{};$resourceNames=@();$jobs=@()
foreach($job in $review.jobs){
 $key=if($job.id -eq 'sts_wbr_hil_07'){'h7'}else{'h1'};$tag='PTFRB5_'+$key.ToUpper()
 $roots=@{};$depotMap=@{}
 foreach($res in $job.resources){
  $name=if($res.prefabs.Count -gt 0){'native'}elseif($res.depot -match 'gameplay'){'gpl'}else{'ow'}
  $file=Read-Cr2wFile (Join-Path $WorkspaceRoot $res.raw);$roots[$name]=$file.RootChunk.DeepCopy();RewireB5 $roots[$name].Graph.Chunk $file.RootChunk.Graph.Chunk
  $depotMap[$res.depot]=$prefix+$key+'_'+$name+'.questphase'
 }
 foreach($root in $roots.Values){
  $pending=[Collections.Generic.Queue[object]]::new();$pending.Enqueue($root.Graph.Chunk)
  while($pending.Count){$g=$pending.Dequeue();foreach($h in $g.Nodes){$n=$h.Chunk;if($n.GetType().Name -eq 'questPhaseNodeDefinition'){
   if($null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){$pending.Enqueue($n.PhaseGraph.Chunk)}
   $dep=$n.PhaseResource.DepotPath.ToString();if($null -ne $dep -and $depotMap.ContainsKey($dep)){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($depotMap[$dep])}
  }}}
 }
 if($key -eq 'h7'){
  $play=NestedB5 $roots.ow.Graph.Chunk @(4);RedirectB5 $play 200 'Start1' 188 'Active'
  $cleanup=NestedB5 $roots.ow.Graph.Chunk @(5);RedirectB5 $cleanup 11 'Start1' 42 'Active'
  RewardB5 $cleanup 12 $tag;AccountB5 $cleanup 4 $tag
 }else{
  $play=NestedB5 $roots.ow.Graph.Chunk @(7);RedirectB5 $play 155 'Start 0' 145 'Active'
  $cleanup=NestedB5 $roots.ow.Graph.Chunk @(6);RedirectB5 $cleanup 39 'Start 0' 54 'In'
  RewardB5 $cleanup 14 $tag;RewardB5 $cleanup 16 $tag;AccountB5 $cleanup 29 $tag
 }
 # Native input/output, initial spawning, devices, item hand-in, scene choices,
 # main outcomes and departure/time waits remain native. Only shared calls use
 # their authored text alternatives and payout/accounting acquire an owned guard.
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $root Graph $g
 $child=(Get-QuestNode $roots.native.Graph.Chunk $(if($key -eq 'h7'){11}else{15})).DeepCopy();$child.Id=[uint16]7;ClearB5 $child
 $child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($prefix+$key+'_native.questphase')
 $guard=AllB5 ([ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;($tag+'_Request')=1;($tag+'_Started')=0;($tag+'_Fault')=0;($tag+'_RewardClaim')=0;($tag+'_AccountClaim')=0;('hil_'+$(if($key -eq 'h7'){'07'}else{'01'})+'_start')=0;('hil_'+$(if($key -eq 'h7'){'07'}else{'01'})+'_finished')=0})
 foreach($n in @((New-InputNode 0 'In1'),(New-OutputNode 1 'Out1'),(New-SetFactNode 2 ($tag+'_Ready') 1),(New-SetFactNode 3 ($tag+'_Revision') 1),(PauseB5 4 $guard),(New-SetFactNode 5 ($tag+'_Started') 1),(New-SetFactNode 6 ($tag+'_OwnerFinished') 1),$child)){AddNodeB5 $g $n}
 RebuildB5 $g @(@(0,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'Out',5,'In'),@(5,'Out',7,'In1'),@(7,'Out1',6,'In'),@(6,'Out',1,'In'))
 $roots.boot=$root
 foreach($name in @('native','ow','gpl','boot')){$resourceNames+=,($key+'_'+$name);$allRoots[$key+'_'+$name]=$roots[$name]}
 $jobs+=,[ordered]@{id=$job.id;key=$key;tag=$tag;native_sources=$job.resources.raw;fresh_only=$true;manual_journal_paths=@('points_of_interest/street_stories/'+$job.id)}
}
# Separate Wakako earned-tier fragment. Never restart native completed/failure
# counter waiters, welcome/default scenes, NCPD tiers or final fixer rewards.
$fixer=Read-Cr2wFile (Join-Path $audit 'sources\raw\base\open_world\fixers\wakako\phases\wakako.questphase');$fg=$fixer.RootChunk.Graph.Chunk
$tier=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$tg=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $tier Graph $tg
AddNodeB5 $tg (New-InputNode 0 'In1');AddNodeB5 $tg (New-SetFactNode 99 'PTFRB5_TierReady' 1);$edges=@();$edges+=,@(0,'Out',99,'In');$specs=@(@(2,72,88,89,90,91,100,76,77),@(5,81,92,93,94,95,101,64,67),@(7,82,96,97,98,99,102,65,68),@(8,83,0,0,0,0,0,66,69))
foreach($spec in $specs){
 $threshold=$spec[0];$base=$threshold*100;$own='PTFRB5_Tier'+$threshold
 $condition=AllB5 ([ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRB5_TierRequest=1;($own+'_Claim')=0;($own+'_Ack')=0})
 Add-RedHandle $condition.Conditions (Get-QuestNode $fg $spec[1]).Condition.Chunk.DeepCopy()
 if($threshold -eq 8){Add-RedHandle $condition.Conditions (Get-QuestNode $fg 107).Condition.Chunk.DeepCopy()}
 AddNodeB5 $tg (PauseB5 $base $condition);AddNodeB5 $tg (New-SetFactNode ($base+1) ($own+'_Claim') 1)
 $edges+=,@(99,'Out',$base,'In');$edges+=,@($base,'Out',($base+1),'In');$last=$base+1
 if($threshold -ne 8){
  for($i=2;$i -le 5;$i++){$n=(Get-QuestNode $fg $spec[$i]).DeepCopy();$n.Id=[uint16]($base+$i);ClearB5 $n;AddNodeB5 $tg $n;$edges+=,@($last,'Out',($base+$i),'In');$last=$base+$i}
  $msg=(Get-QuestNode $fg $spec[6]).DeepCopy();$msg.Id=[uint16]($base+6);ClearB5 $msg;AddNodeB5 $tg $msg
  $var=[WolvenKit.RED4.Types.questJournalEntry_ConditionType]::new();$var.Path=$msg.Type.Chunk.Msg.DeepCopy();$var.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryUserState]::Inactive
  $jc=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $jc Type $var
  AddNodeB5 $tg (New-ConditionNode ($base+7) $jc);AddNodeB5 $tg (New-SetFactNode ($base+8) ($own+'_MessageChecked') 1)
  foreach($e in @(@($last,'Out',($base+7),'In'),@(($base+7),'True',($base+6),'In'),@(($base+6),'Out',($base+8),'In'),@(($base+7),'False',($base+8),'In'))){$edges+=,$e};$last=$base+8
 }
 for($i=7;$i -le 8;$i++){
  $n=(Get-QuestNode $fg $spec[$i]).DeepCopy();$id=$base+10+($i-7)*2;$n.Id=[uint16]($id+1);ClearB5 $n;$n.Type.Chunk.SetExactValue=[WolvenKit.RED4.Types.CBool]::op_Implicit($true);AddNodeB5 $tg $n
  AddNodeB5 $tg (New-ConditionNode $id (New-FactCondition $n.Type.Chunk.FactName.ToString() 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)))
  $next=$base+12+($i-7)*2
  foreach($e in @(@($last,'Out',$id,'In'),@($id,'True',($id+1),'In'),@($id,'False',$next,'In'),@(($id+1),'Out',$next,'In'))){$edges+=,$e};$last=-1
  if($i -eq 7){$last=$base+11}
 }
 # The first setter already points to the second condition; do not also wire it
 # twice when assembling the second setter above.
 $edges=@($edges|Where-Object {-not ($_[0] -eq ($base+11) -and $_[2] -eq ($base+12))});$edges+=,@(($base+11),'Out',($base+12),'In')
 AddNodeB5 $tg (New-SetFactNode ($base+14) ($own+'_Ack') 1)
}
RebuildB5 $tg $edges;$allRoots.tiers=$tier;$resourceNames+=,'tiers'
$resources=@()
foreach($name in $resourceNames){$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$allRoots[$name];$depot=$prefix+$name+'.questphase';$resources+=,$depot;Write-Cr2wFile $file (Join-Path $source $depot);Export-Cr2wJson (Read-Cr2wFile (Join-Path $source $depot)) (Join-Path $audit ($name+'.questphase.json'))}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_FreshB5.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$entry.Extract($m);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray())) -ne (Get-FileHash (Join-Path $source $entry.Name)).Hash){throw 'Packed mismatch'}}finally{$m.Dispose()}}
$result=[ordered]@{status='BUILT_B5_TWO_NATIVE_FRESH_OWNERS_LIVE_PENDING';archive_sha256=(Get-FileHash $archive).Hash;source_review_sha256=(Get-FileHash (Join-Path $audit 'source_review.json')).Hash;resources=$resources;jobs=$jobs;tier_thresholds=@(2,5,7,8);packed_readback=$true;vanilla_replacements=@();completed_replay=$false;game_writes=0;direct_save_writes=0}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($result|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false));[pscustomobject]$result|Select-Object status,archive_sha256,packed_readback|ConvertTo-Json
