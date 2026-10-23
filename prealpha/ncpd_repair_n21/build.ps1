param([string]$Revision='n21_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$WorkspaceRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $WorkspaceRoot 'tools/shark_b7_2_helpers.ps1')
$helper=Get-Content (Join-Path $WorkspaceRoot 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
if($Revision -cnotmatch '^n21_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Preserve existing build'}
New-Item -ItemType Directory $out,(Join-Path $out 'source'),(Join-Path $out 'readback') | Out-Null
$oldRoot=Join-Path $WorkspaceRoot 'prealpha/ncpd_scanners_n2/build/n2_05'
$oldFile=Join-Path $oldRoot 'build.json'
if((Get-FileHash $oldFile).Hash -cne 'DE4A625A6EE5158D5DEB17B4E0A61229F012566D64207680BC302AA8C17EF4AF'){throw 'N2 identity changed'}
$old=Get-Content $oldFile -Raw|ConvertFrom-Json
$cat=Get-Content (Join-Path $WorkspaceRoot 'research/ncpd_scanners_n2/catalog_v2.json') -Raw|ConvertFrom-Json -Depth 100
$initial=@{'ma_wbr_hil_02'='ma_wbr_hil_02_start';'ma_wbr_hil_03'='ma_wbr_hil_03_start';'ma_wbr_hil_04'='ma_wbr_hil_04_start';'ma_std_rcr_07'='ma_rcr_07_start'}
$factless=@('ma_cct_cpz_16','ma_wbr_nok_05');$selected=@($initial.Keys)+$factless
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$ep=Get-Content (Join-Path $WorkspaceRoot 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($inventory.id)+@($ep.Data.RootChunk.graph.Data.nodes.Data.id)
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$rows=@()
foreach($rel in @('prealpha/ncpd_repair_n21/build.ps1','prealpha/ncpd_repair_n21/ScannerRepairN21.reds','prealpha/ncpd_scanners_n2/build/n2_05/build.json','research/ncpd_scanners_n2/catalog_v2.json','tools/build_phase2a.ps1','tools/build_fresh_gigs_b5.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','research/q307_extracted/json/ep1/quest/ep1.quest.json')){$pins[$rel]=(Get-FileHash (Join-Path $WorkspaceRoot $rel)).Hash}
foreach($id in $selected|Sort-Object){
 $spec=@($old.activities|Where-Object key -ceq $id)[0]
 $source=Join-Path $oldRoot ('source/'+$spec.depot)
 if((Get-FileHash $source).Hash -cne $old.resources.($spec.depot)){throw 'Donor changed'}
 $pins[[IO.Path]::GetRelativePath($WorkspaceRoot,$source).Replace('\','/')]=(Get-FileHash $source).Hash
 $file=Read-Cr2wFile $source;$root=$file.RootChunk;$outer=$root.Graph.Chunk;$g=(Get-QuestNode $outer 100).PhaseGraph.Chunk
 $tag='PTFRN21_'+$id;$pairs=[ordered]@{}
 foreach($p in $spec.guard_equal.PSObject.Properties){$pairs[$p.Name]=$p.Value}
 if($initial.ContainsKey($id)){$pairs[$initial[$id]]=1}else{$pairs['PTFRN2_'+$id+'_Permit']=0}
 Set-RedHandleProperty (Get-QuestNode $outer 2) Condition (AllB5 $pairs)
 Set-RedHandleProperty (Get-QuestNode $g 1000) Condition (AllB5 $pairs)
 (Get-QuestNode $outer 1).Type.Chunk.FactName=$tag+'_Ready'
 (Get-QuestNode $g 1002).Type.Chunk.FactName=$tag+'_Refused'
 $response=[WolvenKit.RED4.Types.questLogicalCondition]::new();$response.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 foreach($suffix in @('_Permit','_Denied')){Add-RedHandle $response.Conditions (New-FactCondition ($tag+$suffix) 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))}
 if($id -in $factless){
  (Get-QuestNode $g 1003).Type.Chunk.FactName=$tag+'_Request'
  Set-RedHandleProperty (Get-QuestNode $g 1004) Condition $response
  Set-RedHandleProperty (Get-QuestNode $g 1005) Condition (New-FactCondition ($tag+'_Permit') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
 }else{
  $permitCondition=New-FactCondition ($tag+'_Permit') 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)
  foreach($n in @((New-SetFactNode 1003 ($tag+'_Request') 1),(PauseB5 1004 $response),(New-ConditionNode 1005 $permitCondition))){AddNodeB5 $g $n}
  $ad=$spec.admission_edge
  $ee=@(EdgesB5 $g|ForEach-Object {$_}|Where-Object {-not($_[0] -eq $ad[0] -and $_[1] -ceq $ad[1] -and $_[2] -eq 1000)})
  $ee+=,@($ad[0],$ad[1],1003,'In');$ee+=,@(1003,'Out',1004,'In');$ee+=,@(1004,'Out',1005,'In');$ee+=,@(1005,'True',1000,'In');$ee+=,@(1005,'False',1002,'In')
  RebuildB5 $g $ee
 }
 # Retain N2's Issued fact as the common one-shot owner record. Never clear it.
 if((Get-QuestNode $g 1001).Type.Chunk.FactName -cne ('PTFRN2_'+$id+'_Issued')){throw 'Ownership mismatch'}
 $depot='towercontinued\ncpd_repair_n21\'+$id+'.questphase';$crc=B72Id ($depot+':1')
 if($crc -in $used -or $crc -ne (B72IdIndependent ($depot+':1'))){throw 'Injection identity collision'}
 $used+=,$crc;$boots+=,$depot
 $raw=Join-Path $out ('source/'+$depot);Write-Cr2wFile $file $raw;Export-Cr2wJson (Read-Cr2wFile $raw) (Join-Path $out ('readback/'+$id+'.json'))
 $resources[$depot]=(Get-FileHash $raw).Hash
 $rows+=,@{key=$id;depot=$depot;guard_equal=$pairs;injection_id=$crc;mode=if($initial.ContainsKey($id)){1}else{2};native_depot=$spec.native_depot;parent=$spec.parent;donor=$spec.depot}
}
# Generate the bounded runtime table from exactly the already-installed N2 set.
$data="`npublic abstract class ScannerDataN21 {`n public static func Count() -> Int32 { return 154; }`n"
$activities=@($old.activities|Sort-Object key)
$data+=" public static func ID(i: Int32) -> String { switch i {`n"
for($i=0;$i -lt $activities.Count;$i++){$data+='  case '+$i+': return "'+$activities[$i].key+'";'+"`n"};$data+=" } return `"`"; }`n"
$data+=" public static func Mode(i: Int32) -> Int32 { switch i {`n"
for($i=0;$i -lt $activities.Count;$i++){ $id=$activities[$i].key;if($id -in $selected){$mode=if($initial.ContainsKey($id)){1}else{2};$data+='  case '+$i+': return '+$mode+';'+"`n"}};$data+=" } return 0; }`n"
$data+=" public static func InitFact(i: Int32) -> String { switch i {`n"
for($i=0;$i -lt $activities.Count;$i++){ $id=$activities[$i].key;if($initial.ContainsKey($id)){$data+='  case '+$i+': return "'+$initial[$id]+'";'+"`n"}};$data+=" } return `"`"; }`n"
$data+=" public static func Finish(i: Int32) -> array<String> { let names: array<String>; switch i {`n"
$dataset=@()
for($i=0;$i -lt $activities.Count;$i++){
 $id=$activities[$i].key;$c=@($cat.rows|Where-Object key -ceq $id)[0];$finish=@($c.finish_facts)
 if($id -in @('ma_wat_lch_14','ma_wat_lch_15')){$finish=@($finish|Where-Object {$_ -cne 'ma_wat_lch_14_finished'})}
 if($finish.Count){$data+='  case '+$i+': ';foreach($f in $finish){$data+='ArrayPush(names,"'+$f+'"); '};$data+="break;`n"}
 $dataset+=,@{index=$i;key=$id;finish=$finish;mode=if($initial.ContainsKey($id)){1}elseif($id -in $factless){2}else{0};init_fact=if($initial.ContainsKey($id)){$initial[$id]}else{''}}
};$data+=" } return names; }`n}`n"
$script=Join-Path $out 'ScannerRepairN21.reds'
[IO.File]::WriteAllText($script,((Get-Content (Join-Path $PSScriptRoot 'ScannerRepairN21.reds') -Raw)+$data),[Text.UTF8Encoding]::new($false))
$archive=Join-Path $out 'TowerContinued_NCPD_N21.archive';$xl=B71Render $boots;B71Parse $xl|Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError' -or $packed.Files.Count -ne 6){throw 'Archive scope mismatch'}
foreach($entry in $packed.Files.Values){$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray())) -cne $resources[$entry.Name]){throw 'Packed mismatch'}}finally{$mem.Dispose()}}
$files=@();foreach($name in @('TowerContinued_NCPD_N21.archive','TowerContinued_NCPD_N21.archive.xl','ScannerRepairN21.reds')){$files+=,@{relative=if($name -like '*.reds'){'r6/scripts/TowerContinued_NCPD_N21/'+$name}else{'archive/pc/mod/'+$name};sha256=(Get-FileHash (Join-Path $out $name)).Hash}}
$result=@{status='BUILT_N21_LIVE_PENDING';files=$files;resources=$resources;activities=$rows;dataset=$dataset;source_pins=$pins;installed_injections=$inventory;boots=$boots;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=1;official_overrides=@();mod_override='';game_writes=0;save_writes=0;scope='Owned N2 POI activation; six disjoint supplemental native owners. No generic partial-progress restart or native fact reset.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=(Get-FileHash (Join-Path $out 'build.json')).Hash}|ConvertTo-Json
