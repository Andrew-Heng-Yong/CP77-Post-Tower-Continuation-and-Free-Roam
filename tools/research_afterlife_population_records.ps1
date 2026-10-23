param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$out=Join-Path $WorkspaceRoot 'research\afterlife_world'
$registry=Get-Content -LiteralPath (Join-Path $out 'patron_vanilla_registry.json') -Raw | ConvertFrom-Json -Depth 100 -AsHashtable
$names=@($registry | Where-Object {$_.community_index -in @(1070,8665,7725,2821)} | ForEach-Object {$_.entries | ForEach-Object {$_.data.characterRecordId.'$value'}} | Sort-Object -Unique)
$dbs=[Collections.Generic.List[object]]::new();$dbSources=[Collections.Generic.List[object]]::new()
foreach($name in @('tweakdb_ep1.bin','tweakdb.bin')){
 $path=Join-Path $game ('r6\cache\'+$name);$before=(Get-FileHash -LiteralPath $path).Hash
 $stream=[IO.File]::OpenRead($path)
 try{$db=$null;if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($stream)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'TweakDB parse failed'};$dbs.Add($db)}finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $path).Hash -ne $before){throw 'Database changed while reading'}
 $dbSources.Add(@{path=$path;sha256=$before;unchanged=$true})
}
function Primitive($v){
 if($null -eq $v){return $null}
 if($v -is [System.Collections.IEnumerable] -and $v -isnot [string]){return ,@($v|ForEach-Object {Primitive $_})}
 return $v.ToString()
}
$records=[Collections.Generic.List[object]]::new()
foreach($name in $names){
 $type=$null;$rh=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name)
 foreach($db in $dbs){$type=$db.Records.GetRecord($rh);if($null -ne $type){break}}
 if($null -eq $type){throw "Missing record $name"}
 $fields=[ordered]@{}
 foreach($property in $type.GetProperties()){
  $field=$property.Name.Substring(0,1).ToLowerInvariant()+$property.Name.Substring(1)
  if($field -notmatch 'appearance|template|crowd|entity|spawn|body|gender|ethnic|visual|affiliation|rarity|npcType|tags'){continue}
  $key=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name+'.'+$field)
  foreach($db in $dbs){if($db.Flats.Exists($key)){$fields[$field]=Primitive ($db.Flats.GetValue($key));break}}
 }
 $records.Add(@{record=$name;fields=$fields})
}
$factNames=@('q103_done','q103_active','q005_done','q005_plan_finished','afterlife_community_activated','tiny_mike_default_on','q307_done','q307_finished','q307_active','q307_2079','q307_main_game_killed','q307_ep1_killed')
$toHash=[WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]}
$wanted=@{};foreach($name in $factNames){$f=[WolvenKit.RED4.Save.Fact]::op_Implicit($name);$wanted[[uint32]$toHash.Invoke($null,[object[]]@($f))]=$name}
$samples=[Collections.Generic.List[object]]::new()
foreach($slot in @('ManualSave-9','AutoSave-10')){
 $path=Join-Path 'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077' ($slot+'\sav.dat')
 $values=[ordered]@{};foreach($name in $factNames){$values[$name]=@()}
 $before=(Get-FileHash -LiteralPath $path).Hash;$stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try{
  $save=$null;if(([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)).ReadFile([ref]$save).ToString() -ne 'NoError'){throw 'Save parse failed'}
  function Visit($nodes){foreach($n in $nodes){
   if($n.Value -is [WolvenKit.RED4.Save.FactsTable]){foreach($e in $n.Value.FactEntries){$key=[uint32]$script:toHash.Invoke($null,[object[]]@($e.FactName));if($script:wanted.ContainsKey($key)){$script:values[$script:wanted[$key]]+=([uint32]$e.Value)}}}
   if($n.Children.Count){Visit $n.Children}
  }}
  Visit $save.Nodes
 }finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $path).Hash -ne $before){throw 'Save changed during read'}
 $samples.Add(@{slot=$slot;sha256=$before;unchanged=$true;facts=$values})
}
$report=[ordered]@{status='READ_ONLY_OFFICIAL_RECORDS_AND_SELECTED_SAVE_FACTS';database_sources=@($dbSources);records=@($records);save_samples=@($samples);limits=@('Official base/EP1 records only, not a live TweakXL-resolved database.','Save samples are not current in-memory community states.','Absent serialized facts are not inferred as runtime zero.');game_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'population_rules_records.json'),($report|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
@{records=$records.Count;saves=@($samples);output='research/afterlife_world/population_rules_records.json'}|ConvertTo-Json -Depth 8
