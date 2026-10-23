param([string]$Revision='support_01',[Parameter(Mandatory=$true)][string[]]$Contracts)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^support_\d{2}$'){throw 'Bad revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$rows=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function Native($p){Pin $p;Pin ($p.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $p)}
function CopyGraph($g,$ids){
 $new=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){$o=Get-QuestNode $g $id;$n=$o.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $o.PhaseGraph.Chunk};AddNodeB5 $new $n
 };return $new
}
function SaveGraph($g,$label,$inject,$depot){
 $r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $r Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$label+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash;if($inject){$script:boots+=,$depot}
}
foreach($p in @('prealpha/sidejobs_s23/support/build.ps1','prealpha/sidejobs_s23/support/extract.ps1','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1')){Pin $p}
$contractsAll=@()
foreach($rel in $Contracts){Pin $rel;$d=Get-Content -LiteralPath (Join-Path $WorkspaceRoot $rel) -Raw|ConvertFrom-Json
 if($d -is [array]){$contractsAll+=@($d)}elseif($d.PSObject.Properties.Name -contains 'contracts'){$contractsAll+=@($d.contracts)}elseif($d.PSObject.Properties.Name -contains 'owners'){$contractsAll+=@($d.owners)}else{$contractsAll+=,$d}
}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
$globalIdle=@('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance')
$contacts=@(
 @{name='FRANK';folder='frank';init=57;condition=445;cleanup=311;input='In19';output='Out19';job='mq041_corpo'},
 @{name='MRSTUD';folder='mr_stud';init=74;condition=463;cleanup=331;input='In37';output='Out37';job='mq012_stud'},
 @{name='OZOB';folder='ozob';init=78;condition=467;cleanup=335;input='In41';output='Out41';job='mq035_ozob'},
 @{name='SANDRA';folder='sandra';init=87;condition=477;cleanup=345;input='In51';output='Out51';job='mq024_sandra'},
 @{name='WILSON';folder='wilson';init=99;condition=490;cleanup=357;input='In63';output='Out63';job='mq011_wilson'}
)
$initSource='research/gig_restoration/gig_phone_u9/sources/raw/base/quest/holocalls/holocall_initializers.questphase'
$init=(Native $initSource).RootChunk.Graph.Chunk
foreach($contact in $contacts){
 $eligible=@($contractsAll|Where-Object {$_.id -ceq $contact.job})
 if($eligible.Count -eq 0){throw "Missing contact consumer: $($contact.job)"}
 $idle=[ordered]@{};foreach($name in $globalIdle){$idle[$name]=0}
 # Use only current busy/request facts named by the ORIGINAL controller and
 # scenes, not historical start/end equality. S22.1 demonstrated why that fails.
 foreach($suffix in @('_holocall.questphase','_cleanup.questphase','_holocall.scene')){
  $p='research/sidejobs_s23/support/native_01/raw/base/quest/holocalls/'+$contact.folder+'/'+$contact.folder+$suffix
  [void](Native $p)
  $json=Get-Content -LiteralPath (Join-Path $WorkspaceRoot ($p.Replace('/raw/','/json/')+'.json')) -Raw
  foreach($match in [regex]::Matches($json,'"(holo_[A-Za-z0-9_]+)"')){
   $name=$match.Groups[1].Value
   if($name -match '_(start_activate|end_activate|active|started)$'){$idle[$name]=0}
  }
 }
 $tag='PTFRS23_PHONE_'+$contact.name
 function Admission {
  $pairs=[ordered]@{};foreach($key in $common.Keys){$pairs[$key]=$common[$key]};foreach($key in $idle.Keys){$pairs[$key]=0};$pairs[$tag+'_Issued']=0
  $c=AllB5 $pairs;$consumers=[WolvenKit.RED4.Types.questLogicalCondition]::new();$consumers.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
  foreach($row in $eligible){Add-RedHandle $consumers.Conditions (AllB5 ([ordered]@{($row.tag+'_Permit')=1;($row.tag+'_Issued')=0;($row.tag+'_Fault')=0}))}
  Add-RedHandle $c.Conditions $consumers;return $c
 }
 $g=CopyGraph $init @($contact.init)
 foreach($n in @((New-InputNode 1000 'In1'),(New-SetFactNode 1001 ($tag+'_Ready') 1),(PauseB5 1002 (Admission)),(New-ConditionNode 1003 (Admission)),(New-SetFactNode 1004 ($tag+'_Issued') 1))){AddNodeB5 $g $n}
 RebuildB5 $g @(@(1000,'Out',1001,'In'),@(1001,'Out',1002,'In'),@(1002,'Out',1003,'In'),@(1003,'False',1002,'In'),@(1003,'True',1004,'In'),@(1004,'Out',$contact.init,'In1'))
 $depot='towercontinued\sidejobs_s23\phone\'+$contact.name.ToLower()+'.questphase';SaveGraph $g $contact.name $true $depot
 $rows+=,@{contact=$contact;tag=$tag;consumer_tags=@($eligible.tag);idle=$idle;depot=$depot}
}
# Continue the CURRENT S22.1 cleanup, including all previous fixers, NCPD,
# Daniels and Delamain. No broad initializer/interrupt service is restarted.
$oldSource='prealpha/sidejobs_s221/build/s221_01/source/towercontinued/gig_phone_u9/fixer_cleanup.questphase';Pin $oldSource
$old=(Read-Cr2wFile (Join-Path $WorkspaceRoot $oldSource)).RootChunk.Graph.Chunk
$cleanupSource='research/gig_restoration/gig_phone_u9/sources/raw/base/quest/holocalls/holocall_cleanup.questphase'
$nativeCleanup=(Native $cleanupSource).RootChunk.Graph.Chunk
$g=CopyGraph $old @($old.Nodes|ForEach-Object {[int]$_.Chunk.Id.ToString()})
$edges=@(EdgesB5 $old|ForEach-Object {$_});$redirects=0
foreach($e in $edges){if($e[0] -in @(700,701) -and $e[2] -eq 6){$e[2]=800;$e[3]='In';$redirects++}}
if($redirects -ne 2){throw 'Current cleanup boundary changed'}
for($i=0;$i -lt $contacts.Count;$i++){
 $contact=$contacts[$i];$cid=800+2*$i;$phaseID=$cid+1
 foreach($pair in @(@($contact.condition,$cid),@($contact.cleanup,$phaseID))){
  $original=Get-QuestNode $nativeCleanup $pair[0];$node=$original.DeepCopy();ClearB5 $node;$node.Id=[uint16]$pair[1]
  if($node -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $node.PhaseGraph -and $null -ne $node.PhaseGraph.Chunk){RewireB5 $node.PhaseGraph.Chunk $original.PhaseGraph.Chunk};AddNodeB5 $g $node
 }
 $next=if($i -lt $contacts.Count-1){$cid+2}else{6};$input=if($next -eq 6){'In2'}else{'In'}
 $edges+=,@($cid,'True',$phaseID,$contact.input);$edges+=,@($cid,'False',$next,$input);$edges+=,@($phaseID,$contact.output,$next,$input)
}
RebuildB5 $g $edges;SaveGraph $g 'fixer_cleanup' $false 'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
$m=[ordered]@{status='EXPORTED_S23_SUPPORT_NOT_INSTALLED';resources=$resources;boots=$boots;source_pins=$pins;contacts=$rows;common=$common;init_source=$initSource;cleanup_source=$cleanupSource;cleanup_previous=$oldSource;mod_overrides=@('towercontinued\gig_phone_u9\fixer_cleanup.questphase');native_counter_writes=0;global_owner_restarts=0;history_equalities=0}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($m|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
@{status=$m.status;resources=$resources.Count;boots=$boots.Count;build=$out}|ConvertTo-Json
