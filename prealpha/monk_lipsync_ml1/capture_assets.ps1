Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$planPath = Join-Path $PSScriptRoot 'plan.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json -Depth 80
if ((Get-FileHash -LiteralPath $plan.capture).Hash -cne $plan.capture_sha256) { throw 'Capture changed' }
$capture = Get-Content -LiteralPath $plan.capture -Raw | ConvertFrom-Json
$manifest = Get-Content -LiteralPath $plan.installed_manifest -Raw | ConvertFrom-Json
$out = Join-Path $PSScriptRoot 'assets_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh asset capture required' }
New-Item -ItemType Directory -Path $out | Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function Open-Archive([string]$path) {
    $archive = $null
    if ($reader.ReadArchive($path, $hashService, [ref]$archive).ToString() -cne 'NoError') { throw "Cannot index $path" }
    return $archive
}
function Key([string]$depot) {
    if ($depot -match '^[0-9]+$') { return [uint64]$depot }
    return [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
}
$paths = @(Get-ChildItem -LiteralPath (Join-Path $manifest.game_root 'archive/pc') -Filter '*.archive' -Recurse -File | Sort-Object FullName)
if (Compare-Object @($capture.archives) @($paths.FullName)) { throw 'Archive inventory changed' }
$queries = @{}
foreach ($depot in @($plan.asset_depots) + @($plan.other_custom_maps)) { $queries[(Key $depot)] = $depot }
$rigs = @{}
$rows = [Collections.Generic.List[object]]::new()
$englishVoiceMapNames = [Collections.Generic.List[object]]::new()
$index = 0
foreach ($path in $paths) {
    $index += 1
    $archive = Open-Archive $path.FullName
    if ($path.Name -like '*en_voice.archive') {
        foreach ($entry in $archive.Files.Values) {
            if ($entry.Name -like '*.lipmap') { $englishVoiceMapNames.Add(@{archive=$path.FullName;depot=$entry.Name}) }
        }
    }
    foreach ($key in $queries.Keys) {
        if (!$archive.Files.ContainsKey($key)) { continue }
        $depot = $queries[$key]
        $raw = Join-Path $out ($index.ToString() + '/' + $key.ToString() + [IO.Path]::GetExtension($depot))
        New-Item -ItemType Directory -Path (Split-Path -Parent $raw) -Force | Out-Null
        $stream = [IO.File]::Create($raw)
        try { $archive.Files[$key].Extract($stream) } finally { $stream.Dispose() }
        $resource = Read-Cr2wFile $raw
        $root = $resource.RootChunk
        $row = [ordered]@{depot=$depot;key=$key.ToString();archive=$path.FullName;raw=$raw;sha256=(Get-FileHash -LiteralPath $raw).Hash}
        if ($depot.EndsWith('.anims')) {
            if ($root.GetType().Name -cne 'animAnimSet') { throw "Not an animation set: $depot" }
            $row.rig = $root.Rig.DepotPath.ToString()
            $rigs[(Key $row.rig)] = $row.rig
            $row.clips = @(foreach ($item in $root.Animations) { $item.Chunk.Animation.Chunk.Name.ToString() })
        } else {
            if ($root.GetType().Name -cne 'animLipsyncMapping') { throw "Not a lipmap: $depot" }
            $row.language = $root.LanguageCodeName.ToString()
            $row.scene_keys = @($root.ScenePaths | ForEach-Object { $_.ToString() })
        }
        $rows.Add($row)
    }
}
$rigRows = [Collections.Generic.List[object]]::new()
foreach ($path in $paths) {
    $archive = Open-Archive $path.FullName
    foreach ($key in $rigs.Keys) {
        if (!$archive.Files.ContainsKey($key)) { continue }
        $stream = [IO.MemoryStream]::new()
        try {
            $archive.Files[$key].Extract($stream)
            $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))
        } finally { $stream.Dispose() }
        $rigRows.Add(@{depot=$rigs[$key];key=$key.ToString();archive=$path.FullName;sha256=$digest})
    }
}
$result = [ordered]@{plan_sha256=(Get-FileHash -LiteralPath $planPath).Hash;archive_count=$paths.Count;providers=$rows.ToArray();
    rig_providers=$rigRows.ToArray();english_voice_map_names=$englishVoiceMapNames.ToArray();game_writes=0;save_writes=0}
$result | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
[pscustomobject]@{assets=$rows.Count;rig_providers=$rigRows.Count;english_voice_maps=$englishVoiceMapNames.Count} | ConvertTo-Json -Compress
