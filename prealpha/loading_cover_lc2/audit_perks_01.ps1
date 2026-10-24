$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
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
$numericCast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function Numeric($id){return [uint64]$script:numericCast.Invoke($null,[object[]]@($id.PSObject.BaseObject))}
if([PTFRFlatHash]::Append([WolvenKit.RED4.Types.TweakDBID]::CalculateHash('NewPerks.BodyAttributeData'),'.perks') -ne [WolvenKit.RED4.Types.TweakDBID]::CalculateHash('NewPerks.BodyAttributeData.perks')){throw 'Flat hash continuation failed'}
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

$compiled=Get-Content -LiteralPath (Join-Path $ws 'prealpha/loading_cover_lc1/candidate_04/compile_02/compiled.script') -Raw
$enum=[regex]::Match($compiled,'enum gamedataNewPerkType\s*\{([^}]+)').Groups[1].Value
$names=@([regex]::Matches($enum,'(\w+)\s*=\s*(\d+)')|Where-Object {$_.Groups[1].Value -notin @('Count','Invalid')}|ForEach-Object {'NewPerks.'+$_.Groups[1].Value})
$names+=@('Body','Cool','Espionage','Reflexes','Intelligence','TechnicalAbility'|ForEach-Object {'NewPerks.'+$_+'AttributeData'})
$queue=[Collections.Generic.Queue[uint64]]::new();$known=@{}
foreach($name in $names){$id=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name);$known[$id]=$name;$queue.Enqueue($id)}
$seen=[Collections.Generic.HashSet[uint64]]::new();$rows=[Collections.Generic.List[object]]::new()
while($queue.Count){
 $id=$queue.Dequeue();if(!$seen.Add($id)){continue};if($seen.Count -gt 2000){throw 'Unexpected closure size'}
 $type=$null;foreach($db in $databases){$type=$db.Records.GetRecord($id);if($null -ne $type){break}}
 $row=[ordered]@{id=$id;name=$known[$id];missing=($null -eq $type);fields=[ordered]@{}}
 if($null -ne $type){
  $row['type']=$type.Name
  foreach($field in @('attribute','type','perks','levels','tier','requiresPerks','enumName','requiredAttributePoints','dataPackage','pointsCost')){
   $value=Flat $id $field;if($null -eq $value){continue}
   $row.fields[$field]=Primitive $value
   if($field -in @('attribute','type','perks','levels','tier','requiresPerks')){
    foreach($child in $value){if($child -is [WolvenKit.RED4.Types.TweakDBID] -and (Numeric $child) -ne 0){$queue.Enqueue((Numeric $child))}}
   }
  }
 }
 $rows.Add($row)
}
$sources=@(foreach($name in 'tweakdb_ep1.bin','tweakdb.bin'){$path=Join-Path $game ('r6/cache/'+$name);@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash}})
$out=Join-Path $PSScriptRoot 'candidate_01/diagnosis_01/perks_current.json'
@{records=@($rows);database_sources=$sources;compiled_sha256=(Get-FileHash -LiteralPath (Join-Path $ws 'prealpha/loading_cover_lc1/candidate_04/compile_02/compiled.script')).Hash}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $out -Encoding utf8
@{records=$rows.Count;output=$out}|ConvertTo-Json
