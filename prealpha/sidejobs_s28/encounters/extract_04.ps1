param([string]$Revision='native_04')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
if($Revision -cnotmatch '^native_\d{2}$'){throw 'Invalid revision'}
$out=Join-Path $ws ('research/sidejobs_s28/encounters/'+$Revision)
if(Test-Path -LiteralPath $out){throw 'Immutable extraction exists'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter '*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter '*.archive' -File).FullName)
$wanted=@('ep1\quest\main_quests\q301\phases\q301_hook_setup.questphase','ep1\quest\main_quests\q301\phases\q301_hook_bugfixes.questphase')
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths $wanted -OutputRoot $out -ArchivePaths $archives
