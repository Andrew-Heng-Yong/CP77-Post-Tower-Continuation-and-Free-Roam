# Package the isolated BA1 controller in the existing consolidated install paths.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/coaster_cutoff_cc1/candidate_01'
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package'
$ownerRel='towercontinued\bottle_actions_ba1\bottle_action_owner.questphase'
$owner=Join-Path (Join-Path $candidate 'source') $ownerRel
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package)){throw 'Preserve candidate package; use successor'}
if(!(Test-Path -LiteralPath $owner -PathType Leaf)){throw 'BA1 serialized owner is not ready'}
$ownerProof=Get-Content -LiteralPath (Join-Path $candidate 'owner_proof_01.json') -Raw|ConvertFrom-Json -Depth 80
if($ownerProof.status -cne 'BA1_OWNER_SERIALIZED'){throw 'BA1 owner proof is not ready'}
$baseManifest=Get-Content -LiteralPath (Join-Path $base 'install_manifest_01.json') -Raw|ConvertFrom-Json -Depth 80
if($baseManifest.full_package_count -ne 51 -or $baseManifest.archive_members -ne 1185){throw 'CC1 baseline scope drift'}
foreach($f in $baseManifest.package_files){
 if((Get-FileHash -LiteralPath (Join-Path $game $f.path)).Hash -cne $f.after -or (Get-FileHash -LiteralPath (Join-Path $base ('package/'+$f.path))).Hash -cne $f.after){throw ('CC1 installed/package baseline changed '+$f.path)}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function RawHash($entry){$memory=[IO.MemoryStream]::new();try{$entry.Extract($memory);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}}
$oldArc=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive((Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'),$hs,[ref]$oldArc).ToString() -cne 'NoError'){throw 'CC1 archive unreadable'}
$oldIndex=@{};foreach($e in $oldArc.Files.Values){if($oldIndex.ContainsKey($e.Name)){throw 'Duplicate CC1 depot'};$oldIndex[$e.Name]=RawHash $e}
if($oldIndex.Count -ne 1185 -or $oldIndex.ContainsKey($ownerRel)){throw 'CC1 archive/new owner scope drift'}
$rawBase=Join-Path $base 'archive_source';$rawFiles=@(Get-ChildItem -LiteralPath $rawBase -Recurse -File)
if($rawFiles.Count -ne 1185){throw 'CC1 raw source count drift'}
foreach($f in $rawFiles){$rel=[IO.Path]::GetRelativePath($rawBase,$f.FullName);if(!$oldIndex.ContainsKey($rel) -or (Get-FileHash -LiteralPath $f.FullName).Hash -cne $oldIndex[$rel]){throw ('CC1 archive/source disagreement '+$rel)}}
Copy-Item -LiteralPath $rawBase -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
$ownerTarget=Join-Path $source $ownerRel
[void][IO.Directory]::CreateDirectory((Split-Path $ownerTarget -Parent));Copy-Item -LiteralPath $owner -Destination $ownerTarget
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1186){throw 'BA1 archive read/count failed'}
$readback=@();$unchanged=0;$new=0
foreach($e in $packed.Files.Values){
 $digest=RawHash $e
 if($digest -cne (Get-FileHash -LiteralPath (Join-Path $source $e.Name)).Hash){throw ('Packed source mismatch '+$e.Name)}
 if($oldIndex.ContainsKey($e.Name)){if($digest -cne $oldIndex[$e.Name]){throw ('CC1 resource changed '+$e.Name)};$unchanged++}elseif($e.Name -ceq $ownerRel){$new++}else{throw ('Unexpected new resource '+$e.Name)}
 $readback+=@{depot=$e.Name;sha256=$digest}
}
if($unchanged -ne 1185 -or $new -ne 1){throw 'Resource preservation count failed'}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2 -or $oldXL.Contains($ownerRel)){throw 'XL structure/duplicate registration'}
$entry="    - path: $ownerRel`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entry+'streaming:'),[Text.UTF8Encoding]::new($false))
if([IO.File]::ReadAllText($xl).Replace($entry,'') -cne $oldXL){throw 'XL changed beyond one registration'}
if(@(Get-ChildItem -LiteralPath $package -File -Recurse).Count -ne 51){throw 'Full package path count'}
$expected=@('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl')
$changed=@();foreach($f in $baseManifest.package_files){if((Get-FileHash -LiteralPath (Join-Path $package $f.path)).Hash -cne $f.after){$changed+=,$f.path}}
if(@(Compare-Object ($expected|Sort-Object) ($changed|Sort-Object)).Count){throw 'Unexpected install file changes'}
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($ownerRel).ToString()
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File)
$hits=@();$archivePins=@()
foreach($file in $archives){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable mod archive '+$file.Name)}
 foreach($e in $arc.Files.Values){if($e.Key.ToString() -ceq $key){$hits+=@{archive=$file.Name;depot=$e.Name}}}
 $archivePins+=@{path=$file.FullName;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}
}
if($hits.Count){throw 'New BA1 resource collision'}
$result=[ordered]@{status='BA1_51_PATH_ARCHIVE_READBACK_PASS';base='CC1';archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;archive_members=1186;unchanged_members=1185;new_resource=$ownerRel;new_resource_sha256=(Get-FileHash -LiteralPath $owner).Hash;checked_members=$readback;collision_archives=$archives.Count;collisions=$hits;archive_inventory=$archivePins;package_paths=51;changed_paths=$changed;xl_append_only=$true;reds_changed=0;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_proof_01.json'),($result|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;members=1186;unchanged=1185;paths=51;collision_archives=$archives.Count;archive_sha256=$result.archive_sha256}|ConvertTo-Json
