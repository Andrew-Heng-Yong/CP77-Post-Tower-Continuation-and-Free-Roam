param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$path=Join-Path $game 'r6\cache\tweakdb.bin';$pin=(Get-FileHash $path).Hash
$s=[IO.File]::OpenRead($path)
try{$db=$null;if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($s)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'DB parse failure'}}finally{$s.Dispose()}
$rows=@()
foreach($name in @('Mappins.DefaultStaticMappin','Mappins.StaticPointOfInterestMappinDefinition','Mappins.DefaultQuestMappin')){
 $hash=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name)
 $record=$db.Records.GetRecord($hash)
 $fields=[ordered]@{}
 if($null -ne $record){
  foreach($prop in $record.GetProperties()){
   $field=$prop.Name.Substring(0,1).ToLowerInvariant()+$prop.Name.Substring(1)
   $key=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name+'.'+$field)
   if($db.Flats.Exists($key)){$fields[$field]=$db.Flats.GetValue($key).ToString()}
  }
 }
 $rows+=,[ordered]@{name=$name;hash=$hash;exists=($null -ne $record);type=$(if($record){$record.Name}else{''});fields=$fields}
}
if((Get-FileHash $path).Hash -ne $pin){throw 'DB changed'}
$out=Join-Path $WorkspaceRoot 'research\gig_restoration\fresh_b6\marker_records.json'
if(Test-Path $out){throw 'Preserve evidence'}
$result=[ordered]@{source=$path;sha256=$pin;records=$rows;game_writes=0}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
$rows|ConvertTo-Json -Depth 12
