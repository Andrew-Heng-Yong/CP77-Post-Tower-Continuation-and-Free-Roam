param([string]$OutputName = 'capture_01')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($OutputName -cnotmatch '^capture_[0-9]+$') { throw 'Specify a fresh capture_NN directory name' }
$output = Join-Path $PSScriptRoot $OutputName
if (Test-Path -LiteralPath $output) { throw "Capture already exists at $output" }
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$manifestPath = Join-Path $workspace 'prealpha/quest_restoration_qr19/deployment_01/installed_manifest_01.json'
$installed = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$game = $installed.game_root
$core = @(foreach ($file in $installed.core_files | Where-Object path -Like 'archive/pc/mod/*') {
    $path = Join-Path $game $file.path
    $sha = (Get-FileHash -LiteralPath $path).Hash
    if ($sha -ne $file.sha256) { throw "QR19 Core archive file changed: $path" }
    @{path = $path; sha256 = $sha}
})
if ($core.Count -ne 2) { throw 'Expected the consolidated archive and ArchiveXL registration' }

$wolvenKit = Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot $wolvenKit
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$district = 'base\open_world\street_stories\santo_domingo\rancho_corronado'
$gig = "$district\sts_std_rcr_02"
$depots = @(
    "$district\sts_std_rancho_corronado.questphase",
    "$gig\phases\sts_std_rcr_02_phase.questphase",
    "$gig\communities\sts_std_rcr_02_enemies.community",
    "$gig\scenes\sts_std_rcr_02_scene.scene"
)
$depots += @('dixon', 'reception', 'wheelchair', 'johnny', 'holocall_prebrief', 'holocall_debriefs', 'chats') |
    ForEach-Object { "$gig\scenes\sts_std_rcr_02_${_}.scene" }
$depots += @('entry', 'credit', 'map0', 'map1') |
    ForEach-Object { "towercontinued\native_gigs_u9\sts_std_rcr_02_${_}.questphase" }
$targets = @{}
foreach ($depot in $depots) {
    $targets[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)] = $depot
}
$roots = @(Join-Path $game 'archive/pc')
foreach ($folder in 'mods', 'r6/cache/modded') {
    $path = Join-Path $game $folder
    if (Test-Path -LiteralPath $path -PathType Container) { $roots += $path }
}
$archives = @(Get-ChildItem -LiteralPath $roots -Filter '*.archive' -Recurse -File | Sort-Object FullName)
$providers = [Collections.Generic.List[object]]::new()
[IO.Directory]::CreateDirectory($output) | Out-Null
foreach ($file in $archives) {
    $metadata = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = $null
    if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName, $hashService, [ref]$archive).ToString() -ne 'NoError') {
        throw "Could not read archive index $($file.FullName)"
    }
    foreach ($key in $targets.Keys | Sort-Object) {
        if (-not $archive.Files.ContainsKey([uint64]$key)) { continue }
        $depot = $targets[$key]
        $raw = Join-Path $output ("asset_$($providers.Count)_" + [IO.Path]::GetFileName($depot))
        $stream = [IO.File]::Create($raw)
        try { $archive.Files[[uint64]$key].Extract($stream) } finally { $stream.Dispose() }
        $json = $raw + '.json'
        Export-Cr2wJson (Read-Cr2wFile $raw) $json
        $providers.Add(@{
            depot = $depot; depot_id = [string]$key; provider = $file.FullName; metadata = $metadata
            raw = [IO.Path]::GetFileName($raw); sha256 = (Get-FileHash -LiteralPath $raw).Hash
            json = [IO.Path]::GetFileName($json); json_sha256 = (Get-FileHash -LiteralPath $json).Hash
        })
    }
    $file.Refresh()
    if ($file.Length -ne $metadata[0] -or $file.LastWriteTimeUtc.Ticks -ne $metadata[1]) {
        throw "Archive changed during capture: $($file.FullName)"
    }
}
foreach ($file in $core) {
    if ((Get-FileHash -LiteralPath $file.path).Hash -ne $file.sha256) {
        throw "Core file changed during capture: $($file.path)"
    }
}
@{
    installed_manifest = $manifestPath; installed_manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath).Hash
    core = $core; archives = @($archives.FullName); targets = $depots; providers = $providers
} | ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath (Join-Path $output 'providers.json') -Encoding utf8NoBOM

$legacyCache = Join-Path $workspace 'research/restriction_profiles/profile_r3/fixture_20261007T220546277Z_413087c6/game/r6/cache'
$numericCast = [WolvenKit.RED4.Types.TweakDBID].GetMethods() |
    Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint64] }
function Describe-Flat($Value) {
    if ($Value -is [WolvenKit.RED4.Types.TweakDBID]) {
        $id = [uint64]$numericCast.Invoke($null, [object[]]@($Value.PSObject.BaseObject))
        return @{id = [string]$id; name = [WolvenKit.RED4.Types.Pools.TweakDBIDPool]::ResolveHash($id)}
    }
    if ($Value -is [Collections.IEnumerable] -and $Value -isnot [string]) {
        return ,@($Value | ForEach-Object { Describe-Flat $_ })
    }
    if ($null -ne $Value) { return $Value.ToString() }
}
function Get-RecordEvidence($Database, [string]$Identity) {
    $id = if ($Identity -match '^\d+$') { [uint64]$Identity } else {
        [WolvenKit.RED4.Types.TweakDBID]::CalculateHash($Identity)
    }
    $record = $Database.Records.GetRecord($id)
    $name = [WolvenKit.RED4.Types.Pools.TweakDBIDPool]::ResolveHash($id)
    $row = @{id = [string]$id; name = $name; type = $null; fields = @{}}
    if ($null -eq $record) { return $row }
    $row.type = $record.Name
    if (-not $name) { return $row }
    $propertyPattern = switch -Regex ($record.Name) {
        '^gamedataCharacter_Record$' { 'Loot|Equipment|EntityTemplate|Tags' }
        'Loot' { '.' }
        '^gamedataItem_Record$' { 'ItemType|Tags|EntityName|Savable' }
        default { '^$' }
    }
    foreach ($property in $record.GetProperties() | Where-Object Name -Match $propertyPattern) {
        $field = $property.Name.Substring(0, 1).ToLowerInvariant() + $property.Name.Substring(1)
        $key = [WolvenKit.RED4.Types.TweakDBID]::CalculateHash("$name.$field")
        if ($Database.Flats.Exists($key)) { $row.fields[$field] = Describe-Flat ($Database.Flats.GetValue($key)) }
    }
    return $row
}

$seedRecords = @('114327022403', 'Character.rcr_02_enemy_security_keycard', 'Keycards.rcr_02_keycard_doc', 'Items.sts_std_rcr_02_shard')
$databases = foreach ($cache in @(Join-Path $game 'r6/cache'), $legacyCache) {
    foreach ($filename in 'tweakdb.bin', 'tweakdb_ep1.bin') {
        $path = Join-Path $cache $filename
        $sha = (Get-FileHash -LiteralPath $path).Hash
        $stream = [IO.File]::OpenRead($path)
        try {
            $database = $null
            if (([WolvenKit.RED4.TweakDB.TweakDBReader]::new($stream)).ReadFile([ref]$database).ToString() -ne 'NoError') {
                throw "TweakDB could not be parsed: $path"
            }
            $records = @{}
            $queue = [Collections.Generic.Queue[string]]::new()
            foreach ($seed in $seedRecords) { $queue.Enqueue($seed) }
            while ($queue.Count) {
                $row = Get-RecordEvidence $database $queue.Dequeue()
                if ($records.ContainsKey($row.id)) { continue }
                $records[$row.id] = $row
                if ($records.Count -gt 64) { throw 'Exceeded bounded TweakDB traversal' }
                foreach ($field in $row.fields.GetEnumerator()) {
                    if ($row.type -eq 'gamedataCharacter_Record' -and $field.Key -notmatch 'Loot') { continue }
                    foreach ($reference in @($field.Value)) {
                        if ($reference -is [hashtable] -and $reference.id -ne '0') { $queue.Enqueue($reference.id) }
                    }
                }
            }
        } finally { $stream.Dispose() }
        if ((Get-FileHash -LiteralPath $path).Hash -ne $sha) { throw "TweakDB changed during capture: $path" }
        @{path = $path; sha256 = $sha; records = @($records.Values | Sort-Object id)}
    }
}
@($databases) | ConvertTo-Json -Depth 12 |
    Set-Content -LiteralPath (Join-Path $output 'tweakdb.json') -Encoding utf8NoBOM
