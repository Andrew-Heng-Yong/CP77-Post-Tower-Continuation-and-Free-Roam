Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$wk=Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$out=Join-Path $ws 'research/housing_h1/purchase/web_official_01'
if(Test-Path -LiteralPath $out){throw 'Use an immutable successor extraction'}
New-Item -ItemType Directory $out|Out-Null
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$wanted=@('base\gameplay\gui\world\internet\templates\apartments\web_template_apartments_01_product_page.inkwidget','base\gameplay\gui\world\internet\templates\apartments\web_template_apartments_01_product_page_b.inkwidget','base\gameplay\gui\world\internet\templates\apartments\web_template_apartments_01_product_page_c.inkwidget')
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/archive/pc'
$archives=@(Get-ChildItem -LiteralPath (Join-Path $game 'content') -Filter '*.archive' -File)+@(Get-ChildItem -LiteralPath (Join-Path $game 'ep1') -Filter '*.archive' -File)
$rows=[Collections.Generic.List[object]]::new();$used=[Collections.Generic.List[object]]::new()
foreach($archive in $archives){
 $arc=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw 'Official archive read failed'}
 $count=0
 foreach($entry in $arc.Files.Values){
  $dep=$entry.Name
  if($dep -cnotin $wanted){continue}
  $memory=[IO.MemoryStream]::new()
  try{
   $entry.Extract($memory);$raw=Join-Path $out ($archive.BaseName+'/raw/'+$dep);$json=Join-Path $out ($archive.BaseName+'/json/'+$dep+'.json')
   New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null
   [IO.File]::WriteAllBytes($raw,$memory.ToArray());Export-Cr2wJson (Read-Cr2wFile $raw) $json
   $rows.Add(@{depot=$dep;archive=$archive.FullName;raw=[IO.Path]::GetRelativePath($ws,$raw).Replace('\','/');json=[IO.Path]::GetRelativePath($ws,$json).Replace('\','/');raw_sha256=(Get-FileHash $raw).Hash;json_sha256=(Get-FileHash $json).Hash});$count++
  }finally{$memory.Dispose()}
 }
 if($count){$used.Add(@{path=$archive.FullName;length=$archive.Length;last_write_utc=$archive.LastWriteTimeUtc.ToString('o')})}
}
foreach($p in $wanted){if(@($rows|Where-Object {$_.depot -ceq $p}).Count -eq 0){throw ('Missing source '+$p)}}
$result=@{status='CURRENT_OFFICIAL_HOUSING_SOURCES';rows=$rows.ToArray();archives=$used.ToArray();extractor_sha256=(Get-FileHash $PSCommandPath).Hash;tool_sha256=(Get-FileHash (Join-Path $wk 'WolvenKit.RED4.dll')).Hash;game_writes=0}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),($result|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
Write-Output ('EXTRACTED '+$rows.Count)
