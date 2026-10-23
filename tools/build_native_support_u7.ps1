param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_support_u7';$out=Join-Path $WorkspaceRoot 'build/NativeSupportU7'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed U7 evidence pinned'}
New-Item -ItemType Directory -Force $audit,(Join-Path $out 'source')|Out-Null
$helper=Get-Content (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw;$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$pins=[ordered]@{}
function ReadU7([string]$relative){$pins[$relative]=R5Hash (Join-Path $WorkspaceRoot $relative);return Read-Cr2wFile (Join-Path $WorkspaceRoot $relative)}
function EmptyU7 {return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function CopyU7($source,$ids){$g=EmptyU7;foreach($id in $ids){$n=(Get-QuestNode $source $id).DeepCopy();ClearB5 $n;AddNodeB5 $g $n};return $g}
function RefU7($n,[string]$depot){$n.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($depot)}
$resources=[ordered]@{}
function SaveU7($g,[string]$name){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $depot='towercontinued\native_support_u7\'+$name+'.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw)|Out-Null
 Write-Cr2wFile $f $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit ($name+'.json'))
 $resources[$depot]=R5Hash $raw;return $depot
}
$init=(ReadU7 'research/gig_restoration/stock_shark_u2/sources/raw/base/quest/holocalls/holocall_initializers.questphase').RootChunk.Graph.Chunk
# Exact native initializer slice: Padre plus the shared interrupt controller and
# reset plumbing. Other contacts/patch-era contact activation branches omitted.
$ids=@(5,25,79,102,107,108,114,115,116,117,118,119,120,124,131,132)
$phone=CopyU7 $init $ids
RefU7 (Get-QuestNode $phone 124) 'base\quest\holocalls\padre\padre_cleanup.questphase'
$reset=Get-QuestNode $phone 124
(Get-QuestSocket $reset 'In1').Name='In42';(Get-QuestSocket $reset 'Out1').Name='Out42'
$phoneEdges=@(EdgesB5 $init|ForEach-Object {$_}|Where-Object {$_[0] -in $ids -and $_[2] -in $ids})
foreach($e in $phoneEdges){if($e[2] -eq 124){$e[3]='In42'};if($e[0] -eq 124){$e[1]='Out42'}}
RebuildB5 $phone $phoneEdges
$phoneDepot=SaveU7 $phone 'padre_initializer'
# Stock outer reset_out -> hub -> reset_in lifecycle. The initializer's
# TERMINATING reset_out kills its old controller before a reset re-entry.
$add=(ReadU7 'research/b0_missing_content/root_children/raw/base/quest/additional_game_elements.questphase').RootChunk.Graph.Chunk
$parent=CopyU7 $add @(0,34,35);RefU7 (Get-QuestNode $parent 34) $phoneDepot
RebuildB5 $parent @(@(0,'Out',34,'In1'),@(34,'reset_out',35,'In1'),@(35,'Out1',34,'reset_in'))
$parentDepot=SaveU7 $parent 'padre_parent'
# The original completion watcher and original additive fixer-credit node,
# isolated from historical/completed gigs in the district-wide initializer.
$loop=(ReadU7 'research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_new_fixer_loop.questphase').RootChunk.Graph.Chunk
$hey=NestedB5 $loop @(2,4);$credit=CopyU7 $hey @(0,8,3)
AddNodeB5 $credit (New-SetFactNode 65000 'PTFRU7_Support_CreditDone' 1)
RebuildB5 $credit @(@(0,'Out',8,'In'),@(8,'Out',3,'In'),@(3,'Out',65000,'In'))
$creditDepot=SaveU7 $credit 'jeopardy_credit'
$guard=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;PTFRU7_Support_Request=1;PTFRU7_Support_Permit=1;PTFRU7_Support_Issued=0;PTFRU7_Support_Fault=0;PTFRU6_Padre_Request=0;PTFRU6_Padre_Issued=0;PTFRU4_Jeopardy_Request=0;PTFRU4_Jeopardy_Started=0;rey_06_start=0;rey_06_finished=0;PTFRB7_hey_rey_06_Queued=0;PTFRB7_hey_rey_06_Started=0;holo_setup_active=0;holo_setup_started=0;holo_interrupt_call=0;holo_active_call_interrupted=0;holo_reset=0;holo_force_reset=0;holo_reset_soft=0;holo_padre_calls_v_start_activate=0;holo_padre_calls_v_start_activate_count=0;holo_padre_calls_v_start_done=0;holo_padre_calls_v_end_activate=0;holo_padre_calls_v_end_done=0;holo_padre_calls_v_rejected=0;holo_padre_calls_v_rejectable=0;holo_v_calls_padre_start_activate=0;holo_v_calls_padre_start_done=0;holo_v_calls_padre_end_activate=0;holo_v_calls_padre_end_done=0;audio_padre_calls_v_start_activate=0;audio_v_calls_padre_start_activate=0;audio_v_calls_padre_end_activate=0;phonecall_sebastian_padre_perez_with_player=0;phonecall_player_with_sebastian_padre_perez=0}
function GuardU7 { $c=AllB5 $guard;Add-RedHandle $c.Conditions (EqB5 'holo_padre_calls_v_start_count' 'holo_padre_calls_v_end_count');Add-RedHandle $c.Conditions (EqB5 'holo_v_calls_padre_start_count' 'holo_v_calls_padre_end_count');return $c }
$g=EmptyU7
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRU7_Support_Ready' 1),(New-SetFactNode 2 'PTFRU7_Support_Revision' 1),(PauseB5 3 (GuardU7)),(New-ConditionNode 4 (GuardU7)),(New-SetFactNode 5 'PTFRU7_Support_Issued' 1),(PauseB5 8 (AllB5 ([ordered]@{PTFRU4_Jeopardy_Started=1;PTFRU7_Support_CreditDone=0}))))){AddNodeB5 $g $n}
foreach($pair in @(@(6,$parentDepot),@(7,$creditDepot))){$n=(Get-QuestNode $init 79).DeepCopy();$n.Id=[uint16]$pair[0];ClearB5 $n;RefU7 $n $pair[1];AddNodeB5 $g $n}
(Get-QuestSocket (Get-QuestNode $g 6) 'In1').Name='Input'
RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'False',3,'In'),@(4,'True',5,'In'),@(5,'Out',6,'Input'),@(5,'Out',8,'In'),@(8,'Out',7,'In1'))
$depot=SaveU7 $g 'support_wrapper'
# Disable only new U6 trial requests while U7 is installed; existing U6 owner
# is not cut/migrated. U7 refuses any save already using U6 or U4.
$oldScript=Join-Path $WorkspaceRoot 'redscript/PTFR_NativePadreU6/NativePadreU6.reds'
R5Match $oldScript '64CBD55882A42C4D80A90CFA7886DF8199D4E3E045B4907A2A1BF15B0AD31F92'
$text=Get-Content $oldScript -Raw;$anchor='  public func Start(confirmation: String) -> String {'
$insert="`n    return `"U6 standalone entry superseded while U7 is installed. Use NativeSupportU7 on the original pre-U6/U4 snapshot; existing owners are not migrated.`";`n  }`n  private func LegacyStartUnused(confirmation: String) -> String {"
if([regex]::Matches($text,[regex]::Escape($anchor)).Count -ne 1){throw 'U6 anchor drift'}
# Keep legacy code solely for exact rollback/source comparison, unreachable.
$new=$text.Replace($anchor,$anchor+$insert)
if($new.Replace($insert,'') -cne $text){throw 'Unexpected U6 delta'}
[IO.File]::WriteAllText((Join-Path $out 'NativePadreU6.reds'),$new,[Text.UTF8Encoding]::new($false))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game);$collision=B72CollisionCheck $inventory $WorkspaceRoot $depot
if($collision.new_id -in $inventory.id){throw 'U7 registration already present'}
$xl=B71Render @($depot);B71Parse $xl|Out-Null
[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_NativeSupportU7.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_NativeSupportU7.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 4){throw 'Pack scope failure'}
foreach($entry in $packed.Files.Values){if(-not $resources.Contains($entry.Name)){throw 'Unexpected packed resource'};$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne $resources[$entry.Name]){throw 'Packed mismatch'}}finally{$mem.Dispose()}}
$files=@(
 @{source='build/NativeSupportU7/TowerContinued_NativeSupportU7.archive';relative='archive/pc/mod/TowerContinued_NativeSupportU7.archive';predecessor=$null},
 @{source='build/NativeSupportU7/TowerContinued_NativeSupportU7.archive.xl';relative='archive/pc/mod/TowerContinued_NativeSupportU7.archive.xl';predecessor=$null},
 @{source='redscript/PTFR_NativeSupportU7/NativeSupportU7.reds';relative='r6/scripts/PTFR_NativeSupportU7/NativeSupportU7.reds';predecessor=$null},
 @{source='build/NativeSupportU7/NativePadreU6.reds';relative='r6/scripts/PTFR_NativePadreU6/NativePadreU6.reds';predecessor=R5Hash $oldScript}
)
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U7_NATIVE_SUPPORT_TRIAL';files=$files;depot=$depot;collision=$collision;resources=$resources;source_pins=$pins;phone_nodes=$ids;phone_edges=$phoneEdges;guard_pairs=$guard;packed_readback=$true;builder_sha256=R5Hash $PSCommandPath;scope='Padre-scoped native initializer/reset-parent slice, direct original Padre/interrupt/cleanup resources; original Jeopardy-only credit watcher. No other contact, gig, payout or tier starts; no production history claim.'})
'BUILT_U7_NATIVE_SUPPORT_TRIAL'
