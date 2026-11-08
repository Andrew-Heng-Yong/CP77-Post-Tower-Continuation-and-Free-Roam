param([string]$Output='shared/tdb_records_01',[int]$MaximumRecords=1200,[int]$ReferenceDepth=1)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$O=Join-Path $PSScriptRoot $Output
if(Test-Path -LiteralPath $O){throw 'Fresh shared output required'}
$inputPath=Join-Path $PSScriptRoot 'shared/tdb_vehicle_target_02/targets.json'
$inputPin=(Get-FileHash -LiteralPath $inputPath).Hash
$targets=Get-Content -LiteralPath $inputPath -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
Add-Type -TypeDefinition @'
public static class QR5FlatHash {
 public static ulong Append(ulong id,string suffix) {
  uint crc=(uint)(id & 0xffffffffUL)^0xffffffffU;
  foreach(byte b in System.Text.Encoding.UTF8.GetBytes(suffix)) {
   crc^=b;for(int i=0;i<8;i++)crc=(crc>>1)^((crc&1)!=0?0xedb88320U:0U);
  }
  return ((((id>>32)&255UL)+(ulong)System.Text.Encoding.UTF8.GetByteCount(suffix))<<32)|(crc^0xffffffffU);
 }
}
'@
$tests=@()
foreach($name in @('Items.money','QuestRewards.sts_std_arr_10_completion','Mappins.DefaultQuestMappin')){
 $id=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name)
 foreach($suffix in @('.type','.amount','.displayName')){
  if([QR5FlatHash]::Append($id,$suffix) -ne [WolvenKit.RED4.Types.TweakDBID]::CalculateHash($name+$suffix)){throw 'Flat hash oracle mismatch'}
  $tests+=,@{test='Append suffix matches independent named CalculateHash';record=$name;suffix=$suffix;pass=$true}
 }
}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$dbs=[Collections.Generic.List[object]]::new();$pins=@()
foreach($name in @('tweakdb.bin','tweakdb_ep1.bin')){
 $path=Join-Path $game ('r6/cache/'+$name);$pin=(Get-FileHash -LiteralPath $path).Hash
 $s=[IO.File]::OpenRead($path)
 try{$db=$null;if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($s)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'Stock TweakDB parse failed'}}finally{$s.Dispose()}
 $dbs.Add(@{path=$path;db=$db;sha256=$pin});$pins+=,@{path=$path;sha256=$pin}
}
$cast=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
function Primitive($v){
 if($null -eq $v){return $null}
 if($v -is [WolvenKit.RED4.Types.TweakDBID]){return @{kind='TweakDBID';hash=([uint64]$script:cast.Invoke($null,[object[]]@($v.PSObject.BaseObject))).ToString();resolved=$v.ToString()}}
 if($v -is [Collections.IEnumerable] -and $v -isnot [string]){return ,@($v|ForEach-Object {Primitive $_})}
 return @{kind=$v.GetType().Name;value=$v.ToString()}
}
function IdValue([string]$text){
 $id=[uint64]0
 if([uint64]::TryParse($text,[ref]$id)){return $id}
 return [uint64][WolvenKit.RED4.Types.TweakDBID]::CalculateHash($text)
}
$queue=[Collections.Generic.Queue[object]]::new();$names=@{}
foreach($name in $targets.targets){$id=IdValue $name;$names[$id.ToString()]=$name;$queue.Enqueue(@{id=$id;depth=0;origin=$name})}
$seen=@{};$rows=@();$bounded=@()
while($queue.Count -gt 0 -and $seen.Count -lt $MaximumRecords){
 $item=$queue.Dequeue();$key=$item.id.ToString();if($seen.ContainsKey($key) -or $item.id -eq 0){continue};$seen[$key]=$true
 $sources=@();$refs=[Collections.Generic.HashSet[string]]::new()
 foreach($entry in $dbs){
  $type=$entry.db.Records.GetRecord([uint64]$item.id);if($null -eq $type){continue};$fields=[ordered]@{}
  foreach($prop in $type.GetProperties()){
   $field=$prop.Name.Substring(0,1).ToLowerInvariant()+$prop.Name.Substring(1);$flat=[QR5FlatHash]::Append([uint64]$item.id,'.'+$field)
   # Capture each database separately; no runtime winner or merge inference.
   if($entry.db.Flats.Exists($flat)){
    $v=$entry.db.Flats.GetValue($flat);$pv=Primitive $v;$fields[$field]=@{flat_hash=$flat.ToString();value=$pv}
    if($v -is [WolvenKit.RED4.Types.TweakDBID]){[void]$refs.Add(([uint64]$cast.Invoke($null,[object[]]@($v.PSObject.BaseObject))).ToString())}
    elseif($v -is [Collections.IEnumerable] -and $v -isnot [string]){foreach($child in $v){if($child -is [WolvenKit.RED4.Types.TweakDBID]){[void]$refs.Add(([uint64]$cast.Invoke($null,[object[]]@($child.PSObject.BaseObject))).ToString())}}}
   }
  }
  $sources+=,@{database=$entry.path;record_type=$type.Name;fields=$fields}
 }
 $rows+=,@{id=$key;requested_name=$(if($names.ContainsKey($key)){$names[$key]}else{''});depth=$item.depth;origin=$item.origin;exists=($sources.Count -gt 0);database_definitions=$sources;record_references=@($refs)}
 if($item.depth -lt $ReferenceDepth){foreach($child in $refs){if($child -ne '0'){$queue.Enqueue(@{id=[uint64]$child;depth=($item.depth+1);origin=$item.origin})}}}
}
while($queue.Count -gt 0){$x=$queue.Dequeue();if(-not $seen.ContainsKey($x.id.ToString())){$bounded+=,@{id=$x.id.ToString();depth=$x.depth;origin=$x.origin;reason='MaximumRecords bound'}}}
foreach($entry in $pins){if((Get-FileHash -LiteralPath $entry.path).Hash -cne $entry.sha256){throw 'Stock DB changed during read'}}
if((Get-FileHash -LiteralPath $inputPath).Hash -cne $inputPin){throw 'Target input changed'}
[IO.Directory]::CreateDirectory($O)|Out-Null
@{status='READ_ONLY_SOURCE_PINNED_STOCK_RECORD_DEFINITIONS';target_input=@{path=$inputPath;sha256=$inputPin};reader_code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;databases=$pins;records=$rows;hash_tests=$tests;maximum_records=$MaximumRecords;reference_depth=$ReferenceDepth;bounded_out=$bounded;game_writes=0;save_writes=0;limits=@('Stock base/EP1 definitions captured separately, not a claim of live merged TweakDB winners or CET/TweakXL overrides.','Only public record property flats are captured. Unsupported/unresolved values remain represented with type/string; references deeper than the bound remain open.','Occurrence in a graph is not execution, eligibility, reward amount equivalence or saved-owner proof.')}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $O 'records.json') -Encoding utf8NoBOM
@{status='PASS_READ_ONLY_STOCK_DEFINITION_CAPTURE';records=$rows.Count;found=@($rows|Where-Object {$_.exists}).Count;missing=@($rows|Where-Object {-not $_.exists}).Count;bound=$bounded.Count;hash_controls=$tests.Count}|ConvertTo-Json -Compress
