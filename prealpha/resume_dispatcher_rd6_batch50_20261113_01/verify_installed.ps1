# Read current registered phase mappings and all providers of the watched depot keys.
param([Parameter(Mandatory)][string]$Evidence)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$evidenceFolder = Get-Item -LiteralPath $Evidence -Force
if (!$evidenceFolder.PSIsContainer -or $evidenceFolder.Parent.FullName -ine $PSScriptRoot -or
    $evidenceFolder.Name -notlike 'evidence_*' -or
    ($evidenceFolder.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Expected a contained evidence directory'
}
$Evidence = $evidenceFolder.FullName
$inputPath = Join-Path $Evidence 'provider_watch.json'
$inputs = Get-Content -Raw -LiteralPath $inputPath | ConvertFrom-Json -AsHashtable -Depth 100
$output = Join-Path $Evidence 'installed_readback.json'
if (Test-Path -LiteralPath $output) { throw 'Fresh installed readback required' }
$game = $inputs.game
$xl = Join-Path $game $inputs.xl.path
if ((Get-FileHash -LiteralPath $xl).Hash -cne $inputs.xl.sha256) { throw 'Installed XL drift' }
$wk = Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
[void][Reflection.Assembly]::LoadFrom((Join-Path $wk 'YamlDotNet.dll'))

function Convert-PhaseYaml($Node) {
    if ($Node -is [YamlDotNet.RepresentationModel.YamlScalarNode]) { return $Node.Value }
    if ($Node -is [YamlDotNet.RepresentationModel.YamlSequenceNode]) {
        return ,@($Node.Children | ForEach-Object { Convert-PhaseYaml $_ })
    }
    if ($Node -is [YamlDotNet.RepresentationModel.YamlMappingNode]) {
        $mapping = [ordered]@{}
        foreach ($child in $Node.Children.GetEnumerator()) {
            $mapping[$child.Key.Value] = Convert-PhaseYaml $child.Value
        }
        return $mapping
    }
    throw 'Unsupported YAML node'
}

$yaml = [YamlDotNet.RepresentationModel.YamlStream]::new()
$reader = [IO.StringReader]::new([IO.File]::ReadAllText($xl))
try { $yaml.Load($reader) } finally { $reader.Dispose() }
$bindings = foreach ($doc in $yaml.Documents) {
    $data = Convert-PhaseYaml $doc.RootNode
    if ($data.Contains('quest')) { $data.quest.phases }
}

$keys = [Collections.Generic.HashSet[uint64]]::new()
foreach ($resource in $inputs.resources) {
    $key = [uint64]$resource.key
    if ($key -ne [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($resource.depot)) {
        throw "Resource key drift: $($resource.depot)"
    }
    [void]$keys.Add($key)
}
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$files = @(foreach ($relative in 'archive/pc','mods') {
    $root = Join-Path $game $relative
    if (!(Test-Path -LiteralPath $root)) { continue }
    if ((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Linked archive root: $root"
    }
    if (@(Get-ChildItem -LiteralPath $root -Recurse -Force -Attributes ReparsePoint).Count) {
        throw "Linked archive tree: $root"
    }
    Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.archive'
})
$readback = foreach ($file in ($files | Sort-Object FullName)) {
    $stamp = @($file.Length,$file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if ($archiveReader.ReadArchive($file.FullName,$names,[ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive: $($file.FullName)"
    }
    foreach ($key in $keys) {
        if (!$archive.Files.ContainsKey($key)) { continue }
        $memory = [IO.MemoryStream]::new()
        try {
            $archive.Files[$key].Extract($memory)
            $memory.Position = 0
            $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory))
        } finally {
            $memory.Dispose()
        }
        @{key=[string]$key; archive=$file.FullName; sha256=$digest}
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Archive changed during review' }
}
if ((Get-FileHash -LiteralPath $xl).Hash -cne $inputs.xl.sha256) { throw 'Installed XL changed during review' }
@{
    input_sha256=(Get-FileHash -LiteralPath $inputPath).Hash
    archives=@($files.FullName | Sort-Object)
    providers=@($readback)
    bindings=@($bindings)
} | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
Write-Output "Read $($keys.Count) watched keys across $($files.Count) archives and $(@($bindings).Count) installed XL bindings."
