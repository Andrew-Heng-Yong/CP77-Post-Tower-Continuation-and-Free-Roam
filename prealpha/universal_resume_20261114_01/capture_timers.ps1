# Read the exact timer and node-instance components from the pinned pre-Tower fixture.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'evidence_04'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$prior = Join-Path $workspace 'prealpha/handler_preservation_hp1_20261112_01/saves_01/ManualSave-26/manifest.json'
if ((Get-FileHash -LiteralPath $prior).Hash -cne '6D914C82878C704B70A96CF5A2D94781739E94C41E2F14C7FC5ECD3553509E7D') { throw 'Fixture manifest drift' }
$fixture = Get-Content -LiteralPath $prior -Raw | ConvertFrom-Json

foreach ($path in @($PSScriptRoot,$fixture.source)) {
    for ($item = Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input or output: $path" }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $parser.Assembly.Location).Hash
if ($parserHash -cne $fixture.parser_sha256) { throw 'Save reader drift' }
$bytes = [IO.File]::ReadAllBytes($fixture.source)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $fixture.source_sha256) { throw 'Save differs from pinned body' }

function Get-SingleNode($Nodes, [string]$Name) {
    $matches = @($Nodes | Where-Object Name -ceq $Name)
    if ($matches.Count -ne 1) { throw "Ambiguous or missing node: $Name" }
    return $matches[0]
}

$memory = [IO.MemoryStream]::new($bytes, $false)
$reader = $parser::new($memory)
$binary = [IO.BinaryReader]::new([IO.MemoryStream]::new($bytes,$false))
$decompressed = $null
$view = $null
try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw 'Unsupported save format' }
    $quest = Get-SingleNode $save.Nodes 'questSystem'
    $delay = Get-SingleNode $save.Nodes 'DelaySystem'
    $time = Get-SingleNode $save.Nodes 'TimeSystem'
    $selections = [ordered]@{
        instances = (Get-SingleNode $quest.Children 'nodeInstanceDataManager')
        delay_core = (Get-SingleNode $delay.Children '"Core"')
        delay_structs = (Get-SingleNode $delay.Children '"DelayedStructs"')
        time_core = (Get-SingleNode $time.Children '"Core"')
        time_timers = (Get-SingleNode $time.Children '"Timers"')
        delay_ticks = (Get-SingleNode (Get-SingleNode $save.Nodes 'DelaySystem_V2').Children 'DelayedTicks')
    }
    $settings = $null
    $decompressed = [WolvenKit.RED4.Save.Compression]::Decompress($binary,[ref]$settings)
    $view = [IO.BinaryReader]::new($decompressed,[Text.Encoding]::UTF8,$true)
    $capture = [ordered]@{}
    foreach ($name in $selections.Keys) {
        $node = $selections[$name]
        if ($node.Children.Count -ne 0 -or $node.Size -lt 4 -or $node.Size -gt 65536) {
            throw "Unsupported component: $name ($($node.Children.Count) children, $($node.Size) bytes)"
        }
        $decompressed.Position = $node.Offset
        $raw = $view.ReadBytes($node.Size)
        if ($raw.Length -ne $node.Size -or [BitConverter]::ToInt32($raw,0) -ne $node.Id) { throw "Offset/ID mismatch: $name" }
        $capture[$name] = @{ id = $node.Id; offset = $node.Offset; size = $node.Size; managed_trailing_size = $node.TrailingSize;
                            hex = [Convert]::ToHexString($raw) }
    }
    if ((Get-FileHash -LiteralPath $fixture.source).Hash -cne $fixture.source_sha256) { throw 'Source changed during capture' }
    [void][IO.Directory]::CreateDirectory($out)
    @{ source_sha256 = $fixture.source_sha256; parser_sha256 = $parserHash; save_version = $save.FileHeader.SaveVersion;
       components = $capture; save_writes = 0 } | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $out 'timers.json') -Encoding utf8NoBOM
} finally {
    if ($null -ne $view) { $view.Dispose() }
    if ($null -ne $decompressed) { $decompressed.Dispose() }
    $binary.Dispose()
    $reader.Dispose()
    $memory.Dispose()
}
