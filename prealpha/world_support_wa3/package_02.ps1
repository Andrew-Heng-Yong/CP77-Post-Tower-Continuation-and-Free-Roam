# Pack the approved WA3 controller cohort without modifying existing WA2 resources.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/world_actions_wa2/candidate_01'
$candidate=Join-Path $PSScriptRoot 'candidate_02'
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package'
$newSource=Join-Path $candidate 'source'
$baselineSource=Join-Path $candidate 'script_source/PTFR_RestorationBaseline.reds'
$compiled=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json -Depth 30
if($compiled.status -cne 'PASS' -or $compiled.source_count -lt 1 -or (Get-FileHash -LiteralPath $baselineSource).Hash -cne $compiled.candidate_sha256){throw 'Fresh complete-input Baseline compilation missing or drifted'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package)){throw 'Preserve candidate package; use successor'}
$cohortPath=Join-Path $candidate 'cohort_proof_01.json'
$cohort=Get-Content -LiteralPath $cohortPath -Raw|ConvertFrom-Json -Depth 80
if($cohort.status -cne 'WA3_SOURCE_COHORT_READY' -or @($cohort.resources).Count -lt 1){throw 'Approved WA3 source cohort is not ready'}
$approved=@{}
foreach($r in $cohort.resources){
 $depot=$r.depot.Replace('/','\')
 if($depot -notmatch '^(towercontinued\\world_support_wa3\\[a-zA-Z0-9_\\-]+\.(questphase|streamingblock)|base\\worlds\\03_night_city\\_compiled\\default\\(ep1\\)?quest_[a-f0-9]{16}\.streamingsector)$' -or $approved.ContainsKey($depot) -or $r.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw ('Invalid/duplicate approved depot '+$depot)}
 $approved[$depot]=$r.sha256
}
$blockRows=@($cohort.resources|Where-Object {$_.depot.EndsWith('.streamingblock')})
$streamingBlocks=@()
if($blockRows.Count){
 if(!$cohort.PSObject.Properties['streaming_blocks']){throw 'New private blocks need explicit XL registrations'}
 $streamingBlocks=@($cohort.streaming_blocks)
 if($streamingBlocks.Count -ne $blockRows.Count -or @(Compare-Object ($streamingBlocks|Sort-Object) ($blockRows.depot|Sort-Object)).Count){throw 'Streaming block registration inventory mismatch'}
}
$sectorRows=@($cohort.resources|Where-Object {$_.depot.EndsWith('.streamingsector')})
$sectorBindings=@()
if($sectorRows.Count){
 if(!$cohort.PSObject.Properties['sector_bindings']){throw 'Private sectors need explicit engine-prefab bindings'}
 $sectorBindings=@($cohort.sector_bindings)
 if($sectorBindings.Count -ne $sectorRows.Count -or @($sectorBindings.depot|Select-Object -Unique).Count -ne $sectorRows.Count){throw 'Sector binding inventory mismatch'}
 foreach($binding in $sectorBindings){
  if($binding.prefab_ref -notlike '$/*/world_support_wa3/*'){throw 'Private sector prefab is outside WA3 namespace'}
  $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash([string]$binding.prefab_ref)
  $parent=[IO.Path]::GetDirectoryName([string]$binding.depot)
  if($parent -cnotin @('base\worlds\03_night_city\_compiled\default','base\worlds\03_night_city\_compiled\default\ep1')){throw 'Private sector namespace changed'}
  $expected=$parent+'\quest_'+$hash.ToString('x16')+'.streamingsector'
  if($binding.node_ref_hash -cne $hash.ToString() -or $binding.depot -cne $expected -or !$approved.ContainsKey($expected)){throw 'Private sector does not match exact engine prefab hash'}
 }
}
$newFiles=@(Get-ChildItem -LiteralPath $newSource -Recurse -File|Sort-Object FullName)
if($newFiles.Count -ne $approved.Count){throw 'New source inventory differs from approved cohort'}
$newRows=@()
foreach($f in $newFiles){
 $rel=[IO.Path]::GetRelativePath($newSource,$f.FullName).Replace('/','\')
 if(!$approved.ContainsKey($rel) -or (Get-FileHash -LiteralPath $f.FullName).Hash -cne $approved[$rel]){throw ('Unapproved serialized source '+$rel)}
 $newRows+=@{depot=$rel;sha256=$approved[$rel]}
}
$baseManifest=Get-Content -LiteralPath (Join-Path $base 'install_manifest_01.json') -Raw|ConvertFrom-Json -Depth 80
if($baseManifest.full_package_count -ne 51 -or $baseManifest.archive_members -ne 1212){throw 'WA2 baseline scope drift'}
foreach($f in $baseManifest.package_files){
 if((Get-FileHash -LiteralPath (Join-Path $game $f.path)).Hash -cne $f.after -or (Get-FileHash -LiteralPath (Join-Path $base ('package/'+$f.path))).Hash -cne $f.after){throw ('WA2 installed/package baseline changed '+$f.path)}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function RawHash($entry){$memory=[IO.MemoryStream]::new();try{$entry.Extract($memory);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}}
$oldArc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive((Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'),$hs,[ref]$oldArc).ToString() -cne 'NoError'){throw 'WA2 archive unreadable'}
$oldIndex=@{};$oldKeys=@{}
foreach($e in $oldArc.Files.Values){if($oldIndex.ContainsKey($e.Name)){throw 'Duplicate WA2 depot'};$oldIndex[$e.Name]=RawHash $e;$oldKeys[$e.Key.ToString()]=$e.Name}
if($oldIndex.Count -ne 1212){throw 'WA2 archive member count drift'}
$newKeys=@{}
foreach($r in $newRows){
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.depot).ToString()
 if($oldIndex.ContainsKey($r.depot) -or $oldKeys.ContainsKey($key) -or $newKeys.ContainsKey($key)){throw ('New controller aliases an existing depot/hash '+$r.depot)}
 $newKeys[$key]=$r.depot
}
$rawBase=Join-Path $base 'archive_source';$rawFiles=@(Get-ChildItem -LiteralPath $rawBase -Recurse -File)
if($rawFiles.Count -ne 1212){throw 'WA2 raw source count drift'}
foreach($f in $rawFiles){$rel=[IO.Path]::GetRelativePath($rawBase,$f.FullName);if(!$oldIndex.ContainsKey($rel) -or (Get-FileHash -LiteralPath $f.FullName).Hash -cne $oldIndex[$rel]){throw ('WA2 archive/source disagreement '+$rel)}}
Copy-Item -LiteralPath $rawBase -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
foreach($r in $newRows){$target=Join-Path $source $r.depot;[void][IO.Directory]::CreateDirectory((Split-Path $target -Parent));Copy-Item -LiteralPath (Join-Path $newSource $r.depot) -Destination $target}
$memberCount=1212+$newRows.Count
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne $memberCount){throw 'WA3 archive read/count failed'}
$readback=@();$unchanged=0;$added=0
foreach($e in $packed.Files.Values){
 $digest=RawHash $e
 if($digest -cne (Get-FileHash -LiteralPath (Join-Path $source $e.Name)).Hash){throw ('Packed source mismatch '+$e.Name)}
 if($oldIndex.ContainsKey($e.Name)){if($digest -cne $oldIndex[$e.Name]){throw ('WA2 resource changed '+$e.Name)};$unchanged++}elseif($approved.ContainsKey($e.Name) -and $approved[$e.Name] -ceq $digest){$added++}else{throw ('Unexpected new resource '+$e.Name)}
 $readback+=@{depot=$e.Name;sha256=$digest}
}
if($unchanged -ne 1212 -or $added -ne $newRows.Count){throw 'Resource preservation count failed'}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2){throw 'XL structure drift'}
$phaseRows=@($newRows|Where-Object {$_.depot.EndsWith('.questphase')})
if(!$phaseRows.Count){throw 'No approved owner phases to register'}
$entries=''
foreach($r in $phaseRows){
 if($oldXL.Contains($r.depot)){throw ('Duplicate XL registration '+$r.depot)}
 $entries+="    - path: $($r.depot)`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
}
$blockEntries=''
foreach($depot in $streamingBlocks){if($oldXL.Contains($depot)){throw 'Duplicate streaming block registration'};$blockEntries+="    - $depot`n"}
if($oldXL.Split('localization:').Count -ne 2){throw 'XL localization boundary drift'}
[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entries+'streaming:').Replace('localization:',$blockEntries+'localization:'),[Text.UTF8Encoding]::new($false))
$newXL=[IO.File]::ReadAllText($xl)
$restoredXL=$newXL.Replace($entries,'');if($blockEntries){$restoredXL=$restoredXL.Replace($blockEntries,'')}
if($restoredXL -cne $oldXL){throw 'XL changed beyond new registrations'}
foreach($r in $phaseRows){if([regex]::Matches($newXL,[regex]::Escape('    - path: '+$r.depot)+"\r?\n").Count -ne 1){throw ('XL registration is not unique '+$r.depot)}}
foreach($depot in $streamingBlocks){if([regex]::Matches($newXL,[regex]::Escape('    - '+$depot)+"\r?\n").Count -ne 1){throw 'Streaming block is not registered exactly once'}}
Copy-Item -LiteralPath $baselineSource -Destination (Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds')
if(@(Get-ChildItem -LiteralPath $package -File -Recurse).Count -ne 51){throw 'Full package path count'}
$expected=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds')
$changed=@();foreach($f in $baseManifest.package_files){if((Get-FileHash -LiteralPath (Join-Path $package $f.path)).Hash -cne $f.after){$changed+=,$f.path}}
if(@(Compare-Object ($expected|Sort-Object) ($changed|Sort-Object)).Count){throw 'Unexpected install file changes'}
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Recurse -Filter '*.archive' -File)
$dependencyPath=Join-Path $PSScriptRoot 'dependencyqueries_02.json'
$dependencies=@(Get-Content -LiteralPath $dependencyPath -Raw|ConvertFrom-Json -Depth 60)
if(!$dependencies.Count){throw 'Empty native dependency inventory'}
$dependencyKeys=@{}
foreach($dependency in $dependencies){
 $depot=$dependency.depot.Replace('/','\');$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()
 if($dependencyKeys.ContainsKey($key) -or $dependency.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Invalid/duplicate native dependency'}
 $dependencyKeys[$key]=$dependency
}
$hits=@();$archivePins=@();$dependencyHits=@()
foreach($file in $archives){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable mod archive '+$file.Name)}
 foreach($e in $arc.Files.Values){if($newKeys.ContainsKey($e.Key.ToString())){$hits+=@{archive=$file.Name;depot=$e.Name;new_resource=$newKeys[$e.Key.ToString()]}}}
 foreach($key in $dependencyKeys.Keys){
  if($arc.Files.ContainsKey([uint64]$key)){
   $e=$arc.Files[[uint64]$key];$dependencyHits+=@{depot=$dependencyKeys[$key].depot;archive=$file.FullName;sha256=RawHash $e}
  }
 }
 if($file.FullName.StartsWith((Join-Path $game 'archive/pc/mod').Replace('/','\')+'\',[StringComparison]::OrdinalIgnoreCase)){$archivePins+=@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}}
}
if($hits.Count){throw 'New WA3 resource collision'}
foreach($dependency in $dependencies){
 $found=@($dependencyHits|Where-Object depot -ceq $dependency.depot)
 if(!$found.Count){throw ('Missing native dependency '+$dependency.depot)}
 if(@($found|Where-Object {$_.archive -like '*\archive\pc\mod\*'}).Count){throw ('Native dependency overridden by mod '+$dependency.depot)}
 if($dependency.PSObject.Properties['expected_archive']){
  $winner=@($found|Where-Object {[IO.Path]::GetFileName($_.archive) -ceq $dependency.expected_archive})
  if($winner.Count -ne 1 -or $winner[0].sha256 -cne $dependency.sha256){throw ('Expected native winner changed '+$dependency.depot)}
  foreach($other in $found){
   if($other.sha256 -ceq $dependency.sha256){continue}
   if(!($dependency.expected_archive -like 'ep1_*' -and [IO.Path]::GetFileName($other.archive) -like 'basegame_*')){throw ('Unreviewed competing native winner '+$dependency.depot)}
  }
 }elseif($found.Count -ne 1 -or $found[0].sha256 -cne $dependency.sha256){throw ('Native dependency winner ambiguous/changed '+$dependency.depot)}
}
$result=[ordered]@{status='WA3_51_PATH_ARCHIVE_READBACK_PASS';base='WA2';archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;archive_members=$memberCount;unchanged_members=1212;new_resource_count=$newRows.Count;new_resources=$newRows;registered_phase_count=$phaseRows.Count;registered_block_count=$blockRows.Count;streaming_blocks=$streamingBlocks;new_sector_count=$sectorRows.Count;sector_bindings=$sectorBindings;cohort_proof_sha256=(Get-FileHash -LiteralPath $cohortPath).Hash;checked_members=$readback;collision_archives=$archives.Count;collisions=$hits;archive_inventory=$archivePins;package_paths=51;changed_paths=$changed;xl_append_only=$true;reds_changed=1;baseline_sha256=$compiled.candidate_sha256;compile_source_count=$compiled.source_count;game_writes=0;save_writes=0}
$result.archive_paths=@($archives|ForEach-Object {[IO.Path]::GetRelativePath($game,$_.FullName).Replace('\','/')}|Sort-Object)
$result.native_dependency_queries_sha256=(Get-FileHash -LiteralPath $dependencyPath).Hash
$result.native_dependency_count=$dependencies.Count
$result.native_dependency_hits=$dependencyHits
[IO.File]::WriteAllText((Join-Path $candidate 'package_proof_01.json'),($result|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;members=$memberCount;unchanged=1212;added=$newRows.Count;paths=51;collision_archives=$archives.Count;archive_sha256=$result.archive_sha256}|ConvertTo-Json
