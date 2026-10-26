Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $ws 'tools/shark_b7_2_helpers.ps1')
$build=Join-Path $PSScriptRoot 'build/native_04';$out=Join-Path $PSScriptRoot 'candidate_01';$m=Get-Content (Join-Path $build 'component.json') -Raw|ConvertFrom-Json -Depth 100
$test=Get-Content (Join-Path $build 'tests_01.json') -Raw|ConvertFrom-Json
if($test.status -cne 'PASS_OFFLINE_NOT_GAMEPLAY' -or $test.component_sha256 -cne (Get-FileHash (Join-Path $build 'component.json')).Hash){throw 'Native tests missing or stale'}
$compiled=Get-Content (Join-Path $out 'compile_04/result.json') -Raw|ConvertFrom-Json
if($compiled.status -cne 'PASS_FULL_SCC_NOT_LIVE' -or !$compiled.full_scc_equipmentex){throw 'Combined SCC required'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$mods=Join-Path $game 'archive/pc/mod'
if(Test-Path (Join-Path $mods 'modlist.txt')){throw 'Explicit load order requires review'}
$name='00000000_TowerContinued_SideJobs_S29.archive';$archive=Join-Path $out ('package/archive/pc/mod/'+$name)
if(Test-Path $archive){throw 'Use successor packaging output'}
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content (Join-Path $ws 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id);$injections=@()
foreach($dep in $m.boots){$id=B72Id ($dep+':1');if($id -in $used -or $id -ne (B72IdIndependent ($dep+':1'))){throw "Injection collision $dep id=$id"};$used+=,$id;$injections+=,@{depot=$dep;id=$id}}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{}
foreach($r in $m.resources.PSObject.Properties){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.Name)]=$r.Name;if((Get-FileHash (Join-Path (Join-Path $build 'source') $r.Name)).Hash -cne $r.Value){throw 'Resource drift'}}
$cleanup='towercontinued\gig_phone_u9\fixer_cleanup.questphase';$donorHash=(Get-FileHash (Join-Path $ws $m.cleanup_donor)).Hash;$collisions=@();$seenCleanup=$false
foreach($f in Get-ChildItem -LiteralPath $mods -Filter '*.archive' -File|Sort-Object Name){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw ('Cannot read '+$f.Name)}
 foreach($key in $keys.Keys){if(!$a.Files.ContainsKey([uint64]$key)){continue};$dep=$keys[$key]
  if($dep -cne $cleanup){throw "Unexpected resource override: $dep"}
  $mem=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($mem);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
  if(!$seenCleanup){if($h -cne $donorHash -or [string]::CompareOrdinal($name,$f.Name) -ge 0){throw 'Wrong winning cleanup donor/order'};$seenCleanup=$true}
  $collisions+=,@{archive=$f.FullName;depot=$dep;sha256=$h}
 }
}
if(!$seenCleanup){throw 'Current cleanup not found'}
New-Item -ItemType Directory -Path (Split-Path $archive -Parent) -Force|Out-Null
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $build 'source')),$stream)){throw 'Archive pack failed'}}finally{$stream.Dispose()}
$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$a).ToString() -ne 'NoError' -or $a.Files.Count -ne @($m.resources.PSObject.Properties).Count){throw 'Packed resource count mismatch'}
foreach($e in $a.Files.Values){$mem=[IO.MemoryStream]::new();try{$e.Extract($mem);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()};if($h -cne $m.resources.($e.Name)){throw 'Packed resource readback mismatch'}}
$xl=B71Render $m.boots;B71Parse $xl|Out-Null;[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$proof=[ordered]@{status='PASS_PACKED_READBACK_AND_LOAD_ORDER';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=$a.Files.Count;injections=$injections;installed_injections=$inventory;allowed_override=$cleanup;donor_sha256=$donorHash;override_sources=$collisions;component_sha256=(Get-FileHash (Join-Path $build 'component.json')).Hash;tests_sha256=(Get-FileHash (Join-Path $build 'tests_01.json')).Hash;compiled_sha256=$compiled.compiled_sha256;packager_sha256=(Get-FileHash $PSCommandPath).Hash}
[IO.File]::WriteAllText((Join-Path $out 'package_proof_01.json'),($proof|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
@{status=$proof.status;resources=$a.Files.Count;injections=$injections.Count;sha256=$proof.sha256}|ConvertTo-Json
