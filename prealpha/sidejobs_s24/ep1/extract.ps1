param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$out=Join-Path $ws ('research/sidejobs_s24/ep1/'+$Revision)
if($Revision -cnotmatch '^native_\d{2}$' -or (Test-Path -LiteralPath $out)){throw 'Immutable extraction revision required'}
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File).FullName)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$wanted=[Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($ap in $archives){
 $a=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($ap,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Archive read failed'}
 foreach($e in $a.Files.Values){
  if($e.Name -match '(mq305|mq306|q304_car_retrieval)' -and $e.Extension -in @('.questphase','.scene')){[void]$wanted.Add($e.Name)}
 }
}
foreach($r in @('ep1\quest\minor_quests\ep1_minor_quests.questphase','ep1\quest\ep1_persistent_content.questphase','ep1\quest\main_quests\q304\q304.questphase','ep1\quest\holocalls\holocall_initializers_ep1.questphase','ep1\quest\holocalls\holocall_cleanup_ep1.questphase')){[void]$wanted.Add($r)}
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @($wanted) -OutputRoot $out -ArchivePaths $archives
