param([string]$Revision='native_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $ws ('research/sidejobs_s25/services/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable output exists'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File).FullName)
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @(
 'base\quest\bugfixing\minor_quests\mq000\mq000_quest_bugfixes.questphase',
 'base\quest\bugfixing\minor_quests\mq033\mq033_quest_bugfixes.questphase',
 'base\quest\main_quests\prologue\q001\scenes\q001_04_ripperdoc.scene'
) -OutputRoot $out -ArchivePaths $archives
