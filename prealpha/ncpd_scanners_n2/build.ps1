param([string]$Revision='n2_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^n2_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable build exists; use a new revision'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$rows=@();$collisions=@()
function Pin([string]$rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $rel)).Hash}
function Native([string]$rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return Read-Cr2wFile (Join-Path $WorkspaceRoot $rel)}
foreach($p in @('prealpha/ncpd_scanners_n2/build.ps1','prealpha/ncpd_scanners_n2/ScannerAdmissionN2.reds','prealpha/ncpd_scanners_n2/catalog.py','research/ncpd_scanners_n2/catalog_v2.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/json/ep1/quest/ep1.quest.json')){Pin $p}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
$catalog=Get-Content (Join-Path $WorkspaceRoot 'research/ncpd_scanners_n2/catalog_v2.json') -Raw|ConvertFrom-Json
if($catalog.rows.Count -ne 157 -or $catalog.issues.Count -ne 0){throw 'Catalog changed'}
Pin $catalog.journal_source
$pilots=@('ma_wat_lch_01','ma_wat_lch_02','ma_wat_lch_03')
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0;PTFRN1_Support_Issued=1}
function CopyN2($source,$ids){
 $g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($id in $ids){$original=Get-QuestNode $source $id;$n=$original.DeepCopy();ClearB5 $n
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk $original.PhaseGraph.Chunk}
  AddNodeB5 $g $n
 };return $g
}
$loaded=@{}
$badlandsSource='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/badlands/badlands_minor_activities.questphase'
$badlands=(Native $badlandsSource).RootChunk.Graph.Chunk
foreach($s in $catalog.rows){
 if($s.key -in $pilots){continue}
 $parent=($s.parent -replace '\.json$','').Replace('/json/','/raw/')
 if(!$loaded.ContainsKey($parent)){$loaded[$parent]=Native $parent}
 $resource=$loaded[$parent];$ng=$resource.RootChunk.Graph.Chunk
 if($resource.RootChunk.PhasePrefabs.Count -ne 0){throw 'Parent prefabs require explicit scoping'}
 $tag='PTFRN2_'+$s.key;$pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]}
 $pairs[$tag+'_Issued']=0
 foreach($f in @($s.start_facts)+@($s.finish_facts)){
  # Stock LCH14 and LCH15 both write LCH14's finish fact. Neither encounter's
  # eligibility may be inferred from that shared fact. Each has an independent
  # native start fact that increments on entry and is never reset by its phase.
  if($s.key -in @('ma_wat_lch_14','ma_wat_lch_15') -and $f -eq 'ma_wat_lch_14_finished'){continue}
  $pairs[$f]=0
 }
 foreach($w in $s.writes){if($w.factName -like '*_av_start_only' -and $w.value -gt 0){$pairs[$w.factName]=0}}
 $special=$s.key -in @('ma_cct_cpz_16','ma_wbr_nok_05')
 if(!$special -and $s.start_facts.Count -eq 0){throw 'No reliable start guard'}
 $g=CopyN2 $ng $s.selected_nodes
 $ee=@(EdgesB5 $ng|ForEach-Object {$_}|Where-Object {$_[0] -in $s.selected_nodes -and $_[2] -in $s.selected_nodes})
 if($s.admission_edges.Count -ne 1){throw 'Ambiguous admission'}
 $ad=$s.admission_edges[0]
 $ee=@($ee|Where-Object {-not($_[0] -eq $ad[0] -and $_[1] -ceq $ad[1] -and $_[2] -eq $ad[2] -and $_[3] -ceq $ad[3])})
 # Check native progress again AFTER stock tier/prerequisite waits. Only the
 # initial entry edge changes: native retry loops and all output ports stay.
 foreach($n in @((New-ConditionNode 1000 (AllB5 $pairs)),(New-SetFactNode 1001 ($tag+'_Issued') 1),(New-SetFactNode 1002 ($tag+'_Refused') 1))){AddNodeB5 $g $n}
 if($special){
  $response=[WolvenKit.RED4.Types.questLogicalCondition]::new();$response.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
  Add-RedHandle $response.Conditions (New-FactCondition ($tag+'_Permit') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
  Add-RedHandle $response.Conditions (New-FactCondition ($tag+'_Denied') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
  foreach($n in @((New-SetFactNode 1003 ($tag+'_Request') 1),(PauseB5 1004 $response),(New-ConditionNode 1005 (New-FactCondition ($tag+'_Permit') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))))){AddNodeB5 $g $n}
  $ee+=,@($ad[0],$ad[1],1003,'In');$ee+=,@(1003,'Out',1004,'In');$ee+=,@(1004,'Out',1005,'In')
  $ee+=,@(1005,'True',1000,'In');$ee+=,@(1005,'False',1002,'In')
 }else{$ee+=,@($ad[0],$ad[1],1000,'In')}
 $ee+=,@(1000,'True',1001,'In');$ee+=,@(1000,'False',1002,'In');$ee+=,@(1001,'Out',$ad[2],$ad[3])
 RebuildB5 $g $ee
 # Outer boot always has In1; the embedded stock slice keeps its original input
 # name (including Badlands In2) and all original node IDs/payloads.
 $outer=[WolvenKit.RED4.Types.questGraphDefinition]::new()
 foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($tag+'_Ready') 1),(PauseB5 2 (AllB5 $pairs)))){AddNodeB5 $outer $n}
 $phase=[WolvenKit.RED4.Types.questPhaseNodeDefinition]::new();$phase.Id=[uint16]100;Set-RedHandleProperty $phase PhaseGraph $g;AddNodeB5 $outer $phase
 $entryPort=(Get-QuestNode $ng $s.input).SocketName.ToString()
 [void](New-QuestSocket $phase $entryPort ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
 [void](New-QuestSocket $phase 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
 $oe=@(@(0,'Out',1,'In'),@(1,'Out',2,'In'))
 if($s.extra_parent_gate){$b=(Get-QuestNode $badlands 9).DeepCopy();ClearB5 $b;AddNodeB5 $outer $b;$oe+=,@(2,'Out',9,'In');$oe+=,@(9,'Out',100,$entryPort)}
 else{$oe+=,@(2,'Out',100,$entryPort)}
 RebuildB5 $outer $oe
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $outer
 $file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$root
 $depot='towercontinued\ncpd_scanners_n2\'+$s.key+'.questphase';$attempt=0
 while((B72Id ($depot+':1')) -in $used){$collisions+=,$depot;$attempt++;$depot='towercontinued\ncpd_scanners_n2\'+$s.key+'_id'+$attempt+'.questphase'}
 $id=B72Id ($depot+':1');if($id -ne (B72IdIndependent ($depot+':1'))){throw 'CRC mismatch'}
 $used+=,$id;$boots+=,$depot
 $raw=Join-Path (Join-Path $out 'source') $depot;Write-Cr2wFile $file $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$s.key+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash
 $sources=@($s.source)+@($s.phase_refs|ForEach-Object {'research/ncpd_scanner_n1/encounters_02/json/'+$_.Replace('\','/')+'.json'})
 foreach($p in $sources){Native (($p -replace '\.json$','').Replace('/json/','/raw/'))|Out-Null}
 $rows+=,@{key=$s.key;depot=$depot;injection_id=$id;guard_equal=$pairs;selected_nodes=$s.selected_nodes;parent=$parent;child=$s.child;entry=$s.entry;admission_edge=$ad;native_depot=$s.native_depot;input=$entryPort;saved_poi_guard=$special;extra_parent_gate=$s.extra_parent_gate;native_outputs=$s.outputs}
}
if($rows.Count -ne 154){throw 'Wrong expansion count'}
foreach($p in Get-ChildItem (Join-Path $WorkspaceRoot 'research/ncpd_scanners_n2/scenes_01/raw') -Recurse -File){Native ([IO.Path]::GetRelativePath($WorkspaceRoot,$p.FullName).Replace('\','/'))|Out-Null}
$archive=Join-Path $out 'TowerContinued_NCPD_N2.archive';$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 154){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ScannerAdmissionN2.reds') -Destination (Join-Path $out 'ScannerAdmissionN2.reds')
$files=@();foreach($name in @('TowerContinued_NCPD_N2.archive','TowerContinued_NCPD_N2.archive.xl','ScannerAdmissionN2.reds')){
 $rel=if($name -like '*.reds'){'r6/scripts/TowerContinued_NCPD_N2/'+$name}else{'archive/pc/mod/'+$name}
 $files+=,@{relative=$rel;sha256=(Get-FileHash (Join-Path $out $name)).Hash}
}
$result=[ordered]@{status='BUILT_N2_LIVE_PENDING';files=$files;resources=$resources;activities=$rows;source_pins=$pins;installed_injections=$inventory;boots=$boots;resolved_crc_collisions=$collisions;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=1;official_overrides=@();mod_override='';game_writes=0;save_writes=0;pilots_preserved=$pilots;unwired_journal_entries=$catalog.unbound;scope='154 additional stock-connected fresh scanner owners; N1 three untouched. No cyberpsycho or completed-activity reset, synthetic markers, custom rewards or achievement repair.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
