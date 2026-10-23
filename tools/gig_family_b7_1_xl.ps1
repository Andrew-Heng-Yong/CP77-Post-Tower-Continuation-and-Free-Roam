# B7.1 configuration-only repair helpers. Dot-source; no build or deployment at load.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')

function B71Parser {
    $path = 'C:\Users\Ayong\Documents\WolvenKit-8.20.0\YamlDotNet.dll'
    R5Match $path '86F873F682C619A0C24E263DCDD15FE027104666641C92F503516671D61EDDA6'
    Add-Type -Path $path
    return $path
}

function B71Manifest([string]$Workspace) {
    $path = Join-Path $Workspace 'research/gig_restoration/family_b7/manifest.json'
    R5Match $path '806C20C539258ECE459415700B96955C24CB6858995B99C990DF5DB4B3CBDD6E'
    $m = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    if ($m.owners -ne 55 -or @($m.resources).Count -ne 245 -or @($m.boots).Count -ne 76 -or -not $m.packed_readback) { throw 'Pinned B7 manifest shape mismatch' }
    if (@($m.boots | Sort-Object -Unique).Count -ne 76) { throw 'Duplicate boot' }
    foreach ($boot in $m.boots) {
        if ($boot -cnotin $m.resources -or $boot -cnotmatch '^towercontinued\\family_b7\\(sts_[a-z0-9_]+\\boot|tiers\\[a-z]+_\d+)\.questphase$') { throw "Invalid or unpacked boot: $boot" }
    }
    if (@($m.boots | Where-Object { $_ -match '\\tiers\\' }).Count -ne 21) { throw 'Tier count mismatch' }
    return $m
}

function B71Render([string[]]$Boots) {
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('quest:')
    $lines.Add('  phases:')
    foreach ($boot in $Boots) {
        # Individual Add calls avoid the previous PowerShell +/comma array coercion.
        $lines.Add('    - path: ' + $boot)
        $lines.Add('      parent: ep1\quest\ep1.quest')
        $lines.Add('      input:')
        $lines.Add('        node: [1]')
        $lines.Add('        socket: Out')
    }
    return ($lines -join "`n") + "`n"
}

function B71Parse([string]$Text) {
    $stream = [YamlDotNet.RepresentationModel.YamlStream]::new()
    $reader = [IO.StringReader]::new($Text)
    try { $stream.Load($reader) } finally { $reader.Dispose() }
    if ($stream.Documents.Count -ne 1) { throw 'Expected one YAML document' }
    return ,$stream.Documents[0].RootNode
}

function B71Map($Node, [string[]]$Keys) {
    if ($Node -isnot [YamlDotNet.RepresentationModel.YamlMappingNode]) { throw 'Expected YAML mapping' }
    $actual = @($Node.Children.Keys | ForEach-Object {
        if ($_ -isnot [YamlDotNet.RepresentationModel.YamlScalarNode]) { throw 'Expected scalar mapping key' }
        $_.Value
    })
    if ((($actual | Sort-Object) -join '|') -cne (($Keys | Sort-Object) -join '|')) { throw 'Unexpected YAML keys' }
}

function B71Child($Node, [string]$Key) {
    return ,$Node.Children[[YamlDotNet.RepresentationModel.YamlScalarNode]::new($Key)]
}

function B71Scalar($Node, [string]$Expected) {
    if ($Node -isnot [YamlDotNet.RepresentationModel.YamlScalarNode] -or $Node.Value -cne $Expected) { throw "Expected YAML scalar: $Expected" }
}

function B71Validate([string]$Text, $Manifest) {
    $root = B71Parse $Text
    B71Map $root @('quest')
    $quest = B71Child $root 'quest'
    B71Map $quest @('phases')
    $phases = B71Child $quest 'phases'
    if ($phases -isnot [YamlDotNet.RepresentationModel.YamlSequenceNode] -or $phases.Children.Count -ne 76) { throw 'Expected 76 phase entries' }
    for ($i = 0; $i -lt 76; $i++) {
        $entry = $phases.Children[$i]
        B71Map $entry @('path','parent','input')
        B71Scalar (B71Child $entry 'path') $Manifest.boots[$i]
        B71Scalar (B71Child $entry 'parent') 'ep1\quest\ep1.quest'
        $inputNode = B71Child $entry 'input'
        B71Map $inputNode @('node','socket')
        B71Scalar (B71Child $inputNode 'socket') 'Out'
        $nodes = B71Child $inputNode 'node'
        if ($nodes -isnot [YamlDotNet.RepresentationModel.YamlSequenceNode] -or $nodes.Children.Count -ne 1) { throw 'Expected single parent input node' }
        B71Scalar $nodes.Children[0] '1'
    }
    return [ordered]@{ phases=76; gig_boots=55; earned_tiers=21; exact_pinned_bindings=$true; parser=[YamlDotNet.RepresentationModel.YamlStream].Assembly.FullName }
}
