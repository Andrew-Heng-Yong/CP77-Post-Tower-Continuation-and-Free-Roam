param([string]$Revision='base_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^base_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$copies=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function ReadPinned($p){Pin $p;Pin ($p.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $p)}
foreach($p in @('prealpha/sidejobs_s24/base/build.ps1','prealpha/sidejobs_s24/base/prepare.py','prealpha/sidejobs_s24/base/contract03.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1')){Pin $p}
function CopyNode($g,$source,$id,$newid=-1){
 $o=Get-QuestNode $source $id;$n=$o.DeepCopy();ClearB5 $n
 if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk}
 if($newid -ge 0){$n.Id=[uint16]$newid};AddNodeB5 $g $n
}
function SaveGraph($g,$depot,$label){
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$r.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $r Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r;$p=Join-Path (Join-Path $out 'source') $depot
 Write-Cr2wFile $f $p;Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $out ('readback/'+$label+'.json'))
 $resources[$depot]=(Get-FileHash -LiteralPath $p).Hash;$script:boots+=,$depot
}
function JournalCondition($j){
 if(@($j.states).Count -ne 1 -or [int]$j.states[0] -ne 1){throw 'Fresh only'}
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$j.path;$p.ClassName=$j.class;$p.FileEntryIndex=$(if($j.path.StartsWith('contacts/')){1}else{2})
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$contract=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract03.json') -Raw|ConvertFrom-Json
foreach($p in $contract.source_pins.PSObject.Properties){Pin $p.Name;if($pins[$p.Name] -cne $p.Value){throw ('Contract source changed: '+$p.Name)}}
function Guard($s){
 $p=[ordered]@{};foreach($k in $common.Keys){$p[$k]=$common[$k]};foreach($f in $s.facts_equal.PSObject.Properties){$p[$f.Name]=[int]$f.Value}
 $p[$s.tag+'_Permit']=1;$p[$s.tag+'_Issued']=0;$p[$s.tag+'_Finished']=0;$p[$s.tag+'_Fault']=0
 $c=AllB5 $p
 foreach($f in $s.fact_ranges.PSObject.Properties){
  Add-RedHandle $c.Conditions (New-FactCondition $f.Name ([int]$f.Value.min) ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual))
  Add-RedHandle $c.Conditions (New-FactCondition $f.Name ([int]$f.Value.max) ([WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual))
 }
 foreach($j in $s.journals){Add-RedHandle $c.Conditions (JournalCondition $j)};return $c
}
function Dependency($s){$p=[ordered]@{};foreach($contact in $s.phone_dependencies){$p['PTFRS24_PHONE_'+$contact+'_Issued']=1};if(!$p.Count){$p['PTFRPA2_Finished']=1};return AllB5 $p}
$parentSource='research/sidejobs_s2/sacrum_audit/native_01/raw/base/quest/minor_quests/minorquests.questphase'
$parent=(ReadPinned $parentSource).RootChunk.Graph.Chunk
foreach($s in $contract.owners){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new();$edges=@()
 foreach($id in $s.parent_nodes){CopyNode $g $parent ([int]$id);$copies+=,@{depot=$s.depot;source=$parentSource;source_graph='root';source_id=[int]$id;target_id=[int]$id}}
 foreach($e in $s.parent_edges){$edges+=,@([int]$e[0],[string]$e[1],[int]$e[2],[string]$e[3])}
 $child=Get-QuestNode $g ([int]$s.parent_node)
 if(@($child.Sockets|Where-Object {$_.Chunk.Name.ToString() -eq 'Out1'}).Count -eq 0){[void](New-QuestSocket $child 'Out1' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))}
 foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 ($s.tag+'_Ready') 1),(PauseB5 1002 (Guard $s)),(PauseB5 1003 (Dependency $s)),(New-ConditionNode 1004 (Guard $s)),(New-SetFactNode 1005 ($s.tag+'_Issued') 1),(New-SetFactNode 1006 ($s.tag+'_Entered') 1),(New-SetFactNode 1007 ($s.tag+'_Finished') 1))){AddNodeB5 $g $n}
 $edges+=,@(1000,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In');$edges+=,@(1002,'Out',1003,'In');$edges+=,@(1003,'Out',[int]$s.parent_start,'In')
 $edges+=,@(1004,'False',1002,'In');$edges+=,@(1004,'True',1005,'In');$edges+=,@(1005,'Out',1006,'In')
 if($null -ne $s.contact_copy){
  $cc=$s.contact_copy;$cg=(ReadPinned $cc.source).RootChunk.Graph.Chunk
  foreach($part in ($cc.graph -split '/'|Select-Object -Skip 1)){$cg=(Get-QuestNode $cg ([int]$part)).PhaseGraph.Chunk}
  CopyNode $g $cg ([int]$cc.id) 1010
  $copies+=,@{depot=$s.depot;source=$cc.source;source_graph=$cc.graph;source_id=[int]$cc.id;target_id=1010}
  $edges+=,@(1006,'Out',1010,'In');$edges+=,@(1010,'Out',[int]$s.issue_target,$(if($s.key -eq 'MQ015'){'In'}else{'In1'}))
 }else{$edges+=,@(1006,'Out',[int]$s.issue_target,'In1')}
 $edges+=,@([int]$s.parent_node,'Out1',1007,'In')
 RebuildB5 $g $edges;SaveGraph $g $s.depot $s.key.ToLower()
}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw 'Pinned source changed during build'}}
$manifest=[ordered]@{schema=1;status='BUILT_NOT_INSTALLED';revision=$Revision;resources=$resources;boots=$boots;source_pins=$pins;native_copies=$copies;transforms=@();mod_overrides=@();contract='prealpha/sidejobs_s24/base/contract03.json';common=$common;live='NOT_TESTED'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$manifest.status;resources=$resources.Count;boots=$boots.Count;manifest=(Join-Path $out 'build.json')}|ConvertTo-Json
