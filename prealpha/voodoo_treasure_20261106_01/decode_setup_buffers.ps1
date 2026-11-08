param([string]$OutputName = 'setups_01')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^[a-z][a-z0-9_]+$') { throw 'Use a simple fresh output directory name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$scan = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'sectors_01/manifest.json') | ConvertFrom-Json -Depth 80
$rows = @($scan.providers | Where-Object {
    $_.target.depot -match '(quest_02032d862a5c14c8|exterior_-28_-37_0_0|always_loaded_0)\.streamingsector$' -and $_.captured
})
if ($rows.Count -ne 3) { throw 'Expected exact trigger, gameplay sector and always-loaded candidate' }
[IO.Directory]::CreateDirectory($output) | Out-Null
$data = foreach ($row in $rows) {
    if ((Get-FileHash -LiteralPath $row.captured).Hash -cne $row.sha256) { throw 'Captured sector changed' }
    $stream = [IO.File]::OpenRead($row.captured)
    $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
    try {
        $info = $null
        if ($reader.ReadFileInfo([ref]$info, $null).ToString() -ne 'NoError') { throw 'CR2W header read failed' }
        $buffer = $info.BufferInfo[0]
        if ($buffer.memSize -eq 0 -or $buffer.memSize % 0x90 -ne 0) { throw 'First buffer is not an integral setup array' }
        $stream.Position = $buffer.offset
        $decoded = [IO.MemoryStream]::new()
        try {
            [WolvenKit.Core.Compression.Oodle]::DecompressAndCopySegment($stream, $decoded, $buffer.diskSize, $buffer.memSize)
            $bytes = $decoded.ToArray()
        } finally { $decoded.Dispose() }
        if ($bytes.Length -ne $buffer.memSize) { throw 'Setup buffer size mismatch' }
        $path = Join-Path $output ([IO.Path]::GetFileNameWithoutExtension($row.captured) + '.setups.bin')
        [IO.File]::WriteAllBytes($path, $bytes)
        $names = @($row.string_matches | Where-Object { $_.StartsWith('$/') } | ForEach-Object {
            $name = $_.TrimEnd('?')
            @{ref = $name; hash = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($name).ToString()}
        })
        @{
            source = $row; refs = $names; buffer_path = $path; offset = $buffer.offset
            disk_size = $buffer.diskSize; size = $buffer.memSize; sha256 = (Get-FileHash -LiteralPath $path).Hash
        }
    } finally { $reader.Dispose(); $stream.Dispose() }
}
$data | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
$data | Select-Object -Property offset,disk_size,size,buffer_path
