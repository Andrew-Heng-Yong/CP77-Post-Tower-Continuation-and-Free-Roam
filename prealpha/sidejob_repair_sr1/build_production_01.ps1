Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$prior=Join-Path $PSScriptRoot 'candidate_02'
$out=Join-Path $PSScriptRoot 'production_01'
if(Test-Path -LiteralPath $out){throw 'Production candidate exists; use successor'}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$archiveRel='archive/pc/mod/00000000_TowerContinued_SideJobs_S29.archive'
$xlRel=$archiveRel+'.xl'
$scriptRel='r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds'
$baselineArchive=Join-Path $game $archiveRel
$baselineXL=Join-Path $game $xlRel
$baselineScript=Join-Path $game $scriptRel
$core=Get-Content -LiteralPath (Join-Path $prior 'build_native_02.json') -Raw|ConvertFrom-Json
$visual=Get-Content -LiteralPath (Join-Path $prior 'visual_07/proof.json') -Raw|ConvertFrom-Json
$lipmap=Get-Content -LiteralPath (Join-Path $prior 'package_lipmap_01.json') -Raw|ConvertFrom-Json
$tests=@('test_native_01.json','test_visual_01.json','test_visual_02.json','test_lipmap_01.json','deployment_tests_02.json','compile_01/result.json')
foreach($p in $tests){if(!(Test-Path -LiteralPath (Join-Path $prior $p))){throw ('Missing tested proof '+$p)}}
if($core.status -cne 'STAGED_NATIVE_SIX_RESOURCE_PATCH_NOT_INSTALLED' -or $visual.status -cne 'WORKSPACE_VISUAL_SEVEN_RESOURCE_FINAL_NOT_INSTALLED' -or $lipmap.status -cne 'STAGED_44_LIPMAP_ARCHIVE_XL_READBACK_NO_INSTALL'){throw 'Prior tested build changed'}
New-Item -ItemType Directory -Path (Join-Path $out 'source'),(Join-Path $out 'archived_previous'),(Join-Path $out 'package') -Force|Out-Null
foreach($r in @($archiveRel,$xlRel,$scriptRel)){$src=Join-Path $game $r;$dst=Join-Path (Join-Path $out 'archived_previous') $r;New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null;Copy-Item -LiteralPath $src -Destination $dst;if((Get-FileHash -LiteralPath $dst).Hash -cne (Get-FileHash -LiteralPath $src).Hash){throw ('Prior archive backup mismatch '+$r)}}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$a=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($baselineArchive,$hs,[ref]$a).ToString() -cne 'NoError' -or $a.Files.Count -ne 194){throw 'Installed S29 baseline archive changed'}
$old=[ordered]@{};$new=[ordered]@{};$source=Join-Path $out 'source'
foreach($e in $a.Files.Values){
 $rel=$e.Name
 if($rel -notlike 'towercontinued\*' -or [IO.Path]::IsPathRooted($rel) -or $rel.Contains(':') -or @($rel.Replace('\','/').Split('/')) -contains '..'){throw ('Unexpected archive member path '+$rel)}
 if($old.Contains($rel)){throw ('Duplicate archive name '+$rel)}
 $raw=Join-Path $source $rel;New-Item -ItemType Directory -Path (Split-Path $raw -Parent) -Force|Out-Null
 $m=[IO.MemoryStream]::new();try{$e.Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
 $hash=(Get-FileHash -LiteralPath $raw).Hash;$old[$rel]=$hash;$new[$rel]=$hash
}
$overlays=[Collections.Generic.List[object]]::new()
foreach($p in $core.resources.PSObject.Properties){$overlays.Add(@{depot=$p.Name;path=(Join-Path (Join-Path $prior 'source') $p.Name);sha=$p.Value;kind='core'})}
foreach($p in @($visual.prior)+@($visual.additional)+@($visual.new_private_kold)){$overlays.Add(@{depot=$p.depot;path=(Join-Path (Join-Path $prior 'visual_07') $p.depot);sha=$p.patched_sha256;kind='visual'})}
$lipmapDepot=$lipmap.depot;$overlays.Add(@{depot=$lipmapDepot;path=(Join-Path (Join-Path $prior 'lipmap_source') $lipmapDepot);sha=$lipmap.resource_sha256;kind='lipmap'})
if($overlays.Count -ne 14 -or @($overlays.depot|Select-Object -Unique).Count -ne 14){throw 'Expected fourteen unique repaired resources'}
$rows=[Collections.Generic.List[object]]::new()
foreach($p in $overlays){
 if((Get-FileHash -LiteralPath $p.path).Hash -cne $p.sha){throw ('Overlay source drift '+$p.depot)}
 $dst=Join-Path $source $p.depot;New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force|Out-Null
 Copy-Item -LiteralPath $p.path -Destination $dst -Force
 $new[$p.depot]=$p.sha
 $rows.Add(@{depot=$p.depot;kind=$p.kind;prior=$old[$p.depot];after=$p.sha})
}
$archiveOut=Join-Path (Join-Path $out 'package') $archiveRel
New-Item -ItemType Directory -Path (Split-Path $archiveOut -Parent) -Force|Out-Null
$stream=[IO.File]::Create($archiveOut)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Production archive writer failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archiveOut,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 199){throw 'Production archive member count mismatch'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};if($h -cne $new[$e.Name]){throw ('Production archive member changed '+$e.Name)}}
$xlOriginal=[IO.File]::ReadAllText($baselineXL,[Text.Encoding]::UTF8)
if($xlOriginal.Contains('localization:') -or !$xlOriginal.EndsWith("`n")){throw 'Existing S29 XL unexpectedly changed'}
$xlOut=Join-Path (Join-Path $out 'package') $xlRel;New-Item -ItemType Directory -Path (Split-Path $xlOut -Parent) -Force|Out-Null
$xlAdded="localization:`n  lipmaps:`n    en-us: $lipmapDepot`n"
[IO.File]::WriteAllText($xlOut,($xlOriginal+$xlAdded),[Text.UTF8Encoding]::new($false))
$scriptSource=Join-Path $prior 'package/r6/scripts/TowerContinued_SideJobs_S29/SideJobsS29.reds'
$scriptOut=Join-Path (Join-Path $out 'package') $scriptRel;New-Item -ItemType Directory -Path (Split-Path $scriptOut -Parent) -Force|Out-Null;Copy-Item -LiteralPath $scriptSource -Destination $scriptOut
$proof=[ordered]@{status='THREE_FILE_PRODUCTION_CANDIDATE_READBACK_NOT_INSTALLED';previous=@{archive=(Get-FileHash -LiteralPath $baselineArchive).Hash;xl=(Get-FileHash -LiteralPath $baselineXL).Hash;script=(Get-FileHash -LiteralPath $baselineScript).Hash};package=@{archive=(Get-FileHash -LiteralPath $archiveOut).Hash;xl=(Get-FileHash -LiteralPath $xlOut).Hash;script=(Get-FileHash -LiteralPath $scriptOut).Hash};baseline_members=194;production_members=199;overlays=$rows.ToArray();unchanged_members=185;new_members=5;replaced_members=9;archived_previous=(Join-Path $out 'archived_previous');game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'build_01.json'),($proof|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
@{status=$proof.status;production_members=$proof.production_members;package=$proof.package}|ConvertTo-Json -Depth 10
