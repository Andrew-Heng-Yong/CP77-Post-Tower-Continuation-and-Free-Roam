Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$prior=Join-Path $ws 'prealpha/sidejobs_s30/candidate_02'
$out=Join-Path $PSScriptRoot 'candidate_01'
if(Test-Path $out){throw 'Use a successor candidate'}
$source=Join-Path $out 'archive_source'
$package=Join-Path $out 'package'
Copy-Item -LiteralPath (Join-Path $prior 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $prior 'package') -Destination $package -Recurse
$before=@{};foreach($p in Get-ChildItem (Join-Path $prior 'archive_source') -File -Recurse){$rel=[IO.Path]::GetRelativePath((Join-Path $prior 'archive_source'),$p.FullName).Replace('/','\');$before[$rel]=(Get-FileHash $p.FullName).Hash}
if($before.Count -ne 1172){throw 'Prior resource count changed'}

# The original MQ040 parent starts after Heroes and twelve hours. Its child sets
# mq040_active=1 as soon as V is outside El Coyote, before any journal progress.
# On the Tower transition that original owner is killed, leaving this setup
# latch in otherwise fresh saves. Admit 0 or 1 only; all later facts and journal
# entries remain required to be untouched.
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
 $changes++
}
if($changes -ne 2){throw 'Wrong entry guard count'}
Write-Cr2wFile $file $path
$check=(Read-Cr2wFile $path).RootChunk.Graph.Chunk
foreach($id in @(65003,65004)){
 $conditions=(Get-QuestNode $check $id).Condition.Chunk.Conditions
 $a=@($conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Chunk.Type.Chunk.FactName -ceq 'mq040_active'}|ForEach-Object {"$($_.Chunk.Type.Chunk.ComparisonType):$($_.Chunk.Type.Chunk.Value)"}|Sort-Object)
 if(($a -join ',') -cne 'GreaterOrEqual:0,LessOrEqual:1'){throw "Guard readback failed at $id : $($a -join ',')"}
}
$after=@{};foreach($p in Get-ChildItem $source -File -Recurse){$r=[IO.Path]::GetRelativePath($source,$p.FullName).Replace('/','\');$after[$r]=(Get-FileHash $p.FullName).Hash;if($r -cne $rel -and $after[$r] -cne $before[$r]){throw "Unchanged resource drift $r"}}
if($after.Count -ne 1172 -or $after[$rel] -ceq $before[$rel]){throw 'Resource change/count mismatch'}

$reds=Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
$old=[IO.File]::ReadAllText($reds)
$needle='public static func FactMax5() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }'
$replacement='public static func FactMax5() -> array<Int32> { return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; }'
if($old.Split(@($needle),[StringSplitOptions]::None).Count -ne 2){throw 'S29 data contract changed'}
[IO.File]::WriteAllText($reds,$old.Replace($needle,$replacement),[Text.UTF8Encoding]::new($false))

$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive writer failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1172){throw 'Archive readback failed'}
foreach($e in $packed.Files.Values){$expected=$after[$e.Name];if(!$expected){throw "Unexpected resource $($e.Name)"};$m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};if($hash -cne $expected){throw "Packed resource mismatch $($e.Name)"}}
$files=@(Get-ChildItem $package -File -Recurse)
if($files.Count -ne 51){throw "Package file count $($files.Count)"}
$manifest=[ordered]@{status='RC1_51_FILE_SUCCESSOR_STAGED';source_members=1172;changed_resource=$rel;changed_resource_before=$before[$rel];changed_resource_after=$after[$rel];guard_nodes=@(65003,65004);allowed_active=@(0,1);files=@($files|ForEach-Object {@{path=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($manifest|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
@{status=$manifest.status;members=1172;changed_resources=1;files=51}|ConvertTo-Json
