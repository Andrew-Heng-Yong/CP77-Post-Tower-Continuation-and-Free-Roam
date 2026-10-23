param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$databases=[Collections.Generic.List[object]]::new()
foreach($name in 'tweakdb_ep1.bin','tweakdb.bin'){
 $stream=[IO.File]::OpenRead((Join-Path $game ('r6\cache\'+$name)))
 try{$db=$null;if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($stream)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'TweakDB parse failure'};$databases.Add($db)}finally{$stream.Dispose()}
}
$numericCast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function Numeric($id){return [uint64]$script:numericCast.Invoke($null,[object[]]@($id.PSObject.BaseObject))}
function Primitive($value){
 if($null -eq $value){return $null};if($value -is [WolvenKit.RED4.Types.TweakDBID]){return [ordered]@{hash=(Numeric $value);name=$value.ToString()}}
 if($value -is [System.Collections.IEnumerable] -and $value -isnot [string]){return ,@($value|ForEach-Object {Primitive $_})};return $value.ToString()
}
$record='Character.ServiceTubeDancerFemale';$recordHash=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($record);$type=$null
foreach($db in $databases){$type=$db.Records.GetRecord($recordHash);if($null -ne $type){break}}
if($null -eq $type){throw 'Missing tube dancer record'};$fields=[ordered]@{}
foreach($property in $type.GetProperties()){
 $name=$property.Name.Substring(0,1).ToLowerInvariant()+$property.Name.Substring(1);$key=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($record+'.'+$name)
 foreach($db in $databases){if($db.Flats.Exists($key)){$fields[$name]=Primitive ($db.Flats.GetValue($key));break}}
}
$nodeCast=[WolvenKit.RED4.Types.NodeRef].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
$refs=@(1..10|ForEach-Object {'$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#afterlife_ws_dancer_'+$_.ToString('00')})
$refs+='$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#q005_com_afterlife_tube_dancers'
$refHashes=foreach($ref in $refs){$r=[WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref);[ordered]@{ref=$ref;hash=([uint64]$nodeCast.Invoke($null,[object[]]@($r.PSObject.BaseObject))).ToString()}}
$row=[ordered]@{record=$record;fields=$fields;refs=@($refHashes)}
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot 'research/afterlife_world/hologram_record_and_refs.json'),($row|ConvertTo-Json -Depth 30))
$row|ConvertTo-Json -Depth 8
