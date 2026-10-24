$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$out=Join-Path $PSScriptRoot 'candidate_01/diagnosis_01/doors_02'
if(Test-Path -LiteralPath $out){throw 'Use a successor output'}
[void][IO.Directory]::CreateDirectory($out)
$names=@('PTFRMV_Enabled','PTFRMV_Applied','PTFRMV_AccessRevision','PTFRMV11_Registered','PTFRMV_QuestOwns','PTFRMV_Suspended','PTFRBASE_Suspended','PTFRWORLD_Suspended','q115_point_of_no_return','q305_johnny_scene_active')
foreach($prefix in @('Front','Inner','Rear','Street')){foreach($suffix in @('Ready','Requests')){$names+="PTFRMV11_${prefix}${suffix}"}}
$hashMethod=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{}
foreach($name in $names){$f=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$wanted[[uint32]$hashMethod.Invoke($null,[object[]]@($f))]=$name}
foreach($slot in @('AutoSave-13')){
 $source=Join-Path $ws "recovery/h10_h3_diagnosis_01/$slot/sav.dat"
 $before=(Get-FileHash -LiteralPath $source).Hash
 $stream=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
  if($reader.ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save parse failed'}
  $facts=[Collections.Generic.List[object]]::new()
  $pending=[Collections.Generic.Stack[object]]::new()
  foreach($node in $save.Nodes){$pending.Push(@{node=$node;path=$node.Name})}
  while($pending.Count){$item=$pending.Pop();$node=$item.node
   if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($entry in $node.Value.FactEntries){$h=[uint32]$hashMethod.Invoke($null,[object[]]@($entry.FactName));if($wanted.ContainsKey($h)){$facts.Add(@{name=$wanted[$h];value=[uint32]$entry.Value;table=$item.path})}}}
   foreach($child in $node.Children){$pending.Push(@{node=$child;path=$item.path+'/'+$child.Name})}
  }
  $ps=($save.Nodes|Where-Object Name -eq 'PersistencySystem2').Value
  $doors=@($ps.Entries|Where-Object {$null -ne $_.Data -and ($_.Data.GetType().Name -eq 'DoorControllerPS' -or ($_.Data -is [WolvenKit.RED4.Types.IDynamicClass] -and $_.Data.ClassName.ToString() -eq 'DoorControllerPS'))})
  foreach($door in $doors){
   $json=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($door.Data,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
   [IO.File]::WriteAllText((Join-Path $out "$slot.door_$($door.Id).json"),$json,[Text.UTF8Encoding]::new($false))
  }
  $report=@{source=$source;sha256=$before;facts=@($facts.ToArray());queried_names=$names;door_ids_found=@($doors|ForEach-Object {[string]$_.Id});note='Absent serialized facts are not asserted live zero. No matching private door ID does not prove absence: persistence IDs may differ or unchanged devices may not serialize.'}
  [IO.File]::WriteAllText((Join-Path $out "$slot.json"),($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
  Write-Output "${slot}: $($facts.Count) matched facts; $($doors.Count) matching private door IDs"
 }finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $source).Hash -ne $before){throw 'Backup changed'}
}

