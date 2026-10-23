param([string]$Revision='native_02')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$out=Join-Path $ws ('research/sidejobs_s24/ep1/'+$Revision)
if($Revision -cnotmatch '^native_\d{2}$' -or (Test-Path -LiteralPath $out)){throw 'Immutable extraction revision required'}
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File).FullName)
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @('base\journal\cooked_journal.journal','ep1\journal\cooked_journal.journal','base\quest\minor_quests\mq025\phases\mq025_01_tease.questphase') -OutputRoot $out -ArchivePaths $archives
