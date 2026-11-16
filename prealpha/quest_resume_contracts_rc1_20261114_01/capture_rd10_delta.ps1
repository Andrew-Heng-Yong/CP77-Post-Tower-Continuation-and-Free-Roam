Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$inputPath = Join-Path $PSScriptRoot 'delta_input_01.json'
$inputData = Get-Content -Raw -LiteralPath $inputPath | ConvertFrom-Json -Depth 100
$out = Join-Path $PSScriptRoot 'delta_capture_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
if ((Get-FileHash -LiteralPath $inputData.archive -Algorithm SHA256).Hash -cne $inputData.archive_sha256) {
    throw 'RD10 archive changed'
}
$wk = Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wk
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$archive = $null
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
if ($reader.ReadArchive($inputData.archive,$hashService,[ref]$archive).ToString() -cne 'NoError') {
    throw 'RD10 archive unreadable'
}
New-Item -ItemType Directory -Path $out | Out-Null
$rows = [Collections.Generic.List[object]]::new()
$index = 0
foreach ($target in $inputData.members) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($target.depot)
    if (!$archive.Files.ContainsKey($key)) { throw "Member missing: $($target.depot)" }
    $entry = $archive.Files[$key]
    $memory = [IO.MemoryStream]::new()
    try { $entry.Extract($memory); $bytes = $memory.ToArray() } finally { $memory.Dispose() }
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    if ($digest -cne $target.sha256) { throw "Member changed: $($target.depot)" }
    $path = Join-Path $out ("{0:D2}.json" -f $index)
    $memory = [IO.MemoryStream]::new($bytes,$false)
    try {
        $resourceReader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($memory)
        $resource = $null
        $code = $resourceReader.ReadFile([ref]$resource,$true)
        if ($code.ToString() -cne 'NoError') { throw "Decode failed: $($target.depot): $code" }
        Export-Cr2wJson $resource $path
    } finally { $memory.Dispose() }
    $rows.Add(@{ depot=$target.depot; change=$target.change; prior_sha256=$target.prior_sha256;
                 sha256=$digest; export=$path; export_sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash })
    $index++
}
@{ source_sha256=(Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash;
   archive_sha256=$inputData.archive_sha256; rows=$rows.ToArray();
   game_writes=0; save_writes=0 } |
    ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
if ((Get-FileHash -LiteralPath $inputData.archive -Algorithm SHA256).Hash -cne $inputData.archive_sha256) {
    throw 'Archive changed during capture'
}
Write-Output "Captured $index RD10 graph members"
