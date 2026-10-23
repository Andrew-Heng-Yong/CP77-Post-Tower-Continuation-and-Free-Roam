param([string]$Revision='native_02')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$out=Join-Path $ws ('research/sidejobs_s23/ep1/'+$Revision)
if($Revision -cnotmatch '^native_\d{2}$' -or (Test-Path -LiteralPath $out)){throw 'Immutable extraction revision required'}
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File).FullName)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$wanted=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($ap in $archives){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($e in $a.Files.Values){
  if(($e.Name -match '^ep1\\quest\\main_quests\\q304\\' -and $e.Extension -in @('.quest','.questphase')) -or ($e.Name -match '(bill_default|hasan_default)' -and $e.Extension -in @('.questphase','.scene')) -or ($e.Name -match '^ep1\\[^\\]+\\[^\\]+\.questphase$') -or ($e.Name -match 'world_stories\\[^\\]+\.questphase$')){[void]$wanted.Add($e.Name)}
 }
}
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @($wanted) -OutputRoot $out -ArchivePaths $archives
