param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
. (Join-Path $PSScriptRoot 'shark_b7_2_helpers.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_heywood_u8';$out=Join-Path $WorkspaceRoot 'build/NativeHeywoodU8'
if(Test-Path -LiteralPath (Join-Path $audit 'install_receipt.json')){throw 'Installed U8 evidence pinned'}
New-Item -ItemType Directory -Force $audit,(Join-Path $out 'source')|Out-Null
$helper=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$pins=[ordered]@{}
function ReadU8([string]$relative){$p=Join-Path $WorkspaceRoot $relative;$pins[$relative]=R5Hash $p;return Read-Cr2wFile $p}
function EmptyU8 {return [WolvenKit.RED4.Types.questGraphDefinition]::new()}
function SliceU8($g,$ids){$c=EmptyU8;foreach($id in $ids){$n=(Get-QuestNode $g $id).DeepCopy();ClearB5 $n;if($n.GetType().Name -eq 'questPhaseNodeDefinition' -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RewireB5 $n.PhaseGraph.Chunk (Get-QuestNode $g $id).PhaseGraph.Chunk};AddNodeB5 $c $n};return $c}
function OwnU8([string]$id,[string]$suffix){return 'PTFRU8_'+$id+'_'+$suffix}
$resources=[ordered]@{};$boots=[Collections.Generic.List[string]]::new();$recipes=[Collections.Generic.List[object]]::new()
function SaveU8($g,[string]$name){
 $root=[WolvenKit.RED4.Types.questQuestPhaseResource]::new();Set-RedHandleProperty $root Graph $g
 $f=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$f.RootChunk=$root
 $depot='towercontinued\native_heywood_u8\'+$name+'.questphase';$raw=Join-Path (Join-Path $out 'source') $depot
 New-Item -ItemType Directory -Force (Split-Path -Parent $raw)|Out-Null;Write-Cr2wFile $f $raw
 Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $audit ($name+'.json'))
 $resources[$depot]=R5Hash $raw;$boots.Add($depot);return $depot
}
$planPath=Join-Path $WorkspaceRoot 'research/gig_restoration/family_b7/build_plan.json'
R5Match $planPath '329F8CE605137D6E32556029B673D7375FC4B7F30436D73C127F92CB7609B5E3'
$plan=Get-Content -LiteralPath $planPath -Raw|ConvertFrom-Json
$jobs=@($plan.jobs|Where-Object {$_.region -eq 'hey' -and $_.id -ne 'sts_hey_rey_06'})
if($jobs.Count -ne 7){throw 'Whitelist subset drift'}
$nativePins=[ordered]@{}
foreach($job in $jobs){
 if($job.parent.edits.Count -ne 0){throw 'Native parent requires separate review'}
 foreach($r in $job.resources){if($null -ne $r.binding.embedded_index){throw 'Embedded native binding needs review'};R5Match (Join-Path $WorkspaceRoot $r.binding.source) $r.binding.sha256;$nativePins[$r.raw]=R5Hash (Join-Path $WorkspaceRoot $r.raw)}
 $old='build/GigFamilyB7/source/towercontinued/family_b7/'+$job.id+'/boot.questphase'
 $boot=ReadU8 $old;$g=$boot.RootChunk.Graph.Chunk;$child=Get-QuestNode $g $job.parent.child.id
 $child.PhaseResource=[WolvenKit.RED4.Types.CResourceAsyncReference`1[WolvenKit.RED4.Types.questQuestPhaseResource]]::new($job.resources[0].depot)
 foreach($id in @(65000,65003,65004,65006)){$n=Get-QuestNode $g $id;$n.Type.Chunk.FactName=$n.Type.Chunk.FactName.ToString().Replace($job.tag,('PTFRU8_'+$job.id))}
 foreach($id in @(65001,65002)){
  $n=Get-QuestNode $g $id
  foreach($h in $n.Condition.Chunk.Conditions){$t=$h.Chunk.Type.Chunk;$t.FactName=$t.FactName.ToString().Replace($job.tag,('PTFRU8_'+$job.id))}
  foreach($key in @('Queued','Request','Started','OwnerFinished','Fault','CounterClaim','CounterAck')){Add-RedHandle $n.Condition.Chunk.Conditions (New-FactCondition ($job.tag+'_'+$key) 0 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
  Add-RedHandle $n.Condition.Chunk.Conditions (New-FactCondition 'PTFRU7_Support_Issued' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 }
 $depot=SaveU8 $g ($job.id+'_entry')
 $recipes.Add(@{kind='gig';id=$job.id;title=$job.title;depot=$depot;old=$old;native=$job.resources[0].depot;child=$job.parent.child.id})
}
# Exact original credit routing includes failure alternatives. Hot Merchandise
# native watcher14 has no edge to counter3, so no credit is invented for it.
$loop=(ReadU8 'research/gig_restoration/lifecycle_sources/raw/base/open_world/street_stories/street_stories_new_fixer_loop.questphase').RootChunk.Graph.Chunk
$credit=NestedB5 $loop @(2,4)
$creditMap=[ordered]@{sts_hey_gle_06=@(0,2,3);sts_hey_gle_04=@(0,4,3);sts_hey_spr_01=@(0,12,3);sts_hey_rey_08=@(0,10,3);sts_hey_gle_01=@(0,6,17,18,3);sts_hey_spr_03=@(0,13,3)}
foreach($id in $creditMap.Keys){
 $ids=$creditMap[$id];$g=SliceU8 $credit $ids
 $edges=@(EdgesB5 $credit|ForEach-Object {$_}|Where-Object {$_[0] -in $ids -and $_[2] -in $ids})
 $guard=[ordered]@{(OwnU8 $id 'Started')=1;(OwnU8 $id 'CreditEntered')=0;(OwnU8 $id 'CreditDone')=0}
 AddNodeB5 $g (PauseB5 65000 (AllB5 $guard));AddNodeB5 $g (New-SetFactNode 65001 (OwnU8 $id 'CreditEntered') 1);AddNodeB5 $g (New-SetFactNode 65002 (OwnU8 $id 'CreditDone') 1)
 foreach($e in $edges){if($e[0] -eq 0){$e[0]=65001}}
 $edges+=,@(0,'Out',65000,'In');$edges+=,@(65000,'Out',65001,'In');$edges+=,@(3,'Out',65002,'In');RebuildB5 $g $edges
 $depot=SaveU8 $g ($id+'_credit');$recipes.Add(@{kind='credit';id=$id;depot=$depot;ids=$ids})
}
$padre=(ReadU8 'research/gig_restoration/family_b7/fixers/raw/base/open_world/fixers/padre/phases/padre.questphase').RootChunk.Graph.Chunk
# Retain exact native threshold/delay/content/message/additive-fact nodes.
# Admission excludes already-earned/partially-delivered tiers instead of replay.
foreach($tier in @($plan.tiers|Where-Object region -eq 'hey')){
 $ids=@($tier.nodes|ForEach-Object id);$g=SliceU8 $padre $ids;$id='Tier'+$tier.threshold
 $guard=[ordered]@{PTFRU8_Heywood_TierRequest=1;(OwnU8 $id 'Permit')=1;(OwnU8 $id 'Entered')=0;PTFRU7_Support_Issued=1}
 foreach($n in @((New-InputNode 65000 'In1'),(PauseB5 65001 (AllB5 $guard)),(New-SetFactNode 65002 (OwnU8 $id 'Entered') 1),(New-SetFactNode 65003 (OwnU8 $id 'Done') 1))){AddNodeB5 $g $n}
 $edges=@($tier.edges);$edges+=,@(65000,'Out',65001,'In');$edges+=,@(65001,'Out',65002,'In');$edges+=,@(65002,'Out',$tier.start,'In')
 $last=@($tier.targets|Where-Object {$target=$_;@($tier.edges|Where-Object {$_[0] -eq $target}).Count -eq 0})
 if($last.Count -ne 1){throw 'Tier endpoint mismatch'};$edges+=,@($last[0],'Out',65003,'In');RebuildB5 $g $edges
 $depot=SaveU8 $g ('tier_'+$tier.threshold);$recipes.Add(@{kind='tier';threshold=$tier.threshold;depot=$depot;ids=$ids;last=$last[0]})
}
# Copy native per-gig marker branches, not a custom marker. The input to a
# selected leaf formerly behind unrelated POI writes is rebased to its own
# admission. Native visited/outcome/discovery and outside triggers are kept.
$maps=@(
 @{id='sts_hey_gle_04';phase=61;ids=@(0,2,14,16,48);activation=48},
 @{id='sts_hey_gle_06';phase=61;ids=@(0,2,24,23,49);activation=49},
 @{id='sts_hey_spr_01';phase=61;ids=@(0,2,47,46,51);activation=51},
 @{id='sts_hey_rey_08';phase=65;ids=@(0,2,55,50,57,56);activation=$null},
 @{id='sts_hey_gle_01';phase=46;ids=@(0,2,7,10,60,50);activation=$null},
 @{id='sts_hey_spr_03';phase=46;ids=@(0,2,24,23,62,52);activation=$null},
 @{id='sts_hey_spr_06';phase=97;ids=@(0,2,3,4,5,6);activation=$null}
)
foreach($m in $maps){
 $og=(Get-QuestNode $padre $m.phase).PhaseGraph.Chunk;$g=SliceU8 $og $m.ids
 $edges=@(EdgesB5 $og|ForEach-Object {$_}|Where-Object {$_[0] -in $m.ids -and $_[2] -in $m.ids})
 if($null -ne $m.activation -and @($edges|Where-Object {$_[2] -eq $m.activation}).Count -eq 0){$edges+=,@(0,'Out',$m.activation,'Active')}
 $guard=[ordered]@{(OwnU8 $m.id 'Request')=1;(OwnU8 $m.id 'MapPermit')=1;(OwnU8 $m.id 'MapEntered')=0;(OwnU8 $m.id 'Fault')=0;PTFRU7_Support_Issued=1}
 AddNodeB5 $g (PauseB5 65000 (AllB5 $guard));AddNodeB5 $g (New-SetFactNode 65001 (OwnU8 $m.id 'MapEntered') 1)
 foreach($e in $edges){if($e[0] -eq 0){$e[0]=65001}};$edges+=,@(0,'Out',65000,'In');$edges+=,@(65000,'Out',65001,'In');RebuildB5 $g $edges
 $depot=SaveU8 $g ($m.id+'_map');$recipes.Add(@{kind='map';id=$m.id;depot=$depot;phase=$m.phase;ids=$m.ids;activation=$m.activation})
}
B71Parser|Out-Null;$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$inventory=@(B72Inventory $game);$collisions=@()
foreach($depot in $boots){$c=B72CollisionCheck $inventory $WorkspaceRoot $depot;if($c.new_id -in $inventory.id){throw 'U8 batch node collision'};$collisions+=@{depot=$depot;node_id=$c.new_id};$inventory+=@{path=$depot;id=$c.new_id;source='U8_batch'}}
$xl=B71Render @($boots);B71Parse $xl|Out-Null;[IO.File]::WriteAllText((Join-Path $out 'TowerContinued_NativeHeywoodU8.archive.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$archive=Join-Path $out 'TowerContinued_NativeHeywoodU8.archive';$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Pack scope mismatch'}
foreach($e in $packed.Files.Values){if(-not $resources.Contains($e.Name)){throw 'Unexpected resource'};$mem=[IO.MemoryStream]::new();try{$e.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -ne $resources[$e.Name]){throw 'Packed readback mismatch'}}finally{$mem.Dispose()}}
$b7=Join-Path $WorkspaceRoot 'build/NativeJeopardyU4/GigFamilyB7.reds';R5Match $b7 '51AD9771C8FB0F18D1BF754CD6A2F78E9BDEE78C08AB3657680E0D22E355A87F'
$text=Get-Content -LiteralPath $b7 -Raw;$anchor='  public func Restore(id: String,overrideHistory: Bool) -> String {'
$insert=@'

    // U8: copied Heywood gameplay is superseded for NEW requests only.
    let u8ids=NativeHeywoodU8.IDs();
    if ArrayContains(u8ids,id) { return "Copied Heywood adapter disabled; use NativeHeywoodU8 on a disposable save."; }

'@
if([regex]::Matches($text,[regex]::Escape($anchor)).Count -ne 1){throw 'B7 anchor mismatch'}
$new=$text.Replace($anchor,$anchor+$insert);if($new.Replace($insert,'') -cne $text){throw 'Unexpected B7 delta'}
[IO.File]::WriteAllText((Join-Path $out 'GigFamilyB7.reds'),$new,[Text.UTF8Encoding]::new($false))
$files=@(
 @{source='build/NativeHeywoodU8/TowerContinued_NativeHeywoodU8.archive';relative='archive/pc/mod/TowerContinued_NativeHeywoodU8.archive';predecessor=$null},
 @{source='build/NativeHeywoodU8/TowerContinued_NativeHeywoodU8.archive.xl';relative='archive/pc/mod/TowerContinued_NativeHeywoodU8.archive.xl';predecessor=$null},
 @{source='redscript/PTFR_NativeHeywoodU8/NativeHeywoodU8.reds';relative='r6/scripts/PTFR_NativeHeywoodU8/NativeHeywoodU8.reds';predecessor=$null},
 @{source='build/NativeHeywoodU8/GigFamilyB7.reds';relative='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds';predecessor=R5Hash $b7}
)
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='BUILT_U8_ENGINE_PENDING';files=$files;recipes=$recipes.ToArray();boots=$boots.ToArray();resources=$resources;source_pins=$pins;native_pins=$nativePins;collisions=$collisions;packed_readback=$true;builder_sha256=R5Hash $PSCommandPath;original_gig_resources_packed=0;native_credit_no_branch='sts_hey_spr_06';production_auto=$false;final_fixer_reward=$false})
'BUILT_U8_ENGINE_PENDING'
