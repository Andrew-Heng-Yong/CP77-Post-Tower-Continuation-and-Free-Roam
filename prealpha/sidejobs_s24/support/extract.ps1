param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $ws ('research/sidejobs_s24/support/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable extraction exists'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$wanted=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($ap in $archives){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($e in $a.Files.Values){if($e.Name -match '^base\\quest\\holocalls\\(lizzy|r3no)\\.*\.(questphase|scene)$'){[void]$wanted.Add($e.Name)}}
}
if($wanted.Count -lt 6){throw 'Missing contact resources'}
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @($wanted) -OutputRoot $out -ArchivePaths $archives

