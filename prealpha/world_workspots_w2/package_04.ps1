Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_04'
$base=Join-Path $PSScriptRoot 'candidate_02'
$baseSource=Join-Path $PSScriptRoot 'candidate_01/archive_source'
$rancho=Join-Path $PSScriptRoot 'candidate_03'
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package'
$proofPath=Join-Path $candidate 'package_proof_01.json'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package) -or (Test-Path -LiteralPath $proofPath)){throw 'Preserve W3 package evidence'}
$ownerProof=Get-Content -LiteralPath (Join-Path $rancho 'owner_proof_01.json') -Raw|ConvertFrom-Json -Depth 80
$graph=Get-Content -LiteralPath (Join-Path $rancho 'graph_validation_01.json') -Raw|ConvertFrom-Json
$compile=Get-Content -LiteralPath (Join-Path $candidate 'compile_01/result.json') -Raw|ConvertFrom-Json
if($ownerProof.owners -ne 31 -or $ownerProof.resources -ne 1 -or $graph.status -cne 'PASS_RANCHO_PRIVATE_OWNER_GRAPHS' -or $compile.status -cne 'PASS' -or $compile.source_count -ne 64){throw 'W3 source proof missing'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$currentArchive=Join-Path $game 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$baseArchive=Join-Path $base 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if((Get-FileHash -LiteralPath $currentArchive).Hash -cne (Get-FileHash -LiteralPath $baseArchive).Hash){throw 'Installed W2 archive drift'}
Copy-Item -LiteralPath $baseSource -Destination $source -Recurse
Copy-Item -LiteralPath (Join-Path $base 'package') -Destination $package -Recurse
if(@(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1182 -or @(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'W2 source/package census drift'}
$one=$ownerProof.proofs[0]
$src=Join-Path (Join-Path $rancho 'source') $one.resource
if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -cne $one.sha256){throw 'Rancho owner resource changed'}
$dest=Join-Path $source $one.resource
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent));Copy-Item -LiteralPath $src -Destination $dest
if(@(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1183){throw 'W3 source count'}
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'Archive readback failed'}
if($packed.Files.Count -ne 1183){throw 'W3 archive member count'}
$index=@{};foreach($e in $packed.Files.Values){if($index.ContainsKey($e.Name)){throw 'Duplicate depot'};$index[$e.Name]=$e}
$checked=0
foreach($file in Get-ChildItem -LiteralPath $source -Recurse -File){
 $relative=[IO.Path]::GetRelativePath($source,$file.FullName)
 if(!$index.ContainsKey($relative)){throw "Missing packed member $relative"}
 $memory=[IO.MemoryStream]::new()
 try{$index[$relative].Extract($memory);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}finally{$memory.Dispose()}
 if($hash -cne (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash){throw "Packed member mismatch $relative"}
 $checked++
}
if($checked -ne 1183){throw 'Packed check count'}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2){throw 'XL structure drift'}
$entry="    - path: $($one.resource)`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entry+'streaming:'),[Text.UTF8Encoding]::new($false))
$scriptSource=Join-Path $candidate 'script_source/PTFR_RestorationBaseline.reds'
$script=Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds'
if((Get-FileHash -LiteralPath $scriptSource -Algorithm SHA256).Hash -cne $compile.candidate_sha256){throw 'Compiled W3 script changed'}
Copy-Item -LiteralPath $scriptSource -Destination $script
if(@(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'W3 path count'}
$result=[ordered]@{status='W3_51_PATH_CANDIDATE_PACKED_NOT_INSTALLED';base_archive_sha256=(Get-FileHash -LiteralPath $baseArchive -Algorithm SHA256).Hash;archive_sha256=(Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash;xl_sha256=(Get-FileHash -LiteralPath $xl -Algorithm SHA256).Hash;script_sha256=(Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash;archive_members=1183;new_resource=$one.resource;new_resource_sha256=$one.sha256;checked_members=$checked;package_paths=51;game_writes=0;save_writes=0}
[IO.File]::WriteAllText($proofPath,($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;members=$result.archive_members;paths=$result.package_paths}|ConvertTo-Json
