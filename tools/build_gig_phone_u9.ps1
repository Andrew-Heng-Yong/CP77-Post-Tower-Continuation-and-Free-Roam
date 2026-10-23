param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/gig_phone_u9';$out=Join-Path $WorkspaceRoot 'build/GigPhoneU9'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed U9 phone evidence pinned'}
New-Item -ItemType Directory -Force $audit,(Join-Path $out 'source')|Out-Null
$helper=Get-Content (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw;$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$pins=[ordered]@{};$resources=[ordered]@{}
function ReadP9([string]$relative){$pins[$relative]=R5Hash (Join-Path $WorkspaceRoot $relative);return Read-Cr2wFile (Join-Path $WorkspaceRoot $relative)}
function CopyP9($source,$ids){$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();foreach($id in $ids){$n=(Get-QuestNode $source $id).DeepCopy();ClearB5 $n;AddNodeB5 $g $n};return $g}
function RefP9($n,[string]$depot){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($depot)}
function SaveP9($g,[string]$name){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $depot='towercontinued\gig_phone_u9\'+$name+'.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
 Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit ($name+'.json'))
 $resources[$depot]=R5Hash $raw;return $depot
}
$contacts=@('dakota','dino','mr_hands','muamar','padre','reggie','rogue','wakako')
$base='research/gig_restoration/gig_phone_u9/sources/raw/'
$init=(ReadP9 ($base+'base/quest/holocalls/holocall_initializers.questphase')).RootChunk.Graph.Chunk
$cleanup=(ReadP9 ($base+'base/quest/holocalls/holocall_cleanup.questphase')).RootChunk.Graph.Chunk
# Select only the eight approved gig-fixer cleanup tests and their ORIGINAL
# cleanup refs. Bypass omitted contacts through the stock False continuation;
# preserve native order, checks, timeout and terminal output. EP1's separate
# cleanup handshake is omitted because that controller service is not started.
$ce=@(EdgesB5 $cleanup|ForEach-Object {$_});$contactNodes=@();$condNodes=@()
foreach($c in $contacts){
 $depot="base\quest\holocalls\$c\${c}_cleanup.questphase"
 $hits=@($cleanup.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'questPhaseNodeDefinition' -and $_.Chunk.PhaseResource.DepotPath.ToString() -ceq $depot})
 if($hits.Count -ne 1){throw "Cleanup ref missing $c"};$id=[int]$hits[0].Chunk.Id.ToString();$contactNodes+=,$id
 $edge=@($ce|Where-Object {$_[2] -eq $id -and $_[1] -eq 'True'});if($edge.Count -ne 1){throw 'Cleanup condition shape changed'};$condNodes+=,[int]$edge[0][0]
 ReadP9 ($base+$depot)|Out-Null;ReadP9 ($base+"base\quest\holocalls\$c\${c}_holocall.questphase")|Out-Null
}
$cleanupIds=@(0,1,6,7,423,424,495)+$contactNodes+$condNodes
$cg=CopyP9 $cleanup $cleanupIds;$cleanupEdges=@();$bypasses=@()
foreach($e in $ce){
 if($e[0] -notin $cleanupIds){continue};$n=@($e);$trail=@()
 # Terminal EP1 handshake cannot wait for a service intentionally not restored.
 if($n[0] -eq 424){$cleanupEdges+=,@(424,'Out1',6,'In2');$bypasses+=,@{from=$e;to=@(424,'Out1',6,'In2');reason='No separate EP1 reset service is started'};continue}
 while($n[2] -notin $cleanupIds){
  $node=Get-QuestNode $cleanup $n[2]
  if($node.GetType().Name -ne 'questConditionNodeDefinition'){throw "Unexpected excluded cleanup node $($n[2])"}
  $trail+=,$n[2];$next=@($ce|Where-Object {$_[0] -eq $n[2] -and $_[1] -eq 'False'});if($next.Count -ne 1){throw 'Ambiguous cleanup bypass'}
  $n[2]=$next[0][2];$n[3]=$next[0][3]
 }
 $cleanupEdges+=,$n;if($trail.Count){$bypasses+=,@{from=$e;to=$n;omitted_conditions=$trail}}
}
RebuildB5 $cg $cleanupEdges;$cleanupDepot=SaveP9 $cg 'fixer_cleanup'
$phoneIds=@(5,25,50,53,73,75,79,84,86,97,102,107,108,114,115,116,117,118,119,120,124,131,132)
$phone=CopyP9 $init $phoneIds;RefP9 (Get-QuestNode $phone 124) $cleanupDepot
$phoneEdges=@(EdgesB5 $init|ForEach-Object {$_}|Where-Object {$_[0] -in $phoneIds -and $_[2] -in $phoneIds})
RebuildB5 $phone $phoneEdges;$phoneDepot=SaveP9 $phone 'fixer_initializer'
$add=(ReadP9 'research/b0_missing_content/root_children/raw/base/quest/additional_game_elements.questphase').RootChunk.Graph.Chunk
$parent=CopyP9 $add @(0,34,35);RefP9 (Get-QuestNode $parent 34) $phoneDepot
RebuildB5 $parent @(@(0,'Out',34,'In1'),@(34,'reset_out',35,'In1'),@(35,'Out1',34,'reset_in'))
$parentDepot=SaveP9 $parent 'fixer_parent'
$predecessors=@('PTFRU6_Padre_Request','PTFRU6_Padre_Issued','PTFRU6_Padre_Permit','PTFRU7_Support_Request','PTFRU7_Support_Issued','PTFRU7_Support_Permit','PTFRB5_TierRequest','PTFRU8_Heywood_TierRequest')
foreach($r in @('wat','wbr','hey','std','cct','bls','pac')){$predecessors+='PTFRB7_'+$r+'_TierRequest'}
$idle=@('holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance')
$balances=@();foreach($c in $contacts){
 foreach($s in @('start_activate','start_activate_count','start_done','end_activate','end_done','rejected','rejectable')){$idle+="holo_${c}_calls_v_$s"}
 foreach($s in @('start_activate','start_done','end_activate','end_done')){$idle+="holo_v_calls_${c}_$s"}
 foreach($s in @('calls_v_start_activate','calls_v_end_activate')){$idle+="audio_${c}_$s"}
 foreach($s in @('start_activate','end_activate')){$idle+="audio_v_calls_${c}_$s"}
 $balances+=,@("holo_${c}_calls_v_start_count","holo_${c}_calls_v_end_count");$balances+=,@("holo_v_calls_${c}_start_count","holo_v_calls_${c}_end_count")
}
$guard=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;PTFRU9_Support_Request=1;PTFRU9_Support_Permit=1;PTFRU9_Support_Issued=0;PTFRU9_Support_Fault=0}
foreach($s in $predecessors+$idle){$guard[$s]=0}
function GuardP9 {$c=AllB5 $guard;foreach($p in $balances){Add-RedHandle $c.Conditions (EqB5 $p[0] $p[1])};return $c}
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRU9_Support_Ready' 1),(New-SetFactNode 2 'PTFRU9_Support_Revision' 1),(PauseB5 3 (GuardP9)),(New-ConditionNode 4 (GuardP9)),(New-SetFactNode 5 'PTFRU9_Support_Issued' 1))){AddNodeB5 $g $n}
$child=(Get-QuestNode $init 79).DeepCopy();$child.Id=[uint16]6;ClearB5 $child;RefP9 $child $parentDepot;(Get-QuestSocket $child 'In1').Name='Input';AddNodeB5 $g $child
RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'False',3,'In'),@(4,'True',5,'In'),@(5,'Out',6,'Input'))
$depot=SaveP9 $g 'support_wrapper'
# Script predicates and graph guards share an auditable generated catalogue.
function ArrayTextP9($values){return '['+(($values|ForEach-Object {'"'+$_+'"'}) -join ',')+']'}
$data="module PTFR.ActivityStateR3`n// Generated only by build_gig_phone_u9.ps1; exact wrapper admission facts.`npublic abstract class GigPhoneDataU9 {`n"
foreach($row in @(@('PredecessorFacts',$predecessors),@('IdleFacts',$idle),@('BalanceStarts',@($balances|ForEach-Object {$_[0]})),@('BalanceEnds',@($balances|ForEach-Object {$_[1]})))){$data+='  public static func '+$row[0]+'() -> array<String> { return '+(ArrayTextP9 $row[1])+"; }`n"};$data+="}`n"
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'redscript/PTFR_GigPhoneU9/GigPhoneDataU9.generated.reds'),$data,[Text.UTF8Encoding]::new($false))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';B71Parser|Out-Null;$inventory=@(B72Inventory $game);$collision=B72CollisionCheck $inventory $WorkspaceRoot $depot
if($collision.new_id -in $inventory.id){throw 'U9 phone registration exists'}
$xl=B71Render @($depot);B71Parse $xl|Out-Null;[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_GigPhoneU9.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_GigPhoneU9.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 4){throw 'Pack scope failure'}
foreach($entry in $packed.Files.Values){if(-not $resources.Contains($entry.Name)){throw 'Unexpected packed resource'};$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne $resources[$entry.Name]){throw 'Packed mismatch'}}finally{$mem.Dispose()}}
$files=@(@{source='build/GigPhoneU9/TowerContinued_GigPhoneU9.archive';relative='archive/pc/mod/TowerContinued_GigPhoneU9.archive';predecessor=$null},@{source='build/GigPhoneU9/TowerContinued_GigPhoneU9.archive.xl';relative='archive/pc/mod/TowerContinued_GigPhoneU9.archive.xl';predecessor=$null})
foreach($script in @('GigPhoneU9.reds','GigPhoneDataU9.generated.reds')){$files+=,@{source='redscript/PTFR_GigPhoneU9/'+$script;relative='r6/scripts/PTFR_GigPhoneU9/'+$script;predecessor=$null}}
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U9_GIG_PHONE_LIVE_PENDING';files=$files;depot=$depot;collision=$collision;resources=$resources;source_pins=$pins;contacts=$contacts;phone_nodes=$phoneIds;cleanup_nodes=$cleanupIds;cleanup_contact_nodes=$contactNodes;cleanup_condition_nodes=$condNodes;cleanup_bypasses=$bypasses;guard_pairs=$guard;balances=$balances;idle_facts=$idle;predecessor_facts=$predecessors;packed_readback=$true;builder_sha256=R5Hash $PSCommandPath;scope='Eight stock fixer controllers, shared stock interrupt/reset owner, scoped native contact cleanup chain. No gig/sidejob/world activity starts, rewards or tiers. PRE-U7 baseline only; no owner migration.'})
'BUILT_U9_GIG_PHONE_LIVE_PENDING'
