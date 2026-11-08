# Read only the already-pinned header; never load gameplay or write a save.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../..')).FullName
$output = Join-Path $PSScriptRoot 'header.json'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$evidence = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'extraction.json') -Raw | ConvertFrom-Json
foreach ($path in @($evidence.source, $evidence.metadata)) {
    $item = Get-Item -LiteralPath $path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked save input refused' }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
if ((Get-FileHash -LiteralPath $evidence.source).Hash -cne $evidence.source_sha256 -or (Get-FileHash -LiteralPath $evidence.metadata).Hash -cne $evidence.metadata_sha256) { throw 'Pinned historical source changed' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$file = [IO.File]::Open($evidence.source, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
$reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($file)
$header = $null
try {
    if ($reader.ReadFileInfo([ref]$header).ToString() -cne 'NoError') { throw 'Header reader failed' }
    $result = @{
        status = 'READ_ONLY_PINNED_HEADER'; source = $evidence.source; source_sha256 = $evidence.source_sha256; metadata_sha256 = $evidence.metadata_sha256
        save_version = $header.SaveVersion; game_version = $header.GameVersion; archive_version = $header.ArchiveVersion
        game_def_path = $header.GameDefPath; timestamp = $header.TimeStamp
        parser_sha256 = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.IO.CyberpunkSaveReader].Assembly.Location)).Hash
        save_writes = 0; game_calls = 0
    }
} finally { $reader.Dispose() }
if ((Get-FileHash -LiteralPath $evidence.source).Hash -cne $evidence.source_sha256 -or (Get-FileHash -LiteralPath $evidence.metadata).Hash -cne $evidence.metadata_sha256) { throw 'Source changed while reading header' }
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
$result | ConvertTo-Json -Depth 4
