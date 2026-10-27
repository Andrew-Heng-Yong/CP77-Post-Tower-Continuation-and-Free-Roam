# Workspace-only full 51-path successor; source/archive/xl/script, no installation.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_01'
$base=Join-Path $ws 'prealpha/coaster_jean_jc1/candidate_01'
$source=Join-Path $candidate 'archive_source'
$package=Join-Path $candidate 'package'
$proofPath=Join-Path $candidate 'package_proof_01.json'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package) -or (Test-Path -LiteralPath $proofPath)){throw 'Preserve package evidence; use successor'}
$ownerProof=Get-Content -LiteralPath (Join-Path $candidate 'owner_proof_01.json') -Raw|ConvertFrom-Json -Depth 80
$compile=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json -Depth 30
if($ownerProof.status -cne 'PRIVATE_PREFAB_OWNERS_READBACK_PASS_NOT_PACKED_OR_INSTALLED' -or $ownerProof.owners -ne 205 -or $ownerProof.resources -ne 9 -or $compile.status -cne 'PASS' -or $compile.source_count -ne 64){throw 'Owner/script proofs missing'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$currentArchive=Join-Path $game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$baselineArchive=Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if((Get-FileHash -LiteralPath $currentArchive).Hash -cne (Get-FileHash -LiteralPath $baselineArchive).Hash){throw 'Installed/base archive mismatch'}
Copy-Item -LiteralPath (Join-Path $base 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
if(@(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1172 -or @(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'Base package/source census drift'}
$new=[Collections.Generic.List[object]]::new()
$probe='towercontinued\world_workspots_ww1\ce_pac_cvi_116_owner.questphase'
$probeSource=Join-Path $ws ('prealpha/world_workspots_ww1/probe_04/source/'+$probe)
$probeDest=Join-Path $source $probe
[void][IO.Directory]::CreateDirectory((Split-Path $probeDest -Parent))
Copy-Item -LiteralPath $probeSource -Destination $probeDest
$new.Add([ordered]@{resource=$probe;sha256=(Get-FileHash -LiteralPath $probeDest -Algorithm SHA256).Hash})
foreach($p in $ownerProof.proofs){
 $src=Join-Path (Join-Path $candidate 'source') $p.resource
 if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -cne $p.sha256){throw "Owner resource drift $($p.resource)"}
 $dst=Join-Path $source $p.resource
 [void][IO.Directory]::CreateDirectory((Split-Path $dst -Parent))
 Copy-Item -LiteralPath $src -Destination $dst
 $new.Add([ordered]@{resource=$p.resource;sha256=$p.sha256})
}
if($new.Count -ne 10 -or @(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1182){throw 'Archive source member count mismatch'}
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$stream=[IO.File]::Create($archive)
try{
 $writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
 if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}
}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'Archive readback failed'}
if($packed.Files.Count -ne 1182){throw "Packed member count $($packed.Files.Count)"}
$sourceFiles=@(Get-ChildItem -LiteralPath $source -Recurse -File)
$members=[Collections.Generic.List[object]]::new()
foreach($f in $sourceFiles){
 $relative=[IO.Path]::GetRelativePath($source,$f.FullName)
 $entry=@($packed.Files.Values|Where-Object Name -ceq $relative)
 if($entry.Count -ne 1){throw "Packed resource missing/colliding $relative"}
 $memory=[IO.MemoryStream]::new()
 try{$entry[0].Extract($memory);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}
 $sourceHash=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
 if($hash -cne $sourceHash){throw "Packed resource mismatch $relative"}
 $members.Add([ordered]@{path=$relative;sha256=$hash})
}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2){throw 'ArchiveXL structure changed'}
$insert=[Text.StringBuilder]::new()
foreach($r in $new){
 [void]$insert.AppendLine('    - path: '+$r.resource)
 [void]$insert.AppendLine('      parent: ep1\quest\ep1.quest')
 [void]$insert.AppendLine('      input:')
 [void]$insert.AppendLine('        node: [1]')
 [void]$insert.AppendLine('        socket: Out')
}
$newXL=$oldXL.Replace('streaming:', $insert.ToString()+'streaming:')
[IO.File]::WriteAllText($xl,$newXL,[Text.UTF8Encoding]::new($false))
$scriptSource=Join-Path $candidate 'script_source/PTFR_RestorationBaseline.reds'
$script=Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds'
if((Get-FileHash -LiteralPath $scriptSource -Algorithm SHA256).Hash -cne $compile.candidate_sha256){throw 'Compiled script changed'}
Copy-Item -LiteralPath $scriptSource -Destination $script
if(@(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'Production file count changed'}
$summary=[ordered]@{status='FULL_51_PATH_W2_CANDIDATE_PACKED_NOT_INSTALLED';base_archive_sha256=(Get-FileHash -LiteralPath $baselineArchive -Algorithm SHA256).Hash;archive_sha256=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash;archive_xl_sha256=(Get-FileHash -LiteralPath $xl -Algorithm SHA256).Hash;script_sha256=(Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash;members=1182;new_resources=@($new);full_package_paths=51;source_count=64;packed_member_checks=$members.Count;source_pins=@($members);game_writes=0;save_writes=0}
[IO.File]::WriteAllText($proofPath,($summary|ConvertTo-Json -Depth 80)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$summary.status;members=$summary.members;new_resources=$new.Count;package_paths=$summary.full_package_paths}|ConvertTo-Json
