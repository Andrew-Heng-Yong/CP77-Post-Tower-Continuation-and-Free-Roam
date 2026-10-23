param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\afterlife_world\emmerick_r7'
$out=Join-Path $WorkspaceRoot 'build\AfterlifeEmmerickR7'
$source=Join-Path $out 'source'
New-Item -ItemType Directory -Force $audit,$source|Out-Null
function ReadWorld([string]$path){
 $s=[IO.File]::OpenRead($path)
 try{$rd=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$rd.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($rd.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw "Parse failed $path"};return $f}finally{$s.Dispose()}
}
$r2=Get-Content -LiteralPath (Join-Path $WorkspaceRoot 'research\afterlife_world\population_r2\manifest.json') -Raw|ConvertFrom-Json
$hashes=[ordered]@{}
foreach($relative in $r2.resources){
 $from=Join-Path $r2.source_root $relative;$to=Join-Path $source $relative
 $expected=@($r2.payloads|Where-Object {$_.depot -eq $relative})
 if($expected.Count -ne 1 -or (Get-FileHash -LiteralPath $from).Hash -ne $expected[0].sha256){throw "R2 source mismatch $relative"}
 $hashes[$from]=(Get-FileHash -LiteralPath $from).Hash
 New-Item -ItemType Directory -Force (Split-Path $to)|Out-Null
 Copy-Item -LiteralPath $from -Destination $to
}
$sectorPath=Join-Path $WorkspaceRoot 'research\afterlife_world\patron_world_sources\raw\base\worlds\03_night_city\_compiled\default\quest_1d80ac67f39864eb.streamingsector'
$registryPath=Join-Path $WorkspaceRoot 'research\phase2b_p4\staging_scan\ep1_1_nightcity\raw\base\worlds\03_night_city\_compiled\default\always_loaded_1.streamingsector'
foreach($p in @($sectorPath,$registryPath)){$hashes[$p]=(Get-FileHash -LiteralPath $p).Hash}
$vanilla=ReadWorld $sectorPath
$original=ReadWorld $registryPath
# Inspector's position matches entrance02 (node97), not entrance (node84).
$vanillaNode=$vanilla.RootChunk.Nodes[97].Chunk
$datum=@($vanilla.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq '97'})
if($datum.Count -ne 1 -or -not $datum[0].QuestPrefabRefHash.ToString().EndsWith('/#q103_ws_emmerick_entrance02')){throw 'Observed entrance02 source mismatch'}
$oldHash=$datum[0].QuestPrefabRefHash.GetRedHash().ToString()
$pd=@($original.RootChunk.Nodes[3256].Chunk.WorkspotsPersistentData|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $oldHash})
if($pd.Count -ne 1){throw 'Vanilla persistent workspot descriptor ambiguous'}
$animation='base\workspots\common\ground\generic__stand_ground__stand_around__04.workspot'
if($vanillaNode.Spot.Chunk.Resource.DepotPath.ToString() -ne $animation -or $vanillaNode.IsWorkspotInfinite.ToString() -ne 'True' -or $vanillaNode.Spot.Chunk.MasterNodeRef.ToString() -notin @('0','') -or $vanillaNode.LookAtTarget.ToString() -notin @('0','')){throw 'Unexpected workspot dependencies/animation'}
$spotsRel='towercontinued\afterlife_r1\patrons_spots.streamingsector'
$regRel='towercontinued\afterlife_r1\patrons_registry.streamingsector'
$spots=ReadWorld (Join-Path $source $spotsRel)
$registry=ReadWorld (Join-Path $source $regRel)
if($spots.RootChunk.Nodes.Count -ne 79){throw 'Unexpected private spot count'}
$target=$spots.RootChunk.Nodes[78].Chunk
$privateDatum=@($spots.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq '78'})[0]
$privateRef='$/03_night_city/#PTFRAL1_PatronSpot78'
if($privateDatum.QuestPrefabRefHash.ToString() -ne $privateRef){throw 'Private Emmerick identity mismatch'}
$newNode=$vanillaNode.DeepCopy()
$newNode.DebugName=$target.DebugName
$newNode.SourcePrefabHash=$target.SourcePrefabHash
$spots.RootChunk.Nodes[78].Chunk=$newNode
# Retain private identity, metadata and stream envelope; copy authored transform.
foreach($property in @('Position','Orientation','Scale','Bounds')){$privateDatum.$property=$datum[0].$property.DeepCopy()}
$privateHash=$privateDatum.QuestPrefabRefHash.GetRedHash().ToString()
$privatePd=@($registry.RootChunk.Nodes[0].Chunk.WorkspotsPersistentData|Where-Object {$_.GlobalNodeId.Hash.ToString() -eq $privateHash})
if($privatePd.Count -ne 1){throw 'Private persistent descriptor ambiguous'}
$privatePd[0].WorldPosition=$pd[0].WorldPosition.DeepCopy()
$privatePd[0].Yaw=$pd[0].Yaw
# Its compiled area remains the same one-entry/one-spot metadata, reanchored only.
$areaDatum=@($registry.RootChunk.NodeData.Data|Where-Object {$_.NodeIndex.ToString() -eq '2'})
if($areaDatum.Count -ne 1){throw 'Private area placement ambiguous'}
foreach($property in @('Position','Orientation','Scale','Bounds')){$areaDatum[0].$property=$datum[0].$property.DeepCopy()}
Write-Cr2wFile $spots (Join-Path $source $spotsRel)
Write-Cr2wFile $registry (Join-Path $source $regRel)
Export-Cr2wJson $spots (Join-Path $audit 'patrons_spots.streamingsector.json')
Export-Cr2wJson $registry (Join-Path $audit 'patrons_registry.streamingsector.json')
Export-Cr2wJson $vanilla (Join-Path $audit 'vanilla_entrance.streamingsector.json')
[IO.File]::WriteAllText((Join-Path $audit 'vanilla_persistent.json'),([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($pd[0])),[Text.UTF8Encoding]::new($false))
$archive=Join-Path $out 'TowerContinued_AfterlifeR1.archive'
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -ne 'NoError'){throw 'Readback failed'}
if(@(Compare-Object @($r2.resources|Sort-Object) @($packed.Files.Values|ForEach-Object {$_.Name}|Sort-Object)).Count){throw 'Unexpected archive scope'}
foreach($p in $packed.Files.Values){$ms=[IO.MemoryStream]::new();try{$p.Extract($ms);$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($ms.ToArray()))}finally{$ms.Dispose()};if($actual -ne (Get-FileHash -LiteralPath (Join-Path $source $p.Name)).Hash){throw 'Packed bytes mismatch'}}
foreach($p in $hashes.Keys){if((Get-FileHash -LiteralPath $p).Hash -ne $hashes[$p]){throw 'Source changed'}}
$manifest=@{status='BUILT_R7_NOT_INSTALLED_NOT_LIVE';archive=$archive;sha256=(Get-FileHash -LiteralPath $archive).Hash;resources=@($r2.resources);source_root=$source;source_hashes=$hashes;packed_readback=$true;replacements=1;changed_payloads=@($spotsRel,$regRel);unchanged_r2_payloads=8;original_resource_overrides=0;new_actor_identities=0;story_writes=0;private_ref=$privateRef;original_spot=$datum[0].QuestPrefabRefHash.ToString();source_node=97;animation=$animation;preserved_private_phase_label='q005_emmerick_bouncer';position=@($datum[0].Position.X.ToString(),$datum[0].Position.Y.ToString(),$datum[0].Position.Z.ToString())}
[IO.File]::WriteAllText((Join-Path $audit 'manifest.json'),($manifest|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$manifest|Select-Object status,sha256,packed_readback,unchanged_r2_payloads|ConvertTo-Json
