param([string]$Build='prealpha/sidejobs_s23/ep1/build/ep1_05',[string]$Revision='native_03')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$m=Get-Content (Join-Path $ws ($Build+'/component.json')) -Raw|ConvertFrom-Json
$deps=Get-Content (Join-Path $ws ($Build+'/dependencies.json')) -Raw|ConvertFrom-Json
$source=[ordered]@{}
foreach($p in $m.source_pins.PSObject.Properties){if($p.Name -match '/raw/(.+)$'){$source[$Matches[1].Replace('/','\')]=$p.Name}}
foreach($p in $deps.native_resources.PSObject.Properties){$source[$p.Name]=$p.Value.raw}
$out=Join-Path $ws ('research/sidejobs_s23/ep1/'+$Revision)
if($Revision -cnotmatch '^native_\d{2}$' -or (Test-Path -LiteralPath $out)){throw 'Immutable new extraction required'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$archives=@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/content') -Filter 'basegame_*.archive' -File).FullName)+@((Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc/ep1') -Filter 'ep1_*.archive' -File).FullName)
& (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @($source.Keys) -OutputRoot $out -ArchivePaths $archives
$results=[ordered]@{}
foreach($p in $source.GetEnumerator()){
 $expected=(Get-FileHash (Join-Path $ws $p.Value)).Hash;$actual=(Get-FileHash (Join-Path $out ('raw/'+$p.Key))).Hash
 if($expected -cne $actual){throw ('Official bytes changed: '+$p.Key)}
 $results[$p.Key]=[ordered]@{source=$p.Value;sha256=$actual;official_witness=('research/sidejobs_s23/ep1/'+$Revision+'/raw/'+$p.Key.Replace('\','/'))}
}
$report=[ordered]@{status='PASS_OFFICIAL_BYTES';component=(Get-FileHash (Join-Path $ws ($Build+'/component.json'))).Hash;verifier_sha256=(Get-FileHash $PSCommandPath).Hash;comparisons=$results;scope='Read official archives only; no game/saves/cache modifications.'}
[IO.File]::WriteAllText((Join-Path $out 'official_comparison.json'),($report|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
Write-Output ('PASS '+$results.Count+' original resources byte-identical')
