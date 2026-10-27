Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$helper=Get-Content (Join-Path $ws 'tools/build_fresh_gigs_b5.ps1') -Raw
$begin=$helper.IndexOf('function ClearB5(');$end=$helper.IndexOf('$allRoots=@{};')
if($begin -lt 0 -or $end -le $begin){throw 'Graph helper boundary changed'}
. ([scriptblock]::Create($helper.Substring($begin,$end-$begin)))
$prior=Join-Path $ws 'prealpha/consolidation_repair_cr1/candidate_01'
$out=Join-Path $PSScriptRoot 'candidate_02'
if(Test-Path $out){throw 'Use a successor candidate'}
$source=Join-Path $out 'archive_source'
$package=Join-Path $out 'package'
Copy-Item -LiteralPath (Join-Path $prior 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $prior 'package') -Destination $package -Recurse
$before=@{};foreach($p in Get-ChildItem (Join-Path $prior 'archive_source') -File -Recurse){$rel=[IO.Path]::GetRelativePath((Join-Path $prior 'archive_source'),$p.FullName).Replace('/','\');$before[$rel]=(Get-FileHash $p.FullName).Hash}
if($before.Count -ne 1172){throw 'Prior resource count changed'}

# The original MQ040 parent starts after Heroes and twelve hours. Its child sets
# mq040_active=1 as soon as V is outside El Coyote, before any journal progress.
# On the Tower transition, the saved bar setup may be stranded. The observed
# save has the actors present but idle. The active=1 route below reuses these
# actors and skips the native setup spawns. Later facts and journal entries must
# still be untouched; active=1 additionally requires Pepe's service lease idle.
$rel='towercontinued\sidejobs_s29\entries\mq040_biosculpt.questphase'
$path=Join-Path $source $rel
$file=Read-Cr2wFile $path
$graph=$file.RootChunk.Graph.Chunk
$changes=0
foreach($id in @(65003,65004)){
 $node=Get-QuestNode $graph $id
 $condition=$node.Condition.Chunk
 if($condition.Operation.ToString() -cne 'AND'){throw "Entry guard $id changed"}
 $matches=@($condition.Conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Chunk.Type.Chunk.FactName -ceq 'mq040_active'})
 if($matches.Count -ne 1){throw "mq040_active guard count changed at $id"}
 $v=$matches[0].Chunk.Type.Chunk
 if($v.ComparisonType.ToString() -cne 'Equal' -or [int]$v.Value -ne 0){throw "mq040_active comparison changed at $id"}
 $v.ComparisonType=[WolvenKit.RED4.Types.Enums+EComparisonType]::LessOrEqual
 $v.Value=1
 Add-RedHandle $condition.Conditions (New-FactCondition 'mq040_active' 0 'GreaterOrEqual')
 $or=[WolvenKit.RED4.Types.questLogicalCondition]::new();$or.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::OR
 Add-RedHandle $or.Conditions (New-FactCondition 'mq040_active' 0 'Equal')
 $and=[WolvenKit.RED4.Types.questLogicalCondition]::new();$and.Operation=[WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
 Add-RedHandle $and.Conditions (New-FactCondition 'elcoyote_barman_default_on' 0 'Equal')
 Add-RedHandle $and.Conditions (New-FactCondition 'PTFRB0STPEPE_OwnerActive' 0 'Equal')
 Add-RedHandle $or.Conditions $and
 Add-RedHandle $condition.Conditions $or
 $changes++
}
if($changes -ne 2){throw 'Wrong entry guard count'}
Write-Cr2wFile $file $path
$check=(Read-Cr2wFile $path).RootChunk.Graph.Chunk
foreach($id in @(65003,65004)){
 $conditions=(Get-QuestNode $check $id).Condition.Chunk.Conditions
 $a=@($conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Chunk.Type.Chunk.FactName -ceq 'mq040_active'}|ForEach-Object {"$($_.Chunk.Type.Chunk.ComparisonType):$($_.Chunk.Type.Chunk.Value)"}|Sort-Object)
 if(($a -join ',') -cne 'GreaterOrEqual:0,LessOrEqual:1'){throw "Guard readback failed at $id : $($a -join ',')"}
 $or=@($conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questLogicalCondition] -and $_.Chunk.Operation.ToString() -ceq 'OR'})
 if($or.Count -ne 1 -or $or[0].Chunk.Conditions.Count -ne 2){throw "Pepe lease guard readback failed at $id"}
}

$nativeRel='towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq040\mq040_biosculpt.questphase'
$nativePath=Join-Path $source $nativeRel
$nativeFile=Read-Cr2wFile $nativePath
$g=$nativeFile.RootChunk.Graph.Chunk
if(@($g.Nodes|Where-Object {[int]$_.Chunk.Id.ToString() -eq 65000}).Count -ne 0){throw 'MQ040 handoff node already exists'}
$edges=@(EdgesB5 $g|ForEach-Object {$_});$rewired=0
foreach($edge in $edges){if($edge[0] -eq 0 -and $edge[1] -ceq 'Out' -and $edge[2] -eq 3 -and $edge[3] -ceq 'In1'){$edge[2]=65000;$edge[3]='In';$rewired++}}
if($rewired -ne 1){throw 'MQ040 root entry changed'}
AddNodeB5 $g (New-ConditionNode 65000 (New-FactCondition 'mq040_active' 1 'Equal'))
$edges+=,@(65000,'True',4,'In1');$edges+=,@(65000,'False',3,'In1')
RebuildB5 $g $edges
Write-Cr2wFile $nativeFile $nativePath
$nativeCheck=(Read-Cr2wFile $nativePath).RootChunk.Graph.Chunk
$readEdges=@(EdgesB5 $nativeCheck|ForEach-Object {($_ -join ':')})
foreach($needed in @('0:Out:65000:In','65000:True:4:In1','65000:False:3:In1','3:Out1:4:In1')){if($readEdges -cnotcontains $needed){throw "MQ040 branch readback missing $needed"}}

$changed=@($rel,$nativeRel)
$after=@{};foreach($p in Get-ChildItem $source -File -Recurse){$r=[IO.Path]::GetRelativePath($source,$p.FullName).Replace('/','\');$after[$r]=(Get-FileHash $p.FullName).Hash;if($r -cnotin $changed -and $after[$r] -cne $before[$r]){throw "Unchanged resource drift $r"}}
if($after.Count -ne 1172 -or $after[$rel] -ceq $before[$rel] -or $after[$nativeRel] -ceq $before[$nativeRel]){throw 'Resource change/count mismatch'}

$reds=Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
$old=[IO.File]::ReadAllText($reds)
$needle='public static func FactMax5() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }'
$replacement='public static func FactMax5() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }'
if($old.Split(@($needle),[StringSplitOptions]::None).Count -ne 2){throw 'S29 data contract changed'}
$marker='    let items = SideJobDataS29.ItemNames(i);'
$inject=@'
    // The pre-journal El Coyote setup can survive the Tower as idle actors.
    // Only that exact idle-service state may enter the scoped handoff route.
    if i == 5 && qs.GetFactStr("mq040_active") == 1 {
      let barman = qs.GetFactStr("elcoyote_barman_default_on");
      let owner = qs.GetFactStr("PTFRB0STPEPE_OwnerActive");
      ArrayPush(sample.facts, barman); ArrayPush(sample.facts, owner);
      if barman != 0 || owner != 0 {
        if sample.valid { sample.reason = "Raymond setup lease still occupied; deferred."; }
        sample.valid = false;
      }
    }
'@
if($old.Split(@($marker),[StringSplitOptions]::None).Count -ne 2){throw 'S29 read marker changed'}
$updated=$old.Replace($needle,$replacement).Replace($marker,$inject+$marker)
[IO.File]::WriteAllText($reds,$updated,[Text.UTF8Encoding]::new($false))

$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive writer failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1172){throw 'Archive readback failed'}
foreach($e in $packed.Files.Values){$expected=$after[$e.Name];if(!$expected){throw "Unexpected resource $($e.Name)"};$m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};if($hash -cne $expected){throw "Packed resource mismatch $($e.Name)"}}
$files=@(Get-ChildItem $package -File -Recurse)
if($files.Count -ne 51){throw "Package file count $($files.Count)"}
$manifest=[ordered]@{status='RC2_51_FILE_SUCCESSOR_STAGED_LIVE_TEST_PENDING';source_members=1172;changed_resources=@($changed);changed_resource_before=@($changed|ForEach-Object {$before[$_]});changed_resource_after=@($changed|ForEach-Object {$after[$_]});guard_nodes=@(65003,65004);handoff_node=65000;allowed_active=@(0,1);files=@($files|ForEach-Object {@{path=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($manifest|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
@{status=$manifest.status;members=1172;changed_resources=2;files=51}|ConvertTo-Json
