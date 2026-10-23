param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_padre_u6';$out=Join-Path $WorkspaceRoot 'build/NativePadreU6'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed U6 evidence pinned'}
New-Item -ItemType Directory -Force $audit,(Join-Path $out 'source')|Out-Null
$helper=Get-Content (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw;$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$initial=Read-Cr2wFile (Join-Path $WorkspaceRoot 'research/gig_restoration/stock_shark_u2/sources/raw/base/quest/holocalls/holocall_initializers.questphase')
$child=(Get-QuestNode $initial.RootChunk.Graph.Chunk 79).DeepCopy();$child.Id=[uint16]7;ClearB5 $child
$native='base\quest\holocalls\padre\padre_holocall.questphase'
if($child.PhaseResource.DepotPath.ToString() -cne $native){throw 'Wrong native child'}
$guardPairs=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;PTFRU6_Padre_Request=1;PTFRU6_Padre_Permit=1;PTFRU6_Padre_Issued=0;PTFRU6_Padre_Fault=0;rey_06_start=0;rey_06_finished=0;holo_setup_active=0;holo_setup_started=0;holo_interrupt_call=0;holo_active_call_interrupted=0;holo_reset=0;holo_force_reset=0;holo_reset_soft=0;holo_padre_calls_v_start_activate=0;holo_padre_calls_v_start_activate_count=0;holo_padre_calls_v_start_done=0;holo_padre_calls_v_end_activate=0;holo_padre_calls_v_end_done=0;holo_padre_calls_v_rejected=0;holo_padre_calls_v_rejectable=0;holo_v_calls_padre_start_activate=0;holo_v_calls_padre_start_done=0;holo_v_calls_padre_end_activate=0;holo_v_calls_padre_end_done=0;audio_padre_calls_v_start_activate=0;audio_v_calls_padre_start_activate=0;audio_v_calls_padre_end_activate=0;phonecall_sebastian_padre_perez_with_player=0;phonecall_player_with_sebastian_padre_perez=0}
function GuardU6 {
 $c=AllB5 $guardPairs
 Add-RedHandle $c.Conditions (EqB5 'holo_padre_calls_v_start_count' 'holo_padre_calls_v_end_count')
 Add-RedHandle $c.Conditions (EqB5 'holo_v_calls_padre_start_count' 'holo_v_calls_padre_end_count')
 return $c
}
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$g=[WolvenKit.RED4.Types.questGraphDefinition]::new();Set-RedHandleProperty $root Graph $g
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 'PTFRU6_Padre_Ready' 1),(New-SetFactNode 2 'PTFRU6_Padre_Revision' 1),(PauseB5 3 (GuardU6)),(New-ConditionNode 4 (GuardU6)),(New-SetFactNode 5 'PTFRU6_Padre_Issued' 1),$child)){AddNodeB5 $g $n}
RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'Out',4,'In'),@(4,'False',3,'In'),@(4,'True',5,'In'),@(5,'Out',7,'In1'))
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
$depot='towercontinued\native_padre_u6\padre_wrapper.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
New-Item -ItemType Directory -Force (Split-Path -Parent $raw)|Out-Null
Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit 'wrapper.json')
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null
$inventory=@(B72Inventory $game);$collision=B72CollisionCheck $inventory $WorkspaceRoot $depot
if($collision.new_id -in $inventory.id){throw 'U6 injection ID already installed'}
B71Parser|Out-Null;$xl=B71Render @($depot);B71Parse $xl|Out-Null
[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_NativePadreU6.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_NativePadreU6.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 1){throw 'Pack scope failure'}
$entry=@($packed.Files.Values)[0];if($entry.Name -cne $depot){throw 'Packed unexpected resource'}
$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne (R5Hash $raw)){throw 'Packed mismatch'}}finally{$mem.Dispose()}
$files=@(
 @{source='build/NativePadreU6/TowerContinued_NativePadreU6.archive';relative='archive/pc/mod/TowerContinued_NativePadreU6.archive'},
 @{source='build/NativePadreU6/TowerContinued_NativePadreU6.archive.xl';relative='archive/pc/mod/TowerContinued_NativePadreU6.archive.xl'},
 @{source='redscript/PTFR_NativePadreU6/NativePadreU6.reds';relative='r6/scripts/PTFR_NativePadreU6/NativePadreU6.reds'}
)
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U6_NATIVE_CONTROLLER_TRIAL';files=$files;depot=$depot;native_resource=$native;collision=$collision;wrapper_only=$true;original_resources_packed=0;packed_readback=$true;guard_pairs=$guardPairs;builder_sha256=R5Hash $PSCommandPath;scope='Original Padre controller/scene; explicit post-Tower one-shot entry only. Source-backed native parent shutdown and idle/balanced protocol guard, not arbitrary owner introspection. No global initializer/interrupt loop/reset, gig/reward changes or pre-ending activation.'})
'BUILT_U6_NATIVE_CONTROLLER_TRIAL'
