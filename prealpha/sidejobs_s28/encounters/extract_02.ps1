param([string]$Revision='native_02')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $ws ('research/sidejobs_s28/encounters/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable extraction exists'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter '*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter '*.archive' -File).FullName)
$wanted=@('base\quest\main_quests\prologue\q001\q001.questphase','base\quest\main_quests\prologue\q005\q005_heist.questphase','base\quest\main_quests\part1\q101\phases\q101_cleanup.questphase','base\quest\main_quests\part1\q101\phases\q101_p2_meet_takemura.questphase','base\quest\main_quests\part1\q105\phases\q105_complete.questphase','base\quest\main_quests\part1\q110\q110.questphase','ep1\quest\main_quests\q301\q301.questphase')
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths $wanted -OutputRoot $out -ArchivePaths $archives
