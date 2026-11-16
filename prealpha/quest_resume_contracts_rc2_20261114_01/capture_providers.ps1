# Read installed resource providers and phase bindings into a fresh workspace.
param([ValidateRange(1,99)][int]$Attempt = 1,
      [ValidatePattern('^inputs(_[0-9]{2})?\.json$')][string]$PlanName = 'inputs.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$inputPath = Join-Path $PSScriptRoot $PlanName
$out = Join-Path $PSScriptRoot ('capture_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$plan = Get-Content -LiteralPath $inputPath -Raw | ConvertFrom-Json -Depth 50
if ($plan.core_epoch -cne 'RD10_MEET_KIRK_CONTENT_LOCK') { throw 'Unexpected installed epoch' }
$wk = Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
[void][Reflection.Assembly]::LoadFrom((Join-Path $wk 'YamlDotNet.dll'))

function Assert-Plain([string]$Path) {
    for ($entry = Get-Item -LiteralPath $Path -Force; $null -ne $entry;) {
        if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $Path" }
        $entry = if ($entry -is [IO.DirectoryInfo]) { $entry.Parent } else { $entry.Directory }
    }
}

function Read-YamlNode($Node) {
    if ($Node -is [YamlDotNet.RepresentationModel.YamlScalarNode]) { return $Node.Value }
    if ($Node -is [YamlDotNet.RepresentationModel.YamlSequenceNode]) {
        return ,@($Node.Children | ForEach-Object { Read-YamlNode $_ })
    }
    if ($Node -is [YamlDotNet.RepresentationModel.YamlMappingNode]) {
        $result = [ordered]@{}
        foreach ($pair in $Node.Children.GetEnumerator()) { $result[$pair.Key.Value] = Read-YamlNode $pair.Value }
        return $result
    }
    throw "Unsupported YAML node: $($Node.GetType().FullName)"
}

function ProviderFiles {
    foreach ($relative in 'archive/pc','mods','red4ext/plugins') {
        $folder = Join-Path $plan.game_root $relative
        if (!(Test-Path -LiteralPath $folder)) { continue }
        Assert-Plain $folder
        foreach ($file in Get-ChildItem -LiteralPath $folder -Force -Recurse) {
            if ($file.PSIsContainer -and ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Linked provider directory: $($file.FullName)"
            }
            if (!$file.PSIsContainer -and $file.Extension -in '.archive','.xl') {
                Assert-Plain $file.FullName
                $file
            }
        }
    }
}

Assert-Plain $PSScriptRoot
foreach ($item in $plan.installed) {
    $path = Join-Path $plan.game_root $item.path
    Assert-Plain $path
    if ((Get-FileHash -LiteralPath $path).Hash -cne $item.sha256) { throw "Installed file changed: $($item.path)" }
}
$files = @(ProviderFiles | Sort-Object FullName)
$keys = [Collections.Generic.HashSet[uint64]]::new()
foreach ($key in $plan.keys) { [void]$keys.Add([uint64]$key) }
$hs = [WolvenKit.Common.Services.HashService]::new()
$hs.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$archiveRows = [Collections.Generic.List[object]]::new()
$rows = [Collections.Generic.List[object]]::new()
$configRows = [Collections.Generic.List[object]]::new()
$phases = [Collections.Generic.List[object]]::new()
$journals = [Collections.Generic.List[object]]::new()
foreach ($file in $files) {
    $size = $file.Length
    $timestamp = $file.LastWriteTimeUtc.Ticks
    $relative = [IO.Path]::GetRelativePath($plan.game_root, $file.FullName).Replace('\','/')
    if ($file.Extension -ieq '.archive') {
        $archive = $null
        if ($reader.ReadArchive($file.FullName, $hs, [ref]$archive).ToString() -cne 'NoError') {
            throw "Archive unreadable: $relative"
        }
        $archiveRows.Add(@{path=$relative; bytes=$size; ticks=$timestamp; members=$archive.Files.Count})
        foreach ($key in $keys) {
            if (!$archive.Files.ContainsKey($key)) { continue }
            $memory = [IO.MemoryStream]::new()
            try {
                $archive.Files[$key].Extract($memory)
                $memory.Position = 0
                $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory))
            } finally { $memory.Dispose() }
            $rows.Add(@{archive=$relative; key=[string]$key; sha256=$hash})
        }
    } else {
        $hash = (Get-FileHash -LiteralPath $file.FullName).Hash
        $yaml = [YamlDotNet.RepresentationModel.YamlStream]::new()
        $text = [IO.StringReader]::new([IO.File]::ReadAllText($file.FullName))
        try { $yaml.Load($text) } finally { $text.Dispose() }
        $configRows.Add(@{path=$relative; sha256=$hash; documents=$yaml.Documents.Count})
        for ($doc = 0; $doc -lt $yaml.Documents.Count; $doc++) {
            $root = Read-YamlNode $yaml.Documents[$doc].RootNode
            if ($root -isnot [Collections.IDictionary]) { throw "Unreviewed XL root: $relative" }
            if ($root.Contains('quest') -and $root.quest.Contains('phases')) {
                $ordinal = 0
                foreach ($binding in $root.quest.phases) {
                    if (!$binding.Contains('path') -or !$binding.Contains('parent')) { throw "Invalid phase binding: $relative" }
                    $phases.Add(@{path=$relative; document=$doc; ordinal=$ordinal; binding=$binding})
                    $ordinal++
                }
            }
            if ($root.Contains('journal')) {
                $journals.Add(@{path=$relative; document=$doc; journal=$root.journal})
            }
        }
        if ((Get-FileHash -LiteralPath $file.FullName).Hash -cne $hash) { throw "Changed XL input: $relative" }
    }
    $file.Refresh()
    if ($file.Length -ne $size -or $file.LastWriteTimeUtc.Ticks -ne $timestamp) { throw "Provider changed: $relative" }
}
if (@(Compare-Object @($files.FullName) @(ProviderFiles | ForEach-Object FullName)).Count) {
    throw 'Provider inventory changed during capture'
}
[void][IO.Directory]::CreateDirectory($out)
@{
    input_file=$PlanName; input_sha256=(Get-FileHash -LiteralPath $inputPath).Hash
    decoder_sha256=(Get-FileHash -LiteralPath ([WolvenKit.RED4.Archive.IO.CR2WReader].Assembly.Location)).Hash
    archives=$archiveRows.ToArray(); providers=$rows.ToArray(); xl_files=$configRows.ToArray()
    phase_bindings=$phases.ToArray(); journal_bindings=$journals.ToArray()
} | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
Write-Output "$($keys.Count) keys, $($rows.Count) matching archive payloads, $($archiveRows.Count) archives, $($phases.Count) XL quest bindings."
