Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
function ReadWorld([string]$path){
 $stream=[IO.File]::OpenRead($path)
 try{$reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream);$reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e)return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])});$file=$null;if($reader.ReadFile([ref]$file,$true).ToString() -cne 'NoError'){throw 'Read failed'};return $file}finally{$stream.Dispose()}
}
function HashBytes([byte[]]$bytes){return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))}
function Json($object){return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($object,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
$proof=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build_comprehensive_proof_09.json') -Raw|ConvertFrom-Json -Depth 100
if($proof.status -cne 'COMPREHENSIVE_PRIVATE_SUPPORT_SERIALIZED_PENDING_INDEPENDENT_VERIFICATION' -or $proof.groups.Count -ne 315 -or $proof.resources.Count -ne 316 -or $proof.native_world_overrides -ne 0){throw 'Build proof scope invalid'}
$source=Join-Path $PSScriptRoot 'source_comprehensive_09'
$blockPath=Join-Path $source 'towercontinued/world_support_wa3/filtered_support_comprehensive.streamingblock'
if((Get-FileHash -LiteralPath $blockPath).Hash -cne $proof.block_sha256){throw 'Block bytes changed'}
$block=ReadWorld $blockPath
if($block.RootChunk.Descriptors.Count -ne 315){throw 'Private block count changed'}
$checks=0;$spotCount=0;$groupRows=@();$seen=[Collections.Generic.HashSet[string]]::new()
foreach($g in $proof.groups){
 if(!$seen.Add([string]$g.group)){throw 'Duplicate group'}
 $privatePath=Join-Path $source $g.depot
 if((Get-FileHash -LiteralPath $g.native_raw).Hash -cne $g.native_sha256 -or (Get-FileHash -LiteralPath $privatePath).Hash -cne $g.sha256){throw ('Sector hash drift '+$g.group)}
 $native=ReadWorld $g.native_raw;$private=ReadWorld $privatePath
 if($native.RootChunk.Nodes.Count -ne $g.native_nodes -or $private.RootChunk.Nodes.Count -ne $g.private_nodes -or $private.RootChunk.Nodes.Count -ne $native.RootChunk.Nodes.Count-$g.drop_nodes.Count){throw ('Node inventory drift '+$g.group)}
 if($native.RootChunk.Version.ToString() -cne $private.RootChunk.Version.ToString()){throw ('Sector version drift '+$g.group)}
 $oldNodes=@($native.RootChunk.Nodes|ForEach-Object {Json $_.Chunk});$newNodes=@($private.RootChunk.Nodes|ForEach-Object {Json $_.Chunk})
 foreach($r in $g.retained){
  if($newNodes[$r.private_node] -cne $oldNodes[$r.native_node]){throw ('Retained node changed '+$g.group+'/'+$r.native_node)}
  if($private.RootChunk.Nodes[$r.private_node].Chunk.GetType().Name -ceq 'worldAISpotNode'){$spotCount++}
  $checks++
 }
 $old=$native.RootChunk.NodeData.Buffer.GetBytes();$new=$private.RootChunk.NodeData.Buffer.GetBytes()
 if((HashBytes $old) -cne $g.native_placement_sha256 -or (HashBytes $new) -cne $g.private_placement_sha256 -or $new.Length -ne $g.retained.Count*144){throw ('Opaque placement summary changed '+$g.group)}
 $cursor=0
 foreach($r in $g.retained){
  $offset=[int]$r.native_datum*144;$record=[byte[]]$old[$offset..($offset+143)]
  if((HashBytes $record) -cne $r.native_sha256){throw ('Native placement changed '+$g.group)}
  $bits=[BitConverter]::ToUInt64($record,0x70)
  if(([int]($bits -band [uint64]0x7FFFF)) -ne $r.native_node){throw ('Native placement index changed '+$g.group)}
  $expected=($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$r.private_node
  [Array]::Copy([BitConverter]::GetBytes($expected),0,$record,0x70,8)
  if((HashBytes $record) -cne $r.private_sha256 -or (HashBytes ([byte[]]$new[$cursor..($cursor+143)])) -cne $r.private_sha256){throw ('Private opaque placement changed '+$g.group)}
  $cursor+=144;$checks++
 }
 foreach($r in $g.removed){
  $offset=[int]$r.datum*144
  if((HashBytes ([byte[]]$old[$offset..($offset+143)])) -cne $r.sha256 -or $g.drop_nodes -notcontains $r.native_node){throw ('Removed placement mismatch '+$g.group)}
  $checks++
 }
 $oldVariants=@($native.RootChunk.VariantIndices|ForEach-Object {[int]$_.ToString()})
 $newVariants=@($private.RootChunk.VariantIndices|ForEach-Object {[int]$_.ToString()})
 if(@(Compare-Object $oldVariants $g.variant_indices_before).Count -or @(Compare-Object $newVariants $g.variant_indices_after).Count){throw ('Variant index drift '+$g.group)}
 for($i=0;$i -lt $oldVariants.Count;$i++){if($newVariants[$i] -ne $oldVariants[$i]-@($g.drop_nodes|Where-Object {$_ -lt $oldVariants[$i]}).Count){throw ('Variant index relocation error '+$g.group)}}
 $desc=@($block.RootChunk.Descriptors|Where-Object {$_.QuestPrefabNodeRef.ToString() -ceq $g.prefab_ref -and $_.Data.DepotPath.ToString() -ceq $g.depot})
 if($desc.Count -ne 1 -or $desc[0].Category.ToString() -cne 'Quest' -or $desc[0].Variants.Count -ne $g.native_descriptor.variants.Count){throw ('Private descriptor drift '+$g.group)}
 $checks+=4
 $groupRows+=@{group=$g.group;native_sha256=$g.native_sha256;private_sha256=$g.sha256;removed_nodes=$g.drop_nodes.Count;retained_nodes=$g.retained.Count;retained_placements=$g.retained.Count;variant_indices_before=$oldVariants;variant_indices_after=$newVariants;status='PASS'}
 if($groupRows.Count%50 -eq 0){Write-Host ('Verified '+$groupRows.Count+'/315')}
}
if($spotCount -lt 5000){throw 'Native workspots unexpectedly missing'}
$result=@{status='PASS_COMPREHENSIVE_PRIVATE_SUPPORT';groups=$groupRows;group_count=$groupRows.Count;sector_count=$groupRows.Count;resource_count=$proof.resources.Count;retained_workspots=$spotCount;checks=$checks;source_proof_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'build_comprehensive_proof_09.json')).Hash;game_writes=0;save_writes=0}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'verification_comprehensive_01.json'),($result|ConvertTo-Json -Depth 20)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;groups=$result.group_count;checks=$result.checks;workspots=$spotCount}|ConvertTo-Json
