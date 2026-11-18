# Repack the installed scene with the two corrected choice nodes.
param([string]$Python = 'C:/Users/Ayong/.local/bin/python3.14.exe')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$previous = Join-Path $workspace 'prealpha/misty_roof_lighting_and_seat_20261118_01'
$out = Join-Path $PSScriptRoot 'work/pack_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
$geometryJson = & $Python -X utf8 -B (Join-Path $PSScriptRoot 'prompt.py') --target
if ($LASTEXITCODE -ne 0) { throw 'Rooftop coordinate check failed' }
$geometry = $geometryJson | ConvertFrom-Json
$manifest = Get-Content -LiteralPath (Join-Path $previous 'installed_manifest.json') -Raw | ConvertFrom-Json
$relative = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$livePath = Join-Path $manifest.game_root $relative
$source = Join-Path $workspace 'prealpha/misty_rooftop_alignment_20261118_01/work/pack_01/source'
$depot = 'towercontinued\misty_rooftop_seat\sit.scene'
function Digest($path) { (Get-FileHash -LiteralPath $path).Hash }
if ((Digest $livePath) -cne $manifest.archive_sha256) { throw 'Installed archive drift' }
if (@(Get-ChildItem -LiteralPath $source -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked source tree' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$names = [WolvenKit.Common.Services.HashService]::new()
$names.Load()
function OpenArchive($path) {
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$names,[ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive $path" }
    return $archive
}
function Member($archive, [uint64]$key) {
    $memory = [IO.MemoryStream]::new()
    try { $archive.Files[$key].Extract($memory); return ,$memory.ToArray() } finally { $memory.Dispose() }
}
function ByteHash([byte[]]$bytes) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }
$installed = OpenArchive $livePath
$scenePath = Join-Path $source $depot
if ((Digest $scenePath) -cne '6C3BE8EA9BF382D748D2ECADF8B2CB83079FB271EA6D0F72804D9C392076B2F1') { throw 'Unexpected chair input' }
$scene = Read-Cr2wFile $scenePath
$choices = @($scene.RootChunk.SceneGraph.Chunk.Graph | ForEach-Object { $_.Chunk } | Where-Object { $_.GetType().Name -ceq 'scnChoiceNode' })
if ($choices.Count -ne 2) { throw 'Unexpected choice graph' }
foreach ($choice in $choices) {
    if ($choice.DisplayNameOverride.ToString() -cne 'LocKey#46417') { throw 'Unexpected input label' }
    $choice.DisplayNameOverride = [WolvenKit.RED4.Types.CString]::op_Implicit([string]$geometry.label)
}
$sit = @($choices | Where-Object { $_.NodeId.Id.ToString() -eq '4' })
if ($sit.Count -ne 1) { throw 'Sit choice missing' }
$atw = $sit[0].AtwParams
$atw.EntityPosition.X = [float]$geometry.x
$atw.EntityPosition.Y = [float]$geometry.y
$atw.EntityPosition.Z = [float]$geometry.z
$atw.EntityOrientation.K = [float]$geometry.k
$atw.EntityOrientation.R = [float]$geometry.r
$shape = $sit[0].ShapeParams.Chunk
$shape.Rotation.K = [float]$geometry.shape_k
$shape.Rotation.R = [float]$geometry.shape_r
$staging = Join-Path $out 'source'
$target = Join-Path $staging $depot
[void][IO.Directory]::CreateDirectory((Split-Path $target -Parent))
Write-Cr2wFile $scene $target
$expected = @{}
foreach ($file in Get-ChildItem -File -Recurse -LiteralPath $source) {
    $name = [IO.Path]::GetRelativePath($source,$file.FullName)
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name)
    if ($expected.ContainsKey($key) -or !$installed.Files.ContainsKey($key)) { throw "Unexpected member $name" }
    $hash = ByteHash (Member $installed $key)
    if ($hash -cne (Digest $file.FullName)) { throw "Source drift $name" }
    if ($name -cne $depot) {
        $dest = Join-Path $staging $name
        [void][IO.Directory]::CreateDirectory((Split-Path $dest -Parent))
        [IO.File]::Copy($file.FullName,$dest,$false)
    } else { $hash = Digest $target }
    $expected[$key] = $hash
}
if ($installed.Files.Count -ne 1751 -or $expected.Count -ne $installed.Files.Count) { throw 'Incomplete archive inventory' }
$package = Join-Path $out ('package/' + $relative)
[void][IO.Directory]::CreateDirectory((Split-Path $package -Parent))
$stream = [IO.File]::Open($package, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($names, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($staging),$stream)) { throw 'Archive pack failed' }
} finally { $stream.Dispose() }
$packed = OpenArchive $package
if ($packed.Files.Count -ne $expected.Count) { throw 'Packed count changed' }
foreach ($key in $expected.Keys) {
    if (!$packed.Files.ContainsKey($key) -or (ByteHash (Member $packed $key)) -cne $expected[$key]) { throw "Packed member drift $key" }
}
$sceneKey = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
$readback = Join-Path $out 'packed.scene'
[IO.File]::WriteAllBytes($readback,(Member $packed $sceneKey))
Export-Cr2wJson (Read-Cr2wFile $readback) ($readback + '.json')
& $Python -X utf8 -B (Join-Path $PSScriptRoot 'prompt.py')
if ($LASTEXITCODE -ne 0 -or (Digest $livePath) -cne $manifest.archive_sha256) { throw 'Final scene or baseline check failed' }
@{status='MEMBERS_VERIFIED';checked_members=$packed.Files.Count;preserved_members=1750;
  baseline_sha256=(Digest (Join-Path $previous 'installed_manifest.json'));scene_depot=$depot;
  changed_member=@{before=(Digest $scenePath);after=(Digest $readback)};
  package_file=@{path=$relative;bytes=(Get-Item -LiteralPath $package).Length;sha256=(Digest $package)};
  packed_json_sha256=(Digest ($readback + '.json'))} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output "Verified $($packed.Files.Count) packed members."
