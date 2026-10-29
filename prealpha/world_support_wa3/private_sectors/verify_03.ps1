# Independent native/candidate readback; builder proof is not used as an oracle.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
function ReadWorld([string]$path){$s=[IO.File]::OpenRead($path);try{$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($r.ReadFile([ref]$f,$true).ToString() -cne 'NoError'){throw 'Native/candidate read failed'};return $f}finally{$s.Dispose()}}
function Json($x){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($x,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function BytesHash([byte[]]$x){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($x))}
$checks=[Collections.Generic.List[string]]::new()
function Check([string]$label,[bool]$value){if(!$value){throw $label};$checks.Add($label)}
$source=Join-Path $PSScriptRoot 'source_03'
$out=Join-Path $PSScriptRoot 'verification_03.json';if(Test-Path -LiteralPath $out){throw 'Preserve verification'}
$specs=@(@{id=160;stem='quest_da3955dd67711180';drop=@(42,43);expected=44;spots=36},@{id=161;stem='quest_0b5baaafb70a2a64';drop=@(38);expected=40;spots=34})
$nativeBlockPath=Join-Path $PSScriptRoot '../environment_variants/extract_01/ep1_1_nightcity_539214763179621144.streamingblock'
$nativeBlock=ReadWorld $nativeBlockPath
$blockDepot='towercontinued\world_support_wa3\filtered_support.streamingblock';$blockPath=Join-Path $source $blockDepot;$block=ReadWorld $blockPath
Check 'Private block has exactly two descriptor registrations' ($block.RootChunk.Descriptors.Count -eq 2)
Check 'Private block preserves exact native root index' ((Json $block.RootChunk.Index) -ceq (Json $nativeBlock.RootChunk.Index))
$rows=@();$targetDepots=@($blockDepot,'base\worlds\03_night_city\_compiled\default\blocks\all.streamingblock')
$pins=@($nativeBlockPath,$blockPath,(Join-Path $PSScriptRoot 'verify_03.ps1'),(Join-Path $PSScriptRoot 'build_03.ps1'),(Join-Path $ws 'research/framework_pr63_01/codeware/src/Red/StreamingSector.hpp'),(Join-Path $ws 'research/framework_pr63_01/archivexl/src/App/Extensions/WorldStreaming/Extension.cpp'),(Join-Path $ws 'research/framework_pr63_01/archivexl/src/App/Extensions/ResourcePatch/Extension.cpp'))
foreach($spec in $specs){
 $nativePath=Join-Path $PSScriptRoot ('../extracted_01/basegame_3_nightcity.archive/'+$spec.stem+'.streamingsector')
 $native=ReadWorld $nativePath
 $privateRef='$/03_night_city/towercontinued/world_support_wa3/group'+$spec.id+'_support'
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($privateRef)
 $depot='base\worlds\03_night_city\_compiled\default\quest_'+$hash.ToString('x16')+'.streamingsector'
 $path=Join-Path $source $depot;$candidate=ReadWorld $path
 $pins+=@($nativePath,$path);$targetDepots+=@($depot,('base\worlds\03_night_city\_compiled\default\'+$spec.stem+'.streamingsector'))
 $n=$native.RootChunk;$c=$candidate.RootChunk
 Check ($spec.id.ToString()+': exact native/candidate node count') ($n.Nodes.Count -eq $spec.expected -and $c.Nodes.Count -eq $spec.expected-$spec.drop.Count)
 Check ($spec.id.ToString()+': current68 sector layout preserved') ($n.Version.ToString() -ceq '68' -and $c.Version.ToString() -ceq '68')
 Check ($spec.id.ToString()+': complete native NodeRef table preserved') ((@($n.NodeRefs|ForEach-Object ToString)-join "`n") -ceq (@($c.NodeRefs|ForEach-Object ToString)-join "`n"))
 $nativeMeta=Json $n|ConvertFrom-Json -Depth 100;$candidateMeta=Json $c|ConvertFrom-Json -Depth 100
 foreach($prop in @('category','cookingPlatform','externInplaceResource','level','localInplaceResource','persistentNodeIndex','persistentNodes','variantIndices','variantNodes')){Check ($spec.id.ToString()+': sector metadata '+$prop) (($nativeMeta.$prop|ConvertTo-Json -Depth 100 -Compress) -ceq ($candidateMeta.$prop|ConvertTo-Json -Depth 100 -Compress))}
 $expectedNodes=@();$mapping=@{};$keptSpots=0
 for($i=0;$i -lt $n.Nodes.Count;$i++){
  $node=$n.Nodes[$i].Chunk
  if($spec.drop -contains $i){Check ($spec.id.ToString()+': removed node is auto-start preview '+$i) ($node.GetType().Name -ceq 'worldPopulationSpawnerNode' -and $node.SpawnOnStart.ToString() -ceq 'True');continue}
  $j=$expectedNodes.Count;$mapping[$i]=$j;$expectedNodes+=,$node
  Check ($spec.id.ToString()+': exact retained node payload '+$i) ((Json $node) -ceq (Json $c.Nodes[$j].Chunk))
  if($node.GetType().Name -ceq 'worldAISpotNode'){$keptSpots++}
 }
 Check ($spec.id.ToString()+': all native workspot definitions retained') ($keptSpots -eq $spec.spots)
 Check ($spec.id.ToString()+': no remaining population-spawner definition') (@($c.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'worldPopulationSpawnerNode'}).Count -eq 0)
 $nb=$n.NodeData.Buffer.GetBytes();$cb=$c.NodeData.Buffer.GetBytes();$expected=[Collections.Generic.List[byte]]::new();$retained=0;$removed=0
 Check ($spec.id.ToString()+': complete144-byte placement records') ($nb.Length%144 -eq 0 -and $cb.Length%144 -eq 0)
 for($offset=0;$offset -lt $nb.Length;$offset+=144){
  $bits=[BitConverter]::ToUInt64($nb,$offset+0x70);$index=[int]($bits -band [uint64]0x7FFFF)
  if($spec.drop -contains $index){$removed++;continue}
  $record=[byte[]]$nb[$offset..($offset+143)];$newBits=($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$mapping[$index]
  [Array]::Copy([BitConverter]::GetBytes($newBits),0,$record,0x70,8);$expected.AddRange($record);$retained++
 }
 Check ($spec.id.ToString()+': exactly preview placements removed') ($removed -eq $spec.drop.Count)
 Check ($spec.id.ToString()+': every retained byte unchanged except node index relocation') ((BytesHash $expected.ToArray()) -ceq (BytesHash $cb))
 Check ($spec.id.ToString()+': retained globalNodeID and proxy IDs unchanged') ($retained*144 -eq $cb.Length)
 $originalDescriptor=@($nativeBlock.RootChunk.Descriptors|Where-Object {$_.Data.DepotPath.ToString().EndsWith($spec.stem+'.streamingsector')})
 $privateDescriptor=@($block.RootChunk.Descriptors|Where-Object {$_.QuestPrefabNodeRef.ToString() -ceq $privateRef})
 Check ($spec.id.ToString()+': exact native and private descriptor lookup') ($originalDescriptor.Count -eq 1 -and $privateDescriptor.Count -eq 1)
 $d=$privateDescriptor[0];Check ($spec.id.ToString()+': descriptor preserves exact native block index') ((Json $d.BlockIndex) -ceq (Json $originalDescriptor[0].BlockIndex));Check ($spec.id.ToString()+': private descriptor targets exact engine-hash sector') ($d.Data.DepotPath.ToString() -ceq $depot)
 Check ($spec.id.ToString()+': private descriptor stays Quest gated') ($d.Category.ToString() -ceq 'Quest' -and $d.Level.ToString() -ceq '0' -and $d.NumNodeRanges.ToString() -ceq '1' -and $d.Variants.Count -eq 0)
 $comparison=$d.DeepCopy();$comparison.Data=$originalDescriptor[0].Data;$comparison.QuestPrefabNodeRef=$originalDescriptor[0].QuestPrefabNodeRef
 Check ($spec.id.ToString()+': only descriptor resource and owner ref changed') ((Json $comparison) -ceq (Json $originalDescriptor[0]))
 # Negative controls operate on serialized output bytes, not the builder's stated success.
 $bad=[byte[]]$cb.Clone();$bad[0x58]=$bad[0x58] -bxor 1
 Check ($spec.id.ToString()+': altered workspot/global ID negative control rejected') ((BytesHash $bad) -cne (BytesHash $expected.ToArray()))
 Check ($spec.id.ToString()+': unfiltered native placement negative control rejected') ((BytesHash $nb) -cne (BytesHash $expected.ToArray()))
 $rows+=@{group=$spec.id;depot=$depot;prefab_ref=$privateRef;node_ref_hash=$hash.ToString();sha256=(Get-FileHash -LiteralPath $path).Hash;native_sha256=(Get-FileHash -LiteralPath $nativePath).Hash;retained_nodes=$c.Nodes.Count;retained_placements=$retained;retained_workspots=$keptSpots;removed_preview_nodes=$spec.drop;placement_sha256=BytesHash $cb}
}
# All current archives, including the three user additions, are checked for old/native and new depots.
$wanted=@{};foreach($depot in $targetDepots){$wanted[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()]=$depot}
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File)
$hits=@()
foreach($archive in $archives){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw 'Archive read failed'};foreach($key in $wanted.Keys){if($a.Files.ContainsKey([uint64]$key)){$e=$a.Files[[uint64]$key];$s=[IO.MemoryStream]::new();try{$e.Extract($s);$hits+=@{depot=$wanted[$key];archive=$archive.FullName;sha256=BytesHash $s.ToArray()}}finally{$s.Dispose()}}}}
foreach($r in $rows){Check ($r.group.ToString()+': private sector absent from every installed archive') (@($hits|Where-Object depot -eq $r.depot).Count -eq 0);$stem=($specs|Where-Object id -eq $r.group).stem;$nativeHits=@($hits|Where-Object {$_.depot.EndsWith($stem+'.streamingsector')});Check ($r.group.ToString()+': one official native sector winner with exact donor bytes') ($nativeHits.Count -eq 1 -and [IO.Path]::GetFileName($nativeHits[0].archive) -ceq 'basegame_3_nightcity.archive' -and $nativeHits[0].sha256 -ceq $r.native_sha256)}
Check 'Private streaming block absent from every installed archive' (@($hits|Where-Object depot -eq $blockDepot).Count -eq 0)
$blockHits=@($hits|Where-Object {$_.depot.EndsWith('all.streamingblock')});Check 'Only official base andEP1 native streaming block winners' ((@($blockHits|ForEach-Object {[IO.Path]::GetFileName($_.archive)}|Sort-Object)-join ';') -ceq 'basegame_3_nightcity.archive;ep1_1_nightcity.archive')
Check 'Selected EP1 block donor exactly matches current winner' (@($blockHits|Where-Object {([IO.Path]::GetFileName($_.archive) -ceq 'ep1_1_nightcity.archive') -and $_.sha256 -ceq (Get-FileHash -LiteralPath $nativeBlockPath).Hash}).Count -eq 1)
$resources=@($rows|ForEach-Object {@{depot=$_.depot;sha256=$_.sha256}})+@(@{depot=$blockDepot;sha256=(Get-FileHash -LiteralPath $blockPath).Hash})
$result=@{status='PASS_PRIVATE_160_161_FILTERED_SECTORS_STATIC';checks_passed=$checks.Count;checks=@($checks.ToArray());groups=$rows;resources=$resources;sector_bindings=@($rows|ForEach-Object {@{depot=$_.depot;prefab_ref=$_.prefab_ref;node_ref_hash=$_.node_ref_hash}});streaming_blocks=@($blockDepot);archive_census_count=$archives.Count;archive_hits=$hits;negative_controls=4;native_resource_overrides=0;native_community_ids_changed=0;retained_workspot_ids_changed=0;limits=@('Private quest descriptors still require the corresponding guarded private PhaseInstancePrefabs owners and the block registered exactly once through ArchiveXL.','Native workspot identities are intentionally retained; native old prefab owner must remain retired under completed-Tower ancestry.','Static graph/resource verification is not live streaming, speech or reload verification.');game_writes=0;save_writes=0;pins=@($pins|Select-Object -Unique|ForEach-Object {@{path=[IO.Path]::GetFullPath($_);sha256=(Get-FileHash -LiteralPath $_).Hash}})}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 30)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;checks=$checks.Count;archive_count=$archives.Count;sha256=(Get-FileHash -LiteralPath $out).Hash}|ConvertTo-Json
