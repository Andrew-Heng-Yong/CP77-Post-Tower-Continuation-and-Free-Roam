# Extract only selected exact quest child spans from one pinned historical body.
# No save writer, game API, process access or complete decompressed save output.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=(Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../..')).FullName
$output=Join-Path $PSScriptRoot 'components_01'
if(Test-Path -LiteralPath $output){throw 'Fresh output required'}
$source='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-8\sav.dat'
$metadata=Join-Path (Split-Path $source -Parent) 'metadata.9.json'
$sourceHash='AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E'
$metadataHash='BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E'
foreach($path in @($source,$metadata,$PSScriptRoot)){
 $item=Get-Item -LiteralPath $path
 while($null -ne $item){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked input/output path refused'}
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory}
 }
}
if((Get-FileHash -LiteralPath $source).Hash -cne $sourceHash -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metadataHash){throw 'Historical body changed; no substitution permitted'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerHash=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
if($readerHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987'){throw 'Reader drift'}
$bytes=[IO.File]::ReadAllBytes($source)
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $sourceHash){throw 'Unstable source snapshot'}
$memory=[IO.MemoryStream]::new($bytes,$false)
$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
$save=$null
try{
 if($reader.ReadFile([ref]$save).ToString() -cne 'NoError'){throw 'Read failed'}
 $roots=@($save.Nodes|Where-Object Name -ceq 'questSystem')
 if($roots.Count -ne 1){throw 'Ambiguous questSystem root'}
 $root=$roots[0]
 $selectedNames=@('QueuedData','customArray','eventManager','nodeInstanceDataManager','questPrefabsHandler','questPhaseFreezer','questDebugLogManager','questSceneDataHelper','playerObjectListenerMapper')
 $nodes=@()
 foreach($name in $selectedNames){
  $found=@($root.Children|Where-Object Name -ceq $name)
  if($found.Count -ne 1){throw "Ambiguous selected node $name"}
  if($found[0].Children.Count -ne 0 -or $found[0].TrailingSize -ne 0 -or $found[0].Size -ne $found[0].DataSize){throw 'Selected span has unexplained children/trailing bytes'}
  $nodes+=@($found[0])
 }
 $selectedBytes=($nodes|Measure-Object -Property Size -Sum).Sum
 if($selectedBytes -le 0 -or $selectedBytes -gt 1048576){throw 'Selected component capture exceeds bound'}
 $stream=[IO.MemoryStream]::new($bytes,$false)
 $binary=[IO.BinaryReader]::new($stream)
 $settings=$null;$decompressed=$null
 $captured=[Collections.Generic.List[object]]::new()
 $eventRows=[Collections.Generic.List[object]]::new()
 $checks=[Collections.Generic.List[object]]::new()
 try{
  $decompressed=[WolvenKit.RED4.Save.Compression]::Decompress($binary,[ref]$settings)
  $view=[IO.BinaryReader]::new($decompressed,[Text.Encoding]::UTF8,$true)
  try{
   foreach($node in @($root)+$nodes){
    $decompressed.Position=$node.Offset
    if($view.ReadInt32() -ne $node.Id){throw 'Exact parsed-node offset/ID control failed'}
    $checks.Add(@{name="offset_id_$($node.Name)";pass=$true;offset=$node.Offset;id=$node.Id})
   }
   foreach($node in $nodes){
    if([long]$node.Offset+ $node.Size -gt $decompressed.Length){throw 'Selected node exceeds decompressed stream'}
    $decompressed.Position=$node.Offset
    $raw=$view.ReadBytes($node.Size)
    if($raw.Length -ne $node.Size){throw 'Short selected span'}
    $captured.Add(@{node=$node;raw=$raw})
    if($node.Name -ceq 'customArray'){
     if($node.Value -isnot [WolvenKit.RED4.Save.CustomArray]){throw 'Unexpected CustomArray parser'}
     $count=[BitConverter]::ToUInt32($raw,4)
     if(8+2*[long]$count -ne $raw.Length -or $count -ne $node.Value.Unknown.Count){throw 'CustomArray raw/managed span equation mismatch'}
     for($i=0;$i -lt $count;$i++){if([BitConverter]::ToUInt16($raw,8+2*$i) -ne $node.Value.Unknown[$i]){throw 'CustomArray managed/raw value mismatch'}}
     $checks.Add(@{name='custom_array_raw_managed_complete_equality';pass=$true;elements=$count})
    }elseif($node.Name -ceq 'eventManager'){
     if($node.Value -isnot [WolvenKit.RED4.Save.EventManager]){throw 'Unexpected EventManager parser'}
     $count=[BitConverter]::ToUInt32($raw,4)
     if(8+16*[long]$count -ne $raw.Length -or $count -ne $node.Value.Unknown.Count){throw 'EventManager raw/managed span equation mismatch'}
     for($i=0;$i -lt $count;$i++){
      $at=8+16*$i;$record=$node.Value.Unknown[$i]
      if([BitConverter]::ToUInt64($raw,$at) -ne $record.Unknown1 -or [BitConverter]::ToUInt32($raw,$at+8) -ne $record.Unknown2 -or [BitConverter]::ToUInt16($raw,$at+12) -ne $record.Unknown3 -or [BitConverter]::ToUInt16($raw,$at+14) -ne $record.Unknown4){throw 'EventManager managed/raw value mismatch'}
      $eventRows.Add(@{ordinal=$i;relative_offset=$at;u64_0=$record.Unknown1.ToString();u32_8=$record.Unknown2;u16_12=$record.Unknown3;u16_14=$record.Unknown4})
     }
     $checks.Add(@{name='event_manager_raw_managed_complete_equality';pass=$true;elements=$count})
    }
   }
  }finally{$view.Dispose()}
 }finally{if($null -ne $decompressed){$decompressed.Dispose()};$binary.Dispose()}
 if((Get-FileHash -LiteralPath $source).Hash -cne $sourceHash -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metadataHash){throw 'Source changed during extraction'}
 New-Item -ItemType Directory -Path $output|Out-Null
 $rows=@()
 foreach($record in $captured){
  $node=$record.node;$destination=Join-Path $output ($node.Name+'.bin')
  [IO.File]::WriteAllBytes($destination,$record.raw)
  $rows+=@{name=$node.Name;id=$node.Id;offset=$node.Offset;size=$node.Size;data_size=$node.DataSize;parsed_type=$node.Value.GetType().FullName;path=$destination;sha256=(Get-FileHash -LiteralPath $destination).Hash}
 }
 @{status='RAW_RECORD_LABELS_ONLY';records=$eventRows.ToArray();limits='Field widths proven by managed reader; semantic ownership requires exact native source.'}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $output 'event_records.json') -Encoding utf8NoBOM
 $debug=@($nodes|Where-Object Name -ceq 'questDebugLogManager')[0]
 if($debug.Value -isnot [WolvenKit.RED4.Save.QuestDebugLogManager]){throw 'Unexpected debug log parser'}
 @{status='MANAGED_PARSED_LINES_NOT_EXECUTION_RECEIPTS';lines=@($debug.Value.Lines)}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $output 'quest_debug_lines.json') -Encoding utf8NoBOM
 @{status='READ_ONLY_TARGETED_QUEST_CHILD_CAPTURE';source=$source;source_sha256=$sourceHash;metadata=$metadata;metadata_sha256=$metadataHash;reader_sha256=$readerHash;nodes=$rows;selected_bytes=$selectedBytes;checks=$checks.ToArray();source_unchanged=$true;save_writes=0;game_calls=0;limits='Pinned historical body, not bound to JF01/JF02. Only selected child spans retained; no full decompressed save persisted. No active/pending/applied semantics assigned without native source.'}|ConvertTo-Json -Depth 9|Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
 @{status='CAPTURED';nodes=$rows.Count;selected_bytes=$selectedBytes;checks=$checks.Count;event_records=$eventRows.Count;output=$output}|ConvertTo-Json
}finally{$reader.Dispose();$memory.Dispose()}
