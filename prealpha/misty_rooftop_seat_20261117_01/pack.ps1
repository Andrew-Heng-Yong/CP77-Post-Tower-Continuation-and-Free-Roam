# Preserve every active archive payload and add the two private seating resources.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$work = Join-Path $PSScriptRoot 'work'
$out = Join-Path $work 'pack_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh archive output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly `
    -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

function Json([string]$path) { return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable -Depth 100 -DateKind String }
function Hash([string]$path) { return (Get-FileHash -LiteralPath $path).Hash }
function Plain([string]$path) {
    for ($item = Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input $path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}

$manifestPath = Join-Path $workspace 'prealpha/misty_rooftop_lift_20261117_01/installed_manifest.json'
$manifestHash = 'B738804793E5E669D71F72E9FB7755B2786D2B25E3B0A212681F10427C9EF5C0'
if ((Hash $manifestPath) -cne $manifestHash) { throw 'Installed manifest drift' }
$manifest = Json $manifestPath
$scene = Json (Join-Path $work 'scene_01/manifest.json')
$providers = Json (Join-Path $work 'native_01/providers.json')
if ($scene.status -cne 'SERIALIZED' -or $scene.baseline_sha256 -cne $manifestHash -or
    $providers.manifest_sha256 -cne $manifestHash -or $scene.resources.Count -ne 2) { throw 'Unqualified scene inputs' }
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$xlRel = $archiveRel + '.xl'
$archive = Join-Path $manifest.game_root $archiveRel
$xl = Join-Path $manifest.game_root $xlRel
foreach ($path in @($archiveRel, $xlRel)) {
    $expected = @($manifest.core_files | Where-Object path -ceq $path)
    $actual = Join-Path $manifest.game_root $path
    Plain $actual
    if ($expected.Count -ne 1 -or (Hash $actual) -cne $expected[0].sha256) { throw "Installed package drift $path" }
}

$currentArchivePaths = @(foreach ($relative in 'archive/pc','mods') {
    $folder = Join-Path $manifest.game_root $relative
    if (Test-Path -LiteralPath $folder) {
        Plain $folder
        if (@(Get-ChildItem -LiteralPath $folder -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive directory' }
        Get-ChildItem -LiteralPath $folder -Recurse -File -Filter '*.archive'
    }
})
if ($currentArchivePaths.Count -ne $providers.archives.Count) { throw 'Current archive inventory changed' }
$archivePins = @{}
foreach ($row in $providers.archives) { $archivePins[$row.path] = $row }
foreach ($file in $currentArchivePaths) {
    $pin = $archivePins[$file.FullName]
    if (!$pin -or $file.Length -ne $pin.length -or $file.LastWriteTimeUtc.ToString('o') -cne $pin.last_write_utc) {
        throw "Archive changed since provider scan $($file.FullName)"
    }
}

$donorRoot = Join-Path $workspace 'prealpha/world_overlap_20261116_01/work/archive_01'
$donor = Json (Join-Path $donorRoot 'readback.json')
$donorSource = Join-Path $donorRoot 'source'
Plain $donorSource
if (@(Get-ChildItem -LiteralPath $donorSource -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive source' }
if ($donor.status -cne 'MEMBERS_VERIFIED' -or $donor.archive_sha256 -cne $manifest.archive_sha256 -or
    $donor.members.Count -ne 1749) { throw 'Donor does not match the active archive' }

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function OpenArchive([string]$path) {
    $file = $null
    if ($reader.ReadArchive($path, $hashService, [ref]$file).ToString() -cne 'NoError') { throw "Archive could not open $path" }
    return $file
}
function DepotKey([string]$path) { return [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($path) }
function MemberHash($entry) {
    $memory = [IO.MemoryStream]::new()
    try {
        $entry.Extract($memory)
        $memory.Position = 0
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory))
    } finally { $memory.Dispose() }
}

$old = OpenArchive $archive
if ($old.Files.Count -ne $donor.members.Count) { throw 'Installed archive inventory changed' }
[void][IO.Directory]::CreateDirectory($out)
$staging = Join-Path $out 'source'
$members = @{}
function CopyMember([string]$depot, [string]$src, [string]$sha256) {
    $key = DepotKey $depot
    if ($members.ContainsKey($key) -or (Hash $src) -cne $sha256) { throw "Member collision or drift $depot" }
    $dest = Join-Path $staging $depot
    [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
    [IO.File]::Copy($src, $dest, $false)
    $members[$key] = @{depot=$depot;sha256=$sha256}
}
foreach ($item in $donor.members) {
    $key = DepotKey $item.depot
    if (!$old.Files.ContainsKey($key) -or (MemberHash $old.Files[$key]) -cne $item.sha256) { throw "Active payload drift $($item.depot)" }
    CopyMember $item.depot (Join-Path $donorSource $item.depot) $item.sha256
}
foreach ($item in $scene.resources) {
    if ($item.depot -cnotmatch '^towercontinued\\misty_rooftop_seat\\(gate\.questphase|sit\.scene)$' -or
        $item.depot -cnotin $providers.queries -or @($providers.hits | Where-Object depot -ceq $item.depot).Count) {
        throw "Unapproved private depot or provider collision $($item.depot)"
    }
    CopyMember $item.depot $item.raw $item.sha256
}

$package = Join-Path $out 'package'
$newArchive = Join-Path $package $archiveRel
[void][IO.Directory]::CreateDirectory((Split-Path $newArchive -Parent))
$stream = [IO.File]::Open($newArchive, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($staging), $stream)) { throw 'Archive packing failed' }
} finally { $stream.Dispose() }
$new = OpenArchive $newArchive
if ($new.Files.Count -ne 1751 -or $new.Files.Count -ne $members.Count) { throw 'Packed member count differs' }
foreach ($key in $members.Keys) {
    if (!$new.Files.ContainsKey($key) -or (MemberHash $new.Files[$key]) -cne $members[$key].sha256) {
        throw "Packed member drift $($members[$key].depot)"
    }
}

$oldXL = [IO.File]::ReadAllText($xl)
if ([regex]::Matches($oldXL, '(?m)^streaming:').Count -ne 1) { throw 'ArchiveXL registration insertion point changed' }
$newline = if ($oldXL.Contains("`r`n")) { "`r`n" } else { "`n" }
$entry = @('    - path: towercontinued\misty_rooftop_seat\gate.questphase', '      parent: ep1\quest\ep1.quest',
    '      input:', '        node: [1]', '        socket: Out', '') -join $newline
$newXL = Join-Path $package $xlRel
[IO.File]::WriteAllText($newXL, $oldXL.Replace('streaming:', ($entry + 'streaming:')), [Text.UTF8Encoding]::new($false))
foreach ($path in @($archiveRel, $xlRel)) {
    $expected = ($manifest.core_files | Where-Object path -ceq $path).sha256
    if ((Hash (Join-Path $manifest.game_root $path)) -cne $expected) { throw "Installed package changed during packing: $path" }
}
$packageFiles = @(foreach ($path in @($archiveRel, $xlRel)) {
    $file = Get-Item -LiteralPath (Join-Path $package $path)
    @{path=$path;bytes=$file.Length;sha256=(Hash $file.FullName)}
})
@{status='MEMBERS_VERIFIED';baseline_sha256=$manifestHash;package_files=$packageFiles;xl_addition=$entry;
   unchanged_members=$old.Files.Count;packed_members=$new.Files.Count;provider_count=$providers.archives.Count;
   private_resources=$scene.resources;native_resource_changes=0;game_writes=0} |
    ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output 'Read back all 1,751 archive payloads. All 1,749 prior members match the installed archive.'
