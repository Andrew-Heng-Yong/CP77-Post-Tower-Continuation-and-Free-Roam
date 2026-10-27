Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base=Join-Path $ws 'prealpha/world_workspots_w2/candidate_04'
$candidate=Join-Path $PSScriptRoot 'candidate_07'
$source=Join-Path $candidate 'archive_source';$package=Join-Path $candidate 'package'
if((Test-Path -LiteralPath $source) -or (Test-Path -LiteralPath $package)){throw 'Preserve existing candidate'}
$proof=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_04/semantic_proof_01.json') -Raw|ConvertFrom-Json
$compile=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_05/compile_01/result.json') -Raw|ConvertFrom-Json
if($proof.status -cne 'PASS' -or $compile.status -cne 'PASS' -or $compile.source_count -ne 64){throw 'Candidate evidence missing'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$basePackage=Join-Path $base 'package'
foreach($path in @('archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds')){
 if((Get-FileHash -LiteralPath (Join-Path $game $path)).Hash -cne (Get-FileHash -LiteralPath (Join-Path $basePackage $path)).Hash){throw ('W3 installed baseline drift '+$path)}
}
Copy-Item -LiteralPath (Join-Path $base 'archive_source') -Destination $source -Recurse
Copy-Item -LiteralPath $basePackage -Destination $package -Recurse
if(@(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1183 -or @(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'W3 census drift'}
$sceneRel='towercontinued\sidejobs_s30\native\base\quest\minor_quests\mq006\scenes\mq006_02_finale.scene'
$ownerRel='towercontinued\skippy_ambient_sc1\skippy_ambient_owner.questphase'
$scene=Join-Path $PSScriptRoot 'candidate_04/scene_after_01.scene'
$owner=Join-Path $PSScriptRoot ('candidate_06/source/'+$ownerRel)
if((Get-FileHash -LiteralPath (Join-Path $source $sceneRel)).Hash -cne '91997539E039F5090BDB255B6FDACE67BBADBC96326AB178B53B6609D784530F'){throw 'MQ006 scene drift'}
Copy-Item -LiteralPath $scene -Destination (Join-Path $source $sceneRel)
$ownerTarget=Join-Path $source $ownerRel
[void][IO.Directory]::CreateDirectory((Split-Path $ownerTarget -Parent))
Copy-Item -LiteralPath $owner -Destination $ownerTarget
if(@(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1184){throw 'Successor source count'}
$archive=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$stream=[IO.File]::Create($archive)
try{$writer=[WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new());if(-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Archive write failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'Archive readback failed'}
if($packed.Files.Count -ne 1184){throw 'Successor archive member count'}
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
if($checked -ne 1184){throw 'Packed check count'}
$xl=Join-Path $package 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=[IO.File]::ReadAllText($xl)
if($oldXL.Split('streaming:').Count -ne 2 -or $oldXL.Contains($ownerRel)){throw 'XL structure drift'}
$entry="    - path: $ownerRel`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
[IO.File]::WriteAllText($xl,$oldXL.Replace('streaming:',$entry+'streaming:'),[Text.UTF8Encoding]::new($false))
$script=Join-Path $package 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
$scriptSource=Join-Path $PSScriptRoot 'candidate_05/script_source/PTFR_SideJobsS23.reds'
if((Get-FileHash -LiteralPath $scriptSource).Hash -cne $compile.candidate_sha256){throw 'Compiled script drift'}
Copy-Item -LiteralPath $scriptSource -Destination $script
if(@(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne 51){throw 'Package path count'}
$result=[ordered]@{status='SC1_51_PATH_CANDIDATE_PACKED_NOT_INSTALLED';base_archive_sha256=(Get-FileHash -LiteralPath (Join-Path $basePackage 'archive/pc/mod/zzzz_PTFR_Combined.archive')).Hash;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath $xl).Hash;script_sha256=(Get-FileHash -LiteralPath $script).Hash;archive_members=1184;new_resource=$ownerRel;changed_resource=$sceneRel;checked_members=$checked;package_paths=51;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_proof_01.json'),($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;members=$result.archive_members;paths=$result.package_paths}|ConvertTo-Json
