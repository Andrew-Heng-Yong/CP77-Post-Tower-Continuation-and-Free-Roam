# Read-only saved Bartmoss phone and Killing in the Name projection.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$root = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
$out = Join-Path $PSScriptRoot 'manual31_32_bartmoss_phone.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $readerType.Assembly.Location -Algorithm SHA256).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Save reader drift' }
$catalogue = Get-Content -LiteralPath (Join-Path $workspace 'prealpha/installed_qualification_20261115_01/run_01/catalogue.json') -Raw | ConvertFrom-Json
$kold = @($catalogue.entries | Where-Object { $_.id -ceq 'mq016_bartmoss' })
if ($kold.Count -ne 1) { throw 'KOLD catalogue entry missing' }
$pathKeys = @{}
foreach ($item in $kold[0].journals) {
    $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash([string]$item.path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
    if ($pathKeys.ContainsKey($key)) { throw 'Journal hash collision' }
    $pathKeys[$key] = [string]$item.path
}
foreach ($path in @('quests/minor_quest/mq018_writer','contacts/bartmoss','contacts/bartmoss/bartmoss_spam','contacts/bartmoss/bartmoss_spam/msg01','contacts/bartmoss/bartmoss_spam/msg02','contacts/bartmoss/bartmoss_spam/msg05','contacts/bartmoss/bartmoss_spam/msg06','contacts/bartmoss/bartmoss_spam/msg07')) {
    $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
    if ($pathKeys.ContainsKey($key) -and $pathKeys[$key] -cne $path) { throw 'Journal hash collision' }
    $pathKeys[$key] = $path
}
$names = @(
    'PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','PTFRPA2_Fault',
    'q307_done','q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed',
    'q307_active','q307_debug_reset','q115_point_of_no_return','q305_johnny_scene_active',
    'q001_done','q005_done','q101_enable_side_content','q103_rogue_done','mq015_active',
    'mq016_02_changed_mind','mq016_active','mq016_cryofreezer_opened','mq016_done',
    'mq016_fusebox_active','mq016_hacked','mq016_recognized_bartmoss','mq016_saved_life'
)
foreach ($suffix in @('Ready','Permit','Issued','Entered','Finished','Fault')) { $names += 'PTFRS29_mq016_bartmoss_' + $suffix }
$names += @('mq018_started','mq018_active','mq018_done','mq018_visit_website','mq018_web_bartmosscollective_visited','mq018_debug','mq018_call_nancy_chicken','PTFRS29_PHONE_nancy_Issued','q003_done','q101_done','q110_done')
foreach ($suffix in @('Ready','Permit','Issued','Entered','Finished','Fault')) { $names += 'PTFRS29_mq018_writer_' + $suffix }
$toHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object { $_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32] })
if ($toHash.Count -ne 1) { throw 'Ambiguous fact hash method' }
$factKeys = @{}
foreach ($name in $names) {
    $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit($name)
    $key = [uint32]$toHash[0].Invoke($null, [object[]]@($fact))
    if ($factKeys.ContainsKey($key)) { throw 'Fact hash collision' }
    $factKeys[$key] = $name
}
function Plain([string]$path) {
    for ($item = Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
$rows = @(foreach ($slot in @('ManualSave-31','ManualSave-32')) {
    $folder = Join-Path $root $slot
    $savePath = Join-Path $folder 'sav.dat'
    $metaPath = Join-Path $folder 'metadata.9.json'
    Plain $savePath; Plain $metaPath
    $saveHash = (Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash
    $metaHash = (Get-FileHash -LiteralPath $metaPath -Algorithm SHA256).Hash
    $bytes = [IO.File]::ReadAllBytes($savePath)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $saveHash) { throw 'Input changed while copying' }
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = $readerType::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw "Save parse/version failed: $slot" }
        $rootNodes = @($save.Nodes | Where-Object Name -CEQ 'questSystem')
        $journalNodes = @($save.Nodes | Where-Object Name -CEQ 'JournalManager')
        if ($rootNodes.Count -ne 1 -or $journalNodes.Count -ne 1) { throw 'Ambiguous native roots' }
        $db = @($rootNodes[0].Children | Where-Object Name -CEQ 'FactsDB')
        if ($db.Count -ne 1 -or $db[0].Children.Count -ne 10) { throw 'Unexpected fact store' }
        $facts = [ordered]@{}
        foreach ($name in $names) { $facts[$name] = $null }
        foreach ($entry in $db[0].Children[0].Value.FactEntries) {
            $key = [uint32]$toHash[0].Invoke($null, [object[]]@($entry.FactName))
            if ($factKeys.ContainsKey($key)) {
                $name = $factKeys[$key]
                if ($null -ne $facts[$name]) { throw "Duplicate fact: $name" }
                $facts[$name] = [uint32]$entry.Value
            }
        }
        $journals = @(foreach ($entry in $journalNodes[0].Value.Entries) {
            $raw = [byte[]]$entry.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Unexpected journal framing' }
            $key = [BitConverter]::ToUInt32($raw, 0)
            if ($pathKeys.ContainsKey($key)) { @{ path=$pathKeys[$key]; state_u32=[BitConverter]::ToUInt32($raw,4); raw15=[Convert]::ToHexString($raw) } }
        })
        $meta = (Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json).Data.metadata
        if ((Get-FileHash -LiteralPath $savePath -Algorithm SHA256).Hash -cne $saveHash -or (Get-FileHash -LiteralPath $metaPath -Algorithm SHA256).Hash -cne $metaHash) { throw 'Input changed during read' }
        @{ slot=$slot; save_sha256=$saveHash; metadata_sha256=$metaHash; timestamp=$meta.timestampString; playthrough_id=$meta.playthroughID; point_of_no_return_id=$meta.pointOfNoReturnId; end_game=$meta.isEndGameSave; location=$meta.locationName; tracked=$meta.trackedQuestEntry; facts=$facts; journals=$journals }
    } finally { $reader.Dispose(); $memory.Dispose() }
})
if ($rows[0].playthrough_id -cne $rows[1].playthrough_id -or $rows[0].point_of_no_return_id -cne $rows[1].point_of_no_return_id) { throw 'Save lineage mismatch' }
$result = @{ status='READ_ONLY_BARTMOSS_PHONE_SAVE_PROJECTION'; parser_sha256=$parserHash; source_catalogue_sha256=(Get-FileHash -LiteralPath (Join-Path $workspace 'prealpha/installed_qualification_20261115_01/run_01/catalogue.json') -Algorithm SHA256).Hash; saves=$rows; limits=@('Null fact or absent journal row means not serialized, not a proven runtime zero/Inactive.','Saved journal values do not show live phone UI filtering or message visited state.'); save_writes=0; game_calls=0 }
[IO.File]::WriteAllText($out, ($result | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Write-Output "Bartmoss phone save projection complete: $out"
