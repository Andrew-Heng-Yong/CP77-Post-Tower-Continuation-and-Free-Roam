Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$WorkspaceRoot=$W
$helper=Get-Content (Join-Path $W 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$O=Join-Path $PSScriptRoot 'candidate_01';if(Test-Path $O){throw 'Fresh candidate required'}
$B=Join-Path $W 'prealpha/lizzies_lr2/candidate_01'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$inventory=Get-Content (Join-Path $W 'diagnostics/phone_restoration_preparation_20261029_01/current_01/inventory.json') -Raw|ConvertFrom-Json -Depth 100
$cases=@(Get-Content (Join-Path $W 'diagnostics/phone_restoration_preparation_20261029_01/cases_02.json') -Raw|ConvertFrom-Json -Depth 100)
foreach($f in Get-ChildItem (Join-Path $B 'package') -Recurse -File){$rel=[IO.Path]::GetRelativePath((Join-Path $B 'package'),$f.FullName);if((Get-FileHash $f.FullName).Hash -cne (Get-FileHash (Join-Path $game $rel)).Hash){throw "Baseline drift $rel"}}
New-Item -ItemType Directory $O|Out-Null
Copy-Item (Join-Path $B 'archive_source') (Join-Path $O 'archive_source') -Recurse
Copy-Item (Join-Path $B 'package') (Join-Path $O 'package') -Recurse
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$contracts=@()
function Native([string]$depot){$r=@($inventory.resources|Where-Object depot -CEQ $depot);if($r.Count -ne 1 -or (Get-FileHash $r[0].raw).Hash -cne $r[0].sha256){throw "Native pin $depot"};$pins[$depot]=$r[0].sha256;return (Read-Cr2wFile $r[0].raw).RootChunk}
function CopyNode($g,$src,$id,$newid){$s=Get-QuestNode $src $id;$n=$s.DeepCopy();ClearB5 $n;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $s.PhaseGraph.Chunk};$n.Id=[uint16]$newid;AddNodeB5 $g $n;return $n}
function Save($root,$depot){$p=Join-Path (Join-Path $O 'archive_source') $depot;$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root;Write-Cr2wFile $f $p;Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $O ($depot.Replace('\','_')+'.json'));$resources[$depot]=(Get-FileHash $p).Hash}
function Any($conditions){$c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR;foreach($v in $conditions){Add-RedHandle $c.Conditions $v};return $c}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;holo_setup_active=0;holo_setup_started=0;holo_reset=0;holo_force_reset=0;holo_reset_soft=0}
$cleanupDepot='towercontinued\gig_phone_u9\fixer_cleanup.questphase'
$old=(Read-Cr2wFile (Join-Path (Join-Path $O 'archive_source') $cleanupDepot)).RootChunk
$cg=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($h in $old.Graph.Chunk.Nodes){[void](CopyNode $cg $old.Graph.Chunk ([int]$h.Chunk.Id.ToString()) ([int]$h.Chunk.Id.ToString()))}
$ce=@(EdgesB5 $old.Graph.Chunk|ForEach-Object {$_});$tail=1400
foreach($e in $ce){if($e[2] -eq 6 -and $e[3] -eq 'In2'){$e[2]=$tail;$e[3]='In'}}
for($i=0;$i -lt $cases.Count;$i++){
 $case=$cases[$i];$contact=$case.contact;$tag='PTFRPH1_'+$contact
 $init=(Native $case.native_initializer_bindings.depot).Graph.Chunk
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 $controller=CopyNode $g $init $case.native_initializer_bindings.node 10
 $input=@($controller.Sockets|Where-Object {$_.Chunk.Type.ToString() -eq 'Input'}|ForEach-Object {$_.Chunk.Name.ToString()});if($input.Count -ne 1){throw 'Initializer input ambiguous'}
 $guard=AllB5 $common;Add-RedHandle $guard.Conditions (New-FactCondition ($tag+'_Issued') 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 if($null -ne $case.job){
  $p='PTFRU9_'+$case.job+'_'
  $fresh=AllB5 ([ordered]@{($p+'Permit')=1;($p+'Started')=0;($p+'Fault')=0})
  $active=AllB5 ([ordered]@{($p+'ParentEntered')=1;($p+'Started')=1;($p+'MainFinished')=0;($p+'OwnerFinished')=0;($p+'Fault')=0})
  Add-RedHandle $guard.Conditions (Any @($fresh,$active))
 }else{
  $site=if($contact -eq 'nix'){'NIX'}else{'VIKTOR'}
  Add-RedHandle $guard.Conditions (AllB5 ([ordered]@{('PTFRB0S4'+$site+'_Ready')=1;('PTFRB0S4'+$site+'_Enabled')=1;('PTFRB0S4'+$site+'_OwnerActive')=1;('PTFRB0S4'+$site+'_Excluded')=0}))
 }
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($tag+'_Ready') 1),(PauseB5 2 $guard),(New-ConditionNode 3 $guard),(New-SetFactNode 4 ($tag+'_Issued') 1))){AddNodeB5 $g $n}
 RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',10,$input[0]))
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g
 $depot='towercontinued\phone_support_ph1\'+$contact+'.questphase';Save $r $depot;$boots+=,$depot
 # Contact cleanup joins the existing reset chain, never a competing reset loop.
 $native=(Native $case.cleanup_integration.source).Graph.Chunk;$phaseId=if($i -lt 2){$case.cleanup_integration.inline_phase_node}else{$case.native_cleanup_bindings.node}
 $ne=@(EdgesB5 $native|ForEach-Object {$_});$incoming=@($ne|Where-Object {$_[2] -eq $phaseId -and $_[1] -eq 'True'})
 if($incoming.Count -ne 1){throw 'Cleanup condition ambiguous'}
 $id=1400+($i*3);$next=if($i -eq 5){6}else{$id+3}
 AddNodeB5 $cg (New-ConditionNode $id (AllB5 ([ordered]@{($tag+'_Issued')=1})))
 [void](CopyNode $cg $native $incoming[0][0] ($id+1));$cp=CopyNode $cg $native $phaseId ($id+2)
 $out=@($ne|Where-Object {$_[0] -eq $phaseId});if($out.Count -ne 1){throw 'Cleanup output ambiguous'}
 $dest=if($next -eq 6){'In2'}else{'In'}
 $ce+=,@($id,'False',$next,$dest);$ce+=,@($id,'True',($id+1),'In');$ce+=,@(($id+1),'False',$next,$dest);$ce+=,@(($id+1),'True',($id+2),$incoming[0][3]);$ce+=,@(($id+2),$out[0][1],$next,$dest)
 $contracts+=,@{contact=$contact;tag=$tag;depot=$depot;init_node=$case.native_initializer_bindings.node;cleanup_condition=$incoming[0][0];cleanup_phase=$phaseId;guard=$common;source=$case}
}
RebuildB5 $cg $ce;Set-RedHandleProperty $old Graph $cg;Save $old $cleanupDepot
# Gate only new native gig admission; saved executing descendants are untouched.
foreach($job in @('sts_ep1_08','sts_std_arr_06','sts_std_arr_12')){
 $d='towercontinued\native_gigs_u9\'+$job+'_entry.questphase';$r=(Read-Cr2wFile (Join-Path (Join-Path $O 'archive_source') $d)).RootChunk;$g=$r.Graph.Chunk
 $edges=@(EdgesB5 $g|ForEach-Object {$_});$e=@($edges|Where-Object {$_[0] -eq 65001});if($e.Count -ne 1){throw 'Entry boundary changed'}
 $c=[WolvenKit.RED4.Types.questLogicalCondition]::new();$c.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 foreach($case in $cases|Where-Object job -EQ $job){Add-RedHandle $c.Conditions (New-FactCondition ('PTFRPH1_'+$case.contact+'_Issued') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 AddNodeB5 $g (PauseB5 64999 $c);$target=$e[0][2];$socket=$e[0][3];$e[0][2]=64999;$e[0][3]='In';$edges+=,@(64999,'Out',$target,$socket);RebuildB5 $g $edges;Save $r $d
}
$xl=Join-Path $O 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';$x=[IO.File]::ReadAllText($xl);$nl="`n";if($x.Contains("`r`n")){$nl="`r`n"}
$entries=@();foreach($b in $boots){$entries+=@("    - path: $b",'      parent: ep1\quest\ep1.quest','      input:','        node: [1]','        socket: Out')}
[IO.File]::WriteAllText($xl,$x.Replace('streaming:',(($entries -join $nl)+$nl+'streaming:')),[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create((Join-Path $O 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'))
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $O 'archive_source')),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
@{status='BUILT_NOT_INSTALLED';resources=$resources;boots=$boots;contracts=$contracts;native_pins=$pins}|ConvertTo-Json -Depth 100|Set-Content (Join-Path $O 'build_01.json') -Encoding utf8NoBOM
'BUILT_NOT_INSTALLED'
