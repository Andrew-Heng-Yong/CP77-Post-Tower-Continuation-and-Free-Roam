param([string]$Output='research/sidejobs_s26/cassius/native_records_01.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
. (Join-Path $root 'tools/build_phase2a.ps1') -HelpersOnly
$dbs=@();$inputs=@()
foreach($name in @('tweakdb_ep1.bin','tweakdb.bin')) {
 $path=Join-Path 'C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/r6/cache' $name
 $h=(Get-FileHash $path).Hash;$s=[IO.File]::OpenRead($path);$db=$null
 try { if(([WolvenKit.RED4.TweakDB.TweakDBReader]::new($s)).ReadFile([ref]$db).ToString() -ne 'NoError'){throw 'Read failed'} } finally {$s.Dispose()}
 $dbs+=,$db;$inputs+=@{path=$path;sha256=$h}
}
Add-Type -TypeDefinition @'
public static class CassiusHash {
 public static ulong Append(ulong id,string suffix){byte[] b=System.Text.Encoding.UTF8.GetBytes(suffix);uint c=((uint)id)^0xffffffffu;foreach(byte x in b){c^=x;for(int j=0;j<8;j++)c=(c>>1)^((c&1)!=0?0xedb88320u:0u);}return (((id>>32)+(ulong)b.Length)<<32)|(c^0xffffffffu);}
}
'@
$convert=[WolvenKit.RED4.Types.TweakDBID].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64]}
$known=@{}
foreach($n in @('Items.YakuzaTattoo','Items.AdvancedYakuzaTattoo','Items.CasiusTattoo','Items.AdvancedCasiusTattoo','Vendors.wat_nid_ripperdoc_01')) {
 $known[[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($n).ToString()]=$n
 for($i=0;$i -lt 100;$i++){$c=$n+'_inline'+$i;$known[[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($c).ToString()]=$c}
}
function CassiusHashId($v){return $convert.Invoke($null,[object[]]@($v.PSObject.BaseObject))}
function Primitive($v){
 if($null -eq $v){return $null}
 if($v -is [WolvenKit.RED4.Types.TweakDBID]){$h=(CassiusHashId $v).ToString();return @{hash=$h;name=$known[$h]}}
 if($v -is [Collections.IEnumerable] -and $v -isnot [string]){return ,@($v|ForEach-Object {Primitive $_})}
 return $v.ToString()
}
function TypeOf([uint64]$h){foreach($d in $dbs){$t=$d.Records.GetRecord($h);if($null -ne $t){return $t}};return $null}
function Flat([uint64]$h,[string]$f){$key=[CassiusHash]::Append($h,'.'+$f);foreach($d in $dbs){if($d.Flats.Exists($key)){return ,$d.Flats.GetValue($key)}};return $null}
function Record([uint64]$h){
 $type=TypeOf $h;if($null -eq $type){return @{hash=$h.ToString();missing=$true}}
 $fields=[ordered]@{}
 foreach($p in $type.GetProperties()){$f=$p.Name.Substring(0,1).ToLowerInvariant()+$p.Name.Substring(1);if($p.Name -eq 'OnEquip'){$f='OnEquip'};$v=Flat $h $f;if($null -ne $v){$fields[$f]=Primitive $v}}
 foreach($f in @('fact','factName','value','comparisonType','comparison','invert','prereq','nestedPrereqs')){$v=Flat $h $f;if($null -ne $v){$fields[$f]=Primitive $v}}
 return @{hash=$h.ToString();name=$known[$h.ToString()];type=$type.Name;fields=$fields}
}
$targets=@('Items.YakuzaTattoo','Items.AdvancedYakuzaTattoo')|ForEach-Object {[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($_)}
$wares=@();$vendors=@();$seen=@{}
foreach($d in $dbs){foreach($entry in $d.Records){if($entry.Item2.Name -ne 'gamedataVendorItem_Record'){continue};$h=CassiusHashId $entry.Item1;$k=$h.ToString();if($seen.ContainsKey($k)){continue};$seen[$k]=$true
 if($entry.Item2.Name -eq 'gamedataVendorItem_Record'){$item=Flat $h 'item';if($null -ne $item -and (CassiusHashId $item) -in $targets){$wares+=,$h}}
}}
$seen=@{}
foreach($d in $dbs){foreach($entry in $d.Records){if($entry.Item2.Name -ne 'gamedataVendor_Record'){continue};$h=CassiusHashId $entry.Item1;$k=$h.ToString();if($seen.ContainsKey($k)){continue};$seen[$k]=$true
 if($entry.Item2.Name -eq 'gamedataVendor_Record'){$stock=Flat $h 'itemStock';foreach($v in $stock){if((CassiusHashId $v) -in $wares){$vendors+=,$h;break}}}
}}
$pending=[Collections.Generic.Queue[object]]::new();foreach($h in @($targets)+@($wares)+@($vendors)){$pending.Enqueue(@{hash=$h;depth=0})}
$records=@{};$follow=@('generationPrereqs','availabilityPrereq','quantity','prereq','prereqs','prereqRecords','prereqToCheck','prereqToCheckFor','fact','statModifiers','item','items','inlinePrereq','prerequisite')
while($pending.Count -gt 0){$n=$pending.Dequeue();$k=$n.hash.ToString();if($records.ContainsKey($k)){continue};$r=Record $n.hash;$r.depth=$n.depth;$records[$k]=$r
 if($n.depth -lt 6 -and $r.ContainsKey('fields')){foreach($f in $follow){if($r.fields.Contains($f)){foreach($v in @($r.fields[$f])){if($v -is [Collections.IDictionary] -and $v.ContainsKey('hash') -and $v.hash -ne '0'){$pending.Enqueue(@{hash=[uint64]$v.hash;depth=$n.depth+1})}}}}}
}
foreach($i in $inputs){if((Get-FileHash $i.path).Hash -ne $i.sha256){throw 'Source changed'}}
$out=Join-Path $root $Output;if(Test-Path $out){throw 'Output exists'};[void](New-Item -ItemType Directory -Force (Split-Path $out))
@{status='READ_ONLY_NATIVE_RECORDS';inputs=$inputs;ware_ids=@($wares|ForEach-Object ToString);vendor_ids=@($vendors|ForEach-Object ToString);records=@($records.Values|Sort-Object depth,hash);game_writes=0;save_writes=0}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $out -Encoding utf8
Write-Output (@{records=$records.Count;wares=$wares.Count;vendors=$vendors.Count;output=$out}|ConvertTo-Json)
