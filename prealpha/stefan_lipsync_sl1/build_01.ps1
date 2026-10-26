Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$out=Join-Path $PSScriptRoot 'candidate_01';if(Test-Path -LiteralPath $out){throw 'Use a successor output'}
New-Item -ItemType Directory -Path $out|Out-Null
$inv=Get-Content -LiteralPath (Join-Path $ws 'research/sidejobs_s29/stefan_lipmap_01/inventory.json') -Raw|ConvertFrom-Json -Depth 30
if($inv.rows.Count -ne 1){throw 'Ambiguous English map source'}
$row=$inv.rows[0];$source=Join-Path $ws $row.raw
if((Get-FileHash -LiteralPath $source).Hash -cne $row.sha256){throw 'Source changed'}
$native=(Read-Cr2wFile $source).RootChunk
$old='base\quest\minor_quests\mq036\scenes\mq036_stefan_dialogues.scene'
$private='towercontinued\sidejobs_s29\native\'+$old
$oldHash=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($old)
$newHash=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($private)
$indices=@(for($i=0;$i -lt $native.ScenePaths.Count;$i++){if($native.ScenePaths[$i].ToString() -ceq $oldHash.ToString()){$i}})
if($indices.Count -ne 1 -or @($native.ScenePaths|Where-Object {$_.ToString() -ceq $newHash.ToString()}).Count){throw 'Source registration mismatch'}
$entry=$native.SceneEntries[$indices[0]].DeepCopy()
if($entry.ActorVoiceTags.Count -ne 1 -or $entry.ActorVoiceTags[0].ToString() -cne '1624173162010259716' -or $entry.AnimSets.Count -ne 1){throw 'Unexpected Stefan mapping'}
$map=[WolvenKit.RED4.Types.animLipsyncMapping]::new()
$map.LanguageCodeName='en-us'
$map.ScenePaths.Add([WolvenKit.RED4.Types.CUInt64]::op_Implicit($newHash))
$map.SceneEntries.Add($entry)
$depot='towercontinued\stefan_lipsync_sl1\en-us.lipmap'
$raw=Join-Path $out ('source/'+$depot)
$file=[WolvenKit.RED4.Archive.CR2W.CR2WFile]::new();$file.RootChunk=$map
Write-Cr2wFile $file $raw
$rb=Join-Path $out 'mapping_readback.json';Export-Cr2wJson (Read-Cr2wFile $raw) $rb
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$collisionCount=0
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -Filter '*.archive' -File){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable archive '+$f.Name)}
 if($arc.Files.ContainsKey($key)){throw ('New resource collision '+$f.Name)};$collisionCount++
}
$name='00000000_TowerContinued_StefanLipsync_SL1.archive'
$archive=Join-Path $out ('package/archive/pc/mod/'+$name)
New-Item -ItemType Directory -Path (Split-Path $archive -Parent) -Force|Out-Null
$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc).ToString() -cne 'NoError' -or $arc.Files.Count -ne 1 -or !$arc.Files.ContainsKey($key)){throw 'Packed members mismatch'}
$mem=[IO.MemoryStream]::new();try{$arc.Files[$key].Extract($mem);$packedHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
if($packedHash -cne (Get-FileHash -LiteralPath $raw).Hash){throw 'Packed bytes differ'}
$xl="localization:`n  lipmaps:`n    en-us: $depot`n"
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$proof=[ordered]@{status='PACKED_READBACK_READY_FOR_SEMANTIC_CHECK';source=$row;original_scene=$old;original_hash=$oldHash.ToString();private_scene=$private;private_hash=$newHash.ToString();depot=$depot;map_sha256=$packedHash;archive_sha256=(Get-FileHash -LiteralPath $archive).Hash;xl_sha256=(Get-FileHash -LiteralPath ($archive+'.xl')).Hash;installed_archives_checked=$collisionCount;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'build_01.json'),($proof|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$proof|Select-Object status,private_hash,archive_sha256,installed_archives_checked|ConvertTo-Json
