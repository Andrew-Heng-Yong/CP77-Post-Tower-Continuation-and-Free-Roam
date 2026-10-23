param([int]$Round=1)
$ErrorActionPreference='Stop'
$py='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$refs=if($Round -eq 1){@('base\quest\minor_quests\mq056\mq056.questphase')}else{@((& $py prealpha/races_r1/research.py missing)|ConvertFrom-Json)}
if(!$refs.Count){Write-Output 'Closure complete';return}
$dest=Join-Path (Get-Location) ('research/races_r1/native_{0:d2}' -f $Round)
if(Test-Path $dest){throw 'Evidence exists'}
$archives=@(Get-ChildItem -LiteralPath "$game/archive/pc/content","$game/archive/pc/ep1" -Filter '*gamedata*.archive'|ForEach-Object {$_.FullName})
& ./tools/extract_resources.ps1 -ResourcePaths $refs -OutputRoot $dest -ArchivePaths $archives
