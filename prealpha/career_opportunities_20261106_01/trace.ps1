param([string]$OutputName = 'capture_01')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^capture_[0-9]+$') { throw 'Specify a fresh capture_NN name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$manifestPath = Join-Path $workspace 'prealpha/quest_restoration_qr19/deployment_01/installed_manifest_01.json'
$installed = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$game = $installed.game_root
$stock = 'base\open_world\mini_world_stories\watson\mws_wat_08'
$targets = @(
    "$stock\mws_wat_08.questphase",
    "$stock\scenes\mws_wat_08.scene",
    "$stock\mws_wat_08.gamedef",
    'base\open_world\mini_world_stories\watson\watson_mini_world_stories.questphase',
    'base\quest\cyberpunk2077.quest',
    'base\quest\cyberpunk2077.questphase',
    'base\quest\additional_game_elements.questphase',
    'ep1\quest\ep1.quest',
    'ep1\quest\ep1_additional_game_elements.questphase',
    'ep1\quest\main_quests\q307\q307.quest',
    'ep1\quest\main_quests\q307\q307.questphase',
    'ep1\quest\main_quests\q307\phases\q307_cleanup.questphase',
    "towercontinued\sidejobs_s30\native\$stock\mws_wat_08.questphase",
    "towercontinued\sidejobs_s30\native\$stock\scenes\mws_wat_08.scene",
    'towercontinued\sidejobs_s30\entries\mws_wat_08_trauma_drama.questphase'
)
$expectedCore = @($installed.core_files | Where-Object path -Like 'archive/pc/mod/*')
if ($expectedCore.Count -ne 2) { throw 'Expected QR19 consolidated archive and registration' }
foreach ($file in $expectedCore) {
    if ((Get-FileHash -LiteralPath (Join-Path $game $file.path)).Hash -ne $file.sha256) {
        throw "QR19 Core baseline changed: $($file.path)"
    }
}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$service = [WolvenKit.Common.Services.HashService]::new()
$service.Load()
$lookup = @{}
foreach ($target in $targets) { $lookup[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($target)] = $target }
$markers = @('mws_wat_08.questphase','watson_mini_world_stories.questphase','ow_mini_world_stories.questphase',
    'open_world_content.questphase','cyberpunk2077.questphase',
    'shooter_appeared_on_leaderboard','shooter_position_1','mws_wat_08_pr_starter','mws_pr_trauma_drama')
$filePattern = 'mws_wat_08|trauma_drama|minigame_shooter|arcade_shooter|shooter_highscore'
$extensions = @('.quest', '.questphase', '.gamedef')
$results = [Collections.Generic.List[object]]::new()
$namedFiles = [Collections.Generic.List[object]]::new()
$archives = [Collections.Generic.List[object]]::new()
$failures = [Collections.Generic.List[object]]::new()
[IO.Directory]::CreateDirectory($output) | Out-Null
$roots = @(Join-Path $game 'archive/pc')
foreach ($folder in 'mods', 'r6/cache/modded') {
    $path = Join-Path $game $folder
    if (Test-Path -LiteralPath $path -PathType Container) { $roots += $path }
}
foreach ($file in Get-ChildItem -LiteralPath $roots -Filter '*.archive' -Recurse -File | Sort-Object FullName) {
    $metadata = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $service, [ref]$archive).ToString() -ne 'NoError') {
        throw "Could not read archive index $($file.FullName)"
    }
    $scan = $file.Name -in @('basegame_4_gamedata.archive','ep1_2_gamedata.archive','zzzz_PTFR_Combined.archive')
    $scanned = 0
    $entries = @{}
    foreach ($key in $lookup.Keys) {
        if ($archive.Files.ContainsKey([uint64]$key)) { $entries[$key] = $archive.Files[[uint64]$key] }
    }
    if ($scan -or $file.Name -in @('basegame_3_nightcity.archive','ep1_1_nightcity.archive')) {
        foreach ($entry in $archive.Files.Values) {
            if ($entry.Name -match $filePattern) {
                $namedFiles.Add(@{depot=$entry.Name; provider=$file.FullName; id=[string]$entry.Key; extension=$entry.Extension})
            }
            if ($scan -and $entry.Extension -in $extensions) { $entries[[uint64]$entry.Key] = $entry }
        }
    }
    foreach ($key in $entries.Keys | Sort-Object) {
        $entry = $entries[$key]
        $stream = [IO.MemoryStream]::new()
        try {
            $scanned += 1
            $entry.Extract($stream)
            $content = [Text.Encoding]::ASCII.GetString($stream.GetBuffer(), 0, [int]$stream.Length)
            $matches = @($markers | Where-Object { $content.Contains($_, [StringComparison]::OrdinalIgnoreCase) })
            if ($matches.Count -eq 0 -and -not $lookup.ContainsKey($key)) { continue }
            $depot = if ($lookup.ContainsKey($key)) { $lookup[$key] } else { $entry.Name }
            $raw = Join-Path $output ("asset_$($results.Count)_" + [IO.Path]::GetFileName($depot))
            [IO.File]::WriteAllBytes($raw, $stream.ToArray())
            $row = @{depot=$depot; provider=$file.FullName; id=[string]$key; markers=$matches
                raw=[IO.Path]::GetFileName($raw); sha256=(Get-FileHash -LiteralPath $raw).Hash}
            try {
                $resource = Read-Cr2wFile $raw
                $row.imports = @($resource.GetImports() | ForEach-Object { $_.ToString() })
                $json = "$raw.json"
                Export-Cr2wJson $resource $json
                $row.json = [IO.Path]::GetFileName($json)
                $row.json_sha256 = (Get-FileHash -LiteralPath $json).Hash
            } catch {
                $row.decode_error = $_.Exception.Message
            }
            $results.Add($row)
        } catch {
            $failures.Add(@{depot=$entry.Name; provider=$file.FullName; error=$_.Exception.Message})
        } finally { $stream.Dispose() }
    }
    $file.Refresh()
    if ($file.Length -ne $metadata[0] -or $file.LastWriteTimeUtc.Ticks -ne $metadata[1]) {
        throw "Archive changed during capture: $($file.FullName)"
    }
    $archives.Add(@{path=$file.FullName; metadata=$metadata; indexed=$archive.Files.Count; scanned=$scanned; scan_all_quest_extensions=$scan})
}
@{
    installed_manifest_sha256=(Get-FileHash -LiteralPath $manifestPath).Hash
    core=$expectedCore; targets=$targets; content_markers=$markers; native_extensions=$extensions
    archives=$archives; resources=$results; named_files=$namedFiles; extraction_failures=$failures
} | ConvertTo-Json -Depth 12 |
    Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding utf8NoBOM
$results | ForEach-Object { '{0} [{1}] {2}' -f $_.depot, ($_.markers -join ', '), $_['decode_error'] }
