param([string]$OutputName = 'instances_01')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^[a-z][a-z0-9_]+$') { throw 'Use a simple fresh output directory name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$bindings = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'bindings_01.json') | ConvertFrom-Json -Depth 80
$sector = @($bindings | Where-Object { $_.source.target.depot.EndsWith('exterior_-28_-37_0_0.streamingsector') })
if ($sector.Count -ne 1 -or (Get-FileHash -LiteralPath $sector[0].source.captured).Hash -cne $sector[0].source.sha256) { throw 'Sector missing or changed' }
$sector = $sector[0]
[IO.Directory]::CreateDirectory($output) | Out-Null
$stream = [IO.File]::OpenRead($sector.source.captured)
$reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
try {
    $info = $null
    if ($reader.ReadFileInfo([ref]$info, $null).ToString() -ne 'NoError') { throw 'CR2W header read failed' }
    $instances = foreach ($match in ($sector.matches | Where-Object { $_.PSObject.Properties.Name -contains 'instance_buffer_number' })) {
        $record = $info.BufferInfo[$match.instance_buffer_number - 1]
        $stream.Position = $record.offset
        $memory = [IO.MemoryStream]::new()
        try {
            [WolvenKit.Core.Compression.Oodle]::DecompressAndCopySegment($stream, $memory, $record.diskSize, $record.memSize)
            $bytes = $memory.ToArray()
        } finally { $memory.Dispose() }
        if ($bytes.Length -ne $record.memSize) { throw 'Instance buffer size mismatch' }
        $buffer = [WolvenKit.RED4.Types.RedBuffer]::CreateBuffer($record.flags, $bytes)
        $buffer.ParentTypes.Add('entEntityInstanceData.buffer') | Out-Null
        $packageReader = $null
        if (-not [WolvenKit.RED4.Archive.BufferHelper]::TryGetReader($buffer, [ref]$packageReader)) { throw 'No instance package reader' }
        if ($packageReader.ReadBuffer($buffer).ToString() -ne 'NoError') { throw 'Instance package decode failed' }
        $name = $match.ref.Split('/')[-1].TrimStart('#')
        $path = Join-Path $output ($name + '.json')
        $bufferPath = Join-Path $output ($name + '.bin')
        [IO.File]::WriteAllBytes($bufferPath, $bytes)
        $json = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($buffer.Data.RootChunk, [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
        Set-Content -LiteralPath $path -Value $json -Encoding utf8NoBOM
        @{
            ref = $match.ref; template = $match.template; global_node_id = $match.global_node_id
            root_cruids = @($buffer.Data.RootCruids | ForEach-Object { $_.ToString() })
            buffer_number = $match.instance_buffer_number; chunk_type = $buffer.Data.RootChunk.GetType().Name
            decoded = $path; decoded_sha256 = (Get-FileHash -LiteralPath $path).Hash
            raw = $bufferPath; raw_sha256 = (Get-FileHash -LiteralPath $bufferPath).Hash
        }
    }
} finally { $reader.Dispose(); $stream.Dispose() }
@{sector = $sector.source; instances = @($instances)} | ConvertTo-Json -Depth 16 |
    Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
$instances | ForEach-Object { '{0} {1}' -f $_.chunk_type, $_.decoded }
