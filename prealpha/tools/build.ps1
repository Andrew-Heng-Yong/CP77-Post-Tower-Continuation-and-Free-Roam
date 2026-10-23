param([string]$Output='')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
if(!$Output){$Output=Join-Path $ws ('prealpha/build/'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))}
if(Test-Path -LiteralPath $Output){throw 'Fresh build directory required'}
$out=[IO.Path]::GetFullPath($Output)
if(!$out.StartsWith($ws+'\prealpha\build\',[StringComparison]::OrdinalIgnoreCase)){throw 'Build outside designated directory'}
New-Item -ItemType Directory $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $ws 'tools/gig_family_b7_1_xl.ps1')
[void](B71Parser)
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}
function Json([string]$p,$v){[IO.File]::WriteAllText($p,($v|ConvertTo-Json -Depth 50),[Text.UTF8Encoding]::new($false))}
function SaveBytes([string]$p,[byte[]]$bytes){New-Item -ItemType Directory -Force (Split-Path -Parent $p)|Out-Null;[IO.File]::WriteAllBytes($p,$bytes)}
function MergeYaml($a,$b){
 if($a -is [YamlDotNet.RepresentationModel.YamlMappingNode] -and $b -is [YamlDotNet.RepresentationModel.YamlMappingNode]){
  foreach($kv in $b.Children.GetEnumerator()){
   if($a.Children.ContainsKey($kv.Key)){MergeYaml $a.Children[$kv.Key] $kv.Value}else{$a.Add($kv.Key,$kv.Value)}
  };return
 }
 if($a -is [YamlDotNet.RepresentationModel.YamlSequenceNode] -and $b -is [YamlDotNet.RepresentationModel.YamlSequenceNode]){foreach($c in $b.Children){$a.Add($c)};return}
 throw 'Unsupported scalar/repeated YAML setting; review manually'
}
function InjectId([string]$key){
 $crc=65535
 foreach($b in [Text.Encoding]::UTF8.GetBytes($key)){$x=($crc -shr 8) -bxor $b;$x=$x -bxor ($x -shr 4);$crc=(($crc -shl 8) -bxor ($x -shl 12) -bxor ($x -shl 5) -bxor $x) -band 65535}
 return $crc
}
$sel=Get-Content (Join-Path $ws 'research/pre_alpha_clean/inventory/selection.json') -Raw|ConvertFrom-Json
$inv=Get-Content (Join-Path $ws 'research/pre_alpha_clean/inventory/archives.json') -Raw|ConvertFrom-Json
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$reader=[WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$source=Join-Path $out 'source';$package=Join-Path $out 'package';New-Item -ItemType Directory $source,$package|Out-Null
$yaml=[YamlDotNet.RepresentationModel.YamlMappingNode]::new()
$keys=@{};$members=[Collections.Generic.List[object]]::new();$inputs=[Collections.Generic.List[object]]::new()
foreach($name in $sel.keep_archives){
 $p=Join-Path $game ('archive/pc/mod/'+$name);$ar=$null;$reader.ReadArchive($p,$hs,[ref]$ar)|Out-Null
 $inputs.Add(@{path=$p;sha256=(Hash $p)})
 foreach($e in $ar.Files.Values){
  $known=@($inv.members|Where-Object {$_.archive -ceq $name -and $_.key -ceq [string]$e.Key})
  if($known.Count -ne 1){throw 'Resource inventory mismatch'}
  $depot=$known[0].depot
  if($depot -match '(^[\\/]|:|(^|[\\/])\.\.([\\/]|$))'){throw 'Unsafe depot path'}
  if($keys.ContainsKey([string]$e.Key)){throw 'Duplicate resource'};$keys[[string]$e.Key]=$depot
  $mem=[IO.MemoryStream]::new();try{$e.Extract($mem);$bytes=$mem.ToArray()}finally{$mem.Dispose()}
  $dest=Join-Path $source $depot;SaveBytes $dest $bytes
  $members.Add(@{depot=$depot;key=[string]$e.Key;sha256=(Hash $dest);origin=$name})
 }
 $xl=$p+'.xl'
 if(Test-Path -LiteralPath $xl){MergeYaml $yaml (B71Parse ([IO.File]::ReadAllText($xl)));$inputs.Add(@{path=$xl;sha256=(Hash $xl)})}
}
# Exact single-resource phone admission repair; gameplay/scenes remain original.
$overlay=Join-Path $ws 'prealpha/phone/resources'
foreach($f in Get-ChildItem -LiteralPath $overlay -File -Recurse){
 $depot=[IO.Path]::GetRelativePath($overlay,$f.FullName)
 $row=@($members|Where-Object {$_.depot -ceq $depot})
 if($row.Count -ne 1){throw "Overlay is not an existing selected resource: $depot"}
 $row[0].predecessor_sha256=$row[0].sha256
 Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $source $depot)
 $row[0].sha256=Hash $f.FullName;$row[0].overlay=$f.FullName
}
# Existing registrations are copied, not regenerated from a shared quest template.
$phaseList=(B71Child (B71Child $yaml 'quest') 'phases').Children
$phaseKeys=@{};$idKeys=@{};$nativeIds=@{}
$native=Get-Content (Join-Path $ws 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw|ConvertFrom-Json -Depth 100
foreach($n in $native.Data.RootChunk.graph.Data.nodes){$nativeIds[[string]$n.Data.id]=$true}
foreach($p in $phaseList){
 $depot=(B71Child $p 'path').Value;$parent=(B71Child $p 'parent').Value
 if($phaseKeys.ContainsKey($depot)){throw "Duplicate phase registration $depot"};$phaseKeys[$depot]=$true
 if(!(Test-Path -LiteralPath (Join-Path $source $depot))){throw "Unpacked phase $depot"}
 if($parent -cne 'ep1\quest\ep1.quest'){throw "Unreviewed parent $parent"}
 $nodes=(B71Child (B71Child $p 'input') 'node').Children
 if($nodes.Count -ne 1 -or $nodes[0].Value -cne '1'){throw 'Unreviewed input node'}
 $id=InjectId ($depot+':1')
 if($nativeIds.ContainsKey([string]$id) -or $idKeys.ContainsKey([string]$id)){throw "Injected node collision $id $depot"};$idKeys[[string]$id]=$depot
}
# Preserve unrelated mods. Detect resource and phase-ID conflicts before renaming archive.
$thirdParty=[Collections.Generic.List[object]]::new()
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File -Filter '*.archive'|Where-Object {$_.Name -notlike 'TowerContinued*'}){
 $ar=$null;$reader.ReadArchive($f.FullName,$hs,[ref]$ar)|Out-Null
 foreach($k in $ar.Files.Keys){if($keys.ContainsKey([string]$k)){throw "Third-party resource collision: $($f.Name) $($keys[[string]$k])"}}
 $thirdParty.Add(@{path=$f.FullName;sha256=(Hash $f.FullName);members=$ar.Files.Count})
}
# ArchiveXL also accepts standalone .xl files, not just <archive>.archive.xl.
foreach($f in Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File -Filter '*.xl'|Where-Object {$_.Name -notlike 'TowerContinued*'}){
  $root=B71Parse ([IO.File]::ReadAllText($f.FullName))
  $q=B71Child $root 'quest'
  if($null -ne $q){$ps=B71Child $q 'phases';if($null -ne $ps){foreach($p in $ps.Children){
   $par=(B71Child $p 'parent').Value
   if($par -ceq 'ep1\quest\ep1.quest'){
    $dp=(B71Child $p 'path').Value
    foreach($n in (B71Child (B71Child $p 'input') 'node').Children){$id=InjectId ($dp+':'+$n.Value);if($idKeys.ContainsKey([string]$id)){throw "Third-party phase ID collision $dp"}}
   }
  }}}
  $thirdParty.Add(@{path=$f.FullName;sha256=(Hash $f.FullName);kind='archive_xl'})
}
$destArchive=Join-Path $package 'archive/pc/mod/TowerContinued_PreAlpha.archive'
New-Item -ItemType Directory -Force (Split-Path -Parent $destArchive)|Out-Null
$st=[IO.File]::Create($destArchive)
try{([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$st)}finally{$st.Dispose()}
$ys=[YamlDotNet.RepresentationModel.YamlStream]::new([YamlDotNet.RepresentationModel.YamlDocument]::new($yaml))
$sw=[IO.StringWriter]::new();$ys.Save($sw,$false);[IO.File]::WriteAllText($destArchive+'.xl',$sw.ToString(),[Text.UTF8Encoding]::new($false));$sw.Dispose()
$parsed=B71Parse ([IO.File]::ReadAllText($destArchive+'.xl'))
if((B71Child (B71Child $parsed 'quest') 'phases').Children.Count -ne $phaseList.Count){throw 'YAML roundtrip mismatch'}
$ar=$null;$reader.ReadArchive($destArchive,$hs,[ref]$ar)|Out-Null
if($ar.Files.Count -ne $members.Count){throw 'Packed member count mismatch'}
foreach($r in $members){
 $e=$ar.Files[[uint64]$r.key];$mem=[IO.MemoryStream]::new();try{$e.Extract($mem);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($h -cne $r.sha256){throw "Packed byte drift $($r.depot)"}
}
# Keep existing class/module names while placing the runtime under a single mod directory.
$scripts=Join-Path $package 'r6/scripts/PTFR_PreAlpha';New-Item -ItemType Directory $scripts|Out-Null
foreach($name in @($sel.keep_script_dirs)+@($sel.replace_script_dirs)){
 $p=Join-Path $game ('r6/scripts/'+$name)
 foreach($f in Get-ChildItem -LiteralPath $p -Recurse -File -Filter '*.reds'){
  $rel=$name+'/'+[IO.Path]::GetRelativePath($p,$f.FullName);$dest=Join-Path $scripts $rel
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Copy-Item -LiteralPath $f.FullName -Destination $dest
 }
}
foreach($part in @('entry','phone','arrival')){
 $dir=Join-Path $ws ('prealpha/'+$part+'/scripts')
 if(!(Test-Path -LiteralPath $dir)){throw "Component unfinished: $part"}
 foreach($f in Get-ChildItem -LiteralPath $dir -File -Filter '*.reds'){
  $matches=@(Get-ChildItem -LiteralPath $scripts -Recurse -File -Filter $f.Name)
  if($matches.Count -gt 1){throw "Ambiguous source replacement $($f.Name)"}
  $dest=if($matches.Count){$matches[0].FullName}else{Join-Path $scripts ('PA1/'+$f.Name)}
  New-Item -ItemType Directory -Force (Split-Path -Parent $dest)|Out-Null;Copy-Item -LiteralPath $f.FullName -Destination $dest
 }
}
$tweak=Join-Path $package 'r6/tweaks/TowerContinued_PreAlpha.yaml';New-Item -ItemType Directory -Force (Split-Path -Parent $tweak)|Out-Null
Copy-Item -LiteralPath (Join-Path $game 'r6/tweaks/TowerContinued_MistyViktor_Terry_R11.yaml') -Destination $tweak
$cet=Join-Path $package 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha';New-Item -ItemType Directory -Force $cet|Out-Null
Copy-Item -LiteralPath (Join-Path $ws 'prealpha/cet/init.lua') -Destination (Join-Path $cet 'init.lua')
$packageFiles=@(Get-ChildItem -LiteralPath $package -Recurse -File|ForEach-Object {@{relative=[IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/');sha256=Hash $_.FullName;bytes=$_.Length}})
$result=[ordered]@{status='BUILT_PACKED_READBACK_PASS_COMPILE_PENDING';output=$out;package_root=$package;package_files=$packageFiles;input_archives=$sel.keep_archives.Count;members=$members;phases=$phaseList.Count;inputs=$inputs;third_party=$thirdParty;resources_unchanged_except_phone=$true}
Json (Join-Path $out 'build.json') $result
Write-Output ('BUILD='+$out)
