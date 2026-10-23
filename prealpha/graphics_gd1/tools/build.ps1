param(
    [string]$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path,
    [string]$GameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
    [string]$BuildName = 'gd1_01'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($BuildName -notmatch '^gd1_[0-9]{2}$') { throw 'BuildName must be gd1_NN.' }

# This existing file is imported ONLY for serialization/archive helper definitions.
. (Join-Path $WorkspaceRoot 'tools/build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$diagRoot = Join-Path $WorkspaceRoot 'prealpha/graphics_gd1'
$outRoot = Join-Path $diagRoot "build/$BuildName"
if (Test-Path -LiteralPath $outRoot) { throw 'Refusing to overwrite an existing/pinned GD1 build.' }
$depot = 'ep1\fx\quest\q307\q307_dizzy.effect'
$originalPath = Join-Path $WorkspaceRoot ('research/graphics_investigation_20261013/misty_dizzy/raw/' + $depot)
$originalExpected = '008E93AD4225D08BE81E89A634F3E77FF516655B2C5650DA4DE644CAA38965A3'
if ((Get-FileHash -LiteralPath $originalPath -Algorithm SHA256).Hash -ne $originalExpected) { throw 'Original extracted effect hash differs.' }

function Get-ObjectJson($Value) {
    $opts = [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
    return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($Value, $opts)
}
function Write-Json($Value, [string]$Path) {
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 30), [Text.UTF8Encoding]::new($false))
}
function Get-BytesSha([byte[]]$Bytes) { return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)) }
function Read-Archive([string]$Path) {
    $a = $null
    $result = $archiveReader.ReadArchive($Path, $hashService, [ref]$a)
    if ($result.ToString() -ne 'NoError') { throw "Archive decode failed: $Path / $result" }
    return $a
}

$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$nativePath = Join-Path $GameRoot 'archive/pc/ep1/ep1_2_gamedata.archive'
$native = Read-Archive $nativePath
$entry = @($native.Files.Values | Where-Object Name -eq $depot)
if ($entry.Count -ne 1) { throw 'Expected exactly one original native effect.' }
$resourceKey = $entry[0].Key
$mem = [IO.MemoryStream]::new()
try { $entry[0].Extract($mem); if ((Get-BytesSha $mem.ToArray()) -ne $originalExpected) { throw 'Extracted source is not current original game resource.' } }
finally { $mem.Dispose() }

# Key comparison also detects an unresolved-name collision; no other installed
# archive may provide this target for a meaningful isolated diagnostic.
$collisionAudit = [Collections.Generic.List[object]]::new()
$modArchives = @(Get-ChildItem -LiteralPath (Join-Path $GameRoot 'archive/pc/mod') -File -Filter '*.archive' | Sort-Object FullName)
foreach ($file in $modArchives) {
    $a = Read-Archive $file.FullName
    $hits = @($a.Files.Values | Where-Object { $_.Key -eq $resourceKey -or $_.Name -eq $depot })
    $collisionAudit.Add([ordered]@{ name=$file.Name; length=$file.Length; target_hits=$hits.Count; resource_count=$a.Files.Count })
    if ($hits.Count -ne 0) { throw "Existing target override prevents isolated diagnostic: $($file.Name)" }
}

$fx = Read-Cr2wFile -Path $originalPath
$r = $fx.RootChunk
if ($r.GetType().Name -ne 'worldEffect' -or $r.Length.ToString() -ne '40.0625' -or $r.EffectLoops.Count -ne 0 -or $r.InputParameterNames.Count -ne 0) { throw 'Original effect identity/lifetime differs.' }
$types = @($r.Events | ForEach-Object { $_.Chunk.GetType().Name })
if (($types -join '|') -ne 'effectTrackItemVignette|effectTrackItemColorGrade|effectTrackItemChromaticAberration') { throw 'Original visual event set differs.' }
$counts = @($r.TrackRoot.Chunk.Tracks | ForEach-Object { $_.Chunk.Items.Count })
if (($counts -join ',') -ne '0,1,0,1,1') { throw 'Original five native track shells differ.' }
foreach ($i in @(1,3,4)) {
    $eventIndex = switch ($i) { 1 {0} 3 {1} 4 {2} }
    if (-not [object]::ReferenceEquals($r.TrackRoot.Chunk.Tracks[$i].Chunk.Items[0].Chunk, $r.Events[$eventIndex].Chunk)) { throw 'Track item is not expected event handle.' }
}

$sourceRoot = Join-Path $outRoot 'source'
$originalCopy = Join-Path $outRoot ('original/' + $depot)
$patchedPath = Join-Path $sourceRoot $depot
New-Item -ItemType Directory -Path (Split-Path -Parent $originalCopy) -Force | Out-Null
Copy-Item -LiteralPath $originalPath -Destination $originalCopy
Export-Cr2wJson -File $fx -Path (Join-Path $outRoot 'original.json')

# The only semantic change: remove the three visual event instances and their
# corresponding track references. Retain all native track shells, effect length,
# identity, input parameters, looping metadata, scene caller and camera handback.
$r.Events.Clear()
foreach ($track in $r.TrackRoot.Chunk.Tracks) { $track.Chunk.Items.Clear() }
$expectedRootJson = Get-ObjectJson $r
Write-Cr2wFile -File $fx -Path $patchedPath
$readback = Read-Cr2wFile -Path $patchedPath
if ((Get-ObjectJson $readback.RootChunk) -cne $expectedRootJson) { throw 'Patched CR2W readback has unintended semantic differences.' }
if ($readback.RootChunk.Events.Count -ne 0 -or @($readback.RootChunk.TrackRoot.Chunk.Tracks | Where-Object { $_.Chunk.Items.Count -ne 0 }).Count -ne 0) { throw 'Residual active visual track references.' }
Export-Cr2wJson -File $readback -Path (Join-Path $outRoot 'patched.json')

# Independent identity/lifetime comparison after stripping only allowed deltas.
$normalizedOriginal = Read-Cr2wFile -Path $originalCopy
$normalizedOriginal.RootChunk.Events.Clear()
foreach ($track in $normalizedOriginal.RootChunk.TrackRoot.Chunk.Tracks) { $track.Chunk.Items.Clear() }
if ((Get-ObjectJson $normalizedOriginal.RootChunk) -cne (Get-ObjectJson $readback.RootChunk)) { throw 'Unexpected root/track metadata change.' }
if ($fx.MetaData.Version -ne $readback.MetaData.Version -or $fx.MetaData.BuildVersion -ne $readback.MetaData.BuildVersion) { throw 'CR2W metadata changed.' }

$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File)
if ($sourceFiles.Count -ne 1 -or [IO.Path]::GetRelativePath($sourceRoot, $sourceFiles[0].FullName) -ne $depot) { throw 'Source includes non-target resources.' }
$archiveName = 'TowerContinued_DizzyDiagnostic_GD1.archive'
$archivePathGD1 = Join-Path $outRoot $archiveName
$stream = [IO.File]::Create($archivePathGD1)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($sourceRoot), $stream)) { throw 'ArchiveWriter failed.' }
} finally { $stream.Dispose() }
$packed = Read-Archive $archivePathGD1
if ($packed.Files.Count -ne 1 -or $packed.Files.Values[0].Name -ne $depot -or $packed.Files.Values[0].Key -ne $resourceKey) { throw 'Archive resource identity/count differs.' }
$patchedSha = (Get-FileHash -LiteralPath $patchedPath -Algorithm SHA256).Hash
$mem = [IO.MemoryStream]::new()
try {
    $packed.Files.Values[0].Extract($mem)
    if ((Get-BytesSha $mem.ToArray()) -ne $patchedSha) { throw 'Packed resource differs from patched source.' }
    $mem.Position = 0
    $cr = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($mem)
    $packedFx = $null
    if ($cr.ReadFile([ref]$packedFx, $true).ToString() -ne 'NoError' -or (Get-ObjectJson $packedFx.RootChunk) -cne $expectedRootJson) { throw 'Packed CR2W semantic readback failed.' }
} finally { $mem.Dispose() }
if ((Get-FileHash -LiteralPath $originalPath -Algorithm SHA256).Hash -ne $originalExpected) { throw 'Original source changed during build.' }

Write-Json @($collisionAudit) (Join-Path $outRoot 'collision_audit.json')
$manifest = [ordered]@{
    status='BUILT_GD1_DIAGNOSTIC'; created_utc=[DateTime]::UtcNow.ToString('o')
    archive=$archiveName; archive_sha256=(Get-FileHash -LiteralPath $archivePathGD1 -Algorithm SHA256).Hash
    archive_bytes=(Get-Item -LiteralPath $archivePathGD1).Length
    resource_count=1; resource_depot=$depot; resource_key=$resourceKey.ToString()
    original_sha256=$originalExpected; patched_sha256=$patchedSha
    builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    source_relative=('source/' + $depot); original_relative=('original/' + $depot)
    native_archive=$nativePath; collision_audit='collision_audit.json'; scanned_installed_archives=$modArchives.Count
    change='Clear all three q307_dizzy visual events and matching track items; retain all five track shells, finite lifetime40.0625s and other metadata.'
    includes_scripts=$false; includes_xl=$false; game_save_cache_settings_writes=$false
    native_empty_analogue='Two original empty effect tracks exist. Bounded search did not locate a whole empty native effect. Structurally decoded no-op resource is not proof of in-engine validity; user live diagnostic remains necessary.'
    live_verified=$false; shader_cause_confirmed=$false
}
Write-Json $manifest (Join-Path $outRoot 'build.json')
$tests = [ordered]@{
    status='PASS_NOT_LIVE'; build_sha256=(Get-FileHash -LiteralPath (Join-Path $outRoot 'build.json') -Algorithm SHA256).Hash
    checks=@(
        'Original extracted SHA256 pinned and matches currently installed original archive payload.'
        'No existing installed mod archive has target depot/key.'
        'Original worldEffect type, finite40.0625 length, zero loops and zero input names pinned.'
        'Original three visual event types and0,1,0,1,1 native track layout pinned.'
        'Original nonempty track handles point to the matching visual events.'
        'Patched CR2W reads successfully with zero root events.'
        'All five native track shells retained and have zero item references.'
        'Complete normalized root semantic comparison allows only cleared events/items.'
        'CR2W Version and BuildVersion retained.'
        'Pack source contains exactly one intended resource.'
        'Archive reopens with exactly one target depot and same key.'
        'Extracted packed payload byte hash equals patched source.'
        'Extracted packed CR2W decodes and matches complete expected root semantics.'
        'Original extracted source remains byte-identical after build.'
    )
    limitations=@('No game launch or rendered-image proof.','No renderer/shader/driver diagnosis established.','No changes to scene timing/callers, camera PA4, scripts, saves, settings or caches.')
}
Write-Json $tests (Join-Path $outRoot 'tests.json')
$manifest | ConvertTo-Json -Depth 10
