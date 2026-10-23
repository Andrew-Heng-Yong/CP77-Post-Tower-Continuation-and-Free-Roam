param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\misty_viktor_world'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
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
function Primitive($value){
 if($null -eq $value){return $null}
 if($value -is [WolvenKit.RED4.Types.TweakDBID]){return [ordered]@{hash=(Numeric $value);name=$value.ToString()}}
 if($value -is [System.Collections.IEnumerable] -and $value -isnot [string]){return ,@($value|ForEach-Object {Primitive $_})}
 return $value.ToString()
}
$record='Vehicle.v_utility4_militech_behemoth_police'
$recordHash=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($record)
$type=$null
foreach($db in $databases){$type=$db.Records.GetRecord($recordHash);if($null -ne $type){break}}
if($null -eq $type){throw 'Missing truck record'}
$fields=[ordered]@{}
foreach($property in $type.GetProperties()){
 $name=$property.Name.Substring(0,1).ToLowerInvariant()+$property.Name.Substring(1)
 $key=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($record+'.'+$name)
 foreach($db in $databases){if($db.Flats.Exists($key)){$fields[$name]=Primitive ($db.Flats.GetValue($key));break}}
}
$row=[ordered]@{status='READ_ONLY_SOURCE_AUDIT';record=$record;record_hash=$recordHash;type=$type.Name;fields=$fields}
[IO.File]::WriteAllText((Join-Path $audit 'r7_trucks_record.json'),($row|ConvertTo-Json -Depth 30))
$row|ConvertTo-Json -Depth 8
