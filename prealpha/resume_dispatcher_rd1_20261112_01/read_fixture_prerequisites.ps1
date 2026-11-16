# Additional read-only facts from the already-reviewed historical fixture.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pin=Get-Content -LiteralPath (Join-Path $workspace 'prealpha/handler_preservation_hp1_20261112_01/saves_01/AutoSave-5/manifest.json') -Raw|ConvertFrom-Json
$output=Join-Path $PSScriptRoot 'fixture_prerequisites_01.json'
if(Test-Path -LiteralPath $output){throw 'Fresh output required'}
if((Get-FileHash -LiteralPath $pin.source).Hash -cne $pin.source_sha256){throw 'Historical fixture changed'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if((Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash -cne $pin.parser_sha256){throw 'Parser changed'}
$toHash=@([WolvenKit.RED4.Save.Fact].GetMethods()|Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})[0]
$keys=@{};$values=[ordered]@{}
foreach($name in @('q305_done','q306_done','q001_done','q005_done','q101_enable_side_content')){
 $fact=[WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name);$key=[uint32]$toHash.Invoke($null,[object[]]@($fact));$keys[$key]=$name;$values[$name]=$null
}
$bytes=[IO.File]::ReadAllBytes($pin.source)
if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $pin.source_sha256){throw 'Fixture changed during read'}
$stream=[IO.MemoryStream]::new($bytes,$false);$reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream);$save=$null
try{
 if($reader.ReadFile([ref]$save).ToString() -cne 'NoError'){throw 'Save parse failed'}
 $root=@($save.Nodes|Where-Object Name -ceq 'questSystem');if($root.Count -ne 1){throw 'Ambiguous root'}
 $facts=@($root[0].Children|Where-Object Name -ceq 'FactsDB');if($facts.Count -ne 1 -or $facts[0].Children.Count -ne 10){throw 'Unexpected fact store'}
 foreach($entry in $facts[0].Children[0].Value.FactEntries){$key=[uint32]$toHash.Invoke($null,[object[]]@($entry.FactName));if($keys.ContainsKey($key)){$values[$keys[$key]]=[uint32]$entry.Value}}
}finally{$reader.Dispose();$stream.Dispose()}
if((Get-FileHash -LiteralPath $pin.source).Hash -cne $pin.source_sha256){throw 'Fixture changed'}
@{status='READ_ONLY_HISTORICAL_FACT_PROJECTION';source=$pin.source;source_sha256=$pin.source_sha256;facts=$values;save_writes=0;game_calls=0}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8NoBOM
$values|ConvertTo-Json -Compress
