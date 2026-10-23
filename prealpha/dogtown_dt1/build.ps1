param([string]$Revision='dt1_01',[string[]]$Components=@('gate/build/gate_06/component.json'))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
. (Join-Path $workspace 'tools/shark_b7_2_helpers.ps1')
if($Revision -cnotmatch '^dt1_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $PSScriptRoot ('build/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable build exists'}
New-Item -ItemType Directory -Path $out,(Join-Path $out 'source') | Out-Null
function HashDT1([string]$p){return (Get-FileHash -LiteralPath $p).Hash}
function WithinDT1([string]$p,[string]$root){
 $full=[IO.Path]::GetFullPath($p);$base=[IO.Path]::GetFullPath($root).TrimEnd('\')+'\'
 if(!$full.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){throw 'Path outside expected root'}
 return $full
}
$pins=[ordered]@{};$resources=[ordered]@{};$boots=@();$componentRecords=@();$native=[ordered]@{}
foreach($p in @('prealpha/dogtown_dt1/build.ps1','prealpha/dogtown_dt1/test.py','prealpha/dogtown_dt1/resource_check.ps1','tools/build_phase2a.ps1','tools/shark_b7_2_helpers.ps1','tools/gig_family_b7_1_xl.ps1','tools/afterlife_faces_r5_deployment.ps1','research/q307_extracted/raw/ep1/quest/ep1.quest','research/q307_extracted/json/ep1/quest/ep1.quest.json')){$pins[$p]=HashDT1 (Join-Path $workspace $p)}
$native['ep1\quest\ep1.quest']=$pins['research/q307_extracted/raw/ep1/quest/ep1.quest']
foreach($relative in $Components){
 $cp=WithinDT1 (Join-Path $PSScriptRoot $relative) $PSScriptRoot
 $c=Get-Content -LiteralPath $cp -Raw | ConvertFrom-Json
 $cr=Split-Path -Parent $cp
 if(@($c.boots).Count -lt 1 -or @($c.resources.PSObject.Properties).Count -lt 1){throw 'Empty component'}
 $pins[[IO.Path]::GetRelativePath($workspace,$cp).Replace('\','/')]=HashDT1 $cp
 foreach($p in $c.source_pins.PSObject.Properties){
  $source=WithinDT1 (Join-Path $workspace $p.Name) $workspace
  if((HashDT1 $source) -cne $p.Value){throw "Component source drift: $($p.Name)"}
  if($pins.Contains($p.Name) -and $pins[$p.Name] -cne $p.Value){throw 'Conflicting source pin'}
  $pins[$p.Name]=$p.Value
  if($p.Name -match '/raw/(.+)$'){
   $depot=$Matches[1].Replace('/','\')
   if($native.Contains($depot) -and $native[$depot] -cne $p.Value){throw 'Conflicting native source'}
   $native[$depot]=$p.Value
  }
 }
 foreach($r in $c.resources.PSObject.Properties){
  if($r.Name -cnotmatch '^towercontinued[\\/]dogtown_dt1[\\/]' -or $resources.Contains($r.Name)){throw 'Unexpected or duplicate resource'}
  $src=WithinDT1 (Join-Path (Join-Path $cr 'source') $r.Name) (Join-Path $cr 'source')
  if((HashDT1 $src) -cne $r.Value){throw 'Component resource drift'}
  $dst=WithinDT1 (Join-Path (Join-Path $out 'source') $r.Name) (Join-Path $out 'source')
  [IO.Directory]::CreateDirectory((Split-Path -Parent $dst)) | Out-Null
  [IO.File]::Copy($src,$dst,$false)
  $resources[$r.Name]=HashDT1 $dst
 }
 foreach($boot in $c.boots){if($boot -cin $boots -or !$resources.Contains($boot)){throw 'Invalid boot'};$boots+=,$boot}
 $testPath=Join-Path $cr 'tests.json';$testRel=[IO.Path]::GetRelativePath($workspace,$testPath).Replace('\','/')
 $pins[$testRel]=HashDT1 $testPath
 $witnesses=@()
 foreach($p in Get-ChildItem -LiteralPath (Join-Path $cr 'readback') -File -Filter '*.json'){
  $rel=[IO.Path]::GetRelativePath($workspace,$p.FullName).Replace('\','/');$pins[$rel]=HashDT1 $p.FullName;$witnesses+=,@{path=$rel;sha256=$pins[$rel]}
 }
 $componentRecords+=,@{path=[IO.Path]::GetRelativePath($workspace,$cp).Replace('\','/');sha256=HashDT1 $cp;tests=$testRel;tests_sha256=$pins[$testRel];readbacks=$witnesses}
}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
B71Parser | Out-Null
$inventory=@(B72Inventory $game)
$stock=Get-Content -LiteralPath (Join-Path $workspace 'research/q307_extracted/json/ep1/quest/ep1.quest.json') -Raw | ConvertFrom-Json
$used=@($stock.Data.RootChunk.graph.Data.nodes.Data.id)+@($inventory.id)
$ids=@()
foreach($boot in $boots){$id=B72Id ($boot+':1');if($id -in $used -or $id -in $ids -or $id -ne (B72IdIndependent ($boot+':1'))){throw 'Injection collision'};$ids+=,$id}
$xls=@(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/mod') -File -Filter '*.xl' | Sort-Object Name | ForEach-Object {@{name=$_.Name;sha256=HashDT1 $_.FullName}})
$archive=Join-Path $out 'TowerContinued_Dogtown_DT1.archive'
$xl=B71Render $boots;B71Parse $xl | Out-Null
[IO.File]::WriteAllText(($archive+'.xl'),$xl,[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$stream=[IO.File]::Create($archive)
try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $out 'source')),$stream)){throw 'Pack failed'}}finally{$stream.Dispose()}
$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError' -or $packed.Files.Count -ne $resources.Count){throw 'Archive resource count mismatch'}
foreach($entry in $packed.Files.Values){
 if(!$resources.Contains($entry.Name)){throw 'Unexpected packed resource'}
 $memory=[IO.MemoryStream]::new()
 try{$entry.Extract($memory);if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) -cne $resources[$entry.Name]){throw 'Packed resource differs'}}finally{$memory.Dispose()}
}
$files=@($archive,($archive+'.xl')) | ForEach-Object {@{relative='archive/pc/mod/'+[IO.Path]::GetFileName($_);sha256=HashDT1 $_}}
$result=[ordered]@{status='BUILT_DT1_LIVE_PENDING';files=@($files);resources=$resources;boots=$boots;injection_ids=$ids;components=$componentRecords;source_pins=$pins;native_sources=$native;installed_injections=$inventory;installed_xl=$xls;packed_readback=$true;native_scenes_unchanged=$true;runtime_scripts_added=0;official_overrides=@();game_writes=0;save_writes=0;scope='Bounded post-Tower Dogtown native sandbox owners only; no EP1/story root restart or wanted/quest fact reset.'}
[IO.File]::WriteAllText((Join-Path $out 'build.json'),($result | ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
@{status=$result.status;build=$out;sha256=HashDT1 (Join-Path $out 'build.json');resources=$resources.Count;boots=$boots.Count} | ConvertTo-Json
