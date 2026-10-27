Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$selection=Get-Content -LiteralPath (Join-Path $candidate 'selected_resources_01.json') -Raw|ConvertFrom-Json -Depth 40
$base=Get-Content -LiteralPath (Join-Path $candidate 'baseline_01.json') -Raw|ConvertFrom-Json -Depth 40
$source=Join-Path $candidate 'archive_source'
if($selection.resources.Count -ne 30 -or $base.resources.Count -ne 1172){throw 'Unexpected reviewed resource scope'}
if(Test-Path -LiteralPath (Join-Path $candidate 'manifest.json')){throw 'Candidate pinned; use successor'}
$final=@{};foreach($r in $base.resources){$final[$r.depot]=$r.sha256}
foreach($r in $selection.resources){
 if(!$final.ContainsKey($r.depot) -or $final[$r.depot] -cne $r.before){throw ('Reviewed prior differs '+$r.depot)}
 if((Get-FileHash -LiteralPath $r.donor_raw).Hash -cne $r.after){throw ('Donor drift '+$r.depot)}
 $target=Join-Path $source $r.depot
 if((Get-FileHash -LiteralPath $target).Hash -cne $r.before){throw ('Staged baseline drift '+$r.depot)}
 Copy-Item -LiteralPath $r.donor_raw -Destination $target -Force
 $final[$r.depot]=$r.after
}
$files=@(Get-ChildItem -LiteralPath $source -Recurse -File)
if($files.Count -ne 1172){throw 'Resource count drift'}
foreach($p in $files){$rel=[IO.Path]::GetRelativePath($source,$p.FullName).Replace('/','\');if((Get-FileHash -LiteralPath $p.FullName).Hash -cne $final[$rel]){throw ('Unreviewed resource mutation '+$rel)}}
$archive=Join-Path $candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive packing failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 1172){throw 'Packed count mismatch'}
$members=[Collections.Generic.List[object]]::new()
foreach($e in $packed.Files.Values){
 $m=[IO.MemoryStream]::new();try{$e.Extract($m);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}
 if($h -cne $final[$e.Name]){throw ('Packed payload mismatch '+$e.Name)}
 $members.Add(@{depot=$e.Name;key=$e.Key.ToString();sha256=$h})
}
$keys=@{};foreach($r in $members){$keys[$r.key]=$r.depot}
$mod='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc/mod'
$other=@(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File|Where-Object {$_.Name -cne 'zzzz_PTFR_Combined.archive'})
$collisions=[Collections.Generic.List[object]]::new()
foreach($p in $other){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('External archive unreadable '+$p.FullName)}
 foreach($e in $a.Files.Values){if($keys.ContainsKey($e.Key.ToString())){$collisions.Add(@{archive=$p.FullName;depot=$keys[$e.Key.ToString()]})}}
}
if($collisions.Count){throw 'External resource collision'}
$package=Join-Path $candidate 'package';$packageFiles=@(Get-ChildItem -LiteralPath $package -Recurse -File)
if($packageFiles.Count -ne 51){throw 'Install file count changed'}
$rows=@($packageFiles|ForEach-Object {@{path=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
$changed=0
foreach($r in $rows){$old=@($base.package_files|Where-Object {$_.path -ceq $r.path});if($old.Count -ne 1){throw 'New install path'};if($r.sha256 -cne $old[0].sha256){$changed++;if($r.path -cne 'archive/pc/mod/zzzz_PTFR_Combined.archive'){throw 'Unexpected nonarchive package change'}}}
if($changed -ne 1){throw 'Expected exactly one replaced package file'}
$manifest=@{status='CR1_51_FILE_CONSOLIDATED_SUCCESSOR_PACKED';files=$rows;source_members=1172;repaired_members=30;unchanged_members=1142;new_resource_paths=0;removed_resource_paths=0;changed_install_files=1;unchanged_install_files=50;game_writes=0;save_writes=0}
$proof=@{status='PASS';member_count=1172;members=$members.ToArray();other_archives=$other.Count;external_collisions=$collisions.ToArray();archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;game_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'manifest.json'),($manifest|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $candidate 'archive_readback_01.json'),($proof|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
@{status=$manifest.status;resource_replacements=30;unchanged_resources=1142;package_files=51;changed_install_files=1;external_collisions=0;archive_sha256=$proof.archive_sha256}|ConvertTo-Json
