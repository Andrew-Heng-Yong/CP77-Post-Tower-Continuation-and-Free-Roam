$ErrorActionPreference='Stop'
$root=Join-Path $PSScriptRoot '../../..'
$dest=Join-Path $root 'research/dogtown_dt1/interactions/native_01'
if(Test-Path -LiteralPath $dest){throw 'Immutable evidence destination exists'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$refs=@(
 'ep1\openworld\community\ep1_community.questphase',
 'ep1\openworld\world_encounters\ep1_world_encounters.questphase',
 'ep1\openworld\dynamic_events\ep1_dynamic_events.questphase',
 'ep1\openworld\combat_zone_convoy\combat_zone_convoy.questphase',
 'ep1\openworld\combat_zone_drones\combat_zone_drones.questphase',
 'ep1\openworld\scene\chats\stadium\cz_stadium_chats_questphase.questphase'
)
$archives=@(Get-ChildItem -LiteralPath "$game/archive/pc/content","$game/archive/pc/ep1" -Filter '*.archive' | Where-Object {$_.Name -match 'gamedata'} | ForEach-Object {$_.FullName})
& (Join-Path $root 'tools/extract_resources.ps1') -ResourcePaths $refs -OutputRoot $dest -ArchivePaths $archives
