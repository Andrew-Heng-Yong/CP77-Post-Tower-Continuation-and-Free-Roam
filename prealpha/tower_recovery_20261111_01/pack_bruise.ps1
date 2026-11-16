param([Parameter(Mandatory)][ValidateRange(1, 99)][int]$Attempt)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$prealpha = Split-Path -Parent $PSScriptRoot
$workspace = Split-Path -Parent $prealpha
$output = Join-Path $PSScriptRoot ('archive_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $output) { throw 'Fresh archive output required.' }

$baselineFile = Join-Path $prealpha 'johnny_load_crash_20261111_01/deployment_01/installed_manifest_01.json'
$baselineHash = 'EE5CEF96EE36BB8C876A46BA9FFE179B235592138059C75FC45BB7636B880878'
if ((Get-FileHash -LiteralPath $baselineFile).Hash -cne $baselineHash) { throw 'Predecessor manifest drift.' }
$baseline = Get-Content -LiteralPath $baselineFile -Raw | ConvertFrom-Json -AsHashtable
$combined = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
$source = Join-Path $baseline.game_root $combined
$archiveRow = $baseline.core_files | Where-Object path -ceq $combined
$xlRow = $baseline.core_files | Where-Object path -ceq ($combined + '.xl')
if ((Get-FileHash -LiteralPath $source).Hash -cne $archiveRow.sha256 -or
    (Get-FileHash -LiteralPath ($source + '.xl')).Hash -cne $xlRow.sha256) { throw 'Installed combined archive or XL drift.' }

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (
    Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()

function Key([string]$Depot) {
    [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($Depot)
}
function Open-Archive([string]$Path) {
    $archive = $null
    if ($reader.ReadArchive($Path, $hashService, [ref]$archive).ToString() -cne 'NoError') {
        throw "Unreadable archive $Path"
    }
    return $archive
}
function Entry-Hash($Entry) {
    $stream = [IO.MemoryStream]::new()
    try {
        [void]$Entry.Extract($stream)
        return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream.ToArray()))
    } finally {
        $stream.Dispose()
    }
}
function Save-Entry($Entry, [string]$Path) {
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { [void]$Entry.Extract($stream) } finally { $stream.Dispose() }
}
function Guard-Tree([string]$Path, [switch]$ArchiveOnly) {
    $rootItem = Get-Item -LiteralPath $Path -Force
    $links = @(Get-ChildItem -LiteralPath $Path -Recurse -Force -Attributes ReparsePoint | Where-Object {
        !$ArchiveOnly -or $_.PSIsContainer -or $_.Extension -in @('.archive', '.xl')
    })
    if ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint -or
        $links.Count) {
        throw "Linked resource tree $Path"
    }
}

$depot = 'towercontinued\recovery\bruise_clear.questphase'
$sceneDepot = 'ep1\quest\main_quests\q307\scenes\q307_09_cutscene.scene'
$parentDepot = 'ep1\quest\ep1.quest'
$key = Key $depot
$nativeKeys = [ordered]@{ final_scene = (Key $sceneDepot); ep1_root = (Key $parentDepot) }
$providers = [ordered]@{ final_scene = @(); ep1_root = @() }
$donor = $baseline.archive_source
$archiveRoot = Join-Path $baseline.game_root 'archive/pc'
$pluginRoot = Join-Path $baseline.game_root 'red4ext/plugins'
Guard-Tree $donor
foreach ($path in @($archiveRoot, $pluginRoot)) { Guard-Tree $path -ArchiveOnly }
$archives = @(Get-ChildItem -LiteralPath $archiveRoot, $pluginRoot -Recurse -File -Force -Filter '*.archive')
$archiveInputs = @(foreach ($file in $archives) {
    @{
        path = [IO.Path]::GetRelativePath($baseline.game_root, $file.FullName).Replace('\', '/')
        bytes = $file.Length; mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks
    }
})
[void](New-Item -ItemType Directory -Path $output)
$nativeScene = Join-Path $output 'q307_09_cutscene.scene'
$nativeParent = Join-Path $output 'ep1.quest'
$nativePaths = @{ final_scene = $nativeScene; ep1_root = $nativeParent }
foreach ($file in $archives) {
    $stamp = @($file.Length, $file.LastWriteTimeUtc.Ticks)
    $archive = Open-Archive $file.FullName
    if ($archive.Files.ContainsKey($key)) { throw "New depot path already exists in $($file.FullName)." }
    foreach ($name in $nativeKeys.Keys) {
        if (!$archive.Files.ContainsKey($nativeKeys[$name])) { continue }
        $entry = $archive.Files[$nativeKeys[$name]]
        $providers[$name] += @{
            path = [IO.Path]::GetRelativePath($baseline.game_root, $file.FullName).Replace('\', '/')
            sha256 = (Entry-Hash $entry)
        }
        if ($providers[$name].Count -eq 1) { Save-Entry $entry $nativePaths[$name] }
    }
    $file.Refresh()
    if ($file.Length -ne $stamp[0] -or $file.LastWriteTimeUtc.Ticks -ne $stamp[1]) {
        throw "Archive changed while reading $($file.FullName)."
    }
}
foreach ($name in $nativeKeys.Keys) {
    if ($providers[$name].Count -ne 1 -or $providers[$name][0].path -notmatch '^archive/pc/ep1/[^/]+\.archive$' -or
        (Get-FileHash -LiteralPath $nativePaths[$name]).Hash -cne $providers[$name][0].sha256) {
        throw "Unexpected native providers for $name."
    }
}

$sceneJson = Join-Path $output 'q307_09_cutscene.scene.json'
Export-Cr2wJson (Read-Cr2wFile $nativeScene) $sceneJson
$parentFile = Read-Cr2wFile $nativeParent
$parentGraph = $parentFile.RootChunk.Graph.Chunk
$parentIds = @($parentGraph.Nodes | ForEach-Object { [int]::Parse($_.Chunk.Id.ToString()) })
$parentNode = Get-QuestNode $parentGraph 1
if ($parentNode.GetType().Name -cne 'questStartNodeDefinition') { throw 'EP1 root start node changed.' }
[void](Get-QuestSocket $parentNode 'Out')

$graph = [WolvenKit.RED4.Types.questGraphDefinition]::new()
$inputNode = New-InputNode 0 'In1'
$doneNode = New-ConditionNode 1 (New-FactCondition 'PTFRRecovery_BruiseApplied' 1 ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
$waitNode = [WolvenKit.RED4.Types.questPauseConditionNodeDefinition]::new()
$waitNode.Id = [uint16]2
$facts = [ordered]@{
    q307_done=1; q307_finished=1; q307_active=0; q307_2079=1
    q307_main_game_killed=1; q307_ep1_killed=1; q305_johnny_scene_active=0
    PostTowerFreeRoamActive=1; PTFRP0_DR13=1; PTFRPA2_ControlReady=1; PTFRPA2_Fault=0
    PTFRRecovery_BruiseReady=1; PTFRRecovery_BruiseApplied=0
}
$gate = [WolvenKit.RED4.Types.questLogicalCondition]::new()
$gate.Operation = [WolvenKit.RED4.Types.Enums+questLogicalOperation]::AND
foreach ($fact in $facts.Keys) {
    Add-RedHandle $gate.Conditions (New-FactCondition $fact $facts[$fact] ([WolvenKit.RED4.Types.Enums+EComparisonType]::Equal))
}
Set-RedHandleProperty $waitNode Condition $gate

$resetNode = [WolvenKit.RED4.Types.questCharacterManagerNodeDefinition]::new()
$resetNode.Id = [uint16]3
$visuals = [WolvenKit.RED4.Types.questCharacterManagerVisuals_NodeType]::new()
$brokenNose = [WolvenKit.RED4.Types.questCharacterManagerVisuals_SetBrokenNoseStage]::new()
$brokenNose.BrokenNoseStage = [WolvenKit.RED4.Types.Enums+gameuiCharacterCustomization_BrokenNoseStage]::CCBN_Disabled
Set-RedHandleProperty $visuals Subtype $brokenNose
Set-RedHandleProperty $resetNode Type $visuals
$ack = New-SetFactNode 4 'PTFRRecovery_BruiseApplied' 1
$exitNode = New-OutputNode 5 'Out1'

foreach ($node in @($waitNode, $resetNode)) {
    [void](New-QuestSocket $node 'CutDestination' ([WolvenKit.RED4.Types.Enums+questSocketType]::CutDestination))
    [void](New-QuestSocket $node 'In' ([WolvenKit.RED4.Types.Enums+questSocketType]::Input))
    [void](New-QuestSocket $node 'Out' ([WolvenKit.RED4.Types.Enums+questSocketType]::Output))
}
foreach ($node in @($inputNode, $doneNode, $waitNode, $resetNode, $ack, $exitNode)) {
    Add-RedHandle $graph.Nodes $node
}
function Link([int]$From, [string]$Socket, [int]$To) {
    [void](Connect-QuestSockets (Get-QuestSocket (Get-QuestNode $graph $From) $Socket) (Get-QuestSocket (Get-QuestNode $graph $To) 'In'))
}
Link 0 'Out' 1
Link 1 'True' 5
Link 1 'False' 2
Link 2 'Out' 3
Link 3 'Out' 4
Link 4 'Out' 5

$phaseRoot = [WolvenKit.RED4.Types.questQuestPhaseResource]::new()
$phaseRoot.CookingPlatform = [WolvenKit.RED4.Types.Enums+ECookingPlatform]::PLATFORM_PC
Set-RedHandleProperty $phaseRoot Graph $graph
$phaseFile = [WolvenKit.RED4.Archive.CR2W.CR2WFile]::new()
$phaseFile.RootChunk = $phaseRoot

$staged = Join-Path $output 'archive_source'
Copy-Item -LiteralPath $donor -Destination $staged -Recurse
$newFile = Join-Path $staged $depot
if (Test-Path -LiteralPath $newFile) { throw 'New private phase already exists in source.' }
Write-Cr2wFile $phaseFile $newFile

$stagedArchive = Join-Path $output 'zzzz_PTFR_Combined.archive'
$stream = [IO.File]::Open($stagedArchive, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hashService, [WolvenKit.SerilogWrapper]::new())
    if (!$writer.WriteArchive([IO.DirectoryInfo]::new($staged), $stream)) { throw 'Archive packing failed.' }
} finally {
    $stream.Dispose()
}
$old = Open-Archive $source
$new = Open-Archive $stagedArchive
if ($old.Files.Count -ne $baseline.archive_payloads -or $new.Files.Count -ne $old.Files.Count + 1 -or
    !$new.Files.ContainsKey($key)) { throw 'Archive inventory mismatch.' }
foreach ($item in $old.Files.GetEnumerator()) {
    if (!$new.Files.ContainsKey($item.Key) -or (Entry-Hash $new.Files[$item.Key]) -cne (Entry-Hash $item.Value)) {
        throw "Retained archive resource drift: $($item.Key)"
    }
}
$readback = Join-Path $output 'bruise_clear.questphase'
Save-Entry $new.Files[$key] $readback
if ((Get-FileHash -LiteralPath $readback).Hash -cne (Get-FileHash -LiteralPath $newFile).Hash) {
    throw 'Packed private phase readback mismatch.'
}
$readbackJson = Join-Path $output 'bruise_clear.questphase.json'
Export-Cr2wJson (Read-Cr2wFile $readback) $readbackJson
if ((Get-FileHash -LiteralPath $source).Hash -cne $archiveRow.sha256) { throw 'Installed archive changed.' }
[ordered]@{
    status = 'PASS'; before_archive_sha256 = $archiveRow.sha256
    after_archive_sha256 = (Get-FileHash -LiteralPath $stagedArchive).Hash
    retained_members = $old.Files.Count; members = $new.Files.Count
    added_depot = $depot; added_key = $key.ToString(); archive_inputs = $archiveInputs
    raw_sha256 = (Get-FileHash -LiteralPath $readback).Hash
    graph_json_sha256 = (Get-FileHash -LiteralPath $readbackJson).Hash
    source_scene_json_sha256 = (Get-FileHash -LiteralPath $sceneJson).Hash
    native_providers = $providers; native_root_ids = $parentIds
} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $output 'archive_readback.json') -Encoding utf8
Write-Output "Verified $($old.Files.Count) retained payloads and the private bruise-clear phase."
