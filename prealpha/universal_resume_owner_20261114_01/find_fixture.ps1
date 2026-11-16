# Read selected journal/fact values and exact handler rows; never write a save.
param([string[]]$Slots = @('ManualSave-23','ManualSave-24','ManualSave-25','ManualSave-26','ManualSave-27','AutoSave-0'))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'fixture_search_01.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh fixture-search output required' }
$manifestPath = Join-Path $workspace 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $manifestPath).Hash -cne 'AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8') { throw 'RD10 manifest changed' }
$root = (Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json).save_root
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$readerHash = (Get-FileHash -LiteralPath $parser.Assembly.Location).Hash
if ($readerHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Save reader changed' }

$targets = @{
    [uint32]0x9A66DFB6L = 'native-open-world'
    [uint32]0xDE605479L = 'native-bugfix'
    [uint32]0x617629A2L = 's23-quest'
}
$journalTargets = @{}
foreach ($path in 'ep1/quests/minor_quest/wst_ep1_05','contacts/mr_hands/sts_ep1_04/sts_ep1_04_sms_hasan_alive_v_response') {
    $key = [WolvenKit.Core.Murmur3.Murmur32]::Hash($path, [uint32]0x5EEDBA5E, [Text.Encoding]::UTF8)
    $journalTargets[$key] = $path
}
$factTargets = @{}
$toHash = @([WolvenKit.RED4.Save.Fact].GetMethods() | Where-Object {$_.Name -eq 'op_Implicit' -and $_.ReturnType -eq [uint32]})[0]
foreach ($name in 'q307_point_of_no_return','q307_2079','q307_done','q307_finished','q307_ep1_killed','q115_point_of_no_return','hasan_default_on','sts_ep1_04_blueprints_corpo','sts_ep1_04_mr_hands_holo_convinced','wst_ep1_05_active','wst_ep1_05_finished') {
    $fact = [WolvenKit.RED4.Save.Fact]::op_Implicit([string]$name)
    $key = [uint32]$toHash.Invoke($null, [object[]]@($fact))
    $factTargets[$key] = $name
}

$results = @()
foreach ($slotName in $Slots) {
    if ($slotName -cnotmatch '^(ManualSave|AutoSave|PointOfNoReturnSave)-\d+$') { throw 'Expected an exact save slot name' }
    $file = Join-Path (Join-Path $root $slotName) 'sav.dat'
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) { throw "Save body missing for $slotName" }
    for ($item = Get-Item -LiteralPath $file; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $file" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
    $digest = (Get-FileHash -LiteralPath $file).Hash
    $bytes = [IO.File]::ReadAllBytes($file)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $digest) { throw "Changed during capture: $slotName" }
    $stream = [IO.MemoryStream]::new($bytes, $false)
    try {
        $reader = $parser::new($stream)
        try {
            $body = $null
            $status = $reader.ReadFile([ref]$body).ToString()
            if ($status -cne 'NoError') { throw "Reader status: $status" }
            $version = $body.FileHeader.SaveVersion
            if ($version -notin @(269,277)) { throw "Unsupported save version $version" }
            $quests = @($body.Nodes | Where-Object Name -ceq 'questSystem')
            $journal = @($body.Nodes | Where-Object Name -ceq 'JournalManager')
            if ($quests.Count -ne 1 -or $journal.Count -ne 1) { throw 'Quest/journal root ambiguous' }
            $events = @($quests[0].Children | Where-Object Name -ceq 'eventManager')
            $facts = @($quests[0].Children | Where-Object Name -ceq 'FactsDB')
            if ($events.Count -ne 1 -or $facts.Count -ne 1 -or $facts[0].Children.Count -ne 10) { throw 'Quest stores changed shape' }
            $registrations = @()
            foreach ($record in $events[0].Value.Unknown) {
                if ($record.Unknown1 -and $record.Unknown4 -eq 0 -and $record.Unknown3 -in @(47,61,62,69,81) -and
                    $targets.ContainsKey([uint32]$record.Unknown2)) {
                    $registrations += @{owner=$targets[[uint32]$record.Unknown2]; node=$record.Unknown3; type_u64=$record.Unknown1.ToString('X16')}
                }
            }
            $selectedFacts = @{}
            foreach ($fact in $facts[0].Children[0].Value.FactEntries) {
                $key = [uint32]$toHash.Invoke($null, [object[]]@($fact.FactName))
                if ($factTargets.ContainsKey($key)) { $selectedFacts[$factTargets[$key]] = $fact.Value }
            }
            $selectedJournal = @{}
            foreach ($row in $journal[0].Value.Entries) {
                $data = [byte[]]$row.UnkownBytes
                if ($data.Length -ne 15) { throw 'Saved journal row changed shape' }
                $hash = [BitConverter]::ToUInt32($data, 0)
                if ($journalTargets.ContainsKey($hash)) { $selectedJournal[$journalTargets[$hash]] = [BitConverter]::ToUInt32($data, 4) }
            }
            $result = @{slot=$slotName; body_sha256=$digest; save_version=$version; facts=$selectedFacts;
                        journal_state_u32=$selectedJournal; candidate_registrations=$registrations}
        } finally { $reader.Dispose() }
    } catch {
        $result = @{slot=$slotName; body_sha256=$digest; read_error=$_.Exception.Message}
    } finally { $stream.Dispose() }
    if ((Get-FileHash -LiteralPath $file).Hash -cne $digest) { throw "Changed during read: $file" }
    $results += $result
    Write-Output "Read $slotName."
}
@{ parser_sha256=$readerHash; saves=$results; scope='Managed projection uses candidate phase hash and node IDs. Hits need full path, scheduler and ending-lineage proof.' } |
    ConvertTo-Json -Depth 9 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "Inspected $($results.Count) manual, autosave and point-of-no-return slots."
