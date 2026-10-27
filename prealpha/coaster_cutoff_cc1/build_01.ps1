Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/skippy_ambient_sc3/candidate_02'
$out=Join-Path $PSScriptRoot 'candidate_01'
if(Test-Path -LiteralPath $out){throw 'Preserve candidate; use successor'}
$source=Join-Path $out 'archive_source'
$package=Join-Path $out 'package'
$prior=Get-Content -LiteralPath (Join-Path $base 'install_manifest_01.json') -Raw|ConvertFrom-Json -Depth 80
if($prior.full_package_count -ne 51 -or $prior.archive_members -ne 1185){throw 'SC3 baseline drift'}
Copy-Item -LiteralPath (Join-Path $base 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
$before=@{}
foreach($f in Get-ChildItem -LiteralPath $source -File -Recurse){$r=[IO.Path]::GetRelativePath($source,$f.FullName).Replace('/','\');$before[$r]=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash}
if($before.Count -ne 1185){throw 'SC3 source count drift'}
$entryRel='towercontinued\sidejobs_s30\entries\mq006_rollercoaster.questphase'
$entryPath=Join-Path $source $entryRel
$entry=Read-Cr2wFile $entryPath
foreach($id in @(65003,65004)){
 $node=Get-QuestNode $entry.RootChunk.Graph.Chunk $id
 $condition=$node.Condition.Chunk
 if($condition.Operation.ToString() -cne 'AND'){throw "Guard $id changed"}
 if(@($condition.Conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Chunk.Type.Chunk.FactName -ceq 'q105_done'}).Count){throw "Cutoff already present $id"}
 Add-RedHandle $condition.Conditions (New-FactCondition 'q105_done' 0 'Equal')
}
Write-Cr2wFile $entry $entryPath
$read=Read-Cr2wFile $entryPath
foreach($id in @(65003,65004)){
 $conditions=(Get-QuestNode $read.RootChunk.Graph.Chunk $id).Condition.Chunk.Conditions
 $cut=@($conditions|Where-Object {$_.Chunk -is [WolvenKit.RED4.Types.questFactsDBCondition] -and $_.Chunk.Type.Chunk.FactName -ceq 'q105_done'})
 if($cut.Count -ne 1 -or $cut[0].Chunk.Type.Chunk.ComparisonType.ToString() -cne 'Equal' -or [int]$cut[0].Chunk.Type.Chunk.Value -ne 0){throw "Cutoff readback $id"}
}
$script=Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
$old=[IO.File]::ReadAllText($script)
$pairs=@(
 @('public static func FactNames0() -> array<String> { return ["mq006", "mq006_done", "mq006_roller_coaster_fixed", "mq006_enable_repeatable_rollercoaster", "mq006_ride_no_quest", "PTFRWORLD_Coaster_QuestOwns", "PTFRWORLD_Coaster_Registered"]; }','public static func FactNames0() -> array<String> { return ["mq006", "mq006_done", "mq006_roller_coaster_fixed", "mq006_enable_repeatable_rollercoaster", "mq006_ride_no_quest", "PTFRWORLD_Coaster_QuestOwns", "PTFRWORLD_Coaster_Registered", "q105_done"]; }'),
 @('public static func FactMin0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0]; }','public static func FactMin0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0]; }'),
 @('public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 1, 0, 0]; }','public static func FactMax0() -> array<Int32> { return [0, 0, 0, 0, 1, 0, 0, 0]; }')
)
foreach($pair in $pairs){if($old.Split(@($pair[0]),[StringSplitOptions]::None).Count -ne 2){throw ('S30 unique table mismatch '+$pair[0])};$old=$old.Replace($pair[0],$pair[1])}
[IO.File]::WriteAllText($script,$old,[Text.UTF8Encoding]::new($false))
$after=@{}
foreach($f in Get-ChildItem -LiteralPath $source -File -Recurse){$r=[IO.Path]::GetRelativePath($source,$f.FullName).Replace('/','\');$after[$r]=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash;if($r -cne $entryRel -and $after[$r] -cne $before[$r]){throw ('Unexpected source mutation '+$r)}}
if($after.Count -ne 1185 -or $after[$entryRel] -ceq $before[$entryRel]){throw 'Entry mutation count'}
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive writer failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1185){throw 'Archive read/count'}
$changes=@()
foreach($e in $packed.Files.Values){$mem=[IO.MemoryStream]::new();try{$e.Extract($mem);$digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()};if($digest -cne (Get-FileHash -LiteralPath (Join-Path $source $e.Name) -Algorithm SHA256).Hash){throw ('Archive mismatch '+$e.Name)};if($digest -cne $before[$e.Name]){$changes+=,$e.Name}}
if($changes.Count -ne 1 -or $changes[0] -cne $entryRel){throw ('Unexpected archive delta '+($changes -join ','))}
if(@(Get-ChildItem -LiteralPath $package -File -Recurse).Count -ne 51){throw 'Package path count'}
$result=[ordered]@{status='CC1_STAGED_NOT_INSTALLED';base='SC3';source_members=1185;changed_member=$entryRel;changed_member_sha256=$after[$entryRel];archive_sha256=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash;script_sha256=(Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash;package_paths=51;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'build_01.json'),($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
