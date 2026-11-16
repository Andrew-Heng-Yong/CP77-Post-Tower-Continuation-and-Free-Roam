# Supplemental read-only inventory for providers outside archive/pc.
param([int]$Attempt=7)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$plan=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/plan.json') -Raw|ConvertFrom-Json
$out=Join-Path $PSScriptRoot ('verification_{0:d2}' -f $Attempt)
if(Test-Path -LiteralPath $out){throw 'Fresh verification directory required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[void][Reflection.Assembly]::LoadFrom((Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll'))
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
function Plain([string]$Path){
 for($p=Get-Item -LiteralPath $Path -Force;$null -ne $p;){
  if($p.Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked input refused: $Path"}
  if($p -is [IO.FileInfo]){$p=$p.Directory}else{$p=$p.Parent}
 }
}
function Convert-YamlNode($node){
 if($node -is [YamlDotNet.RepresentationModel.YamlScalarNode]){return $node.Value}
 if($node -is [YamlDotNet.RepresentationModel.YamlSequenceNode]){return ,@($node.Children|ForEach-Object {Convert-YamlNode $_})}
 if($node -is [YamlDotNet.RepresentationModel.YamlMappingNode]){
  $map=[ordered]@{};foreach($item in $node.Children.GetEnumerator()){$map[$item.Key.Value]=Convert-YamlNode $item.Value};return $map
 }
 throw "Unsupported YAML node $($node.GetType().FullName)"
}
$roots=@(foreach($relative in @('red4ext/plugins','mods')){
 $path=Join-Path $plan.game_root $relative
 if(Test-Path -LiteralPath $path){Plain $path;@{path=$path;exists=$true}}else{@{path=$path;exists=$false}}
})
$ignoredLinks=[Collections.Generic.List[object]]::new()
$files=@(foreach($root in $roots|Where-Object exists){
 $all=@(Get-ChildItem -LiteralPath $root.path -Recurse -Force)
 foreach($link in $all|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}){
  if($link.PSIsContainer -or $link.Extension -ine '.log'){throw "Linked provider input/tree refused: $link"}
  $ignoredLinks.Add(@{path=$link.FullName;target=$link.Target;reason='Non-provider log symlink; not opened or followed'})
 }
 $all|Where-Object {-not $_.PSIsContainer -and $_.Extension -in @('.archive','.xl')}
})
$archives=[Collections.Generic.List[object]]::new();$configs=[Collections.Generic.List[object]]::new();$bindings=[Collections.Generic.List[object]]::new()
foreach($file in $files){
 Plain $file.FullName;$stamp=@($file.Length,$file.LastWriteTimeUtc.Ticks);$hash=(Get-FileHash -LiteralPath $file.FullName).Hash
 if($file.Extension -ieq '.archive'){
  $archive=$null;$code=([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive)
  if($code.ToString() -cne 'NoError'){throw "Unreadable plugin archive: $file"}
  foreach($gate in $plan.gates){if($archive.Files.ContainsKey([uint64]$gate.key)){throw "Unreviewed plugin provider: $file : $($gate.depot)"}}
  $archives.Add(@{path=$file.FullName;bytes=$file.Length;sha256=$hash;modified_ticks=$stamp[1];members=$archive.Files.Count;patched_depot_matches=0})
 }else{
  $yaml=[YamlDotNet.RepresentationModel.YamlStream]::new();$reader=[IO.StringReader]::new([IO.File]::ReadAllText($file.FullName))
  try{$yaml.Load($reader)}finally{$reader.Dispose()}
  $documentIndex=0
  foreach($document in $yaml.Documents){
   $data=Convert-YamlNode $document.RootNode
   if($data -isnot [Collections.IDictionary]){throw "Non-mapping XL root: $file"}
   if($data.Contains('quest')){
    $quest=$data['quest'];if($quest -isnot [Collections.IDictionary] -or -not $quest.Contains('phases')){throw "Unreviewed quest XL schema: $file"}
    $ordinal=0
    foreach($phase in $quest['phases']){
     if($phase -isnot [Collections.IDictionary] -or -not $phase.Contains('parent') -or -not $phase.Contains('path')){throw "Unreviewed phase binding: $file"}
     $parent=$phase['parent'].Replace('/','\').ToLowerInvariant()
     foreach($gate in $plan.gates){if($parent -ceq $gate.depot.ToLowerInvariant()){throw "XL injection targets patched resource: $file"}}
     $bindings.Add(@{file=$file.FullName;document=$documentIndex;ordinal=$ordinal;binding=$phase});$ordinal++
    }
   }
   $documentIndex++
  }
  $configs.Add(@{path=$file.FullName;bytes=$file.Length;sha256=$hash;modified_ticks=$stamp[1];documents=$yaml.Documents.Count})
 }
 $file.Refresh()
 if($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1] -or (Get-FileHash -LiteralPath $file.FullName).Hash -cne $hash){throw 'Provider changed during check'}
}
$second=@(foreach($root in $roots|Where-Object exists){Get-ChildItem -LiteralPath $root.path -Recurse -Force -File|Where-Object {$_.Extension -in @('.archive','.xl')}|ForEach-Object FullName})
if(@(Compare-Object @($files.FullName) $second).Count){throw 'Provider inventory changed during check'}
New-Item -ItemType Directory -Path $out|Out-Null
@{status='PASS_SUPPLEMENTAL_PROVIDER_AND_XL_CHECK';roots=$roots;archives=$archives.ToArray();xl_files=$configs.ToArray();phase_bindings=$bindings.ToArray();ignored_nonprovider_links=$ignoredLinks.ToArray();patched_depot_collisions=0;patched_phase_injections=0;new_xl_registrations=0;game_writes=0;save_writes=0;tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;plan_sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'evidence_01/plan.json')).Hash;scope='Supplements archive/pc inventory. No new ArchiveXL registrations; native node IDs remain scoped to independently checked graphs.'}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $out 'plugin_providers.json') -Encoding utf8NoBOM
Write-Output "PASS: $($archives.Count) supplemental archives, $($configs.Count) XL files, $($bindings.Count) phase bindings; no target collision."
