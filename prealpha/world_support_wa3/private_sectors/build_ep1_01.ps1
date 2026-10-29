param([string]$HighPeakSpec='ep1_1111_filter_spec_02.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ReadWorld([string]$p){$s=[IO.File]::OpenRead($p);try{$r=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($s);$r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$f=$null;if($r.ReadFile([ref]$f,$true).ToString() -cne 'NoError'){throw 'World read failed'};return $f}finally{$s.Dispose()}}
function Json($x){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($x,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function BytesHash([byte[]]$b){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$source=Join-Path $PSScriptRoot 'source_ep1_01';if(Test-Path $source){throw 'Preserve EP1 source'}
$review=Join-Path $PSScriptRoot '../native_review'
$specPaths=@((Join-Path $review 'ep1_1103_filter_spec_01.json'),(Join-Path $review 'ep1_1107_filter_spec_02.json'),(Join-Path $review 'ep1_1108_filter_spec_02.json'),(Join-Path $review $HighPeakSpec))
$specs=@($specPaths|ForEach-Object {Get-Content -LiteralPath $_ -Raw|ConvertFrom-Json -Depth 80})
$hp=@($specs|Where-Object id -eq 1111)[0]
if((Get-FileHash $hp.native_block_raw).Hash -cne $hp.native_block_sha256){throw 'Native EP1 block changed'}
$block=ReadWorld $hp.native_block_raw;$descriptors=@($block.RootChunk.Descriptors);$block.RootChunk.Descriptors.Clear()
$rows=@();$resources=@()
foreach($spec in $specs){
 if((Get-FileHash $spec.sector_raw).Hash -cne $spec.sector_sha256){throw 'Native EP1 sector changed'}
 $file=ReadWorld $spec.sector_raw;$r=$file.RootChunk;$expected=@{1103=486;1107=124;1108=71;1111=347}[[int]$spec.id]
 if($r.Nodes.Count -ne $expected -or $r.Version.ToString() -cne '68' -or $r.PersistentNodes.Count -ne 0 -or $r.VariantNodes.Count -ne 0 -or $r.VariantIndices.Count -ne 1){throw 'EP1 native layout not bounded'}
 if($spec.drop_nodes.Count -ne $spec.drop_types.Count -or @($spec.drop_nodes|Select-Object -Unique).Count -ne $spec.drop_nodes.Count){throw 'Drop set invalid'}
 for($i=0;$i -lt $spec.drop_nodes.Count;$i++){if($r.Nodes[$spec.drop_nodes[$i]].Chunk.GetType().Name -cne $spec.drop_types[$i]){throw 'Wrong native removed type'}}
 $raw=$r.NodeData.Buffer.GetBytes();if($raw.Length%144){throw 'Incomplete placement records'}
 $originalNodes=@($r.Nodes|ForEach-Object {Json $_.Chunk});$kept=@();$removed=@();$bytes=[Collections.Generic.List[byte]]::new()
 for($offset=0;$offset -lt $raw.Length;$offset+=144){
  $bits=[BitConverter]::ToUInt64($raw,$offset+0x70);$old=[int]($bits -band [uint64]0x7FFFF)
  if($old -ge $r.Nodes.Count){throw 'Native placement out of range'}
  if($spec.drop_nodes -contains $old){$removed+=@{datum=$offset/144;node=$old};continue}
  $next=$old-@($spec.drop_nodes|Where-Object {$_ -lt $old}).Count;$record=[byte[]]$raw[$offset..($offset+143)]
  $bits=($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$next
  [Array]::Copy([BitConverter]::GetBytes($bits),0,$record,0x70,8);$bytes.AddRange($record);$kept+=@{old=$old;new=$next}
 }
 if(@(Compare-Object @($removed.datum|Sort-Object) @($spec.drop_placements|Sort-Object)).Count){throw 'Removed placement set drift'}
 foreach($i in @($spec.drop_nodes|Sort-Object -Descending)){$r.Nodes.RemoveAt($i)}
 $r.NodeData.Buffer.Data=$null;$r.NodeData.Buffer.SetBytes($bytes.ToArray())
 $privateRef='$/03_night_city/towercontinued/world_support_wa3/group'+$spec.id+'_support';$hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($privateRef)
 $depot='base\worlds\03_night_city\_compiled\default\ep1\quest_'+$hash.ToString('x16')+'.streamingsector';$path=Join-Path $source $depot
 Write-Cr2wFile $file $path;$back=ReadWorld $path
 if((BytesHash $back.RootChunk.NodeData.Buffer.GetBytes()) -cne (BytesHash $bytes.ToArray())){throw 'EP1 opaque buffer roundtrip changed'}
 foreach($k in $kept){if((Json $back.RootChunk.Nodes[$k.new].Chunk) -cne $originalNodes[$k.old]){throw 'Retained EP1 payload changed'}}
 $preview=@($back.RootChunk.Nodes|Where-Object {$_.Chunk.GetType().Name -ceq 'worldPopulationSpawnerNode'})
 if($preview.Count -ne $(if($spec.id -eq 1103){19}else{0})){throw 'Unexpected retained preview count'}
 foreach($p in $preview){if($p.Chunk.SpawnOnStart.ToString() -cne 'False' -or $p.Chunk.AlwaysSpawned.ToString() -cnotin @('false_','default__false_')){throw 'Retained automatic preview'}}
 $descriptor=@($descriptors|Where-Object {$_.Data.DepotPath.ToString() -ceq $spec.sector_resource})
 if($descriptor.Count -ne 1 -or $descriptor[0].QuestPrefabNodeRef.ToString() -cne $spec.native_prefab -or $descriptor[0].Category.ToString() -cne 'Quest'){throw 'EP1 native descriptor mismatch'}
 $d=$descriptor[0].DeepCopy();$d.QuestPrefabNodeRef=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($privateRef);$d.Data=[Activator]::CreateInstance($d.GetType().GetProperty('Data').PropertyType,[object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($depot)));$block.RootChunk.Descriptors.Add($d)
 $rows+=@{group=$spec.id;depot=$depot;prefab_ref=$privateRef;node_ref_hash=$hash.ToString();sha256=(Get-FileHash $path).Hash;native=$spec.sector_raw;native_sha256=$spec.sector_sha256;dropped_nodes=$spec.drop_nodes;dropped_placements=$removed;retained_nodes=$back.RootChunk.Nodes.Count;retained_spots=$spec.preserve_ai_spots;retained_previews=$preview.Count}
 $resources+=@{depot=$depot;sha256=(Get-FileHash $path).Hash}
}
$blockDepot='towercontinued\world_support_wa3\filtered_support_ep1.streamingblock';$bp=Join-Path $source $blockDepot;Write-Cr2wFile $block $bp
$resources+=@{depot=$blockDepot;sha256=(Get-FileHash $bp).Hash}
@{status='BUILT_EP1_PRIVATE_SUPPORT_PENDING_INDEPENDENT';rows=$rows;resources=$resources;streaming_blocks=@($blockDepot);sector_bindings=@($rows|ForEach-Object {@{depot=$_.depot;prefab_ref=$_.prefab_ref;node_ref_hash=$_.node_ref_hash}});spec_paths=$specPaths;native_block=$hp.native_block_raw;native_block_sha256=$hp.native_block_sha256;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 70|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build_ep1_proof_01.json') -Encoding utf8NoBOM
@{status='BUILT';resources=5;spots=612}|ConvertTo-Json
