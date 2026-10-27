# Pack SC3 as a successor at the same 51 installed paths.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/skippy_coaster_sc2/candidate_01'
$rawBase=Join-Path $ws 'prealpha/skippy_coaster_sc1/candidate_07/archive_source'
$candidate=Join-Path $PSScriptRoot 'candidate_02'
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package)){throw 'Preserve candidate; use successor'}
$compile=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json
if($compile.status -cne 'PASS' -or $compile.source_count -ne 64){throw 'Full compile missing'}
$baseManifest=Get-Content -LiteralPath (Join-Path $base 'install_manifest_01.json') -Raw|ConvertFrom-Json
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
foreach($f in $baseManifest.package_files){
 if((Get-FileHash -LiteralPath (Join-Path $game $f.path)).Hash -cne $f.after -or (Get-FileHash -LiteralPath (Join-Path $base ('package/'+$f.path))).Hash -cne $f.after){throw ('SC2 baseline changed '+$f.path)}
}
$ownerRel='towercontinued\skippy_ambient_sc3\skippy_ambient_owner.questphase'
$owner=Join-Path $PSScriptRoot ('native_review/candidate_02/source/'+$ownerRel)
if(!(Test-Path -LiteralPath $owner)){throw 'Native lifecycle owner missing'}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$oldArc=$null
$oldArchivePath=Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($oldArchivePath,$hs,[ref]$oldArc).ToString() -cne 'NoError'){throw 'SC2 archive unreadable'}
function RawHash($entry){$memory=[IO.MemoryStream]::new();try{$entry.Extract($memory);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}}
$oldIndex=@{};foreach($e in $oldArc.Files.Values){if($oldIndex.ContainsKey($e.Name)){throw 'Duplicate old depot'};$oldIndex[$e.Name]=RawHash $e}
if($oldIndex.Count -ne 1184){throw 'SC2 member count drift'}
$rawFiles=@(Get-ChildItem -LiteralPath $rawBase -Recurse -File)
if($rawFiles.Count -ne 1184){throw 'SC1 raw source count drift'}
foreach($f in $rawFiles){$rel=[IO.Path]::GetRelativePath($rawBase,$f.FullName);if(!$oldIndex.ContainsKey($rel) -or (Get-FileHash -LiteralPath $f.FullName).Hash -cne $oldIndex[$rel]){throw ('Baseline source/readback disagreement '+$rel)}}
Copy-Item -LiteralPath $rawBase -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
$ownerTarget=Join-Path $source $ownerRel
[void][IO.Directory]::CreateDirectory((Split-Path $ownerTarget -Parent));Copy-Item -LiteralPath $owner -Destination $ownerTarget
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new());if(!$writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'SC3 archive unreadable'}
if($packed.Files.Count -ne 1185){throw 'SC3 archive member count'}
$readback=@();$unchanged=0
foreach($e in $packed.Files.Values){
 $digest=RawHash $e;$path=Join-Path $source $e.Name
 if($digest -cne (Get-FileHash -LiteralPath $path).Hash){throw ('Archive/source mismatch '+$e.Name)}
 if($oldIndex.ContainsKey($e.Name)){if($digest -cne $oldIndex[$e.Name]){throw ('Old resource changed '+$e.Name)};$unchanged++}elseif($e.Name -cne $ownerRel){throw ('Unexpected added resource '+$e.Name)}
 $readback+=@{depot=$e.Name;sha256=$digest}
}
if($unchanged -ne 1184){throw 'Baseline preservation count'}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2 -or $oldXL.Contains($ownerRel)){throw 'XL structure drift'}
$entry="    - path: $ownerRel`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entry+'streaming:'),[Text.UTF8Encoding]::new($false))
$scriptSource=Join-Path $candidate 'script_source/PTFR_SideJobsS23.reds'
if((Get-FileHash -LiteralPath $scriptSource).Hash -cne $compile.candidate_sha256){throw 'Script changed since compile'}
Copy-Item -LiteralPath $scriptSource -Destination (Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds')
if(@(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'Full package count'}
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($ownerRel).ToString()
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File)
$hits=@()
foreach($file in $archives){$arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable mod archive '+$file.Name)};foreach($e in $arc.Files.Values){if($e.Key.ToString() -ceq $key){$hits+=@{archive=$file.Name;depot=$e.Name}}}}
if($hits.Count){throw 'New SC3 depot collision'}
$result=[ordered]@{status='SC3_51_PATH_ARCHIVE_READBACK_PASS';archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;archive_members=1185;unchanged_members=1184;new_resource=$ownerRel;new_resource_sha256=(Get-FileHash -LiteralPath $owner).Hash;checked_members=$readback;collision_archives=$archives.Count;collisions=$hits;package_paths=51;xl_append_only=$true;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_proof_01.json'),($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;members=1185;unchanged=1184;paths=51;collision_archives=$archives.Count}|ConvertTo-Json
