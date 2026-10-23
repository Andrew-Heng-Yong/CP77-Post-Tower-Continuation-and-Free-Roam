param([string]$Revision='claire_03',[string]$Contract='prealpha/sidejobs_s27/claire/contract03.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$helper=Get-Content -LiteralPath (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper definitions changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^claire_\d{2}$'){throw 'Invalid immutable revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Build exists; choose successor'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback')|Out-Null
$spec=Get-Content -LiteralPath (Join-Path $ws $Contract) -Raw|ConvertFrom-Json
$o=@($spec.owners)[0]
$pins=[ordered]@{}
foreach($p in $spec.source_pins.PSObject.Properties){$pins[$p.Name]=$p.Value}
function Pin($rel){$pins[$rel]=(Get-FileHash -LiteralPath (Join-Path $ws $rel)).Hash}
function ReadGraph($rel){Pin $rel;Pin ($rel.Replace('/raw/','/json/')+'.json');return (Read-Cr2wFile (Join-Path $ws $rel)).RootChunk.Graph.Chunk}
function JournalCondition($path,$class){
 $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.RealPath=$path;$p.ClassName=$class;$p.FileEntryIndex=if($path -match '^contacts/'){1}else{2}
 $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t Path $p;$t.State=[WolvenKit.RED4.Types.Enums+gameJournalEntryState]::Inactive;$t.Inverted=$false
 $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c Type $t;return $c
}
function Guard([bool]$post){
 $pairs=[ordered]@{}
 foreach($part in @($spec.common_equal,$o.facts_equal)){foreach($p in $part.PSObject.Properties){$pairs[$p.Name]=[int]$p.Value}}
 $pairs[$o.tag+'_Issued']=[int]$post;$pairs[$o.tag+'_Fault']=0;$pairs[$o.tag+'_Finished']=0
 $pairs[$spec.phone.support_fact]=1
 if(!$post){$pairs[$o.tag+'_Permit']=1}
 $c=AllB5 $pairs
 foreach($p in $o.fact_ranges.PSObject.Properties){Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.min) 'GreaterOrEqual');Add-RedHandle $c.Conditions (New-FactCondition $p.Name ([int]$p.Value.max) 'LessOrEqual')}
 foreach($j in $o.journals){if(@($j.states).Count -ne 1 -or $j.states[0] -ne 1){throw 'Fresh-only native guard'};Add-RedHandle $c.Conditions (JournalCondition $j.path $j.class)}
 return $c
}
$questRel='research/sidejobs_s25/families/native_01/raw/base/quest/side_quests/sq024/sq024.quest'
$native=ReadGraph $questRel
$tickRel='research/ncpd_scanner_n1/parents_02/raw/base/open_world/minor_activities/badlands/inland_avenue_se1/ma_bls_ina_se1_minor_activities.questphase'
$tick=ReadGraph $tickRel
$g=[WolvenKit.RED4.Types.questGraphDefinition]::new()
$phase=(Get-QuestNode $native 2).DeepCopy();ClearB5 $phase;$phase.Id=[uint16]100
if($null -ne $phase.PhaseGraph -and $null -ne $phase.PhaseGraph.Chunk){throw 'Expected original direct phase reference without embedded graph'}
$contact=(Get-QuestNode $native 13).DeepCopy();ClearB5 $contact;$contact.Id=[uint16]93
$delay=(Get-QuestNode $tick 173).DeepCopy();ClearB5 $delay;$delay.Id=[uint16]89;$delay.Condition.Chunk.Type.Chunk.TickCount=[uint32]2
foreach($n in @((New-InputNode 0 'In1'),(New-SetFactNode 1 ($o.tag+'_Ready') 1),(PauseB5 2 (Guard $false)),(New-ConditionNode 3 (Guard $false)),(New-SetFactNode 4 ($o.tag+'_Issued') 1),$delay,(New-ConditionNode 90 (Guard $true)),(New-SetFactNode 91 ($o.tag+'_Fault') 1),(New-SetFactNode 92 ($o.tag+'_Entered') 1),$contact,$phase,(New-SetFactNode 101 ($o.tag+'_Finished') 1))){AddNodeB5 $g $n}
RebuildB5 $g @(@(0,'Out',1,'In'),@(1,'Out',2,'In'),@(2,'Out',3,'In'),@(3,'False',2,'In'),@(3,'True',4,'In'),@(4,'Out',89,'In'),@(89,'Out',90,'In'),@(90,'False',91,'In'),@(90,'True',92,'In'),@(92,'Out',93,'In'),@(93,'Out',100,'sq024_in'),@(100,'sq024_out',101,'In'))
$root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
$f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
$raw=Join-Path (Join-Path $out 'source') $o.depot
Write-Cr2wFile $f $raw
$json=Join-Path $out 'readback/sq024_fresh.json';Export-Cr2wJson (Read-Cr2wFile $raw) $json
foreach($p in @($Contract,'prealpha/sidejobs_s27/claire/build.ps1','prealpha/sidejobs_s27/claire/test.py','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1',('research/sidejobs_s27/claire/dependency_'+[IO.Path]::GetFileNameWithoutExtension($Contract).Substring(8)+'.json'))){Pin $p}
foreach($p in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $ws $p)).Hash -cne $pins[$p]){throw "Source drift: $p"}}
$resources=[ordered]@{};$resources[$o.depot]=(Get-FileHash -LiteralPath $raw).Hash
$nativeResources=[ordered]@{};foreach($p in $spec.native_resources.PSObject.Properties){$nativeResources[$p.Name]=$p.Value}
$nativeResources['base\quest\side_quests\sq024\sq024.quest']=@{raw=$questRel;raw_sha256=(Get-FileHash -LiteralPath (Join-Path $ws $questRel)).Hash;json=$questRel.Replace('/raw/','/json/')+'.json';json_sha256=(Get-FileHash -LiteralPath (Join-Path $ws ($questRel.Replace('/raw/','/json/')+'.json'))).Hash}
$result=[ordered]@{status='BUILT_CLAIRE_FRESH_NOT_LIVE';component='claire';contract=$Contract;contract_sha256=(Get-FileHash -LiteralPath (Join-Path $ws $Contract)).Hash;resources=$resources;boots=@($o.depot);resource_details=@(@{depot=$o.depot;relative='source/'+$o.depot.Replace('\','/');sha256=(Get-FileHash -LiteralPath $raw).Hash;readback='readback/sq024_fresh.json';readback_sha256=(Get-FileHash -LiteralPath $json).Hash});source_pins=$pins;native_resources=$nativeResources;native_copies=@(@{source=$questRel;source_graph='root';source_id=2;target_graph='root';target_id=100},@{source=$questRel;source_graph='root';source_id=13;target_graph='root';target_id=93});override_donors=@{};roots=@($o.ids);runtime_scripts_added=0;official_overrides=@();native_progress_resets=$false;support_dependency=$spec.phone.support_fact;scope='One genuinely unstarted five-root Claire family through original sq024_in. Original story/calls/races/rewards/service handoffs retained. No debug inputs, reset, bypass, fake missing-phase replacement, B0 override or MQ056 repeatable change.'}
[IO.File]::WriteAllText((Join-Path $out 'component.json'),($result|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash -LiteralPath (Join-Path $out 'component.json')).Hash}|ConvertTo-Json
