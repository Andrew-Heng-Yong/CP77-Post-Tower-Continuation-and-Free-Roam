$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$report=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'decode_01/report_01.json') -Raw|ConvertFrom-Json -Depth 15
$unknown=@{}
foreach($row in $report.rows|Where-Object {!$_.parsed}){
 $text=[Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($row.raw))
 foreach($m in [regex]::Matches($text,'(?:^|\x00)(world[A-Za-z0-9_]{3,80})\x00')){
  $name=$m.Groups[1].Value
  if(![WolvenKit.RED4.Types.RedReflection]::GetTypes().ContainsKey($name)){$unknown[$name]=$true}
 }
}
@($unknown.Keys|Sort-Object)|ConvertTo-Json
