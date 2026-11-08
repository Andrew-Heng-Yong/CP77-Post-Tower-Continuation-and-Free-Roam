# One targeted historical save read; exports identity metadata, never a playable save.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace=(Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../../..')).FullName
$output=Join-Path $PSScriptRoot 'capture_03'
if(Test-Path -LiteralPath $output){throw 'Fresh output required'}
$prior=Join-Path $workspace 'prealpha/quest_restoration_qr15/lifecycle_01/save_community'
$sourceEvidence=Get-Content -LiteralPath (Join-Path $prior 'capture_01/capture.json') -Raw|ConvertFrom-Json
foreach($path in @($sourceEvidence.source,$sourceEvidence.metadata,$PSScriptRoot)){
 $item=Get-Item -LiteralPath $path
 while($null -ne $item){
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked path refused'}
  $item=if($item -is [IO.DirectoryInfo]){$item.Parent}else{$item.Directory}
 }
}
if((Get-FileHash -LiteralPath $sourceEvidence.source).Hash -cne $sourceEvidence.source_sha256 -or (Get-FileHash -LiteralPath $sourceEvidence.metadata).Hash -cne $sourceEvidence.metadata_sha256){throw 'Historical body changed'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$bytes=[IO.File]::ReadAllBytes($sourceEvidence.source)
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $sourceEvidence.source_sha256){throw 'Unstable source'}
$memory=[IO.MemoryStream]::new($bytes,$false)
$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
$save=$null
try{
 if($reader.ReadFile([ref]$save).ToString() -cne 'NoError'){throw 'Save reader failed'}
 $psName=[WolvenKit.RED4.Save.PersistencySystem2Parser]::NodeName
 $psNodes=@($save.Nodes|Where-Object Name -ceq $psName)
 if($psNodes.Count -ne 1 -or $psNodes[0].Value -isnot [WolvenKit.RED4.Save.PersistencySystem2]){throw 'PS2 root unavailable'}
 $ps=$psNodes[0].Value
 $target=[uint64]10229047
 $candidateKeys=@('10229047','6695448052237678836','15311582179580628726','17113219195054135786')
 $idList=@($ps.Ids|ForEach-Object {$_.ToString()})
 $seen=[Collections.Generic.HashSet[uint64]]::new()
 $classes=@{}
 $vehicleRows=[Collections.Generic.List[object]]::new()
 $candidateMatches=[Collections.Generic.List[object]]::new()
 $duplicate=0;$low=0
 $propertiesField=[WolvenKit.RED4.Types.RedBaseClass].GetField('_properties',[Reflection.BindingFlags]'Instance,NonPublic')
 foreach($entry in $ps.Entries){
  if(-not $seen.Add($entry.Id)){$duplicate++}
  if($entry.Id -le 0xFFFFFF){$low++}
  $class=if($null -eq $entry.Data){'NULL'}else{$entry.Data.GetType().Name}
  if(-not $classes.ContainsKey($class)){$classes[$class]=0};$classes[$class]++
  $row=@{id_u64=$entry.Id.ToString();parsed_class=$class}
  if($class -match 'VehicleComponentPS$|vehicleControllerPS$|vehiclePersistentDataPS$'){
   if($vehicleRows.Count -ge 8192){throw 'Vehicle metadata bound exceeded'}
   $dictionary=$propertiesField.GetValue($entry.Data)
   $selected=@()
   foreach($key in $dictionary.Keys){
    if($key -match 'State|Visual|Door|Destroy|Initial|Entity'){
     $value=$dictionary[$key]
     if($value -is [WolvenKit.RED4.Types.CBool]){$selected+=@{property=$key;parsed_text=$value.ToString()}}
    }
   }
   $row['selected_parsed_bools']=$selected
   if($class -ceq 'vehiclePersistentDataPS'){
    $row['property_names_before_native_export']=@($dictionary.Keys)
    $row['native_parsed_data_json']=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($entry.Data,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
   }
   $vehicleRows.Add($row)
  }
  if($row.id_u64 -in $candidateKeys){$candidateMatches.Add($row)}
 }
 $dynamicName=[WolvenKit.RED4.Save.DynamicEntityIDSystemParser]::NodeName
 $dynamicNodes=@($save.Nodes|Where-Object Name -ceq $dynamicName)
 $dynamic=@{status='UNAVAILABLE'}
 if($dynamicNodes.Count -eq 1 -and $dynamicNodes[0].Value -is [WolvenKit.RED4.Save.DynamicEntityIDSystem]){
  $d=$dynamicNodes[0].Value
  $dynamic=@{status='PARSED_UNINTERPRETED_MAPS';next_non_savable_entity_id=$d.NextNonSavableEntityID;next_savable_entity_id=$d.NextSavableEntityID;next_list_id=$d.Unk_NextListId;unknown3_type=$d.Unknown3.GetType().FullName;unknown4_type=$d.Unknown4.GetType().FullName;unknown3=$d.Unknown3;unknown4=$d.Unknown4}
 }
 if((Get-FileHash -LiteralPath $sourceEvidence.source).Hash -cne $sourceEvidence.source_sha256 -or (Get-FileHash -LiteralPath $sourceEvidence.metadata).Hash -cne $sourceEvidence.metadata_sha256){throw 'Input changed during capture'}
 New-Item -ItemType Directory -Path $output|Out-Null
 @{ids_u64=$idList;limits='Native meaning still requires serializer binding; neither inclusion nor absence is a completion receipt.'}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $output 'ps2_ids.json') -Encoding utf8NoBOM
 @{entries=@($vehicleRows.ToArray());limits='Parsed bools may include reader defaults; not certified serialized presence or quest-event completion.'}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath (Join-Path $output 'vehicle_ps_metadata.json') -Encoding utf8NoBOM
 $dynamic|ConvertTo-Json -Depth 9|Set-Content -LiteralPath (Join-Path $output 'dynamic_ids.json') -Encoding utf8NoBOM
 @{status='READ_ONLY_IDENTITY_METADATA';source=$sourceEvidence.source;source_sha256=$sourceEvidence.source_sha256;metadata_sha256=$sourceEvidence.metadata_sha256;reader_sha256=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.PersistencySystem2].Assembly.Location)).Hash;target_associated_id_u64=$target.ToString();ps2_entry_count=$ps.Entries.Count;ps2_header_ids_count=$idList.Count;ps2_header_ids_contain_raw_target=$idList.Contains($target.ToString());ps2_entry_duplicate_keys=$duplicate;ps2_entry_low24_keys=$low;ps2_unknown1=$ps.Unk1;class_counts=$classes;vehicle_metadata_rows=$vehicleRows.Count;candidate_matches=@($candidateMatches.ToArray());source_unchanged=$true;save_writes=0;game_calls=0;limits='Raw and two component-hash candidates checked separately. No namespace/savability/stage interpretation follows without native binding. No complete save persisted.'}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
 @{status='IDENTITY_METADATA_CAPTURED';ps2_entries=$ps.Entries.Count;header_ids=$idList.Count;header_has_target=$idList.Contains($target.ToString());duplicate_entry_ids=$duplicate;low24_entry_ids=$low;vehicle_rows=$vehicleRows.Count;candidate_matches=@($candidateMatches.ToArray());dynamic_status=$dynamic.status}|ConvertTo-Json -Depth 5
}finally{$reader.Dispose()}
