Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ReadWorld([string]$p){$s=[IO.File]::OpenRead($p);try{$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($r.ReadFile([ref]$f,$true).ToString() -cne 'NoError'){throw 'World read failed'};return $f}finally{$s.Dispose()}}
function Json($x){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($x,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function BytesHash([byte[]]$b){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$checks=[Collections.Generic.List[string]]::new();$pins=[Collections.Generic.List[object]]::new();$rows=@();$resources=@()
function Check($label,$ok){if(!$ok){throw $label};$checks.Add($label)}
function Pin($p){$pins.Add(@{path=[IO.Path]::GetFullPath($p);sha256=(Get-FileHash -LiteralPath $p).Hash})}
$out=Join-Path $PSScriptRoot 'verification_ep1_01.json';if(Test-Path $out){throw 'Preserve independent proof'}
$source=Join-Path $PSScriptRoot 'source_ep1_01';$review=Join-Path $PSScriptRoot '../native_review'
$specPaths=@('ep1_1103_filter_spec_01.json','ep1_1107_filter_spec_02.json','ep1_1108_filter_spec_02.json','ep1_1111_filter_spec_02.json')|ForEach-Object {Join-Path $review $_}
$specs=@($specPaths|ForEach-Object {Pin $_;Get-Content -LiteralPath $_ -Raw|ConvertFrom-Json -Depth 80});$hp=@($specs|Where-Object id -eq 1111)[0]
$nb=ReadWorld $hp.native_block_raw;$blockDepot='towercontinued\world_support_wa3\filtered_support_ep1.streamingblock';$blockPath=Join-Path $source $blockDepot;$pb=ReadWorld $blockPath
$nativeDescriptors=@($nb.RootChunk.Descriptors);$privateDescriptors=@($pb.RootChunk.Descriptors)
Check 'Exactly four private EP1 quest descriptors' ($privateDescriptors.Count -eq 4)
Check 'Exact native EP1 block index' ((Json $pb.RootChunk.Index) -ceq (Json $nb.RootChunk.Index))
$nb.RootChunk.Descriptors.Clear();$pb.RootChunk.Descriptors.Clear()
Check 'All other block root fields preserved' ((Json $pb.RootChunk) -ceq (Json $nb.RootChunk))
Pin $hp.native_block_raw;Pin $blockPath
$targetDepots=@($blockDepot,'base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock')
foreach($spec in $specs){
 $id=[int]$spec.id;$native=ReadWorld $spec.sector_raw;$n=$native.RootChunk
 $privateRef='$/03_night_city/towercontinued/world_support_wa3/group'+$id+'_support';$hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($privateRef)
 $depot='base\worlds\03_night_city\_compiled\default\ep1\quest_'+$hash.ToString('x16')+'.streamingsector';$path=Join-Path $source $depot;$candidate=ReadWorld $path;$c=$candidate.RootChunk
 $targetDepots+=@($spec.sector_resource,$depot);Pin $path;Pin $spec.sector_raw
 Check "$id exact native donor" ((Get-FileHash $spec.sector_raw).Hash -ceq $spec.sector_sha256)
 Check "$id current68 native layout" ($n.Version.ToString() -ceq '68' -and $c.Version.ToString() -ceq '68')
 Check "$id node counts" ($n.Nodes.Count -eq @{1103=486;1107=124;1108=71;1111=347}[$id] -and $c.Nodes.Count -eq $n.Nodes.Count-$spec.drop_nodes.Count)
 $dropTypes=if($id -eq 1103){@('worldDeviceNode','worldTriggerAreaNode')}elseif($id -eq 1111){@('worldTriggerAreaNode','worldInterestingConversationsAreaNode','worldAudioAttractAreaNode')}else{@('worldTriggerAreaNode')}
 $expectedDrop=@(for($i=0;$i -lt $n.Nodes.Count;$i++){if($n.Nodes[$i].Chunk.GetType().Name -in $dropTypes){$i}})
 Check "$id complete selected stateful node family removed" ((@($expectedDrop|Sort-Object)-join ',') -ceq (@($spec.drop_nodes|Sort-Object)-join ','))
 $allowed=if($id -eq 1103){@('worldAISpotNode','worldSmartObjectNode','worldPatrolSplineNode','worldGuardAreaNode','worldPopulationSpawnerNode')}elseif($id -eq 1111){@('worldAISpotNode','worldGuardAreaNode','worldSmartObjectNode')}elseif($id -eq 1107){@('worldAISpotNode','worldPatrolSplineNode','worldGuardAreaNode')}else{@('worldAISpotNode','worldInterestingConversationsAreaNode','worldPatrolSplineNode')}
 Check "$id exact retained support families" (@($c.Nodes|Where-Object {$_.Chunk.GetType().Name -cnotin $allowed}).Count -eq 0)
 $mapping=@{};$next=0;$spots=0;$previews=0
 for($i=0;$i -lt $n.Nodes.Count;$i++){
  if($expectedDrop -contains $i){continue}
  $mapping[$i]=$next;Check "$id unchanged retained node$i" ((Json $n.Nodes[$i].Chunk) -ceq (Json $c.Nodes[$next].Chunk))
  if($c.Nodes[$next].Chunk.GetType().Name -ceq 'worldAISpotNode'){$spots++}
  if($c.Nodes[$next].Chunk.GetType().Name -ceq 'worldPopulationSpawnerNode'){$previews++;$node=$c.Nodes[$next].Chunk;Check "$id preview$i remains nonautomatic" ($node.SpawnOnStart.ToString() -ceq 'False' -and $node.AlwaysSpawned.ToString() -cin @('false_','default__false_'))}
  $next++
 }
 Check "$id all native AI spots retained" ($spots -eq @{1103=226;1107=93;1108=61;1111=232}[$id])
 Check "$id exact disabled preview count" ($previews -eq $(if($id -eq 1103){19}else{0}))
 Check "$id native NodeRef table retained" ((@($n.NodeRefs|ForEach-Object ToString)-join '|') -ceq (@($c.NodeRefs|ForEach-Object ToString)-join '|'))
 $nm=Json $n|ConvertFrom-Json -Depth 100;$cm=Json $c|ConvertFrom-Json -Depth 100
 foreach($prop in @('category','cookingPlatform','externInplaceResource','level','localInplaceResource','persistentNodeIndex','persistentNodes','variantIndices','variantNodes')){Check "$id native metadata $prop" (($nm.$prop|ConvertTo-Json -Depth 100 -Compress) -ceq ($cm.$prop|ConvertTo-Json -Depth 100 -Compress))}
 $raw=$n.NodeData.Buffer.GetBytes();$actual=$c.NodeData.Buffer.GetBytes();Check "$id complete144byte placements" ($raw.Length%144 -eq 0 -and $actual.Length%144 -eq 0)
 $expected=[Collections.Generic.List[byte]]::new();$removed=@()
 for($offset=0;$offset -lt $raw.Length;$offset+=144){
  $bits=[BitConverter]::ToUInt64($raw,$offset+0x70);$index=[int]($bits -band [uint64]0x7FFFF)
  if($expectedDrop -contains $index){$removed+=($offset/144);continue}
  $record=[byte[]]$raw[$offset..($offset+143)];$bits=($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$mapping[$index]
  [Array]::Copy([BitConverter]::GetBytes($bits),0,$record,0x70,8);$expected.AddRange($record)
 }
 Check "$id exact removed placements" ((@($removed|Sort-Object)-join ',') -ceq (@($spec.drop_placements|Sort-Object)-join ','))
 Check "$id every retained placement byte unchanged except node index" ((BytesHash $actual) -ceq (BytesHash $expected.ToArray()))
 $nd=@($nativeDescriptors|Where-Object {$_.Data.DepotPath.ToString() -ceq $spec.sector_resource});$pd=@($privateDescriptors|Where-Object {$_.QuestPrefabNodeRef.ToString() -ceq $privateRef})
 Check "$id unique descriptor pair" ($nd.Count -eq 1 -and $pd.Count -eq 1)
 Check "$id native descriptor owner is exact" ($nd[0].QuestPrefabNodeRef.ToString() -ceq $spec.native_prefab)
 Check "$id private descriptor has exact enginehash resource" ($pd[0].Data.DepotPath.ToString() -ceq $depot -and $pd[0].Category.ToString() -ceq 'Quest')
 $copy=$pd[0].DeepCopy();$copy.Data=$nd[0].Data;$copy.QuestPrefabNodeRef=$nd[0].QuestPrefabNodeRef
 Check "$id only descriptor owner/data changed" ((Json $copy) -ceq (Json $nd[0]))
 $bad=[byte[]]$actual.Clone();$bad[0x58]=$bad[0x58] -bxor 1
 Check "$id mutated global ID negative control rejected" ((BytesHash $bad) -cne (BytesHash $expected.ToArray()))
 Check "$id native unfiltered negative control rejected" ((BytesHash $raw) -cne (BytesHash $expected.ToArray()))
 $rows+=@{group=$id;depot=$depot;prefab_ref=$privateRef;node_ref_hash=$hash.ToString();sha256=(Get-FileHash $path).Hash;native_sha256=$spec.sector_sha256;retained_spots=$spots;retained_previews=$previews;removed_nodes=$expectedDrop}
 $resources+=@{depot=$depot;sha256=(Get-FileHash $path).Hash}
}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$wanted=@{};foreach($d in $targetDepots){$wanted[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($d).ToString()]=$d}
$archives=@(Get-ChildItem -LiteralPath 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc' -Recurse -Filter '*.archive' -File);$hits=@()
foreach($archive in $archives){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive.FullName,$hs,[ref]$a).ToString() -cne 'NoError'){throw 'Archive read failure'};foreach($key in $wanted.Keys){if($a.Files.ContainsKey([uint64]$key)){$s=[IO.MemoryStream]::new();try{$a.Files[[uint64]$key].Extract($s);$hits+=@{depot=$wanted[$key];archive=$archive.FullName;sha256=BytesHash $s.ToArray()}}finally{$s.Dispose()}}}}
foreach($spec in $specs){$found=@($hits|Where-Object depot -ceq $spec.sector_resource);Check "$($spec.id) unique current EP1 winner" ($found.Count -eq 1 -and [IO.Path]::GetFileName($found[0].archive) -ceq 'ep1_1_nightcity.archive' -and $found[0].sha256 -ceq $spec.sector_sha256)}
$blockHits=@($hits|Where-Object {$_.depot.EndsWith('all.streamingblock')})
Check 'Only official base stub and EP1 block winners' ((@($blockHits|ForEach-Object {[IO.Path]::GetFileName($_.archive)}|Sort-Object)-join ';') -ceq 'basegame_3_nightcity.archive;ep1_1_nightcity.archive')
Check 'Exact current EP1 native block winner' (@($blockHits|Where-Object {[IO.Path]::GetFileName($_.archive) -ceq 'ep1_1_nightcity.archive' -and $_.sha256 -ceq $hp.native_block_sha256}).Count -eq 1)
$resources+=@{depot=$blockDepot;sha256=(Get-FileHash $blockPath).Hash};foreach($r in $resources){Check ('No private depot collision '+$r.depot) (@($hits|Where-Object depot -ceq $r.depot).Count -eq 0)}
Pin $PSCommandPath;Pin (Join-Path $PSScriptRoot 'build_ep1_01.ps1');Pin (Join-Path $review 'ep1_passive_filter_assessment_01.json');Pin (Join-Path $review 'monument_support_assessment_01.json')
@{status='PASS_PRIVATE_EP1_FILTERED_SUPPORT_STATIC';checks_passed=$checks.Count;checks=$checks;groups=$rows;resources=$resources;streaming_blocks=@($blockDepot);sector_bindings=@($rows|ForEach-Object {@{depot=$_.depot;prefab_ref=$_.prefab_ref;node_ref_hash=$_.node_ref_hash}});archive_census_count=$archives.Count;archive_hits=$hits;negative_controls=8;pins=$pins;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 60|Set-Content -LiteralPath $out -Encoding utf8NoBOM
@{status='PASS';checks=$checks.Count;resources=5;spots=612}|ConvertTo-Json
