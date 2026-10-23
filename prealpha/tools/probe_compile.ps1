param([Parameter(Mandatory)][string]$Build)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$stage=Join-Path $Build ('source_probe_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'))
New-Item -ItemType Directory $stage|Out-Null
Copy-Item -LiteralPath (Join-Path $Build 'package/r6/scripts/PTFR_PreAlpha') -Destination (Join-Path $stage 'scripts') -Recurse
foreach($part in @('entry','phone','arrival')){
 foreach($f in Get-ChildItem -LiteralPath (Join-Path $ws ('prealpha/'+$part+'/scripts')) -File -Filter '*.reds'){
  $matches=@(Get-ChildItem -LiteralPath (Join-Path $stage 'scripts') -File -Recurse -Filter $f.Name)
  if($matches.Count -ne 1){throw "Probe source absent/ambiguous $($f.Name)"}
  Copy-Item -LiteralPath $f.FullName -Destination $matches[0].FullName
 }
}
$cli=Join-Path $ws 'research/finalboards_dismissal/tooling/redscript-cli.exe'
$args=@('compile','-s',(Join-Path $stage 'scripts'),'-s',(Join-Path $game 'red4ext/plugins/Codeware/Scripts'),'-b',(Join-Path $game 'r6/cache/final.redscripts'),'-o',(Join-Path $stage 'probe.redscripts'))
$log=(& $cli @args 2>&1|Out-String)
[IO.File]::WriteAllText((Join-Path $stage 'probe.log'),$log,[Text.UTF8Encoding]::new($false))
if($LASTEXITCODE -ne 0 -or $log -notmatch 'Output successfully saved'){Write-Output $log;throw 'Source probe failed; not installable'}
Write-Output ('SOURCE_PROBE_ONLY_PASS '+$stage)
