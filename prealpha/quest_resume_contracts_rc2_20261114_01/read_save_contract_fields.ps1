# Project journal entries and known native state tables from the pinned pre-Tower fixture.
param([ValidateRange(1,99)][int]$Attempt = 1)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot ('save_projection_{0:00}.json' -f $Attempt)
if (Test-Path -LiteralPath $output) { throw 'Fresh save evidence required' }
$pinPath = Join-Path $workspace 'prealpha/handler_preservation_hp1_20261112_01/saves_01/ManualSave-26/manifest.json'
$pinHash = '6D914C82878C704B70A96CF5A2D94781739E94C41E2F14C7FC5ECD3553509E7D'
if ((Get-FileHash -LiteralPath $pinPath).Hash -cne $pinHash) { throw 'Pinned save manifest changed' }
$pin = Get-Content -LiteralPath $pinPath -Raw | ConvertFrom-Json -Depth 50
$source = $pin.source
foreach ($path in $PSScriptRoot,$source) {
    for ($entry = Get-Item -LiteralPath $path -Force; $null -ne $entry;) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $path" }
        $entry = if ($entry -is [IO.DirectoryInfo]) { $entry.Parent } else { $entry.Directory }
    }
}
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'inputs.json') -Raw | ConvertFrom-Json -Depth 50
$engine = Join-Path $plan.game_root 'bin/x64/Cyberpunk2077.exe'
$engineHash = (Get-FileHash -LiteralPath $engine).Hash
if ($engineHash -cne 'D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4') { throw 'Native layout evidence is bound to a different executable' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$kind = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $kind.Assembly.Location).Hash
if ($parserHash -cne $pin.parser_sha256) { throw 'Save reader changed' }
$meta = Join-Path (Split-Path $source -Parent) 'metadata.9.json'
if ((Get-FileHash -LiteralPath $meta).Hash -cne $pin.metadata_sha256) { throw 'Fixture metadata changed' }
$data = [IO.File]::ReadAllBytes($source)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($data)) -cne $pin.source_sha256) {
    throw 'Fixture body changed'
}
$memory = [IO.MemoryStream]::new($data,$false)
$reader = $kind::new($memory)
try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save reader failed' }
    if ($save.FileHeader.SaveVersion -ne 277 -or $pin.save_version -ne 277) { throw 'Unsupported save version' }
    $journal = @($save.Nodes | Where-Object Name -ceq 'JournalManager')
    $quest = @($save.Nodes | Where-Object Name -ceq 'questSystem')
    if ($journal.Count -ne 1 -or $quest.Count -ne 1) { throw 'Expected one native journal and quest system' }
    $facts = @($quest[0].Children | Where-Object Name -ceq 'FactsDB')
    if ($facts.Count -ne 1 -or $facts[0].Children.Count -ne 10) { throw 'Native fact table layout changed' }
    $hashMethod = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {
        $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]
    })
    if ($hashMethod.Count -ne 1) { throw 'Unexpected saved fact key conversion' }
    $tables = [ordered]@{}
    foreach ($index in 1,3,4,5) {
        $table = $facts[0].Children[$index - 1].Value
        if ($table -isnot [WolvenKit.RED4.Save.FactsTable]) { throw 'Invalid table type' }
        $tables[[string]$index] = @(foreach ($entry in $table.FactEntries) {
            $key = [uint32]$hashMethod[0].Invoke($null, [object[]]@($entry.FactName))
            ,@($key, [uint32]$entry.Value)
        })
    }
    $journalRows = @(foreach ($entry in $journal[0].Value.Entries) {
        $raw = [byte[]]$entry.UnkownBytes
        if ($raw.Length -ne 15) { throw 'Unexpected journal record shape' }
        ,@([BitConverter]::ToUInt32($raw, 0), [BitConverter]::ToUInt32($raw, 4))
    })
    if ((Get-FileHash -LiteralPath $source).Hash -cne $pin.source_sha256 -or
        (Get-FileHash -LiteralPath $meta).Hash -cne $pin.metadata_sha256) { throw 'Fixture changed during the read' }
    $result = @{save_sha256=$pin.source_sha256; fixture_manifest_sha256=$pinHash; parser_sha256=$parserHash
        engine_sha256=$engineHash; save_version=277; journal_hash_and_state=$journalRows; native_tables=$tables}
    $bytes = [Text.Encoding]::UTF8.GetBytes(($result | ConvertTo-Json -Depth 12 -Compress))
    $out = [IO.File]::Open($output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try { $out.Write($bytes,0,$bytes.Length) } finally { $out.Dispose() }
    Write-Output "Read $($journalRows.Count) serialized journal entries and tables 1, 3, 4 and 5."
} finally {
    $reader.Dispose()
    $memory.Dispose()
}
