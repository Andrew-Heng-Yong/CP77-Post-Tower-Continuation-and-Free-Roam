# Pack the approved WA2 controller cohort without modifying existing BA1 resources.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/bottle_actions_ba1/candidate_01'
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package'
$newSource=Join-Path $candidate 'source'
$baselineSource=Join-Path $candidate 'script_source/PTFR_RestorationBaseline.reds'
$compiled=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json -Depth 30
if($compiled.status -cne 'PASS' -or $compiled.source_count -ne 64 -or (Get-FileHash -LiteralPath $baselineSource).Hash -cne $compiled.candidate_sha256){throw 'Fresh64-source Baseline compilation missing or drifted'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package)){throw 'Preserve candidate package; use successor'}
$cohortPath=Join-Path $candidate 'cohort_proof_01.json'
$cohort=Get-Content -LiteralPath $cohortPath -Raw|ConvertFrom-Json -Depth 80
if($cohort.status -cne 'WA2_SOURCE_COHORT_READY' -or @($cohort.resources).Count -lt 1){throw 'Approved WA2 source cohort is not ready'}
$approved=@{}
foreach($r in $cohort.resources){
 $depot=$r.depot.Replace('/','\')
 if($depot -notmatch '^towercontinued\\world_actions_wa2\\[a-zA-Z0-9_\\-]+\.questphase$' -or $approved.ContainsKey($depot) -or $r.sha256 -cnotmatch '^[A-F0-9]{64}$'){throw ('Invalid/duplicate approved depot '+$depot)}
 $approved[$depot]=$r.sha256
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
if($baseManifest.full_package_count -ne 51 -or $baseManifest.archive_members -ne 1186){throw 'BA1 baseline scope drift'}
foreach($f in $baseManifest.package_files){
 if((Get-FileHash -LiteralPath (Join-Path $game $f.path)).Hash -cne $f.after -or (Get-FileHash -LiteralPath (Join-Path $base ('package/'+$f.path))).Hash -cne $f.after){throw ('BA1 installed/package baseline changed '+$f.path)}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function RawHash($entry){$memory=[IO.MemoryStream]::new();try{$entry.Extract($memory);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}}
$oldArc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive((Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'),$hs,[ref]$oldArc).ToString() -cne 'NoError'){throw 'BA1 archive unreadable'}
$oldIndex=@{};$oldKeys=@{}
foreach($e in $oldArc.Files.Values){if($oldIndex.ContainsKey($e.Name)){throw 'Duplicate BA1 depot'};$oldIndex[$e.Name]=RawHash $e;$oldKeys[$e.Key.ToString()]=$e.Name}
if($oldIndex.Count -ne 1186){throw 'BA1 archive member count drift'}
$newKeys=@{}
foreach($r in $newRows){
 $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.depot).ToString()
 if($oldIndex.ContainsKey($r.depot) -or $oldKeys.ContainsKey($key) -or $newKeys.ContainsKey($key)){throw ('New controller aliases an existing depot/hash '+$r.depot)}
 $newKeys[$key]=$r.depot
}
$rawBase=Join-Path $base 'archive_source';$rawFiles=@(Get-ChildItem -LiteralPath $rawBase -Recurse -File)
if($rawFiles.Count -ne 1186){throw 'BA1 raw source count drift'}
foreach($f in $rawFiles){$rel=[IO.Path]::GetRelativePath($rawBase,$f.FullName);if(!$oldIndex.ContainsKey($rel) -or (Get-FileHash -LiteralPath $f.FullName).Hash -cne $oldIndex[$rel]){throw ('BA1 archive/source disagreement '+$rel)}}
Copy-Item -LiteralPath $rawBase -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
foreach($r in $newRows){$target=Join-Path $source $r.depot;[void][IO.Directory]::CreateDirectory((Split-Path $target -Parent));Copy-Item -LiteralPath (Join-Path $newSource $r.depot) -Destination $target}
$memberCount=1186+$newRows.Count
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne $memberCount){throw 'WA2 archive read/count failed'}
$readback=@();$unchanged=0;$added=0
foreach($e in $packed.Files.Values){
 $digest=RawHash $e
 if($digest -cne (Get-FileHash -LiteralPath (Join-Path $source $e.Name)).Hash){throw ('Packed source mismatch '+$e.Name)}
 if($oldIndex.ContainsKey($e.Name)){if($digest -cne $oldIndex[$e.Name]){throw ('BA1 resource changed '+$e.Name)};$unchanged++}elseif($approved.ContainsKey($e.Name) -and $approved[$e.Name] -ceq $digest){$added++}else{throw ('Unexpected new resource '+$e.Name)}
 $readback+=@{depot=$e.Name;sha256=$digest}
}
if($unchanged -ne 1186 -or $added -ne $newRows.Count){throw 'Resource preservation count failed'}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2){throw 'XL structure drift'}
$entries=''
foreach($r in $newRows){
 if($oldXL.Contains($r.depot)){throw ('Duplicate XL registration '+$r.depot)}
 $entries+="    - path: $($r.depot)`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
}
[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entries+'streaming:'),[Text.UTF8Encoding]::new($false))
$newXL=[IO.File]::ReadAllText($xl)
if($newXL.Replace($entries,'') -cne $oldXL){throw 'XL changed beyond new registrations'}
foreach($r in $newRows){if([regex]::Matches($newXL,[regex]::Escape('    - path: '+$r.depot)+"\r?\n").Count -ne 1){throw ('XL registration is not unique '+$r.depot)}}
Copy-Item -LiteralPath $baselineSource -Destination (Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds')
if(@(Get-ChildItem -LiteralPath $package -File -Recurse).Count -ne 51){throw 'Full package path count'}
$expected=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds')
$changed=@();foreach($f in $baseManifest.package_files){if((Get-FileHash -LiteralPath (Join-Path $package $f.path)).Hash -cne $f.after){$changed+=,$f.path}}
if(@(Compare-Object ($expected|Sort-Object) ($changed|Sort-Object)).Count){throw 'Unexpected install file changes'}
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File)
$hits=@();$archivePins=@()
foreach($file in $archives){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable mod archive '+$file.Name)}
 foreach($e in $arc.Files.Values){if($newKeys.ContainsKey($e.Key.ToString())){$hits+=@{archive=$file.Name;depot=$e.Name;new_resource=$newKeys[$e.Key.ToString()]}}}
 $archivePins+=@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}
}
if($hits.Count){throw 'New WA2 resource collision'}
$result=[ordered]@{status='WA2_51_PATH_ARCHIVE_READBACK_PASS';base='BA1';archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;archive_members=$memberCount;unchanged_members=1186;new_resource_count=$newRows.Count;new_resources=$newRows;cohort_proof_sha256=(Get-FileHash -LiteralPath $cohortPath).Hash;checked_members=$readback;collision_archives=$archives.Count;collisions=$hits;archive_inventory=$archivePins;package_paths=51;changed_paths=$changed;xl_append_only=$true;reds_changed=1;baseline_sha256=$compiled.candidate_sha256;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_proof_01.json'),($result|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;members=$memberCount;unchanged=1186;added=$newRows.Count;paths=51;collision_archives=$archives.Count;archive_sha256=$result.archive_sha256}|ConvertTo-Json
