param(
    [ValidateRange(1,99)][int]$Assessment = 2,
    [ValidateRange(1,99)][int]$Attempt = 1
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot ('archive_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $out) { throw 'Fresh archive output required' }
$rd10 = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01'
$manifestPath = Join-Path $rd10 'deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $manifestPath).Hash -cne 'AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8') {
    throw 'RD10 manifest drift'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$archiveName = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$installed = Join-Path $manifest.game_root $archiveName
if ((Get-FileHash -LiteralPath $installed).Hash -cne $manifest.archive_sha256) { throw 'Installed archive drift' }
$evidence = Join-Path $PSScriptRoot ('evidence_{0:00}/assessment.json' -f $Assessment)
$proof = Get-Content -LiteralPath $evidence -Raw | ConvertFrom-Json -AsHashtable
if ($proof.status -cne 'WORKSPACE_CANDIDATE_CHECKED' -or $proof.script.manifest_sha256 -cne (Get-FileHash -LiteralPath $manifestPath).Hash) {
    throw 'Select a verified Claire candidate'
}
$graph = Join-Path $PSScriptRoot ('graph_{0:00}' -f $proof.graph)
$entry = 'towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase'
$reply = 'towercontinued\sidejobs_s29\continuation\mq058_claire_reply.questphase'
$targets = [ordered]@{ $entry = 'entry'; $reply = 'reply' }
foreach ($depot in $targets.Keys) {
    $file = Join-Path $graph ($targets[$depot] + '.questphase')
    if ((Get-FileHash -LiteralPath $file).Hash -cne $proof.archive_changes[$depot]) { throw "Graph drift: $depot" }
}

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Open-Archive([string]$Path) {
    $result = $null
    if ($reader.ReadArchive($Path,$names,[ref]$result).ToString() -cne 'NoError') { throw "Cannot read archive $Path" }
    $result
}
function Key([string]$Depot) { [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot) }
function Hash-Member($Entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        $Entry.Extract($stream)
        $stream.Position = 0
        [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream))
    } finally { $stream.Dispose() }
}
function Assert-Plain([string]$Path) {
    for ($item = Get-Item -LiteralPath $Path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path $Path" }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}

$entryKey = Key $entry
$replyKey = Key $reply
$providerCount = 0
$scanned = 0
foreach ($relative in 'archive/pc','mods') {
    $folder = Join-Path $manifest.game_root $relative
    if (!(Test-Path -LiteralPath $folder)) { continue }
    Assert-Plain $folder
    if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive tree' }
    foreach ($file in Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive') {
        $stamp = @($file.Length,$file.LastWriteTimeUtc.Ticks)
        $archive = Open-Archive $file.FullName
        if ($archive.Files.ContainsKey($replyKey)) { throw "Reply depot is already provided by $($file.FullName)" }
        if ($archive.Files.ContainsKey($entryKey)) {
            if ($file.FullName -ine $installed) { throw "Unexpected entry provider $($file.FullName)" }
            $providerCount++
        }
        $file.Refresh()
        if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) { throw 'Provider changed during scan' }
        $scanned++
    }
}
if ($providerCount -ne 1) { throw 'Existing S29 entry provider missing' }

$readbackPath = Join-Path $rd10 'archive_01/readback.json'
if ((Get-FileHash -LiteralPath $readbackPath).Hash -cne '5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81') {
    throw 'Pinned readback drift'
}
$previous = Get-Content -LiteralPath $readbackPath -Raw | ConvertFrom-Json
$donor = Join-Path $rd10 'archive_01/source'
Assert-Plain $donor
if (@(Get-ChildItem -LiteralPath $donor -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked source tree' }
$source = Join-Path $out 'source'
[void][IO.Directory]::CreateDirectory($source)
$current = Open-Archive $installed
$expected = @{}
foreach ($member in $previous.members) {
    $path = Join-Path $donor $member.depot
    $key = Key $member.depot
    if (!$current.Files.ContainsKey($key) -or $expected.ContainsKey($key) -or
        (Get-FileHash -LiteralPath $path).Hash -cne $member.sha256 -or
        (Hash-Member $current.Files[$key]) -cne $member.sha256) { throw "Source drift $($member.depot)" }
    $sha = $member.sha256
    if ($member.depot -ceq $entry) {
        $path = Join-Path $graph 'entry.questphase'
        $sha = $proof.archive_changes[$entry]
    }
    $dest = Join-Path $source $member.depot
    [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
    [IO.File]::Copy($path,$dest,$false)
    $expected[$key] = $sha
}
if ($expected.Count -ne 1748 -or $current.Files.Count -ne $expected.Count) { throw 'Incomplete baseline' }
$dest = Join-Path $source $reply
[void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
[IO.File]::Copy((Join-Path $graph 'reply.questphase'),$dest,$false)
$expected[$replyKey] = $proof.archive_changes[$reply]
$packed = Join-Path $out 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($packed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($names,[WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Packing failed' }
} finally { $stream.Dispose() }
$packedArchive = Open-Archive $packed
if ($packedArchive.Files.Count -ne $expected.Count) { throw 'Packed inventory mismatch' }
foreach ($key in $expected.Keys) {
    if (!$packedArchive.Files.ContainsKey($key) -or (Hash-Member $packedArchive.Files[$key]) -cne $expected[$key]) {
        throw "Packed payload mismatch $key"
    }
}
if ((Get-FileHash -LiteralPath $installed).Hash -cne $manifest.archive_sha256) { throw 'Installed archive changed during verification' }
@{ status = 'MEMBERS_VERIFIED'; packed = (Get-FileHash -LiteralPath $packed).Hash;
   members = $expected.Count; archives_scanned = $scanned; unchanged = 1747;
   graph = $proof.graph; changed_payloads = $proof.archive_changes;
   changed = @($entry,$reply); assessment_sha256 = (Get-FileHash -LiteralPath $evidence).Hash } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Verified $($expected.Count) members across $scanned provider archives."
