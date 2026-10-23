param([int]$Round=3)
$ErrorActionPreference='Stop'
$py='C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$refs=@((& $py prealpha/courier_c1/research.py missing)|ConvertFrom-Json)
if($LASTEXITCODE -ne 0){throw 'Reference discovery failed'}
if(!$refs.Count){Write-Output 'No missing phase/scene references';exit}
$dest=Join-Path (Get-Location) ('research/courier_c1/dependencies_{0:d2}' -f $Round)
if(Test-Path $dest){throw 'Evidence exists'}
$archives=@(Get-ChildItem -LiteralPath "$game/archive/pc/content","$game/archive/pc/ep1" -Filter '*.archive'|Where-Object {$_.Name -match 'gamedata'}|ForEach-Object {$_.FullName})
& ./tools/extract_resources.ps1 -ResourcePaths $refs -OutputRoot $dest -ArchivePaths $archives
