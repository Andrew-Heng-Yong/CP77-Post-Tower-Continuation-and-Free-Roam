param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
Add-Type -TypeDefinition @'
public static class PTFRFlatHash {
 public static ulong Append(ulong id, string suffix) {
  uint crc = (uint)(id & 0xffffffffUL) ^ 0xffffffffU;
  foreach(byte b in System.Text.Encoding.UTF8.GetBytes(suffix)) {
   crc ^= b;
   for(int i=0;i<8;i++) crc = (crc >> 1) ^ ((crc & 1) != 0 ? 0xedb88320U : 0U);
  }
  return ((((id >> 32) & 255UL) + (ulong)suffix.Length) << 32) | (crc ^ 0xffffffffU);
 }
}
'@
$databases=[Collections.Generic.List[object]]::new()
foreach($name in 'tweakdb_ep1.bin','tweakdb.bin'){
 $stream=[IO.File]::OpenRead((Join-Path $game ('r6\cache\'+$name)))
 try{
  $db=$null
  if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($stream)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'TweakDB parse failure'}
  $databases.Add($db)
 }finally{$stream.Dispose()}
}
$record='Character.q307_thug_01'
$recordHash=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($record)
$numericCast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function Numeric($id){return [uint64]$script:numericCast.Invoke($null,[object[]]@($id.PSObject.BaseObject))}
if([PTFRFlatHash]::Append($recordHash,'.tags') -ne [WolvenKit.RED4.Types.TweakDBID]::CalculateHash($record+'.tags')){throw 'Flat hash continuation failed'}
function Flat([uint64]$id,[string]$name){
 $key=[PTFRFlatHash]::Append($id,'.'+$name)
 foreach($db in $script:databases){if($db.Flats.Exists($key)){return ,$db.Flats.GetValue($key)}}
 return $null
}
function Primitive($value){
 if($null -eq $value){return $null}
 if($value -is [WolvenKit.RED4.Types.TweakDBID]){return Numeric $value}
 if($value -is [System.Collections.IEnumerable] -and $value -isnot [string]){return ,@($value|ForEach-Object {Primitive $_})}
 return $value.ToString()
}
function Fields([uint64]$id,[string[]]$names){
 $row=[ordered]@{id=$id}
 foreach($name in $names){$v=Flat $id $name;if($null -ne $v){$row[$name]=Primitive $v}}
 return $row
}
$statNames=@{}
foreach($name in [Enum]::GetNames([WolvenKit.RED4.Types.Enums+gamedataStatType])){
 $statNames[[WolvenKit.RED4.Types.TweakDBID]::CalculateHash('BaseStats.'+$name)]='BaseStats.'+$name
}
$seen=[Collections.Generic.HashSet[uint64]]::new()
$queue=[Collections.Generic.Queue[uint64]]::new()
foreach($id in @((Flat $recordHash 'abilities'))+@((Flat $recordHash 'statModifiers'))){$queue.Enqueue((Numeric $id))}
$dependencies=[Collections.Generic.List[object]]::new()
while($queue.Count){
 $id=$queue.Dequeue();if(-not $seen.Add($id)){continue}
 if($seen.Count -gt 200){throw 'Dependency audit exceeded bounded scope'}
 $type=$null;foreach($db in $databases){$type=$db.Records.GetRecord($id);if($null -ne $type){break}}
 if($null -eq $type){throw "Missing dependency record: $id"}
 $row=[ordered]@{id=$id;type=$type.Name;fields=[ordered]@{}}
 foreach($property in $type.GetProperties()){
  $name=$property.Name.Substring(0,1).ToLowerInvariant()+$property.Name.Substring(1)
  $v=Flat $id $name;if($null -eq $v){continue}
  $row.fields[$name]=Primitive $v
  if($name -in @('statType','refStat') -and $statNames.ContainsKey((Numeric $v))){$row.fields[$name+'_resolved']=$statNames[(Numeric $v)]}
  # Bounded gameplay payload walk, not prerequisites or unrelated quest records.
  if($name -in @('abilityPackage','effectors','stats','statModifier','statModifiers','statusEffect','packages')){
   foreach($child in $v){if($child -is [WolvenKit.RED4.Types.TweakDBID] -and (Numeric $child) -ne 0){$queue.Enqueue((Numeric $child))}}
  }
 }
 $dependencies.Add($row)
}
$abilityRows=@(foreach($id in (Flat $recordHash 'abilities')){
 $numeric=Numeric $id
 $row=Fields $numeric @('effectors','statModifiers','prereqRecord')
 $row['effector_details']=@(foreach($effector in (Flat $numeric 'effectors')){
  $eid=Numeric $effector
  $erow=Fields $eid @('className','statModifier','statModifiers','statusEffect','prereqRecord','removeWithEffector')
  $erow['modifier_details']=@(foreach($modifier in @((Flat $eid 'statModifier'))+@((Flat $eid 'statModifiers'))){
   if($null -ne $modifier){Fields (Numeric $modifier) @('statType','modifierType','value','refStat','op')}
  })
  $erow
 })
 $row
})
$modRows=@(foreach($id in (Flat $recordHash 'statModifiers')){
 Fields (Numeric $id) @('statType','modifierType','value','refStat','op')
})
$localization=Get-Content (Join-Path $audit 'street_localization\json\ep1\localization\en-us\onscreens\onscreens.json.json') -Raw|ConvertFrom-Json -Depth 100
$entries=$localization.Data.RootChunk.root.Data.entries
$terry=@($entries|Where-Object {$_.primaryKey -eq '81616'})
if($terry.Count -ne 1 -or $terry[0].femaleVariant -ne 'Terry'){throw 'Terry identity unconfirmed'}
$row=[ordered]@{status='READ_ONLY_SOURCE_AUDIT_NOT_IMPLEMENTED_OR_INSTALLED';record=$record;record_hash=$recordHash;display_key='81616';display_name='Terry';appearance='man_average__q307__streetkid_01';tags=(Primitive (Flat $recordHash 'tags'));base_attitude=(Primitive (Flat $recordHash 'baseAttitudeGroup'));stat_modifiers=$modRows;abilities=$abilityRows;gameplay_dependencies=@($dependencies);original_record_mutations=0;required_treatment='Mod-owned clone, do not alter original ending record';live_damage_tested=$false}
[IO.File]::WriteAllText((Join-Path $audit 'terry_record_audit.json'),($row|ConvertTo-Json -Depth 16))
[pscustomobject]@{status=$row.status;name=$row.display_name;tags=$row.tags;modifiers=$modRows;abilities=$abilityRows.Count}|ConvertTo-Json -Depth 5
