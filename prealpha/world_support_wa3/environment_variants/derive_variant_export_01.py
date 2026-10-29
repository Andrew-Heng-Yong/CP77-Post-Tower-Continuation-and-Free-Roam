from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'decode_02.ps1').read_text();prefix=s[:s.index("$out=Join-Path $PSScriptRoot")]
body=r'''
$inputs=Get-Content (Join-Path $PSScriptRoot 'inputs_01.json') -Raw|ConvertFrom-Json -Depth 50
$report=Get-Content (Join-Path $PSScriptRoot 'extract_01/report_01.json') -Raw|ConvertFrom-Json -Depth 30
$out=Join-Path $PSScriptRoot 'variant_ranges_01.json'
if(Test-Path $out){throw 'Preserve proof'}
$rows=[Collections.Generic.List[object]]::new()
foreach($blockFile in Get-ChildItem (Join-Path $PSScriptRoot 'extract_01') -Filter '*.streamingblock.json'){
 $block=Get-Content $blockFile.FullName -Raw|ConvertFrom-Json -Depth 100
 $archive=if($blockFile.Name.StartsWith('basegame')){'basegame_3_nightcity.archive'}else{'ep1_1_nightcity.archive'}
 foreach($group in $inputs.groups){
  $param=$group.operations[0].payload.type.params[0]
  $ref=$param.prefabNodeRef.'$value'
  foreach($desc in $block.Data.RootChunk.descriptors){
   $variants=@($desc.variants|Where-Object {$_.nodeRef.'$value' -ceq $ref -and $_.name.'$value' -cin @($param.variantStates.name.'$value')})
   if(!$variants.Count){continue}
   $depot=$desc.data.DepotPath.'$value'
   $hit=@($report.hits|Where-Object {$_.depot -ceq $depot -and (Split-Path $_.archive -Leaf) -ceq $archive})
   if($hit.Count -ne 1){throw "Missing exact variant sector $depot"}
   $stream=[IO.File]::OpenRead($hit[0].raw)
   $reader=[WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
   $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{param($e) return ($e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs])})
   $f=$null
   if($reader.ReadFile([ref]$f,$true).ToString() -ne 'NoError'){throw 'Read failure'}
   $stream.Dispose()
   $setups=$f.RootChunk.NodeData.Buffer.GetBytes()
   if($setups.Length -ne $f.RootChunk.NodeData.Data.Count*0x90){throw 'Placement stride'}
   foreach($v in $variants){
    $range=[int]$v.rangeIndex
    if($range -le 0 -or $range -ge $f.RootChunk.VariantIndices.Count){throw 'Variant range'}
    $start=[int]$f.RootChunk.VariantIndices[$range].ToString()
    $end=if($range+1 -lt $f.RootChunk.VariantIndices.Count){[int]$f.RootChunk.VariantIndices[$range+1].ToString()}else{$f.RootChunk.NodeData.Data.Count}
    $nodes=@($f.RootChunk.Nodes|ForEach-Object {$_.Chunk})
    $placements=@()
    for($i=$start;$i -lt $end;$i++){
     $d=$f.RootChunk.NodeData.Data[$i]
     $index=[int]([BitConverter]::ToUInt64($setups,$i*0x90+0x70) -band 0x7FFFF)
     if($index -ge $nodes.Count){throw "Variant localindex $index exceeds $($nodes.Count)"}
     $placements+=@{datum=$i;index=$index;id=$d.Id.ToString();position=@([double]$d.Position.X.ToString(),[double]$d.Position.Y.ToString(),[double]$d.Position.Z.ToString());node_ref=$d.QuestPrefabRefHash.ToString();type=$nodes[$index].GetType().Name}
    }
    $defs=@($placements.index|Select-Object -Unique|ForEach-Object {@{index=$_;definition=([WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($nodes[$_],[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())|ConvertFrom-Json -AsHashtable -Depth 100)}})
    $rows.Add(@{group=$group.id;archive=$archive;depot=$depot;raw=$hit[0].raw;raw_sha256=$hit[0].sha256;descriptor=$desc;variant=$v;start=$start;end=$end;nodes=$defs;placements=$placements})
   }
  }
 }
}
@{status='READ_ONLY_NATIVE_VARIANT_RANGE_READBACK';rows=$rows.ToArray();game_writes=0;save_writes=0}|ConvertTo-Json -Depth 100|Set-Content $out -Encoding utf8NoBOM
@{ranges=$rows.Count;groups=@($rows.group|Select-Object -Unique);status='VARIANT_RANGES_EXPORTED'}|ConvertTo-Json
'''
(H/'export_variant_ranges_01.ps1').write_text(prefix+body,encoding='utf-8',newline='\n')
