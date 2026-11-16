# Workspace-only native successor. No installation, game launch or save writes.
param([int]$Attempt=1,[switch]$ValidateTypesOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$baseline=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/baseline.json') -Raw|ConvertFrom-Json
$contracts=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'analysis_03/contracts.json') -Raw|ConvertFrom-Json
$out=Join-Path $PSScriptRoot ('archive_{0:d2}' -f $Attempt)
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
function Plain([string]$Path){
 for($p=[IO.FileInfo]::new($Path);$null -ne $p;){
  if($p.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked input refused: $Path"}
  if($p -is [IO.FileInfo]){$p=$p.Directory}else{$p=$p.Parent}
 }
}
function OpenArchive([string]$Path){$a=$null;$code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($Path,$hashService,[ref]$a);if($code.ToString() -cne 'NoError'){throw "Unreadable archive: $Path"};return $a}
function RawBytes($Entry){$s=[IO.MemoryStream]::new();try{$Entry.Extract($s);return ,$s.ToArray()}finally{$s.Dispose()}}
function ByteHash([byte[]]$Bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes))}
function Key([string]$Depot){return [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot)}
function Edges($Graph){
 $owners=@{};$rows=[Collections.Generic.List[object]]::new()
 foreach($nh in $Graph.Nodes){foreach($sh in $nh.Chunk.Sockets){$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($sh.Chunk)]=@([int]::Parse($nh.Chunk.Id.ToString()),$sh.Chunk.Name.ToString())}}
 foreach($nh in $Graph.Nodes){foreach($sh in $nh.Chunk.Sockets){foreach($ch in $sh.Chunk.Connections){$c=$ch.Chunk;if([object]::ReferenceEquals($c.Source.Chunk,$sh.Chunk)){
  $a=$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Source.Chunk)];$b=$owners[[Runtime.CompilerServices.RuntimeHelpers]::GetHashCode($c.Destination.Chunk)];$rows.Add(@($a[0],$a[1],$b[0],$b[1]))
 }}}};return ,$rows.ToArray()
}
function Rebuild($Graph,$Rows){
 foreach($nh in $Graph.Nodes){foreach($sh in $nh.Chunk.Sockets){$sh.Chunk.Connections.Clear()}}
 foreach($e in $Rows){[void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $Graph $e[0]) $e[1]) (Get-QuestSocket (Get-QuestNode $Graph $e[2]) $e[3]))}
}
function Rewire($Copy,$Original){
 Rebuild $Copy (Edges $Original)
 foreach($h in $Copy.Nodes){$n=$h.Chunk;if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){Rewire $n.PhaseGraph.Chunk (Get-QuestNode $Original ([int]::Parse($n.Id.ToString()))).PhaseGraph.Chunk}}
}
function Logic([string]$Operation,$Children){
 $r=[WolvenKit.RED4.Types.questLogicalCondition]::new();$r.Operation=[Enum]::Parse([WolvenKit.RED4.Types.Enums+questLogicalOperation],$Operation)
 foreach($c in $Children){Add-RedHandle $r.Conditions $c};return $r
}
function Fact([string]$Name,[int]$Value){return New-FactCondition $Name $Value ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal)}
function Journal($Definition,$States){
 $all=[Collections.Generic.List[object]]::new()
 foreach($v in $States){
  $p=[WolvenKit.RED4.Types.gameJournalPath]::new();$p.ClassName=[string]$Definition.class;$p.RealPath=[string]$Definition.path;$p.FileEntryIndex=[int32]2
  $t=[WolvenKit.RED4.Types.questJournalEntryState_ConditionType]::new();Set-RedHandleProperty $t 'Path' $p
  $t.State=[Enum]::Parse([WolvenKit.RED4.Types.Enums+gameJournalEntryState],@('Undefined','Inactive','Active','Succeeded','Failed')[[int]$v])
  $c=[WolvenKit.RED4.Types.questJournalCondition]::new();Set-RedHandleProperty $c 'Type' $t;$all.Add($c)
 };return Logic 'OR' $all
}
function HasJournal($Condition){
 if($Condition -is [WolvenKit.RED4.Types.questJournalCondition]){return $true}
 if($Condition -is [WolvenKit.RED4.Types.questLogicalCondition]){foreach($h in $Condition.Conditions){if(HasJournal $h.Chunk){return $true}}}
 return $false
}
function RenameCondition($Condition){
 if($Condition -is [WolvenKit.RED4.Types.questLogicalCondition]){foreach($h in $Condition.Conditions){RenameCondition $h.Chunk}}
 elseif($Condition -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $Condition.Type.Chunk -is [WolvenKit.RED4.Types.questVarComparison_ConditionType]){
  $Condition.Type.Chunk.FactName=$Condition.Type.Chunk.FactName.ToString().Replace('PTFRS23_MQ007_RESUME','PTFRRD1_MQ007_DELIVERY')
 }
}
function RenameGraph($Graph){
 foreach($h in $Graph.Nodes){$n=$h.Chunk
  if($n -is [WolvenKit.RED4.Types.questConditionNodeDefinition] -or $n -is [WolvenKit.RED4.Types.questPauseConditionNodeDefinition]){RenameCondition $n.Condition.Chunk}
  if($n -is [WolvenKit.RED4.Types.questFactsDBManagerNodeDefinition] -and $n.Type.Chunk -is [WolvenKit.RED4.Types.questSetVar_NodeType]){$n.Type.Chunk.FactName=$n.Type.Chunk.FactName.ToString().Replace('PTFRS23_MQ007_RESUME','PTFRRD1_MQ007_DELIVERY')}
  if($n -is [WolvenKit.RED4.Types.questPhaseNodeDefinition] -and $null -ne $n.PhaseGraph -and $null -ne $n.PhaseGraph.Chunk){RenameGraph $n.PhaseGraph.Chunk}
 }
}
function StageGuard($Original,$Contract,[bool]$Late){
 if($Original -isnot [WolvenKit.RED4.Types.questLogicalCondition] -or $Original.Operation.ToString() -cne 'AND'){throw 'Unexpected guard shape'}
 $all=[Collections.Generic.List[object]]::new()
 foreach($h in $Original.Conditions){$c=$h.Chunk
  if(HasJournal $c){continue}
  if($Contract.id -ceq 'mq007_smartgun' -and $c -is [WolvenKit.RED4.Types.questFactsDBCondition]){
   $name=$c.Type.Chunk.FactName.ToString()
   if($name.StartsWith('mq007_') -or $name -ceq 'PTFRS23_MQ007_ModeTalkConfirmed'){continue}
  }
  $copy=$c.DeepCopy()
  if($Contract.id -ceq 'mq007_smartgun' -and $copy -is [WolvenKit.RED4.Types.questObjectCondition] -and $copy.Type.Chunk -is [WolvenKit.RED4.Types.questInventory_ConditionType]){$copy.Type.Chunk.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::Equal}
  $all.Add($copy)
 }
 foreach($p in $Contract.fixed_facts.PSObject.Properties){$all.Add((Fact $p.Name ([int]$p.Value)))}
 foreach($p in $Contract.live_only_facts.PSObject.Properties){$all.Add((Fact $p.Name ([int]$p.Value)))}
 foreach($name in @($Contract.other_owner_receipts)+@($Contract.own_receipts)){
  $value=0;if($Late -and $name -ceq ($Contract.tag+'_Issued')){$value=1};$all.Add((Fact $name $value))
 }
 for($i=0;$i -lt $Contract.journals.Count;$i++){
  $j=$Contract.journals[$i];$states=$j.live
  if($Late -and (($Contract.id -ceq 'mq007_smartgun' -and $i -eq 0) -or ($Contract.id -ceq 'q304_car_retrieval' -and $i -lt 3))){$states=@(2)}
  $all.Add((Journal $j $states))
 }
 foreach($tag in $Contract.handoff){
  $vacant=Logic 'AND' @((Fact ($tag+'_Claimed') 0),(Fact ($tag+'_Entered') 0),(Fact ($tag+'_Request') 0),(Fact ($tag+'_Stop') 1))
  $all.Add((Logic 'OR' @((Fact ($tag+'_Stopped') 1),$vacant)))
 }
 return Logic 'AND' $all
}
if($ValidateTypesOnly){
 foreach($c in $contracts){foreach($j in $c.journals){$null=Journal $j $j.live}}
 Write-Output 'Native journal condition types constructed successfully.';return
}
foreach($r in @($baseline.core_files)+@($baseline.required_files)){$p=Join-Path $baseline.game_root $r.path;Plain $p;if((Get-FileHash -LiteralPath $p).Hash -cne $r.sha256){throw "Baseline changed: $p"}}
New-Item -ItemType Directory -Path $out|Out-Null
$donor=$baseline.archive_source;$source=Join-Path $out 'archive_source';New-Item -ItemType Directory -Path $source|Out-Null
Plain $donor;if(@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked donor'}
$current=OpenArchive (Join-Path $baseline.game_root 'archive/pc/mod/zzzz_PTFR_Combined.archive')
$expected=@{};$old=@{}
foreach($file in Get-ChildItem -LiteralPath $donor -Recurse -File){
 $depot=[IO.Path]::GetRelativePath($donor,$file.FullName).Replace('/','\');$key=Key $depot;$hash=(Get-FileHash -LiteralPath $file.FullName).Hash
 if($expected.ContainsKey($key) -or -not $current.Files.ContainsKey($key) -or (ByteHash (RawBytes $current.Files[$key])) -cne $hash){throw "Donor does not match installed payload: $depot"}
 $dest=Join-Path $source $depot;New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null;[IO.File]::Copy($file.FullName,$dest,$false)
 $expected[$key]=@{depot=$depot;sha256=$hash};$old[$key]=$hash
}
if($expected.Count -ne 1740 -or $current.Files.Count -ne 1740){throw 'Donor inventory incomplete'}
$newOwner='towercontinued\resume_rd1\mq007_delivery_owner.questphase'
$newBoot='towercontinued\resume_rd1\mq007_delivery_boot.questphase'
$heatBoot='towercontinued\sidejobs_s22\moving_heat_boot.questphase'
$changed=@($newOwner,$newBoot,$heatBoot)

# Review exact providers for changed/new depots and all source-qualified native inputs.
$pins=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_02/sources.json') -Raw|ConvertFrom-Json
$watch=@{};foreach($p in $pins){$watch[(Key $p.depot)]=$p};foreach($d in @($newOwner,$newBoot)){$watch[(Key $d)]=$null}
$providers=[Collections.Generic.List[object]]::new();$inventories=[Collections.Generic.List[object]]::new()
$archives=@();foreach($root in @('archive/pc','mods')){$dir=Join-Path $baseline.game_root $root;if(Test-Path -LiteralPath $dir){Plain $dir;if(@(Get-ChildItem -LiteralPath $dir -Recurse -Force -Attributes ReparsePoint).Count){throw 'Linked archive tree'};$archives+=@(Get-ChildItem -LiteralPath $dir -Recurse -File -Filter '*.archive')}}
foreach($file in $archives){
 $stamp=@($file.Length,$file.LastWriteTimeUtc.Ticks);$a=OpenArchive $file.FullName
 foreach($key in $watch.Keys){if($a.Files.ContainsKey($key)){
  $pin=$watch[$key];$h=ByteHash (RawBytes $a.Files[$key])
  if($null -eq $pin -or $file.FullName -cne $pin.archive -or $h -cne $pin.sha256){throw "Unreviewed provider collision: $key in $file"}
  $providers.Add(@{depot=$pin.depot;archive=$file.FullName;sha256=$h})
 }}
 $file.Refresh();if($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]){throw 'Provider changed during inventory'}
 $inventories.Add(@{path=$file.FullName;bytes=$stamp[0];mtime_ticks=$stamp[1];members=$a.Files.Count})
}
if($providers.Count -ne $pins.Count){throw 'Missing reviewed provider'}

$owner=Read-Cr2wFile (Join-Path $donor 'towercontinued/sidejobs_s23/base_a_v2/mq007_resume_owner.questphase')
$original=$owner.RootChunk.Graph.Chunk;$copy=$original.DeepCopy();Rewire $copy $original;Set-RedHandleProperty $owner.RootChunk 'Graph' $copy
$delivery=(Get-QuestNode $copy 5).PhaseGraph.Chunk;$edges=Edges $delivery
if(@($edges|Where-Object {$_[0] -eq 0 -and $_[2] -eq 32}).Count -ne 1){throw 'Delivery entry changed'}
$rows=[Collections.Generic.List[object]]::new();foreach($e in $edges){if($e[0] -ne 0){$rows.Add($e)}}
$rows.Add(@(0,'Out',11,'Active'));$rows.Add(@(0,'Out',72,'In'));Rebuild $delivery $rows
Write-Cr2wFile $owner (Join-Path $source $newOwner)

$boot=Read-Cr2wFile (Join-Path $donor 'towercontinued/sidejobs_s23/base_a_v2/mq007_resume_boot.questphase')
$original=$boot.RootChunk.Graph.Chunk;$g=$original.DeepCopy();Rewire $g $original;Set-RedHandleProperty $boot.RootChunk 'Graph' $g;RenameGraph $g
foreach($id in @(1001,1002,1007,1008,1100)){$n=Get-QuestNode $g $id;Set-RedHandleProperty $n 'Condition' (StageGuard $n.Condition.Chunk $contracts[0] ($id -in @(1007,1008,1100)))}
Set-RedHandleProperty (Get-QuestNode $g 1004) 'Condition' (Journal $contracts[0].journals[0] @(1,4))
$phase=Get-QuestNode $g 21;$phase.PhaseResource=[Activator]::CreateInstance($phase.GetType().GetProperty('PhaseResource').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($newOwner)))
$activate=(Get-QuestNode $g 1005).DeepCopy();$activate.Id=[uint16]60000
foreach($s in $activate.Sockets){$s.Chunk.Connections.Clear()}
$activate.Type.Chunk.Path.Chunk.RealPath=[string]$contracts[0].journals[1].path;$activate.Type.Chunk.Path.Chunk.ClassName=[string]$contracts[0].journals[1].class
$rows=[Collections.Generic.List[object]]::new();$found=0
foreach($e in (Edges $g)){if($e[0] -eq 1101 -and $e[2] -eq 21){$rows.Add(@(1101,$e[1],60000,'Active'));$rows.Add(@(60000,'Out',21,$e[3]));$found++}else{$rows.Add($e)}}
if($found -ne 1){throw 'Delivery owner entry changed'};Add-RedHandle $g.Nodes $activate;Rebuild $g $rows
Write-Cr2wFile $boot (Join-Path $source $newBoot)

$heat=Read-Cr2wFile (Join-Path $donor $heatBoot)
# Existing node/field identities and graph edges are retained. Only conditions expand.
foreach($id in @(2,3,9)){$n=Get-QuestNode $heat.RootChunk.Graph.Chunk $id;$oldCondition=$n.Condition.Chunk
 $earned=StageGuard $oldCondition $contracts[1] ($id -eq 9)
 Set-RedHandleProperty $n 'Condition' (Logic 'OR' @($oldCondition.DeepCopy(),$earned))
}
Write-Cr2wFile $heat (Join-Path $source $heatBoot)

foreach($depot in $changed){
 $path=Join-Path $source $depot;$decoded=Read-Cr2wFile $path
 Export-Cr2wJson $decoded (Join-Path $out (([IO.Path]::GetFileName($depot))+'.json'))
 $expected[(Key $depot)]=@{depot=$depot;sha256=(Get-FileHash -LiteralPath $path).Hash}
}
$target=Join-Path $out 'zzzz_PTFR_Combined.archive';$stream=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$packed=OpenArchive $target;if($packed.Files.Count -ne $expected.Count){throw 'Packed inventory mismatch'}
$members=@(foreach($entry in $packed.Files.GetEnumerator()){$p=$expected[$entry.Key];if($null -eq $p -or (ByteHash (RawBytes $entry.Value)) -cne $p.sha256){throw 'Packed readback mismatch'}
 @{depot=$p.depot;key=$entry.Key.ToString();sha256=$p.sha256;unchanged=($old.ContainsKey($entry.Key) -and $old[$entry.Key] -ceq $p.sha256)}
})
@{status='PACKED_SEMANTIC_ASSESSMENT_PENDING';archive_sha256=(Get-FileHash -LiteralPath $target).Hash;members=$members;providers=$providers.ToArray();archive_inventory=$inventories.ToArray();changed=$changed;game_writes=0;save_writes=0;contracts_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'analysis_03/contracts.json')).Hash;builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Packed and read back $($members.Count) members; semantic and fixture qualification pending."
