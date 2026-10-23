Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$source='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-6'
$dest=Join-Path $workspace 'recovery/ncpd_n1_fixture_20261014/AutoSave-6'
if(Test-Path $dest){throw 'Fixture already preserved'}
if((Get-FileHash -LiteralPath (Join-Path $source 'sav.dat')).Hash -cne 'EEB8EC10B5162A332E88239E18E83D096BD98E6FC6602771B0D758E0B45BBAFA'){throw 'AutoSave slot changed; do not copy a different save under this identity'}
$files=@(Get-ChildItem -LiteralPath $source -Force -File)
if($files.Count -ne 3 -or @($files|Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count){throw 'Unexpected fixture shape'}
New-Item -ItemType Directory -Path $dest|Out-Null
$rows=@()
foreach($f in $files){
 $before=(Get-FileHash -LiteralPath $f.FullName).Hash
 $target=Join-Path $dest $f.Name
 [IO.File]::Copy($f.FullName,$target,$false)
 if((Get-FileHash -LiteralPath $target).Hash -cne $before -or (Get-FileHash -LiteralPath $f.FullName).Hash -cne $before){throw 'Fixture changed during copy'}
 $rows+=,@{name=$f.Name;sha256=$before}
}
$result=@{status='BYTE_EXACT_WORKSPACE_BACKUP';source=$source;backup=$dest;files=$rows;metadata='level48, 11:14:31, 14.10.2026';source_unchanged=$true;runtime_writes=0}
[IO.File]::WriteAllText((Join-Path (Split-Path $dest -Parent) 'fixture.json'),($result|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
