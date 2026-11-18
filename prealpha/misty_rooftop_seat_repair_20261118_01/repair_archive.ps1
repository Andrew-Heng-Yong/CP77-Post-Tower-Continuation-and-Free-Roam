# Restore the authored V stand-up animation pair in the installed private scene.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$previous = Join-Path $workspace 'prealpha/misty_rooftop_seat_20261117_01'
$out = Join-Path $PSScriptRoot 'work/pack_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh repair output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly `
    -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

function Hash($path) { (Get-FileHash -LiteralPath $path).Hash }
function Plain($path) {
    for ($item = Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path $path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}

$manifestPath = Join-Path $previous 'installed_manifest.json'
$baseline = '8261F9C3E9B228B636E71A432AF6D715207F3A688E3AC1EC5393772A0194A738'
if ((Hash $manifestPath) -cne $baseline) { throw 'Installed seat manifest changed' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$archiveRel = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$installedArchive = Join-Path $manifest.game_root $archiveRel
$archiveHash = $manifest.archive_sha256
if ((Hash $installedArchive) -cne $archiveHash) { throw 'Installed seat archive changed' }

$donorRoot = Join-Path $previous 'work/pack_01/source'
Plain $donorRoot
if (@(Get-ChildItem -LiteralPath $donorRoot -Recurse -Force -Attributes ReparsePoint).Count) {
    throw 'Linked archive staging source'
}
$sceneDepot = 'towercontinued\misty_rooftop_seat\sit.scene'
$vanillaDepot = 'base\quest\side_quests\sq028\scenes\kerry_villa\sq028_kerry_villa_sit.scene'
$maleDepot = 'base\animations\player\male\body\player_locomotion_sick.anims'
$femaleDepot = 'base\animations\player\female\body\player_locomotion_johnny_guitar.anims'
$vanillaHash = '360699A5277BF21CCBBC097D325F698A08ED1F4F0EFE3ED049CFDDC5027F9110'
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
function OpenArchive($path) {
    $file = $null
    if ($reader.ReadArchive($path, $hashService, [ref]$file).ToString() -cne 'NoError') { throw "Unreadable archive $path" }
    return $file
}
function DepotKey([string]$path) { [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($path) }
function MemberBytes($entry) {
    $memory = [IO.MemoryStream]::new()
    try { $entry.Extract($memory); return ,$memory.ToArray() } finally { $memory.Dispose() }
}
function ByteHash([byte[]]$bytes) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }

Plain $PSScriptRoot
[void][IO.Directory]::CreateDirectory($out)
$depots = @($sceneDepot, $vanillaDepot, $maleDepot, $femaleDepot)
$providers = @{}
foreach ($depot in $depots) { $providers[$depot] = [Collections.Generic.List[object]]::new() }
$scan = @(foreach ($root in 'archive/pc', 'mods') {
    $path = Join-Path $manifest.game_root $root
    if (!(Test-Path -LiteralPath $path)) { continue }
    Plain $path
    if (@(Get-ChildItem -LiteralPath $path -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Linked archive provider tree' }
    foreach ($file in Get-ChildItem -LiteralPath $path -Recurse -File -Filter '*.archive') {
        $stamp = $file.LastWriteTimeUtc.Ticks
        $length = $file.Length
        $arc = OpenArchive $file.FullName
        foreach ($depot in $depots) {
            $key = DepotKey $depot
            if ($arc.Files.ContainsKey($key)) {
                $bytes = MemberBytes $arc.Files[$key]
                $capture = Join-Path $out ('providers/' + $file.Name + '/' + $depot)
                [void][IO.Directory]::CreateDirectory((Split-Path -Parent $capture))
                [IO.File]::WriteAllBytes($capture, $bytes)
                $providers[$depot].Add(@{archive=$file.FullName;raw=$capture;sha256=(ByteHash $bytes)})
            }
        }
        $file.Refresh()
        if ($file.LastWriteTimeUtc.Ticks -ne $stamp -or $file.Length -ne $length) { throw "Archive changed during capture $file" }
        @{path=$file.FullName;length=$length;last_write_utc=$file.LastWriteTimeUtc.ToString('o')}
    }
})
if ($providers[$sceneDepot].Count -ne 1 -or
    $providers[$sceneDepot][0].archive -cne $installedArchive -or
    $providers[$vanillaDepot].Count -ne 1 -or
    $providers[$vanillaDepot][0].sha256 -cne $vanillaHash) { throw 'Seat or vanilla provider differs' }
foreach ($depot in $maleDepot, $femaleDepot) {
    if ($providers[$depot].Count -eq 0 -or @($providers[$depot].sha256 | Select-Object -Unique).Count -ne 1) {
        throw "Ambiguous animation set $depot"
    }
    $set = (Read-Cr2wFile $providers[$depot][0].raw).RootChunk
    $idle = @($set.Animations | Where-Object { $_.Chunk.Animation.Chunk.Name.ToString() -ceq 'fpp_idle_stand' })
    if ($idle.Count -ne 1) { throw "Missing stand-up animation in $depot" }
}

$scene = Read-Cr2wFile $providers[$sceneDepot][0].raw
$beforeJson = Join-Path $out 'before.scene.json'
Export-Cr2wJson $scene $beforeJson
$native = (Read-Cr2wFile $providers[$vanillaDepot][0].raw).RootChunk.ResouresReferences
$refs = $scene.RootChunk.ResouresReferences
if ($refs.GameplayAnimSets.Count -ne 1 -or $refs.GameplayAnimNames.Count -ne 2 -or
    $native.GameplayAnimSets.Count -ne 2 -or $native.GameplayAnimNames.Count -ne 2 -or
    $refs.GameplayAnimSets[0].AsyncAnimSet.DepotPath.ToString() -cne $maleDepot -or
    $native.GameplayAnimSets[0].AsyncAnimSet.DepotPath.ToString() -cne $maleDepot -or
    $native.GameplayAnimSets[1].AsyncAnimSet.DepotPath.ToString() -cne $femaleDepot) {
    throw 'The selected scene no longer has the diagnosed animation-table mismatch'
}
foreach ($refsToVerify in $refs, $native) {
    foreach ($list in $refsToVerify.GameplayAnimNames) {
        if ($list.AnimationNames.Count -ne 1 -or $list.AnimationNames[0].ToString() -cne 'fpp_idle_stand') {
            throw 'Unexpected stand-up animation lookup'
        }
    }
}
$refs.GameplayAnimSets.Add($native.GameplayAnimSets[1].DeepCopy())

$staging = Join-Path $out 'source'
$scenePath = Join-Path $staging $sceneDepot
Write-Cr2wFile $scene $scenePath
$installed = OpenArchive $installedArchive
if ($installed.Files.Count -ne 1751) { throw 'Installed archive inventory differs' }
$oldMembers = @{}
$newMembers = @{}
foreach ($file in Get-ChildItem -LiteralPath $donorRoot -File -Recurse) {
    $depot = [IO.Path]::GetRelativePath($donorRoot, $file.FullName)
    $key = DepotKey $depot
    if ($oldMembers.ContainsKey($key) -or !$installed.Files.ContainsKey($key)) { throw "Member collision or drift $depot" }
    $hash = ByteHash (MemberBytes $installed.Files[$key])
    if ((Hash $file.FullName) -cne $hash) { throw "Staging donor changed $depot" }
    $oldMembers[$key] = $hash
    $dest = Join-Path $staging $depot
    if ($depot -cne $sceneDepot) {
        [void][IO.Directory]::CreateDirectory((Split-Path -Parent $dest))
        [IO.File]::Copy($file.FullName, $dest, $false)
    }
    $newMembers[$key] = @{depot=$depot;sha256=(Hash $dest)}
}
if ($oldMembers.Count -ne $installed.Files.Count) { throw 'Incomplete installed member inventory' }
$changed = @($newMembers.Keys | Where-Object { $newMembers[$_].sha256 -cne $oldMembers[$_] })
if ($changed.Count -ne 1 -or $changed[0] -ne (DepotKey $sceneDepot)) { throw 'Unapproved resource change' }

$archive = Join-Path $out ('package/' + $archiveRel)
[void][IO.Directory]::CreateDirectory((Split-Path -Parent $archive))
$stream = [IO.File]::Open($archive, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($staging), $stream)) { throw 'Archive packing failed' }
} finally { $stream.Dispose() }
$packed = OpenArchive $archive
if ($packed.Files.Count -ne $installed.Files.Count) { throw 'Packed inventory differs' }
foreach ($key in $newMembers.Keys) {
    if (!$packed.Files.ContainsKey($key) -or (ByteHash (MemberBytes $packed.Files[$key])) -cne $newMembers[$key].sha256) {
        throw "Packed member changed $($newMembers[$key].depot)"
    }
}
$packedScene = Join-Path $out 'packed.scene'
$packedJson = Join-Path $out 'packed.scene.json'
[IO.File]::WriteAllBytes($packedScene, (MemberBytes $packed.Files[(DepotKey $sceneDepot)]))
Export-Cr2wJson (Read-Cr2wFile $packedScene) $packedJson
if ((Hash $installedArchive) -cne $archiveHash) { throw 'Installed archive changed during staging' }
$file = Get-Item -LiteralPath $archive
@{
    status='MEMBERS_VERIFIED';baseline_sha256=$baseline;archive_provider_scan=$scan;
    checked_members=$packed.Files.Count;preserved_members=($packed.Files.Count - 1);scene_depot=$sceneDepot;
    changed_member=@{before=$oldMembers[$changed[0]];after=$newMembers[$changed[0]].sha256};
    package_file=@{path=$archiveRel;bytes=$file.Length;sha256=(Hash $archive)};
    captured_providers=$providers;before_json_sha256=(Hash $beforeJson);after_json_sha256=(Hash $packedJson);
    game_writes=0;save_writes=0
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'readback.json') -Encoding utf8NoBOM
Write-Output 'Verified the paired stand-up clips and read back all 1,751 archive members.'
