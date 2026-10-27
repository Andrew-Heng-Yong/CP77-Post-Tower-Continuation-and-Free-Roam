Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$prior=Join-Path $ws 'prealpha/full_consolidation_v1/candidate_01'
$out=Join-Path $PSScriptRoot 'candidate_02';if(Test-Path $out){throw 'Use successor candidate'}
$newSource=Join-Path $out 'archive_source';$newPackage=Join-Path $out 'package'
Copy-Item -LiteralPath (Join-Path $prior 'archive_source') -Destination $newSource -Recurse
Copy-Item -LiteralPath (Join-Path $prior 'package') -Destination $newPackage -Recurse
$baseline=@{};foreach($p in Get-ChildItem (Join-Path $prior 'archive_source') -File -Recurse){$rel=[IO.Path]::GetRelativePath((Join-Path $prior 'archive_source'),$p.FullName).Replace('/','\');$baseline[$rel]=(Get-FileHash $p.FullName).Hash}
if($baseline.Count -ne 1153){throw 'Baseline member count changed'}
$new=Join-Path $PSScriptRoot 'serialized_02/source';$overlaid=@{}
foreach($p in Get-ChildItem $new -File -Recurse){
 $rel=[IO.Path]::GetRelativePath($new,$p.FullName).Replace('/','\')
 if($rel.EndsWith('.reds')){continue}
 $target=Join-Path $newSource $rel;New-Item -ItemType Directory (Split-Path $target -Parent) -Force|Out-Null
 Copy-Item -LiteralPath $p.FullName -Destination $target -Force
 $overlaid[$rel]=(Get-FileHash $p.FullName).Hash
}
if($overlaid.Count -ne 20 -or !$overlaid.ContainsKey('towercontinued\sidejob_repair_sr1\en-us.lipmap')){throw ('Unexpected S30 resources '+$overlaid.Count)}
$final=@{};foreach($p in Get-ChildItem $newSource -File -Recurse){$rel=[IO.Path]::GetRelativePath($newSource,$p.FullName).Replace('/','\');$final[$rel]=(Get-FileHash $p.FullName).Hash;if($baseline.ContainsKey($rel) -and !$overlaid.ContainsKey($rel) -and $final[$rel] -cne $baseline[$rel]){throw ('Unchanged resource drift '+$rel)}}
if($final.Count -ne 1172){throw ('Final member count '+$final.Count)}
$archive=Join-Path $newPackage 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$stream=[IO.File]::Create($archive);$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($newSource),$stream)){throw 'Archive writer failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne $final.Count){throw 'Archive readback count mismatch'}
foreach($e in $packed.Files.Values){$expected=$final[$e.Name];if($null -eq $expected){throw ('Unexpected packed resource '+$e.Name)};$m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};if($hash -cne $expected){throw ('Packed byte mismatch '+$e.Name)}}
$xl=Join-Path $newPackage 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
$oldXL=Get-Content $xl -Raw
$lines=@()
foreach($id in @('mq006_rollercoaster','mws_se5_07','mws_wat_08_trauma_drama')){
 $lines+=,"    - path: towercontinued\sidejobs_s30\entries\$id.questphase`n      parent: ep1\quest\ep1.quest`n      input:`n        node: [1]`n        socket: Out`n"
}
if($oldXL.IndexOf('streaming:') -lt 0){throw 'XL insertion marker missing'}
$newXL=$oldXL.Replace('streaming:',(($lines -join '')+'streaming:'))
if($newXL.Length -le $oldXL.Length){throw 'XL unchanged'}
[IO.File]::WriteAllText($xl,$newXL,[Text.UTF8Encoding]::new($false))
$script=Join-Path $newPackage 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'serialized_02/PTFR_SideJobsS29.reds') -Destination $script -Force
$files=@(Get-ChildItem $newPackage -File -Recurse);if($files.Count -ne 51){throw ('Package file count '+$files.Count)}
$manifest=[ordered]@{status='STAGED_51_FILE_SUCCESSOR_NOT_INSTALLED';source_members=$final.Count;unchanged_members=$baseline.Count-1;new_members=19;replaced_members=1;overlays=$overlaid;archive_sha256=(Get-FileHash $archive).Hash;xl_sha256=(Get-FileHash $xl).Hash;reds_sha256=(Get-FileHash $script).Hash;files=@($files|ForEach-Object {@{path=[IO.Path]::GetRelativePath($newPackage,$_.FullName).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}});game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'manifest.json'),($manifest|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
@{status=$manifest.status;members=$final.Count;files=$files.Count;archive_sha256=$manifest.archive_sha256}|ConvertTo-Json
