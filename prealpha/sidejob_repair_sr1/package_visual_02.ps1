Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$candidate=Join-Path $PSScriptRoot 'candidate_02'
$proof=Get-Content -LiteralPath (Join-Path $candidate 'visual_07/proof.json') -Raw|ConvertFrom-Json
$test1=Get-Content -LiteralPath (Join-Path $candidate 'test_visual_01.json') -Raw|ConvertFrom-Json
$test2=Get-Content -LiteralPath (Join-Path $candidate 'test_visual_02.json') -Raw|ConvertFrom-Json
if($proof.status -cne 'WORKSPACE_VISUAL_SEVEN_RESOURCE_FINAL_NOT_INSTALLED' -or $test1.status -cne 'VISUAL_TWO_RESOURCE_SEMANTIC_PRESERVATION_PASS' -or $test2.status -cne 'VISUAL_FOUR_ADDITIONAL_SCENES_AND_EXACT_KOLD_WORKSPOT_SEMANTIC_PASS'){throw 'Visual proofs missing'}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077';$mods=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $mods 'modlist.txt')){throw 'Explicit mod load order requires review'}
$name='zzzz_PTFR_SideJobs_SR1_Visual2.archive';$archive=Join-Path $candidate ('package/archive/pc/mod/'+$name)
if(Test-Path -LiteralPath $archive){throw 'Visual successor package exists'}
$members=@($proof.prior)+@($proof.additional)+@($proof.new_private_kold)
if($members.Count -ne 7){throw 'Expected seven visual resources'}
$source=Join-Path $candidate 'visual_package_source_02';if(Test-Path -LiteralPath $source){throw 'Visual source output exists'}
$lookup=@{}
foreach($m in $members){$p=Join-Path (Join-Path $candidate 'visual_07') $m.depot;if((Get-FileHash -LiteralPath $p).Hash -cne $m.patched_sha256){throw ('Visual source drift '+$m.depot)};$dest=Join-Path $source $m.depot;New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force|Out-Null;Copy-Item -LiteralPath $p -Destination $dest;$lookup[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($m.depot).ToString()]=$m}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$matches=[Collections.Generic.List[object]]::new()
$files=[string[]]@(Get-ChildItem -LiteralPath $mods -Filter '*.archive' -File|ForEach-Object FullName);[Array]::Sort($files,[StringComparer]::OrdinalIgnoreCase)
foreach($path in $files){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -cne 'NoError'){throw ('Archive read failed: '+$path)}
 foreach($key in $lookup.Keys){$id=[uint64]::Parse($key);if(!$a.Files.ContainsKey($id)){continue};$m=[IO.MemoryStream]::new();try{$a.Files[$id].Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};$matches.Add(@{archive=$path;depot=$lookup[$key].depot;sha256=$hash})}
}
foreach($m in $members){$hits=@($matches|Where-Object {$_.depot -ceq $m.depot});if($null -eq $m.PSObject.Properties['source_sha256']){if($hits.Count -ne 0){throw 'Private workspot collides with installed mod'}}elseif($hits.Count -ne 1 -or $hits[0].sha256 -cne $m.source_sha256 -or [string]::CompareOrdinal($name,[IO.Path]::GetFileName($hits[0].archive)) -le 0){throw ('Winning visual source changed '+$m.depot)}}
New-Item -ItemType Directory -Path (Split-Path $archive -Parent) -Force|Out-Null
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Visual archive writer failed'}}finally{$stream.Dispose()}
$packed=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne 7){throw 'Visual member count mismatch'}
foreach($e in $packed.Files.Values){$m=[IO.MemoryStream]::new();try{$e.Extract($m);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()};$want=@($members|Where-Object {$_.depot -ceq $e.Name});if($want.Count -ne 1 -or $hash -cne $want[0].patched_sha256){throw ('Visual packed readback drift '+$e.Name)}}
$result=[ordered]@{status='STAGED_VISUAL_SEVEN_RESOURCE_ARCHIVE_READBACK_NO_INSTALL';archive=$archive;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;resources=7;existing_collisions=$matches.ToArray();visual_test_01_sha256=(Get-FileHash -LiteralPath (Join-Path $candidate 'test_visual_01.json')).Hash;visual_test_02_sha256=(Get-FileHash -LiteralPath (Join-Path $candidate 'test_visual_02.json')).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $candidate 'package_visual_02.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 30
