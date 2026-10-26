Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
. (Join-Path $ws 'tools/shark_b7_2_helpers.ps1')
$build=Join-Path $PSScriptRoot 'native_02';$out=Join-Path $PSScriptRoot 'candidate_01'
$m=Get-Content -LiteralPath (Join-Path $build 'component.json') -Raw|ConvertFrom-Json
$test=Get-Content -LiteralPath (Join-Path $build 'tests_02.json') -Raw|ConvertFrom-Json
if($test.status -cne 'PASS_OFFLINE_NOT_GAMEPLAY' -or $test.component_sha256 -cne (Get-FileHash (Join-Path $build 'component.json')).Hash){throw 'Stale tests'}
$compiled=Get-Content -LiteralPath (Join-Path $out 'compile_04/result.json') -Raw|ConvertFrom-Json
if($compiled.status -cne 'PASS_FULL_SCC_NOT_LIVE' -or !$compiled.full_scc_equipmentex -or $test.compiled_sha256 -cne $compiled.compiled_sha256){throw 'Combined compile required'}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077';$mods=Join-Path $game 'archive/pc/mod'
if(Test-Path (Join-Path $mods 'modlist.txt')){throw 'Explicit load order requires review'}
$name='000000000_TowerContinued_JD1.archive';$archive=Join-Path $out ('package/archive/pc/mod/'+$name)
if(Test-Path $archive){throw 'Use successor'}
B71Parser|Out-Null;$inventory=@(B72Inventory $game)
$stock=Get-Content -LiteralPath (Join-Path $ws 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id);$injections=@()
foreach($dep in $m.boots){$id=B72Id ($dep+':1');if($id -in $used -or $id -ne (B72IdIndependent ($dep+':1'))){throw 'Injection collision'};$used+=,$id;$injections+=,@{depot=$dep;id=$id}}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$keys=@{}
foreach($r in $m.resources.PSObject.Properties){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($r.Name)]=$r.Name;if((Get-FileHash (Join-Path (Join-Path $build 'source') $r.Name)).Hash -cne $r.Value){throw 'Resource drift'}}
$sources=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'research_01/inventory.json') -Raw|ConvertFrom-Json
$donors=@{}
foreach($pair in @(@('towercontinued\sidejobs_s23\base_b\mq038.questphase','0000_TowerContinued_SideJobs_S23.archive'),@('towercontinued\gig_phone_u9\fixer_cleanup.questphase','00000000_TowerContinued_SideJobs_S29.archive'))){
 $r=@($sources|Where-Object {$_.depot -ceq $pair[0] -and [IO.Path]::GetFileName($_.archive) -ceq $pair[1]});if($r.Count -ne 1){throw 'Ambiguous donor'};$donors[$pair[0]]=$r[0].sha256
}
$seen=@{};$collisions=@();$paths=[string[]]@(Get-ChildItem -LiteralPath $mods -Filter '*.archive' -File|ForEach-Object FullName);[Array]::Sort($paths,[StringComparer]::OrdinalIgnoreCase)
foreach($path in $paths){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($key in $keys.Keys){if(!$a.Files.ContainsKey([uint64]$key)){continue};$dep=$keys[$key]
  if(!$donors.ContainsKey($dep)){throw ('Unexpected override '+$dep)}
  $mem=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($mem);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
  if(!$seen.ContainsKey($dep)){if($hash -cne $donors[$dep] -or [string]::CompareOrdinal($name,[IO.Path]::GetFileName($path)) -ge 0){throw 'Wrong winning donor or load order'};$seen[$dep]=$true}
  $collisions+=,@{archive=$path;depot=$dep;sha256=$hash}
 }
}
if($seen.Count -ne 2){throw 'Missing donor'}
New-Item -ItemType Directory -Force -Path (Split-Path $archive -Parent)|Out-Null
$stream=[IO.File]::Create($archive);try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $build 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$a).ToString() -ne 'NoError' -or $a.Files.Count -ne 3){throw 'Packed resource count wrong'}
foreach($e in $a.Files.Values){$mem=[IO.MemoryStream]::new();try{$e.Extract($mem);$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()};if($hash -cne $m.resources.($e.Name)){throw 'Packed readback mismatch'}}
$xl=B71Render $m.boots;B71Parse $xl|Out-Null;[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$proof=@{status='PASS_PACKED_READBACK_AND_LOAD_ORDER';archive=$archive;sha256=(Get-FileHash $archive).Hash;resources=3;injections=$injections;donors=$donors;override_sources=$collisions;component_sha256=(Get-FileHash (Join-Path $build 'component.json')).Hash;compiled_sha256=$compiled.compiled_sha256;game_writes=0}
$proof|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $out 'package_proof_01.json') -Encoding utf8
@{status=$proof.status;resources=3;injections=1;sha256=$proof.sha256}|ConvertTo-Json
