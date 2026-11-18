# Read saved world-state and weather payloads for inspection. No save writes.
param([Parameter(Mandatory)][string]$Slot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($Slot -cnotmatch '^(?:ManualSave|AutoSave|EndGameSave)-[0-9]+$') { throw 'Invalid save slot' }
$wk = 'C:/Users/Ayong/Documents/WolvenKit-8.20.0'
foreach ($name in 'WolvenKit.Core.dll', 'WolvenKit.Common.dll', 'WolvenKit.RED4.dll') {
    [void][Reflection.Assembly]::LoadFrom((Join-Path $wk $name))
}
$source = Join-Path ('C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077/' + $Slot) 'sav.dat'
$before = (Get-FileHash -LiteralPath $source).Hash
$stream = [IO.File]::Open($source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
try {
    $save = $null
    if (([WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)).ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save parse failed' }
    $world, $weather = $null, $null
    $world = @($save.Nodes | Where-Object Name -ceq 'WorldStateSystem')
    if ($world.Count -ne 1) { throw 'World state missing' }
    $weather = @($world[0].Children | Where-Object Name -ceq 'WeatherWorldState')
    if ($weather.Count -ne 1) { throw 'Weather missing' }
    $data = @{slot=$Slot;sha256=$before;world=[Convert]::ToBase64String($world[0].Value.HeaderBlob);
        weather=[Convert]::ToBase64String($weather[0].Value.HeaderBlob)}
} finally { $stream.Dispose() }
if ((Get-FileHash -LiteralPath $source).Hash -cne $before) { throw 'Save changed during read' }
$data | ConvertTo-Json -Compress
