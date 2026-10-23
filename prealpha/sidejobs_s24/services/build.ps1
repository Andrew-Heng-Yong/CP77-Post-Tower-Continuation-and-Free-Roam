param([string]$Revision='services_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^services_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path $out){throw 'Immutable output exists'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$copies=@();$transforms=@()
function Pin($p){$pins[$p]=(Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash}
function ReadPinned($p){Pin $p;return Read-Cr2wFile (Join-Path $WorkspaceRoot $p)}
foreach($p in @('prealpha/sidejobs_s24/services/build.ps1','prealpha/sidejobs_s24/services/contract.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1')){Pin $p}
$contract=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'contract.json') -Raw|ConvertFrom-Json
$s=$contract.owners[0]
$native=(ReadPinned $s.native_source).RootChunk.Graph.Chunk
$contact=(ReadPinned $s.contact_source).RootChunk.Graph.Chunk
foreach($p in $s.sourcepins.PSObject.Properties){if($pins[$p.Name] -cne $p.Value){throw 'Native source changed'}}
$common=[ordered]@{PostTowerFreeRoamActive=1;PTFRP0_DR13=1;PTFRPA2_Finished=1;PTFRPA2_Fault=0;q307_done=1;q307_finished=1;q307_2079=1;q307_main_game_killed=1;q307_ep1_killed=1;q307_active=0;q307_debug_reset=0;q115_point_of_no_return=0;q305_johnny_scene_active=0;PTFRU9_Support_Issued=1;PTFRU9_Support_Fault=0}
function JournalCondition($j){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$j.path;$p.ClassName=$j.class;$p.FileEntryIndex=$(if($j.path.StartsWith('contacts/')){1}else{2})
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function Guard {
 $pairs=[ordered]@{};foreach($k in $common.Keys){$pairs[$k]=$common[$k]};foreach($f in $s.facts_equal.PSObject.Properties){$pairs[$f.Name]=[int]$f.Value}
 $pairs[$s.tag+'_Permit']=1;$pairs[$s.tag+'_Issued']=0;$pairs[$s.tag+'_Finished']=0;$pairs[$s.tag+'_Fault']=0
 $c=AllB5 $pairs
 foreach($r in $s.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $r.Name ([int]$r.Value.min) ([WolvenKit.RED4.Types.Enums+EComparisonType]::GreaterOrEqual));Add-RedHandle $c.Conditions (New-FactCondition $r.Name ([int]$r.Value.max) ([WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual))}
 foreach($j in $s.journals){Add-RedHandle $c.Conditions (JournalCondition $j)};return $c
}
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
foreach($h in $native.Nodes){$n=$h.Chunk.DeepCopy();ClearB5 $n;AddNodeB5 $g $n;$copies+=,@{depot=$s.depot;source=$s.native_source;source_graph='root';source_id=[int]$n.Id.ToString();target_id=[int]$n.Id.ToString()}}
$addContact=(Get-QuestNode $contact ([int]$s.contact_source_node)).DeepCopy();ClearB5 $addContact;$addContact.Id=[uint16]1006
if($addContact.Type.Chunk.Params.Count -ne 1 -or $addContact.Type.Chunk.Params[0].Contact.Chunk.RealPath.ToString() -cne 'contacts/dex'){throw 'Native contact shape changed'}
$addContact.Type.Chunk.Params[0].Contact.Chunk.RealPath=$s.contact_target;AddNodeB5 $g $addContact
foreach($n in @((New-SetFactNode 1001 ($s.tag+'_Ready') 1),(PauseB5 1002 (Guard)),(New-ConditionNode 1003 (Guard)),(New-SetFactNode 1004 ($s.tag+'_Issued') 1),(New-SetFactNode 1005 ($s.tag+'_Entered') 1),(New-SetFactNode 1007 ($s.tag+'_Finished') 1))){AddNodeB5 $g $n}
$edges=@(EdgesB5 $native|ForEach-Object {$_}|Where-Object {$_[0] -ne 0 -and $_[0] -ne 27})
$edges+=,@(0,'Out',1001,'In');$edges+=,@(1001,'Out',1002,'In');$edges+=,@(1002,'Out',1003,'In');$edges+=,@(1003,'False',1002,'In');$edges+=,@(1003,'True',1004,'In');$edges+=,@(1004,'Out',1006,'In');$edges+=,@(1006,'Out',1005,'In');$edges+=,@(1005,'Out',25,'In');$edges+=,@(27,'Out',1007,'In');$edges+=,@(1007,'Out',1,'In')
RebuildB5 $g $edges
$r=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();$r.CookingPlatform=[WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC;Set-RedHandleProperty $r Graph $g
$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$r;$p=Join-Path (Join-Path $out 'source') $s.depot
Write-Cr2wFile $f $p;Export-Cr2wJson (Read-Cr2wFile $p) (Join-Path $out 'readback/the_gig.json')
$resources[$s.depot]=(Get-FileHash -LiteralPath $p).Hash;$boots+=,$s.depot
$transforms+=,@{depot=$s.depot;source=$s.contact_source;source_graph='root';source_id=168;target_id=1006;modified_field='type.params[0].contact.realPath';before='contacts/dex';after='contacts/wakako_okada';reason='Restore only this fresh job contact visibility before its native SMS, without invoking a main-quest owner.'}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $WorkspaceRoot $p)).Hash -cne $pins[$p]){throw 'Pinned source changed during build'}}
$manifest=[ordered]@{schema=1;status='BUILT_NOT_INSTALLED';revision=$Revision;resources=$resources;boots=$boots;source_pins=$pins;native_copies=$copies;transforms=$transforms;mod_overrides=@();contract='prealpha/sidejobs_s24/services/contract.json';common_equal=$common;live='NOT_TESTED'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($manifest|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 2
