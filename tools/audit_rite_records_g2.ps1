param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$audit=Join-Path $WorkspaceRoot 'research\gig_restoration\rite_g2'
New-Item -ItemType Directory -Force $audit|Out-Null
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
Add-Type -TypeDefinition @'
public static class PTFRG2FlatHash {
 public static ulong Append(ulong id, string suffix) {
  uint crc = (uint)(id & 0xffffffffUL) ^ 0xffffffffU;
  foreach(byte b in System.Text.Encoding.UTF8.GetBytes(suffix)) {
   crc ^= b;
   for(int i=0;i<8;i++) crc = (crc >> 1) ^ ((crc & 1) != 0 ? 0xedb88320U : 0U);
  }
  return ((((id >> 32) & 255UL) + (ulong)System.Text.Encoding.UTF8.GetByteCount(suffix)) << 32) | (crc ^ 0xffffffffU);
 }
}
'@
$dbs=[Collections.Generic.List[object]]::new();$pins=[ordered]@{}
foreach($name in 'tweakdb_ep1.bin','tweakdb.bin'){
 $path=Join-Path $game ('r6\cache\'+$name);$pins[$path]=(Get-FileHash $path).Hash
 $stream=[IO.File]::OpenRead($path)
 try{$db=$null;if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($stream)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'TweakDB parse failure'};$dbs.Add($db)}finally{$stream.Dispose()}
}
$cast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function Primitive($v){
 if($null -eq $v){return $null}
 if($v -is [WolvenKit.RED4.Types.TweakDBID]){return [ordered]@{hash=[uint64]$script:cast.Invoke($null,[object[]]@($v.PSObject.BaseObject));resolved=$v.ToString()}}
 if($v -is [Collections.IEnumerable] -and $v -isnot [string]){return ,@($v|ForEach-Object {Primitive $_})}
 return $v.ToString()
}
$rows=@(foreach($id in @([uint64]100486752765,[uint64]133091080138,[uint64]131195701084,[uint64]163539604770)){
 $type=$null;foreach($db in $dbs){$type=$db.Records.GetRecord($id);if($null -ne $type){break}}
 if($null -eq $type){throw "Missing exact native item/reward $id"}
 $fields=[ordered]@{}
 foreach($prop in $type.GetProperties()){
  $field=$prop.Name.Substring(0,1).ToLowerInvariant()+$prop.Name.Substring(1);$key=[PTFRG2FlatHash]::Append($id,'.'+$field)
  foreach($db in $dbs){if($db.Flats.Exists($key)){$fields[$field]=Primitive ($db.Flats.GetValue($key));break}}
 }
 [ordered]@{hash=$id;type=$type.Name;fields=$fields}
})
foreach($p in $pins.Keys){if((Get-FileHash $p).Hash -ne $pins[$p]){throw 'Stock DB changed'}}
$result=[ordered]@{status='READ_ONLY_RITE_G2_NATIVE_RECORD_AUDIT';database_sha256=$pins;records=$rows;game_writes=0;save_writes=0}
$out=Join-Path $audit 'records.json';$data=$result|ConvertTo-Json -Depth 30
if(Test-Path $out){if((Get-Content $out -Raw).TrimEnd() -ne $data.TrimEnd()){throw 'Changed evidence: use new revision'}}else{[IO.File]::WriteAllText($out,$data,[Text.UTF8Encoding]::new($false))}
$rows|ForEach-Object {[ordered]@{hash=$_.hash;type=$_.type;displayName=$_.fields['displayName'];tags=$_.fields['tags'];journalEntry=$_.fields['journalEntry'];itemType=$_.fields['itemType']} }|ConvertTo-Json -Depth 5
