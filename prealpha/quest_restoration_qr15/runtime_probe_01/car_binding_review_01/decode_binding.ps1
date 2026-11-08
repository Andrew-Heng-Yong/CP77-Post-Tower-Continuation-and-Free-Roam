# Inspection only. Reads captured bytes; does not repack or modify resources.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=(Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../../..')).FullName
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'capture_01/manifest.json') -Raw|ConvertFrom-Json -Depth 100
$row=@($manifest.resources|Where-Object {$_.depot.EndsWith('.streamingsector')})
if($row.Count -ne 1){throw 'Exactly one sector provider required'}
$row=$row[0]
if((Get-FileHash -LiteralPath $row.raw).Hash -cne $row.sha256){throw 'Captured source drift'}
if((Get-FileHash -LiteralPath $row.json).Hash -cne $row.json_sha256){throw 'Captured export drift'}
$out=Join-Path $PSScriptRoot 'binding_02'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
$resource=Read-Cr2wFile $row.raw
$root=$resource.RootChunk
$buffer=$root.NodeData.Buffer.GetBytes()
if($buffer.Length -eq 0 -or $buffer.Length % 0x90 -ne 0){throw 'Unexpected current sector setup stride'}
[IO.File]::WriteAllBytes((Join-Path $out 'node_setups.bin'),$buffer)
$json=Get-Content -LiteralPath $row.json -Raw|ConvertFrom-Json -Depth 100
$refs=@{}
foreach($ref in $json.Data.RootChunk.nodeRefs){
 $name=$ref.'$value'
 if($ref.'$storage' -cne 'string'){continue}
 $hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash($name).ToString()
 if($refs.ContainsKey($hash) -and $refs[$hash] -cne $name){throw 'Full NodeRef hash collision'}
 $refs[$hash]=$name
}
$setups=@()
for($i=0;$i -lt $buffer.Length/0x90;$i++){
 $offset=$i*0x90
 # Game2.5 layout pinned by codeware/src/Red/StreamingSector.hpp. The
 # default WKit9.1 JSON NodeIndex reads the old layout and is not used.
 $index=[int]([BitConverter]::ToUInt64($buffer,$offset+0x70) -band 0x7FFFF)
 if($index -ge $root.Nodes.Count){throw "Invalid actual node index $index"}
 $globalID=[BitConverter]::ToUInt64($buffer,$offset+0x58).ToString()
 $proxyID=[BitConverter]::ToUInt64($buffer,$offset+0x60).ToString()
 $node=$root.Nodes[$index].Chunk
 $setups+=@{datum=$i;buffer_offset=$offset;actual_node_index=$index;type=$node.GetType().Name;globalNodeID=$globalID;proxyNodeID=$proxyID;full_ref=$(if($refs.ContainsKey($globalID)){$refs[$globalID]}else{$null})}
}
$car=@($setups|Where-Object {$_.type -ceq 'worldPopulationSpawnerNode' -and $_.full_ref.EndsWith('/#sts_ep1_03_gunfight_broken_car')})
if($car.Count -ne 1){throw 'Exact typed car placement binding not unique'}
$carNode=$root.Nodes[$car[0].actual_node_index].Chunk
$carDef=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($carNode,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -Depth 80
# CBool is a boxed object in PowerShell, so use its serialized scalar value.
if($carDef.isVehicle -ne 1 -or $carDef.spawnOnStart -ne 0){throw 'Unexpected native car spawner settings'}
$layout=Join-Path $ws 'research/framework_pr63_01/codeware/src/Red/StreamingSector.hpp'
@{status='EXACT_TYPED_CAR_AND_FULL_REF_BINDING';source=$row;layout_source=@{path=$layout;sha256=(Get-FileHash -LiteralPath $layout).Hash};layout_note='Current2.5 bitpacked index@0x70&0x7FFFF, globalNodeID@0x58, stride0x90; matches historical independent decoder. Not an editable resource.';setups=$setups;car_binding=$car[0];car_definition=$carDef;short_ref_hash=[WolvenKit.RED4.Types.NodeRef]::CalculateHash('#sts_ep1_03_gunfight_broken_car').ToString();prefab_ref_hashes=@($manifest.resources|Where-Object {$_.depot.EndsWith('.streamingblock')}|ForEach-Object {@{archive=$_.archive;sha256=$_.sha256}});game_writes=0;save_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8NoBOM
@{setups=$setups.Count;car=$car[0];car_type=$carDef.'$type';is_vehicle=$carDef.isVehicle;spawn_on_start=$carDef.spawnOnStart}|ConvertTo-Json -Depth 5
