param(
 [string]$Inventory='research/dogtown_dt1/interactions/inventory_01.json',
 [string]$Output='research/dogtown_dt1/interactions/archive_audit_01.json'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$out=[IO.Path]::GetFullPath((Join-Path $workspace $Output))
$evidence=[IO.Path]::GetFullPath((Join-Path $workspace 'research/dogtown_dt1/interactions'))+[IO.Path]::DirectorySeparatorChar
if(!$out.StartsWith($evidence,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $out)){throw 'Unsafe or occupied output'}
$inventoryPath=[IO.Path]::GetFullPath((Join-Path $workspace $Inventory))
if(!$inventoryPath.StartsWith($evidence,[StringComparison]::OrdinalIgnoreCase)){throw 'Inventory outside evidence root'}
function SHA($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function ResourceSHA($e){$m=[IO.MemoryStream]::new();try{$e.Extract($m);[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$inventoryHash=SHA $inventoryPath
$i=Get-Content -LiteralPath $inventoryPath -Raw|ConvertFrom-Json
if($i.status -cne 'READ_ONLY_NATIVE_INVENTORY_NOT_LIVE_PROOF'){throw 'Unexpected inventory'}
$native=@{};$sources=@{$Inventory=$inventoryHash}
foreach($row in $i.sources){
 $json=Join-Path $workspace $row.path
 if((SHA $json) -cne $row.sha256){throw 'JSON witness changed'}
 $rawRel=$row.path.Replace('/json/','/raw/') -replace '\.json$',''
 if($rawRel -notmatch '^research/.+/raw/((base|ep1)/.+)$'){throw 'Invalid native witness path'}
 $depot=$Matches[1].Replace('/','\');$raw=Join-Path $workspace $rawRel;$hash=SHA $raw
 if($native.ContainsKey($depot) -and $native[$depot] -cne $hash){throw 'Conflicting witness'}
 $native[$depot]=$hash;$sources[$rawRel]=$hash;$sources[$row.path]=$row.sha256
}
$wk='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($name in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')){[void][Reflection.Assembly]::LoadFrom((Join-Path $wk $name))}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$keys=@{}
foreach($depot in $native.Keys){$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot);if($keys.ContainsKey($key)){throw 'FNV collision'};$keys[$key]=$depot}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$modRoot=Join-Path $game 'archive/pc/mod'
$mods=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name)
$xls=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.xl'|Sort-Object Name)
$archivePins=@{};$xlPins=@{};$modResources=@{};$overrides=@()
foreach($x in $xls){$xlPins[$x.FullName]=SHA $x.FullName}
foreach($f in $mods){
 $before=SHA $f.FullName;$ar=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Cannot read mod archive'}
 $modResources[$f.Name]=@($ar.Files.Values|ForEach-Object Name|Sort-Object)
 foreach($key in $ar.Files.Keys){if($keys.ContainsKey([uint64]$key)){$overrides+=,@{archive=$f.Name;depot=$keys[[uint64]$key];resource_sha256=ResourceSHA $ar.Files[$key]}}}
 if((SHA $f.FullName) -cne $before){throw 'Mod archive changed during scan'};$archivePins[$f.FullName]=$before
}
$official=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content'),(Join-Path $game 'archive/pc/ep1') -Filter '*.archive' -File|Sort-Object FullName)
$found=@{};$officialRows=@()
foreach($f in $official){
 $before=Get-Item -LiteralPath $f.FullName;$ar=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$ar).ToString() -ne 'NoError'){throw 'Cannot read official archive'}
 foreach($key in $ar.Files.Keys){if($keys.ContainsKey([uint64]$key)){
  $depot=$keys[[uint64]$key];$actual=ResourceSHA $ar.Files[$key]
  if($actual -cne $native[$depot]){throw "Official witness mismatch: $depot"}
  $found[$depot]=$actual
  $officialRows+=,@{archive=$f.FullName;depot=$depot;sha256=$actual}
 }}
 $after=Get-Item -LiteralPath $f.FullName
 if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc -ne $after.LastWriteTimeUtc){throw 'Official archive changed during scan'}
}
if($found.Count -ne $native.Count){throw 'Incomplete official source witness coverage'}
foreach($p in $sources.GetEnumerator()){if((SHA (Join-Path $workspace $p.Key)) -cne $p.Value){throw 'Evidence source changed'}}
foreach($p in $archivePins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'Mod archive changed after scan'}}
foreach($p in $xlPins.GetEnumerator()){if((SHA $p.Key) -cne $p.Value){throw 'XL changed after scan'}}
if((@($mods.FullName|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|ForEach-Object FullName|Sort-Object)-join '|')){throw 'Installed archive set changed'}
if((@($xls.FullName|Sort-Object)-join '|') -cne (@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.xl'|ForEach-Object FullName|Sort-Object)-join '|')){throw 'Installed XL set changed'}
$report=@{status='PASS_READ_ONLY_NATIVE_BYTE_AND_INSTALLED_NAME_AUDIT';inspector_sha256=SHA $PSCommandPath;inventory_sha256=$inventoryHash;source_pins=$sources;official=$officialRows;official_comparisons=$native.Count;native_overrides=$overrides;installed_archive_pins=$archivePins;installed_xl_pins=$xlPins;installed_resources=$modResources;modlist_present=(Test-Path -LiteralPath (Join-Path $modRoot 'modlist.txt'));live_proof=$false;game_writes=0}
[IO.File]::WriteAllText($out,($report|ConvertTo-Json -Depth 25),[Text.UTF8Encoding]::new($false))
@{status=$report.status;official_comparisons=$native.Count;native_overrides=$overrides.Count;installed_archives=$mods.Count;installed_xls=$xls.Count}|ConvertTo-Json
