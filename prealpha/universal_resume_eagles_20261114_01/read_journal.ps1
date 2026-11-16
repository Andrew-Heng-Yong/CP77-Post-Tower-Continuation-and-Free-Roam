param(
    [ValidateRange(1,99)][int]$Attempt = 1,
    [ValidatePattern('^(ManualSave|AutoSave|PointOfNoReturnSave)-\d+$')][string[]]$Slots = @('ManualSave-26')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$output = Join-Path $PSScriptRoot ('evidence_{0:00}' -f $Attempt)
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }

$pinPath = Join-Path $workspace 'prealpha/handler_preservation_hp1_20261112_01/saves_01/ManualSave-26/manifest.json'
if ((Get-FileHash -LiteralPath $pinPath).Hash -cne '6D914C82878C704B70A96CF5A2D94781739E94C41E2F14C7FC5ECD3553509E7D') { throw 'Save manifest changed' }
$pin = Get-Content -LiteralPath $pinPath -Raw | ConvertFrom-Json
$saveRoot = Split-Path (Split-Path $pin.source -Parent) -Parent
function Assert-PlainPath([string]$path) {
    for ($item = Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path: $path" }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
Assert-PlainPath $PSScriptRoot

. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
if ((Get-FileHash -LiteralPath $parser.Assembly.Location).Hash -cne $pin.parser_sha256) { throw 'Save parser changed' }
$journals = [ordered]@{}
$root = 'quests/minor_quest/mq058_semimaru_crystalcoat'
foreach ($path in @($root,
    "$root/mq058_03_resolution", "$root/mq058_03_resolution/00_fix_semimaru",
    "$root/mq058_03_resolution/01_report_claire", "$root/mq058_03_resolution/01_try_crystalcoat",
    'contacts/marianne/mq058_02_resolution/01a_v',
    'contacts/marianne/mq058_02_resolution/01a_v/01a_ch1_1',
    'contacts/marianne/mq058_02_resolution/01a_v/01a_ch2_1',
    'contacts/marianne/mq058_02_resolution/01a_v/01a_ch3_1',
    'contacts/marianne/mq058_02_resolution/01a_v_ch1_2',
    'contacts/marianne/mq058_02_resolution/02a_claire1_1',
    'contacts/marianne/mq058_02_resolution/02a_claire2_1',
    'contacts/marianne/mq058_02_resolution/02a_claire3_1')) {
    $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
    if ($journals.Contains($key)) { throw 'Journal hash collision' }
    $journals.Add($key, $path)
}
$factNames = @('q307_point_of_no_return', 'q115_point_of_no_return', 'q307_2079', 'q307_done', 'q307_finished',
    'q307_main_game_killed', 'q307_ep1_killed',
    'mq058_Quest_Status', 'mq058_active', 'mq058_done', 'mq058_Claire_Attitude',
    'mq058_update_applied', 'mq058_opened_vvc', 'mq058_ContentToken_Main_Enable', 'mq058_ContentToken_Main_Disable',
    'sq024_done', 'mq057_done')
$hashMethod = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})[0]
$factKeys = @{}
foreach ($name in $factNames) {
    $value = [WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)
    $key = [uint32]$hashMethod.Invoke($null, [object[]]@($value))
    if ($factKeys.ContainsKey($key)) { throw 'Fact hash collision' }
    $factKeys.Add($key, $name)
}

function Read-Projection([string]$slot) {
    $source = Join-Path $saveRoot "$slot/sav.dat"
    Assert-PlainPath $source
    $bytes = [IO.File]::ReadAllBytes($source)
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
    if ($slot -ceq 'ManualSave-26' -and $digest -cne $pin.source_sha256) { throw 'Manual Save 26 changed' }
    $stream = [IO.MemoryStream]::new($bytes, $false)
    $reader = $parser::new($stream)
    try {
        $save = $null
        $status = $reader.ReadFile([ref]$save).ToString()
        if ($status -cne 'NoError') { throw "Save reader status: $status" }
        $version = $save.FileHeader.SaveVersion
        if ($version -notin @(269,277)) { throw "Unsupported save version: $version" }
        $manager = @($save.Nodes | Where-Object Name -ceq 'JournalManager')
        $quest = @($save.Nodes | Where-Object Name -ceq 'questSystem')
        if ($manager.Count -ne 1 -or $quest.Count -ne 1) { throw 'Unexpected native stores' }
        $tables = @($quest[0].Children | Where-Object Name -ceq 'FactsDB')
        if ($tables.Count -ne 1 -or $tables[0].Children.Count -ne 10) { throw 'Unexpected fact store' }
        $states = [ordered]@{}
        foreach ($path in $journals.Values) { $states.Add($path, $null) }
        foreach ($row in $manager[0].Value.Entries) {
            $raw = [byte[]]$row.UnkownBytes
            if ($raw.Length -ne 15) { throw 'Journal row framing changed' }
            $key = [BitConverter]::ToUInt32($raw, 0)
            if ($journals.Contains($key)) {
                $path = $journals[$key]
                if ($null -ne $states[$path]) { throw "Duplicate journal entry $path" }
                $states[$path] = [BitConverter]::ToUInt32($raw, 4)
            }
        }
        $facts = [ordered]@{}
        foreach ($name in $factNames) { $facts.Add($name, $null) }
        foreach ($row in $tables[0].Children[0].Value.FactEntries) {
            $key = [uint32]$hashMethod.Invoke($null, [object[]]@($row.FactName))
            if ($factKeys.ContainsKey($key)) { $facts[$factKeys[$key]] = $row.Value }
        }
        if ((Get-FileHash -LiteralPath $source).Hash -cne $digest) { throw 'Save changed during inspection' }
        return @{ slot = $slot; version = $version; journal_state = $states; facts = $facts; save_sha256 = $digest }
    } finally {
        $reader.Dispose()
        $stream.Dispose()
    }
}

$rows = @(foreach ($slot in $Slots) {
    try {
        $row = Read-Projection $slot
    } catch {
        Write-Host "$slot skipped: $($_.Exception.Message)"
        @{ slot = $slot; read_error = $_.Exception.Message }
        continue
    }
    Write-Host ("{0,-24} quest={1} active={2} done={3} update={4} q307-pnr={5} q307-finished={6} q115-pnr={7}" -f
        $slot, $row.journal_state[$root], $row.facts.mq058_active, $row.facts.mq058_done, $row.facts.mq058_update_applied,
        $row.facts.q307_point_of_no_return, $row.facts.q307_finished, $row.facts.q115_point_of_no_return)
    $row
})
[void][IO.Directory]::CreateDirectory($output)
@{ status = 'READ_ONLY_MQ058_PROJECTIONS'; saves = $rows; save_writes = 0 } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $output 'journal.json') -Encoding utf8NoBOM
