Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$manifestPath = Join-Path $ws 'prealpha/johnny_batch4_jb3/deployment_01/installed_manifest_01.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.core_epoch -cne 'JB3') { throw 'Unexpected installed baseline' }
$game = $manifest.game_root
foreach ($row in @($manifest.core_files) + @($manifest.required_files)) {
    if ((Get-FileHash -LiteralPath (Join-Path $game $row.path)).Hash -cne $row.sha256) {
        throw "Installed baseline changed: $($row.path)"
    }
}
$out = Join-Path $PSScriptRoot 'capture_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh capture required' }
New-Item -ItemType Directory -Path $out | Out-Null

. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$targets = @('base\localization\en-us.lipmap','ep1\localization\en-us.lipmap','towercontinued\sidejob_repair_sr1\en-us.lipmap')
foreach ($stem in @('mq032_01_hook','mq032_02_maelstrom','mq032_03_epilogue')) {
    $targets += "base\quest\minor_quests\mq032\scenes\$stem.scene"
    $targets += "towercontinued\johnny_batch3\mq032\$stem.scene"
}
$keys = @{}
foreach ($target in $targets) { $keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($target)] = $target }
$archives = @(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Filter '*.archive' -File -Recurse | Sort-Object FullName)
$providers = [Collections.Generic.List[object]]::new()
$index = 0
foreach ($archiveFile in $archives) {
    $index += 1
    $archive = $null
    if ($reader.ReadArchive($archiveFile.FullName, $hashService, [ref]$archive).ToString() -cne 'NoError') {
        throw "Cannot index $($archiveFile.FullName)"
    }
    foreach ($key in $keys.Keys) {
        if (!$archive.Files.ContainsKey([uint64]$key)) { continue }
        $depot = $keys[$key]
        $path = Join-Path $out ('raw/' + $index + '/' + $key.ToString() + [IO.Path]::GetExtension($depot))
        New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
        $stream = [IO.File]::Create($path)
        try { $archive.Files[[uint64]$key].Extract($stream) } finally { $stream.Dispose() }
        $json = $path + '.json'
        Export-Cr2wJson (Read-Cr2wFile $path) $json
        $providers.Add([ordered]@{depot=$depot;key=$key.ToString();archive=$archiveFile.FullName;raw=$path;
            sha256=(Get-FileHash -LiteralPath $path).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash})
    }
}
$registrationFiles = @(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -Filter '*.xl' -File -Recurse |
    Where-Object { Select-String -LiteralPath $_.FullName -Pattern '^\s*lipmaps:' -Quiet })
$registrations = @(foreach ($file in $registrationFiles) {
    $copy = Join-Path $out ('xl_' + $file.Name)
    if (Test-Path -LiteralPath $copy) { throw 'Ambiguous localization config filename' }
    Copy-Item -LiteralPath $file.FullName -Destination $copy
    $digest = (Get-FileHash -LiteralPath $file.FullName).Hash
    if ((Get-FileHash -LiteralPath $copy).Hash -cne $digest) { throw 'Localization config changed during read' }
    @{path=$file.FullName;copy=$copy;sha256=$digest}
})
$settings = Join-Path $env:LOCALAPPDATA 'CD Projekt Red/Cyberpunk 2077/UserSettings.json'
$voice = $null
if (Test-Path -LiteralPath $settings) {
    $voiceMatch = [regex]::Match((Get-Content -LiteralPath $settings -Raw), '"name"\s*:\s*"VoiceOver"[^}]*"value"\s*:\s*"([^"]+)"')
    if ($voiceMatch.Success) { $voice = $voiceMatch.Groups[1].Value }
}
$result = [ordered]@{epoch='JB3';installed_manifest=$manifestPath;installed_manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash;
    archive_sha256=$manifest.archive_sha256;core_and_dependency_hashes=(@($manifest.core_files).Count+@($manifest.required_files).Count);
    archives_indexed=$archives.Count;archives=@($archives.FullName);queries=$targets;providers=$providers.ToArray();
    voice_over=$voice;localization_configs=$registrations;game_writes=0;save_writes=0}
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $out 'providers.json') -Encoding utf8NoBOM
[pscustomobject]@{baseline='JB3';providers=$providers.Count;archives=$archives.Count;voice_over=$voice;
    localization_configs=$registrations.Count} | ConvertTo-Json -Compress
