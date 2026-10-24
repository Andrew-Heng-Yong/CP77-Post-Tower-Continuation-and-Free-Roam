# Offline diagnostic reader. Only backed-up saves are opened, read-only.
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$outRoot=Join-Path $PSScriptRoot 'candidate_01/diagnosis_01'
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $a))}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$names=[Collections.Generic.HashSet[string]]::new()
foreach($p in Get-ChildItem -LiteralPath (Join-Path $game 'r6/scripts') -Recurse -File -Filter '*.reds'){
 foreach($m in [regex]::Matches([IO.File]::ReadAllText($p.FullName),'"((?:PTFR|PostTower|q307_)[A-Za-z0-9_]+)"')){[void]$names.Add($m.Groups[1].Value)}
}
foreach($id in @('h10','northside','japantown','glen','corpo')){
 foreach($suffix in @('Entitled','LossPermit','AccessPermit','LossApplied','AccessApplied')){[void]$names.Add("PTFRH1_${id}_${suffix}")}
}
foreach($name in @('wat_lch_gunsmith_01_default_on','q001_spawn_wilson_attention','q101_spawn_wilson_attention','mq011_active','wat_lch_gunsmith_01_disabled','q001_wilson_talked','q101_done')){[void]$names.Add($name)}
foreach($p in Get-ChildItem -LiteralPath (Join-Path $outRoot "../native_inspect_01") -Recurse -Filter "*.questphase.json"){foreach($m in [regex]::Matches([IO.File]::ReadAllText($p.FullName), '"factName":\s*"([^"\r\n]+)"')){[void]$names.Add($m.Groups[1].Value)}}
$hashMethod=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{}
foreach($name in $names){$f=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$h=[uint32]$hashMethod.Invoke($null,[object[]]@($f));$wanted[$h]=$name}
foreach($slot in @('AutoSave-11','AutoSave-12')){
 $source=Join-Path $ws "recovery/h10_h2_diagnosis_01/$slot/sav.dat"
 $dest=Join-Path $outRoot "$slot.expanded_02.json"
 if(Test-Path -LiteralPath $dest){throw 'Existing evidence; use a successor.'}
 $before=(Get-FileHash -LiteralPath $source).Hash
 $stream=[IO.File]::Open($source,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
  $result=$reader.ReadFile([ref]$save).ToString()
  if($result -ne 'NoError'){throw "Save parse failed: $result"}
  $rows=[Collections.Generic.List[object]]::new();$nodeRows=[Collections.Generic.List[object]]::new()
  $pending=[Collections.Generic.Stack[object]]::new()
  foreach($node in $save.Nodes){$pending.Push(@{node=$node;path=$node.Name})}
  while($pending.Count){
   $item=$pending.Pop();$node=$item.node
   $nodeRows.Add(@{path=$item.path;type=if($node.Value){$node.Value.GetType().FullName}else{'null'};size=$node.Size})
   if($node.Value -is [WolvenKit.RED4.Save.FactsTable]){
    foreach($entry in $node.Value.FactEntries){
     $h=[uint32]$hashMethod.Invoke($null,[object[]]@($entry.FactName))
     if($wanted.ContainsKey($h)){$rows.Add(@{name=$wanted[$h];value=[uint32]$entry.Value;table=$item.path;hash=[string]$h})}
    }
   }
   foreach($child in $node.Children){$pending.Push(@{node=$child;path=$item.path+'/'+$child.Name})}
  }
  $report=@{source=$source;sha256=$before;parse_result=$result;facts=@($rows.ToArray());nodes=@($nodeRows.ToArray());queried_names=@($names|Sort-Object);note='Missing facts are absent serialized entries, not an asserted runtime zero. All matching table rows retained.'}
  [IO.File]::WriteAllText($dest,($report|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
  Write-Output "$slot read-only parse $result; matched $($rows.Count) facts, $($nodeRows.Count) nodes"
 }finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $source).Hash -ne $before){throw 'Backup changed'}
}

